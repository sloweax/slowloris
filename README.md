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
