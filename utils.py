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

APP_SECRET = {
    'e0x9wycfx7flq' : ['UfmrYyG1lpE', 'http://apixq.rongcloud.net'],
    'c9kqb3rdkbb8j' : ['uTNrkYskbNC', 'http://apiserverqa.cn.ronghub.com'],
    'z3v5yqkbv8v30' : ['vRSwt4t69JFg', 'https://api.cn.ronghub.com'],
    'qf3d5gbjq962h' : ['4XHbT4dpJs', 'https://api.cn.ronghub.com'],
    'qd46yzrfq04ef' : ['TMr47yh4WxM5', 'http://apiserverqa.cn.ronghub.com'],
    'y745wfm8yhb3v' : ['CshYsnmzTGfR', 'http://api.cn.ronghub.com'],
}


def _http_header(key):
    nonce = str(random.randint(0, 1000000000))
    timestamp = str(int(time.time()))
    sha1 = (APP_SECRET[key][0] + nonce + timestamp).encode('utf8')
    signature = hashlib.sha1(sha1).hexdigest()
    return {
        HEADER_CONTENT_TYPE: 'application/x-www-form-urlencoded',
        HEADER_APP_KEY: key,
        HEADER_NONCE: nonce,
        HEADER_TIMESTAMP: timestamp,
        HEADER_SIGNATURE: signature
    }


def render(params, format_str):
    template = Template(format_str)
    data = template.render(params)
    return data


def http_post(url, key, data):
    if key not in APP_SECRET.keys():
        return '{"code":-1, "reason":"Wrong app key."}', 400
    headers = _http_header(key)
    data = data.encode('utf8')
    host = APP_SECRET[key][1]
    try:
        req = request.Request(host + url, headers=headers, data=data)
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
