import psutil
import os
from CustomLogger import setup_custom_logger
logging = setup_custom_logger("logging", os.path.basename(__file__))

def show_fan_speed_stats() -> None:
    stats = psutil.sensors_fans()
    logging.info(f"fans_stats: {psutil.sensors_fans()}")
    names = list(stats.keys())
    for name in names:
        if name in stats:
            logging.info("Fans:")
            for entry in stats[name]:
                logging.info("%-20s %s RPM:" % (entry.label or name, entry.current))


if __name__ == "__main__":
    show_fan_speed_stats()
