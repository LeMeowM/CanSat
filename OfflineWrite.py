#!/usr/bin/env python3

from gps3 import agps3
import time
import csv
import adafruit_adxl34x
import board
import busio
import digitalio
import traceback

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
import logging
import sys

# creating logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.warning("Make sure you run\nsudo gpsd /dev/ttyS0 -F /var/run/gpsd.sock\nbefore running this code if its your first time after launch!")

fh = logging.FileHandler('spam.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

# prelaunch initialisation
logger.info("-------Prelaunch Initialisation------")
initstart = time.time()
all = False
if "--a" in sys.argv:
    all = True
if all or "--acc" in sys.argv:
    logger.info("initialising accelerometer")
    i2c = busio.I2C(board.SCL, board.SDA)
    adx = adafruit_adxl34x.ADXL345(i2c)
    logger.info("Accelerometer initialised")
if all or "--gnss" in sys.argv:
    logger.info("Initialising GPS")
    # GPSDSocket creates a GPSD socket connection & request/retrieve GPSD output.
    gps_socket = agps3.GPSDSocket()
    # DataStream unpacks the streamed gpsd data into python dictionaries.
    data_stream = agps3.DataStream()
    gps_socket.connect()
    gps_socket.watch()
    logger.info("GPS initialised")
else:
    raise NotImplementedError
cameraOn = False
if all or "--cam" in sys.argv:
    cameraOn = True
    logger.info("Initialising camera")
    picam2 = Picamera2()
    video_config = picam2.create_video_configuration()
    picam2.configure(video_config)
    encoder = H264Encoder(bitrate=10000000)
    output = "test.h264"
    logger.info("Camera initialised")

# Output file name
OUTPUT = str(time.time()) + ".csv"

stop_threads = False
main_thread = True

PERIOD_OF_TIME = 1200  # 20min
if "--time" in sys.argv:
    try:
        indexplusone = sys.argv[sys.argv.index("--time")+1]
        PERIOD_OF_TIME = int(indexplusone)
        logger.info("Mission length set to {PERIOD_OF_TIME} seconds.")
    except IndexError:
        logger.warning("Argument order is wrong, time set ignored. Mission length is set to 300 seconds.")
    except ValueError:
        logger.warning("{indexplusone} is not a number. Mission length is set to 300 seconds.")
logger.info("------Initialisation Complete-------")
logger.debug(f"Initialisation took {time.time()-initstart} seconds")

start = time.time()

def write_to_file():
    with open(OUTPUT, "a") as output_file:
        write = csv.writer(output_file, lineterminator="\n")
        write.writerow("time", "lon", "lat", "speed", "accx", "accy", "accz")
        while True:
            for new_data in gps_socket:
                if new_data:
                    data_stream.unpack(new_data)
                    accx, accy, accz = adx.acceleration
                    if data_stream.lat != "n/a" and data_stream.lon != "n/a":
                        array = [
                            time.time(),
                            float(data_stream.lon),
                            float(data_stream.lat),
                            float(data_stream.alt),
                            float(data_stream.speed),
                            float(accx),
                            float(accy),
                            float(accz)
                        ]   
                    else:
                        array = [
                            time.time(),
                            "n/a",
                            "n/a",
                            "n/a",
                            "n/a",
                            float(accx),
                            float(accy),
                            float(accz)
                        ]
                    write.writerow(array)
                    time.sleep(0.2)          
            if time.time() > start + PERIOD_OF_TIME:
                return "mission successful"

def write_to_file_safe():
    with open(OUTPUT, "a") as output_file:
        write = csv.writer(output_file, lineterminator="\n")
        write.writerow("time", "accx", "accy", "accz")
        while True:
                accx, accy, accz = adx.acceleration
                array = [
                    time.time(),
                    "n/a",
                    "n/a",
                    "n/a",
                    "n/a",
                    float(accx),
                    float(accy),
                    float(accz),
                ]
                write.writerow(array)
                time.sleep(0.5)
                if time.time() > start + PERIOD_OF_TIME:
                    return "mission successful"

logger.info("Starting mission")
try:
    logger.info(write_to_file())
except Exception:
    logger.warning("Write failed, falling back to safer write.")
    # if this fails all goes to shit lol, might as well traceback
    try:
        logger.info(write_to_file_safe())
    except Exception:
        logger.exception("its jover")
else:
    logger.info("Mission completed successfully, and without errors.")
finally:
    logger.info(f"EOF reached at {time.asctime()}")
