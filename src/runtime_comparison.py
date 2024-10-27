from benders import run_benders
from mip import run_mip
from tqdm import tqdm
from util import Graph, load_graph_object
import numpy as np
import pandas
from params import ModelParams, ModelOutput

def output_runtimes(file_number, presolve:bool=True) -> None:
    dict_df = {
        'P' : [],
        'benders' : [],
        'mip' : [],
        'benders_obj' : [],
        'mip_obj' : []
    }
    params = ModelParams(file_number, 0, do_presolve=presolve)

    for p in tqdm(np.arange(0.2, 1.0, 0.2)):
        params.P = p
        benders_output = run_benders(params)
        mip_output = run_mip(params)

        dict_df['benders'].append(benders_output.time)
        dict_df['mip'].append(mip_output.time)
        dict_df['P'].append(round(p, 1))
        dict_df['benders_obj'].append(benders_output.obj)
        dict_df['mip_obj'].append(mip_output.obj)
    
    print(dict_df)
    df = pandas.DataFrame(dict_df)
    df.to_csv(f'outputs/{file_number}.csv', index=False)

def output_runtimes2(params:ModelParams) -> None:
    dict_df = {
        'P' : [],
        'benders' : [],
        'mip' : [],
        'benders_obj' : [],
        'mip_obj' : [],
        "mip_gap" : [],
        'benders_gap' : []
    }

    for p in tqdm(np.arange(0.2, 1.0, 0.2)):
        params.P = p
        params.verbal = True
        benders_output = run_benders(params)
        quit()
        params.verbal = True
        mip_output = run_mip(params)

        dict_df['benders'].append(benders_output.time)
        dict_df['mip'].append(mip_output.time)
        dict_df['P'].append(round(p, 1))
        dict_df['benders_obj'].append(benders_output.obj)
        dict_df['mip_obj'].append(mip_output.obj)
        dict_df['benders_gap'].append(benders_output.gap)
        dict_df['mip_gap'].append(mip_output.gap)
    
    print(dict_df)
    df = pandas.DataFrame(dict_df)
    df.to_csv(f'outputs/gen{params.file_number}.csv', index=False)

if __name__ == "__main__":
    params = ModelParams(4, 0.2, nodes_factor=10, make_similar_graph=True, verbal=True)
    run_mip(params)
    # output_runtimes2(params)