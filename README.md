## Usage
```
usage: slowloris.py [-h] [--workers WORKERS] [--interval SECONDS] [--timeout SECONDS] [--read-rate SECONDS] [--write-rate SECONDS] [-H HEADER] [-X REQUEST] [-d DATA] [-x PROXY]
                    [--proxy-file FILE]
                    url

positional arguments:
  url

options:
  -h, --help            show this help message and exit
  --workers WORKERS     (default: 8)
  --interval SECONDS    interval between requests (default: 1)
  --timeout SECONDS     connection timeout (default: 15)
  --read-rate SECONDS   bytes/second (default: 0.05)
  --write-rate SECONDS  bytes/second (default: 0.05)
  -H HEADER, --header HEADER
                        add custom header
  -X REQUEST, --request REQUEST
                        request method (default: GET)
  -d DATA, --data DATA
  -x PROXY, --proxy PROXY
                        (example: socks5://...)
  --proxy-file FILE     load all line separated proxies from FILE
```
