from project import clean_data, generate_sequences, is_valid_graph, construct_dna_sequence, construct_graph
from pytest import mark
import pandas as pd
import networkx as nx

@mark.parametrize(
    'dna_df, expected',
    [
        (
                pd.DataFrame(data=[
                    [1, 1, 1, 0, 0, 1],
                    [1, 2, 0, 0, 0, 1],
                    [2, 1, 1, 0, 0, 0],
                    [2, 2, 0, 1, 0, 0]],
                    columns=['SegmentNr', 'Position', 'A', 'C', 'G', 'T']),
                pd.DataFrame(data=[
                    [2, 1, 1, 0, 0, 0],
                    [2, 2, 0, 1, 0, 0]],
                    columns=['SegmentNr', 'Position', 'A', 'C', 'G', 'T'])
        ),
        (
                pd.DataFrame(data=[
                    [1, 1, 0, 0, 0, 1],
                    [1, 2, 0, 0, 0, 1],
                    [2, 1, 1, 0, 0, 0],
                    [2, 2, 0, 1, 0, 0],
                    [3, 1, 1, 0, 0, 0],
                    [3, 2, 0, 1, 0, 0]],
                    columns=['SegmentNr', 'Position', 'A', 'C', 'G', 'T']),
                pd.DataFrame(data=[
                    [1, 1, 0, 0, 0, 1],
                    [1, 2, 0, 0, 0, 1],
                    [2, 1, 1, 0, 0, 0],
                    [2, 2, 0, 1, 0, 0]],
                    columns=['SegmentNr', 'Position', 'A', 'C', 'G', 'T'])
        ),
        (
                pd.DataFrame(data=[
                    [1, 1, 0, 0, 0, 1],
                    [1, 2, 0, 0, 0, 1],
                    [2, 1, 1, 0, 0, 0],
                    [2, 2, 0, 1, 0, 0],
                    [3, 1, 1, 0, 0, 0],
                    [3, 2, 0, 1, 0, 0],
                    [2, 2, 0, 1, 0, 0]],
                    columns=['SegmentNr', 'Position', 'A', 'C', 'G', 'T']),
                pd.DataFrame(data=[
                    [1, 1, 0, 0, 0, 1],
                    [1, 2, 0, 0, 0, 1],
                    [2, 1, 1, 0, 0, 0],
                    [2, 2, 0, 1, 0, 0]],
                    columns=['SegmentNr', 'Position', 'A', 'C', 'G', 'T'])
        )
    ],

)
def test_clean_data(dna_df: pd.DataFrame, expected: pd.DataFrame) -> None:
    assert clean_data(dna_df).equals(expected)


@mark.parametrize(
    'dna_df, expected_json_str',
    [
        (
            pd.DataFrame(data=[
                [1, 1, 1, 0, 0, 0],
                [1, 2, 0, 0, 0, 1],
                [2, 1, 1, 0, 0, 0],
                [2, 2, 0, 1, 0, 0]],
                columns=['SegmentNr', 'Position', 'A', 'C', 'G', 'T']),
            [{"SegmentNr":1,"segment":"AT"},{"SegmentNr":2,"segment":"AC"}]
        ),
        (
            pd.DataFrame(data=[
                [1, 1, 1, 0, 0, 0],
                [1, 2, 0, 1, 0, 0],
                [3, 1, 0, 0, 1, 0],
                [3, 2, 0, 0, 0, 1],
                [3, 3, 1, 0, 0, 0]],
                columns=['SegmentNr', 'Position', 'A', 'C', 'G', 'T']),
            [{"SegmentNr":1,"segment":"AC"},{"SegmentNr":3,"segment":"GTA"}]
        ),
        (
            pd.DataFrame(data=[
                [1, 1, 1, 0, 0, 0],
                [1, 2, 0, 0, 0, 1],
                [2, 1, 1, 0, 0, 0],
                [2, 2, 0, 1, 0, 0],
                [2, 2, 0, 0, 1, 0],
                [3, 2, 0, 1, 0, 0],
                [3, 1, 1, 0, 0, 0],
                [3, 3, 0, 0, 0, 1]],
                columns=['SegmentNr', 'Position', 'A', 'C', 'G', 'T']),
            [{"SegmentNr": 1, "segment": "AT"}, {"SegmentNr": 2, "segment": "ACG"}, {"SegmentNr": 3, "segment": "ACT"}]
        )
    ], )
def test_generate_sequences(dna_df: pd.DataFrame, expected_json_str: str) -> None:
    assert (generate_sequences(dna_df) == expected_json_str)


@mark.parametrize(
    'json_data, k,  expected_edge_list',
    [
        (
            [{'SegmentNr': 1, 'segment': 'ATTACTC'}],
            5,
            [('ATTA', 'TTAC'), ('TTAC', 'TACT'), ('TACT', 'ACTC')]
        ),
        (
            [{'SegmentNr': 1, 'segment': 'GGGT'},
             {'SegmentNr': 2, 'segment': 'TTGG'},
             {'SegmentNr': 3, 'segment': 'GTTT'}],
            3,
            [('GG', 'GG'), ('GG', 'GT'), ('GT', 'TT'), ('TT', 'TG'),
             ('TT', 'TT'), ('TG', 'GG')]
        ),
        (
            [{'SegmentNr': 1, 'segment': 'ATTACTCGCTA'}],
            5,
            [('ATTA', 'TTAC'), ('TTAC', 'TACT'), ('TACT', 'ACTC'),
             ('ACTC', 'CTCG'), ('CTCG', 'TCGC'), ('TCGC', 'CGCT'), 
             ('CGCT', 'GCTA')]
        )
    ])
def test_construct_graph(json_data: str, k: int, expected_edge_list: list) -> None:
    assert (list(construct_graph(json_data, k).edges(keys=False)) == expected_edge_list)

@mark.parametrize(
    'DNA_edge_list,  expected_validity',
    [
        (
                [('ATTA', 'TTAC'), ('TTAC', 'TACT'), ('TACT', 'ACTC'), ('ACTC', 'ATTA')],
                True
        ),
        (
            [('GG', 'GG'), ('GG', 'GT'), ('GT', 'TT'), ('TT', 'TG'),
             ('TT', 'TT'), ('TG', 'GG')],
            True
        ),
        (
            [('ATTA', 'TTAC'), ('TTAC', 'TACT'), ('TACT', 'ACTC'),
             ('ACTC', 'CTCG'), ('CTCG', 'TCGC'), ('TCGC', 'CGCT'), 
             ('CGCT', 'GCTA')],
            True
        ),
        (
            [('ATTA', 'TTAC'), ('TTAC', 'TACT'), ('TACT', 'ACTC'),
             ('ACTC', 'CTCG'), ('CTCG', 'TCGC'), ('TCGC', 'CGCT'), 
             ('CGCT', 'GCTA'), ('TCGC', 'GCTA')],
            False
        )
        
    ])
def test_is_valid_graph(DNA_edge_list: list, expected_validity: bool) -> None:
    debruijn_graph = nx.MultiDiGraph()
    for edge in DNA_edge_list:
        debruijn_graph.add_edge(edge[0], edge[1])

    assert is_valid_graph(debruijn_graph) is expected_validity


@mark.parametrize(
    'DNA_edge_list,  possible_dna_sequence',
    [
        (
                [('AAA', 'AAC'), ('AAC', 'ACA'), ('ACA', 'CAC')],
                ["AAACAC"]
        ),
        (
            [('ATTA', 'TTAC'), ('TTAC', 'TACT'), ('TACT', 'ACTC'),
             ('ACTC', 'CTCG'), ('CTCG', 'TCGC'), ('TCGC', 'CGCT'), 
             ('CGCT', 'GCTA')],
            ['ATTACTCGCTA']
        ),
        (
            [('GG', 'GG'), ('GG', 'GT'), ('GT', 'TT')
             , ('TT', 'TT'), ('TT', 'TG'), ('TG', 'GG')],
            ["GGGTTTGG"]
        )
    ])
def test_construct_dna_sequence(DNA_edge_list: list, possible_dna_sequence) -> None:
    debruijn_graph = nx.MultiDiGraph()
    for edge in DNA_edge_list:
        debruijn_graph.add_edge(edge[0], edge[1])

    assert construct_dna_sequence(debruijn_graph) in possible_dna_sequence