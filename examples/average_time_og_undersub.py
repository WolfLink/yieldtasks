import qsearch
from qsearch import unitaries, advanced_unitaries
from simple_multistart_solver import *
from timeit import default_timer as timer

if __name__ == "__main__":
    with qsearch.Project("benchmarks") as project:
        project.add_compilation("qft2", unitaries.qft(4))
        project.add_compilation("qft3", unitaries.qft(8))
        project.add_compilation("fredkin", unitaries.fredkin)
        project.add_compilation("toffoli", unitaries.toffoli)
        project.add_compilation("peres", unitaries.peres)
        project.add_compilation("or", unitaries.logical_or)

        project.add_compilation("miro", advanced_unitaries.mirogate)
        project.add_compilation("hhl", advanced_unitaries.HHL)
        project["verbosity"] = 0
        project["solver"] = SimpleMultistartSolver()
        project["parallelizer"] = qsearch.parallelizers.ProcessPoolParallelizer

        # run the benchmarks script with default settings 10x and average the timing results
        # reported times are between 0.1s and 5s on my 2018 Macbook Pro

        num_repetitions = 1
        start = timer()
        for _ in range(num_repetitions):
            project.reset()
            project.run()
        end = timer()

        print(f"Test suite took {end-start}s total so {(end-start)/num_repetitions}s on average.")

