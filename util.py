from reader import *
from copy import deepcopy
import matplotlib.pyplot as plt
import networkx as nx
import itertools

class Graph:
    def __init__(self, info : Info) -> None:
        self.info = info
        
        # Maps node num to bus object
        self.index_node:dict[int, Node] = {x.index : x for x in self.info.nodes}
        vertices = [node.index for node in info.nodes]
        edges = [(edge.node1, edge.node2) for edge in info.edges + info.ties]

        self.G = nx.DiGraph()
        self.G.add_nodes_from(vertices)
        self.G.add_edges_from(edges)

        self.successors_dict = {index : nx.descendants(self.G, index) for index in vertices}
        if (self.successors_dict[1] | {1} != set(vertices)):
            print('Graph is not fully connected from origin.')
        else:
            print('Graph is fully connected from origin.')

        for index in self.successors_dict:
            if (self.successors_dict[index] | {index} == set(vertices)):
                print('Does exist some point acting as origin.')
        
        # t = [(index, len(self.successors_dict[index])) for index in self.successors_dict.keys()]
        # t = sorted(t, key = lambda x : x[1], reverse=True)
        # print(t[0])

        # for node in self.successors_dict.keys():
        #     if node not in self.successors_dict[t[0][0]]:
        #         print(node)

    def get_downstream_load(self, index : int) -> float:
        return sum([self.index_node[child].power for child in self.successors_dict[index]])

    def plot_graph(self) -> None:
        G = self.G
        
        #pos = nx.spring_layout(G, seed=0, k=0.1)
        pos = nx.circular_layout(G)
        # pos = nx.kamada_kawai_layout(G)

        components = list(nx.weakly_connected_components(G))
        colors = itertools.cycle(['lightblue', 'lightgreen', 'red', 'purple', 'orange'])
        color_map = {}
        for component, color in zip(components, colors):
            for node in component:
                color_map[node] = color
        node_colors = [color_map[node] for node in G.nodes()]
        # print(nx.is_weakly_connected(G))

        plt.figure(figsize=(8, 6))
        nx.draw(G, pos, with_labels=True, 
                node_size=10, node_color=node_colors, 
                font_size=5, font_color="black", 
                edge_color="gray", linewidths=1.5)
        plt.show()
        
if __name__ == "__main__":
    filename = 'networks/R4.switch'
    F = read_pos_file(filename)
    g = Graph(F)

    # correct for R3, R6
    # incorrect for R4, R5, R7
    print(g.get_downstream_load(1))
    g.plot_graph()