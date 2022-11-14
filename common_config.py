import os

CREATE_END_POINT = 'create'
SNAPSHOT_END_POINT = 'snapshot'

# TODO (vishal): Pass this using OS parameters
# VMM_REF_DIR = os.environ['VMM_REF']
# '/home/vishal/col732/lab3/vmm-reference'
_script_dir = os.path.dirname(os.path.realpath(__file__))
VMM_REF_DIR = os.path.join(_script_dir, 'vmm-reference')