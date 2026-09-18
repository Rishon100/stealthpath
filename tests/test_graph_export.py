import json

import networkx as nx

from src.graph.export_graph import export_graph


def test_export_graph(tmp_path):

    graph = nx.MultiDiGraph()

    graph.add_node(
        "user1",
        name="USER1",
        object_type="users",
    )

    graph.add_node(
        "group1",
        name="GROUP1",
        object_type="groups",
    )

    graph.add_edge(
        "user1",
        "group1",
        relationship="MemberOf",
        source_name="USER1",
        target_name="GROUP1",
    )

    output_path = tmp_path / "graph.json"

    export_graph(
        graph,
        output_path,
    )

    assert output_path.exists()

    with open(
        output_path,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    assert data["format"] == "StealthPath Graph"
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1

    assert data["edges"][0]["relationship"] == "MemberOf"