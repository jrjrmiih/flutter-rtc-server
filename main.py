import json
import time

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, Response

import utils

app = Flask(__name__)
live_room_dict = {}
audio_room_dict = {}
user_dict = {}


@app.route('/ver')
def index():
    return '0.1'


@app.route("/avatar/<image_id>.png")
def get_avatar(image_id):
    """ 获取指定序号的用户头像，image_id: [0-19] """
    image = int(image_id)
    if image < 0 or image > 19:
        return 'Image id should be between 0-19!', 400
    with open(r'avatar/{:0>2d}.png'.format(image), 'rb') as f:
        return Response(f.read(), mimetype="image/png")


@app.route('/token/<user_id>', methods=['POST'])
def get_token(user_id):
    """ 获取指定 ID 的用户 token """
    params = {'user_id': user_id}
    template = 'userId={{ user_id }}'
    body = utils.render(params, template)
    return utils.http_post('/user/getToken.json', body)


@app.route('/user/<user_id>', methods=['POST'])
def create_user(user_id):
    """ 创建在线用户，在 IM 连接成功后调用 """
    if user_id in user_dict.keys():
        return 'User has already been created!', 409
    params = request.get_json()
    user_dict[user_id] = {
        'user_name': params['user_name'],
        'portrait_id': params['portrait_id'],
        'last_time': int(time.time())
    }
    return 'OK', 200


@app.route('/user/<user_id>', methods=['DELETE'])
def remove_user(user_id):
    """ 删除在线用户，在退出时调用 """
    user_dict.pop(user_id)
    return 'OK', 200


@app.route('/user/<user_id>')
def get_user(user_id):
    """ 获取在线用户信息 """
    if user_id not in user_dict.keys():
        return 'User not found!', 404
    user = user_dict[user_id].copy()
    user.pop('last_time')
    return json.dumps(user), 200


@app.route('/user/<user_id>', methods=['PUT'])
def ping_user(user_id):
    """ 保持用户在线，1 分钟调用一次，超过 2 分钟没有调用会被服务器清理掉 """
    if user_id not in user_dict.keys():
        return 'User not found!', 404
    user_dict[user_id]['last_time'] = int(time.time())
    return 'OK', 200


@app.route('/live_room/<room_id>', methods=['POST'])
def create_live_room(room_id):
    """ 创建直播房间 """
    if room_id in live_room_dict.keys():
        return 'Room has already been created!', 409
    params = request.get_json()
    live_room_dict[room_id] = {
        'user_id': params['user_id'],
        'user_name': params.setdefault('user_name', default='Unknown'),
        'mcu_url': params['mcu_url'],
    }
    return 'OK', 200


@app.route('/live_room/<room_id>', methods=['DELETE'])
def remove_live_room(room_id):
    """ 销毁直播房间 """
    live_room_dict.pop(room_id)
    return 'OK', 200


@app.route('/live_room')
def get_live_room_list():
    """ 获取直播房间列表 """
    return json.dumps(live_room_dict), 200


@app.route('/audio_room/<room_id>', methods=['POST'])
def create_audio_room(room_id):
    """ 创建语聊房间 """
    if room_id in audio_room_dict.keys():
        return 'Room has already been created!', 409
    params = request.get_json()
    audio_room_dict[room_id] = {
        'user_id': params['user_id'],
        'user_name': params.setdefault('user_name', default='Unknown'),
        'mcu_url': params['mcu_url'],
    }
    return 'OK', 200


@app.route('/audio_room/<room_id>', methods=['DELETE'])
def remove_audio_room(room_id):
    """ 销毁语聊房间 """
    audio_room_dict.pop(room_id)
    return 'OK', 200


@app.route('/audio_room')
def get_audio_room_list():
    """ 获取语聊房间列表 """
    return json.dumps(audio_room_dict), 200


def destroy_invalid_user():
    for key in list(user_dict.keys()):
        delta = int(time.time()) - user_dict[key]['last_time']
        print('user = ' + key + ', delta = ' + str(delta))
        if delta > 120:
            del user_dict[key]


def destroy_invalid_room():
    for key in list(live_room_dict.keys()):
        body = '{"roomId":"' + key + '"}'
        resp, code = utils.http_post('/rtc/room/query.json', body, is_rtc=True)
        if code == 200 and resp['code'] == 40003:
            del live_room_dict[key]
    for key in list(audio_room_dict.keys()):
        body = '{"roomId":"' + key + '"}'
        resp, code = utils.http_post('/rtc/room/query.json', body, is_rtc=True)
        if code == 200 and resp['code'] == 40003:
            del audio_room_dict[key]


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(destroy_invalid_user, 'cron', minute='0-59')
    scheduler.add_job(destroy_invalid_room, 'cron', minute='0-59/5')
    scheduler.start()
    app.run(host='0.0.0.0', port=8080, threaded=True)
