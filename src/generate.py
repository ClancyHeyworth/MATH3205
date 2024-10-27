from util import Graph
import numpy as np
from reader import Node, Edge, Info
from tqdm import tqdm

def generate_similar_graph(G : Graph, nodes_factor : int = 1) -> Graph:
    np.random.seed(0)

    n_substations = len(G.substations)
    n_nodes = nodes_factor * len(G.index_node) - 1
    node_split = np.random.multinomial(n_nodes, np.ones(n_substations) / n_substations)
    
    children = [len(G.outgoing[j]) for j in G.V if j != 0]
    np.random.shuffle(children)

    substations = [G.index_node[i] for i in G.substations]
    sample = [n for n in G.index_node.values() if n.clients > 0 and n.theta > 0]
    np.random.shuffle(sample)

    nodes = []
    edges = []

    total_placed = 1
    c = 0
    for i in tqdm(range(1, n_substations + 1)):
        leaf_nodes : set[Node] = set()

        # make substation
        substation = substations[i - 1]
        substation = Node(total_placed, substation.index, substation.power, substation.clients)

        leaf_nodes.add(substation)
        nodes.append(substation)
        total_placed += 1
        nodes_placed = 1
        while nodes_placed < node_split[i - 1]:
            current = np.random.choice(tuple(leaf_nodes))

            num_children = children[c % len(children)]
            c += 1
            if num_children == 0:
                continue
            leaf_nodes.remove(current)
            
            if nodes_placed + num_children > node_split[i - 1]:
                num_children = node_split[i - 1] - nodes_placed

            for _ in range(num_children):
                node_index = total_placed
                nodes_placed += 1
                total_placed += 1
                
                new_node = sample[c % len(sample)]
                new_node = Node(node_index, new_node.theta, new_node.power, new_node.clients)

                leaf_nodes.add(new_node)
                nodes.append(new_node)
                edges.append(Edge(current.index, node_index))

    G = Graph(Info(nodes_placed, len(edges), 0, nodes, edges, [], []))
    return G