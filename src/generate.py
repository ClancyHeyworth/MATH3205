from util import Graph
import numpy as np
from reader import Node, Edge, Info
from tqdm import tqdm

def generate_graph(n_nodes : int, n_substations : int, 
        theta_mean : float, theta_sigma : float, 
        load_mean : float, load_sigma : float,
        mean_children : float) -> Graph:
    assert n_nodes >= n_substations
    assert all([i > 0 for i in [theta_mean, theta_sigma, load_mean, load_sigma, mean_children]])

    # Number of nodes to assign to each substation
    node_split = np.random.multinomial(n_nodes, np.ones(n_substations) / n_substations)

    nodes = []
    edges = []

    total_placed = 1
    for i in tqdm(range(1, n_substations + 1)):
        leaf_nodes : set[Node] = set()

        # make substation
        substation = Node(total_placed, 0, np.random.normal(load_mean, load_sigma), -1)
        leaf_nodes.add(substation)
        nodes.append(substation)
        total_placed += 1
        nodes_placed = 1
        while nodes_placed < node_split[i - 1]:
            current = np.random.choice(tuple(leaf_nodes))
            leaf_nodes.remove(current)

            if len(leaf_nodes) == 0:
                num_children = mean_children
            else:
                num_children = min(np.random.poisson(lam = mean_children), node_split[i - 1] - nodes_placed)

            for _ in range(num_children):
                node_index = total_placed
                nodes_placed += 1
                total_placed += 1
                new_node = Node(node_index, 
                    abs(np.random.normal(theta_mean, theta_sigma)),
                    abs(np.random.normal(load_mean, load_sigma)),
                    0)
                leaf_nodes.add(new_node)
                nodes.append(new_node)
                edges.append(Edge(current.index, node_index))
    
    # counts = {e : 0 for e in range(1, n_nodes + 1)}
    # for e in edges:
    #     counts[e.node1] += 1
    # print(np.mean([counts[e] for e in counts if counts[e] != 0]))
    G = Graph(Info(nodes_placed, len(edges), 0, nodes, edges, [], []))
    return G


if __name__ == "__main__":
    # G = generate_graph(300, 4, 0.1, 0.15, 300, 150, 5)
    G = generate_graph(300, 2, 0.1, 0.15, 300, 150, 4)

    print(G.get_downstream_load(0), G.get_ens_lower_bound(), G.get_ens_upper_bound())

    G.plot_graph()

    from benders import run_benders

    run_benders(G, 0.9, verbal=True)