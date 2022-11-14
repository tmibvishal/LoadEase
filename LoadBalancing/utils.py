import hashlib
import os
import pdb
import signal
import subprocess
import uuid
from typing import Dict, Tuple, List, Optional

import grpc
import mon_pb2
import mon_pb2_grpc
from rpc_utils import grpcStat2py
from datetime import datetime
from redis_config import rds
from common_config import VMM_REF_DIR
from redis_functions import eprint, get_ip, get_vm_pid, get_current_host_id, \
    get_vm_host_id


def get_int_from_vm_id(vm_id: str):
    return int(hashlib.sha1(vm_id.encode("utf-8")).hexdigest(), 16)


def add_data_to_redis(host_id: int, vm_id: str, mem_mb: int, cpu_cores: int,
                      image_path: str, pid: int, tap_device: str, rpc_port: int):
    """
    Insert all config in Redis
    :param host_id:
    :param vm_id:
    :param mem_mb: VM Memory in MB
    :param cpu_cores:
    :param image_path:
    :param pid:
    :param tap_device:
    :return: None
    """
    rds.sadd(f'vms_in_host:{host_id}', vm_id)
    vm_configs = {'mem': mem_mb,
                  'cpu': cpu_cores,
                  'disk': '',
                  'image_path': image_path,
                  'host_id': host_id,
                  'pid': pid,
                  'tap_device': tap_device,
                  'rpc_port': rpc_port}
    hkey = f'vm_configs:{vm_id}'
    rds.hset(hkey, mapping=vm_configs)


def create_virtual_machine(mem_mb: int, tap_device: str, cpu_cores: int = 1,
                           image_path: str = './bzimage-hello-busybox',
                           vm_id: Optional[str] = None) -> str:
    """
    :param vm_id:
    :param mem_mb: VM Memory in MB
    :param tap_device:
    :param cpu_cores:
    :param image_path:
    :return: Returns the VM ID
    """
    if mem_mb > 40000:
        eprint(f'Can\'t create VM with {mem_mb} MB memory.')
        return ''
    host_id = get_current_host_id()
    if vm_id is None:
        vm_id = uuid.uuid4().hex + datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        rpc_port = get_int_from_vm_id(vm_id)
    else:
        vm_config = rds.hgetall(f'vm_configs:{vm_id}')
        rpc_port = vm_config['rpc_port']
        assert isinstance(rpc_port, int)
        assert rpc_port == get_int_from_vm_id(vm_id)

    # proc = subprocess.Popen(['./target/debug/vmm-reference', '--kernel',
    # 'path=./bzimage-hello-busybox', '--net', 'tap=vmtap100',
    # '--memory', 'size_mib=512'], cwd=VMM_REF_DIR, stdout=subprocess.DEVNULL,
    # stderr=subprocess.STDOUT)
    pdb.set_trace()
    proc = subprocess.Popen(
        ['./target/debug/vmm-reference',
         '--kernel', f'path={image_path}',
         '--net', f'tap={tap_device}',
         '--memory', f'size_mib={mem_mb}',
         '--vcpus', f'num={cpu_cores}'],
        cwd=VMM_REF_DIR,
        shell=True)
    pid = proc.pid
    if mem_mb > 4000:
        eprint(f'You have created a vm with memory {mem_mb} MB. '
               f'Make sure that this is intentional')
    add_data_to_redis(host_id=host_id,
                      vm_id=vm_id,
                      mem_mb=mem_mb,
                      cpu_cores=cpu_cores,
                      image_path=image_path,
                      pid=pid,
                      tap_device=tap_device,
                      rpc_port=rpc_port)
    return vm_id


def stop_virtual_machine(vm_id: str):
    pid = get_vm_pid(vm_id)
    cur_host_id = get_current_host_id()
    vm_host_id = get_vm_host_id(vm_id)
    if cur_host_id == vm_host_id:
        os.kill(pid, signal.SIGTERM)
    else:
        eprint(f'{vm_id} is not on current host. Can\'t close the VM')


def get_top_perc(hist, perc=0.90):
    covered = 0
    for i in range(0, 100, 5):
        covered += hist[i]
        if covered >= perc:
            return (i + 2.5) / 100.0

    if covered == 0.0:
        # hist not filled ?
        return 0.0
    else:
        # 100% usage
        return 1.0


def get_mem_swap_hist(hist):
    mem_hist = {i: 0 for i in range(0, 100, 5)}
    swap_hist = {i: 0 for i in range(0, 100, 5)}

    total_mem_p = 0.0
    total_swap_p = 0.0

    for i in range(0, 5, 50):
        total_mem_p += hist[i]
        total_swap_p += hist[i + 50]

    for i in range(0, 5, 50):
        mem_hist[i * 2] = hist[i] / total_mem_p
        swap_hist[i * 2] = hist[i + 50] / total_swap_p

    return mem_hist, swap_hist


def deserialize_rds_dict(hset):
    ret = {}
    for k, v in hset.items():
        if isinstance(k, bytes):
            k = k.decode()
        if isinstance(v, bytes):
            v = v.decode()
        ret[k] = v
        if v.isnumeric():
            ret[k] = int(v)
    return ret


def deserialize_rds_str_list(lst):
    ret = []
    for i in lst:
        ret.append(i)
    return ret


def get_stats(proxy: str) -> \
        Dict[str, Tuple[Tuple[List[float], Dict[int, float]],
                        Dict[str, Tuple[List[float], Dict[int, float]]]]]:
    with grpc.insecure_channel(proxy) as channel:
        stub = mon_pb2_grpc.MonitoringStub(channel)
        response = stub.GetStats(mon_pb2.Void())
        return {
            'cpu': grpcStat2py(response.cpu),
            'mem': grpcStat2py(response.mem),
            'net': grpcStat2py(response.net),
        }


def grpc_new_vm(proxy: str):
    with grpc.insecure_channel(proxy) as channel:
        stub = mon_pb2_grpc.MonitoringStub(channel)
        response = stub.CreateTestVM(mon_pb2.Void())
        return response.pid