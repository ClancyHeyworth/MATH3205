import gurobipy as gp
from util import *
from math import floor

def run_mip(G : Graph, P : float, verbal : bool = False) -> None:
    """
    Runs basic MIP optimization for given parameters.\\
    file_number : which dataset to use, between 3 and 7\\
    P : proportion of arcs that can have a switch\\
    verbal : whether to print gurobi output, assigned switches and objective value
    """
    
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
    M = 2**32 # Very large value
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
    m.setParam('OutputFlag', 0)
    m.setParam('MIPGap', 0)

    t1 = time.time()
    m.optimize()
    t2 = time.time()
    print('actual optim time', t2 - t1)

    model_output = [x for x in X if round(X[x].x) == 1]

    if verbal:
        print('Switches placed:', model_output)
        print('ENS', m.ObjVal)
        print('LB:', Elb)
        print('UB', Eub)

    return m.ObjVal

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

if __name__ == "__main__":

    import time

    file_number = 6
    filename = f'networks/R{file_number}.switch'
    F = read_pos_file(filename)
    G = Graph(F)
    P = 0.2

    t1 = time.time()
    output = run_mip(G, 0.4, verbal=False)
    print(output)
    t2 = time.time()
    print(t2 - t1)