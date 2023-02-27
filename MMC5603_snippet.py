# If you want to use the MMC5603 instead of the ST magnetometer, here are the pieces of code to do it
# You will have to experiment to see which axis and what high and low limits are best

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

# Thresholds
THRESH_HIGH = 0
THRESH_LOW = -10000


# The thread for reading the water meter and updating the number of ticks from the water meter
def read_water_meter_thread():
    # Bring in the variable into the thread
    global water_meter_tick_count
    global cycle_max_measure
    global cycle_min_measure
    global THRESH_HIGH
    global THRESH_LOW
    
    # Use I2C 0
    # scl and sda are connected to GP17 and GP16 respectively
    # Frequency is set to 400 000 Hz
    i2c = machine.I2C(0, scl=machine.Pin(17), sda=machine.Pin(16), freq=400000)

    # Print out any addresses found
    #devices = i2c.scan()

    #print("Expect:\t" + hex(MMC_ADDR))
    #if devices:
    #    for d in devices:
    #        print("Found:\t" + hex(d))
             
    # Read the device ID
    data = reg_read(i2c, MMC_ADDR, REG_PRODUCT_ID)
    if (data != bytearray((PRODUCT_ID,))):
        print("Error, did not read PRODUCT_ID")
        time.sleep(5)
        machine.reset()

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
             time.sleep(5)
             machine.reset()

    # Read the temperature
    temp = reg_read(i2c, MMC_ADDR, REG_TEMPERATURE_OUT)
    print("Temperature reading: " + str(temp[0]) + ", temperature (approx): " + str(-75 + 200 / 255 * temp[0]) + " C")

    stat_1_temp_read = reg_read(i2c, MMC_ADDR, REG_DEVICE_STATUS1)
    print("stat_1_temp_read: " + hex(stat_1_temp_read[0]))
    
    time.sleep(1)
    
    current_min = 65536
    current_max = 0
    
    # The state
    search_state = 0 # 0 for LOOK HIGH, 1 for LOW LOW
    
    while True:
        # Try a write - magnetic measurement
        reg_write(i2c, MMC_ADDR, REG_INTERNAL_CONTROL_0, 0x21)
    
        # Read the device status register
        found_it = 0
        count = 0
        while found_it == 0:
            # Let the sensor take a measurement
            time.sleep_us(500)
        
            # Is the sensor ready?
            stat_1_mag_go = reg_read(i2c, MMC_ADDR, REG_DEVICE_STATUS1)
        
            if ((stat_1_mag_go[0] >> 6) & 1) == 1:
                found_it = 1
            else:
                count = count + 1
                       
            if count > 100:
                print("Magnetic data not ready...")
                time.sleep(5)
                machine.reset()
        
        # Read the magnetic data
        mag_data = reg_read(i2c, MMC_ADDR, REG_XOUT0, 9)

        x_total = (mag_data[0] << 12) + (mag_data[1] << 4) + mag_data[6]
        y_total = (mag_data[2] << 12) + (mag_data[3] << 4) + mag_data[7]
        z_total = (mag_data[4] << 12) + (mag_data[5] << 4) + mag_data[8]
    
        x_out = x_total - 524288
        y_out = y_total - 524288
        z_out = z_total - 524288
    
        # Here - you have to select which axis you want to use...
        temp = x_out
                
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
                water_meter_tick_count[water_meter_tick_count[7]] = water_meter_tick_count[water_meter_tick_count[7]] + 1
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
