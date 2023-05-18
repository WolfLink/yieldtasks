# YieldTasks: A Better Parallel Map in Python

YieldTasks provides a parallel map operation that can be written as:

`output = yield yieldtasks.taskmap(f, input)`

YieldTasks was designed with two core goals in mind:
- Code that is parallelized this way will handle nested parallel map calls efficiently
- Code that is parallelized with YieldTasks can be run with a different parallel backend simply by changing the TaskQueue that is used without having to rewrite any other code.

## Installation and Basic Usage

1. Install YieldTasks by cloning this repository and using `pip install .` from the base directory of the repository.
2. Import YieldTasks into your code using `import yieldtasks`.
3. Use `output = yield yieldtasks.taskmap(f, input)` for your parallel map function calls.
4. Start your code with `output = yieldtasks.MPQueue().map(f, input)`.

## Advanced Usage

`taskmap` also takes in `*args` and `**kwargs`.  The first argument to `f` will be one element from the input list.  Then, `*args` and `**kwargs` will be passed.  For example, you can use:

`output = yield yieldtasks.taskmap(f, list_of_data, positional_argument, keyword_argument=keyword_argument)`

`taskwrap` takes in `*args` and `**kwargs` and passes them to `f`.  It can be used as shorthand instead of calling `taskmap` when there is only one value to be sent.  This is necessary when there may be a `taskmap` call somewhere within `f`.


It is also possible to manually write subclasses of `Task` rather than rely on `taskmap` and `taskwrap`.  A `Task` can be submitted directly to a `TaskQueue` such as `MPQueue` using `run`.  For example: `output = MPQueue().run(MyTask())`.


Changing the backend used by YieldTasks requires a different implementation of `TaskQueue`.  Currently, only `MPQueue`, which is based on Multiprocessing, is provided.  If you would like to use a different parallel backend, you must create your own implementation of `TaskQueue`.  If you do so, please add a pull request so your `TaskQueue` can be used by future users.


## Examples

The `examples` folder includes an example of using YieldTasks to accelerate the quantum gate synthesis program [Qsearch](https://github.com/BQSKit/qsearch).
