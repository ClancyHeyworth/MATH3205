from util import Graph, load_graph_object
from random import randint
from generate import generate_similar_graph
from dataclasses import dataclass

@dataclass
class ModelOutput:
    """
    Stores the output of run optimization functions\\
    =====================\\
    obj : objective value of optimisation - optimal ENS\\
    X : value of X variable - binary placement of switches\\
    F : value of F variabkles - Interruption time on arc\\
    FSlack : value of FSlack variables - Slack of interruption time on arc\\
    time : gurobi run time
    """
    obj : float
    X : dict[tuple[int, int], float]
    F : dict[tuple[int, int], float]
    FSlack : dict[tuple[int, int], float]
    time : float
    gap : float = None

class ModelParams:
    """
    Stores parameter value for optimisation functions
    """
    def __init__(self,
                file_number : int,
                P : float,
                do_presolve : bool = True,
                verbal : bool = False,
                time_limit : bool = True,
                MIPGap : float = 0,
                FeasibilityTol : float = 1e-9,
                OptimalityTol : float = 1e-9,
                make_similar_graph : bool = False,
                gurobi_seed : int = None,
                nodes_factor : int = 1
                ) -> None:
        """
        file_number : 3-7, number of dataset in networks to use
        P : proportion of arcs that a switch can be placed
        do_presolve : whether gurobi uses presolve techniques
        verbal : whether to print output
        time_limit : 600 second time limit on optimisation
        MIPGap : Gap between acceptable solution and optimal solution
        FeasibilityTol : Tolerance of floating point number on constraints
        OptimalityTol : Tolerance of floating point number on objective value
        make_similar_graph : if true, create graph with similar values as graph in file_number
        gurobi_seed : what value to seed gurobi randomizer with
        nodes_factor : if make_similar_graph, how many more nodes to multiply current amount by
        """
        self.file_number  = file_number
        self.P = P
        self.do_presolve = do_presolve
        self.verbal = verbal
        self.time_limit = time_limit
        self.MIPGap = MIPGap
        self.FeasibilityTol = FeasibilityTol
        self.OptimalityTol = OptimalityTol
        self.gurobi_seed = gurobi_seed

        if self.gurobi_seed is None:
            self.gurobi_seed = randint(0, 2000000000 - 1)
        
        self.G = load_graph_object(file_number)

        if make_similar_graph:
            self.G = generate_similar_graph(self.G, nodes_factor)

if __name__ == "__main__":
    # G1 = ModelParams(6, 0.6).G
    # G2 = ModelParams(6, 0.6, make_similar_graph=True, verbal=True, nodes_factor=10).G
    # G1.plot_graph()
    # G2.plot_graph()

    # print(G1.get_ens_lower_bound(), G1.get_ens_upper_bound())
    # print(G2.get_ens_lower_bound(), G2.get_ens_upper_bound())
    # quit()
    from benders import run_benders
    from mip import run_mip

    params = ModelParams(6, 0.6, make_similar_graph=True, verbal=False, nodes_factor=10)

    res = run_benders(params)
    print(res.obj, res.time)
    params.verbal=True
    res = run_mip(params)
    print(res.obj, res.time)