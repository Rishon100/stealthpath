import json
from pathlib import Path


def export_graph(graph, output_path):
    """
    Export a StealthPath NetworkX graph to JSON.

    The exported JSON contains:
        nodes
        edges

    This creates a standard graph representation that
    the dashboard can load independently of the
    original BloodHound JSON collection.
    """

    output_path = Path(output_path)

    nodes = []

    for node_id, data in graph.nodes(data=True):

        nodes.append({
            "id": str(node_id),
            "name": data.get(
                "name",
                str(node_id),
            ),
            "object_type": data.get(
                "object_type",
                "unknown",
            ),
        })

    edges = []

    for source, target, edge_key, data in graph.edges(
        keys=True,
        data=True,
    ):

        edges.append({
            "source": str(source),
            "target": str(target),
            "key": str(edge_key),
            "relationship": data.get(
                "relationship",
                "Unknown",
            ),
            "source_name": data.get(
                "source_name",
                str(source),
            ),
            "target_name": data.get(
                "target_name",
                str(target),
            ),
            "inherited": data.get(
                "inherited",
                False,
            ),
        })

    graph_data = {
        "format": "StealthPath Graph",
        "version": "1.0",
        "nodes": nodes,
        "edges": edges,
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            graph_data,
            file,
            indent=2,
        )