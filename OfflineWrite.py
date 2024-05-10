#!/usr/bin/env python3

from gps3 import agps3
import time
import csv
import threading
import adafruit_adxl34x
import board
import busio
import digitalio

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
import logging
import sys


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

logger.info("-------Prelaunch Initialisation------")
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
OUTPUT = str(time.time) + ".csv"

stop_threads = False
main_thread = True

logger.info("------Initialisation Complete-------")
start = time.time()
PERIOD_OF_TIME = 300  # 5min


def write_to_file():
    with open(OUTPUT, "w") as output_file:
        while True:
            for new_data in gps_socket:
                if new_data:
                    data_stream.unpack(new_data)
                    accx, accy, accz = adx.acceleration
                    if data_stream.lat != "n/a" and data_stream.lon != "n/a":
                        array = [
                            float(data_stream.lon),
                            float(data_stream.lat),
                            float(data_stream.alt),
                            float(data_stream.speed),
                            float(accx),
                            float(accy),
                            float(accz),
                        ]
                        write = csv.writer(output_file, lineterminator="\n")
                        write.writerow(array)
                        time.sleep(0.2)
            if time.time() > start + PERIOD_OF_TIME:
                break


write_to_file()
