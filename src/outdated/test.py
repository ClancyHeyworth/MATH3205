from mip import run_mip
from util import load_graph_object, Graph
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

def p_time(file_number:int) -> None:
    G = load_graph_object(file_number)

    step = 0.05
    ps = []
    times = []
    for p in tqdm(np.arange(0, 1 + step, step)):
        time = run_mip(G, p)[1]

        times.append(time)
        ps.append(p)
    
    plt.plot(ps, times)
    plt.show()

def p_value(file_number:int) -> None:
    G = load_graph_object(file_number)
    print(G.get_ens_upper_bound())

    step = 0.02
    ps = []

    E_ub = G.get_ens_upper_bound()

    N = len(G.edges) - len(G.substations)
    C_s = 1358
    C_e = 1.53
    C_e = 1.132
    C_s = 0.32

    savings = []
    switch_investments = []
    returns = []

    from math import floor

    # for p in tqdm(np.arange(0, 1 + step, step)):
    for n in range(101):
        p = n / (len(G.edges) - len(G.substations))
    
        E_n = run_mip(G, p)[0]
        N = n
        # N = p * (len(G.edges) - len(G.substations))

        savings.append(C_e *(E_ub - E_n))
        switch_investments.append(C_s * N)
        returns.append(C_e *(E_ub - E_n) - C_s * N)
        ps.append(p)

        if n == 40:
            

        if n == 21:
            print(returns[-1])
            print(switch_investments[-1])
            print(savings[-1])
            # goal = 66247
            print(66247.41/(C_e *(E_ub - E_n) * N))
    
    plt.plot(ps, savings)
    plt.plot(ps, switch_investments)
    plt.plot(ps, returns)

    plt.show()

p_value(5)

    