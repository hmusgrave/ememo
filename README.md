# ememo

Eternal memoization

## Purpose

When web scraping it often takes a lot of iterations and debug cycles to figure
out exactly how to interpret each web page. Actually hitting the remote server
every time is impolite and prone to triggering IP bans. Instead we can wrap
those http calls with a simple file-based memoizer to only hit the remote
server once no matter how many times we run our script.

## Installation

```
pip install -e git+https://github.com/hmusgrave/ememo.git#egg=ememo
```

## Examples

Proxy all calls from an object.

```python
from ememo import proxy_forever
import httpx

# All function calls and coroutines in httpx are proxied
# through our eternal cache
httpx = proxy_forever('cache.txt', httpx)

# Sends http request the first program execution and
# loads from a cache subsequently
response = httpx.get('https://example.com/')

# Always loads from a cache
response = httpx.get('https://example.com/')
```

Memoize a single callable. Async is supported.

```python
from ememo import memoize_forever
from functools import partial
import asyncio
import httpx
client = httpx.AsyncClient()

# We can just memoize a single function if desired
@partial(memoize_forever, 'cache.txt')
async def get(url):
    return await client.get(url)

# Alternatively:
# 
# async def get(url):
#     return await client.get(url)
# get = memoize_forever('cache.txt', get)

async def main():
    url = 'https://example.com/'

    # Sends 1 http request (on first run)
    a = await get(url)

    # Always pulls from cache
    b = await get(url)

    # We only memoized `get`, not `client.get`, so
    # this also sends an http request
    c = await client.get(url)

asyncio.run(main())
```
