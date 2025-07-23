
from qiskit import Aer, transpile, QuantumCircuit


def normalize(state):
    abs_state = [abs(x)**2 for x in state]
    normalize_state = [i/sum(abs_state)**0.5 for i in state]
    return normalize_state


def check_assertion(qc):
    delta = 0.05
    measure_time = 100000
    qc.measure([0, 1], [0, 1])
    simulator = Aer.get_backend('aer_simulator')
    compiled_circuit = transpile(qc, simulator)
    job = simulator.run(compiled_circuit, shots=measure_time).result().get_counts()

    temp_dir = {}
    for temp in job.keys():
        temp_dir[int(temp, 2)] = job.get(temp, 0)/measure_time
    print(temp_dir)
        
    assert temp_dir.get(1, 0) > 0.2814-delta
    print("Assertion SAT!!!!!!!")
    

def quantum_program(qc):
    qc.rz(0.39269908169872414,0)
    qc.h(0)
    qc.cp(0.39269908169872414,0,1)
    qc.ry(1.5707963267948966,0)
    qc.z(0)
    qc.x(0)

    check_assertion(qc)
    

if __name__ == "__main__":
    qc = QuantumCircuit(2,2)
    norm_state = normalize([(-0.04875961242623633-0.3180644663008133j), (0.575422103254231-0.5185454686779902j), (-0.05440452023755672-0.22049711054640853j), (0.45142053830047235-0.21389176524716888j)])
    qc.initialize(norm_state)
    quantum_program(qc)
    