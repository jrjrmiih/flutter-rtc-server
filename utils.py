import hashlib
import json
import random
import socket
import time
from urllib import request
from urllib.error import HTTPError, URLError

from jinja2 import Template

HEADER_APP_KEY = 'App-Key'
HEADER_NONCE = 'Nonce'
HEADER_TIMESTAMP = 'Timestamp'
HEADER_SIGNATURE = 'Signature'
HEADER_CONTENT_TYPE = 'Content-Type'

APP_KEY = 'z3v5yqkbv8v30'
APP_SECRET = 'vRSwt4t69JFg'


def _http_header():
    nonce = str(random.randint(0, 1000000000))
    timestamp = str(int(time.time()))
    sha1 = (APP_SECRET + nonce + timestamp).encode('utf8')
    signature = hashlib.sha1(sha1).hexdigest()
    return {
        HEADER_CONTENT_TYPE: 'application/x-www-form-urlencoded',
        HEADER_APP_KEY: APP_KEY,
        HEADER_NONCE: nonce,
        HEADER_TIMESTAMP: timestamp,
        HEADER_SIGNATURE: signature
    }


def render(params, format_str):
    template = Template(format_str)
    data = template.render(params)
    return data


def http_post(url, data):
    data = data.encode('utf8')
    headers = _http_header()
    try:
        req = request.Request('http://api.cn.ronghub.com' + url, headers=headers, data=data)
        rep_bytes = request.urlopen(req).read()
        rep = json.loads(rep_bytes.decode('utf8'))
        code = 200
    except HTTPError as e:
        rep = e.read()
        code = e.code
    except URLError:
        rep = '{"code":-1, "reason":"Url not found."}'
        code = 404
    except socket.timeout:
        rep = '{"code":-1, "reason":"Http request timeout."}'
        code = 504
    return rep, code
