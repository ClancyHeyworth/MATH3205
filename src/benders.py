import gurobipy as gp
from util import *
from math import floor
from copy import deepcopy

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
    m = gp.Model()

    """
    Sets
    """

    V = G.V
    A = G.edges

    """
    Data
    """

    L_D = {i : G.get_downstream_load(i) for i in V} # Downstream load of node i
    Theta = {v : G.index_node[v].theta for v in V}
    M = 2**32 # Very large value
    P = P
    # N = floor(P * (len(A) - len(G.substations))) + len(G.substations) # Maximum number of switches that can be placed, including mandatory between substations and root
    N = floor(P * len(A)) + len(G.substations)
    Outgoing = { # stores nodes that go out of j for incoming (i, j)
        j : [k for k in V if (j, k) in A]
        for j in V
    }
    Elb = G.get_ens_lower_bound()
    Eub = G.get_ens_upper_bound()

    """
    Variables
    """

    X = { # Assignment of switch on arc (i, j)
        (i, j) : m.addVar(vtype=gp.GRB.BINARY)
        for i, j in A
    }

    Lambda = {
        (i, j) : m.addVar(lb = 0)
        for i, j in A
    }

    """
    Objective
    """

    m.setObjective(
        gp.quicksum(Lambda[i, j] for i, j in A) + Elb,
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
    MaxSwitches = m.addConstr(gp.quicksum(X[i, j] for (i, j) in A) <= N)

    """
    Optimize + Output
    """

    def Callback(model : gp.Model, where : int):
        if where == gp.GRB.Callback.MIPSOL:
            XV = model.cbGetSolution(X)
            XV = {x : round(XV[x]) for x in XV}

            print('Current EPS:', G.calculate_V_s(A, XV) + Elb)

            subtrees = G.get_subtrees(XV)

            for subtree in subtrees:
                Savings = {}
                V_s = G.calculate_V_s(subtree, XV)
                for i, j in subtree:
                    XV_copy = deepcopy(XV)
                    XV_copy[i, j] = 1
                    Savings[i, j] = V_s - G.calculate_V_s(subtree, XV_copy)
                try:
                    model.cbLazy(gp.quicksum(Lambda[i, j] for i, j in subtree) >= 
                                V_s - 
                                gp.quicksum(
                                    Savings[i, j] * X[i, j] for i, j in subtree
                                )
                    )
                except:
                    print('Constraint adding failed. Clancys fault.')
                    xxxx
    
    if not verbal:
        pass
    m.setParam('OutputFlag', 0)
    m.setParam('MIPGap', 0)
    m.setParam('LazyConstraints', 1)
    m.optimize(Callback)

    model_output = [x for x in X if round(X[x].x) == 1]

    if verbal:
        print('Switches placed:', model_output)
        print('ENS', m.ObjVal)
        print('LB:', Elb)
        print('UB', Eub)
    #print(model_output)
    # model_output = {x : round(X[x].X) for x in X}
    # subtrees = G.get_subtrees(model_output)
    # total = sum(G.calculate_V_s(subtree, model_output, reset=True) for subtree in subtrees)
    # print(total + Elb)
    print(m.ObjVal)

    # output = 0
    # for i, j in A:
    #     downstream_theta = G.calculate_contribution(i, j, model_output)
    #     output += (L_D[i] - L_D[j]) * downstream_theta
    # print(output)
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

    # for i in range(3, 8):
    #     output = run_optimisation(i, P)
    #     print(i, output)
    #     if (i, P) in KNOWN_OPTIMAL_OUTPUTS:
    #         print('Difference from expected:', abs(100 * (KNOWN_OPTIMAL_OUTPUTS[i, P] - output)/KNOWN_OPTIMAL_OUTPUTS[i, P]))
    #     print()
    # P = 0.2
    # output = run_optimisation(7, P, verbal=True)

    import time

    t1 = time.time()
    P = 0.8
    output = run_optimisation(5, P, verbal=False)
    t2 = time.time()
    print(t2 - t1)