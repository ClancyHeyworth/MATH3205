import gurobipy as gp
from util import *
from math import floor

filename = 'networks/R3.switch'
F = read_pos_file(filename)
G = Graph(F)

m = gp.Model()

# Sets
V = range(len(G.G.nodes))
A = [(a.node1, a.node2) for a in G.info.edges if a.node1]

# Data
L_D = {i : G.get_downstream_load(i) for i in V} # Downstream load of node i
N = floor(0.2 * len(A)) # Maximum number of switches that can be placed
Outgoing = { # stores nodes that go out of j for incoming (i, j)
    (i, j) : [k for k in V if (j, k) in A]
    for (i, j) in A
}
Theta = {v : G.index_node[v].theta for v in V}
M = 2**32 # Very large value

# Variables
X = { # Assignment of switch on arc (i, j)
    (i, j) : m.addVar(vtype=gp.GRB.BINARY)
    for i, j in A
}

F = { # Interruption flow on arc (i, j)
    (i, j) : m.addVar()
    for i, j in A
}

BigF = { # Interruption slack on arc (i, j)
    j : m.addVar()
    for j in V
}

# Objective - LB not included
m.setObjective(
    gp.quicksum((L_D[i] + L_D[j]) * F[i, j] for (i, j) in A),
    gp.GRB.MINIMIZE
)

# Constraints

# Number of switches <= Max switches
m.addConstr(gp.quicksum(X[i, j] for (i, j) in A) <= N)

# Node balance constraint
NodeBalance = {
    (i, j) :
    m.addConstr(
        BigF[j] + F[i, j] ==\
        Theta[j] + gp.quicksum(F[j, k] for k in Outgoing[(i, j)])
    )
    for (i, j) in A
}

# Slack only non-zero if switch present on arfc
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
print('Switches placed:', model_output)
print('Objective Value:', m.ObjVal)
print('Bounds:', Elb, m.ObjVal + Elb, Eub)