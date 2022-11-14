import random

from LoadBalancing.utils import create_virtual_machine, stop_virtual_machine, \
    get_int_from_vm_id

import logging
import json
from flask import Flask, request, jsonify

from LoadBalancing import balancer
from LoadBalancing.utils import create_virtual_machine
from common_config import SNAPSHOT_END_POINT, CREATE_END_POINT
from redis_config import rds
from redis_functions import get_vm_pid, get_vm_id_with_rpc_port
import hashlib

app = Flask(__name__)


@app.route('/')
def home():
    return 'Welcome to Temporary Flask Server. ' \
           'With Regards - Load Balancing Team'


@app.route(f'/{SNAPSHOT_END_POINT}', methods=['POST'])
def snapshot():
    # TODO: Save Previous VM ID and close the VM

    # Check that rpc_port as given while creating the VM
    req = request.get_json()
    rpc_port = req['rpc_port']
    vm_id = get_vm_id_with_rpc_port(rpc_port)
    # Stop VM with id vm_id
    stop_virtual_machine(vm_id)
    return jsonify({'success': True, 'response': 'Snapshot Taken'})


@app.route(f'/{CREATE_END_POINT}', methods=['POST'])
def create():
    # TODO: Delete Previous VM ID data and reinsert new ID.
    vm = request.get_json()
    vm_id = create_virtual_machine(mem_mb=vm['mem'],
                                   tap_device=vm['tap_device'],
                                   cpu_cores=vm['cpu'])
    rpc_port = get_int_from_vm_id(vm_id)
    temp = rds.hget(name='rpc_ports', key=vm_id)
    if temp is not None:
        assert temp == rpc_port
    return jsonify({'success': True,
                    'response': 'Created New VM',
                    'rpc_port': rpc_port,
                    'pid': get_vm_pid(vm_id)})


@app.route('/ping')
def ping():
    return {'success': True}


def start_vm_listener_flask_server(port: int):
    app.run(host='0.0.0.0', debug=True, port=port, threaded=True)
