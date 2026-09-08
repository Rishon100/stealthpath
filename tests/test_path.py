import networkx as nx

from src.planners.base import Path


def test_path_stores_nodes_and_edges():
    graph = nx.MultiDiGraph()

    graph.add_node("A")
    graph.add_node("B")

    graph.add_edge(
        "A",
        "B",
        relationship="MemberOf"
    )

    path = Path(
        nodes=("A", "B"),
        edges=(0,),
        cost=1.0,
        planner="shortest_path",
    )

    assert path.nodes == ("A", "B")
    assert path.edges == (0,)
    assert path.length == 1


def test_path_validation():
    graph = nx.MultiDiGraph()

    graph.add_edge(
        "A",
        "B",
        relationship="MemberOf"
    )

    path = Path(
        nodes=("A", "B"),
        edges=(0,),
        cost=1.0,
    )

    path.validate(graph)