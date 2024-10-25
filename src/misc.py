from util import Graph
from math import floor
import gurobipy as gp

def run_mip_start(G : Graph, P : float, solution : dict[tuple[int, int], int], verbal : bool = False) \
        -> tuple[float, dict[tuple[int, int], int], dict[tuple[int, int], float], dict[tuple[int, int], float]]:
    """
    Runs basic MIP optimization for given parameters with suggested starting values of X from solution.\\
    G : Graph object\\
    P : proportion of arcs that can have a switch\\
    solution : Dictionary of X values from solved model, mapping arc (i, j) to assignment {0, 1} \\
    verbal : whether to print gurobi output, assigned switches and objective value\\
    Returns:\\
    objective value, X values, F values, Slack values
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
    M = G.M # Very large value
    print('M', M)
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

    # Set solution as starting values
    for i, j in A:
        X[i, j].Start = solution[i, j]
    m.update()
    # m.setParam('FeasibilityTol', 1e-09)
    # m.setParam('IntFeasTol', 1e-09)
    # m.setParam('NumericFocus', 3)
    # m.setParam('BarConvTol', 1e-10)
    # m.setParam('Presolve', 0)


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
    m.setParam('MIPGap', 0)

    # m.setParam('PoolSearchMode', 1)
    # m.setParam('PoolSolutions', 10)

    m.optimize()

    for i, j in A:
        try:
            assert BigF[j].X <= M * round(X[i, j].X)
        except:
            print(X[i,j].X, X[i,j].X * M, BigF[j].X)

    if verbal:
        # model_output = [x for x in X if round(X[x].x) == 1]
        # print('Switches placed:', model_output)
        print('ENS', m.ObjVal)
        print('LB:', Elb)
        print('UB', Eub)

    return m.ObjVal, {x : round(X[x].x) for x in X}, {x : F[x].X for x in F}, {x : BigF[x].X for x in BigF}

def run_mip_fixed(G : Graph, P : float, solution : dict[tuple[int, int], int], verbal : bool = False) \
        -> tuple[float, dict[tuple[int, int], int], dict[tuple[int, int], float], dict[tuple[int, int], float]]:
    """
    Runs basic MIP optimization for given parameters with fixed X values from solution.\\
    G : Graph object\\
    P : proportion of arcs that can have a switch\\
    solution : Dictionary of X values from solved model, mapping arc (i, j) to assignment {0, 1} \\
    verbal : whether to print gurobi output, assigned switches and objective value\\
    Returns:\\
    objective value, X values, F values, Slack values
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
    M = G.M # Very large value
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

    # Set solution
    SolutionConstraint = {
        (i, j) :
        m.addConstr(
            X[i, j] == solution[i, j]
        )
        for i, j in A
    }

    """
    Optimize + Output
    """
    
    # if not verbal:
    if not verbal:
        m.setParam('OutputFlag', 0)
    m.setParam('MIPGap', 0)

    # m.setParam('PoolSearchMode', 1)
    # m.setParam('PoolSolutions', 10)

    m.optimize()

    if verbal:
        model_output = [x for x in X if round(X[x].x) == 1]
        print('Switches placed:', model_output)
        print('ENS', m.ObjVal)
        print('LB:', Elb)
        print('UB', Eub)

    return m.ObjVal, {x : round(X[x].x) for x in X}, {x : F[x].X for x in F}, {x : BigF[x].X for x in V}