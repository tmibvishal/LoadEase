from LoadBalancing import vmm_backend, config
from redis_config import rds
from LoadBalancing.config import migration_lock
from LoadBalancing.utils import get_top_perc, deserialize_rds_dict, \
    deserialize_rds_str_list, get_stats
from typing import Dict, List, Any
import uuid
import LoadBalancing.vmm_backend


# TODO (update all the state in redis in a transaction)
# TODO (use redis in monitor.py and elsewhere to get the state of the vms)
class LoadBalancer():
    # Don't initialize like this (moved to redis)
    # def __init__(self, host_configs : Dict[str, Dict[str : Any]]) -> None:
    #     self.host_configs = host_configs
    #     self.vms_in_host : Dict[str, List[str]] = {host_id : [] for host_id in host_configs.keys()}
    #     self.vm_configs : Dict[str, Dict] = {}

    #     self.mons : Dict[str, ServerProxy] = {
    #             host_id : ServerProxy(f"http://{host_cfg['ip']}:{config.MON_PORT}/)") 
    #             for (host_id, host_cfg) in host_configs.items()
    #         }

    def __init__(self) -> None:
        self.host_ids: List[str] = []
        self.host_configs = {}
        self.vms_in_host: Dict[str, List[str]] = {}
        self.vm_configs: Dict[str, Dict] = {}
        # self.mons : Dict[str, ServerProxy] = {}
        self.proxys = {}
        self.all_stats = None

    # Assumes caller has migration lock
    def provision(self, vm_config) -> str:
        # Build latest state from redis
        self.host_ids = deserialize_rds_str_list(rds.smembers("host_ids"))
        self.host_configs = {}
        for host_id in self.host_ids:
            self.host_configs[host_id] = deserialize_rds_dict(
                rds.hgetall(f"host_configs:{host_id}"))

        self.vms_in_host = {}
        self.vm_configs = {}
        for host_id in self.host_ids:
            self.vms_in_host[host_id] = deserialize_rds_str_list(
                rds.smembers(f"vms_in_host:{host_id}"))
            for vm_id in self.vms_in_host[host_id]:
                self.vm_configs[vm_id] = deserialize_rds_dict(
                    rds.hgetall(f"vm_configs:{vm_id}"))
                for key, val in self.vm_configs[vm_id].items():
                    self.vm_configs[vm_id][key] = val

        self.proxys = {}
        for host_id in self.host_ids:
            proxy_addr = rds.get(f"mon_proxy_addr:{host_id}")
            self.proxys[host_id] = proxy_addr

        self.all_stats = {host_id: get_stats(proxy) for host_id, proxy in
                          self.proxys.items()}

        # Get best host
        host_id = self.get_best_host(vm_config)

        return host_id

    def get_best_host_cpu_mem(self, vm_config):
        all_stats = self.all_stats
        mem_host_stats = {host_id: stats['mem'][0] for host_id, stats in
                          all_stats.items()}
        mem_vm_stats = {host_id: stats['mem'][1] for host_id, stats in
                        all_stats.items()}
        cpu_host_stats = {host_id: stats['cpu'][0] for host_id, stats in
                          all_stats.items()}
        cpu_vm_stats = {host_id: stats['cpu'][1] for host_id, stats in
                        all_stats.items()}

        # Try to provision based on SLA
        best_host = None
        best_val = -(10 ** 20)
        for host_id, vm_ids in self.vms_in_host.items():
            # All the SLA memory allocated to the VMs in this host
            total_vm_sla_mem = sum(
                [self.vm_configs[vm_id]['mem'] for vm_id in vm_ids])
            leftover_sla_mem = self.host_configs[host_id]['mem'] - total_vm_sla_mem

            # All the SLA vCPUs to the VMs in this host
            total_vm_sla_cpu = sum(
                [self.vm_configs[vm_id]['cpu'] for vm_id in vm_ids])
            leftover_sla_cpu = self.host_configs[host_id]['cpu'] - total_vm_sla_cpu

            if leftover_sla_mem >= vm_config['mem'] and leftover_sla_cpu >= \
                    vm_config['cpu']:
                # Prioritize the amount of SLA memory left
                if leftover_sla_mem > best_val:
                    best_host = host_id
                    best_val = leftover_sla_mem

        if config.DEBUG:
            best_host = None

        if best_host is not None:
            return best_host

        # Try to provision based on peak usage
        best_host = None
        best_val = -(10 ** 20)

        for host_id, vm_stats in mem_vm_stats.items():
            total_vm_mem_peak_usage = 0
            for vm_id, (_, vm_hist) in vm_stats.items():
                peak_usage = get_top_perc(vm_hist, 0.95) * \
                             self.vm_configs[vm_id]['mem']
                total_vm_mem_peak_usage += peak_usage

            total_mem_leftover = self.host_configs[host_id][
                                     'mem'] - total_vm_mem_peak_usage

            total_vm_cpu_peak_usage = 0

            vm_stats = cpu_vm_stats[host_id]

            for vm_id, (_, vm_hist) in vm_stats.items():
                peak_usage = get_top_perc(vm_hist, 0.95) * \
                             self.host_configs[host_id]['cpu']
                total_vm_cpu_peak_usage += peak_usage

            total_cpu_leftover = self.host_configs[host_id][
                                     'cpu'] - total_vm_cpu_peak_usage

            if total_mem_leftover >= vm_config['mem'] and total_cpu_leftover >= \
                    vm_config['cpu']:
                if total_mem_leftover > best_val:
                    best_host = host_id
                    best_val = total_mem_leftover

        if config.DEBUG:
            best_host = None

        if best_host is not None:
            return best_host

        # Try to provision based peak host usage
        best_host = None
        best_val = -(10 ** 20)

        for host_id, (_, host_hist) in mem_host_stats.items():
            # mem_hist, swap_hist = get_mem_swap_hist(host_hist)
            # peak_host_mem_usage = get_top_perc(mem_hist, 0.95)
            peak_host_mem_usage = get_top_perc(host_hist, 0.95)

            peak_host_cpu_usage = get_top_perc(cpu_host_stats[host_id][1], 0.95)
            leftover_peak_cpu = self.host_configs[host_id]['cpu'] * (
                    1 - peak_host_cpu_usage)


            if peak_host_mem_usage >= 0.5:
                # this means swap was used and memory was full 
                continue
            else:
                leftover_peak_mem = (1 - peak_host_mem_usage * 2) * \
                                    self.host_configs[host_id]['mem']
                if leftover_peak_mem >= vm_config[
                    'mem'] and leftover_peak_cpu >= vm_config['cpu']:
                    if leftover_peak_mem > best_val:
                        best_host = host_id
                        best_val = leftover_peak_mem

        if config.DEBUG:
            best_host = None
        if best_host is not None:
            return best_host

        # Nothing worked return None, we will try to provision only based no memory now.
        return None

    def get_best_host_mem(self, vm_config):

        all_stats = self.all_stats
        mem_host_stats = {host_id: stats['mem'][0] for host_id, stats in
                          all_stats.items()}
        mem_vm_stats = {host_id: stats['mem'][1] for host_id, stats in
                        all_stats.items()}

        # Try to provision based on SLA
        best_host = None
        best_val = -(10 ** 20)
        for host_id, vm_ids in self.vms_in_host.items():
            total_vm_sla_mem = sum(
                [self.vm_configs[vm_id]['mem'] for vm_id in vm_ids])
            leftover_sla_mem = self.host_configs[host_id]['mem'] - total_vm_sla_mem
            if leftover_sla_mem >= vm_config[
                'mem'] and leftover_sla_mem > best_val:
                best_host = host_id
                best_val = leftover_sla_mem

        if config.DEBUG:
            best_host = None

        if best_host is not None:
            return best_host

        # Try to provision based on peak usage
        best_host = None
        best_val = -(10 ** 20)

        for host_id, vm_stats in mem_vm_stats.items():
            total_vm_peak_usage = 0
            for vm_id, (_, vm_hist) in vm_stats.items():
                peak_usage = get_top_perc(vm_hist, 0.95) * \
                             self.vm_configs[vm_id]['mem']
                total_vm_peak_usage += peak_usage

            total_mem_leftover = self.host_configs[host_id][
                                     'mem'] - total_vm_peak_usage
            if total_mem_leftover >= vm_config[
                'mem'] and total_mem_leftover > best_val:
                best_host = host_id
                best_val = total_mem_leftover

        if config.DEBUG:
            best_host = None

        if best_host is not None:
            return best_host

        # Try to provision based peak host usage
        best_host = None
        best_val = -(10 ** 20)

        for host_id, (_, host_hist) in mem_host_stats.items():
            # mem_hist, swap_hist = get_mem_swap_hist(host_hist)
            # peak_host_usage = get_top_perc(mem_hist, 0.95)
            peak_host_usage = get_top_perc(host_hist, 0.95)

            if peak_host_usage >= 0.5:
                # this means swap was used and memory was full 
                continue
            else:
                leftover_peak_mem = (1 - peak_host_usage * 2) * \
                                    self.host_configs[host_id]['mem']
                if leftover_peak_mem >= vm_config[
                    'mem'] and leftover_peak_mem > best_val:
                    best_host = host_id
                    best_val = leftover_peak_mem

        if best_host is not None:
            return best_host

        # Nothing worked, provision based on min. current usage

        # Can be improved to take into account total mem and swap space at each host,
        # but for now this works

        best_host = None
        best_val = 10 ** 20

        for host_id, (host_timeseries, _) in mem_host_stats.items():
            curr_usage = host_timeseries[-1]
            if curr_usage < best_val:
                best_host = host_id
                best_val = curr_usage

        return best_host

    def get_best_host(self, vm_config) -> str:
        best_host = self.get_best_host_cpu_mem(vm_config)

        if best_host is not None:
            return best_host

        best_host = self.get_best_host_mem(vm_config)

        assert (best_host is not None)

        return best_host


vm_provioner = LoadBalancer()


def create_vm(vm_config):
    with migration_lock:

        host_id = vm_provioner.provision(vm_config)

        # vm_id = str(uuid.uuid4())

        vm_id = vm_config['vm_id']

        # vm_config['vm_id'] = vm_id
        # vm_config['host_id'] = host_id
        # vm_config['tap_device'] = f'tap:{vm_id}'

        resp = vmm_backend.create_vm_request(
            host_id=host_id,
            vm_config=vm_config)

        for k, v in resp.items():
            vm_config[k] = v

        assert 'pid' in vm_config
        assert 'tap_device' in vm_config

        # Add vm info. in redis
        rds.hset(f'vm_configs:{vm_id}', mapping=vm_config)
        rds.sadd(f'vms_in_host:{host_id}', vm_id)

    return vm_config


_vm_id = 4
def test_create_vm_local(vm_config=None):
    global _vm_id
    vm_config = {
        'mem' : 1024 * 1024 * 256,
        'cpu' : 2,
        'net' : 1024 * 1024 * 4,
        'vm_id' : str(_vm_id),
        'tap_device' : 'vmtap103',
    }
    _vm_id += 1

    from SnapshotTeam.create_vm import new_vm
    with migration_lock:

        host_id = vm_provioner.provision(vm_config)
        # ignore host_id for this test

        pid = new_vm(vm_config)
        print(pid)
        vm_config['pid'] = pid
        vm_id = vm_config['vm_id']
        vm_config['host_id'] = host_id

        print(vm_config)

        rds.hset(f'vm_configs:{vm_id}', mapping=vm_config)
        rds.sadd(f'vms_in_host:{host_id}', vm_id)
