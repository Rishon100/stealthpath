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