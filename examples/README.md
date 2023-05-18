# YieldTasks Example Usage and Case Study based on Qsearch (https://github.com/BQSKit/qsearch)

The code here runs a benchmark involving 8 synthesis tasks repeated 10 times, and reports the timing information.  This can be used to demonstrate the usefulness of YieldTasks in this example use case.

This code here requires Qsearch which can be installed using `pip install qsearch`.


- `yieldtasks_qsearch.py` includes an implementation of `SearchCompiler` from Qsearch using subclasses of Task.

- `yieldtasks_qsearch2.py` includes an implementation of `SearchCompiler` from Qsearch using `taskmap`.

- `simple_multistart_solver.py` implements a simpler version of `NaiveMultiStart_Solver` from Qsearch that is not parallelized.

- `simple_multitart_solver_parallel.py` implements a parallel version of `simple_multistart_solver.py` that is functionally identical to `NaiveMultiStart_Solver`.

- `average_time_og_oversub.py` runs the benchmark using original Qsearch code, but using `simple_multistart_solver_parallel.py`.  This results in oversubscription because Qsearch parallelizes by solving multiple Ansatzes in parallel, but now it also parallelizes by performing multi-start optimization in parallel.

- `average_time_og_undersub.py` runs the benchmark using original Qsearch code, but using `simple_multistart_solver.py`.  This results in undersubscription because Qsearch parallelizes only by solving multiple Ansatzes in parallel.

- `average_time_yt.py` runs the benchmark using YieldTasks Qsearch code, allowing the processor to be better utilized without oversubscription.
