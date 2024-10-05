from util import Graph
import networkx as nx
import matplotlib.pyplot as plt
from generate import generate_graph
from mip import run_mip
from reader import read_pos_file
from benders import run_benders
import numpy as np

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

    for p in p_values:
        val, _ = run_mip(G, p, verbal=False)
        vals.append(val)

    plt.plot(p_values, vals)
    plt.show()

if __name__ == "__main__":
    # G = generate_graph(300, 2, 0.1, 0.15, 300, 150, 4)

    # mip had trouble
    file_number = 6
    P = 0.6

    # file_number = 6
    # P = 0.2
    filename = f'networks/R{file_number}.switch'
    F = read_pos_file(filename)
    G = Graph(F)

    val1, solution1 = run_benders(G, P, verbal = True)
    # val2, solution2 = run_mip(G, P, verbal=True)

    # assert round(val1, 5) == round(val2, 5)

    # try:
    #     assert solution1 == solution2
    # except:
    #     for s in solution1:
    #         print(solution1[s], solution2[s])
    construct_output_graph(G, solution1)

