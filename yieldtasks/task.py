# This file defines the Task API, some Task subclasses that are critical for yieldtasks to function, and some common utility subclasses.
from inspect import isgeneratorfunction

class Task():
    def run(self):
        raise NotImplementedError


class ResumedTask(Task):
    def __init__(self, gen, task):
        self.id = task.id
        self.waiting_id = task.waiting_id
        self.gen = gen
        self.sub_ids = []
        self.waiting_count = 0

class PlaceholderTask(Task):
    def __init__(self, task, output):
        self.id = task.id
        self.waiting_id = task.waiting_id
        self.output = output
       
    def run(self):
        return self.output


class Partial(Task):
    def __init__(self, f, *args, **kwargs):
        self.f = f
        self.args = args
        self.kwargs = kwargs

    def run(self):
        if isgeneratorfunction(self.f):
            output = yield from self.f(*self.args, **self.kwargs)
            return output
        else:
            return self.f(*self.args, **self.kwargs)

class TaskList(Task):
    def __init__(self, *tasks):
        self.tasks = tasks

    def run(self):
        data = yield self.tasks
        return data

