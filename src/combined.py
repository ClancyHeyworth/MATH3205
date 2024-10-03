import numpy as np
from util import *
from math import floor
import gurobipy as gp

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

from copy import copy
import matplotlib.pyplot as plt
from tqdm import tqdm

def SA(G:Graph, P:float, k_max:int):
    downstream_load = G.downstream_load
    theta = G.theta
    Eub = G.get_ens_upper_bound()
    Elb = G.get_ens_lower_bound()

    A = G.edges
    N = floor(P * len(A)) + len(G.substations)

    # Initial placement
    A_ = [a for a in A if a[0] != 0]
    indexes = np.random.choice(len(A_), size = N - len(G.substations))
    s = [A_[i] for i in indexes]

    outgoing = G.outgoing # stores nodes that go out of j for incoming (i, j)

    percentage_replace = 0.2
    n_replace = floor(percentage_replace * len(s))

    # e_initial = energy_function(A_, s, downstream_theta, downstream_load)
    e_initial = energy_function(A_, s, theta, downstream_load, G, Eub, outgoing)
    energy_values = [e_initial]

    best_e = e_initial
    best_s = s

    temps = []

    T = None
    a = 0.99
    for k in tqdm(range(k_max), disable = False):

        to_replace = np.random.choice(len(s), size=n_replace)
        new_choice = np.random.choice(len(A_), size=n_replace)

        s_new = copy(s)
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
    print('Best ENS from SA:', best_e * Eub + Elb)
    return set(best_s)

def run_optimisation(G:Graph, initial_solution, P, 
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

    for (i, j) in A:
        if (i, j) in initial_solution:
            X[i, j].Start = 1

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
    _searched_subtrees = dict()
    def Callback(model : gp.Model, where : int):
        if where == gp.GRB.Callback.MIPSOL:
            XV = model.cbGetSolution(X)
            XV = {x : round(XV[x]) for x in XV}

            # print('Current ENS:', G.calculate_V_s(A, XV) + Elb)
            numcuts = 0

            subtrees = G.get_subtrees(XV)

            # print('Average subtree length:', sum(len(subtree) for subtree in subtrees) / len(subtrees))
            # print('X used', sum(XV.values()), 'X Available', N)

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
                    numcuts += 1
                    model.cbLazy(gp.quicksum(Lambda[i, j] for i, j in subtree) >= 
                                V_s - 
                                gp.quicksum(
                                    Savings[i, j] * X[i, j] for i, j in subtree
                                )
                    )
                except:
                    print('Constraint adding failed. Clancys fault.')
                    quit()
            # print('Cuts:', numcuts)
    
    if not verbal:
        pass
    m.setParam('OutputFlag', 0)
    m.setParam('MIPGap', 0)
    m.setParam('LazyConstraints', 1)

    t1 = time.time()
    m.optimize(Callback)
    t2 = time.time()
    print('Benders Time', t2 - t1)
   

    model_output = [x for x in X if round(X[x].x) == 1]

    if verbal:
        print('Switches placed:', model_output)
        print('ENS', m.ObjVal)
        print('LB:', Elb)
        print('UB', Eub)

    return m.ObjVal

import time
def run_combined_optimisation(P, file_number) -> float:
    filename = f'networks/R{file_number}.switch'
    F = read_pos_file(filename)
    G = Graph(F)

    t1 = time.time()
    SA_solution = SA(G, P, 100)
    t2 = time.time()
    print('SA Time', t2 - t1)
    run_optimisation(G, SA_solution, P)

if __name__ == "__main__":

    P = 0.8
    file_number = 4
    
    run_combined_optimisation(P, file_number)


   