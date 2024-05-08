#!/usr/bin/env python3

from gps3 import agps3
import time
import csv
import threading
import adafruit_adxl34x
import board
import busio
import digitalio
import adafruit_rfm69
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
import logging
logger = logging.getLogger(__name__)
logger.info("-------Prelaunch Initialisation------")
logger.info("Begin initialisation of radio")
# Define radio parameters.
RADIO_FREQ_MHZ = 434.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip:
CS = digitalio.DigitalInOut(board.CE0)  # SPI0 CE0
RESET = digitalio.DigitalInOut(board.D1)  # GPIO 5, DPI D1

logger.info("Begin initialisation of SPI")
# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialze RFM radio
print(board.SCK, board.MOSI, board.MISO)
print(board.CE0, board.D1)
rfm69 = adafruit_rfm69.RFM69(spi, CS, RESET, RADIO_FREQ_MHZ)

# Optionally set an encryption key (16 byte AES key). MUST match both
# on the transmitter and receiver (or be set to None to disable/the default).
rfm69.encryption_key = b"\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08"  # TODO: fix keys
logger.info("Radio initialised successfully")

logger.info("initialising accelerometer")
i2c = busio.I2C(board.SCL, board.SDA)
adx = adafruit_adxl34x.ADXL345(i2c)
logger.info("Accelerometer initialised")

logger.info("Initialising GPS")
# GPSDSocket creates a GPSD socket connection & request/retrieve GPSD output.
gps_socket = agps3.GPSDSocket()
# DataStream unpacks the streamed gpsd data into python dictionaries.
data_stream = agps3.DataStream()
gps_socket.connect()
gps_socket.watch()
logger.info("GPS initialised")




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


def receiver():
    thread_alive = threading.Thread(target=keep_alive, args=(lambda: main_thread))
    thread_alive.start()
    while main_thread:
        packet = rfm69.receive()
        # Optionally change the receive timeout from its default of 0.5 seconds:
        # packet = rfm69.receive(timeout=5.0)
        # If no packet was received during the timeout then None is returned.
        if packet is None:
            # Packet has not been received
            print("Received nothing! Listening again...")
        else:
            # Received a packet!
            # Print out the raw bytes of the packet:

            # And decode to ASCII text and print it too.  Note that you always
            # receive raw bytes and need to convert to a text format like ASCII
            # if you intend to do string processing on your data.  Make sure the
            # sending side is sending ASCII data before you try to decode!
            workers = []
            packet_text = str(packet, "ascii")
            if packet_text == "Go":
                if stop_threads == False:
                    print("no..no..no..")
                    rfm69.send(bytes("no..no..no..", "utf-8"))
                else:
                    stop_threads = False
                    picam2.start_recording(encoder, output)
                    thread1 = threading.Thread(
                        target=write_to_file, args=(lambda: stop_threads)
                    )
                    thread2 = threading.Thread(
                        target=write_to_file_slow,
                        args=(lambda: stop_threads),
                    )
                    workers.append(thread1, thread2)
                    thread1.start()
                    thread2.start()

            if packet_text == "Stop":
                stop_threads = True
                picam2.stop_recording()
                for worker in workers:
                    worker.join()
            if packet_text == "Stop_everythig":
                main_thread = False
                stop_threads = True
                picam2.stop_recording()
                for worker in workers:
                    worker.join()


def write_to_file(stop):
    with open(OUTPUT, "w") as output_file:
        while True:
            for new_data in gps_socket:
                if new_data:
                    data_stream.unpack(new_data)
                    accx, accy, accz = adx.acceleration
                    if data_stream.lat != "n/a" and data_stream.lon != "n/a":
                        array = []
                        array.append(
                            float(data_stream.lon),
                            float(data_stream.lat),
                            float(data_stream.alt),
                            float(data_stream.speed),
                            float(accx),
                            float(accy),
                            float(accz),
                        )

                        write = csv.writer(output_file, lineterminator="\n")
                        write.writerow(array)
                        time.sleep(0.2)
            if stop():
                print("  Exiting loop.")
                break


def keep_alive(stop):
    while True:
        rfm69.send(bytes(str("I'm Alive"), "utf-8"))
        if stop():
            print("  Exiting loop.")
            break
        time.sleep(10)


def write_to_file_slow(stop):
    while True:
        for new_data in gps_socket:
            if new_data:
                data_stream.unpack(new_data)
                if data_stream.lat != "n/a" and data_stream.lon != "n/a":
                    rfm69.send(
                        bytes(
                            str(data_stream.lon) + " " + str(data_stream.lat), "utf-8"
                        )
                    )
            if stop():
                print("  Exiting loop.")
                break

        if stop():
            print("  Exiting loop.")
            break
        time.sleep(2)


thread3 = threading.Thread(target=receiver)
stop_threads = True
