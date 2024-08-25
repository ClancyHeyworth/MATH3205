from reader import *

# R3 ?
# filename = 'Project/power_systems_radial/bus_32_1.pos'

# # R4 ?
filename = 'Project/power_systems_radial/bus_83_11.pos'

# # R5 ?
# filename = 'Project/power_systems_radial/bus_135_8.pos'

# # R6 ?
# filename = 'Project/power_systems_radial/bus_201_3.pos'

# # R7 ?
# filename = 'Project/power_systems_radial/bus_873_7.pos'

F = read_pos_file(filename)

total = 0
for arc in F.Branches:
    arc : Branch
    if arc.Rec_bus != 0:
        total += arc.PL_kw

print(total)