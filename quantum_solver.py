import ast
from z3 import And, Not, Or, RealVal
from symqv.expressions.qbit import Qbits
from symqv.models.circuit import Circuit
from qiskit_plugin import operations_to_program
from symqv.expressions.complex import Complexes
import subprocess


# SMT encoding for ==
def eq_constraint(prob_constraint, symbolic_state_list, circuit):
    for index, prob in enumerate(prob_constraint):
        target_state = symbolic_state_list[index]
        circuit.solver.add(target_state.r ** 2 + target_state.i ** 2 == RealVal(prob))
    return circuit

# SMT encoding for !=
def neq_constraint(prob_constraint, symbolic_state_list, circuit):
    for index, prob in enumerate(prob_constraint):
        target_state = symbolic_state_list[index]
        circuit.solver.add(Not(target_state.r ** 2 + target_state.i ** 2 == RealVal(prob)))
    return circuit

# SMT encoding for >
def gt_constraint(prob_constraint, symbolic_state_list, circuit):
    for single in prob_constraint:
        target_state = symbolic_state_list[single[0]]
        circuit.solver.add(target_state.r ** 2 + target_state.i ** 2 > single[1])
    return circuit

# SMT encoding for <
def lt_constraint(prob_constraint, symbolic_state_list, circuit):
    for single in prob_constraint:
        target_state = symbolic_state_list[single[0]]
        circuit.solver.add(target_state.r ** 2 + target_state.i ** 2 < single[1])
    return circuit

# for quantum register index != classical register index
# not finish
def reorder_string(s, order):
    s = str(s)
    if len(s) == 1:
        return s
    # reordered = [''] * len(s)
    # for i, new_position in enumerate(order):
    #     reordered[new_position] = s[len(s)-1-i]
    # return ''.join(reordered)
    return s

# SMT encoding for in and not_in
def result_constraint(measured_qubit, symbolic_state_list, num_qbits, target_result, flag):
    num_measured = len(measured_qubit)
    state_list = [format(number, f'0{num_qbits}b') for number in range(2**num_qbits)]
    s_part, u_part = [], []
    for j in state_list:
        for k in range(num_measured):
            if j[measured_qubit[num_measured-k-1]] == target_result[k]:
                continue
            else:
                u_part.append(int(j, 2))
    u_part = list(set(u_part))
    s_part = list(set([number for number in range(2**num_qbits)])-set(u_part))
    u_state, s_state = [], []
    for i in u_part:
        u_state.append(symbolic_state_list[i])
    for i in s_part:
        s_state.append(symbolic_state_list[i])

    if flag == "in":
        return And([And(target.r == 0, target.i == 0) for target in u_state])
    elif flag == "not_in":
        return And([And(target.r == 0, target.i == 0) for target in s_state])
    
    
# create SMT file for in and not_in
def measure_constraint(prob_constraint, symbolic_state_list, num_qubits, flag):
    measured_qubit, classicalreg, target_state = prob_constraint[0], prob_constraint[1], prob_constraint[2]
    new_target_state = []
    for i in target_state:
        new_target_state.append(reorder_string(i, classicalreg))
    return Or([result_constraint(measured_qubit, symbolic_state_list, num_qubits, target, flag) for target in new_target_state])
    
# for some fixed state or fixed qubit value
def locked_state_constraint(measured_qubit, num_qbits):
    index = []
    state_list = [format(number, f'0{num_qbits}b') for number in range(2**num_qbits)]
    for i in measured_qubit:
        index.append(int(i[1:]))
    
    for k in index:
        o_part, z_part = [], []
        for j in state_list:
            if j[k] == "0":
                z_part.append(int(j, 2))
            else:
                o_part.append(int(j, 2))
        o_state = Complexes([f"psi_{0}_{i}" for i in o_part])
        z_state = Complexes([f"psi_{0}_{i}" for i in z_part])
        return Or(And([And(target.r == 0, target.i == 0) for target in o_state]),
                  And([And(target.r == 0, target.i == 0) for target in z_state]))

# only generate quantum state without superposition
def light_concolic(num_qbits):
    state_list = [f"psi_{0}_{i}" for i in range(2 ** num_qbits)]
    c_state = Complexes(state_list)
    return Or([And(target.r == 0, target.i == 0) for target in c_state])

# check measurement whether in quantum state list 
def check_measure(operation_string, unmeasure):
    for i in unmeasure:
        if i in operation_string:
            return True
    return False

def quantum_constraint_solver(num_qbits, operations, prob_constraint, flag, unaccepted_results=None, concolic_mode = "n", matrix_method = True):

    qbit_name = [f"q{i}" for i in range(num_qbits)]
    symbolic_qubit_list = Qbits(qbit_name)
    num_flag = len(operations)
    program_list = []
    index_list = []
    for nf in range(num_flag):
        num_operations = len(operations[nf])
        if operations[nf] == ['']:
            index_list.append(nf-1)
        else:
            index_list.append(nf)
            program = operations_to_program(num_qbits, operations[nf])
        measured_qubit = []
        new_program = []
        unmeasured = [i for i in qbit_name]
        for i in range(num_operations-1, -1, -1):
            if isinstance(program[i], list) and program[i][1] not in measured_qubit:
                measured_qubit.append(program[i][1])
                unmeasured = [item for item in qbit_name if item not in measured_qubit]
            else:
                target_qubit = program[i]
                if check_measure(str(program[i]), unmeasured):
                    new_program.append(program[i])
        
        new_program = [new_program[i] for i in range(len(new_program)-1, -1, -1)]
        program_list.append(new_program)

    num_program = len(program_list)
    circuit = Circuit(symbolic_qubit_list, program=program_list)
    # create a_i, b_i based on qubit number
    circuit.initialize([None for i in range(num_qbits)])

    for nf in range(num_flag):
        if matrix_method:
            final_state_list = [f"psi_{index_list[nf]+1}_{i}" for i in range(2 ** num_qbits)]
        else:
            final_state_list = [f"psi_{num_program}_{i}" for i in range(2 ** num_qbits)]
        initial_state_list = [f"psi_{index_list[nf]}_{i}" for i in range(2 ** num_qbits)]

        symbolic_initial_state = Complexes(initial_state_list)
        symbolic_state_list = Complexes(final_state_list)

        if locked_state_constraint(measured_qubit, num_qbits) is not None:
            circuit.solver.add(locked_state_constraint(measured_qubit, num_qbits))
        
        if concolic_mode == "l":
            circuit.solver.add(light_concolic(num_qbits))

        # check detail text file to create SMT file
        if flag[nf] == "==":
            circuit = eq_constraint(prob_constraint[nf], symbolic_state_list, circuit)
        elif flag[nf] == "!=":
            circuit = neq_constraint(prob_constraint[nf], symbolic_state_list, circuit)
        elif flag[nf] == ">":
            circuit = gt_constraint(prob_constraint[nf], symbolic_state_list, circuit)
        elif flag[nf] == "<":
            circuit = lt_constraint(prob_constraint[nf], symbolic_state_list, circuit)
        elif flag[nf] == "in" or flag[nf] == "not_in":
            circuit.solver.add(measure_constraint(prob_constraint[nf], symbolic_state_list, num_qbits, flag[nf]))
        

    initial_state_list = [f"psi_{0}_{i}" for i in range(2 ** num_qbits)]
    symbolic_initial_state = Complexes(initial_state_list)
        
    # duplicate result elimination module
    alphi = 0.0005
    if unaccepted_results != None:
        for un_result in unaccepted_results:
            constraint = []
            for key in symbolic_initial_state:
                temp_result_r = un_result[str(key.r)+" "]
                temp_result_i = un_result[str(key.i)+" "]
                if type(temp_result_r).__name__ == "list":
                    constraint.append(And(key.r > temp_result_r[0]-alphi, key.r < temp_result_r[1]+alphi))
                else:
                    constraint.append(Not(key.r == temp_result_r))
                if type(temp_result_i).__name__ == "list":
                    constraint.append(And(key.i > temp_result_i[0]-alphi, key.i < temp_result_i[1]+alphi))
                else:
                    constraint.append(Not(key.i == temp_result_i))
            circuit.solver.add(Not(And(constraint)))


    result, time_full = circuit.prove(overapproximation=False, matrix_method= matrix_method)

    # print("result:", result.stdout.decode("utf-8"))

    # output processing
    output = result.stdout.decode("utf-8")
    if "unsat" in output:
        print("-------------------- Unsat Constraint! --------------------")
        raise ValueError
    quantum_result = output.replace("define-fun", "").replace("() Real", "!").split("\n")[2:-2]

    result_dict = {}
    for obj in quantum_result:
        state_name, state_value = obj.split("!")
        state_name, state_value = state_name[4:], ast.literal_eval(state_value[1:-1])
        if state_name[4] == "0":
            result_dict[state_name] = state_value


    result_state = []
    for state_obj in initial_state_list:
        temp1, temp2 = result_dict.get(state_obj + ".r "), result_dict.get(state_obj + ".i ")
        if type(temp1).__name__ == "list":
            temp1 = temp1[0]
        if type(temp2).__name__ == "list":
            temp2 = temp2[0]
        result_state.append(complex(temp1, temp2))

    return result_state, time_full, result_dict


if __name__ == "__main__":
    result, time, _ = quantum_constraint_solver(2, 
                                                ['cz(0, 1)', 'rx(0.7853981633974483, 0)', 'cx(1, 0)', 'swap(1, 0)'], 
                                                [0, 0.36363636363636365, 0.18181818181818182, 0.45454545454545453], 
                                                flag="!=")
    print(result)