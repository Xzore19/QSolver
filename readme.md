## Installation

Python version: 3.9.18

There are three requirements to run. The Python packages are:

- z3-solver (for SMT sort declaration and syntax generation)
- pyparsing (needed for output parsing)
- numpy (for arithmetic)
- scipy (for optimization)

Also, the system runs on requires [dReal](http://dreal.github.io) to be installed and added to the path
in order for the solver to work.

Install Python packages:

    pip install z3-solver
    pip install pyparsing
    pip install numpy
    pip install scipy

Install dReal on Ubuntu:

    # 20.04
    sudo apt-get install curl
    curl -fsSL https://raw.githubusercontent.com/dreal/dreal4/master/setup/ubuntu/20.04/install.sh | sudo bash
    
    # 18.04
    sudo apt-get install curl
    curl -fsSL https://raw.githubusercontent.com/dreal/dreal4/master/setup/ubuntu/18.04/install.sh | sudo bash

Alternatively, make the shell script `install.sh` executable and run it:

    sudo chmod +x install.sh
    ./install.sh

## Examples for QSolver

    python QCS.py -q #qubit_num -r #max_result_num -a #assertion -m #method #filename

    - #qubit_num : the number of qubits in the target program
    - #max_result_num: the maximum number of dReal solver output results (default=10)
    - #assertion: build assertion for results or not", default=True
    - #method: generate SMT for each gate(-s)(todo) o for combinational gate(-m) (default="m")
    - #filename : target filename

    python run_different_gate.py

    python run_different_size.py

## Benchmark

    Experiments dataset in different_gates and different_size

## Results

    The output results are recorded in result_for_different_gates and result_for_different_size.

    The SMT file is recorded in test/temp_file/constraint.smt2

    The assertion program is recorded in assert_result/assertion_program_1_i.py

## Hyperparameter

    δ for dReal solver: in line 341 in symqv/models/circuit.py 

    maximum solving time for dReal solver: in line 348 in symqv/models/circuit.py 
        result = subprocess.run(command, capture_output=True, timeout=5000)

    ε for duplicate result elimination module: in line 167 in quantum_solver.py
        alphi = 0.0005

    δ for assertion program: in line 62 in QCS.py
