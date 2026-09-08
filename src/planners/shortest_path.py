import networkx as nx


def find_shortest_path(graph, source, target):
    """
    Find the shortest path between two nodes.

    The path minimizes the number of graph transitions.
    """

    return nx.shortest_path(
        graph,
        source=source,
        target=target,
    )