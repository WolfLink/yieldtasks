import qsearch
from qsearch import unitaries, advanced_unitaries
from timeit import default_timer as timer

from yieldtasks_qsearch2 import synthesize
from yieldtasks import MPQueue

if __name__ == "__main__":
    with qsearch.Project("benchmarks") as project:
        compilations = [
                unitaries.qft(4),
                unitaries.qft(8),
                unitaries.fredkin,
                unitaries.toffoli,
                unitaries.peres,
                unitaries.logical_or,
                advanced_unitaries.mirogate,
                advanced_unitaries.HHL,
                ]
        mq = MPQueue()

        opt = qsearch.Options()
        opt.set_defaults(**qsearch.standard_defaults)
        opt.set_smart_defaults(**qsearch.standard_smart_defaults)

        def opt_with_target(target):
            newopt = opt.copy()
            newopt.target = target
            return newopt

        optionlist = [opt_with_target(target) for target in compilations]

        # run the benchmarks script with default settings 10x and average the timing results
        # reported times are between 0.1s and 5s on my 2018 Macbook Pro

        num_repetitions = 10
        start = timer()

        for _ in range(num_repetitions):
            mq.map(synthesize, optionlist)

        end = timer()

        print(f"Test suite took {end-start}s total so {(end-start)/num_repetitions}s on average.")
