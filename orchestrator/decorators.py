from functools import singledispatch, update_wrapper


def method_singledispatch(func):
    """
    Decorator for method. Used & works the same way as functools.singledispatch decorator
    """
    dispatcher = singledispatch(func)

    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)

    wrapper.register = dispatcher.register
    update_wrapper(wrapper, func)
    return wrapper


