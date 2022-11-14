import uuid
import os

from redis_functions import get_current_host_id

MON_PORT = 3413

HOST_PEAK_NET_BIT_RATE = 1024 * 1024 * 50  # 50 MBps, setup will overwrite this

MONITOR_INTERVAL = 0.5    # Collect stats for each vm and host every `MONITOR_INTERVAL` seconds
TIME_SERIES_LEN = 100
TIME_SERIES_INTERVAL = MONITOR_INTERVAL * TIME_SERIES_LEN


HOST_ID = get_current_host_id()

