"""
This file contains an example for how to run the different optimisation methods.
"""
from params import ModelParams, ModelOutput
from benders import run_benders
from mip import run_mip
from check_validity import check_constraints

"""
The parameters given to one of the optimisation functions are controlled by the 
ModelParams object. This object also loads in the power distribution datasets.
Networks with similar values to an existing file can be generated with the
make_similar_graph argument, and nodes_factor as a multiplier for the amount
of nodes in the new dataset.
"""
params = ModelParams(file_number = 6, P = 0.6, verbal = True)

"""
The optimisation methods return a ModelOutput object, which contains the variable 
values, the objective value, and the optimisation time. The example chosen, R6
with P = 60%, highlights how the Benders formulation can find the solution with far 
less time for some select situations.
"""
benders_output = run_benders(params)
mip_output = run_mip(params)

print(f'Benders Objective: {round(benders_output.obj, ndigits=3)}, Benders Time to Optimality: {round(benders_output.time, ndigits=3)}')
print(f'MIP Objective: {round(mip_output.obj, ndigits = 3)}, MIP Time to Optimality: {round(mip_output.time, ndigits=3)}')

"""
The validity of a solution, i.e. it did not violate any constraints, can be checked as 
such. This is used to ensure that the optimization functions had constraint that were
correctly configured.
"""
check_constraints(params, benders_output)
check_constraints(params, mip_output)