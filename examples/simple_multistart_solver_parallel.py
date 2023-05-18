from qsearch.solvers import *
from qsearch.multistart_solvers import optimize_worker
import multiprocessing as mp

class SimpleMultistartSolver(Solver):
    def __init__(self, num_threads=16):
        self.threads = num_threads
        self.ctx = mp.get_context('fork') if sys.platform != 'win32' else mp.get_context()

    def solve_for_unitary(self, circuit, options, x0=None):
        options.inner_solver = default_solver(options)
        U = options.target
        n = circuit.num_inputs
        initial_samples = [np.random.rand(n)*2*np.pi for _ in range(self.threads)]
        error_func = options.objective.gen_error_func(circuit, options)
        q = self.ctx.Queue()
        processes = []
        rets = []
        for x0 in initial_samples:
            p = self.ctx.Process(target=optimize_worker, args=(circuit, options, q, x0, error_func))
            processes.append(p)
            p.start()
        for p in processes:
            ret = q.get()
            rets.append(ret)
        for p in processes:
            p.join()


        best_found = np.argmin([r[0] for r in rets])
        best_val = rets[best_found][0]
        xopt = rets[best_found][1]

        return (circuit.matrix(xopt), xopt)
