import unittest
import subprocess
import logging
import os
import signal
from config import VMM_REF_DIR
# from memory_monitoring import MemoryMonitor
from cpu_monitoring import CpuMonitor

class SimpleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = subprocess.Popen(
            ['./target/debug/vmm-reference', '--kernel path=./bzimage-hello-busybox', '--net tap=vmtap100',
             '--memory size_mib=512'], cwd=VMM_REF_DIR)
        # Find this new vm process id

        self.cpu_monitor = CpuMonitor()

    def test_cpu_stats(self):
        # assert vm is created or not.
        self.assertIsNotNone(self.p)

        vm1_id = self.p.pid
        logging.info(f"vm1_id: {vm1_id}")

        self.cpu_monitor.vm_ids.append(vm1_id)

        # now collect stats
        stat = self.cpu_monitor.collect_stats()

        # print stats
        logging.info(f"stats: {stat}")

        # created vm is not under use.
        self.assertAlmostEqual(0, list(stat[1].values())[0], 1)

        # create vm's
        p2 = subprocess.Popen(
            ['./target/debug/vmm-reference', '--kernel path=./bzimage-hello-busybox', '--net tap=vmtap100',
             '--memory size_mib=512'], cwd=VMM_REF_DIR)

        # assert vm is created or not.
        self.assertIsNotNone(p2)

        # get all vm's ids
        vm2_id = p2.pid
        logging.info(f"vm2_id: {vm2_id}")

        # allocate the vm-ids
        self.cpu_monitor.vm_ids.append(vm1_id)
        self.cpu_monitor.vm_ids.append(vm2_id)

        # now collect stats
        stat = self.cpu_monitor.collect_stats()

        # vm is not under use.
        self.assertAlmostEqual(0, list(stat[1].values())[1], 1)

        # print stats
        logging.info(f"stats: {stat}")

        # kill all processes
        kill(vm1_id)
        kill(vm2_id)


def kill(proc_pid):
    logging.getLogger().setLevel(logging.INFO)
    logging.debug(f"kill vm-{proc_pid}")
    os.kill(proc_pid, signal.SIGTERM)


if __name__ == '__main__':
    unittest.main()

