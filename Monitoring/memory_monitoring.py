from redis_functions import get_vm_pid
from redis_functions import eprint
from monitor import Monitor
from typing import Any, Dict, List, Tuple, Union
import psutil


class MemoryMonitor(Monitor):
    def update_time_series(self, vm_id, resource_usage,
                          host: bool = False) -> None:
        # In base class. Circular
        pass

    def collect_stats(self) -> Tuple[float, Dict[str, float]]:
        """
        This will collect host-side RAM statistics.
        This function will be periodically invoked to populate the histogram
        and time series data.
        :return: tuple
                1) First element of the tuple is the current + swap memory
                   in host
                2) Second element of the tuple is a dictionary with mapping
                   vm_id to percentage of memory it uses on the host
        """

        # Getting the host stats
        # Host stats are nothing but the swap memory used
        # We'd want to decrease this swap memory

        # TODO FIXME: swap can be filled even though mem has a lot of space
        # So don't add swap percentage until mem is mostly full.
        # TODO FIXME: removing swap
        
        virt_stats = psutil.virtual_memory()
        ram_used = virt_stats.used / virt_stats.total


        host_stats = ram_used * 100

        # print all vm ids
        # print(f"vm-ids: {self.vm_ids}")

        # Getting the VM stats
        vm_stats = {}
        for vm_id in self.vm_ids:
            vm_info = self._get_vm_stat(vm_id)
            vm_stats[vm_id] = vm_info['memory_percent']
        return host_stats, vm_stats

    @staticmethod
    def _get_vm_stat(vm_id: str) -> Dict[str, Union[str, int, float]]:
        # Iterate over all running process
        total = psutil.virtual_memory().total
        pid = get_vm_pid(vm_id)
        vm_info = {}
        try:
            proc = psutil.Process(pid)
            assert '' in proc.name(), \
                f'PID {pid} doesn\'t represent a VM but rather {proc.name()}.' \
                f' Your vm_id to process id mapping is wrong'
            temp = proc.as_dict(
                attrs=['pid', 'name', 'cpu_percent', 'memory_percent'])
            temp['memory_bytes'] = temp['memory_percent'] * total / 100
            vm_info = temp
        except psutil.NoSuchProcess:
            eprint(
                f'PID {pid} doesn\'t represent any process. '
                f'Your vm_id to process id mapping is wrong')
        except psutil.ZombieProcess:
            eprint(
                f'PID {pid} represents a ZombieProcess. '
                f'Your vm_id to process id mapping might be wrong')
        except psutil.AccessDenied:
            eprint(
                f'Can\'t access PID {pid}. '
                f'Your vm_id to process id mapping might be wrong')
        assert len(vm_info) > 0, 'Can\'t get VM Info'
        return vm_info

    @staticmethod
    def _get_all_vm_stats() -> List[Dict[str, Union[str, int, float]]]:
        # Reference: https://thispointer.com/python-get-list-of-all-running-processes-and-sort-by-highest-memory-usage/
        # Iterate over all running process
        total = psutil.virtual_memory().total
        vm_infos = []
        for proc in psutil.process_iter():
            try:
                # Get process name & pid from process object.
                if 'vmm-reference' in proc.name():
                    vm_info = proc.as_dict(
                        attrs=['pid', 'name', 'cpu_percent', 'memory_percent'])
                    vm_info['memory_bytes'] = vm_info['memory_percent'] * total / 100
                    # for k in vm_info:
                    #     vm_info[k] = str(vm_info[k])
                    vm_infos.append(vm_info)
            except (psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess):
                pass
        return vm_infos
