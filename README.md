# CanSat
CanSAT CircuitPy Project for launch in switzerland

This is the source code of the entire project that will run through CircuitPython on a RaspberryPi Zero 2 W.


We will need to convert everything from `.py` files to `.mpy` files through the [converter](https://adafruit-circuit-python.s3.amazonaws.com/index.html?prefix=bin/mpy-cross/) to be able to reduce memory footprint and compile time checks once we have all of this done.

# Dependencies
## General Control
- Circuit Python
## Transmission
- [RF69](https://docs.circuitpython.org/projects/rfm69/en/latest/)

## Data Collection
- [PiCamera2](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf), [(github)](https://github.com/raspberrypi/picamera2)
- [GPSd](https://gpsd.gitlab.io/gpsd/index.html)
- [gps3](https://pypi.org/project/gps3/)

# Important Wikis
- [GNSS](https://www.waveshare.com/wiki/MAX-M8Q_GNSS_HAT#Using_with_Raspberry_Pi)
- [Camera](https://github.com/raspberrypi/picamera2?tab=readme-ov-file)
- [Transciever Hookup](https://learn.sparkfun.com/tutorials/rfm69hcw-hookup-guide/all)
- [Transciever Tutorial](https://circuitdigest.com/microcontroller-projects/how-to-interface-rfm69hcw-rf-module-with-arduino)



