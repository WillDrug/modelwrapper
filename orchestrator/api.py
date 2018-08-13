# API
from flask import request, Flask
from flask.app import BadRequest
from flask_restful import Resource, Api as rapi
from . import ApiEnvironment, Api, ConfigLoader, Tasker, l, Conductor
from .config import ApiConfig, TaskerConfig
from .errors import TaskNotFound, InvalidTaskArguments
from json import loads as json_loads
from json.decoder import JSONDecodeError
from time import time, sleep


def gen_response(message, error=False, object=None, timestamp=None, response=None):
    res = dict(message=message, error=error)
    if object is not None:
        res['object'] = object
    if timestamp is not None:
        res['timestamp'] = int(timestamp)
    if response is not None:
        res['response'] = response
    return res
class BaseResource(Resource):
    tasker = None
    @classmethod
    def get_cls(cls, tasker):
        new_cls = cls
        new_cls.tasker = tasker
        return new_cls

class FlaskApi(Api):
    name = ApiEnvironment.WEB_FLASK.cls

    class TaskControl(BaseResource):
        def get(self):
            """ returns list of tasks in tasker """
            tasks = BaseResource.tasker.list_tasks()
            ret_t = list()
            for task in tasks:
                ret_t.append({
                    'id': task.tid,
                    'name': task.name,
                    'progress': False if task.result[0] is not None or task.result[1] else True,
                    'worked_for': task.status[1] - task.ident[1]
                })
            return ret_t

        def delete(self):
            task_id = request.args.get('task_id')
            return BaseResource.tasker.kill_task(task_id)

    class Task(BaseResource):
        def get(self, task, **kwargs):
            """
            returns task result
            :param task: task id
            :param kwargs: unused
            :return: gen_response dict, containing status, response (or error), and timestamp updated
            """
            # request.args.get()
            res = BaseResource.tasker.get_task_info(task)
            if res is None:
                return gen_response(f'Task {task} not found', error=True)
            message = f'Task is in {res.status[0]} status since {res.status[1]}'
            response = res.result[0]
            if isinstance(response, Exception):
                response = response.__repr__()
            error = res.result[1]
            object = res.ident[0]
            timestamp = res.status[1]

            return gen_response(
                message,
                response=response,
                error=error,
                object=object,
                timestamp=timestamp
            )

        def post(self, task, **kwargs):
            """
            Add a new task. Task kwargs are taken from input JSON payload
            :param task: Task name in TaskRegistry
            :param kwargs: unused
            :return: gen_response dict, containing status, response (if available right away), and timestamp created
            """
            try:
                validate = request.headers.get('Validate')
                if validate is None:
                    validate = BaseResource.tasker.config.get(TaskerConfig.VALIDATE)
                else:
                    validate = True if validate == 'true' else False
                l.debug(f'Validate is {validate}')
                # task is task_name
                in_data = dict() if int(request.headers.get('Content-Length', 0)) == 0 else request.get_json(force=True)
                ret = BaseResource.tasker.run_task(task, kwargs=in_data, validate=validate)
                exc = ret.result[0] if not isinstance(ret.result[0], Exception) else ret.result[0].__repr__()
                return gen_response(
                    'Task registered',
                    response=exc,
                    error=ret.result[1],
                    object=ret.ident[0],
                    timestamp=ret.status[1]
                )
            except Exception as e:  #catching anything to return as error
                return gen_response(f'{e.__class__}: {e.__str__()}', error=True)

        def put(self, task, **kwargs):
            try:
                validate = request.headers.get('Validate')
                if validate is None:
                    validate = BaseResource.tasker.config.get(TaskerConfig.VALIDATE)
                else:
                    validate = True if validate == 'true' else False
                l.debug(f'Validate is {validate}')
                # task is task_name
                in_data = dict() if int(request.headers.get('Content-Length', 0)) == 0 else request.get_json(force=True)
                ret = BaseResource.tasker.run_task(task, kwargs=in_data, validate=validate, blocking=True)
                exc = ret.result[0] if not isinstance(ret.result[0], Exception) else ret.result[0].__repr__()
                return gen_response(
                    'Task ran',
                    response=exc,
                    error=ret.result[1],
                    object=ret.ident[0],
                    timestamp=ret.status[1]
                )
            except Exception as e:  #catching anything to return as error
                return gen_response(f'{e.__class__}: {e.__str__()}', error=True)

    class Service(BaseResource):
        def delete(self):
            """
            Shuts down server
            :return: HTTP OK + basic message
            """
            l.info(f'API got shutdown command')
            func = request.environ.get('werkzeug.server.shutdown')
            l.debug(f'Got {func} to shutdown')
            if func is None:
                l.error(f'Not running Werkzeug server, API can''t shutdown')
                return gen_response(message=f'Failed to shutdown service', error=True)
            func()
            return gen_response(message='Shutting down server')

        def get(self):
            """
            Get server status;
            :return: json object; tasker_status contains list of threads and their status (True\False);
            api_status contains "alive" when alive.
            """
            pub = BaseResource.tasker.config.list_public
            configurable = {q: {
                "desc": pub[q],
                "val": BaseResource.tasker.config.get_public(q)
            } for q in pub}
            return dict(
                tasker_status=BaseResource.tasker.get_self_status(),
                api_status='alive',  # TODO: api status
                configurable=configurable
            )


        def patch(self):
            """
            Config server or tasker. Config names and new values are taken from JSON payload.
            :return: response dict with error\response pairs.
            """
            in_data = request.get_json(force=True)
            c_res = dict()
            for key in in_data:
                if not BaseResource.tasker.config.check_public(key):
                    c_res[key] = {'error': True, 'response': 'Config not changeable or doesnt exist'}
                    continue
                current = BaseResource.tasker.config.get_public(key)
                if type(current) != type(in_data[key]):
                    c_res[key] = {'error': True, 'response': 'Type mismatch'}
                    continue
                BaseResource.tasker.config.set_public(key, in_data[key])
                c_res[key] = {'error': False, 'response': f'{key} data is set to {in_data[key]}'}
            return c_res


    def __init__(self, **kwargs):
        l.info(f'Initializing {self.name} WEB API')

        self.config = kwargs.pop('configurator', ApiEnvironment.WEB_FLASK.conf.get('configurator', ConfigLoader(ApiConfig)))
        self.tasker = kwargs.pop('tasker', ApiEnvironment.WEB_FLASK.conf.get('tasker', Tasker()))
        BaseResource.tasker = self.tasker

        self.app = Flask(Conductor.ORCHESTRATION)
        self.api = rapi(self.app)
        
        self.add_resource(FlaskApi.Service, ['/service'], strict_slashes=False)
        self.add_resource(FlaskApi.Task, ['/tasks/<string:task>', '/tasks'], strict_slashes=False)  # ?sync blocks

        self.add_resource(FlaskApi.TaskControl, ['/control/'], strict_slashes=False)

        l.info(f'Web API initialized')


    def add_resource(self, res_cls: type, routes: list, **kwargs):
        strict_slashes = kwargs.pop('strict_slashes', False)
        self.api.add_resource(res_cls, *routes, strict_slashes=strict_slashes)
        l.info(f'Routes {routes} added to {res_cls} resource')
        return True

    def graceful_shutdown(self):
        l.info('Shutting down API')
        self.config.graceful_shutdown()
        self.tasker.graceful_shutdown()
        l.info('Goodbye...')

    def run(self):
        return self.start()  # TODO: threading

    def start(self):
        l.info(f'Starting API IO loop')
        self.app._logger = l.logger
        self.app.run(
            self.config.get(ApiConfig.API_HOST),
            self.config.get(ApiConfig.API_PORT),
            self.config.get(ApiConfig.DEBUG)
        )
        self.graceful_shutdown()