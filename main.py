import json
import time

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, Response

import utils

app = Flask(__name__)
live_room_dict = {}
audio_room_dict = {}


@app.route('/ver')
def index():
    return '0.1'


@app.route('/token/<user_id>', methods=['POST'])
def get_token(user_id):
    """ 获取指定 ID 的用户 token """
    params = request.get_json()
    key = params['key']
    if key not in live_room_dict.keys():
        live_room_dict[key] = {}
    if key not in audio_room_dict.keys():
        audio_room_dict[key] = {}
    params = {'user_id': user_id}
    template = 'userId={{ user_id }}'
    body = utils.render(params, template)
    return utils.http_post('/user/getToken.json', key, body)


@app.route('/live_room/<room_id>', methods=['POST'])
def create_live_room(room_id):
    """ 创建直播房间 """
    params = request.get_json()
    key = params['key']
    if key not in live_room_dict.keys():
        return '{"code":-1, "reason":"Wrong app key."}', 400
    if room_id in live_room_dict[key].keys():
        return 'Room has already been created!', 409
    live_room_dict[key][room_id] = {
        'user_id': params['user_id'],
        'user_name': params.setdefault('user_name', 'Unknown'),
        'mcu_url': params['mcu_url'],
    }
    return 'OK', 200


@app.route('/live_room/<room_id>', methods=['DELETE'])
def remove_live_room(room_id):
    """ 销毁直播房间 """
    params = request.get_json()
    key = params['key']
    if key not in live_room_dict.keys():
        return '{"code":-1, "reason":"Wrong app key."}', 400
    live_room_dict[key].pop(room_id)
    return 'OK', 200


@app.route('/live_room')
def get_live_room_list():
    """ 获取直播房间列表 """
    params = request.get_json()
    key = params['key']
    if key not in live_room_dict.keys():
        return '{"code":-1, "reason":"Wrong app key."}', 400
    return json.dumps(live_room_dict[key]), 200


@app.route('/audio_room/<room_id>', methods=['POST'])
def create_audio_room(room_id):
    """ 创建语聊房间 """
    params = request.get_json()
    key = params['key']
    if key not in audio_room_dict.keys():
        return '{"code":-1, "reason":"Wrong app key."}', 400
    if room_id in audio_room_dict[key].keys():
        return 'Room has already been created!', 409
    audio_room_dict[key][room_id] = {
        'user_id': params['user_id'],
        'user_name': params.setdefault('user_name', 'Unknown'),
        'mcu_url': params['mcu_url'],
    }
    return 'OK', 200


@app.route('/audio_room/<room_id>', methods=['DELETE'])
def remove_audio_room(room_id):
    """ 销毁语聊房间 """
    params = request.get_json()
    key = params['key']
    if key not in audio_room_dict.keys():
        return '{"code":-1, "reason":"Wrong app key."}', 400
    audio_room_dict[key].pop(room_id)
    return 'OK', 200


@app.route('/audio_room')
def get_audio_room_list():
    """ 获取语聊房间列表 """
    params = request.get_json()
    key = params['key']
    if key not in audio_room_dict.keys():
        return '{"code":-1, "reason":"Wrong app key."}', 400
    return json.dumps(audio_room_dict[key]), 200


def destroy_invalid_room():
    for app in list(live_room_dict.keys()):
        for key in list(live_room_dict[app].keys()):
            body = '{"roomId":"' + key + '"}'
            resp, code = utils.http_post('/rtc/room/query.json', app, body, is_rtc=True)
            if code == 200 and resp['code'] == 40003:
                del live_room_dict[app][key]
    for app in list(audio_room_dict.keys()):
        for key in list(audio_room_dict[app].keys()):
            body = '{"roomId":"' + key + '"}'
            resp, code = utils.http_post('/rtc/room/query.json', app, body, is_rtc=True)
            if code == 200 and resp['code'] == 40003:
                del audio_room_dict[app][key]


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(destroy_invalid_room, 'cron', minute='0-59/5')
    scheduler.start()
    app.run(host='0.0.0.0', port=8080, threaded=True)
