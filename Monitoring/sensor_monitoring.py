import psutil
import os
from CustomLogger import setup_custom_logger
logging = setup_custom_logger("logging", os.path.basename(__file__))

def show_sen_temp_stats() -> None:
    stats = psutil.sensors_temperatures(fahrenheit=True)
    for n in range(len(stats['coretemp'])):
        logging.info(
            str(stats['coretemp'][n].label) + " has a temperature of " + str(stats['coretemp'][n].current) + "F")
        if stats['coretemp'][n].current > stats['coretemp'][n].high:
            logging.info("Temperature is too high")
        else:
            logging.info("Temperature is Normal")


if __name__ == "__main__":
    show_sen_temp_stats()
