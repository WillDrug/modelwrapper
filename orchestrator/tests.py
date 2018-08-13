import unittest

import time

from . import Conductor, Connector, ConfigLoader, Api, Tasker
from . import StorageEnvironment, ConfigEnvironment, ApiEnvironment, TaskEnvironment
from .config_loader import BaseConfig
Conductor.STORAGE = StorageEnvironment.REDIS
Conductor.STORAGE.conf['db'] = 13
Conductor.CONFIG = ConfigEnvironment.PERSISTENT
Conductor.API = ApiEnvironment.WEB_FLASK
Conductor.API.conf['port'] = 80
Conductor.API.conf['host'] = '0.0.0.0'
Conductor.API.conf['debug'] = True
Conductor.TASKER = TaskEnvironment.THREAD


class ConnectorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.connector = Connector()
        cls.connector.flushdb()
        super().setUpClass()

    def setUp(self):
        self.connector.flushdb()

    def test_set(self):
        self.assertTrue(self.connector.set('testkey', [1, 2, 3]))

    def test_get(self):
        self.connector.set('test', True)
        self.assertTrue(self.connector.get('test'))

    def test_keys(self):
        self.connector.set('key1', '1')
        self.connector.set('key2', '2')
        self.assertEqual(set(self.connector.keys('*')), {'key1', 'key2'})

    def test_delete(self):
        self.connector.set('test_del', True)
        self.connector.delete('test_del')
        self.assertEqual(self.connector.get('test_del'), None)

class TestConfig(BaseConfig):
    INT_KEY = {
        'namespace': 'test.numeric',
        'default': 1,
        'public': False,
        'description': 'Test of int type'
    }
    BOOL_KEY = {
        'namespace': 'test.bool',
        'default': True,
        'public': True,
        'description': 'Test of bool type'
    }
    TEXT_KEY = {
        'namespace': 'test.str',
        'default': 'test',
        'public': False,
        'description': 'Test of str type'
    }
class NotConfig(BaseConfig):
    NONNA = {
        'namespace': 'no',
        'default': 'no',
        'public': False,
        'description': 'will not be initialized or used'
    }
from orchestrator.errors import NotAValidConfig, NotPermitted
class ConfigLoaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conn = Connector()
        conn.flushdb()
        cls.config = ConfigLoader()
        super().setUpClass()

    def setUp(self):
        """ returns config to default state """
        for cfg in TestConfig:
            self.config.set(cfg)
            if self.config.check_public(cfg.namespace) and not cfg.public:
                self.config.unmake_public(cfg)
            if not self.config.check_public(cfg.namespace) and cfg.public:
                self.config.make_public(cfg)

    def test_valid(self):
        self.assertTrue(self.config.valid(TestConfig.INT_KEY))
        self.assertFalse(self.config.valid('lolz'))

    def test_get(self):
        self.assertEqual(self.config.get(TestConfig.INT_KEY), 1)
        self.assertEqual(self.config.get(TestConfig.BOOL_KEY), True)
        self.assertEqual(self.config.get(TestConfig.TEXT_KEY), 'test')
        with self.assertRaises(NotAValidConfig):
            self.config.get('lolz')

    def test_set(self):
        self.config.set(TestConfig.INT_KEY, 5)
        self.assertEqual(self.config.get(TestConfig.INT_KEY), 5)
        with self.assertRaises(NotAValidConfig):
            self.config.set('lol', 'kek')

    def test_is_initialized(self):
        self.assertTrue(self.config.is_initialized(TestConfig.INT_KEY))
        self.assertFalse(self.config.is_initialized(NotConfig.NONNA))
        with self.assertRaises(NotAValidConfig):
            self.config.is_initialized('cheburek')

    def test_make_public(self):
        self.assertTrue(self.config.make_public(TestConfig.TEXT_KEY))
        self.assertEqual(self.config.get_public('test.str'), 'test')
        with self.assertRaises(NotAValidConfig):
            self.config.make_public('fizz')

    def test_unmake_public(self):
        self.assertTrue(self.config.unmake_public(TestConfig.BOOL_KEY))
        with self.assertRaises(NotPermitted):
            self.config.get_public('test.bool')

    def test_list_public(self):
        self.assertEqual(set(self.config.list_public.keys()), {'test.bool'})

    def test_set_public(self):
        self.config.set_public('test.bool', False)
        self.assertFalse(self.config.get_public('test.bool'))
        with self.assertRaises(NotPermitted):
            self.config.set_public('nonna', 'this')

    def test_get_public(self):
        self.assertTrue(self.config.get_public('test.bool'))

    def test_check_public(self):
        self.assertTrue(self.config.check_public('test.bool'))
        self.assertFalse(self.config.check_public('test.str'))

from .errors import NotAFunction, InvalidTaskArguments, TaskNotFound

def test_function(strict, non_strict='non_strict'):
    return dict(strict=strict, non_strict=non_strict)

class TaskerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = Connector()
        cls.tasker = Tasker()

    def test_get_self_status(self):
        self.assertEqual(set(self.tasker.get_self_status().keys()), {'threads_alive', 'max_threads'})


    def test_register_task(self):
        self.assertTrue(self.tasker.register_task('test_task_register', test_function))
        with self.assertRaises(NotAFunction):
            self.tasker.register_task('test_task_register', 'notafunction')

    def test_run_task(self):
        self.tasker.register_task('test_task_run', test_function)
        with self.assertRaises(TaskNotFound):
            self.tasker.run_task('not_exists')
        self.assertEqual(
            self.tasker.run_task('test_task_run', args=['strict'], kwargs={'non_strict': 'non'}, blocking=True).result[0],
            dict(strict='strict', non_strict='non')
        )
        trw = self.tasker.run_task('test_task_run', blocking=True)
        trw = self.tasker.get_task_info(trw.tid)
        self.assertIsInstance(trw.result[0], InvalidTaskArguments)

    def test_get_task_info(self):
        self.tasker.register_task('test_task_get', test_function)
        trw = self.tasker.run_task('test_task_get', ['strict'], kwargs={'non-strict': 'non'})
        res = self.tasker.get_task_info(trw.tid)
        self.assertEqual(res.__class__, Tasker.TaskResultWrapper)
        self.assertEqual(res.ident[0], trw.tid)
        self.assertEqual(self.tasker.get_task_info('notask'), None)

    def test_add_pre(self):
        self.tasker.register_task('test_task_add_pre', test_function)
        # True
        self.tasker.add_pre('test_task_add_pre', test_function)
        # tasknotfound
        with self.assertRaises(TaskNotFound):
            self.tasker.add_pre('notask', test_function)
        # invalid function
        with self.assertRaises(NotAFunction):
            self.tasker.add_pre('test_task_add_pre', 'lolz')
        # TODO: figure out how to test actual pre-exec run

    def test_add_post(self):
        self.tasker.register_task('test_task_add_post', test_function)
        # True
        self.tasker.add_post('test_task_add_post', test_function)
        # tasknotfound
        with self.assertRaises(TaskNotFound):
            self.tasker.add_post('notask', test_function)
        # invalid function
        with self.assertRaises(NotAFunction):
            self.tasker.add_post('test_task_add_post', 'lolz')
        # TODO: figure out how to test actual post-exec run

class ApiTest(unittest.TestCase):
    pass
    # TODO: test cases for API