import unittest
import subprocess
import logging
import os
import signal
import threading
from LoadBalancing.utils import create_virtual_machine
from config import VMM_REF_DIR
from memory_monitoring import MemoryMonitor
from redis_functions import get_vm_pid


class SimpleTest(unittest.TestCase):
    def setUp(self) -> None:
        print(VMM_REF_DIR)
        self.vm1_id = create_virtual_machine(mem_mb=512, tap_device='vmtap100')
        self.mem_monitor = MemoryMonitor()

    def test_start(self):
        pass

    def test_mem_stats(self):
        # Create Second VM
        vm1_id = self.vm1_id
        vm2_id = create_virtual_machine(mem_mb=512, tap_device='vmtap100')

        # Assert VM is created or not
        self.assertTrue(vm1_id != '')
        self.assertTrue(vm2_id != '')

        # Allocate the vm-ids
        self.mem_monitor.vm_ids.append(vm1_id)
        self.mem_monitor.vm_ids.append(vm2_id)

        # now collect stats
        stat = self.mem_monitor.collect_stats()

        self.assertIsNotNone(stat[0])
        self.assertIsNotNone(stat[1])

        # Print stats
        print(f"stats: {stat}")

        # Kill all VMs
        pid1 = get_vm_pid(vm1_id)
        pid2 = get_vm_pid(vm2_id)
        kill(pid1)
        kill(pid2)


def kill(proc_pid: int) -> None:
    logging.getLogger().setLevel(logging.INFO)
    logging.info(f"kill vm-{proc_pid}")
    os.kill(proc_pid, signal.SIGTERM)


if __name__ == '__main__':
    unittest.main()
