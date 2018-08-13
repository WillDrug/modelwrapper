from redis import StrictRedis
from redis.exceptions import ConnectionError
import pickle
from . import Connector, StorageEnvironment, l
from .errors import ConnectorInitFail

# CONNECTORS ARE NOT LOGGED BECAUSE FUCK YOU

class RedisConnector(StrictRedis, Connector):
    name = StorageEnvironment.REDIS.cls

    def __init__(self, **kwargs):
        self.typed = kwargs.pop('typed', StorageEnvironment.REDIS.conf.get('typed', True))
        host = kwargs.pop('host', StorageEnvironment.REDIS.conf.get('host', 'localhost'))
        port = kwargs.pop('port', StorageEnvironment.REDIS.conf.get('port', 6379))
        db = kwargs.pop('db', StorageEnvironment.REDIS.conf.get('db', 0))
        password = kwargs.pop('password', StorageEnvironment.REDIS.conf.get('password', None))
        socket_timeout = kwargs.pop('socket_timeout', StorageEnvironment.REDIS.conf.get('socket_timeout', None))
        socket_connect_timeout = kwargs.pop('socket_connect_timeout',
                                            StorageEnvironment.REDIS.conf.get('socket_connect_timeout', None))
        socket_keepalive = kwargs.pop('socket_keepalive', StorageEnvironment.REDIS.conf.get('socket_keepalive', None))
        socket_keepalive_options = kwargs.pop('socket_keepalive_options',
                                              StorageEnvironment.REDIS.conf.get('socket_keepalive_options', None))
        connection_pool = kwargs.pop('connection_pool', StorageEnvironment.REDIS.conf.get('connection_pool', None))
        unix_socket_path = kwargs.pop('unix_socket_path', StorageEnvironment.REDIS.conf.get('unix_socket_path', None))
        encoding_errors = kwargs.pop('encoding_errors', StorageEnvironment.REDIS.conf.get('encoding_errors', 'strict'))
        charset = kwargs.pop('charset', StorageEnvironment.REDIS.conf.get('charset', None))
        errors = kwargs.pop('errors', StorageEnvironment.REDIS.conf.get('errors', None))
        retry_on_timeout = kwargs.pop('retry_on_timeout', StorageEnvironment.REDIS.conf.get('retry_on_timeout', False))
        ssl = kwargs.pop('ssl', StorageEnvironment.REDIS.conf.get('ssl', False))
        ssl_keyfile = kwargs.pop('ssl_keyfile', StorageEnvironment.REDIS.conf.get('ssl_keyfile', None))
        ssl_certfile = kwargs.pop('ssl_certfile', StorageEnvironment.REDIS.conf.get('ssl_certfile', None))
        ssl_cert_reqs = kwargs.pop('ssl_cert_reqs', StorageEnvironment.REDIS.conf.get('ssl_cert_reqs', None))
        ssl_ca_certs = kwargs.pop('ssl_ca_certs', StorageEnvironment.REDIS.conf.get('ssl_ca_certs', None))
        max_connections = kwargs.pop('max_connections', StorageEnvironment.REDIS.conf.get('max_connections', None))

        encoding = 'utf-8'
        if self.typed:
            decode_responses = False
        else:
            decode_responses = True
        try:
            l.debug(f'Starting connector to {host}:{port}({db})')
            super(RedisConnector, self).__init__(host=host, port=port, db=db, password=password,
                                                 socket_timeout=socket_timeout,
                                                 socket_connect_timeout=socket_connect_timeout,
                                                 socket_keepalive=socket_keepalive,
                                                 socket_keepalive_options=socket_keepalive_options,
                                                 connection_pool=connection_pool, unix_socket_path=unix_socket_path,
                                                 encoding=encoding,
                                                 encoding_errors=encoding_errors, charset=charset, errors=errors,
                                                 decode_responses=decode_responses,
                                                 retry_on_timeout=retry_on_timeout, ssl=ssl, ssl_keyfile=ssl_keyfile,
                                                 ssl_certfile=ssl_certfile,
                                                 ssl_cert_reqs=ssl_cert_reqs, ssl_ca_certs=ssl_ca_certs,
                                                 max_connections=max_connections)
        except ConnectionError:
            raise ConnectorInitFail(f'Failed to connect to redis at {host}:{port}')

    def set(self, key, val, ex=None, px=None, nx=False, xx=False):
        if self.typed:
            val = pickle.dumps(val)
        return super(RedisConnector, self).set(key, val, ex=ex, px=px, nx=nx, xx=xx)

    def get(self, key):
        res = super(RedisConnector, self).get(key)
        if res is None or res == '' or not self.typed:
            return res
        else:
            return pickle.loads(res)

    def graceful_shutdown(self):
        return self.connection_pool.disconnect()

    def keys(self, pattern='*'):
        keys = super(RedisConnector, self).keys(pattern)
        if self.typed:
            keys = [key.decode('utf-8') for key in keys]
        return keys

    # TODO: hmset, hmget, etc


# TODO: in-memory fake connector