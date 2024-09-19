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

    def get_downstream_load(self, index : int) -> float:
        """
        Calculates load of descendant nodes from node\n
        index : origin to calculate from
        """
        nodes = self.successors_dict[index] | {index}
        return sum(self.index_node[i].power for i in nodes if i not in self.substations)
    
    def get_eps_lower_bound(self) -> float:
        """
        Calculates EPS lower bound
        """
        return sum(self.get_downstream_load(i) * self.theta[i] for i in self.G.nodes if i not in self.substations)
    
    def get_eps_upper_bound(self) -> float:
        """
        Calculates EPS upper bound
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

if __name__ == "__main__":
    filename = 'networks/R7.switch'
    F = read_pos_file(filename)
    G = Graph(F)

    print(G.get_downstream_load(0), G.get_eps_lower_bound(), G.get_eps_upper_bound())