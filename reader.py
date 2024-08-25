from dataclasses import dataclass

@dataclass
class Branch:
    num : int
    Src_bus : int
    Rec_bus : int
    R : float
    X : float
    PL_kw : float
    QL_kvar : float
    S_NS : str

@dataclass(frozen=True)
class Bus:
    num : int
    x_coord : int
    y_coord : int
    
@dataclass
class Info:
    PU : int
    V_base : float
    S_base : int
    Branch_count : int
    Sectionalizing_count : int
    Tie_count : int
    Nodes : int
    Feeders : int
    Feeder_node_ids : list[int]
    Branches : list[Branch]
    Tie_switches : list[Branch]
    Buses : list[Bus]
    Arcs : list[Branch]

def read_branch_line(branch_line:str) -> Branch:
    try:
        num, Src_bus, Rec_bus, R, X, PL_kw, QL_kvar, S_NS =\
            branch_line.strip().split()
    except:
        print(branch_line.strip().split())
        quit()
    
    return Branch(
        int(num),
        int(Src_bus),
        int(Rec_bus),
        float(R),
        float(X),
        float(PL_kw),
        float(QL_kvar),
        S_NS
    )

def read_switch_line(switch_line:str) -> Branch:
    num, Src_bus, Rec_bus, R, X = switch_line.strip().split()
    
    return Branch(
        int(num),
        int(Src_bus),
        int(Rec_bus),
        float(R),
        float(X),
        None,
        None,
        None
    )
    
def read_bus_line(node_line:str) -> Bus:
    num, x_coord, y_coord = node_line.strip().split()
    
    return Bus(
        int(num),
        int(x_coord),
        int(y_coord)
    )
    
def read_pos_file(filename:str) -> Info:
    with open(filename, 'r') as file:
        lines = file.readlines()
        
    # header
    Pu = int(lines[0].split()[1])
    V_base = float(lines[1].split()[1])
    S_base = float(lines[2].split()[1])
    Branch_count = int(lines[3].split()[1])
    Sectionalizing_count = int(lines[4].split()[1])
    Tie_count = int(lines[5].split()[1])
    Nodes = int(lines[6].split()[1])
    Feeders = int(lines[7].split()[1])
    Feeder_node_ids = [int(i) for i in lines[8].split()[1:]]
    
    k = 10
    Branches = []
    while not lines[k].startswith('.'):
        Branches.append(read_branch_line(lines[k]))
        k += 1
        
    k += 1
    Switches = []
    while not lines[k].startswith('.'):
        Switches.append(read_switch_line(lines[k]))
        k += 1
        
    k += 2
    Buses = []
    while not lines[k].startswith('.'):
        Buses.append(read_bus_line(lines[k]))
        k += 1
        if k >= len(lines):
            break
    return Info(
        PU = Pu,
        V_base = V_base,
        S_base = S_base,
        Branch_count = Branch_count,
        Sectionalizing_count = Sectionalizing_count,
        Tie_count = Tie_count,
        Nodes = Nodes,
        Feeders = Feeders,
        Feeder_node_ids = Feeder_node_ids,
        Branches = Branches,
        Tie_switches = Switches,
        Buses = Buses,
        Arcs = Branches + Switches
    )
