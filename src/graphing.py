from util import Graph, load_graph_object
import networkx as nx
import matplotlib.pyplot as plt
from generate import generate_graph
from mip import run_mip
from reader import read_pos_file
from benders import run_benders
import numpy as np
import time
import pandas
from tqdm import tqdm

def construct_output_graph(G : Graph, solution : dict[tuple[int, int], int]) -> None:
    Gdash = nx.DiGraph()

    for edge in G.edges:
        colour = 'red' if solution[edge] == 1 else 'blue'
        Gdash.add_edge(*edge, color = colour)

    pos = nx.nx_agraph.graphviz_layout(Gdash)

    colours = [Gdash[i][j]['color'] for i,j in Gdash.edges]

    plt.figure(figsize=(8, 6))
    nx.draw(Gdash, pos, with_labels=True, edge_color = colours,
            node_size=10, 
            font_size=5, font_color="black", linewidths=1.5)
    plt.show()

def bang_for_your_buck(file_number):
    filename = f'networks/R{file_number}.switch'
    F = read_pos_file(filename)
    G = Graph(F)

    p_values = np.arange(0, 1 + 0.05, step = 0.05)
    vals = []

    for p in tqdm(p_values):
        val, _, _, _ = run_mip(G, p, verbal=False)
        vals.append(val)

    plt.plot(p_values, vals)
    plt.show()

def compare_performance(file_number):
    np.random.seed(0)
    # filename = f'networks/R{file_number}.switch'
    # F = read_pos_file(filename)
    # G = Graph(F)
    from util import GraphPickle
    G = load_graph_object(file_number)
    # print(G.index_node)
    # quit()

    from check_validity import generate_skinny_graph

    load_mean = np.mean([v.power for v in G.index_node.values() if v.power != 0])
    mean_children = np.mean([len(G.outgoing[j]) for j in G.V])
    load_sigma = np.std([v.power for v in G.index_node.values() if v.power != 0])
    theta_mean = np.mean([v.theta for v in G.index_node.values()])
    theta_sigma = np.std([v.theta for v in G.index_node.values()])
    n_nodes = 1 * len(G.index_node) - 1
    n_substations = len(G.substations)
    # G = generate_graph(n_nodes, n_substations, theta_mean, theta_sigma, load_mean, load_sigma, mean_children)
    # G.plot_graph()

    dict_df = {
        'P' : [],
        'benders' : [],
        'mip' : [],
        'benders_obj' : [],
        'mip_obj' : []
    }
    from benders2 import run_benders as run_benders2
    for p in tqdm(np.arange(0.2 , 1.0, 0.2)):
        t1 = time.time()
        benders_obj, benders_runtime, _, _ = run_benders2(G, p, time_limit=True, verbal=False)
        t2 = time.time()
        mip_obj, mip_runtime, _, _, _, = run_mip(G, p, time_limit=True, verbal=False)
        t3 = time.time()

        dict_df['benders'].append(benders_runtime)
        dict_df['mip'].append(mip_runtime)
        dict_df['P'].append(round(p, 1))
        dict_df['benders_obj'].append(benders_obj)
        dict_df['mip_obj'].append(mip_obj)

        print(p, benders_obj, mip_obj)
    df = pandas.DataFrame(dict_df)
    # df.to_csv(f'{file_number}.csv', index=False)
    # df.to_csv(f'dense.csv', index=False)
    print(df)

def sa_obj(file_number):
    from sa import run_sa, run_optimisation_fixed
    dict_df = {
        'P' : [],
        'Obj' : [],
        'Time' : []
    }

    G = load_graph_object(file_number)

    for p in tqdm(np.arange(0.2 , 1.0, 0.2)):
        t1 = time.time()
        _, solution = run_sa(G, P = p)
        t2 = time.time()
        obj = run_optimisation_fixed(G, p, solution, verbal=False)

        dict_df['P'].append(round(p, 1))
        dict_df['Obj'].append(obj)
        dict_df['Time'].append(t2 - t1)
    df = pandas.DataFrame(dict_df)
    df.to_csv(f'SA{file_number}.csv', index=False)
    print(dict_df)
    
def compare_performance2(file_number):
    filename = f'networks/R{file_number}.switch'
    F = read_pos_file(filename)
    G = Graph(F)

    dict_df = {
        'P' : [],
        'benders' : [],
        'mip' : []
    }

    for p in tqdm(np.arange(0.05, 1.0, 0.05)):
        t1 = time.time()
        # run_benders(G, p, time_limit=True)
        t2 = time.time()
        run_mip(G, p, time_limit=True)
        t3 = time.time()

        dict_df['benders'].append(t2 - t1)
        dict_df['mip'].append(t3 - t2)
        dict_df['P'].append(p)
    df = pandas.DataFrame(dict_df)
    df.to_csv(f'{file_number}.csv', index=False)
    print(df)

if __name__ == "__main__":
    # G = generate_graph(300, 2, 0.1, 0.15, 300, 150, 4)

    # mip had trouble
    file_number = 3

    # compare_performance(file_number)
    sa_obj(file_number)
