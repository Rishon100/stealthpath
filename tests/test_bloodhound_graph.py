from pathlib import Path

from src.graph.bloodhound_graph import build_attack_graph


DATA_DIR = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "ESSOS_20240410083816"
)


def test_essos_graph_loads():
    graph = build_attack_graph(DATA_DIR)

    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0

def test_essos_graph_summary():
    graph = build_attack_graph(DATA_DIR)

    print("Nodes:", graph.number_of_nodes())
    print("Edges:", graph.number_of_edges())

    relationship_counts = {}

    for _, _, data in graph.edges(data=True):
        relationship = data["relationship"]
        relationship_counts[relationship] = (
            relationship_counts.get(relationship, 0) + 1
        )

    print("Relationships:")

    for relationship, count in sorted(relationship_counts.items()):
        print(f"  {relationship}: {count}")

def test_relationships_are_stored():
    graph = build_attack_graph(DATA_DIR)

    relationships = {
        data["relationship"]
        for _, _, data in graph.edges(data=True)
    }

    expected = {
        "Owns",
        "GenericAll",
        "GenericWrite",
        "WriteDacl",
        "WriteOwner",
        "MemberOf",
    }

    for relationship in expected:
        assert relationship in relationships

def test_edge_direction():
    graph = build_attack_graph(DATA_DIR)

    source = "S-1-5-21-2158876063-2930955257-1391117225-512"
    target = "S-1-5-21-2158876063-2930955257-1391117225-1104"

    assert graph.has_edge(source, target)

    edge_data = graph.get_edge_data(source, target)

    relationships = {
        data["relationship"]
        for data in edge_data.values()
    }

    assert "Owns" in relationships
def test_node_types():
    graph = build_attack_graph(DATA_DIR)

    node_types = {}

    for _, data in graph.nodes(data=True):
        object_type = data.get("object_type", "unknown")
        node_types[object_type] = node_types.get(object_type, 0) + 1

    print("\nNode types:")

    for object_type, count in sorted(node_types.items()):
        print(f"  {object_type}: {count}")

    assert graph.number_of_nodes() > 0

def test_show_one_edge():
    graph = build_attack_graph(DATA_DIR)

    source, target, data = next(iter(graph.edges(data=True)))

    print("\nOne edge:")
    print("Source:", source)
    print("Source name:", data["source_name"])
    print("Relationship:", data["relationship"])
    print("Target:", target)
    print("Target name:", data["target_name"])

    assert source is not None
    assert target is not None
    assert data["relationship"]