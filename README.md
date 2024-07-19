## Usage
```
usage: slowloris.py [-h] [-H HEADER] [--workers WORKERS] [--interval SECONDS] [--timeout SECONDS] [--read-rate SECONDS] [--write-rate SECONDS] [-x PROXY] url

positional arguments:
  url

options:
  -h, --help            show this help message and exit
  -H HEADER, --header HEADER
                        add custom header
  --workers WORKERS     default: 8
  --interval SECONDS    interval between requests default: 1
  --timeout SECONDS     connection timeout default: 15
  --read-rate SECONDS   bytes/second default: 0.05
  --write-rate SECONDS  bytes/second default: 0.05
  -x PROXY, --proxy PROXY
```
