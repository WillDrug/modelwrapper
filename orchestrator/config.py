# The One Config To Rule Them All
from enum import Enum
from .config_loader import BaseConfig
import os

class ApiConfig(BaseConfig):
    # API PART
    API_HOST = {
        'namespace': 'orchestrator.api.host',
        'default': '0.0.0.0',
        'public': True,
        'description': 'API host to run orchestration'
    }
    API_PORT = {
        'namespace': 'orchestrator.api.port',
        'default': 80,
        'public': True,
        'description': 'api port to run orchestration'
    }
    DEBUG = {
        'namespace': 'orchestrator.api.debug',
        'default': bool(os.environ.get('DEBUG_MODE', False)),
        'public': True,
        'description': 'enables DEBUG mode in orchestration API'
    }


class TaskerConfig(BaseConfig):
    # TASKER PART
    WORKER_NUM = {
        'namespace': 'orchestrator.tasker.workers',
        'default': 1,
        'public': True,
        'description': 'number of workers to run'
    }

    TASK_EX = {
        'namespace': 'orchestrator.tasker.task_lifetime',
        'default': 86400,
        'public': True,
        'description': 'Time in seconds after which any task is considered dead and is deleted'
    }

    TASK_RESULT_EX = {
        'namespace': 'orchestrator.tasker.task_expire',
        'default': 3600,
        'public': True,
        'description': 'Timeout for task result hold; Also applies to closed tasks hold time'
    }

    TASK_PATH = {
        'namespace': 'orchestrator.tasker.task_key',
        'default': 'tasker.tasks',
        'public': False,
        'description': 'connector key to store task result objects'
    }
    TASK_SYNC_REFRESH_RATE = {  # fixme : this should really be a blocking call instead of this bollocks
        'namespace': 'orchestrator.tasker.task_sync_refresh',
        'default': 5,
        'public': True,
        'description': 'Determines how often a syncrhous request checks task status'
    }

    TASK_SYNC_TIMEOUT = {
        'namespace': 'orchestrator.tasker.task_sync_timeout',
        'default': 180,
        'public': True,
        'description': 'Timeout for a syncrhonous task call'
    }
    VALIDATE = {
        'namespace': 'orchestrator.tasker.validate_tasks',
        'default': True,
        'public': True,
        'description': 'Check if by default task signatures are validated against provided arguments'
    }


