

def when(guard):

    def when_decorator(func):
        func.guard = guard
        return func

    return when_decorator

class Test:

    def method(self, *args):
        print("Args: %s" % repr(args))

    @when(lambda self, v1, v2: v1 == v2)
    def method_with_guard(self, *args):
        print("G/Args: %s" % repr(args))

obj = Test()
obj.method(1, 2)

print(dir(obj.method_with_guard))
hasattr(obj.method_with_guard, "guard")
print(obj.method_with_guard.guard(obj, 1, 1))
obj.method_with_guard(1, 2)


from contextlib import contextmanager

class Context:

    def __init__(self):
        self._storage = []

    @contextmanager
    def addbinding(self, name, bind):
        self._storage.append((name, bind))
        yield
        self._storage.pop()

    def __getitem__(self, index):
        return self._storage[-1-index]

    def __len__(self):
        return len(self._storage)

ctx = Context()

with ctx.addbinding("ololo", "name"):
    print(ctx._storage)
    print(ctx[0])
    print(len(ctx))


