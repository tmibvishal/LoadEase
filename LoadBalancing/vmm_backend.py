import requests

from common_config import CREATE_END_POINT, SNAPSHOT_END_POINT
from redis_config import rds
import json
from LoadBalancing.utils import deserialize_rds_dict, \
    deserialize_rds_str_list, \
    add_data_to_redis
import uuid

from redis_functions import get_current_host_id, get_vm_id_with_rpc_port


def create_vm_request(host_id, vm_config):
    # request_format = {
    #     'mem': 100,
    #     'cpu': 1,
    #     'disk': 100,
    #     'image_path': 'path',
    #     'create': True
    # }
    request = vm_config.copy()
    # request['image_path'] = 'path'
    # request['create'] = True

    vmm_proxy_addr = rds.get(f"vmm_proxy_addr:{host_id}")

    resp = requests.post(f'{vmm_proxy_addr}/{CREATE_END_POINT}', json=request).json()
    resp = json.loads(resp)
    print(resp)
    return resp


def migrate_vm(vm_id, new_host_id):

    vm_config = deserialize_rds_dict(rds.hgetall(f'vm_configs:{vm_id}'))
    old_host = vm_config['host_id']
    rpc_port = vm_config['rpc_port']

    migratiion_uuid = str(uuid.uuid4())

    # pause vm in old host
    vmm_proxy_addr = rds.get(f"vmm_proxy_addr:{old_host}").decode()

    request = {
        'cpu_snapshot_path': f'/snapshots/{migratiion_uuid}.cpu',
        'memory_snapshot_path': f'/snapshots/{migratiion_uuid}.mem',
        'rpc_port': rpc_port,
        'resume' : False
    }

    assert vm_id == get_vm_id_with_rpc_port(rpc_port)

    resp = requests.post(f'{vmm_proxy_addr}/{SNAPSHOT_END_POINT}', json=request).json()
    resp = json.loads(resp)
    print(resp)

    # TODO: Delete all the previous VM data from redis


    # start vm in new host
    vmm_proxy_addr = rds.get(f"vmm_proxy_addr:{new_host_id}").decode()

    request = {
        'cpu_snapshot_path': f'/snapshots/{migratiion_uuid}.cpu',
        'memory_snapshot_path': f'/snapshots/{migratiion_uuid}.mem',
        'resume' : True
    }

    resp = requests.post(f'{vmm_proxy_addr}/{CREATE_END_POINT}', json=request).json()
    resp = json.loads(resp)

    rds.hset(name='rpc_ports', key=vm_id, value=rpc_port)

    print(resp)

    # TODO: Add all the new VM data from redis
    add_data_to_redis(host_id=new_host_id,
                      vm_id=vm_id,
                      mem_mb=vm_config['mem'],
                      cpu_cores=vm_config['cpu'],
                      image_path=vm_config['image_path'],
                      pid=vm_config['pid'],
                      tap_device=vm_config['tap_device'],
                      rpc_port=rpc_port)

    # new_rpc_port = resp['rpc_port']

    # TODO Do all this and update redis in caller
    # vm_config['host_id'] = new_host_id
    # vm_config['rpc_port'] = new_rpc_port 

    return resp