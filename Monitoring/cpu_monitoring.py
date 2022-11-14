import psutil
from monitor import Monitor
from typing import Tuple, Dict

from redis_functions import get_vm_pid


class CpuMonitor(Monitor):
    def __init__(self, vm_ids=None) -> None:
        super().__init__(vm_ids)
        # psutil cpu_percent gives garbage value on the first run
        # so making an initial call to get rid of it
        if vm_ids is None:
            vm_ids = []
        psutil.cpu_percent(interval=None, percpu=True)
        #maintain a dictionary of vm_id to psutil.Process object
        self.vm_processes = {}

        for vm_id in self.vm_ids:
            vm_pid = get_vm_pid(vm_id)
            self.vm_processes[vm_id] = psutil.Process(vm_pid)
            self.vm_processes[vm_id].cpu_percent(interval=None)
    
    def collect_stats(self) -> Tuple[float, Dict[str, float]]:
        '''
        Returns the average cpu usage of the Host and all the VMs
        '''
        # interval=None means that the cpu usage is calculated
        # since the last call to cpu_percent
        # it is a non-blocking call

        # percpu=True means that the cpu usage is calculated
        # for each core
        host_per_cpu_usage = psutil.cpu_percent(interval=None, percpu=True)
        avg_host_cpu_usage = 0
        for cpu in host_per_cpu_usage:
            avg_host_cpu_usage += cpu
        # cpu_percent returns a list of cpu usage for each core
        # so we need to divide by the number of cores
        # to get the average cpu usage
        avg_host_cpu_usage /= len(host_per_cpu_usage)

        # vm_id to cpu usage
        vm_stats = {}

        for vm_id in self.vm_ids:
            if vm_id not in self.vm_processes:
                vm_pid = get_vm_pid(vm_id)
                self.vm_processes[vm_id] = psutil.Process(vm_pid)
                self.vm_processes[vm_id].cpu_percent(interval=None)

        vms_to_del = []
        for vm_id in self.vm_processes.keys():
            if vm_id not in self.vm_ids:
                vms_to_del.append(vm_id)
        
        for vm_id in vms_to_del:
            del self.vm_processes[vm_id]

        for vm_id in self.vm_ids:
            # divide by the number of cores to get the average cpu usage
            # because cpu_percent might return a value > 100
            # as it sums up the cpu usage of all the cores
            vm_stats[vm_id] = self.vm_processes[vm_id].cpu_percent(interval=None) / psutil.cpu_count()

        return avg_host_cpu_usage, vm_stats

    # return the cpu stats, accounting for the effect of network usage
    def collect_stats_network_effect(self, host_stat_net: float,
                vm_stats_net: Dict[str, float]) -> Tuple[float, Dict[str, float]]:

        host_stat, vm_stats = self.collect_stats()
        print(host_stat, vm_stats)
        #calculate the cpu usage accounting for the effect of network usage by host
        host_cpu_used_for_network = host_stat - sum(vm_stats.values())
        # add proportion of host_cpu_used_for_network to vm_stats
        for vm_id in vm_stats:
            vm_stats[vm_id] += host_cpu_used_for_network * vm_stats_net[vm_id]
        
        return host_stat, vm_stats

