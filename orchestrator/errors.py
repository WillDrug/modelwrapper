from . import l


class BaseException(Exception):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return f'{self.__class__}:{self.message}'


class BaseError(BaseException):
    def __init__(self, message):
        self.message = message
        l.error(message)
        pass


class BaseCritical(BaseException):
    def __init__(self, message):
        self.message = message
        l.critical(message)


class NotAValidConfig(BaseCritical):
    pass


class NotAFunction(BaseError):
    pass


class InvalidTaskArguments(BaseError):
    pass


class TaskNotFound(BaseError):
    pass


class ConnectorInitFail(BaseCritical):
    pass

class NotPermitted(BaseError):
    pass

class BorkedException(BaseError):
    pass