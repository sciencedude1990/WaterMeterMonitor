# Very simple web server
# In the idle time, makes the water website

# Imports
import time
import ntptime
import network
import socket
import sys
import os
import array
import machine
import ustruct
import _thread
import wifi_info     # The SSID and WIFI password
import website_info  # The helper functions for creating the website

# Water website filename, HTML
F_NAME_WATER_WEBSITE = 'water_website.html'

# Water meter tick count, 0 to 6 for days of the week, index 7 is the current day of the week
water_meter_tick_count = array.array("I", [0] * 8)
# Make a "temporary" array, used for reducing the threading interaction
temp_water_meter_tick_count = array.array("I", [0] * 8)

# Load the data from the status file - simple file to hold the counts and day of the week, to be robust against power outtages
F_NAME_STATUS = 'water_meter_status.bin'
# Format string to unpack the file
format_string = "I" * 8

try:
    fid = open(F_NAME_STATUS, 'rb')
    content = fid.read()
    fid.close()
except:
    print('Unable to open the status file...')
    sys.exit()
    
# Load the data into the array
water_meter_tick_count[:] = array.array("I", ustruct.unpack(format_string, content))

# Prepare the thread for reading the water meter
# Create a semaphore
baton = _thread.allocate_lock()

# Routine to read a register on SPI - for this particular magnetometer, the LSM9DSO
def reg_read(spi, cs, reg):        
    # Add the 1 to the MSB of reg
    reg = 0x80 | reg
    
    # Create array - need to read twice while writing
    temp_rx = bytearray(2)
    
    # Make sure chip select is high
    cs.value(1)
    # Drop chip select
    cs.value(0)
    # Read the values
    spi.readinto(temp_rx, reg)
    # Chip select set to high
    cs.value(1)
    
    # Return the second result
    return temp_rx[1]

# Routine to read magnetic data from this magnetometer
def reg_read_magnetic(spi, cs):
    # Register for magnetic data, 0x08
    # Add 1 in the MSB for reading
    # Add 1 in bit 7 for increment
    reg = 0x80 | 0x40 | 0x08
    
    # Create array - need to read 7 times while writing
    temp_rx = bytearray(7)
    
    # Make sure chip select is high
    cs.value(1)
    # Drop chip select
    cs.value(0)
    # Read the values
    spi.readinto(temp_rx, reg)
    # Chip select set to high
    cs.value(1)
    
    # Return the readings
    return temp_rx[1 : 7]

# Routine to write a register to the magnetometer
def reg_write(spi, cs, reg, val):
    
    # Create the write array
    txdata = bytearray(2)    
    
    # Address
    txdata[0] = reg
    # Value
    txdata[1] = val
    
    # Throw away
    rxdata = bytearray(2)

    # Make sure chip select is high
    cs.value(1)
    # Drop chip select
    cs.value(0)
    # Write the address and value
    spi.write_readinto(txdata, rxdata)
    # Chip select set to high
    cs.value(1)


# A class to IIR average measurements
class IIRMeasurement:
    def __init__(self, alpha):
        # The IIR state variable
        self.prev = 0;
        
        # Constants for filtering
        self.alpha = alpha
        
    def reset(self):
        self.prev = 0;
        
    def __str__(self):
        # To string
        return "IIR: " + str(self.prev)
    
    def update(self, new_value):    
        # Update the state variable
        self.prev = self.prev * (1 - self.alpha) + new_value * self.alpha
        
# Max and Min objects for tracking magnetic measurement        
cycle_max_measure = IIRMeasurement(0.0625)
cycle_min_measure = IIRMeasurement(0.0625)

# Thresholds
THRESH_HIGH = 6050
THRESH_LOW = 2500

# The thread for reading the water meter and updating the number of ticks from the water meter
def read_water_meter_thread():
    # Bring in the variable into the thread
    global water_meter_tick_count
    global cycle_max_measure
    global cycle_min_measure
    global THRESH_HIGH
    global THRESH_LOW
    
    # Create the SPI interface to the magnetometer
    spi = machine.SPI(0, baudrate=5000000, polarity=1, phase=1, bits=8, firstbit=machine.SPI.MSB, sck=machine.Pin(2), mosi=machine.Pin(3), miso=machine.Pin(0))

    # Chip select
    cs = machine.Pin(1, mode=machine.Pin.OUT, value=1)

    # First read is throw away to get the serial clock to be correct (i.e., idle HIGH)
    temp = reg_read(spi, cs, 0x0F)

    ###
    # Read the WHO_AM_I_XM (i.e., Address of 0x0F, plus add the MSB bit for reading)
    who_am_i_xm = reg_read(spi, cs, 0x0F)

    print("Expect 73, got: " + str(who_am_i_xm))
    time.sleep(0.25)
    ###
    # Write CTRL_REG1_XM, enable block data update
    reg_write(spi, cs, 0x20, 8)

    # Read CTRL_REG1_XM
    ctrl_reg1_xm = reg_read(spi, cs, 0x20)
    print("ctrl_reg1_xm: " + str(ctrl_reg1_xm))
    time.sleep(0.25)

    ###
    # Write CTRL_REG5_XM to high resolution, 100 Hz update
    reg_write(spi, cs, 0x24, 116)

    # Read CTRL_REG5_XM
    ctrl_reg5_xm = reg_read(spi, cs, 0x24)
    print("ctrl_reg5_xm: " + str(ctrl_reg5_xm))
    time.sleep(0.25)
    
    ###
    # Write CTRL_REG6_XM to +- 2 gauss
    reg_write(spi, cs, 0x25, 0)

    # Read CTRL_REG6_XM
    ctrl_reg6_xm = reg_read(spi, cs, 0x25)
    print("ctrl_reg6_xm: " + str(ctrl_reg6_xm))
    time.sleep(0.25)
    ###
    # Write CTRL_REG7_XM to normal mode (out of power down)
    reg_write(spi, cs, 0x26, 0)

    # Read CTRL_REG7_XM
    ctrl_reg7_xm = reg_read(spi, cs, 0x26)
    print("ctrl_reg7_xm: " + str(ctrl_reg7_xm))
    time.sleep(0.25)
    
    mag_read = reg_read_magnetic(spi, cs)
    temp = mag_read[4] + (mag_read[5] << 8)
    temp = (-(65536 - temp)) if (temp > 32767) else temp
    print("Reading: " + str(temp))
    time.sleep(1)
    
    current_min = 65536
    current_max = 0
    
    # The state
    search_state = 0 # 0 for LOOK HIGH, 1 for LOW LOW
    
    while True:
        # read magnetic sensor
        mag_read = reg_read_magnetic(spi, cs)
        # Use the "Z" sensor
        temp = mag_read[4] + (mag_read[5] << 8)
        temp = (-(65536 - temp)) if (temp > 32767) else temp
        
        # process result and update state machine
        # Check the max
        if temp > current_max:
            current_max = temp
        
        # Check the min
        if temp < current_min:
            current_min = temp
            
        # update the state machine
        if search_state == 0:
        
            # Check the threshold
            if temp > THRESH_HIGH:
                search_state = 1
                baton.acquire()
                water_meter_tick_count = water_meter_tick_count + 1
                baton.release()
            
        elif search_state == 1:
        
            # Check the threshold        
            if temp < THRESH_LOW:
                search_state = 0
                baton.acquire()
                cycle_max_measure.update(current_max)
                cycle_min_measure.update(current_min)
                baton.release()
            
                current_max = 0
                current_min = 65536
        
        # Sleep until next reading
        time.sleep(0.002)


# Replace with your own SSID and WIFI password
ssid = wifi_info.ssid
wifi_password = wifi_info.wifi_password
my_ip_addr = '192.168.0.22'

# Please see https://docs.micropython.org/en/latest/library/network.WLAN.html
# Try to connect to WIFI
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Specify the IP address
wlan.ifconfig((my_ip_addr, '255.255.255.0', '192.168.0.1', '8.8.8.8'))

# Connect
wlan.connect(ssid, wifi_password)

# Wait for connect or fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')    
    time.sleep(1)
    
# Handle connection error
if wlan.status() != 3:
    # Connection to wireless LAN failed
    print('Connection failed, reset in 5 seconds')
    time.sleep(5)
    machine.reset()    
    
else:
    print('Connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )
    
# Try to set the time
try:
    ntptime.settime()
except:
    print("Could not set time, reset in 5 seconds")
    time.sleep(5)
    machine.reset()

# Set the offset from UTC
UTC_OFFSET = -4 * 60 * 60
    
# Open socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Try to bind the socket
try:
    s.bind(addr)
        
except:
    print('Bind Failed - waiting 5 seconds and then will reset');    
    time.sleep(5)
    machine.reset()
    
# Listen
s.listen(1)
print('listening on', addr)

# Timeout for the socket accept, i.e., s.accept()
s.settimeout(10)

# Kick off the thread
# Start the thread
print("Starting thread...")
_thread.start_new_thread(read_water_meter_thread, ())        
time.sleep(7)

# Listen for connections, serve up web page
while True:
    
    # Handle connection error
    if wlan.status() != 3:
        # Connection to wireless LAN failed
        print('Connection failed during regular operation - go for reset')
        time.sleep(5)
        machine.reset()
        
    # Main loop
    accept_worked = 0
    try:
        print("Run s.accept()")
        cl, addr = s.accept()
        accept_worked = 1
    except:  
        # Nobody connected, so do a bit of busy work...        
        
        # Get the local time
        temp_time = time.localtime(time.time() + UTC_OFFSET)
        
        # The current day of the week
        day_of_week = temp_time[6]
        
        # Get the day of the week from the status, and the min and max
        baton.acquire()
        old_day = water_meter_tick_count[7]
        temp_str = str(cycle_min_measure) + ", " + str(cycle_max_measure)
        baton.release()
        
        # Print the min and max sensor values
        print("Min Max: " + temp_str)
        
        # If the days don't match
        if day_of_week != old_day:
            baton.acquire()
            # Reset the next day counter
            water_meter_tick_count[day_of_week] = 0
            # Update the day
            water_meter_tick_count[7] = day_of_week
            baton.release()
        
        # Get the contents of the water meter tick count array
        baton.acquire()
        for ii in range(8):
            temp_water_meter_tick_count[ii] = water_meter_tick_count[ii]
        baton.release()
                        
        # Save the status file
        fid = open(F_NAME_STATUS, 'wb')        
        fid.write(bytearray(temp_water_meter_tick_count))
        fid.close()
                
        # Next, create the website
        my_web = website_info.html_start
            
        # Add the bars
        for ii in range(7):            
            my_web = my_web + website_info.createBar(temp_water_meter_tick_count[ii], ii)
            
        # Add the ending HTML
        my_web = my_web + website_info.html_end
        
        # Create the file
        try:
            fid = open(F_NAME_WATER_WEBSITE, 'w')
            fid.write(my_web)
            fid.close()
        except:
            print("Not able to create water website file...")
        
        print('Timeout waiting on accept - reset the pico if you want to break out of this')
        time.sleep(0.5)
        
    if accept_worked == 1:
        # Exciting - somebody is looking for a webpage!
        try:
            print('client connected from', addr)
            request = cl.recv(1024)
            print("request:")
            print(request)
            request = str(request)
            
            # Default response is error message                        
            response = """<HTML><HEAD><TITLE>Error</TITLE></HEAD><BODY>Not found...</BODY></HTML>"""
                    
            # Parse the request for the filename - in the root directory
            # Look for the "GET" text
            base_file = request.find('GET /')            
            if base_file == 2:
                # Look for the "HTTP" text
                end_name = request.find(' HTTP')
                
                if end_name != -1:
                    # Get the filename
                    f_name = request[7 : end_name]
                    
                    # Print the filename
                    print("filename: " + f_name)
                    
                    try:                    
                        # Get the file size, in bytes
                        temp = os.stat(f_name)
                    
                        f_size_bytes = temp[6]
                    
                        fid = open(f_name, 'rb')
                        response = fid.read()
                        print(len(response))
                        fid.close()
                    except:
                        print("Issue finding file...")
                        
                                
            cl.send('HTTP/1.0 200 OK\r\nContent-Length: ' + str(len(response)) + '\r\nConnection: Keep-Alive\r\n\r\n')
            cl.sendall(response)
                
            cl.close()
            
        except OSError as e:
            cl.close()
            print('connection closed')
            

