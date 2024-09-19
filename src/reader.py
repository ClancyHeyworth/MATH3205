from dataclasses import dataclass

@dataclass(frozen=True)
class Node:
    """
    Stores information on each vertex on the graph.\\
    index : index number of node\\
    theta : duration of failure time\\
    power : load/power of node\\
    clients : number of clients, useful for reliability indices
    """
    index : int
    theta : float
    power : float
    clients : int

@dataclass(frozen=True)
class Edge:
    """
    Stores edge connection between two nodes.\\
    node1 : sending node\\
    node2 : receiving node
    """
    node1 : int
    node2 : int
    
@dataclass
class Info:
    """
    Stores information read from dataset file.\\
    node_num : number of nodes in problem\\
    edge_num : number of edges in problem\\
    ties_num : number of ties, can be ignored\\
    nodes : list of Node objects\\
    edges : list of Edge objects\\
    ties : list of Edge objects for ties, can be ignored\\
    all_edges : combined list of edge and ties
    """
    node_num : int
    edge_num : int
    ties_num : int
    nodes : list[Node]
    edges : list[Edge]
    ties : list[Edge]
    all_edges : list[Edge]
    
def read_pos_file(filename:str) -> Info:
    """
    Reads from .switch file into Info object.
    """
    with open(filename, 'r') as file:
        lines = file.readlines()
    
    nodes:list[Node] = []
    edges:list[Edge] = []
    ties:list[Edge] = []
    for line in lines:
        # line is first line
        if line.startswith('p'):
            _, _, node_num, edge_num, ties_num = line.split()
            node_num, edge_num, ties_num =\
                (int(x) for x in [node_num, edge_num, ties_num])
        # line is vertice line
        elif line.startswith('v'):
            _, index, _, theta, power, clients = line.split()
            
            nodes.append(
                Node(
                    index = int(index),
                    theta = float(theta),
                    power = float(power),
                    clients = int(clients)
                )
            )
        # line is edge line
        elif line.startswith('e'):
            _, node1, node2, _ = line.split()
            edges.append(
                Edge(
                    node1 = int(node1),
                    node2 = int(node2)
                )
            )
        # line is tie line
        elif line.startswith('t'):
            _, node1, node2, _ = line.split()
            ties.append(
                Edge(
                    node1 = int(node1),
                    node2 = int(node2)
                )
            )
    assert len(edges) == edge_num
    assert len(nodes) == node_num
    assert len(ties) == ties_num
    return Info(
        node_num = node_num,
        edge_num = edge_num,
        ties_num = ties_num,
        nodes = nodes,
        edges = edges,
        ties = ties,
        all_edges = ties + edges
    )