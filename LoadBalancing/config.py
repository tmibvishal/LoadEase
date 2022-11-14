import os
from threading import Lock

# rpc_mon_host_proxys = []  # TODO (Ramneek)
# This will now be present in Redis
# In this way, you can keep starting new hosts and hotspot will dynamically
# manage it
MON_PORT = 3413

HOTSPOT_THRESHOLD = 0.80
NUM_INTERVALS_FOR_HOTSPOT_CONF = 10

_script_dir = os.path.dirname(os.path.realpath(__file__))
migration_lock = Lock()

DEBUG = True
