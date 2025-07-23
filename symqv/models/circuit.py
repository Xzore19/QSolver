import collections
import time
from enum import Enum
from tempfile import NamedTemporaryFile
from typing import List, Tuple, Union, Set

import numpy as np
from z3 import Tactic, Or, And, If, Real, Bool

from symqv.constants import I_matrix, CNOT_matrix, SWAP_matrix

from symqv.expressions.qbit import QbitVal, Qbits
from symqv.expressions.rqbit import RQbitVal, RQbits
from symqv.expressions.complex import Complexes
from symqv.globals import precision_format
from symqv.models.gate import Gate
from symqv.models.measurement import Measurement
from symqv.models.state_sequence import StateSequence
from symqv.operations.measurements import zero_measurement, one_measurement
from symqv.solver import solve, write_smt_file, SpecificationType
from symqv.utils.arithmetic import state_equals, state_equals_value, matrix_vector_multiplication, \
    complex_kron_n_ary, kron, state_equals_phase_oracle
from symqv.utils.helpers import get_qbit_indices, identity_pad_gate, to_complex_matrix, \
    identity_pad_single_qbit_gates, are_qbits_reversed, are_qbits_adjacent, swap_transform_non_adjacent_gate

import subprocess


class Method(Enum):
    state_model = 'state_model'


class Circuit:
    def __init__(self, qbits: List[Union[QbitVal, RQbitVal]],
                 program: List[Union[Gate, List[Gate], Measurement]],
                 delta: float = 0.00001):

        self.qbits = qbits
        self.final_qbits = None
        self.num_qbits = len(self.qbits)
        self.program = program
        self.state = Complexes([f'psi_0_{i}' for i in range(2 ** self.num_qbits)])
        self.delta = delta
        self.initial_qbit_values = None
        self.initial_gate_applications = None
        self.initial_state_value = None
        self.specification = None
        self.specification_type = None
        self.is_equality_specification = None
        self.initialization_has_none_values = False
        self.solver = Tactic('qfnra-nlsat').solver()

    def __str__(self):
        return ', '.join([str(gate) for gate in self.program])

    def initialize(self, values):
        """
        Initialize a quantum circuit with state values.
        :param values: list all states.
        :return: void.
        """
        basic_constraint = sum([elem.r ** 2 + elem.i ** 2 for elem in self.state]) == 1
        self.solver.add(basic_constraint)

        if self.initial_qbit_values is not None:
            print('Qbits are already initialized. Reinitializing.')

        for i, value in enumerate([v for v in values if v is not None]):
            self.solver.add(state_equals_value(self.state[i], value))

        self.initialization_has_none_values = any([value is None for value in values])
        self.initial_state_values = values

    def set_initial_gate_applications(self, gates: List[Gate]):
        """
        Use gates to construct the initial state.
        :param gates:
        :return:
        """
        if self.initial_qbit_values is None:
            raise Exception("No initial values provided.")

        self.initial_gate_applications = gates

    def prove(self,
              dump_smt_encoding: bool = False,
              dump_solver_output: bool = False,
              measurement_branch: int = None,
              file_generation_only: bool = False,
              synthesize_repair: bool = False,
              overapproximation: bool = False,
              matrix_method = False) -> Union[
        Tuple[str, collections.OrderedDict, float], Tuple[NamedTemporaryFile, Set[str]]]:

        return self._prove_state_model(dump_smt_encoding,
                                       dump_solver_output,
                                       measurement_branch,
                                       file_generation_only,
                                       synthesize_repair,
                                       overapproximation,
                                       matrix_method)

    def _prove_state_model(self,
                           dump_smt_encoding: bool = False,
                           dump_solver_output: bool = False,
                           measurement_branch: int = None,
                           file_generation_only: bool = False,
                           synthesize_repair: bool = False,
                           overapproximation: bool = False,
                           matrix_method: bool = False) -> Union[Tuple[str, collections.OrderedDict, float],
    Tuple[NamedTemporaryFile, Set[str]]]:
        """
        Prove a quantum circuit according to the state model, symbolically encoding states as full vectors.
        :param dump_smt_encoding:  print the utils encoding.
        :param dump_solver_output: print the verbatim solver output.
        :param measurement_branch: which measurement branch to consider (optional, only used by parallel evaluation).
        :param file_generation_only: only generate file, don't call solver.
        :param synthesize_repair: Synthesize repair to make the circuit fulfill the specification.
        :return: Solver output.
        """
        start_full = time.time()

        state_sequence = StateSequence(self.qbits)

        if self.initial_gate_applications is not None:
            combined_initial_gate = identity_pad_gate(I_matrix, [0], self.num_qbits)
        
        for t_op in self.program:
            if matrix_method:
                complex_operation_matrix = np.identity(len(state_sequence.states[-1]), dtype=complex)
                previous_state = state_sequence.states[-1]
                next_state = state_sequence.add_state()
                # print("state_sequence:", next_state)
                for (i, operation) in enumerate(t_op):
                    if isinstance(operation, Gate) or isinstance(operation, List):
                        if len(state_sequence.measured_states) > 0:
                            raise Exception('Gates after measurement are not supported.')

                        if isinstance(operation, Gate) and operation.oracle_value is None:
                            qbit_indices = get_qbit_indices([q.get_identifier() for q in self.qbits], operation.arguments)

                            if not are_qbits_adjacent(qbit_indices):
                                state_operation = swap_transform_non_adjacent_gate(operation.matrix,
                                                                                qbit_indices,
                                                                                self.num_qbits)
                            else:
                                state_operation = identity_pad_gate(operation.matrix
                                                                    if not are_qbits_reversed(qbit_indices)
                                                                    else operation.matrix_swapped,
                                                                    qbit_indices,
                                                                    self.num_qbits)

                    state_operation = state_operation.astype(np.complex128)
                    state_operation.real[np.abs(state_operation.real) < 0.00001] = 0
                    state_operation.imag[np.abs(state_operation.imag) < 0.00001] = 0
                    # print("state_operation:", state_operation)
                    # print("state_operation_type:", type(state_operation))
                    # print("!!!!!!!!!!!!!!!!", state_operation.imag)
                    # print("complex:", complex_operation_matrix)
                    # print("complex_type:", type(complex_operation_matrix))
                    complex_operation_matrix = np.dot(state_operation, complex_operation_matrix)
                    # complex_operation_matrix = np.dot(complex_operation_matrix, state_operation)
                # print("initial:", complex_operation_matrix)
                # print("state_equals in circuit.py:", state_equals(next_state,
                #                                         matrix_vector_multiplication(to_complex_matrix(complex_operation_matrix),
                #                                                                     previous_state)))
                self.solver.add(state_equals(next_state, matrix_vector_multiplication(to_complex_matrix(complex_operation_matrix),
                                                                                    previous_state)))

            else:
                complex_operation_matrix = np.identity(len(state_sequence.states[-1]), dtype=complex)
                for (i, operation) in enumerate(t_op):
                    if isinstance(operation, Gate) or isinstance(operation, List):
                        if len(state_sequence.measured_states) > 0:
                            raise Exception('Gates after measurement are not supported.')

                        previous_state = state_sequence.states[-1]
                        next_state = state_sequence.add_state()

                        if isinstance(operation, Gate) and operation.oracle_value is None:
                            qbit_indices = get_qbit_indices([q.get_identifier() for q in self.qbits], operation.arguments)

                            if not are_qbits_adjacent(qbit_indices):
                                state_operation = swap_transform_non_adjacent_gate(operation.matrix,
                                                                                qbit_indices,
                                                                                self.num_qbits)
                            else:
                                state_operation = identity_pad_gate(operation.matrix
                                                                    if not are_qbits_reversed(qbit_indices)
                                                                    else operation.matrix_swapped,
                                                                    qbit_indices,
                                                                    self.num_qbits)
                            # print("state_equals in circuit.py:", state_equals(next_state,
                            #                             matrix_vector_multiplication(to_complex_matrix(state_operation),
                            #                                                         previous_state)))
                            # print("state_operation:", state_operation)
                            # print("state_operation_type:", type(state_operation))
                            self.solver.add(state_equals(next_state,
                                                        matrix_vector_multiplication(to_complex_matrix(state_operation),
                                                                                    previous_state)))
                    #     elif isinstance(operation, Gate) and operation.oracle_value is not None:
                #         self.solver.add(state_equals_phase_oracle(previous_state, next_state, operation.oracle_value))
                #     else:
                #         state_operation = identity_pad_gate(I_matrix, [0], self.num_qbits)

                #         for operation_element in operation:
                #             qbit_indices = get_qbit_indices([q.get_identifier() for q in self.qbits],
                #                                             operation_element.arguments)

                #             if not are_qbits_adjacent(qbit_indices):
                #                 state_operation = swap_transform_non_adjacent_gate(operation_element.matrix,
                #                                                                    qbit_indices,
                #                                                                    self.num_qbits)
                #             else:
                #                 state_operation = np.matmul(identity_pad_gate(operation_element.matrix
                #                                                               if not are_qbits_reversed(qbit_indices)
                #                                                               else operation_element.matrix_swapped,
                #                                                               qbit_indices,
                #                                                               self.num_qbits),
                #                                             state_operation)

                #         self.solver.add(state_equals(next_state,
                #                                      matrix_vector_multiplication(to_complex_matrix(state_operation),
                #                                                                   previous_state)))
                # elif isinstance(operation, Measurement):
                #     previous_state = state_sequence.states[-1]
                #     exists_measurement_state = len(state_sequence.measured_states) > 0

                #     if isinstance(operation.arguments, QbitVal):
                #         measurement_states = state_sequence.add_measurement_state()

                #         qbit_index = get_qbit_indices([q.get_identifier() for q in self.qbits], [operation.arguments])[0]

                #         for (j, measurement_state) in enumerate(measurement_states):
                #             measurement_operation = identity_pad_gate(zero_measurement
                #                                                       if j % 2 == 0
                #                                                       else one_measurement,
                #                                                       [qbit_index],
                #                                                       self.num_qbits)

                #             if not exists_measurement_state:
                #                 self.solver.add(
                #                     state_equals(measurement_state,
                #                                  matrix_vector_multiplication(to_complex_matrix(measurement_operation),
                #                                                               previous_state)))
                #             else:
                #                 for state_before_element in previous_state:
                #                     self.solver.add(
                #                         state_equals(measurement_state,
                #                                      matrix_vector_multiplication(to_complex_matrix(measurement_operation),
                #                                                                   state_before_element)))
                #     else:
                #         measurement_states = state_sequence.add_measurement_state(len(operation.arguments))

                #         qbit_indices = get_qbit_indices([q.get_identifier() for q in self.qbits], operation.arguments)

                #         num_digits = len('{0:b}'.format(len(measurement_states))) - 1
                #         binary_format = '{0:0' + str(num_digits) + 'b}'

                #         if measurement_branch is not None:
                #             state_sequence.states[-1] = [measurement_states[measurement_branch]]
                #             measurement_states = state_sequence.states[-1]

                #         for (j, measurement_state) in enumerate(measurement_states):
                #             bit_vector = binary_format.format(j if measurement_branch is None else measurement_branch)

                #             measurement_ops = []

                #             for b in bit_vector:
                #                 if b == '0':
                #                     measurement_ops.append(zero_measurement)
                #                 else:
                #                     measurement_ops.append(one_measurement)

                #             combined_measurement = kron(measurement_ops)

                #             measurement_operation = identity_pad_gate(combined_measurement,
                #                                                       qbit_indices,
                #                                                       self.num_qbits)

                #             if not exists_measurement_state:
                #                 # First measured state
                #                 self.solver.add(
                #                     state_equals(measurement_state,
                #                                  matrix_vector_multiplication(to_complex_matrix(measurement_operation),
                #                                                               previous_state)))
                #             else:
                #                 # Existing measured states
                #                 raise Exception('No multi-measurement after other measurements.')
                # else:
                #     raise Exception('Unsupported operation. Has to be either gate or measurement.')

        # 4.1 Repair synthesis:
        if self.final_qbits is not None and synthesize_repair is True:
            raise Exception('State model does not support repair')

        # # 4.2 Final state qbits
        # if self.final_qbits is not None:
        #     final_state_definition = complex_kron_n_ary([qbit.to_complex_list() for qbit in self.final_qbits])
        #     if len(state_sequence.measured_states) == 0:
        #         self.solver.add(state_equals(state_sequence.states[-1], final_state_definition))
        #     else:
        #         # build disjunction for the different measurement results
        #         disjunction_elements = []

        #         for final_state in state_sequence.states[-1]:
        #             disjunction_elements.append(state_equals(final_state, final_state_definition))

        #         self.solver.add(Or(disjunction_elements))
            

        # 5 Call solver
        new_constraint= self.solver.sexpr()
        # print("new_constraint:", new_constraint)
        new_sexpr = ""
        for line in new_constraint.split("\n"):
            if "distinct" in line:
                line = line.replace("distinct", "not (=")
                line = line + ")"+"\n"
            if "declare-fun sin" in line:
                line = ""
            if "declare-fun cos" in line:
                line = ""
            new_sexpr = new_sexpr + line
        # print("circuit.py generate constraint.smt2!!!!!!!!!!!!")
        with open("test/temp_file/constraint.smt2", "w+") as file:
            file.write(new_sexpr)
            file.write("\n(check-sat)")
            file.write("\n(get-model)")

        temp_file = NamedTemporaryFile(mode='w+b', suffix='.smt2', delete=False)

        with open(temp_file.name, "w") as text_file:
            text_file.write(new_sexpr)
            text_file.write("\n(check-sat)")
            text_file.write("\n(get-model)")

        qbit_identifiers = [qbit.get_identifier() for qbit in self.qbits]

        dreal_path = '/opt/dreal/4.21.06.2/bin/dreal'
        z3_path = '/usr/local/bin/z3'
        delta = 0.05
        command = [dreal_path, '--precision', str(delta), temp_file.name] \
            if not isinstance(state_sequence.qbits[0], RQbitVal) else [z3_path, temp_file.name]

        # command = [dreal_path, '--precision', str(delta), "test/temp_file/constraint.smt2"] \
        #    if not isinstance(state_sequence.qbits[0], RQbitVal) else [z3_path, "test/temp_file/constraint.smt2"]

        result = subprocess.run(command, capture_output=True, timeout=1000)
        

        end_full = time.time()
        time_full = end_full - start_full
        return result, time_full


def _has_boolean_gates_only(program):
    for (i, gate) in enumerate(program):
        if gate.name not in ['I', 'X', 'SWAP', 'CNOT', 'CCX']:
            return False

    return True
