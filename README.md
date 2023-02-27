# WaterMeterMonitor
Raspberry pi pico w and a magnetometer to monitor water consumption in real-time!

This kind of project has been done before, but it is really easy with the raspberry pi pico w and micropython!

The main program is: connect to the internet, get the real-time clock synchronized, start taking magnetometer measurements in one thread, and serve up the webserver in the other thread.

All done in Micropython!

The main file is: serve_file_water_webpage.py  Once you have it customized, then you can rename it main.py so that it runs without Thonny.


https://hackaday.io/project/189706-water-meter-monitor-with-raspberry-pi-pico-w

This worked on a Neptune 2237 residential water meter.  Completely non-destructive - just put the magnetometer close to the meter.

I coded up a "snippet" using a MMC5603 instead of the ST magnetometer.
