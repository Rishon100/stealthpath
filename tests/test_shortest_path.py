from src.graph.bloodhound_graph import build_attack_graph
from src.planners.shortest_path import find_shortest_path


DATA_DIR = "data/ESSOS_20240410083816"


def get_node_by_name(graph, name):
    for node, data in graph.nodes(data=True):
        if data.get("name") == name:
            return node

    raise ValueError(f"Node not found: {name}")


def test_shortest_path_on_real_essos_graph():
    graph = build_attack_graph(DATA_DIR)

    source = get_node_by_name(
        graph,
        "VAGRANT@ESSOS.LOCAL"
    )

    target = get_node_by_name(
        graph,
        "DOMAIN ADMINS@ESSOS.LOCAL"
    )

    path = find_shortest_path(graph, source, target)

    assert path[0] == source
    assert path[-1] == target
    assert len(path) >= 2


def test_shortest_path_is_valid():
    graph = build_attack_graph(DATA_DIR)

    source = get_node_by_name(
        graph,
        "VAGRANT@ESSOS.LOCAL"
    )

    target = get_node_by_name(
        graph,
        "DOMAIN ADMINS@ESSOS.LOCAL"
    )

    path = find_shortest_path(graph, source, target)

    for current, next_node in zip(path, path[1:]):
        assert graph.has_edge(current, next_node)


def test_show_real_shortest_path():
    graph = build_attack_graph(DATA_DIR)

    source = get_node_by_name(
        graph,
        "VAGRANT@ESSOS.LOCAL"
    )

    target = get_node_by_name(
        graph,
        "DOMAIN ADMINS@ESSOS.LOCAL"
    )

    path = find_shortest_path(graph, source, target)

    print("\nReal ESSOS shortest path:")

    for current, next_node in zip(path, path[1:]):
        relationships = [
            data.get("relationship")
            for data in graph.get_edge_data(
                current,
                next_node
            ).values()
        ]

        print(
            f"  {graph.nodes[current]['name']}"
            f" -- {relationships} --> "
            f"{graph.nodes[next_node]['name']}"
        )