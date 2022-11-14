from typing import Dict, Union, List

from LoadBalancing.utils import create_virtual_machine


def start_vms(vms_db: List[Dict[str, Union[int, str]]]):
    # Create some VM on this host
    # Start a flask server to listen to its requests
    for vm in vms_db:
        vm_id = create_virtual_machine(mem_mb=vm['mem'] // (1024 * 1024),
                                       cpu_cores=vm['cpu'],
                                       tap_device='vm_tap_100')

