from yieldtasks import *

import qsearch
from qsearch import *
import heapq

def solve(circuit, options):
    solver = qsearch.solvers.default_solver(options)
    return solver.solve_for_unitary(circuit, options)

def solve_multistart(circuit, options, multistarts=16):
    sub_solutions = yield taskmap(solve, [circuit for _ in range(multistarts)], options)
    best_sol = sub_solutions[0]
    error_func = options.objective.gen_error_func(circuit, options)
    best_val = error_func(best_sol[1])
    for sol in sub_solutions[1:]:
        new_val = error_func(sol[1])
        if new_val < best_val:
            best_sol = sol
            best_val = new_val
    return best_sol


def solver_wrap(tup, options):
    step, depth, weight = tup
    result = yield taskwrap(solve_multistart, options.backend.prepare_circuit(step, options), options)
    return (step, result[0], depth, weight) 

def synthesize(options):
    options.make_required("target")
    U = options.target
    
    weight_limit = options.weight_limit
    h = options.heuristic
    qudits = int(np.round(np.log(np.shape(U)[0])/np.log(options.gateset.d)))
    if options.gateset.d**qudits != np.shape(U)[0]:
        raise ValueError("The target matrix of size {} is not compatible with qudits of size {}.".format(np.shape(U)[0], self.options.gateset.d))

    I = gates.IdentityGate(d=options.gateset.d)
    initial_layer = options.gateset.initial_layer(qudits)
    branching_factor = options.gateset.branching_factor(qudits)

    if branching_factor <= 0:
        root = initial_layer
        result = options.solver.solve_for_unitary(options.backend.prepare_circuit(root, options), options)
        return {"structure":root, "parameters":result[1]}

    root = ProductGate(initial_layer)
    result = options.solver.solve_for_unitary(options.backend.prepare_circuit(root, options), options)
    best_value = options.objective.gen_eval_func(root, options)(result[1])
    best_pair = (root, result[1])
    queue = [(h(*best_pair, 0, options), 0, best_value, -1, result[1], root)]
    tiebreaker = 1

    while len(queue) > 0:
        if best_value < options.threshold:
            queue = []
            break
        popped = heapq.heappop(queue)
        new_steps = [(successor[0], popped[1], successor[1]) for successor in options.gateset.successors(popped[5])]

        results = yield taskmap(solver_wrap, new_steps, options=options)
        for step, result, current_weight, weight in results:
            current_value = options.objective.gen_eval_func(step, options)(result[1])
            new_weight = current_weight + weight
            if (current_value < best_value and (best_value >= options.threshold or new_weight <= best_weight)) or (current_value < options.threshold and new_weight < best_weight):
                best_value = current_value
                best_pair = (step, result[1])
                best_weight = new_weight
            if weight_limit is None or new_weight < weight_limit:
                heapq.heappush(queue, (h(step, result[1], new_weight, options), new_weight, current_value, tiebreaker, result[1], step))
                tiebreaker+=1
    return {"structure" : best_pair[0], "parameters" : best_pair[1]}



if __name__ == "__main__":
    mq = MPQueue()
    options = qsearch.Options()
    options.set_defaults(**standard_defaults)
    options.set_smart_defaults(**standard_smart_defaults)

    qft_opt = options.copy()
    qft_opt.target = qsearch.unitaries.qft(8)
    qft4_opt = options.copy()
    qft4_opt.target = qsearch.unitaries.qft(16)
    toff_opt = options.copy()
    toff_opt.target = qsearch.unitaries.toffoli

    #task = TaskList(CompileTask(qft_opt), CompileTask(toff_opt))
    #task = CompileTask(qft_opt)
    #output = mq.run(Partial(synthesize, qft_opt))
    output = mq.map(synthesize, [qft_opt, toff_opt])
    print("finished all tasks!")
    print(output)
