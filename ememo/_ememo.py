import pickle, inspect, atexit

class CallHook:
    def __init__(self, wrapped, hook, async_hook=None, agen_hook=None):
        self.x = wrapped
        self.f = hook
        self.af = async_hook
        self.ag = agen_hook
        self.cache = {}

    def __getattr__(self, key):
        try:
            return self.cache[key]
        except KeyError:
            obj = getattr(self.x, key)
            if inspect.isasyncgenfunction(obj) and self.ag:
                rtn = self.ag(obj)
            elif inspect.iscoroutinefunction(obj) and self.af:
                rtn = self.af(obj)
            elif callable(obj):
                rtn = self.f(obj)
            else:
                rtn = obj
            self.cache[key] = rtn
            return rtn

def create_persist(fname):
    def dec(c):
        def __init__(self, f):
            self.f = f
            try:
                with open(fname, 'rb') as f:
                    self.cache = pickle.load(f)
            except (FileNotFoundError, EOFError):
                self.cache = {}
            atexit.register(self.cleanup)

        def cleanup(self):
            try:
                with open(fname, 'rb') as f:
                    rtn = pickle.load(f)
                    rtn.update(self.cache)
            except (FileNotFoundError, EOFError):
                rtn = self.cache
            with open(fname, 'wb') as f:
                pickle.dump(rtn, f)

        c.__init__ = __init__
        c.cleanup = cleanup
        return c

    def keygen(f, a, k):
        return (f.__name__, a, k)

    @dec
    class persist:
        def __call__(self, *a, **k):
            key = pickle.dumps(keygen(self.f, a, k))
            try:
                return self.cache[key]
            except KeyError:
                rtn = self.cache[key] = self.f(*a, **k)
                return rtn

    @dec
    class apersist:
        async def __call__(self, *a, **k):
            key = pickle.dumps(keygen(self.f, a, k))
            try:
                return self.cache[key]
            except KeyError:
                rtn = self.cache[key] = await self.f(*a, **k)
                return rtn

    @dec
    class agpersist:
        async def __call__(self, *a, **k):
            key = pickle.dumps(keygen(self.f, a, k))
            try:
                for item in self.cache[key]:
                    yield item
            except KeyError:
                rtn = self.cache[key] = [x async for x in self.f(*a, **k)]
                for item in rtn:
                    yield item

    return persist, apersist, agpersist

def proxy_forever(fname, obj):
    return CallHook(obj, *create_persist(fname))

def memoize_forever(fname, f):
    class Wrapper:
        def call(self, *a, **k):
            return f(*a, **k)
        async def acall(self, *a, **k):
            return await f(*a, **k)
        async def agcall(self, *a, **k):
            async for x in f(*a, **k):
                yield x
    proxy = proxy_forever(fname, Wrapper())
    if inspect.isasyncgenfunction(f):
        async def rtn(*a, **k):
            async for x in proxy.agcall(*a, **k):
                yield x
        return rtn
    elif inspect.iscoroutinefunction(f):
        async def rtn(*a, **k):
            return await proxy.acall(*a, **k)
        return rtn
    elif callable(f):
        return lambda *a, **k: proxy.call(*a, **k)
    raise Exception('Not callable')

__all__ = ['proxy_forever', 'memoize_forever']
