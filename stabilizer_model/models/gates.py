from z3 import And, Real, Sqrt

single_gates = {}

def dual(value, index):
    bin_value = bin(value)[2:]
    if len(bin_value) < index:
        bin_value = bin_value.zfill(index)
    tar_num = len(bin_value)-index
    target = str(1-int(bin_value[tar_num]))
    dual_value = bin_value[:tar_num] + target + bin_value[tar_num+1:]
    return int(dual_value, 2)


def h_process(solver, all_sym, target_z_state, gate_index):
    root2 = 1 / Sqrt(Real(2))
    for i in target_z_state:
        solver.add(all_sym[f"a_{gate_index+1}_{i}"] == 
                   root2 * (all_sym[f"a_{gate_index}_{i}"] + all_sym[f"a_{gate_index}_{dual(i)}"]))
        solver.add(all_sym[f"b_{gate_index+1}_{i}"] == 
                   root2 * (all_sym[f"b_{gate_index}_{i}"] + all_sym[f"b_{gate_index}_{dual(i)}"]))
        solver.add(all_sym[f"a_{gate_index+1}_{dual(i)}"] == 
                   root2 * (all_sym[f"a_{gate_index}_{i}"] - all_sym[f"a_{gate_index}_{dual(i)}"]))
        solver.add(all_sym[f"b_{gate_index+1}_{dual(i)}"] == 
                   root2 * (all_sym[f"b_{gate_index}_{i}"] - all_sym[f"b_{gate_index}_{dual(i)}"]))




if __name__ == "__main__":
    pass