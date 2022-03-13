from ememo import proxy_forever, memoize_forever
import tempfile, asyncio

class Counter:
    def __init__(self):
        self.count = 0

    def inc(self):
        self.count += 1
        return self.count

    async def ainc(self):
        self.count += 1
        return self.count

    async def aginc(self):
        self.count += 1
        yield self.count

async def async_test_that_it_runs():
    with tempfile.NamedTemporaryFile() as f:
        x = proxy_forever(f.name, Counter())
        y = Counter()
        y_inc = memoize_forever(f.name, y.inc)
        y_ainc = memoize_forever(f.name, y.ainc)
        y_aginc = memoize_forever(f.name, y.aginc)
        control = Counter()

        for _ in range(2):
            assert x.inc() == 1
            assert await x.ainc() == 2
            assert [z async for z in x.aginc()][0] == 3

        for _ in range(2):
            assert y_inc() == 1
            assert await y_ainc() == 2
            assert [z async for z in y_aginc()][0] == 3

        for i in range(2):
            assert control.inc() == 3*i + 1
            assert await control.ainc() == 3*i + 2
            assert [z async for z in control.aginc()][0] == 3*i + 3

def test_something():
    asyncio.get_event_loop().run_until_complete(async_test_that_it_runs())
    asyncio.get_event_loop().run_until_complete(async_test_that_it_runs())
