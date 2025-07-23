from string import Template
import subprocess

# flag: ==, !=, >, <, in, not_in

basic_import = """
from qiskit import Aer, transpile, QuantumCircuit
"""

normalize_template = """
def normalize(state):
    abs_state = [abs(x)**2 for x in state]
    normalize_state = [i/sum(abs_state)**0.5 for i in state]
    return normalize_state
"""

def measure_flag(qubit_num, target_prob, flag):
    if flag in ["in", "not_in"]:
        measure_string = f"    qc.measure({target_prob[0]}, {target_prob[1]})"
    else:
        measure_qubit = [i for i in range(qubit_num)]
        measure_string = f"    qc.measure({measure_qubit}, {measure_qubit})"
    return measure_string

def process_flag(target_prob, flag):
    temp = {}
    if flag in ["in", "not_in"]:
        process_string = f"""
    temp_dir = {temp}
    for temp in job.keys():
        temp_dir[temp[::-1]] = job[temp]
    result_dir, sum_prob = {temp}, 0
    for temp in temp_dir.keys():
        measure_result = ""
        for i in {target_prob[1]}:
            measure_result += temp[i]
        if result_dir.get(measure_result, False):
            result_dir[measure_result] += temp_dir[temp]/measure_time
        else:
            result_dir[measure_result] = temp_dir[temp]/measure_time
    print(result_dir)
    for target in {target_prob[2]}:
        sum_prob += result_dir.get(target, 0)
        """
    else:
        process_string = f"""
    temp_dir = {temp}
    for temp in job.keys():
        temp_dir[int(temp, 2)] = job.get(temp, 0)/measure_time
    print(temp_dir)
        """
    return process_string

def assert_flag(target_prob, flag):
    if flag == "in":
        assert_string = "    assert sum_prob > 0.95-delta\n"
    elif flag == "not_in":
        assert_string = "    assert sum_prob < 0.05+delta\n"
    elif flag == ">":
        assert_string = ""
        for [target, prob] in target_prob:
            assert_string += f"    assert temp_dir.get({target}, 0) > {prob}-delta\n"
    elif flag == "<":
        assert_string = ""
        for [target, prob] in target_prob:
            assert_string += f"    assert temp_dir.get({target}, 0) < {prob}+delta\n"
    elif flag == "==":
        assert_string = ""
        for target, prob in enumerate(target_prob):
            assert_string += f"    assert {prob}+delta > temp_dir.get({target}, 0) > {prob}-delta\n"
    elif flag == "!=":
        assert_string = ""
        for target, prob in enumerate(target_prob):
            assert_string += f"    assert not ({prob}+delta > temp_dir.get({target}, 0) > {prob}-delta)\n"
    else:
        assert_string = ""
    assert_string += "    print(\"Assertion SAT!!!!!!!\")"
    return assert_string




def check_assertion_generator(qubit_num, target_prob, flag, delta, measure_time):
    program_template = Template("""
def check_assertion(qc):
$initial_part
$measure_part
    simulator = Aer.get_backend('aer_simulator')
    compiled_circuit = transpile(qc, simulator)
    job = simulator.run(compiled_circuit, shots=measure_time).result().get_counts()
$process_part
$assert_part
    """)

    initial_string = f"    delta = {delta}\n"
    initial_string += f"    measure_time = {measure_time}"

    measure_string = measure_flag(qubit_num, target_prob, flag)

    process_string = process_flag(target_prob,flag)

    assert_string = assert_flag(target_prob, flag)

    generated_program = program_template.substitute(initial_part=initial_string,
                                                    measure_part=measure_string,
                                                    process_part=process_string,
                                                    assert_part=assert_string)
    return generated_program


def quantum_program_generator(gates):
    program_template = Template("""
def quantum_program(qc):
$gate_part
$assert_part
    """)
    gate_string = ""
    for gate in gates:
        gate_string += "    "
        gate_string += "qc."+gate
        gate_string += "\n"

    assert_string = "    check_assertion(qc)"
    generated_program = program_template.substitute(gate_part=gate_string,
                                                    assert_part=assert_string)
    return generated_program


def run_generator(qubit_num, state):
    program_template = Template("""
if __name__ == "__main__":
$qc_part
$initial_part
    quantum_program(qc)
    """)

    qc_string = f"    qc = QuantumCircuit({qubit_num},{qubit_num})"
    initial_string = f"    norm_state = normalize({state})\n"
    initial_string += "    qc.initialize(norm_state)"
    generated_program = program_template.substitute(qc_part=qc_string, initial_part=initial_string)
    return generated_program




def assertion_program_generator(qubit_num, gates, target_prob, flag, state, delta, measure_times, filename):
    program = (basic_import + "\n" + normalize_template + "\n"
               + check_assertion_generator(qubit_num, target_prob, flag, delta, measure_times) + "\n"
               + quantum_program_generator(gates) + "\n"
               + run_generator(qubit_num, state))

    with open(filename, "w") as file:
        file.write(program)

    # print(f"Assertion program has generated in {filename}")
    return program

def run_assertion(result_index, qubit_num, gates, target_prob, flag, state, delta, measure_times):
    num_flag = len(gates)
    temp_gate = []
    for nf in range(num_flag):
        temp_gate += gates[nf]
        assert_file = f"assert_result/assertion_program_{result_index}_{nf}.py"
        assertion_program_generator(qubit_num=qubit_num,
                                    gates= temp_gate,
                                    target_prob= target_prob[nf],
                                    flag=flag[nf],
                                    state= state,
                                    delta=delta,
                                    measure_times=measure_times,
                                    filename=assert_file)
        command = ["python", assert_file]

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stderr:
            # print("Assertion not SAT!!!!!!!")
            # print(result.stderr)
            return False
        # print(result.stdout)
    else:
        return True



if __name__ == "__main__":
    qubit_num = 3
    gates = ["h(0)", "cx(0,1)"]
    target_prob = [[4, 0.9]]
    flag = ">"
    state = [-0.015729623549462744j, -0.015729623549462748j, -0.016117108109441374j, -0.016117108109441378j,
             (0.5 - 0.5031094182778674j), (0.5000000000000001 - 0.4999999999999574j), -0.016534716697753544j,
             -0.016534716697753547j]
    delta = 0.05
    measure_times = 1000
    filename = "assertion_program.py"

    assertion_program_generator(qubit_num, gates, target_prob, flag, state, delta, measure_times, filename)