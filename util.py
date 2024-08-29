from reader import *
from copy import deepcopy
import matplotlib.pyplot as plt

class Graph:
    def __init__(self, info : Info) -> None:
        self.info = info
        
        # Maps node num to bus object
        self.int_bus:dict[int, Bus] = {}
        for bus in self.info.Buses:
            self.int_bus[bus.num] = bus

        # Maps bus node -> directly downstream nodes
        self.graph_dict:dict[Bus, set[Bus]] = {}
        
        # Maps bus node -> all downstread nodes
        self.successors:dict[Bus, set[Bus]] = {}

        # Maps (bus1, bus2) -> branch
        self.bus_pair_branches:dict[tuple[Bus], Branch] = {}
        
        self._make_graph()

        # Maps node num -> downstream load
        self.downstream_load:dict[int, float] = {}
        for bus in self.info.Buses:
            self.downstream_load[bus.num] = self._calculate_downstream_load(bus.num)

    def get_downstream_load(self, node:int) -> float:
        return self.downstream_load[node]
    
    def get_possible_switch_placements(self) -> list[tuple[int, int]]:
        return [(bus.num, v.num) for bus in self.info.Buses for v in self.successors[bus]]

    def _calculate_downstream_load(self, node:int) -> float:
        bus = self.info.Buses[node]
        immediate_successors = self.graph_dict[bus]
        branches_to_search = set([self.bus_pair_branches[(bus, child)] 
                                for child in immediate_successors])
        output = 0
        while len(branches_to_search) != 0:
            branch = branches_to_search.pop()
            output += branch.PL_kw
            bus = self.info.Buses[branch.Rec_bus]
            immediate_successors = self.graph_dict[bus]
            branches_to_search |= set([self.bus_pair_branches[(bus, child)] 
                                for child in immediate_successors])
        return output

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

            self.bus_pair_branches[(src_bus, rec_bus)] = branch
            
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

def plot_output(graph:Graph, output:list[tuple[int]]) -> None:
    F = graph.info
    
    x_coords = [x.x_coord for x in F.Buses]
    y_coords = [x.y_coord for x in F.Buses]
    i = plt.scatter(x_coords, y_coords, color='sienna')

    for x in F.Branches + F.Tie_switches:
        j = plt.quiver(x_coords[x.Src_bus], y_coords[x.Src_bus], 
                x_coords[x.Rec_bus] - x_coords[x.Src_bus], y_coords[x.Rec_bus] - y_coords[x.Src_bus],
                angles='xy', scale_units='xy', scale=1, color='teal')
        
    for x in output:
        src_bus, rec_bus = graph.int_bus[x[0]], graph.int_bus[x[1]]
        k = plt.quiver(src_bus.x_coord, src_bus.y_coord, 
                rec_bus.x_coord - src_bus.x_coord, rec_bus.y_coord - src_bus.y_coord,
                angles='xy', scale_units='xy', scale=1, color='orchid')

    plt.title('Example Power Distribution System')

    plt.legend([i, j, k], ['Bus', 'Branch', 'Switch'])
    plt.show()
        
if __name__ == "__main__":
    filename = 'power_systems_radial/bus_29_1.pos'
    F = read_pos_file(filename)
    g = Graph(F)
    print(g.get_downstream_load(0))
    #plot_graph(g)