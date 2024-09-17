import gurobipy as gp
from util import *
from math import floor

filename = 'networks/R4.switch'
F = read_pos_file(filename)
G = Graph(F)

m = gp.Model()

# Sets
V = G.V.keys()
# V = range(len(G.G.nodes))
A = G.edges
# print(A)

# Data
L_D = {i : G.get_downstream_load(i) for i in V} # Downstream load of node i
Outgoing = { # stores nodes that go out of j for incoming (i, j)
    (i, j) : [k for k in V if (j, k) in A]
    for (i, j) in A
}
Theta = {v : G.index_node[v].theta for v in V}
M = 20000 #2**32 # Very large value
P = 0.2
N = floor(P * len(A)) # Maximum number of switches that can be placed

# Variables
X = { # Assignment of switch on arc (i, j)
    (i, j) : m.addVar(vtype=gp.GRB.BINARY)
    for i, j in A
}

F = { # Interruption flow on arc (i, j)
    (i, j) : m.addVar(lb=0)
    for i, j in A
}

# BigF = { # Interruption slack on arc (i, j)
#     j : m.addVar()
#     for j in V
# }

# Objective - LB not included
m.setObjective(
    gp.quicksum((L_D[i] + L_D[j]) * F[i, j] for (i, j) in A),
    gp.GRB.MINIMIZE
)

# Constraints

# Number of switches <= Max switches
m.addConstr(gp.quicksum(X[i, j] for (i, j) in A) <= N)

SlackCoupling = {
    (i, j) :
    m.addConstr(
        F[i, j] >= Theta[j] + gp.quicksum(F[j, k] for k in Outgoing[(i, j)]) - M*X[i, j]
    )
    for (i, j) in A
}

# Node balance constraint
# NodeBalance = {
#     (i, j) :
#     m.addConstr(
#         BigF[j] + F[i, j] ==\
#         Theta[j] + gp.quicksum(F[j, k] for k in Outgoing[(i, j)])
#     )
#     for (i, j) in A
# }

# # Slack only non-zero if switch present on arc
# SlackCoupling = {
#     (i, j) :
#     m.addConstr(
#         BigF[j] <= M * X[i, j] 
#     )
#     for (i, j) in A
# }

m.setParam('MIPGap', 0)
m.optimize()

model_output = [x for x in X if round(X[x].x) == 1]

Elb = G.get_eps_lower_bound()
Eub = G.get_eps_upper_bound()
print('Switches placed:', model_output)
print('Objective Value:', m.ObjVal)
print('EPS', m.ObjVal + Elb)
print('Bounds:', Elb, m.ObjVal + Elb, Eub)

total = 0
for (i, j) in F:
    total += (L_D[i] + L_D[j]) * F[i, j].x
    print(total, F[i, j].x)
    if round(F[(i, j)].X) > 0:
        print(i, j)
