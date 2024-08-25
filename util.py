from reader import *
from copy import deepcopy
import matplotlib.pyplot as plt

class Graph:
    def __init__(self, info : Info) -> None:
        self.info = info
        
        # Maps bus node -> directly downstream nodes
        self.graph_dict:dict[Bus, set[Bus]] = {}
        
        # Maps bus node -> all downstread nodes
        self.successors:dict[Bus, set[Bus]] = {}
        
        self._make_graph()
    
    def _make_graph(self) -> None:
        """
        Constructs node to node dictionary and successors dictionary
        """
        branches = self.info.Branches
        self.graph_dict = {bus : set() for bus in self.info.Buses}
        buses = self.info.Buses
        buses = sorted(buses, key = lambda x : x.num)
        
        for branch in branches:
            src_bus = buses[branch.Src_bus]
            rec_bus = buses[branch.Rec_bus]
            self.graph_dict[src_bus] |= {rec_bus}
            
        for bus in reversed(buses):
            self.successors[bus] = self._construct_successors(bus)
        
    def _construct_successors(self, bus:Bus) -> set[Bus]:
        """
        Depth-first search for successors of bus
        """
        children = self.graph_dict[bus]
        output = deepcopy(children)
        
        for child in children:
            if child in self.successors.keys():
                output |= self.successors[child]
            else:
                output |= self._construct_successors(child)
            
        return output
    
def plot_graph(graph:Graph) -> None:
    F = graph.info
    
    x_coords = [x.x_coord for x in F.Buses]
    y_coords = [x.y_coord for x in F.Buses]
    i = plt.scatter(x_coords, y_coords, color='sienna')

    for x in F.Branches:
        j = plt.quiver(x_coords[x.Src_bus], y_coords[x.Src_bus], 
                x_coords[x.Rec_bus] - x_coords[x.Src_bus], y_coords[x.Rec_bus] - y_coords[x.Src_bus],
                angles='xy', scale_units='xy', scale=1, color='teal')
        
    for x in F.Tie_switches:
        k = plt.quiver(x_coords[x.Src_bus], y_coords[x.Src_bus], 
                x_coords[x.Rec_bus] - x_coords[x.Src_bus], y_coords[x.Rec_bus] - y_coords[x.Src_bus],
                angles='xy', scale_units='xy', scale=1, color='orchid')

    plt.title('Example Power Distribution System')

    plt.legend([i, j, k], ['Bus', 'Branch', 'Switch'])
    plt.show()
        
filename = 'Project/power_systems_radial/bus_29_1.pos'
#filename = 'Project/power_systems_radial/bus_10476_84.pos'
F = read_pos_file(filename)
g = Graph(F)
plot_graph(g)