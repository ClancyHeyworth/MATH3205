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
    np.random.seed(0)
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
                num_children = int(mean_children) + 1
            else:
                num_children = np.random.poisson(lam = mean_children)
                if nodes_placed + num_children > node_split[i - 1]:
                    num_children = node_split[i - 1] - nodes_placed
                # num_children = min(, node_split[i - 1] - nodes_placed)
            for _ in range(num_children):
                node_index = total_placed
                nodes_placed += 1
                total_placed += 1
                new_node = Node(node_index, 
                    abs(np.random.normal(theta_mean, theta_sigma)),
                    abs(np.random.normal(load_mean, load_sigma)),
                    20)
                leaf_nodes.add(new_node)
                nodes.append(new_node)
                edges.append(Edge(current.index, node_index))

    G = Graph(Info(nodes_placed, len(edges), 0, nodes, edges, [], []))
    return G

def generate_graph2(n_nodes : int, n_substations : int, 
        theta_mean : float, 
        theta_sigma : float, 
        load_mean : float, 
        load_sigma : float,
        substation_load_mean : float,
        substation_load_sigma : float,
        mean_children : float, 
        branch_proportion:float) -> Graph:
    assert n_nodes >= n_substations
    assert all([i > 0 for i in [theta_mean, theta_sigma, load_mean, load_sigma, mean_children]])
    np.random.seed(0)
    # Number of nodes to assign to each substation
    node_split = np.random.multinomial(n_nodes, np.ones(n_substations) / n_substations)

    theta_shape = (theta_mean**2)/(theta_sigma**2)
    theta_scale = (theta_sigma**2) / theta_mean

    load_shape = (load_mean**2)/(load_sigma**2)
    load_scale = (load_sigma**2) / load_mean

    substation_load_shape = (substation_load_mean**2)/(substation_load_sigma**2)
    substation_load_scale = (substation_load_sigma**2) / substation_load_mean

    nodes = []
    edges = []

    total_placed = 1
    for i in tqdm(range(1, n_substations + 1)):
        leaf_nodes : set[Node] = set()

        # make substation
        substation = Node(total_placed, 0, np.random.gamma(substation_load_shape, substation_load_scale), -1)
        leaf_nodes.add(substation)
        nodes.append(substation)
        total_placed += 1
        nodes_placed = 1
        while nodes_placed < node_split[i - 1]:
            current = np.random.choice(tuple(leaf_nodes))
            leaf_nodes.remove(current)

            if np.random.random() < branch_proportion:
                num_children = max(1, np.random.poisson(lam=mean_children))
            else:
                num_children = 1
            
            if nodes_placed + num_children > node_split[i - 1]:
                num_children = node_split[i - 1] - nodes_placed

            for _ in range(num_children):
                node_index = total_placed
                nodes_placed += 1
                total_placed += 1

                theta = 0
                load = 0
                theta = np.random.gamma(theta_shape, theta_scale)
                load = np.random.gamma(load_shape, load_scale)
                
                new_node = Node(node_index, 
                    theta,
                    load,
                    np.random.poisson(30))
                leaf_nodes.add(new_node)
                nodes.append(new_node)
                edges.append(Edge(current.index, node_index))

    G = Graph(Info(nodes_placed, len(edges), 0, nodes, edges, [], []))
    return G

def generate_similar_graph(G : Graph, nodes_factor : int = 1) -> Graph:

    branch_proportion = np.mean([1 if len(G.outgoing[v]) > 1 else 0 for v in G.V])
    mean_children = np.mean([len(G.outgoing[j]) for j in G.V if len(G.outgoing[j]) > 1])

    load_data = [v.power for v in G.index_node.values() if v.power > 0 and v.clients > 0]
    load_mean = np.mean(load_data)
    load_sigma = np.std(load_data)
    
    theta_data = [v.theta for v in G.index_node.values() if v.theta > 0 and v.clients > 0]
    theta_mean = np.mean(theta_data)
    theta_sigma = np.std(theta_data)

    substation_load_data = [v.power for v in G.index_node.values() if v.power > 0 and v.clients < 0]
    substation_load_mean = np.mean(substation_load_data)
    substation_load_std = np.mean(substation_load_data)

    n_nodes = nodes_factor * len(G.index_node) - 1
    n_substations = len(G.substations)
    G = generate_graph2(n_nodes, n_substations, 
                        theta_mean, theta_sigma, 
                        load_mean, load_sigma, 
                        substation_load_mean, substation_load_std,
                        mean_children, branch_proportion)
    return G