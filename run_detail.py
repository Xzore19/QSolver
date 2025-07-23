import subprocess
from tqdm import tqdm
import os

def run_benchmark(qubit, 
                  filename, 
                  result_file,
                  result=5, 
                  assertion=True, 
                  method = "m"):
    command = ["python", "QCS.py", "-q", str(qubit), "-r", str(result), "-a", str(assertion), "-m", method, filename]

    result = subprocess.run(command, stdout=subprocess.PIPE,stderr=subprocess.PIPE, text=True)

    with open(result_file, "w") as file:
        file.write(result.stdout)
        file.write(result.stderr)

if __name__ == "__main__":
    filename = "detail.txt"
    result_file = "detail_result.txt"
    run_benchmark(qubit=3, filename=filename, result_file=result_file)