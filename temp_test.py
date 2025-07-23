from quantum_solver import quantum_constraint_solver

if __name__ == "__main__":
    # flag = "in"
    # gates = ['x(1)', 'z(1)', 'h(1)']
    # target_prob = [[1], [1], ['0']]

    flag = "!="
    gates = ['cp(0.39269908169872414, 0, 2)', 'z(0)', 'rz(0.7853981633974483, 2)', 'rx(0.39269908169872414, 1)', 'rz(0.7853981633974483, 1)']
    target_prob = [0.019230769230769232, 0.04807692307692308, 0.14423076923076922, 0.18269230769230768, 0.14423076923076922, 0.19230769230769232, 0.19230769230769232, 0.07692307692307693]

    result, time, _ = quantum_constraint_solver(3, gates, target_prob, flag)
    print(result)