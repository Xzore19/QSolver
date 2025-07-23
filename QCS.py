from optparse import OptionParser 
import os
import sys
from quantum_solver import quantum_constraint_solver
from qiskit_plugin import process_file
from assertion_generation import run_assertion

print("Quantum Constraint Solver with dreal")

usage = "usage: %prog [options] <path to a *.txt file>"
parser = OptionParser(usage=usage)

parser.add_option("-q", "--number", dest="qbit_num", type="int", help="Circuit qubit number", default=3)
parser.add_option("-r", "--result", dest="result_num", type="int", help="Max Generated Result Number", default=10)
parser.add_option("-a", "--assert", dest="assert_flag", help="Build assertion for results or not", default=True)
parser.add_option("-m", "--method", dest="calculation_method", type="str", help="Generate SMT for each gate(-s) or for combinational gate(-m)", default="m")
# parser.add_option("-s", "--multiple", dest="multiple_flag", type="int", help="Add multiple flags in detail text file", default=1)

(options, args) = parser.parse_args()

filename = os.path.abspath(args[0])

gate_list, target_prob, flag = process_file(filename)

for i in range(len(gate_list)):
    print("gates list:", gate_list[i])
    print("target probability:", target_prob[i])
    print("flag:", flag[i])

print("Exploring.......................")

result = None

if options.calculation_method == "m":
    matrix_method = True
else:
    matrix_method = False

try:
    existing_result, expected_results = [], []
    while len(existing_result) < options.result_num:
        result, time, already_result = quantum_constraint_solver(num_qbits=options.qbit_num,
                                                                 operations=gate_list,
                                                                 prob_constraint=target_prob,
                                                                 flag=flag,
                                                                 unaccepted_results=existing_result,
                                                                 matrix_method=matrix_method)
        existing_result.append(already_result)
        expected_results.append(result)
        print(f"Generated time:", time)
        # print(f"quantum sat result {len(expected_results)}:\n", result)
        # if options.assert_flag:
        #     delta, measure_times = 0.05, 100000
        #     run_assertion(result_index= len(expected_results),
        #                     qubit_num=options.qbit_num,
        #                     gates= gate_list,
        #                     target_prob= target_prob,
        #                     flag=flag,
        #                     state= result,
        #                     delta=delta,
        #                     measure_times=measure_times)

        # assertion verification
        delta, measure_times = 0.05, 100000
        assert_result = run_assertion(result_index= 1,
                            qubit_num=options.qbit_num,
                            gates= gate_list,
                            target_prob= target_prob,
                            flag=flag,
                            state= result,
                            delta=delta,
                            measure_times=measure_times)
        if assert_result:
            print(f"quantum sat result:\n", result)
            for al in range(len(gate_list)):
                print(f"Assertion program has generated in assert_result/assertion_program_1_{al}.py")
            print("Assertion SAT!!!!!!!")
            print(f"Generated result number: {len(expected_results)}")
            break



except ImportError:
    sys.exit(1)

if result is None or result == True:
    sys.exit(0)
else:
    sys.exit(1)