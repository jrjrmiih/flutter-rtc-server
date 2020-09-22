import json
import time

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request

import utils

app = Flask(__name__)
room_dict = {}


@app.route('/ver')
def index():
    return '0.1'


@app.route('/token/<user_id>', methods=['POST'])
def get_token(user_id):
    params = {'user_id': user_id}
    template = 'userId={{ user_id }}'
    body = utils.render(params, template)
    return utils.http_post('/user/getToken.json', body)


@app.route('/live_room/<room_id>', methods=['POST'])
def create_live_room(room_id):
    params = request.get_json()
    room_dict[room_id] = {
        'user_id': params['user_id'],
        'mcu_url': params['mcu_url'],
    }
    return 'OK', 200


@app.route('/live_room/<room_id>', methods=['DELETE'])
def remove_live_room(room_id):
    room_dict.pop(room_id)
    return 'OK', 200


@app.route('/live_room', methods=['GET'])
def get_live_room():
    return json.dumps(room_dict), 200


def destroy_invalid_room():
    for key in list(room_dict.keys()):
        body = '{"roomId":"' + key + '"}'
        resp, code = utils.http_post('/rtc/room/query.json', body, is_rtc=True)
        if code == 200 and resp['code'] == 40003:
            del room_dict[key]


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(destroy_invalid_room, 'cron', minute='0-59/5')
    scheduler.start()
    app.run(host='0.0.0.0', port=8080)
