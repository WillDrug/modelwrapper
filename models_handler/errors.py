from orchestrator import logger


class BaseError(Exception):
    """
    Generic exception with logger
    """

    def __init__(self, message: str) -> None:
        logger.log(message)


class WrongModelError(BaseError):
    """
    Used to indicate wrong model name
    """
    pass


class InterfaceNotImplementedError(BaseError):
    """
    Indicates that basic Model module has no class implementing ModelInterface
    """
    pass


class ModeSelectingError(BaseError):
    """
    Generic error for running mode selection
    """
    pass
