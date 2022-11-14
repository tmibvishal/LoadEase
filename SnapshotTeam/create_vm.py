import subprocess
from subprocess import PIPE, DEVNULL
import os

def new_vm(vm_config):
    # assert vm_config is None
    # cmd = "stress-ng --vm-bytes 3719174k --vm-keep -m 1"

    path = os.path.realpath(__file__)
    dir_path = os.path.dirname(path)
    cmd = f'{dir_path}/memtest'
    cmd = cmd.split()

    p = subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL, stdin=DEVNULL)

    return p.pid





