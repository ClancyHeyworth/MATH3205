from util import Graph
import numpy as np
from reader import Node, Edge, Info
from tqdm import tqdm
from random import random

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
        theta_proportion : float,
        load_mean : float, 
        load_sigma : float,
        load_proportion : float,
        mean_children : float, 
        branch_proportion:float) -> Graph:
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

            if random() < branch_proportion:
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
                if random() < theta_proportion:
                    # theta = max(0, np.random.normal(theta_mean, theta_sigma))
                    theta = np.random.exponential(theta_mean)
                if random() < load_proportion:
                    # load = max(0, np.random.normal(load_mean, load_sigma))
                    load = np.random.exponential(load_mean)
                
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

    load_mean = np.mean([v.power for v in G.index_node.values() if v.power > 0])
    load_sigma = np.std([v.power for v in G.index_node.values() if v.power != 0])
    load_proportion = np.mean([1 if v.power > 0 else 0 for v in G.index_node.values()])
    
    theta_mean = np.mean([v.theta for v in G.index_node.values() if v.theta > 0])
    theta_sigma = np.std([v.theta for v in G.index_node.values() if v.theta > 0])
    theta_proportion = np.mean([1 if v.theta > 0 else 0 for v in G.index_node.values()])

    n_nodes = nodes_factor * len(G.index_node) - 1
    n_substations = len(G.substations)
    G = generate_graph2(n_nodes, n_substations, theta_mean, theta_sigma, theta_proportion, load_mean, load_sigma, load_proportion, mean_children, branch_proportion)
    return G

if __name__ == "__main__":
    from benders import run_benders
    from mip import run_mip
    from params import ModelOutput, ModelParams

    params = ModelParams(6, 0.6, verbal=True)

    run_mip(params)