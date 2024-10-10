import gurobipy as gp
from util import *
from math import floor
from copy import deepcopy
import matplotlib.pyplot as plt
import time
from tqdm import tqdm

def run_benders(file_number : int, P : float, 
                    verbal : bool = False) -> None:
    """
    Runs Benders for for given parameters.\\
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

    """
    Optimize + Output
    """
    _searched_subtrees = dict()
    AverageSubtreeLengthList = []
    SubtreeTimeSteps =[]
    def Callback(model : gp.Model, where : int):
        if where == gp.GRB.Callback.MIPSOL:
            XV = model.cbGetSolution(X)
            XV = {x : round(XV[x]) for x in XV}


            if verbal:
                print('Current ENS:', G.calculate_V_s(A, XV) + Elb)

            subtrees = G.get_subtrees(XV)
        
            if verbal:
                AverageSubtreeLength = sum(len(subtree) for subtree in subtrees) / len(subtrees)
                print('Average subtree length:', AverageSubtreeLength)
                print('X used', sum(XV.values()), 'X Available', N)
                AverageSubtreeLengthList.append(AverageSubtreeLength)
                SubtreeStep = time.time()
                SubtreeTimeSteps.append(SubtreeStep)
            for subtree in subtrees:
                Savings = {}
                V_s = G.calculate_V_s(subtree, XV) 
                #how much is contributed to the obj here

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
    m.optimize(Callback)

    if verbal:
        print('ENS', m.ObjVal)
        print('LB:', Elb)
        print('UB', Eub)

    return m.ObjVal, SubtreeTimeSteps, AverageSubtreeLengthList, N, Eub

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

if __name__ == "__main__":

    # for i in range(3, 8):
    #     output = run_optimisation(i, P)
    #     print(i, output)
    #     if (i, P) in KNOWN_OPTIMAL_OUTPUTS:
    #         print('Difference from expected:', abs(100 * (KNOWN_OPTIMAL_OUTPUTS[i, P] - output)/KNOWN_OPTIMAL_OUTPUTS[i, P]))
    #     print()
    # P = 0.2
    # output = run_optimisation(7, P, verbal=True)


    
    # P = 0.4
    # filename = 6
    # output = run_benders(filename, P, verbal=True)
    # P_20 = 0.2
    # P_40 = 0.4
    # P_60 = 0.6
    # P_80 = 0.8
    P = [0.2,0.4,0.6,0.8]
    filename = [3,4,5,6,7]
    #must be a more elegant way to do this
    # for filename in files, run percentage in P P =[0.2,0.4,0.6,0.8]
    #append P points to a list, time points to a list, then plot all at the end
    #could be very slow?
    
    # output_6_20 = run_benders(6, P_20, verbal=True)
    # output_6_40 = 
    # output_6_60 =
    # output_6_80 = 

    # print('Final ENS', output)
    # t2 = time.time()
    # print(t2 - t1)
    # run_time = t2 - t1
    # plt.plot(P, run_time, marker="x")
    # plt.show()
    P_points = []
    time_points = [] 

    P = [0.2,0.4,0.6,0.8]
    # filename = [3,4,5,6,7]
    f = 3
    # for f in filename:
    """
    Visualisation of computation time vs percentage of switches in network
    """
    for p in P:
        t1 = time.time()
        output = run_benders(f, p, verbal=True)
        print('Final ENS', output[0])
        t2 = time.time()
        print(t2 - t1)
        run_time = t2 - t1
        P_points.append(p)
        time_points.append(run_time)
        subtree_times = output[1]
        subtree_lengths = output[2]
        N = output[3]
        EUpperBound = output[4] #kWh/yr
        EN = output[0]
        CostPerSwitch = 1358 #USD/year
        InterruptionCost = 1.53 #USD/kWh
        ENSCostSaving = InterruptionCost*(EUpperBound-EN)
        Cost_Points = [CostPerSwitch*p*N for p in P]
    print(P_points, time_points)
    print(subtree_times, subtree_lengths) #not working properly atm

    # plt.plot(P_points, time_points, marker="x")
    # plt.plot(subtree_times, subtree_lengths, marker = "o")
    # plt.show()

    """
    Visualisation of av. subtree length vs time
    """

    """
    Visualisation of solution lower bound vs time
    """
    """
    Visualisation of costings vs P
    """
    N = output[3]
    EUpperBound = output[4] #kWh/yr
    EN = output[0]
    CostPerSwitch = 1358 #USD/year
    InterruptionCost = 1.53 #USD/kWh
    ENSCostSaving = [InterruptionCost*(EUpperBound-EN)] #how will I get a list here, I don't understand the code
    Cost_Points = [CostPerSwitch*p*N for p in P]
    Returns_Points = [ens-c for c in Cost_Points for ens in ENSCostSaving]
    plt.plot(P_points, Cost_Points, label ="Switch Investment Cost", marker ="o", color="blue")
    plt.plot(P_points, ENSCostSaving, label ="ENS Cost Savings", marker ="x", color="black")
    plt.plot(P_points, Returns_Points, label="Returns", marker = "-", color ="red")
    plt.show()
    #Visualisation code here
    #need to store values for each run, so that they can be all plotted on the same area
    #is there a way to find an optimal P from this plot? would need some arbitrary time limit guideline
