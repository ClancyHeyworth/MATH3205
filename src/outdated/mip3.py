import gurobipy as gp
from util import *
from math import floor

_F_RHS = dict()
def calculate_F_RHS(i, j, XV, Theta, Outgoing):
    if (i, j) not in _F_RHS:
        _F_RHS[(i, j)] = (1 - XV[i, j]) * \
            (
                Theta[j] + sum(
                calculate_F_RHS(j, k, XV, Theta, Outgoing) for k in Outgoing[j]
                )
            )
    return _F_RHS[i, j]

# from mip2 import run_optimisation
# file_number = 4
# filename = f'networks/R{file_number}.switch'
# F = read_pos_file(filename)
# G = Graph(F)

# V = G.V
# A = G.edges

# Theta = {v : G.index_node[v].theta for v in V}
# Outgoing = { # stores nodes that go out of j for incoming (i, j)
#     j : [k for k in V if (j, k) in A]
#     for j in V
# }
# Elb = G.get_eps_lower_bound()
# Eub = G.get_eps_upper_bound()
# L_D = {i : G.get_downstream_load(i) for i in V}

# P = 0.2
# _, XV = run_optimisation(4, P)

# total = 0
# for a in A:
#     print(calculate_F_RHS(*a, XV, Theta, Outgoing))
#     total += (L_D[a[0]] - L_D[a[1]]) * calculate_F_RHS(*a, XV, Theta, Outgoing)
# print(total + Elb)


def run_optimisation(file_number : int, P : float, 
                    verbal : bool = False) -> None:
    """
    Runs basic MIP optimization for given parameters.\\
    file_number : which dataset to use, between 3 and 7\\
    P : proportion of arcs that can have a switch\\
    verbal : whether to print gurobi output, assigned switches and objective value
    """
    
    """
    Setup
    """

    filename = f'networks/R{file_number}.switch'
    F = read_pos_file(filename)
    G = Graph(F)

    """
    Sets
    """

    V = G.V
    A = G.edges

    """
    Data
    """

    L_D = {i : G.get_downstream_load(i) for i in V} # Downstream load of node i
    Local_Interruption = {v : G.index_node[v].theta for v in V}
    M = 2**32 # Very large value
    P = P
    # N = floor(P * (len(A) - len(G.substations))) + len(G.substations) # Maximum number of switches that can be placed, including mandatory between substations and root
    N = floor(P * len(A)) + len(G.substations)
    Outgoing = { # stores nodes that go out of j for incoming (i, j)
        j : [k for k in V if (j, k) in A]
        for j in V
    }
    Elb = G.get_eps_lower_bound()
    Eub = G.get_eps_upper_bound()

    """
    Variables
    """

    m = gp.Model()

    BSP = {(i, j) : gp.Model() for (i, j) in A}

    X = { # Assignment of switch on arc (i, j)
        (i, j) : m.addVar(vtype=gp.GRB.BINARY)
        for i, j in A
    }

    Theta = {
        (i, j) : m.addVar(lb=0)
        for i, j in A
    }

    C = {
        (i, j) : 
        {
            (k, l) : BSP[i, j].addVar()
            for k, l in G.get_successor_arcs(j) | {(i, j)}
        }
        for i, j in BSP
    }
    
    F = { # Interruption flow on arc (i, j)
        (i, j) : BSP[i, j].addVar()
        for i, j in BSP
    }

    """
    Objective
    """

    m.setObjective(
        gp.quicksum(Theta[i, j] for i, j in A) + Elb,
        gp.GRB.MINIMIZE
    )

    for i, j in A:
        BSP[i, j].setObjective(
            (L_D[i] - L_D[j]) * F[i, j],
            gp.GRB.MINIMIZE
        )

    """
    Constraints
    """
    K = {}
    for i, j in BSP:
        K[(i, j)] = BSP[i, j].addConstr(F[i, j] >= 0)
    K:dict[tuple[int, int] : gp.Constr]

    # We must place switch between root and substation for all substations
    SwitchesBetweenRootAndSubstation = {
        (0, j) :
        m.addConstr(X[0, j] == 1)
        for j in V if (0, j) in A
    }

    # Number of switches <= Max switches
    m.addConstr(gp.quicksum(X[i, j] for (i, j) in A) <= N)

    """
    Optimize + Output
    """
    m.setParam('OutputFlag', 0)
    m.setParam('LazyConstraints', 1)
    m.setParam('MIPGap', 0)

    for (i, j) in A:
        BSP[i, j].setParam('OutputFlag', 0)

    while True:
        m.optimize()

        XV = {x : X[x].X for x in X}

        CutsAdded = False
        numcuts = 0

        for (i, j) in A:
            K[i, j].RHS = calculate_F_RHS(i, j, XV, Local_Interruption, Outgoing)
            BSP[i, j].optimize()

            if BSP[i, j].ObjVal > Theta[i, j].X + 0.0001:
                CutsAdded = True
                numcuts += 1
                #print(K[i, j].pi)
                m.addConstr(
                    Theta[i, j] >= K[i, j].RHS #K[i, j].pi * (1 - X[i, j])
                )
        # Reset dict
        global _F_RHS
        _F_RHS = dict()
        print(numcuts, m.ObjVal)
        if not CutsAdded:
            break

    model_output = [x for x in X if round(X[x].x) == 1]

    #print('Switches placed:', model_output)
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

    t1 = time.time()
    P = 0.2
    file_number = 3
    output = run_optimisation(file_number, P, verbal=False)
    print('objval', output)
    t2 = time.time()
    print(t2 - t1)