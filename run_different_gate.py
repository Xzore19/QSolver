import subprocess
from tqdm import tqdm
import os

target_gates_lib = ["h", "x", "ccx", "ccz", "s", "z", "y", "sdg", "t", "tdg", "ch", "u",\
                    "cs", "cz", "csdg", "p", "cp", "rx", "crx", "ry",\
                    "cry", "rz", "crz", "swap", "iswap", "cswap", "sx", "sxdg", "csx"]

single_qubit_gates = ["h","x", "s", "z", "y", "sdg", "t", "tdg", "sx", "sxdg", "p", "rx", "ry", "rz", "u"]

double_qubit_gates = ["ch", "cs", "cz", "csdg", "cx", "swap", "iswap", "cp", "crx", "cry", "crz"]

def run_benchmark(qubit, 
                  filename, 
                  result_file,
                  result=10, 
                  assertion=True, 
                  method = "m"):
    command = ["python", "QCS.py", "-q", str(qubit), "-r", str(result), "-a", str(assertion), "-m", method, filename]

    result = subprocess.run(command, stdout=subprocess.PIPE,stderr=subprocess.PIPE, text=True)

    with open(result_file, "w") as file:
        file.write(result.stdout)
        file.write(result.stderr)

def run_file(qubit_num, gate_name):
    flag_name = ["i", "ni", "e", "la", "le"]
    result_fold = "result_for_different_gates/"+ str(gate_name)
    if not os.path.exists(result_fold):
        os.makedirs(result_fold)

    for flag in flag_name:
        filename = "different_gates/"+ str(gate_name)+"/" + str(gate_name)+ "_" + str(flag) + "_" + str(qubit_num) + ".txt"
        result_file = result_fold + "/" + str(gate_name)+ "_" + str(flag) + "_" + str(qubit_num) + ".txt"
        run_benchmark(qubit=qubit_num, filename=filename, result_file=result_file)




if __name__ == "__main__":
    # run all the different quantum gates
    # for gate_index in tqdm(range(1), desc="Processing", unit="iteration"):
    #     gate_name = target_gates_lib[gate_index]
    #     if gate_name in single_qubit_gates:
    #         for qubit_num in range(1,5):
    #             run_file(qubit_num, gate_name)
    #     elif gate_name in double_qubit_gates:
    #         for qubit_num in range(2,5):
    #             run_file(qubit_num, gate_name)
    #     else:
    #         for qubit_num in range(3,5):
    #             run_file(qubit_num, gate_name)


    # run a specific program
    flags = ["i", "ni", "la", "le", "e", "ne"]
    # test_case = [[#qubit_num, #flag, #quantum_gate]]
    test_case = [[1,0,"crz"]]

    for i in tqdm(test_case, desc="Processing", unit="iteration"):
        qubit_num = i[0]
        gate_name = i[2]
        flag = flags[i[1]]

        filename = "different_gates/"+ str(gate_name)+"/" + str(gate_name)+ "_" + str(flag) + "_" + str(qubit_num) + ".txt"
        result_fold = "result_for_different_gates/"+ str(gate_name)
        result_file = result_fold + "/" + str(gate_name)+ "_" + str(flag) + "_" + str(qubit_num) + ".txt"
        run_benchmark(qubit=qubit_num, filename=filename, result_file=result_file)
    
