import networkx as nx

from .base import Path


def find_shortest_path(graph, source, target):
    """
    Find the shortest path between two nodes.

    The path minimizes the number of graph transitions.
    """

    nodes = nx.shortest_path(
        graph,
        source=source,
        target=target,
    )

    edges = []

    for current, next_node in zip(nodes, nodes[1:]):
        edge_data = graph.get_edge_data(current, next_node)

        edge_keys = sorted(
            edge_data,
            key=lambda key: edge_data[key].get("relationship", "")
        )

        edges.append(edge_keys[0])

    path = Path(
        nodes=tuple(nodes),
        edges=tuple(edges),
        cost=float(len(edges)),
        planner="shortest_path",
    )

    path.validate(graph)

    return path