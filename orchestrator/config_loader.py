from .errors import NotAValidConfig, NotPermitted
from enum import Enum
from . import ConfigLoader, Connector, ConfigEnvironment, l

# lol kek constants
config_path = 'config'
config_public = 'public'


def config_key(cfg):
    return '.'.join((config_path, cfg))


def config_publicity_key(cfg):
    return '.'.join((config_public, cfg))

def config_strip(cfg):
    if cfg.startswith(config_public):
        return cfg[config_public.__len__() + 1:]
    if cfg.startswith(config_path):
        return cfg[config_path.__len__()+1:]
    return cfg

    # CONFIG LOADER IS NOT LOGGED BECAUSE LOGGER USES IT, LOL LOL LOL
class BaseConfig(Enum):
    @property
    def namespace(self):
        return self.value['namespace']

    @property
    def default(self):
        return self.value['default']

    """
        Defaulting to false, asserts that config can be changed by end user in runtime
    """

    @property
    def public(self):
        return self.value.get('public', False)

    """
        Defaulting to empty, holds readable description of the config
    """

    @property
    def description(self):
        return self.value.get('description', '')


class RedisConfigurator(ConfigLoader):
    name = ConfigEnvironment.PERSISTENT.cls

    def __init__(self, initial: BaseConfig = None, **kwargs):
        connector = kwargs.pop('connector', ConfigEnvironment.PERSISTENT.conf.get('connector', Connector()))
        if connector is None:
            connector = Connector()  # initiate default package-wide connection if none given
        self.__conn = connector
        if initial is not None:
            self.init_config(initial)

    @staticmethod
    def valid(cfg: BaseConfig):
        if not isinstance(cfg, BaseConfig):
            return False
        else:
            return True

    def init_config(self, initial):
        if not issubclass(initial, BaseConfig):
            raise NotAValidConfig(f'Provided config {initial} is not BaseConfig subclass')
        for cfg in initial:
            self.__init_config(cfg)

    def __check(self, cfg: BaseConfig):
        return False if self.__conn.keys(config_key(cfg.namespace)).__len__() == 0 else True

    def __init_config(self, cfg):
        if not self.__check(cfg):
            self.set(cfg)
            if cfg.public:
                self.make_public(cfg)

    def __get(self, key):
        return self.__conn.get(key)

    def __set(self, key, value):
        return self.__conn.set(key, value)

    def get(self, cfg: BaseConfig):
        if not RedisConfigurator.valid(cfg):
            raise NotAValidConfig(f'{cfg} is not a BaseConfig subclass')
        if not self.__check(cfg):
            self.__init_config(cfg)
        return self.__get(config_key(cfg.namespace))

    def set(self, cfg: BaseConfig, value=None):
        if not RedisConfigurator.valid(cfg):
            raise NotAValidConfig('set failed: not a valid config')
        if value is None:
            value = cfg.default
        return self.__set(config_key(cfg.namespace), value)

    def is_initialized(self, cfg: BaseConfig):
        if not RedisConfigurator.valid(cfg):
            raise NotAValidConfig('is_initialized got an invalid config')
        return self.__check(cfg)

    def make_public(self, cfg: BaseConfig):
        if not RedisConfigurator.valid(cfg):
            raise NotAValidConfig('Unable to make config public')
        return self.__set(config_publicity_key(cfg.namespace), cfg.description)  # TODO: types

    def unmake_public(self, cfg: BaseConfig):
        if not RedisConfigurator.valid(cfg):
            raise NotAValidConfig(f'Cant unset public status: {cfg} is not a public config')
        if self.__conn.delete(config_publicity_key(cfg.namespace))>0:
            l.info(f'{cfg} is no longer public')
            return True
        else:
            l.warning(f'{cfg} not unset as public since it wasnt in the first place')
            return False  # TODO make self DELETE method

    @property
    def list_public(self):
        res = dict()
        keys = self.__conn.keys(config_publicity_key('*'))
        for key in keys:
            res[config_strip(key)] = self.__get(key)  # return descriptions
        return res

    @property
    def list_config(self) -> dict:
        return {q: self.get_public(q) for q in self.list_public}

    def set_public(self, key, value):
        if key not in self.list_public:
            raise NotPermitted(f'Failed to set {key}: not public')
        return self.__conn.set(config_key(key), value)

    def get_public(self, key):
        if key not in self.list_public:
            raise NotPermitted('{key} is not in public config list')
        return self.__conn.get(config_key(key))

    def check_public(self, key):
        if key not in self.list_public:
            return False
        else:
            return True

    def graceful_shutdown(self):
        self.__conn.graceful_shutdown()



# TODO: in-memory config loader