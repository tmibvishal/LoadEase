import logging
import os
import json
from flask import Flask, request, jsonify
import requests
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

disable_warnings(InsecureRequestWarning)
app = Flask(__name__)
session = requests.Session()
session.trust_env = False


@app.route('/')
def home():
    return 'Welcome to main host. With Regards - Load Balancing Team'


PORT = 8012


@app.route('/create', methods=['POST'])
def create_vm():
    req = request.get_json()
    # req = json.loads(req)
    print(req)
    # req['mem'], req['cpu'], req['disk'], req['image_path']
    # new_req = {
    #     'cpu_snapshot_path': './cpu_snap.snap',
    #     'memory_snapshot_path': './mem_snap.snap',
    #     'kernel_path': './bzimage-hello-busybox',
    #     'tap_device': 'vm_tap_100',
    #     'resume': False
    # }
    resp = session.post(f'http://10.237.23.38:{PORT}/create', json=req,
                        verify=False)
    return resp.json()


@app.route('/snapshot', methods=['POST'])
def snapshot():
    req = request.get_json()
    # req = json.loads(req)
    print(req)
    os.environ['NO_PROXY'] = 'http://10.237.23.38'
    resp = session.post(f'http://10.237.23.38:{PORT}/snapshot', json=req,
                        verify=False)
    return resp.json()


@app.route('/ping')
def ping():
    return {'success': True}


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', debug=True, port=5010, threaded=True)
