#!/usr/bin/env python3

from gps3 import agps3
import time
import csv
import threading
from machine import Pin, I2C
from micropython_adxl343 import adxl343
import board
import busio
import digitalio
import numpy as np


import adafruit_rfm69


# Define radio parameters.
RADIO_FREQ_MHZ = 434.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip, use these if wiring up the breakout according to the guide:
CS = digitalio.DigitalInOut(board.D5)
RESET = digitalio.DigitalInOut(board.D6)
# Or uncomment and instead use these if using a Feather M0 RFM69 board
# and the appropriate CircuitPython build:
# CS = digitalio.DigitalInOut(board.RFM69_CS)
# RESET = digitalio.DigitalInOut(board.RFM69_RST)

# Define the onboard LED
LED = digitalio.DigitalInOut(board.D13)
LED.direction = digitalio.Direction.OUTPUT

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialze RFM radio
rfm69 = adafruit_rfm69.RFM69(spi, CS, RESET, RADIO_FREQ_MHZ)

# Optionally set an encryption key (16 byte AES key). MUST match both
# on the transmitter and receiver (or be set to None to disable/the default).
rfm69.encryption_key = (
    b"\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08"
)

i2c = I2C(1, sda=Pin(2), scl=Pin(3))  # Correct I2C pins for RP2040
adx = adxl343.ADXL343(i2c)


# GPSDSocket creates a GPSD socket connection & request/retrieve GPSD output.
gps_socket = agps3.GPSDSocket()
# DataStream unpacks the streamed gpsd data into python dictionaries.
data_stream = agps3.DataStream()
gps_socket.connect()
gps_socket.watch()

INPUT = ""
# Output file name
OUTPUT = ""


stop_threads = False

main_thread = True


def receiver():
    while main_thread:
        packet = rfm69.receive()
        # Optionally change the receive timeout from its default of 0.5 seconds:
        # packet = rfm69.receive(timeout=5.0)
        # If no packet was received during the timeout then None is returned.
        if packet is None:
            # Packet has not been received
            LED.value = False
            print("Received nothing! Listening again...")
        else:
            # Received a packet!
            LED.value = True
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
                    thread1 = threading.Thread(
                        target=write_to_file, args=("file1.txt", lambda: stop_threads)
                    )
                    thread2 = threading.Thread(
                        target=write_to_file_slow,
                        args=("file2.txt", lambda: stop_threads),
                    )
                    workers.append(thread1, thread2)
                    thread1.start()
                    thread2.start()

            if packet_text == "Stop":
                stop_threads = True
                for worker in workers:
                    worker.join()
            if packet_text == "Stop_everythig":
                main_thread = False
                stop_threads = True
                for worker in workers:
                    worker.join()


def write_to_file(file_name, stop):
    with open(file_name, "w") as output_file:
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


def write_to_file_slow(stop):
    while True:
        accx, accy, accz = adx.acceleration
        rfm69.send(bytes(str(accz), "utf-8"))
        time.sleep(2)
        if stop():
            print("  Exiting loop.")
            break


thread3 = threading.Thread(target=receiver)
stop_threads = True
