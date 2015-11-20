"""
Identifies temperature sensors when individually heated
Writes the information to OUTPUT_FILE (default: map.txt).  If it already
exists from a previous run, that data will be used first.

Requires numpy and pyepics

KL
"""
#!/usr/bin/env python
from __future__ import print_function
import os
import epics
import numpy as np
import time


## NOTE: you will need to change these PV formats
##       %.3d in this example means there will be from
##       3IDC{SENS:001}T-I to 3IDC{SENS:125}T-I
PV_FORMAT = '5IDB{SENS:%.3d}T-I'
ADDR_FORMAT = '5IDB{SENS:%.3d}ID-I'
SENSOR_COUNT = 5
TEMP_THRESHOLD = 26  # 26 degrees C is the detection threshold
OUTPUT_FILE = 'map.txt'
##

SENSOR_COUNT += 1

pvs = dict((idx, epics.PV(PV_FORMAT % idx)) for idx in range(1, SENSOR_COUNT))
addr_pvs = dict((idx, epics.PV(ADDR_FORMAT % idx)) for idx in range(1, SENSOR_COUNT))

remaining_ids = set(pvs.keys())
addresses = dict((idx, addr_pvs[idx].get()) for idx in range(1, SENSOR_COUNT))
for idx, pv in pvs.items():
    addr = addresses[idx]
    print('%.3d %s %.4f' % (idx, addr, pv.get()))


sensor_id = 1
if os.path.exists(OUTPUT_FILE):
    # remove any pre-mapped sensors
    for line in open(OUTPUT_FILE, 'rt').readlines():
        line = line.strip()
        if line.startswith('#'):
            continue
        sid, epics_id, addr, value = line.split('\t')
        remaining_ids.remove(int(epics_id))
        sensor_id = int(sid) + 1

map_file = open(OUTPUT_FILE, 'at')

print('# Sensor ID\tEPICS ID\tAddress\tValue',
      file=map_file)
print('Starting sensor id %s' % sensor_id)
while sensor_id < SENSOR_COUNT:
    ids = list(remaining_ids)
    values = [pvs[sid].get() for sid in ids]
    max_index = np.argmax(values)
    max_value = values[max_index]
    max_id = ids[max_index]
    addr = addresses[max_id]
    if max_value > TEMP_THRESHOLD:
        print('Sensor %d EPICS sensor ID %d address %s temperature %s' %
              (sensor_id, max_id, addr, max_value))
        remaining_ids.remove(max_id)
        print('Remaining sensors: %d' % (len(remaining_ids), ))
        print('%d\t%d\t%s\t%s' % (sensor_id, max_id, addr, max_value),
              file=map_file)
        sensor_id += 1
    else:
        time.sleep(0.1)
