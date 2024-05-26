"""
author: [Mohamadreza Hooshmandzadeh]
studentnumber: [2366713]
"""
import pandas as pd
import os
import json
import networkx as nx
import matplotlib.pyplot as plt
import sys


def read_csv(name):
    """"read a file and convert it to a pd dataframe"""
    current_path = os.getcwd()
    files = os.listdir(current_path)
    for file in files:
        file_name = file.rsplit('.', 1)[0]
        if file.endswith(".csv") and file == name:
            raw_df = pd.read_csv(os.path.join(current_path, file), header=None)
            header = ["SegmentNr", "Position", "A", "C", "G", "T"]
            raw_df.columns = header
            raw_df = raw_df.reset_index(drop=True)
            k = file.rsplit('.', 1)[0][-1]
            k = int(k)
            return raw_df, k, file_name
    else:
        raise LookupError("This file is not existing")


def clean_data(data_frame):
    # cleaning step1: ( number of positions are less than max of the position)
    # redundant data with similar data
    data_frame = data_frame.drop_duplicates()
    
    cl1 = data_frame.groupby("SegmentNr").agg({"Position" : ["max", "nunique"]})
    cl1 = cl1.reset_index()
    error_data = cl1[cl1["Position"]["max"] > cl1["Position"]["nunique"]]["SegmentNr"]
    to_del = data_frame[data_frame["SegmentNr"].isin(error_data)].index
    data_frame = data_frame.drop(to_del)

    # cleaning step2:

    cl2 = data_frame.groupby(["SegmentNr", "Position"]).agg({"A": ["count", "max", "min"],\
            "C": ["max", "min"], "G": ["max", "min"],\
                    "T": ["max", "min"]}).reset_index()
    cl2.columns = [''.join(col).strip() for col in cl2.columns.values]

    # redundant data
    cl2 = cl2[cl2["Acount"] > 1]

    # redundant data with different values
    cl_diff = cl2[((cl2["Amax"] != cl2["Amin"]) | 
            (cl2["Cmax"] != cl2["Cmin"]) | 
            (cl2["Gmax"] != cl2["Gmin"]) | 
            (cl2["Tmax"] != cl2["Tmin"]))]
    to_del = data_frame[data_frame["SegmentNr"].isin(cl_diff["SegmentNr"])].index
    data_frame = data_frame.drop(to_del)

    # cleaning step 3:
    cl3 = data_frame.query("(A + C + G + T) != 1")
    to_del = data_frame[data_frame["SegmentNr"].isin(cl3["SegmentNr"])].index
    data_frame = data_frame.drop(to_del)

    # cleaning step 4:
    cl4 = data_frame.copy()
    cl4["Id"] = cl4[["Position", "A", "C", "G", "T"]].astype(str).agg(''.join, axis = 1)
    cl4 = cl4.groupby("SegmentNr").agg({"Id": lambda x: '\\'.join(x)}).reset_index()
    dups = cl4[cl4.duplicated("Id")]
    to_del =data_frame[data_frame["SegmentNr"].isin(dups["SegmentNr"])].index
    data_frame = data_frame.drop(to_del)
    data_frame = data_frame.reset_index(drop=True)
    return data_frame    
    

def generate_sequences(df):
    """Generates json object for segmemnts by their sequence of nucleotides"""
    df["segment"] = df[['A', 'C', 'G', 'T']].idxmax(axis=1)
    df = df.sort_values(['SegmentNr', 'Position'])
    segment = df.groupby("SegmentNr").agg({"segment": lambda x: ''.join(x)}).reset_index()
    seg_json = segment.to_json(orient='records')
    seg_json = json.loads(seg_json)
    return seg_json


def construct_graph(df, k):
    """create a De Bruijn graph from json object"""
    G = nx.MultiDiGraph()
    for i in df:
        seg = i['segment']
        steps = len(seg) - k
        k_mers = []
        for i in range(steps + 1):
            k_mers.append(seg[i:i+k])

        for i in k_mers:
            l_seg = i[:k-1]
            r_seg = i[1:k+1]
            G.add_edge(l_seg, r_seg)
    return G


def orthogonal_layout(G):
    """helper function to create an nice layout
    for the main graph function"""
    pos = {}
    nodes = list(G.nodes)
    graph_size = int(len(nodes)**0.5) + (len(nodes) % int(len(nodes)**0.5) != 0)

    for i, node in enumerate(nodes):
        row = i // graph_size
        col = i % graph_size
        pos[node] = (col, row)
    return pos


def plot_graph(G, filename):
    """create a visualized graph and save it as a png file"""
    fig = plt.figure()
    pos = orthogonal_layout(G)
    
    nx.draw_networkx_nodes(G, pos, node_size=500, node_color='lightgreen')
    nx.draw_networkx_labels(G, pos, font_size=6, font_color='black', font_weight='bold')
    
    # for separating edges from each other
    for (u, v, key) in G.edges(keys=True):
        num_edges = G.number_of_edges(u, v)
        index = list(G[u][v]).index(key)
        placeholder = (index - num_edges / 2) * 0.2
        rad = 0.2 + placeholder
        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], connectionstyle=f'arc3,rad={rad}')

    plt.savefig(filename, format='png')
    plt.close(fig)


def is_connect(graph):
    visited = set()
    stack = []
    v = list(graph.nodes)[0]
    stack.append(v)
    while stack:
        v = stack.pop()
        if v not in visited:
            visited.add(v)
            neighbours = list(graph[v])
            neighbours.reverse()
            for w in neighbours:
                stack.append(w)
    if len(visited) < len(graph):
        return False            
    else:
        return True


def is_valid_graph(graph):    
    # check if graph is connected
    if not is_connect(graph):
        return False
    else:
        # check if number of nodes with diffent number of in and out degrees are 0 or 2
        # also check if there are 2 nodes in above list they sould be start and end points
        different_in_out = []
        for node in graph.nodes():
            if graph.out_degree(node) != graph.in_degree(node):
                different_in_out.append(graph.out_degree(node) - graph.in_degree(node))
        if len(different_in_out) not in [0,2]:
            return False
        elif len(different_in_out) == 2 and (different_in_out[0]\
            + different_in_out[1] != 0 or different_in_out[0]*different_in_out[1] != -1):
            return False                
        return True


def Eulerian_path_gen(graph):
    start_node =''
    for node in graph.nodes():
        if graph.out_degree(node) - graph.in_degree(node) == 1:
            start_node = node
            break
    if not start_node:
        for node in graph.nodes():
            if graph.out_degree(node) > 0:
                start_node = node
                break
    
    G = graph.copy()
    stack = []
    path = []
    v = start_node
    stack.append(v)
    out_edges = dict(G.out_degree())
    while stack:
        v = stack[-1]
        if out_edges[v] == 0:
            if len(stack) > 1:
                u = stack[-2]
                path.insert(0,(u,v))
            stack.pop()
        else:
            # sort the edges based on name of the destination node
            edges = sorted(G.edges(v, keys=True), key=lambda x: x[1])
            for _, w, key in edges:
                stack.append(w)
                out_edges[v] -= 1
                G.remove_edge(v, w, key=key)
                break
    return list(path)


def construct_dna_sequence(graph):
    path = Eulerian_path_gen(graph)
    DNA = path[0][0]
    for i in path:
        DNA += i[1][-1]
    print(path)
    return DNA


def save_output(s, filename):
    file = filename + ".txt"
    with open(file, 'w') as f:
        f.write(s)

def main():
    if len(sys.argv) != 2:
        print("Please provide correct command includng file name!")
        return
    name = sys.argv[1]
    try:    
        df, k, filename = read_csv(name)
        df = clean_data(df)
        df = generate_sequences(df)
        my_graph = construct_graph(df, k) 
        plot_graph(my_graph, filename)
        if is_valid_graph(my_graph):
            output_dna = construct_dna_sequence(my_graph)
            save_output(output_dna, filename)
        else:
            message = "The DNA sequence can not be constructed!"
            save_output(message, filename)
    except Exception as e:
        print(e)
if __name__ == "__main__":
    main()
