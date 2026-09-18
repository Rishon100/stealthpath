from pathlib import Path
import sys

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.graph.bloodhound_graph import build_attack_graph
from src.graph.export_graph import export_graph

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ESSOS_DIR = (
    PROJECT_ROOT
    / "data"
    / "ESSOS_20240410083816"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "stealthpath_essos_graph.json"
)


graph = build_attack_graph(
    ESSOS_DIR
)

export_graph(
    graph,
    OUTPUT_PATH,
)

print(
    f"Exported {graph.number_of_nodes()} nodes "
    f"and {graph.number_of_edges()} edges."
)

print(
    f"Saved to: {OUTPUT_PATH}"
)