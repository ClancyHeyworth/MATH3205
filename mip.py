import gurobipy as gp
from util import *

filename = 'networks/R3.switch'
F = read_pos_file(filename)
G = Graph(F)

m = gp.Model()

m.setParam('OutputFlag', 0)

N = range(1, G.info.node_num+1)
A = [(a.node1, a.node2) for a in G.info.all_edges]

for a in A:
    j, k = a
    if j not in N:
        print(j)
    if k not in N:
        print(k)
# AS = G.get_possible_switch_placements()
MAX_SWITCHES = int(0.2 * len(N))
print(MAX_SWITCHES)

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
L_D = {i : G.get_downstream_load(i) for i in N}
Theta = {index : G.index_node[index].theta for index in N}
M = 100000

m.setObjective(
    gp.quicksum((L_D[i] + L_D[j]) * F[i, j] for (i, j) in A),
    gp.GRB.MINIMIZE
)

m.addConstr(gp.quicksum(X[i, j] for (i, j) in A) <= MAX_SWITCHES)

NodeDict = {
    (i, j) : [k for k in N if (j, k) in A]
    for (i, j) in A
}

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

Elb = G.get_eps_lower_bound()
Eub = G.get_eps_upper_bound()
print(model_output)
print(m.ObjVal)
print(Elb, m.ObjVal + Elb, Eub)
#print(m.ObjVal + Elb)
#plot_output(G, model_output)
