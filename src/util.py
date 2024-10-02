from reader import *
from copy import deepcopy
import matplotlib.pyplot as plt
import networkx as nx
import itertools

class Graph:
    """
    Object for retrieving processed data from dataset
    """
    def __init__(self, info : Info, verbal:bool=False) -> None:
        """
        info : Info object generated from a dataset \n
        verbal : prints whether origin node was added successfully
        """
        self.info = info
        
        # Maps node num to bus object
        self.index_node:dict[int, Node] = {x.index : x for x in self.info.nodes}

        vertices = [node.index for node in info.nodes]
        edges = [(edge.node1, edge.node2) for edge in info.edges]

        # Add an origin node and edges to each substation for convenience
        node0 = Node(0, 0, 0, 0)
        for index in vertices:
            if self.index_node[index].clients == -1:
                edges.append((0, index))
        self.index_node[0] = node0
        vertices.append(node0.index)
        self.vertices = vertices

        # make graph with networkx
        self.G = nx.DiGraph()
        self.G.add_nodes_from(vertices)
        self.G.add_edges_from(edges)

        self.substations = {i for i in self.index_node.keys() if self.index_node[i].clients == -1}

        # successors are nodes that can be reached from the given node
        self.successors_dict:dict[int, set] = {index : nx.descendants(self.G, index) for index in vertices}

        # maps index -> theta value
        self.theta = {x.index : x.theta for x in info.nodes}
        self.theta[0] = 0

        if verbal:
            if (self.successors_dict[0] | {0} != set(vertices)):
                print('Graph is not fully connected from origin.')
            else:
                print('Graph is fully connected from origin.')

        self.edges = edges
        self.V = {i for i in self.successors_dict}
        self.successor_arcs = {a : self.get_successor_arcs(a[1]) for a in self.edges}

        self._objectives = dict()
        self.outgoing = { # stores nodes that go out of j for incoming (i, j)
            j : [k for k in self.V if (j, k) in self.edges]
            for j in self.V
        }
        self.downstream_load = {i : self.get_downstream_load(i) for i in self.V}

    def get_downstream_load(self, index : int) -> float:
        """
        Calculates load of descendant nodes from node\n
        index : origin to calculate from
        """
        nodes = self.successors_dict[index] | {index}
        return sum(self.index_node[i].power for i in nodes if i not in self.substations)
    
    def get_downstream_theta(self, index : int) -> float:
        nodes = self.successors_dict[index] | {index}
        return sum(self.index_node[i].theta for i in nodes if i not in self.substations)
    
    def get_successor_arcs(self, index : int):
        successors = self.successors_dict[index] | {index}
        successors_arcs = set()
        for a in self.edges:
            if a[0] in successors and a[1] in successors:
                successors_arcs.add(a)
        return successors_arcs
    
    def get_eps_lower_bound(self) -> float:
        """
        Calculates ENS lower bound
        """
        return sum(self.get_downstream_load(i) * self.theta[i] for i in self.G.nodes if i not in self.substations)
    
    def get_ens_upper_bound(self) -> float:
        """
        Calculates ENS upper bound
        """
        return sum(
            self.get_downstream_load(substation) * sum(self.theta[i] for i in self.successors_dict[substation])
            for substation in self.substations
        )

    def plot_graph(self) -> None:
        """
        Plots graph
        """
        G = self.G
        
        # pos = nx.spring_layout(G, seed=0, k=0.1)
        pos = nx.circular_layout(G)
        # pos = nx.kamada_kawai_layout(G)

        components = list(nx.weakly_connected_components(G))
        colors = itertools.cycle(['lightblue', 'lightgreen', 'red', 'purple', 'orange'])
        color_map = {}
        for component, color in zip(components, colors):
            for node in component:
                color_map[node] = color
        node_colors = [color_map[node] for node in G.nodes()]

        plt.figure(figsize=(8, 6))
        nx.draw(G, pos, with_labels=True, 
                node_size=10, node_color=node_colors, 
                font_size=5, font_color="black", 
                edge_color="gray", linewidths=1.5)
        plt.show()

    def calculate_contribution(self, i, j, XV):
        """
        Returns the contribution of (i, j) to the objective function within the current
        solution.
        """
        if (i, j) not in self._objectives:
            if XV[i, j] == 1:
                self._objectives[i, j] = 0
            else:
                self._objectives[(i, j)] = (1 - XV[i, j]) * (self.theta[j] + sum(
                        self.calculate_contribution(j, k, XV) for k in self.outgoing[j])
                )
                
        return self._objectives[i, j]
    
    def calculate_V_s(self, subtree : set[tuple[int, int]], 
            XV : dict[tuple[int, int], int], reset : bool = True) -> float:
        """
        Returns contribution of subtree to objective function.\\
        subtree : set of arcs (i, j)\\
        XV : A dictionary mapping arcs (i, j) -> {0,1}, representing switch placement.
        """
        if reset:
            self._objectives = dict()
        return sum(
            (self.downstream_load[a[0]] - self.downstream_load[a[1]]) *\
            self.calculate_contribution(*a, XV) for a in subtree
        )

    def get_subtrees(self, XV : dict[tuple[int, int], int]) -> list[set[tuple[int, int]]]:
        """
        Returns a list of set of tuples representing arcs between switches.\\
        XV : A dictionary mapping arcs (i, j) -> {0,1}, representing switch placement.
        """
        blocked_off_trees = {a : self.successor_arcs[a] | {a} 
                            for a in XV if XV[a] == 1}
        explored = set()
        output = []

        for arc in XV:
            if XV[arc] == 1 or arc in explored:
                continue
            arc_tree = self.successor_arcs[arc] | {arc}
            for root in blocked_off_trees:
                if root in arc_tree:
                    arc_tree = arc_tree.difference(blocked_off_trees[root])
            explored |= arc_tree
            output.append(arc_tree)
        return output


if __name__ == "__main__":
    filename = 'networks/R7.switch'
    F = read_pos_file(filename)
    G = Graph(F)

    print(G.get_downstream_load(0), G.get_ens_lower_bound(), G.get_ens_upper_bound())
