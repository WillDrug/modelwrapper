# TODO: uncomment when package works
# from utils import log
# from utils.loggers import LogLevels

import os as _os
import json

from .loggers import AbstractLogger

__CONFIG_FILE = 'logger_config.json'
__CONFIG_PATH = _os.path.join(_os.path.dirname(__file__), __CONFIG_FILE)


def __load_json_cfg(path):
    with open(path, 'r') as fl:
        base_cfg = json.load(fl)
    fl.close()
    return base_cfg


cfg = __load_json_cfg(__CONFIG_PATH)

_abstract_logger = AbstractLogger
logger = _abstract_logger.get_new('DefaultLogger')(
    logs_dir=cfg['LOGS_FOLDER'],
    trace_path=cfg['TRACE_PATH'],
    max_trace_size=int(cfg['MAX_TRACE_SIZE']),
    trace_backup=int(cfg['TRACE_BACKUPS_LIMIT']),
    error_path=cfg['ERROR_PATH'],
    max_error_size=int(cfg['MAX_ERROR_SIZE']),
    error_backup=int(cfg['ERRORS_BACKUPS_LIMIT']),
    std_out=cfg['WRITE_TO_STD_OUT'],
    trace_log_level=cfg['LOGGER_LEVEL'],
    module_name='logger',
)
l = logger

from enum import Enum


class Environment(Enum):
    @property
    def cls(self):
        return self.value['cls']

    @property
    def conf(self):
        return self.value['conf']


class StorageEnvironment(Environment):
    REDIS = {
        'cls': 'redis',
        'conf': {
            'typed': True,
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None,
            'socket_timeout': None,
            'socket_connect_timeout': None,
            'socket_keepalive': None,
            'socket_keepalive_options': None,
            'connection_pool': None,
            'unix_socket_path': None,
            'encoding_errors': 'strict',
            'charset': None,
            'errors': None,
            'retry_on_timeout': False,
            'ssl': False,
            'ssl_keyfile': None,
            'ssl_certfile': None,
            'ssl_cert_reqs': None,
            'ssl_ca_certs': None,
            'max_connections': None
        }
    }

    default = {'cls': _os.environ.get('orc_storage_env'), 'conf': {}} if _os.environ.get(
        'orc_storage_env') is not None else REDIS


class ConfigEnvironment(Environment):
    PERSISTENT = {
        'cls': 'persistent',
        'conf': {}  # uses default connector
    }

    default = {'cls': _os.environ.get('orc_config_env'), 'conf': {}} if _os.environ.get(
        'orc_config_env') is not None else PERSISTENT


class ApiEnvironment(Environment):
    WEB_FLASK = {
        'cls': 'flask',
        'conf': {}
    }

    default = {'cls': _os.environ.get('orc_api_env'), 'conf': {}} if _os.environ.get(
        'orc_api_env') is not None else WEB_FLASK

def health(**kwargs):
    return 'OK'

class TaskEnvironment(Environment):
    THREAD = {
        'cls': 'process',
        'conf': {
            'tasks': {
                'health': health
            }
        }
    }

    default = {'cls': _os.environ.get('orc_task_env'), 'conf': {}} if _os.environ.get(
        'orc_task_env') is not None else THREAD


class Conductor:
    """
    If no init values specified, Interfaces will go here for default values
    This can be changed before instantiating interfaces
    :return:
    """
    ORCHESTRATION = 'default'
    STORAGE = [StorageEnvironment.default]
    # Provides package-wide connection config to automatically instantiate Connector() in ConfigLoader, Tasker, Api
    # Defaults to redis for now
    CONFIG = [ConfigEnvironment.default]
    API = [ApiEnvironment.default]
    TASKER = [TaskEnvironment.default]


# Abstract part
from abc import ABCMeta, abstractmethod, abstractstaticmethod, abstractclassmethod


class BaseAbstract(metaclass=ABCMeta):
    name = None
    default = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        """ Forces creation of an implementation on each Interface call
        """
        environment = kwargs.pop('environment', cls.default[0])
        return_class = cls.impl_list().get(environment.cls, None)
        if return_class is None:
            raise TypeError(
                "TypeError: Environment not found"
            )
        return object.__new__(return_class)

    @classmethod
    def impl_list(cls) -> dict:
        return {subcl.name: subcl for subcl in cls.__subclasses__()}


# Connectors
class Connector(BaseAbstract, metaclass=ABCMeta):
    name = None
    default = Conductor.STORAGE

    @abstractmethod
    def __init__(self, environment=None, **kwargs):
        """
        This is here only to expose basic connector signature...
        ... which is none and only has kwargs
        ... because this is such a basic thing everything will be different
        Each Interfcae realisation has it's own docstring
        """
        pass

    @abstractmethod
    def get(self, key):
        """
        Get stored value by key
        :param key: Key in connected database
        :type key: str
        :return: value: Stored value
        """
        return f'value of {key}'

    @abstractmethod
    def set(self, key, value, ex=None):
        """
        Store a value in {key} namespace
        :param key: Key in connected database
        :type key: str
        :param value: Value to insert or update
        :type value: any
        :return: bool: Success of the operation
        """
        return True

    @abstractmethod
    def delete(self, key):
        """
        Delete a value by key
        :param key: Key in connected database
        :type key: str
        :return: bool: Success of the operation

        """
        return True

    @abstractmethod
    def keys(self, pattern='*'):
        """
        Return keys by pattern with * as wildcard
        :param pattern:
        :type pattern: regex string
        :return: list: list of stored keys
        """
        return []

    @abstractmethod
    def graceful_shutdown(self):
        """
        Removes active connection so there are no artifacts left
        :return:
        """


# this populates implementations of connector class
from . import connectors


# ConfgLoader part
class ConfigLoader(BaseAbstract, metaclass=ABCMeta):
    name = None
    default = Conductor.CONFIG

    @abstractmethod
    def __init__(self, environment=None, initial=None, **kwargs):
        """
        Loads config based on BaseConfig enum and gives user interfaces to work with it
        :param connector: Connector class. If none provided , creates a default from Conductor
        :param initial: BaseConfig subclass
        :param kwargs: not used
        """
        pass

    @staticmethod
    @abstractstaticmethod
    def valid(cfg):
        """
        Static method, performs a basic check that provided config is an instance of BaseConfig subclass
        :param cfg: BaseConfig
        :return: bool: check validity of config
        """
        pass

    @abstractmethod
    def init_config(self, initial):
        """
        Initializes config if not set in __init__.initial;
        If config is not present in connector config is set as default
        :param initial: BaseConfig subclass
        :return:
        """
        pass

    @abstractmethod
    def get(self, cfg):
        """
        Get stored config value
        :param cfg: BaseConfig
        :return: config value
        """
        pass

    @abstractmethod
    def set(self, cfg, value=None):
        """
        Set config value
        :param cfg: BaseConfig
        :param value: value to set
        :return: bool: success
        """
        pass

    @abstractmethod
    def is_initialized(self, cfg):
        """
        Check if config key is present; Useful to check config values between modules
        :param cfg: BaseConfig
        :return: bool: runs __check
        """
        pass

    @abstractmethod
    def make_public(self, cfg):
        """
        Marks BaseConfig as public, use if it's not specified in BaseConfig.public
        :param cfg: BaseConfig
        :return: bool, success;
        """
        pass

    @abstractmethod
    def unmake_public(self, cfg):
        """
        Deleted config info from public config lists and prohibits use of set_public for that config
        :param cfg: BaseConfig
        :return: bool, success
        """
        pass

    @property
    @abstractmethod
    def list_public(self):
        """
        Property
        :return: returns a dict of config keys, marked as public, to their respective descriptions
        """
        pass

    @abstractmethod
    def set_public(self, key, value):
        """
        Set new config value by key; Only works if the config is in list_public
        :param key: corresponds to BaseConfig.namespace
        :param value: value to set
        :return:
        """
        pass

    @abstractmethod
    def get_public(self, key):
        """
        Get config value by key; Only works if the config is in list_public
        :param key: corresponds to BaseConfig.namespace
        :return: returns config value
        """
        pass

    @abstractmethod
    def check_public(self, key):
        """
        checks publicity for key
        :param key: str
        :return:
        """

    @abstractmethod
    def graceful_shutdown(self):
        """
        closes files, disconnects from db, etc.
        :return: void
        """
        pass




# Populating impl_list of ConfigLoader
from . import config_loader
from .errors import InvalidTaskArguments, NotAFunction
# Tasker
import types, time

from inspect import signature
from inspect import _ParameterKind, _empty


class Tasker(BaseAbstract, metaclass=ABCMeta):
    default = Conductor.TASKER
    name = None

    @abstractmethod
    def __init__(self, connector=None, configurator=None, **kwargs):
        """
        Initializes a tasker; If no connector and\or configurator provided, creates default from Conductor.
        :param connector:
        :param configurator:
        :param kwargs:
        """
        pass

    @abstractmethod
    def get_self_status(self) -> dict:
        """
        returns number and status of workers
        :return:
        """
        pass

    @abstractmethod
    def register_task(self, name: str, func: types.FunctionType) -> bool:
        """
        Adds a new task to tasker dict;
        :param name: name of function
        :param func:
        :return:
        """
        pass

    @abstractmethod
    def run_task(self, name: str, args: list = [], kwargs: dict = {}, blocking=False, validate=False):
        """
        calls task with *args and **kwargs
        :param name: Name in task Registry
        :type name: str
        :param args: Args for the function stored
        :type args: list
        :param kwargs: Kwargs for the function stored
        :type kwargs: dict
        :param blocking: If set to true, makes the function call synchronous, returning result right away
        :return:
        """
        pass

    @abstractmethod
    def get_task_info(self, task_id: str):
        """
        :param task_id:
        :return:
        """
        pass

    @abstractmethod
    def graceful_shutdown(self):
        """
        Closes all connections and such before exiting
        :return:
        """
        pass
    @abstractmethod
    def add_pre(self, name, f):
        """
        Add a pre-execute hook to a task
        :param name: Task name
        :param f: Pre-execute function
        :return: bool
        """
        pass
    @abstractmethod
    def add_post(self, name, f):
        """
        Add a post-execute hook to a task
        :param name: Task name
        :param f: Post-execute function
        :return: bool
        """
        pass
    @abstractmethod
    def kill_task(self, name: str) -> bool:
        """
        Kills task by id
        :param name:
        :return:
        """
        pass
    @abstractmethod
    def list_tasks(self) -> list:
        """ returns current tasks list """
        pass
    # cheating
    class TaskWrapper:
        class TaskParm:
            def __init__(self, name, arg_only, kwarg_only, has_default, argtype):
                self.name = name
                self.arg_only = arg_only
                self.kwarg_only = kwarg_only
                self.has_default = has_default
                self.type = argtype
        """
        Wrapper for a task with execute hooks and TypError catching
        Stored in TaskRegistry, which is a dict in Tasker
        """
        def __init__(self, name, f):  # 1.1 Adding args and kwargs for validate function calls. Backwards compatible
            """
            Creates a task wrapper to store in TaskRegistry
            :param name:
            :param f:
            """
            l.debug(f'{name} task wrapper created')
            self.name = name  # used for self logging
            if not isinstance(f, types.FunctionType):
                raise NotAFunction(f'{f} is not a function')
            self.f = f
            l.debug(f'Analyzing function signature')
            sig = signature(f)
            parms = sig.parameters
            l.debug(f'Signature is {parms}')
            self.args = []
            for item in parms.items():
                self.args.append(
                    self.TaskParm(
                        item[0],
                        True if item[1].kind == _ParameterKind.POSITIONAL_ONLY else False,
                        True if item[1].kind == _ParameterKind.KEYWORD_ONLY else False,
                        True if item[1].default is not _empty or item[1].kind in [_ParameterKind.VAR_KEYWORD, _ParameterKind.VAR_POSITIONAL] else False,  # *args and **kwargs are omittable hence they default to [] and {} respectively
                        item[1].annotation if item[1].annotation is not _empty else None
                    )
                )

            self.pre_execute = lambda *args, **kwargs: None
            self.post_execute = lambda *args, **kwargs: None

        def validate(self, args, kwargs):
            name = self.name
            l.debug(f'Task {name} got a validation request with {args} args and {kwargs} kwargs')
            for item in self.args:
                if item.kwarg_only and item.name not in list(kwargs.keys()) and not item.has_default:
                    l.debug(f'{item.name} is kwarg only and it\'s name is not in kwarg keys')
                    raise InvalidTaskArguments(f'{item.name} is kwarg_only and not in kwargs provided')
                elif item.arg_only and not item.has_default and self.args.index(
                        item) > args.__len__() - 1:  # redundant check for default, maximum possible here is to check length
                    raise InvalidTaskArguments(f'{item.name} is arg only and arg length is less than it\'s index')
                elif not item.has_default:  # can be both positional and keyword and doesn't have a default value
                    # check type if present

                    if self.args.index(item) > args.__len__() - 1 and item.name not in list(kwargs.keys()):
                        raise InvalidTaskArguments(f'{item.name} not found in args nor kwargs')
                    # TODO: move this to separate IF clause.
                    elif item.type is not None:
                        passed = False
                        try:
                            if type(args[self.args.index(item)]) == item.type:
                                l.debug(f'Arg type matched for {item.name} parm')
                                passed = True
                        except IndexError:
                            pass
                        try:
                            if type(kwargs[item.name]) == item.type:
                                l.debug(f'Kwarg type matched for {item.name} kwarg')
                                passed = True
                        except KeyError:
                            pass
                        if not passed:
                            raise InvalidTaskArguments(f'{item.name} type mismatch for both arg and kwarg kinds')
            # TODO: extensive reverse checks
            # basic reverse check:
            names = [p.name for p in self.args]
            for name in kwargs.keys():
                if name not in names:
                    raise InvalidTaskArguments(f'{name} keyword argument provided is not in function signature')
            return True

        def run(self, args, kwargs):
            """
            Runs a task including pre and post execute hooks
            :param args:
            :param kwargs:
            :return:
            """
            self.pre_execute(self.name, args, kwargs, None)
            l.debug(f'{self.name} ran pre-exec')
            #try:
            res = self.f(*args, **kwargs)  # if function throws exception here it is raised and handled by FUTURE
            #except TypeError as e:
            #    l.warning(f'Task {self.name} not run, exception {e} occurred')
            #    raise InvalidTaskArguments(f'Invalid arguments provided for {self.name} task')
            self.post_execute(self.name, args, kwargs, res)
            l.debug(f'{self.name} ran post-exec')
            return res

        def register_pre_execute(self, f):
            """
            Supply a function to be run before the function;
            Function should expect the following args: name, supplied args, supplied kwargs, None (or result)
            :param f:
            :return:
            """
            if not isinstance(f, types.FunctionType):
                l.warning(f'pre-execute for {self.name} not registered')
                raise NotAFunction(f'{f} is not a function!')
            self.pre_execute = f

        def register_post_execute(self, f):
            """
            Supply a function to be run after the function;
            Function should expect the following args: name, supplied args, supplied kwargs, result
            :param f:
            :return:
            """

            if not isinstance(f, types.FunctionType):
                l.warning(f'post-execute for {self.name} not registered')
                raise NotAFunction(f'{f} is not a function!')
            self.post_execute = f

    class TaskResultWrapper:
        """
        Stores task results, including status, timestamps and initial args-kwargs;
        Represents task run instance
        """
        NEW = 'new'
        PROGRESS = 'progress'
        ERROR = 'error'
        DONE = 'done'

        def __init__(self, task_id: str, task_name: str='', args=[], kwargs={}):
            """
            Creating a class represents task put into work queue
            :param task_id: Id to assing to call (might move id generation here later)
            :param args: Args with which task was run
            :param kwargs: Kwargs with which task was run
            """
            self.name = task_name
            self.tid = task_id
            self.st = Tasker.TaskResultWrapper.NEW
            self.created = time.time()
            self.updated = time.time()
            self.res = None
            self.exception = False
            self.args = args
            self.kwargs = kwargs

        def started(self):
            """
            Run to set status to "in progress"; Should only be used by tasker;
            :return:
            """
            self.updated = time.time()
            self.st = Tasker.TaskResultWrapper.PROGRESS

        def closed(self, result):
            """
            Run to set status to "closed"; Should only be used by tasker;
            :param result: Result of function run
            :return:
            """
            self.updated = time.time()
            self.res = result
            self.st = Tasker.TaskResultWrapper.DONE

        def error(self, exception):
            """
            Set result to error
            :param exception: Exception occured in running task
            :return:
            """
            self.updated = time.time()
            self.exception = True
            self.res = f'{exception.__class__}:({exception.__str__()})'
            self.st = Tasker.TaskResultWrapper.ERROR

        @property
        def ident(self):
            """
            :return: Tuple of task id, time created
            """
            return self.tid, self.created

        @property
        def status(self):
            """
            :return: Tuple of status, time last updated
            """
            return self.st, self.updated

        @property
        def result(self):
            """
            :return: Tuple of result\exception, boolean set to True if exception is stored
            """
            return self.res, self.exception


# oh no, it's time to write a tasker; derp
from . import tasker


# API
class Api(BaseAbstract, metaclass=ABCMeta):
    default = Conductor.API
    name = None

    @abstractmethod
    def __init__(self, configurator: ConfigLoader, tasker: Tasker, **kwargs):
        self.config = configurator
        self.tasker = tasker
        pass

    @abstractmethod
    def add_resource(self, res_cls: type, routes: list, **kwargs):
        """
        Ability to add extra routes to your API such as GUI implements and such;
        Tasker adds itself by default
        :param routes: list of routes (if applicable) to navigate to with corresponding REST object.
        :param res_cls: REST object
        :param kwargs:
        :return: returns True if done
        """
        pass

    @abstractmethod
    def graceful_shutdown(self):
        """
        graceful shutdown
        :return: bool
        """
        pass

    @abstractmethod
    def start(self):
        """
        starts API IO Loop
        :return:
        """
        pass

    @abstractmethod
    def run(self):
        """
        starts API IO Loop as a thread
        :return:
        """
        pass


from . import api
