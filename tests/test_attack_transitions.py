from src.graph.bloodhound_graph import build_attack_graph
from src.graph.attack_transitions import get_available_transitions


DATA_DIR = "data/ESSOS_20240410083816"


def test_available_transitions():
    graph = build_attack_graph(DATA_DIR)

    # Pick a node that has at least one outgoing edge
    current_node = next(iter(graph.nodes))

    transitions = get_available_transitions(graph, current_node)

    assert len(transitions) > 0

    for transition in transitions:
        assert "target" in transition
        assert "relationship" in transition
        assert "target_name" in transition


def test_transition_matches_graph_edge():
    graph = build_attack_graph(DATA_DIR)

    current_node = next(
        node for node in graph.nodes
        if graph.out_degree(node) > 0
    )

    transitions = get_available_transitions(graph, current_node)

    for transition in transitions:
        target = transition["target"]
        relationship = transition["relationship"]

        edge_relationships = [
            data.get("relationship")
            for data in graph.get_edge_data(current_node, target).values()
        ]

        assert relationship in edge_relationships

def test_show_available_transitions():
    graph = build_attack_graph(DATA_DIR)

    current_node = next(
        node for node in graph.nodes
        if graph.out_degree(node) > 0
    )

    transitions = get_available_transitions(graph, current_node)

    print("\nCurrent node:")
    print(graph.nodes[current_node]["name"])

    print("\nAvailable transitions:")

    for transition in transitions:
        print(
            f"  -> {transition['target_name']} "
            f"[{transition['relationship']}]"
        )