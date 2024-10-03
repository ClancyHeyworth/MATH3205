import gurobipy as gp
from util import *
from math import floor, exp
import numpy as np

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

    # X = { # Assignment of switch on arc (i, j)
    #     (i, j) : m.addVar(ub=1)
    #     for i, j in A
    # }

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

    # A_ = [a for a in A if a[0] != 0]
    # indexes = np.random.choice(len(A_), size = N - len(G.substations))
    # choices = [A_[i] for i in indexes]
    # Arbitary = {
    #     (i, j) :
    #     m.addConstr(X[i, j] == 1)
    #     for (i, j) in choices
    # }

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
    
    m.setParam('OutputFlag', 0)
    m.setParam('MIPGap', 0)
    m.optimize()

    model_output = [x for x in X if round(X[x].x) == 1]

    if verbal:
        print('Switches placed:', model_output)
        print('ENS', m.ObjVal)
        print('LB:', Elb)
        print('UB', Eub)

    # downstream_theta = {i : G.get_downstream_theta(i) for i in V}
    # for a in sorted(A):
    #     #if round(X[a].x) == 1:
    #     if downstream_theta[a[1]] < F[a].x:
    #         print(a, F[a].x, X[a].x, len(G.successors_dict[a[1]]), Theta[a[1]], downstream_theta[a[1]])
    # print(np.mean([(L_D[a[0]] - L_D[a[1]]) * downstream_theta[a[1]] for a in A]))
    # print(np.mean([(L_D[a[0]] - L_D[a[1]]) * downstream_theta[a[1]] for a in model_output]))
    return m.ObjVal

def run_optimisation_fixed(G:Graph, P : float, switches : list[tuple[int, int]],
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

    # X = { # Assignment of switch on arc (i, j)
    #     (i, j) : m.addVar(ub=1)
    #     for i, j in A
    # }

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

    SwitchPlacements = {
        (i, j) :
        m.addConstr(X[i, j] == 1)
        for (i, j) in switches
    }

    # Number of switches <= Max switches
    m.addConstr(gp.quicksum(X[i, j] for (i, j) in A) <= N)

    # A_ = [a for a in A if a[0] != 0]
    # indexes = np.random.choice(len(A_), size = N - len(G.substations))
    # choices = [A_[i] for i in indexes]
    # Arbitary = {
    #     (i, j) :
    #     m.addConstr(X[i, j] == 1)
    #     for (i, j) in choices
    # }

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

    m.setParam('OutputFlag', 0)
    m.setParam('MIPGap', 0)
    m.optimize()

    model_output = [x for x in X if round(X[x].x) == 1]

    if verbal:
        # print('Switches placed:', model_output)
        print(N)
        print(len(switches) + len(G.substations))
        print('ENS', m.ObjVal)
        print('LB:', Elb)
        print('UB', Eub)

    # downstream_theta = {i : G.get_downstream_theta(i) for i in V}
    # for a in sorted(A):
    #     #if round(X[a].x) == 1:
    #     if downstream_theta[a[1]] < F[a].x:
    #         print(a, F[a].x, X[a].x, len(G.successors_dict[a[1]]), Theta[a[1]], downstream_theta[a[1]])
    # print(np.mean([(L_D[a[0]] - L_D[a[1]]) * downstream_theta[a[1]] for a in A]))
    # print(np.mean([(L_D[a[0]] - L_D[a[1]]) * downstream_theta[a[1]] for a in model_output]))
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

_F_RHS = dict()
def calculate_F_RHS(i, j, switches_placed, Theta, Outgoing):
    if (i, j) not in _F_RHS:
        XV = 1 if (i, j) in switches_placed else 0

        _F_RHS[(i, j)] = (1 - XV) * \
            (
                Theta[j] + sum(
                calculate_F_RHS(j, k, switches_placed, Theta, Outgoing) for k in Outgoing[j]
                )
            )
    return _F_RHS[i, j]

_energy_function = dict()
def energy_function(A : list[tuple[int, int]], switches_placed : list[tuple[int, int]], 
                    theta : dict[int, float], downstream_load : dict[int, float], 
                    G:Graph, Eub : float, outgoing):
    s_switches_placed = frozenset(switches_placed)
    if s_switches_placed in _energy_function:
        return _energy_function[s_switches_placed]
    else:
        output = 0
        for i, j in A:
            downstream_theta = calculate_F_RHS(i, j, switches_placed, theta, outgoing)
            output += (downstream_load[i] - downstream_load[j]) * downstream_theta
    global _F_RHS
    _F_RHS = dict()
    return output / Eub

def Prob(e_dash, e, T):
    if e_dash < e:
        return True
    r = np.random.random()
    if r < np.exp(-1 * (e_dash - e) / T):
        return True
    return False

from copy import deepcopy
import matplotlib.pyplot as plt
from tqdm import tqdm

def SA(G:Graph, P:float):
    downstream_load = {i : G.get_downstream_load(i) for i in G.V}
    theta = G.theta
    Eub = G.get_ens_upper_bound()

    A = G.edges
    N = floor(P * len(A)) + len(G.substations)

    # Initial placement
    A_ = [a for a in A if a[0] != 0]
    indexes = np.random.choice(len(A_), size = N - len(G.substations))
    s = [A_[i] for i in indexes]

    outgoing = { # stores nodes that go out of j for incoming (i, j)
        j : [k for k in G.V if (j, k) in A]
        for j in G.V
    }

    k_max = 1000
    percentage_replace = 0.2
    n_replace = floor(percentage_replace * len(s))

    # e_initial = energy_function(A_, s, downstream_theta, downstream_load)
    e_initial = energy_function(A_, s, theta, downstream_load, G, Eub, outgoing)
    energy_values = [e_initial]

    best_e = e_initial
    best_s = s

    temps = []
    probs = []

    j = 0

    T = None
    a = 0.99
    for k in tqdm(range(k_max), disable = False):

        to_replace = np.random.choice(len(s), size=n_replace)
        new_choice = np.random.choice(len(A_), size=n_replace)

        s_new = deepcopy(s)
        for t, n in zip(to_replace, new_choice):
            s_new[t] = A_[n]

        e_s = energy_function(A_, s, theta, downstream_load, G, Eub, outgoing)
        e_s_new = energy_function(A_, s_new, theta, downstream_load, G, Eub, outgoing)

        deltaE = abs(e_s_new - e_s)
        if T is None:
            T = -deltaE / np.log(0.5)
            initial_T = T
        else:
            T = a * T

        energy_values.append(e_s)
        temps.append(T)

        if T < initial_T/100:
            T = initial_T * (1 - k/k_max)

        if Prob(e_s_new, e_s, T):
            s = s_new

        if e_s_new < best_e:
            best_e = e_s_new
            best_s = s_new
    
    run_optimisation_fixed(G, P, best_s, verbal=True)
    fig, ax1 = plt.subplots()

    ax1.set_xlabel('Iteration (k)')
    ax2 = ax1.twinx()
    ax1.plot(energy_values, 'g-')
    ax2.plot(temps, 'r-')

    ax1.set_ylabel('Energy')
    ax2.set_ylabel('Temperature')
    plt.show()
if __name__ == "__main__":

    # P = 0.2

    # for i in range(4, 8):
    #     output = run_optimisation(i, P)
    #     break
    #     print(i, output)
    #     if (i, P) in KNOWN_OPTIMAL_OUTPUTS:
    #         print('Difference from expected:', abs(100 * (KNOWN_OPTIMAL_OUTPUTS[i, P] - output)/KNOWN_OPTIMAL_OUTPUTS[i, P]))
    #     print()
    
    # output = run_optimisation(7, P, verbal=True)

    # import time

    # t1 = time.time()
    # output = run_optimisation(4, P, verbal=False)
    # t2 = time.time()
    # print(t2 - t1)
    P = 0.8
    file_number = 6
    filename = f'networks/R{file_number}.switch'
    F = read_pos_file(filename)
    G = Graph(F)
    SA(G, P)


   