from z3 import Real, Tactic

class Circuit:
    def __init__(self, qubit_num, gates):
        self.qubit_num = qubit_num
        self.gates = gates
        self.state = [i for i in range(2**qubit_num)]
        self.all_symbolic = self.symbolic_generation(len(gates))
        self.solver = Tactic('qfnra-nlsat').solver()
        self.z_state = None
        self.o_state = None

    
    def symbolic_generation(self, gate_num):
        all_sym = {}
        for i in self.state:
            for j in range(gate_num + 1):
                all_sym[f"a_{j}_{i}"] = Real(f"a_{j}_{i}")
                all_sym[f"b_{j}_{i}"] = Real(f"b_{j}_{i}")
        return all_sym

    def target_z_state(self, target):
        # S_i_0
        z_state = []
        for val in self.state:
            bin_value = bin(val)[2:]
            if len(bin_value) < target:
                bin_value = bin_value.zfill(target)
            tar_num = len(bin_value)-target
            if bin_value[tar_num] == "0":
                z_state.append(val)
        return z_state