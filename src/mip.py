"""
This module contains run_mip, the function used to run the mixed-integer model.
"""

import gurobipy as gp
from util import Graph
from math import floor
from params import ModelOutput, ModelParams

def run_mip(params : ModelParams) -> ModelOutput:
    """
    Runs basic MIP optimization for given parameters.\\
    """

    """
    Loading in parameters
    """
    G = params.G
    verbal = params.verbal
    time_limit = params.time_limit
    presolve = params.do_presolve
    P = params.P
    
    """
    Setup
    """

    m = gp.Model()

    """
    Sets
    """

    V = G.V
    A = G.edges

    """
    Data
    """

    L_D = G.downstream_load
    Theta = G.theta
    # M = 2**32 # Very large value
    M = G.M
    P = P # Percentage of arcs that can be switches
    # Maximum number of switches that can be placed, including mandatory between substations and root
    N = floor(P * len(A)) + len(G.substations)
    Outgoing = G.outgoing # stores nodes that go out of j for incoming (i, j)

    Elb = G.get_ens_lower_bound()
    Eub = G.get_ens_upper_bound()

    """
    Variables
    """

    X = { # Assignment of switch on arc (i, j)
        (i, j) : m.addVar(vtype=gp.GRB.BINARY)
        for i, j in A
    }

    F = { # Interruption flow on arc (i, j)
        (i, j) : m.addVar(lb=0)
        for i, j in A
    }

    BigF = { # Interruption slack on node j
        j : m.addVar()
        for j in V
    }

    """
    Objective
    """

    m.setObjective(
        gp.quicksum((L_D[i] - L_D[j]) * F[i, j] for (i, j) in A) + Elb,
        gp.GRB.MINIMIZE
    )

    """
    Constraints
    """

    # We must place switch between root and substation for all substations
    SwitchesBetweenRootAndSubstation = {
        (0, j) :
        m.addConstr(X[0, j] == 1)
        for j in V if (0, j) in A
    }

    # Number of switches <= Max switches
    m.addConstr(gp.quicksum(X[i, j] for (i, j) in A) <= N)

    # Node balance constraint
    NodeBalance = {
        (i, j) :
        m.addConstr(
            BigF[j] + F[i, j] == Theta[j] + gp.quicksum(F[j, k] for k in V if k in Outgoing[j])
        )
        for (i, j) in A
    }

    # Slack only non-zero if switch present on arc
    SlackCoupling = {
        (i, j) :
        m.addConstr(
            BigF[j] <= M * X[i, j] 
        )
        for (i, j) in A
    }

    """
    Optimize + Output
    """
    
    # if not verbal:
    if not verbal:
        m.setParam('OutputFlag', 0)
    m.setParam('MIPGap', params.MIPGap)
    m.setParam('FeasibilityTol', params.FeasibilityTol)
    m.setParam('OptimalityTol', params.OptimalityTol)
    m.setParam('Seed', params.gurobi_seed)

    if time_limit:
        m.setParam('TimeLimit', 600)
    if not presolve:
        m.setParam('Presolve', 0)

    m.optimize()

    if verbal:
        model_output = [x for x in X if round(X[x].x) == 1]
        print('Switches placed:', model_output)
        print('ENS', m.ObjVal)
        print('LB:', Elb)
        print('UB', Eub)
    return ModelOutput(m.ObjVal, {x : round(X[x].X) for x in X}, {x : F[x].X for x in F}, {x : BigF[x].X for x in BigF}, m.Runtime) 

KNOWN_OPTIMAL_OUTPUTS = {
    (3, 0.2) : 2715.24,
    (3, 0.4) : 2269.21,
    (3, 0.6) : 2144.88,
    (3, 0.8) : 2089.06,
    (4, 0.2) : 2504.72,
    (4, 0.4) : 2361.50,
    (4, 0.6) : 2340.32,
    (4, 0.8) : 2340.32,
    (5, 0.2) : 4801.43,
    (5, 0.8) : 3747.42,
    (6, 0.8) : 1437.63
}

def main():
    params = ModelParams(6, 0.6, verbal=True)
    print(run_mip(params).time)

if __name__ == "__main__":
    main()