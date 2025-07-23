from assertion_generation import assertion_program_generator
from constraint_generator import constraint_generator
from quantum_solver import quantum_constraint_solver
import subprocess

def main(qubit_num, gate_num, filename, measure_times):
    flag, gates, target_prob, delta = constraint_generator(qubit_num=qubit_num, gate_num=gate_num)
    print("gates:", gates)
    print("target_prob:", target_prob)
    print("flag:", flag)
    result, time, _ = quantum_constraint_solver(qubit_num, gates, target_prob, flag)

    assertion_program_generator(qubit_num=qubit_num,
                                gates=gates,
                                target_prob=target_prob,
                                flag=flag,
                                state=result,
                                delta=delta,
                                measure_times=measure_times,
                                filename=filename)
    
    command = ['python', filename]
    try:
        result = subprocess.run(command, capture_output=True, timeout=1000)
        print("Assertion SAT!")
    except AssertionError:
        print("Assertion Error!")
    




if __name__ == "__main__":
    main(qubit_num=2,
         gate_num=4,
         filename="test/assertion_test/assert.py",
         measure_times= 10000)
    