import inspect
import logging
import os as _os
from abc import ABCMeta, abstractmethod
from functools import partialmethod
from logging.handlers import RotatingFileHandler

#  fixme:  switch to ConfigLoader
class AbstractLogger(metaclass=ABCMeta):
    def __init__(self, *args, **kwargs):
        super().__init__()

    @classmethod
    def get_new(cls, name: str):
        return {x.__name__: x for x in cls.__subclasses__()}[name]

    @abstractmethod
    def _log(self, msg, level, **kwargs): pass

    @abstractmethod
    def debug(self, msg, **kwargs): pass

    @abstractmethod
    def info(self, msg, **kwargs): pass

    @abstractmethod
    def warning(self, msg, **kwargs): pass

    @abstractmethod
    def error(self, msg, **kwargs): pass

    @abstractmethod
    def critical(self, msg, **kwargs): pass


class DefaultLogger(AbstractLogger):
    """
    Wrapper for default logger
    """
    SOURCE_KWARG = 'source'  # custom log field

    def __init__(
            self, logs_dir='logs', trace_path='trace.log', error_path='error.log', max_trace_size=100,
            max_error_size=100, trace_backup=2, error_backup=2, module_name=None, std_out=False,
            trace_log_level='INFO',
    ):

        super().__init__()
        __error_flag = False
        try:
            logging_level = getattr(logging, trace_log_level.upper())
        except AttributeError:
            logging_level = logging.INFO
            __error_flag = True
        verbose_name = logging.getLevelName(logging_level)

        if not _os.path.exists(_os.path.join(logs_dir)):
            _os.makedirs(_os.path.join(logs_dir))

        self.__logger = logging.getLogger(module_name if module_name else __name__)
        self.__logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            f'%(asctime)s - %(process)s - %(levelname)s - %({DefaultLogger.SOURCE_KWARG})s - %(message)s'
        )

        trace_handler = RotatingFileHandler(
            _os.path.join(logs_dir, trace_path),
            maxBytes=max_trace_size * 1024 * 1024,
            backupCount=trace_backup,
        )
        trace_handler.setLevel(logging_level)
        trace_handler.setFormatter(formatter)

        error_handler = RotatingFileHandler(
            _os.path.join(logs_dir, error_path),
            maxBytes=max_error_size * 1024 * 1024,
            backupCount=error_backup,
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(formatter)

        self.__logger.addHandler(trace_handler)
        self.__logger.addHandler(error_handler)

        if std_out is True:
            std_handler = logging.StreamHandler()
            std_handler.setLevel(logging_level)
            std_handler.setFormatter(formatter)
            self.__logger.addHandler(std_handler)
        pass

        if __error_flag:
            self.warning(f'Failed to set provided log level = {verbose_name}. Falling back to default level')
        if logging_level == logging.DEBUG:
            self.warning(f"USING {verbose_name} MODE")

        self.info(f'Logger is loaded. Current trace logging level = {verbose_name}')

    @property
    def logger(self):
        return self.__logger

    def _log(self, msg, level=logging.INFO, **kwargs):
        if DefaultLogger.SOURCE_KWARG not in kwargs:
            try:
                __outer_frame = inspect.getouterframes(inspect.currentframe())[2]
            except IndexError:
                __outer_frame = inspect.getouterframes(inspect.currentframe())[1]
            __caller_frame = __outer_frame[0]
            __file = __outer_frame[1]
            __line = __outer_frame[2]
            __method = __outer_frame[3]
            try:
                __cls = __caller_frame.f_locals["self"].__class__.__name__
            except KeyError:
                __cls = None
            kwargs['source'] = f'{__file} # Class: {__cls} # Method: {__method} # Line: {__line}'

        self.logger.log(level if level.__class__ is int else logging.INFO, msg, extra=kwargs)

    __debug = partialmethod(_log, level=logging.DEBUG)
    __info = partialmethod(_log, level=logging.INFO)
    __warning = partialmethod(_log, level=logging.WARNING)
    __error = partialmethod(_log, level=logging.ERROR)
    __critical = partialmethod(_log, level=logging.CRITICAL)

    def debug(self, msg, **kwargs):
        self.__debug(msg, **kwargs)

    def info(self, msg, **kwargs):
        self.__info(msg, **kwargs)

    def warning(self, msg, **kwargs):
        self.__warning(msg, **kwargs)

    def error(self, msg, **kwargs):
        self.__error(msg, **kwargs)

    def critical(self, msg, **kwargs):
        self.__critical(msg, **kwargs)
