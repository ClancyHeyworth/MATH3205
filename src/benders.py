import gurobipy as gp
from util import Graph
from math import floor
from params import ModelParams, ModelOutput

def run_benders(params : ModelParams) -> ModelOutput:
    """
    Runs Benders optimization for given parameters.\\
    """
    
    """
    Setup
    """
    
    G = params.G
    verbal = params.verbal
    presolve = params.do_presolve
    time_limit = params.time_limit
    m = gp.Model()

    """
    Sets
    """

    V = G.V
    A = G.edges

    """
    Data
    """

    P = params.P
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

    F = { # Duration of interruption on arc (i, j)
        (i, j) : m.addVar(lb = 0)
        for i, j in A
    }

    FSlack = { # Slack variable
        j : m.addVar(lb = 0)
        for j in V
    }

    """
    Objective
    """

    m.setObjective(
        gp.quicksum((G.downstream_load[i] - G.downstream_load[j]) * F[i, j] for i, j in A) + Elb,
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

    theta_sum = sum([v for v in G.theta.values()])
    M = theta_sum * G.downstream_load[0]

    Equality = {
        (i, j) :
        m.addConstr(F[i, j] + FSlack[j] == G.theta[j] + gp.quicksum(F[j, k] for k in G.outgoing[j]))
        for i, j in A
    }

    M = theta_sum
    Slack = {
        (i, j) :
        m.addConstr(FSlack[j] <= M * X[i, j])
        for i, j in A
    }

    """
    Optimize + Output
    """
    _searched_subtrees = dict()
    _ENS = dict()
    def Callback(model : gp.Model, where : int):
        if where == gp.GRB.Callback.MIPSOL:
            XV = model.cbGetSolution(X)
            XV = {x : round(XV[x]) for x in XV}
            subtrees = G.get_subtrees(XV)

            cuts_added = 0

            for subtree in subtrees:
                if subtree not in _ENS:
                    _ENS[subtree] = G.calculate_ENS(subtree, XV)
                    cuts_added += 1
                ENS = _ENS[subtree]

                Savings = {}
                if subtree not in _searched_subtrees:
                    for i, j in subtree:
                        XV[i, j] = 1
                        Savings[i, j] = ENS - G.calculate_ENS(subtree, XV)
                        XV[i, j] = 0
                    _searched_subtrees[subtree] = Savings
                Savings = _searched_subtrees[subtree]

                try:
                    model.cbLazy(gp.quicksum(
                        (G.downstream_load[i] - G.downstream_load[j]) * F[i, j] for i, j in subtree) >= 
                                ENS - 
                                gp.quicksum(
                                    Savings[i, j] * X[i, j] for i, j in subtree
                                )
                    )
                except:
                    print('Constraint adding failed. Clancys fault.')
                    quit()
            
            
            if verbal:
                print('------------')
                print('Current ENS:', G.calculate_ENS(A, XV) + Elb)
                print('Average subtree length:', sum(len(subtree) for subtree in subtrees) / len(subtrees))
                print(f'X used: {sum(XV.values())}, X Available: {N}')
                print(f'Cuts added: {cuts_added}')
                print(f'Total cuts: {len(_searched_subtrees)}')
                print()

    m.setParam('OutputFlag', 0)
    m.setParam('MIPGap', params.MIPGap)
    m.setParam('LazyConstraints', 1)
    m.setParam('FeasibilityTol', params.FeasibilityTol)
    m.setParam('OptimalityTol', params.OptimalityTol)
    m.setParam('Seed', params.gurobi_seed)
    if not presolve:
        m.setParam('Presolve', 0)

    if time_limit:
        m.setParam('TimeLimit', 600)
    m.optimize(Callback)

    if verbal:
        print('ENS', m.ObjVal)
        print('LB:', Elb)
        print('UB', Eub)

    output = ModelOutput(m.ObjVal, 
        {x : round(X[x].X) for x in X}, 
        {x : F[x].X for x in F},
        {x : FSlack[x].X for x in FSlack},
        m.Runtime,
        m.MIPGap
    )
    return output