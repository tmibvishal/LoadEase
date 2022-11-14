import socket
import sys
import os
import uuid
from datetime import datetime
from typing import List

from redis_config import rds


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_ip():
    """
    :return: Returns the IP Address of current system
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def get_vm_id_with_rpc_port(rpc_port: int) -> str:
    d = rds.hgetall('rpc_ports')
    vm_id = ''
    for k, v in d.items():
        if v == rpc_port:
            vm_id = k
    return vm_id


def get_vm_host_id(vm_id: str) -> int:
    d = rds.hgetall(name=f'vm_configs:{vm_id}')
    host_id = d['host_id']
    assert isinstance(host_id, int)
    return host_id


def get_new_host_id() -> int:
    d = rds.hgetall(f'host_id_to_ip')
    existing_host_ids = []
    for k, v in d.items():
        existing_host_ids.append(int(k))
    existing_host_ids = sorted(existing_host_ids + [0])
    for i in range(1, len(existing_host_ids)):
        if existing_host_ids[i] > existing_host_ids[i - 1] + 1:
            return existing_host_ids[i - 1] + 1
    return existing_host_ids[-1] + 1


def get_current_host_id(check_existence: bool = False) -> int:
    host_ip = get_ip()
    host_ids = []
    d = rds.hgetall(f'host_id_to_ip')
    for k, v in d.items():
        if v == host_ip:
            host_ids.append(int(k))
    assert len(host_ids) <= 1, 'There is some issue with the system.' \
                               '2 host ids are there for same system.'
    if len(host_ids) == 0:
        if check_existence:
            eprint(f'This host with {host_ip} is not stored in database. '
                   f'So, can\'t create a VM')
        return -1
    return host_ids[0]


def get_vm_ids() -> List[str]:
    host_id = get_current_host_id()
    vm_ids = rds.smembers(f"vms_in_host:{host_id}")
    return [vm_id for vm_id in vm_ids]


def get_vm_pid(vm_id: str) -> int:
    a = int(rds.hget(f"vm_configs:{vm_id}", 'pid'))
    return a


def get_vm_tap_device(vm_id: str) -> str:
    a = rds.hget(f"vm_configs:{vm_id}", 'tap_device')
    return a


def get_host_net_device() -> str:
    host_id = get_current_host_id()
    tap_device = rds.hget(f"host_configs:{host_id}", 'net_device')
    return tap_device

# Add other things needed, this will be replaced later,
# possibly with database calls as we get info. from other teams
