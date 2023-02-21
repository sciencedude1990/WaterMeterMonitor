# WaterMeterMonitor
Raspberry pi pico w and a magnetometer to monitor water consumption in real-time!

This kind of project has been done before, but it is really easy with the raspberry pi pico w and micropython!

The main program is: connect to the internet, get the real-time clock synchronized, start taking magnetometer measurements in one thread, and serve up the webserver in the other thread.

All done in Micropython!

The main file is: serve_file_water_webpage.py  Once you have it customized, then you can rename it main.py so that it runs without Thonny.


https://hackaday.io/project/189706-water-meter-monitor-with-raspberry-pi-pico-w
