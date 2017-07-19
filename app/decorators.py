from threading import Thread


# Async method call wrapper (decorator), use by adding @async on the line preceding the function definition
def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper