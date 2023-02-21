# Here is a piece of reference code for testing the MMC5603NJ magnetometer

# Imports
import machine
import sys
import time
from machine import Pin

# Functions
def reg_write(i2c, addr, reg, data): # Write bytes to register
        
    # Construct message
    msg = bytearray()
    msg.append(data)
    
    # Write out message to register
    i2c.writeto_mem(addr, reg, msg)
    
def reg_read(i2c, addr, reg, nbytes=1): # Read bytes       
    # Check to make sure caller is asking for 1 or more bytes
    if nbytes < 1:
        return bytearray()
    
    # Request data from specified register(s) over I2C
    data = i2c.readfrom_mem(addr, reg, nbytes)
    
    return data    

# Values
MMC_ADDR = 0x30
REG_XOUT0 = 0x00
REG_PRODUCT_ID = 0x39
REG_TEMPERATURE_OUT = 0x09
REG_DEVICE_STATUS1 = 0x18

REG_INTERNAL_CONTROL_0 = 0x1B
REG_INTERNAL_CONTROL_1 = 0x1C
REG_INTERNAL_CONTROL_2 = 0x1D
REG_ST_X = 0x27
REG_ST_Y = 0x28
REG_ST_Z = 0x29

# Other values
PRODUCT_ID = 0x10

# Create I2C object
# Use I2C 0
# scl and sda are connected to GP17 and GP16 respectively
# Frequency is set to 400 000 Hz
i2c = machine.I2C(0, scl=machine.Pin(17), sda=machine.Pin(16), freq=400000)

# Print out any addresses found
devices = i2c.scan()

print("Expect:\t" + hex(MMC_ADDR))
if devices:
    for d in devices:
        print("Found:\t" + hex(d))

# Used for triggering to measure the I2C waveforms
pin = Pin("GP0", Pin.OUT)
pin.value(1)              
              
# Read the device ID
data = reg_read(i2c, MMC_ADDR, REG_PRODUCT_ID)
if (data != bytearray((PRODUCT_ID,))):
    print("Error, did not read PRODUCT_ID")
    sys.exit()

# Read the device status register
stat_1_start = reg_read(i2c, MMC_ADDR, REG_DEVICE_STATUS1)
print("stat_1_start: " + hex(stat_1_start[0]))

# Set the BW
reg_write(i2c, MMC_ADDR, REG_INTERNAL_CONTROL_1, 0x03)


# Try a write - temperature measurement
reg_write(i2c, MMC_ADDR, REG_INTERNAL_CONTROL_0, 0x22)
found_it = 0
count = 0
while found_it == 0:
    stat_1_temp_go = reg_read(i2c, MMC_ADDR, REG_DEVICE_STATUS1)
    print("   stat_1_temp_go: " + hex(stat_1_temp_go[0]))
    
    if ((stat_1_temp_go[0] >> 7) & 1) == 1:
        found_it = 1
    else:
         count = count + 1
         
         if count > 50:
             print("Temperature Not Ready...")
             sys.exit()

# Read the temperature
temp = reg_read(i2c, MMC_ADDR, REG_TEMPERATURE_OUT)
print("Temperature reading: " + str(temp[0]) + ", temperature (approx): " + str(-75 + 200 / 255 * temp[0]) + " C")

stat_1_temp_read = reg_read(i2c, MMC_ADDR, REG_DEVICE_STATUS1)
print("stat_1_temp_read: " + hex(stat_1_temp_read[0]))

tick_now = time.ticks_us()

for ii in range(128):
    # Try a write - magnetic measurement
    reg_write(i2c, MMC_ADDR, REG_INTERNAL_CONTROL_0, 0x21)
    # Read the device status register
    found_it = 0
    count = 0
    while found_it == 0:
        stat_1_mag_go = reg_read(i2c, MMC_ADDR, REG_DEVICE_STATUS1)
        #print("   stat_1_mag_go: " + hex(stat_1_mag_go[0]))
        
        if ((stat_1_mag_go[0] >> 6) & 1) == 1:
            found_it = 1
        else:
             count = count + 1
             
             if count > 100:
                 print("Magnetic data not ready...")
                 sys.exit()

    # Read the magnetic data
    mag_data = reg_read(i2c, MMC_ADDR, REG_XOUT0, 9)

    x_total = (mag_data[0] << 12) + (mag_data[1] << 4) + mag_data[6]
    y_total = (mag_data[2] << 12) + (mag_data[3] << 4) + mag_data[7]
    z_total = (mag_data[4] << 12) + (mag_data[5] << 4) + mag_data[8]
    
    x_out = x_total - 524288
    y_out = y_total - 524288
    z_out = z_total - 524288
        
    # print(str(x_out) + "\t" + str(y_out) + "\t" + str(z_out))

    # Read the device status register
    # stat_1_mag_read = reg_read(i2c, MMC_ADDR, REG_DEVICE_STATUS1)
    # print("stat_1_mag_read: " + hex(stat_1_mag_read[0]))

tick_done = time.ticks_us()

temp = time.ticks_diff(tick_done, tick_now)

print(temp)
