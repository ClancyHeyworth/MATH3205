import gurobipy as gp
from util import Graph
from reader import read_pos_file
from math import floor
import time

def run_benders(G : Graph, P : float,  verbal : bool = False, time_limit : bool = False) \
        -> tuple[float, dict[tuple[int, int], int], dict[tuple[int, int], float]]:
    """
    Runs Benders optimization for given parameters.\\
    G : Graph object\\
    P : proportion of arcs that can have a switch\\
    verbal : whether to print gurobi output, assigned switches and objective value\\
    time_limit : whether to set 600 second time limit on gurobi optimization \\
    Returns:\\
    objective value, X values, Lambda values
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

    P = P
    N = floor(P * len(A)) + len(G.substations)# Maximum number of switches that can be placed, including mandatory between substations and root
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

    # Initial cut
    # InitialCut = {
    #     (i, j) :
    #     m.addConstr(Lambda[i, j] >= G.theta[j] * (G.downstream_load[i] - G.downstream_load[j]) * (1 - X[i, j]))
    #     for i, j in A
    # }

    """
    Optimize + Output
    """
    _searched_subtrees = dict()
    def Callback(model : gp.Model, where : int):
        if where == gp.GRB.Callback.MIPSOL:
            XV = model.cbGetSolution(X)
            XV = {x : round(XV[x]) for x in XV}

            if verbal:
                print('------------')
                print('Current ENS:', G.calculate_V_s(A, XV) + Elb)
                LambdaV = model.cbGetSolution(Lambda)
                print('Lambda Sum', sum(LambdaV.values()))

            subtrees = G.get_subtrees(XV)

            if verbal:
                print('Average subtree length:', sum(len(subtree) for subtree in subtrees) / len(subtrees))
                print(f'X used: {sum(XV.values())}, X Available: {N}')
                print()

            for subtree in subtrees:
                Savings = {}
                V_s = G.calculate_V_s(subtree, XV)

                if subtree not in _searched_subtrees:
                    for i, j in subtree:
                        XV[i, j] = 1
                        Savings[i, j] = V_s - G.calculate_V_s(subtree, XV)
                        XV[i, j] = 0
                        _searched_subtrees[subtree] = Savings
                Savings = _searched_subtrees[subtree]

                try:
                    model.cbLazy(gp.quicksum(Lambda[i, j] for i, j in subtree) >= 
                                V_s - 
                                gp.quicksum(
                                    Savings[i, j] * X[i, j] for i, j in subtree
                                )
                    )
                except:
                    print('Constraint adding failed. Clancys fault.')
                    quit()

    m.setParam('OutputFlag', 0)
    m.setParam('MIPGap', 0)
    m.setParam('LazyConstraints', 1)

    if time_limit:
        m.setParam('TimeLimit', 600)
    m.optimize(Callback)

    if verbal:
        print('ENS', m.ObjVal)
        print('LB:', Elb)
        print('UB', Eub)

    solution = {x : round(X[x].X) for x in X}
    return m.ObjVal, solution, {x : Lambda[x].X for x in Lambda}

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
    P = 0.2
    file_number = 6
    filename = f'networks/R{file_number}.switch'
    F = read_pos_file(filename)
    G = Graph(F)
    t1 = time.time()
    output = run_benders(G, P, verbal=True)[0]
    print('Final ENS:', output)
    t2 = time.time()

    print('Time taken:', t2 - t1)

if __name__ == "__main__":
    main()