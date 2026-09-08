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

    assert path.nodes[0] == source
    assert path.nodes[-1] == target
    assert path.length >= 1
    assert path.cost == path.length


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

    path.validate(graph)


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

    for index, edge_key in enumerate(path.edges):
        edge = graph.get_edge_data(
            path.nodes[index],
            path.nodes[index + 1],
            key=edge_key,
        )

        print(
            f"  {graph.nodes[path.nodes[index]]['name']}"
            f" -- {edge['relationship']} --> "
            f"{graph.nodes[path.nodes[index + 1]]['name']}"
        )