# This file will always run in the background, detect whether the current host
# is overloaded, and then move the appropriate VM to other host.

# Daemon threads are used for long-running background tasks
# Program can exit if all the other threads are done running

# Reference for daemon thread: SuperFastPython.com
import xmlrpc.client
from time import sleep
from random import random
from threading import Thread
from typing import List, Tuple

from LoadBalancing.utils import get_stats
from LoadBalancing.vmm_backend import migrate_vm
from redis_config import rds
from LoadBalancing.config import HOTSPOT_THRESHOLD, \
    NUM_INTERVALS_FOR_HOTSPOT_CONF, migration_lock
from redis_functions import eprint


def get_avg(lst: List[float], k: int) -> float:
    temp = lst[-k:]
    s = sum(temp)
    l_ = len(temp)
    return s / l_


def background_task():
    while True:
        # Get host monitor proxies from Redis
        d = rds.hgetall('host_id_to_ip')

        overload = False
        overloaded_host: int = -1
        vol: List[Tuple[int, float]] = []

        for host_id, host_proxy in d:
            host_proxy = host_proxy.decode()

            assert isinstance(host_id, int)
            assert isinstance(host_proxy, str)

            # host_proxy example for local host http://localhost:8000/
            port = 8000

            res = get_stats(host_proxy)
            # with xmlrpc.client.ServerProxy(host_proxy + f':{port}') as proxy:
            memory_time_series: List[float] = res['mem'][0][0]
            network_time_series: List[float] = res['network'][0][0]
            cpu_time_series: List[float] = res['cpu'][0][0]

            cpu = get_avg(cpu_time_series, NUM_INTERVALS_FOR_HOTSPOT_CONF)
            mem = get_avg(memory_time_series, NUM_INTERVALS_FOR_HOTSPOT_CONF)
            net = get_avg(network_time_series, NUM_INTERVALS_FOR_HOTSPOT_CONF)

            if cpu > HOTSPOT_THRESHOLD or mem > HOTSPOT_THRESHOLD or net > HOTSPOT_THRESHOLD:
                overload = True
                overloaded_host = host_id

            vol.append((host_id, 1 / ((1 - cpu) * (1 - mem) * (1 - net))))

        if overload:
            # Now you need to do the Migration to balance the VMs properly
            vol.sort(key=lambda x: x[1], reverse=True)

            host_idx = -1
            for i in range(len(vol)):
                if vol[0] == overloaded_host:
                    host_idx = i
                    break

            # Where to transfer ?
            # Lowest volume host would be perfect for transfer
            # Which VM to transfer ?
            # One with the highest VSM on the host where we detected overload

            best = None
            lowest_size = -1
            from_host_id: int = vol[host_idx][0]

            for vm_id in rds.smembers(name=f'vms_in_host:{from_host_id}'):
                vm_id = vm_id.decode()
                assert isinstance(vm_id, str)
                d = rds.hgetall(name=f'vm_info:{vm_id}')
                # Pick the smallest size VM
                if best is None or lowest_size > d['size']:
                    best = vm_id
                    lowest_size = d['size']

            # You need to migrate the VM with id best
            target_host_id = vol[-1][0]

            if from_host_id != target_host_id:
                with migration_lock:
                    # Using migration_lock since we are not using transactions
                    # in Redis
                    migrate_vm(vm_id=best, new_host_id=target_host_id)
            else:
                eprint(f'No proper host available to transfer VM from over '
                       f'loaded host with id {from_host_id}. '
                       f'Best target VM we can find is {target_host_id}')

            # Check if vm with id best can be moved to target_host
            # And then start the migration

        # Wait for 5 sec
        sleep(5)


# create and start the daemon thread
print('Starting background task...')
daemon = Thread(target=background_task, daemon=True, name='Monitor')
daemon.start()
print('Hotspot Detection Started')
while True:
    value = random() * 5
    sleep(value)
