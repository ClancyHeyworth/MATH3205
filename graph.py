
import reader

filename = 'Project/power_systems_radial/bus_29_1.pos'
# filename = 'Project/power_systems_radial/bus_32_1.pos'
# filename = 'Project/power_systems_radial/bus_83_11.pos'
# filename = 'Project/power_systems_radial/bus_10476_84.pos'
# filename = 'Project/power_systems_radial/bus_201_3.pos'
F = reader.read_pos_file(filename)

import matplotlib.pyplot as plt
