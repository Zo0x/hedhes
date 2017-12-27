import threading
import multiprocessing
from app import app


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


# Async method call wrapper (decorator), use by adding @async on the line preceding the function definition
def async(f):
    def wrapper(*args, **kwargs):
        if app.config.get('ASYNC_ENABLED'):
            thr = StoppableThread(target=f, args=args, kwargs=kwargs)
            thr.start()
            return thr
        else:
            return f(*args, **kwargs)
    return wrapper


def asyncp(f):
    def wrapper(*args, **kwargs):
        if app.config.get('ASYNC_ENABLED'):
            proc = multiprocessing.Process(target=f, args=args, kwargs=kwargs)
            proc.start()
            return proc
        else:
            return f(*args, **kwargs)
    return wrapper
