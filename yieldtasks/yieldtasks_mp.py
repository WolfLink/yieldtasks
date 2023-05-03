from .task import *
from .task_queue import *
import multiprocessing as mp

class MPQueueMessage():
    def __init__(self, value, content=None):
        self.value = value
        self.content = content


class MPQueue(TaskQueue):
    def __init__(self):
        super().__init__()
        self.master_lock = mp.Lock()

    def enqueue(self, task):
        self.queue.append(task)
    
    def run(self, task):
        self.enqueue(task)
        workers = [MPWorkerQueue() for _ in range(mp.cpu_count())]
        for i, worker in enumerate(workers):
            worker.worker_id = i

        worker_processes = [mp.Process(target=launch_worker, args=(worker,)) for worker in workers]
        for worker_process in worker_processes:
            worker_process.start()

        alldone = False
        while (len(self.queue) > 0) or (not alldone):
            while len(self.queue) > 0:
                task = self.pop()
                # see if this task needs to go to a specific worker
                if isinstance(task, PlaceholderTask):
                    if task.waiting_id is None:
                        self.store_task_output(task.run(), task)
                    else:
                        workers[task.waiting_id[0]].task_count += 1
                        workers[task.waiting_id[0]].run_in_background(task)
                    continue

                # I am sure there are more efficient ways to keep track of the least busy worker
                # but this should be acceptable for small numbers of workers ( <64 in the current case)
                least_busy_worker = workers[0]
                for i in range(1, len(workers)):
                    if workers[i].busy_count < least_busy_worker.busy_count:
                        least_busy_worker = workers[i]
                least_busy_worker.run_in_background(task)
                least_busy_worker.task_count += 1
                least_busy_worker.busy_count += 1

            # check to see if all the workers are done
            alldone = True
            for worker in workers:
                if worker.task_count > 0:
                    alldone = False
                    break
            if not alldone:
                # wait for some output from the workers
                mp.connection.wait(list([worker.pipe[0] for worker in workers]))
                for worker in workers:
                    while worker.pipe[0].poll():
                        output = worker.pipe[0].recv()
                        if output.value == "completed":
                            worker.task_count -= 1
                            if not output.content[0]:
                                worker.busy_count -= 1
                            if output.content[1] is not None:
                                self.enqueue(output.content[1])
                        elif output.value == "requeued":
                            worker.busy_count -= 1
                            for task in output.content:
                                self.enqueue(task)
                        elif output.value == "resumed":
                            worker.busy_count += 1
                            #print(f"{worker.worker_id} is now {worker.task_count} {worker.busy_count}")
                        else:
                            print(f"Got unknown message {output.value}")
            #print(f"Queue is {len(self.queue)} and workers are {[worker.task_count for worker in workers]}")

        
        # clean up the workers
        for worker in workers:
            worker.pipe[0].send(MPQueueMessage("kill"))
        for worker_process in worker_processes:
            worker_process.join()
        return self.retrieve_return_value()


def launch_worker(worker):
    worker.start()

class MPWorkerQueue(TaskQueue):
    def __init__(self):
        super().__init__()
        self.worker_id = None
        self.pipe = mp.Pipe()
        self.task_count = 0
        self.busy_count = 0

    def done(self):
        if len(self.queue) > 0:
            return False
        try:
            msg = self.pipe[1].recv()
        #except EOFError:
        except: # sometimes I get a ConnectionResetError instead
            return True
        if msg.value == "kill":
            return True
        self.enqueue(msg.content)
        return False

    def enqueue(self, task):
        task.id = (self.worker_id, self.next_task_id)
        self.next_task_id += 1
        try:
            test = task.waiting_id
        except:
            task.waiting_id = None
        self.queue.append(task)

    def store_task_output(self, output, task):
        is_placeholder = isinstance(task, PlaceholderTask)
        if task.waiting_id in self.waiting:
            if task.waiting_id is None:
                print("WARNNG")
            # notify the manager of task completion
            self.pipe[1].send(MPQueueMessage("completed", (is_placeholder, None)))
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
                        #print(f"{self.worker_id} resumed {task.waiting_id}")
                        self.pipe[1].send(MPQueueMessage("resumed"))
        else:
            self.pipe[1].send(MPQueueMessage("completed",(is_placeholder, PlaceholderTask(task, output))))

    def requeue(self, resumedtask, subtasks):
        self.waiting[resumedtask.id] = resumedtask
        resumedtask.sub_ids = []
        resumedtask.waiting_count = 0
        tasks_to_send = []
        for subtask in subtasks:
            subtask.id = (self.worker_id, self.next_task_id)
            self.next_task_id += 1
            subtask.waiting_id = resumedtask.id
            resumedtask.waiting_count += 1
            tasks_to_send.append(subtask)
        #print(f"{resumedtask.id} now waiting on {resumedtask.waiting_count}")
        self.pipe[1].send(MPQueueMessage("requeued",tasks_to_send))

    def start(self):
        while not self.done():
            task = self.pop()
            if isinstance(task, ResumedTask):
                try:
                    subtasks = task.gen.send(self.retrieve_task_input(task))
                    self.requeue(task, subtasks)
                except StopIteration as e:
                    self.store_task_output(e.value, task)
            elif isgeneratorfunction(task.run):
                gen = task.run()
                try:
                    subtasks = next(gen)
                    resumedtask = ResumedTask(gen, task)
                    self.requeue(resumedtask, subtasks)
                except StopIteration as e:
                    self.store_task_output(e.value, task)
            else:
                self.store_task_output(task.run(), task)

    def run_in_background(self, task):
        #if isinstance(task, PlaceholderTask):
        #    print(f"{self.worker_id} got placeholder for {task.waiting_id} {task.waiting_id in self.waiting}")
        #else:
        #    print(f"worker {self.worker_id} was given {task}")
        self.pipe[0].send(MPQueueMessage("task",task))

    def run(self, task):        
        raise NotImplementedError


