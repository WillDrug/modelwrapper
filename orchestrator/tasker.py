from . import TaskEnvironment, ConfigLoader, Connector, Tasker, l, Conductor
from .errors import TaskNotFound, BorkedException
from .config import TaskerConfig

# TODO: task class instead of dict?
# Tasker.TaskWrapper, including pre- and post-execute
from uuid import uuid4
import types
import time
from concurrent.futures import ThreadPoolExecutor, Future

class ThreadTasker(Tasker):
    name = TaskEnvironment.THREAD.cls

    def __init__(self, **kwargs):
        l.info(f'Initializing tasker {self.name}')
        self.__conn = kwargs.pop('connector', TaskEnvironment.THREAD.conf.get('connector', Connector()))
        self.config = kwargs.pop('configurator', TaskEnvironment.THREAD.conf.get('configurator', ConfigLoader()))
        self.config.init_config(TaskerConfig)
        l.debug(f'Tasker initialized ConfigLoader {self.config}')
        ts = kwargs.pop('tasks', TaskEnvironment.THREAD.conf.get('tasks', dict()))
        self.tasks = {t: Tasker.TaskWrapper(t, ts[t]) for t in ts}
        l.debug(f'Tasker loaded supplied tasks {self.tasks}')
        w_num = self.config.get(TaskerConfig.WORKER_NUM)
        l.debug(f'Creating {w_num} workers')
        self.worker = ThreadPoolExecutor(max_workers=w_num, thread_name_prefix=Conductor.ORCHESTRATION)
        self.registry = dict()
        l.info(f'Tasker {self.name} initialized')

        for task in self.list_tasks():
            if task.result[0] is None and not task.result[1]:
                task.error(BorkedException('Container got killed during task completion'))
                l.debug(f'Saving task {task.ident}')
                self.save(task)
                # TODO: reload task results, re-add NEW to queue and restart PROGRESS
                #t = self.tasks.get(task['name'])
                #if t is not None:



    def graceful_shutdown(self):
        l.info(f'Tasker {self.name} is shutting down')
        self.config.graceful_shutdown()
        self.__conn.graceful_shutdown()
        l.info(f'Elvis has left the building')

    def register_task(self, name: str, func: types.FunctionType) -> bool:
        l.info(f'Registering {name} task')
        self.tasks[name] = Tasker.TaskWrapper(name, func)
        l.info(f'Registered {name} task')
        return True

    def add_pre(self, name, fn):
        try:
            self.tasks[name].register_pre_execute(fn)
        except KeyError:
            raise TaskNotFound(f'Cant register pre-execute: task {name} not found in TaskRegistry')
        l.debug(f'Registered pre-execute hook for {name}')
        return True

    def add_post(self, name, fn):
        try:
            self.tasks[name].register_post_execute(fn)
        except KeyError:
            raise TaskNotFound(f'Cant register post-execute: task {name} not found in TaskRegistry')
        l.debug(f'Registered post-execute hook for {name}')
        return True

    def save(self, res: Tasker.TaskResultWrapper) -> bool:
        key = '.'.join((self.config.get(TaskerConfig.TASK_PATH), res.tid))
        if res.status in [Tasker.TaskResultWrapper.DONE, Tasker.TaskResultWrapper.ERROR]:
            ex = self.config.get(TaskerConfig.TASK_RESULT_EX)
        else:
            ex = self.config.get(TaskerConfig.TASK_EX)
        l.debug(f'Saving {res.tid}')
        return self.__conn.set(key, res, ex=ex)

    def load(self, task_id) -> Tasker.TaskResultWrapper:
        key = '.'.join((self.config.get(TaskerConfig.TASK_PATH), task_id))
        l.debug(f'Loading {task_id}')
        return self.__conn.get(key)


    def run_task(self, name, args=[], kwargs={}, blocking=False, validate=False) -> Tasker.TaskResultWrapper:
        # Tasker.TaskWrapper performs argscheck itself, raising InvalidTaskArgument if needed
        l.info(f'Task {name} got a run request')
        tw = self.tasks.get(name)
        if tw is None:
            raise TaskNotFound(f'task {name} not found in TaskRegistry')
        if validate:
            tw.validate(args, kwargs)
        task_id = uuid4().__str__()
        l.debug(f'Designated {task_id} for {tw.name}')
        # using task_name to leave backwards compatibility
        res = Tasker.TaskResultWrapper(task_id, task_name=tw.name, args=args, kwargs=kwargs)
        self.save(res)
        if blocking:
            l.debug(f'Running {task_id} with block')
            try:
                tres = self.__run(task_id, tw, args=args, kwargs=kwargs)
                res.closed(tres)
                self.save(res)
                return res
            except Exception as e:
                res.error(e)
                self.save(res)
                return res
        else:
            l.debug(f'Running {task_id} in separate thread')
            future = self.worker.submit(self.__run, *[task_id, tw], **dict(args=args, kwargs=kwargs))

        # since callback will not fire until added - this fucking works
        self.registry[future] = task_id
        future.add_done_callback(self.__done)
        return self.load(task_id)

    def get_task_info(self, task_id: str):
        return self.load(task_id)

    def get_self_status(self):
        tl = list(self.worker.__dict__['_threads'])
        return {
            'threads_alive': [{t.ident: t.is_alive()} for t in tl],
            'max_threads': self.worker._max_workers
        }

    def __done(self, f: Future):
        """
        Thread task callback, saves result and such
        :param f:
        :return:
        """
        task_id = self.registry[f]
        del self.registry[f]
        trw = self.load(task_id)
        exc = f.exception()
        if exc is not None:
            trw.error(exc)
        else:
            trw.closed(f.result())
        self.save(trw)

    def __run(self, tid: str, task: Tasker.TaskWrapper, args=[], kwargs={}):
        """
        Runs a task, already in a separate thread. Used to set progress status and prepare everything
        :param tid: Task id
        :param task: TaskWrapper
        :param args: Args for stored function; Not used for WEB API
        :param kwargs: Kwargs for stored function
        :return:
        """
        l.debug(f'{tid} ran')
        trw = self.load(tid)
        trw.started()
        self.save(trw)
        return task.run(args, kwargs)  # synchronous for this call

    def kill_task(self, name: str) -> bool:
        raise NotImplementedError('Impossible with threads')

    def list_tasks(self) -> list:
        l.info(f'Got task list request')
        keys = self.__conn.keys('.'.join((self.config.get(TaskerConfig.TASK_PATH), '*')))
        l.debug(f'{keys} are keys')
        tasks = []
        for key in keys:
            k = key.split('.')[-1]
            tasks.append(self.load(k))
        return tasks