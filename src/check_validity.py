
import numpy as np
from benders import run_benders
from mip import run_mip
from math import floor
from params import ModelOutput, ModelParams

def check_constraints(params:ModelParams, output:ModelOutput) -> bool:
    XV = output.X
    SlackV = output.FSlack
    FV = output.F
    G = params.G
    N = floor(params.P * len(G.edges)) + len(G.substations)
    violation = False
    
    # Check max switch constraint
    assert sum([XV[x] for x in XV]) <= N

    for i, j in FV:
        LHS = round(SlackV[j] + FV[i, j], 6)
        RHS = round(G.theta[j] + sum([FV[j, k] for k in G.V if k in G.outgoing[j]]), 6)
        if LHS != RHS:
            print('---- constraint failure ----')
            print(i, j)
            print('Equality Constraint')
            print(LHS, RHS)
            print(SlackV[j] + FV[i, j], G.theta[j] + sum([FV[j, k] for k in G.V if k in G.outgoing[j]]))
            print()
            violation = True
        if SlackV[j] > G.M * XV[i, j]:
            # continue
            print('---- constraint failure ----')
            print(i, j)
            print('Slack Constraint')
            print('XV:', XV[i, j])
            print('Slack', SlackV[j], 'F', FV[i, j], 'RHS', G.theta[j] + sum([FV[j, k] for k in G.V if k in G.outgoing[j]]))
            print()
            violation = True
        if i == 0:
            if XV[i, j] == 0:
                print('---- constraint failure ----')
                print(i, j)
                print('Substation Constraint')
                print(XV[i, j])
                print()
                violation = True
    if violation:
        print('Check showed violations of constraints.')
    else:
        print('Check showed no violations of constraints.')
            
def check_solution():
    np.random.seed(0)

    params = ModelParams(7, 0.2)
    output = run_benders(params)
    check_constraints(params, output)

    output = run_mip(params)
    check_constraints(params, output)

def main():
    check_solution()

if __name__ == "__main__":
    main()