from qsearch.solvers import *
from qsearch.multistart_solvers import optimize_worker
import multiprocessing as mp

class SimpleMultistartSolver(Solver):
    def __init__(self, num_threads=16):
        self.threads = num_threads

    def solve_for_unitary(self, circuit, options, x0=None):
        options.inner_solver = default_solver(options)
        U = options.target
        n = circuit.num_inputs
        initial_samples = [np.random.rand(n)*2*np.pi for _ in range(self.threads)]
        error_func = options.objective.gen_error_func(circuit, options)
        processes = []
        rets = []

        for x0 in initial_samples:
            _, xopt = options.inner_solver.solve_for_unitary(circuit, options, x0)
            rets.append((error_func(xopt), xopt))

        best_found = np.argmin([r[0] for r in rets])
        best_val = rets[best_found][0]
        xopt = rets[best_found][1]

        return (circuit.matrix(xopt), xopt)
