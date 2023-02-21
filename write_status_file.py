# Create the status file for the water meter monitor

# Imports
import array

# File name of the status file
f_name = 'water_meter_status.bin'

# Water meter tick count
water_meter_tick_count = array.array("I", [0] * 8)

# Put in some dummy data
water_meter_tick_count[0] = 0 # Monday
water_meter_tick_count[1] = 0
water_meter_tick_count[2] = 0
water_meter_tick_count[3] = 0
water_meter_tick_count[4] = 0
water_meter_tick_count[5] = 0
water_meter_tick_count[6] = 0
water_meter_tick_count[7] = 6 # Day of the week, 0 for Monday, ...6 for Sunday

# Create the file
fid = open(f_name, 'wb')
fid.write(bytearray(water_meter_tick_count))
fid.close()


