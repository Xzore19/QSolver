
from qiskit import Aer, transpile, QuantumCircuit


def normalize(state):
    abs_state = [abs(x)**2 for x in state]
    normalize_state = [i/sum(abs_state)**0.5 for i in state]
    return normalize_state


def check_assertion(qc):
    delta = 0.005
    measure_time = 10000
    qc.measure([0, 1], [0, 1])
    simulator = Aer.get_backend('aer_simulator')
    compiled_circuit = transpile(qc, simulator)
    job = simulator.run(compiled_circuit, shots=measure_time).result().get_counts()

    temp_dir = {}
    for temp in job.keys():
        temp_dir[int(temp, 2)] = job.get(temp, 0)/measure_time
        
    assert temp_dir.get(0, 0) < 0.104+delta
    assert temp_dir.get(1, 0) < 0.2432+delta
    print("Assertion SAT!!!!!!!")
    

def quantum_program(qc):
    qc.z(0)
    qc.x(1)
    qc.h(1)
    qc.cx(1, 0)

    check_assertion(qc)
    

if __name__ == "__main__":
    qc = QuantumCircuit(2,2)
    norm_state = normalize([(-0.10091379774662737+0.25461014451470004j), (0.3019933774108301-0.6286493458200686j), (0.5304332307391998-0.3726949277426501j), -0.007367050772681832j])
    qc.initialize(norm_state)
    quantum_program(qc)
    