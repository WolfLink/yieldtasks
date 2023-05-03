from inspect import isgeneratorfunction
from .task import *
from .utils import taskmap


class TaskQueue():
    def __init__(self):
        self.queue = []
        self.waiting = dict()
        self.next_task_id = 0
        self.datastore = {None: []}

    def enqueue(self, task):
        task.id = self.next_task_id
        task.waiting_id = None
        self.next_task_id += 1
        self.queue.append(task)
        return task.id

    def requeue(self, resumedtask, subtasks):
        self.waiting[resumedtask.id] = resumedtask
        resumedtask.sub_ids = []
        resumedtask.waiting_count = 0
        for subtask in subtasks:
            self.enqueue(subtask)
            subtask.waiting_id = resumedtask.id
            resumedtask.waiting_count += 1

    def pop(self):
        return self.queue.pop()

    def store_task_output(self, output, task):
        if task.waiting_id in self.datastore:
            self.datastore[task.waiting_id].append(output)
        else:
            self.datastore[task.waiting_id] = [output]

        if task.waiting_id is not None:
            if not task.waiting_id in self.waiting[task.waiting_id].sub_ids:
                self.waiting[task.waiting_id].sub_ids.append(task.id)
                self.waiting[task.waiting_id].waiting_count -= 1
                if self.waiting[task.waiting_id].waiting_count == 0:
                    self.queue.append(self.waiting.pop(task.waiting_id))

    def retrieve_task_input(self, task):
        return self.datastore.pop(task.id)

    def retrieve_return_value(self):
        # if all the root level data is None, just return a single None.
        # if any root level data is not None, return the data list instead
        data = self.datastore.pop(None)
        self.datastore[None] = []
        for entry in data:
            if entry is not None:
                return data
        return None

    def run(self, task):
        raise NotImplementedError

    def map(self, f, v):
        return self.run(TaskList(*taskmap(f, v)))
                


