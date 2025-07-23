import subprocess
from tqdm import tqdm
import os

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

def run_file(qubit_num, gate_num):
    flag_name = ["i", "ni", "e", "ne", "la", "le"]
    result_fold = "result_for_different_size/"+ str(gate_num)
    if not os.path.exists(result_fold):
        os.makedirs(result_fold)

    for flag in flag_name:
        filename = "different_size/"+ str(gate_num)+"/" + str(flag) + "_" + str(qubit_num) + ".txt"
        result_file = result_fold + "/" + str(flag) + "_" + str(qubit_num) + ".txt"
        run_benchmark(qubit=qubit_num, filename=filename, result_file=result_file)




if __name__ == "__main__":
    # for qubit_num in tqdm(range(1,4), desc="Processing", unit="iteration"):
    #     for gate_num in [5,10,20]:
    #         run_file(qubit_num=qubit_num, gate_num=gate_num)


    flags = ["i", "ni", "la", "le", "e"]
    # test_case = [[#gate_num, #qubit_num, #flag]]
    test_case = [[20,3,1],[20,3,2],[20,3,3],[20,3,4]]

    for i in tqdm(test_case, desc="Processing", unit="iteration"):
        qubit_num = i[1]
        gate_num = i[0]
        flag = flags[i[2]]

        result_fold = "result_for_different_size/"+ str(gate_num)
        filename = "different_size/"+ str(gate_num)+"/" + str(flag) + "_" + str(qubit_num) + ".txt"
        result_file = result_fold + "/" + str(flag) + "_" + str(qubit_num) + ".txt"
        run_benchmark(qubit=qubit_num, filename=filename, result_file=result_file)
