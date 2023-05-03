from .task import Partial

def taskmap(f, arglist, *args, **kwargs):
    return [Partial(f, arg, *args, **kwargs) for arg in arglist]

def taskwrap(f, *args, **kwargs):
    return [Partial(f, *args, **kwargs)]
