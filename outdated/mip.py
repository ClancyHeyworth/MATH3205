import gurobipy as gp
from outdated.util import *

filename = 'power_systems_radial/bus_83_11.pos'
F = read_pos_file(filename)
G = Graph(F)
plot_graph(G)

m = gp.Model()

m.setParam('OutputFlag', 0)

N = range(G.info.Nodes)
A = [(a.Src_bus, a.Rec_bus) for a in G.info.Arcs + G.info.Tie_switches]
# AS = G.get_possible_switch_placements()
MAX_SWITCHES = G.info.Tie_count

X = {
    (i, j) : m.addVar(vtype=gp.GRB.BINARY)
    for i, j in A
}

F = {
    (i, j) : m.addVar()
    for i, j in A
}

BigF = {
    j : m.addVar()
    for j in N
}

import numpy as np
np.random.seed(1)
Theta = [np.random.rand()/100 for _ in N]
L_D = [np.random.rand() for _ in N]
#L_D = [G.get_downstream_load(i) for i in N]
M = 100

m.setObjective(
    gp.quicksum((L_D[i] + L_D[j]) * F[i, j] for (i, j) in A),
    gp.GRB.MINIMIZE
)

m.addConstr(gp.quicksum(X[i, j] for (i, j) in A) <= MAX_SWITCHES)

NodeDict = {
    (i, j) : [k for k in N if (j, k) in A]
    for (i, j) in A
}
print(X.keys())
m.addConstr(
    X[0, 11] == 1
)

NodeBalance = {
    (i, j) :
    m.addConstr(
        BigF[j] + F[i, j] ==\
        Theta[j] + gp.quicksum(F[j, k] for k in NodeDict[(i, j)])
    )
    for (i, j) in A
}

SlackCoupling = {
    (i, j) :
    m.addConstr(
        BigF[j] <= M * X[i, j] 
    )
    for (i, j) in A
}

m.optimize()

model_output = [x for x in X if round(X[x].x) == 1]

print(model_output)
print(m.ObjVal)
plot_output(G, model_output)
