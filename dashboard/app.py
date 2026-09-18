import json
import sys
import tempfile
import zipfile
from pathlib import Path

import networkx as nx
import streamlit as st

# ---------------------------------------------------------
# Project import setup
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.graph.bloodhound_graph import (
    build_attack_graph,
    WALKABLE_RELATIONSHIPS,
)
from src.graph.attack_transitions import get_available_transitions
from src.planners.shortest_path import find_shortest_path


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="StealthPath",
    page_icon=None,
    layout="wide",
)


# ---------------------------------------------------------
# Styling
# ---------------------------------------------------------

st.markdown(
    """
    <style>
    .main {
        padding-top: 1rem;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
    }

    .metric-card {
        border: 1px solid #d9d9d9;
        border-radius: 8px;
        padding: 16px;
        background: white;
    }

    .status-box {
        border: 1px solid #d9d9d9;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }

    .small-text {
        color: #666666;
        font-size: 0.9rem;
    }

    h1, h2, h3 {
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

ESSOS_DIR = (
    PROJECT_ROOT
    / "data"
    / "ESSOS_20240410083816"
)


# ---------------------------------------------------------
# General graph helpers
# ---------------------------------------------------------

def get_node_name(graph, node_id):
    """Return a readable node name."""

    data = graph.nodes[node_id]

    return data.get("name", node_id)


def get_node_type(graph, node_id):
    """Return the node type."""

    data = graph.nodes[node_id]

    return data.get("object_type", "unknown")


def get_node_by_name(graph, name):
    """Find a node ID from its display name."""

    for node_id, data in graph.nodes(data=True):

        if data.get("name") == name:
            return node_id

    return None


def get_relationship_counts(graph):
    """Count graph relationships."""

    counts = {}

    for _, _, data in graph.edges(data=True):

        relationship = data.get(
            "relationship",
            "Unknown",
        )

        counts[relationship] = (
            counts.get(relationship, 0) + 1
        )

    return counts


def get_node_type_counts(graph):
    """Count nodes by object type."""

    counts = {}

    for _, data in graph.nodes(data=True):

        node_type = data.get(
            "object_type",
            "unknown",
        )

        counts[node_type] = (
            counts.get(node_type, 0) + 1
        )

    return counts


# ---------------------------------------------------------
# Generic graph loaders
# ---------------------------------------------------------

def load_csv_graph(uploaded_file):
    """
    Load a simple CSV graph.

    Required columns:
        source,target

    Optional:
        relationship
    """

    import pandas as pd

    df = pd.read_csv(uploaded_file)

    columns = {
        column.lower(): column
        for column in df.columns
    }

    if "source" not in columns or "target" not in columns:
        raise ValueError(
            "CSV must contain source and target columns."
        )

    source_column = columns["source"]
    target_column = columns["target"]

    relationship_column = columns.get(
        "relationship"
    )

    graph = nx.MultiDiGraph()

    for _, row in df.iterrows():

        source = str(row[source_column])
        target = str(row[target_column])

        if source not in graph:
            graph.add_node(
                source,
                name=source,
                object_type="generic",
            )

        if target not in graph:
            graph.add_node(
                target,
                name=target,
                object_type="generic",
            )

        relationship = "Unknown"

        if relationship_column:
            relationship = str(
                row[relationship_column]
            )

        graph.add_edge(
            source,
            target,
            relationship=relationship,
            source_name=source,
            target_name=target,
        )

    return graph


def load_json_graph(uploaded_file):
    """
    Load a generic JSON graph.

    Supported structure:

    {
        "nodes": [...],
        "edges": [...]
    }

    Each edge should contain:
        source
        target

    Optional:
        relationship
    """

    raw = uploaded_file.read()

    data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError(
            "JSON graph must be an object."
        )

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    if not edges:
        raise ValueError(
            "JSON graph must contain an edges list."
        )

    graph = nx.MultiDiGraph()

    # Add explicit nodes first.
    for node in nodes:

        if isinstance(node, dict):

            node_id = (
                node.get("id")
                or node.get("ObjectIdentifier")
                or node.get("name")
            )

            if not node_id:
                continue

            graph.add_node(
                str(node_id),
                name=node.get(
                    "name",
                    str(node_id),
                ),
                object_type=node.get(
                    "object_type",
                    "generic",
                ),
            )

        else:

            node_id = str(node)

            graph.add_node(
                node_id,
                name=node_id,
                object_type="generic",
            )

    # Add edges.
    for edge in edges:

        if not isinstance(edge, dict):
            continue

        source = edge.get("source")
        target = edge.get("target")

        if source is None or target is None:
            continue

        source = str(source)
        target = str(target)

        if source not in graph:

            graph.add_node(
                source,
                name=source,
                object_type="generic",
            )

        if target not in graph:

            graph.add_node(
                target,
                name=target,
                object_type="generic",
            )

        graph.add_edge(
            source,
            target,
            relationship=edge.get(
                "relationship",
                "Unknown",
            ),
            source_name=source,
            target_name=target,
        )

    return graph


def load_graphml(uploaded_file):
    """Load a GraphML graph."""

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".graphml",
    ) as temp_file:

        temp_file.write(
            uploaded_file.getvalue()
        )

        temp_path = temp_file.name

    graph = nx.read_graphml(temp_path)

    converted = nx.MultiDiGraph()

    for node, data in graph.nodes(data=True):

        converted.add_node(
            str(node),
            name=data.get(
                "name",
                str(node),
            ),
            object_type=data.get(
                "object_type",
                "generic",
            ),
        )

    for source, target, data in graph.edges(
        data=True
    ):

        converted.add_edge(
            str(source),
            str(target),
            relationship=data.get(
                "relationship",
                "Unknown",
            ),
            source_name=str(source),
            target_name=str(target),
        )

    return converted


def load_bloodhound_zip(uploaded_file):
    """
    Load a compatible SharpHound/BloodHound ZIP.

    This is a dashboard-level generic loader.
    It does not change the core StealthPath
    graph implementation.
    """

    graph = nx.MultiDiGraph()

    with tempfile.TemporaryDirectory() as temp_dir:

        zip_path = (
            Path(temp_dir)
            / "uploaded.zip"
        )

        zip_path.write_bytes(
            uploaded_file.getvalue()
        )

        extract_dir = (
            Path(temp_dir)
            / "collection"
        )

        extract_dir.mkdir()

        with zipfile.ZipFile(
            zip_path,
            "r",
        ) as archive:

            archive.extractall(
                extract_dir
            )

        json_files = list(
            extract_dir.rglob("*.json")
        )

        objects = []

        for path in json_files:

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8",
                ) as file:

                    content = json.load(file)

                records = content.get(
                    "data",
                    [],
                )

                if not isinstance(
                    records,
                    list,
                ):
                    continue

                filename = (
                    path.name.lower()
                )

                if "_users" in filename:
                    object_type = "users"
                elif "_groups" in filename:
                    object_type = "groups"
                elif "_computers" in filename:
                    object_type = "computers"
                elif "_domains" in filename:
                    object_type = "domains"
                elif "_ous" in filename:
                    object_type = "ous"
                elif "_containers" in filename:
                    object_type = "containers"
                elif "_gpos" in filename:
                    object_type = "gpos"
                elif "_certtemplates" in filename:
                    object_type = "certtemplates"
                else:
                    object_type = "unknown"

                for obj in records:

                    if not isinstance(
                        obj,
                        dict,
                    ):
                        continue

                    obj["_dashboard_object_type"] = (
                        object_type
                    )

                    objects.append(obj)

            except Exception:
                continue

        # Build lookup.
        lookup = {}

        for obj in objects:

            object_id = obj.get(
                "ObjectIdentifier"
            )

            if not object_id:
                continue

            properties = obj.get(
                "Properties",
                {},
            )

            name = properties.get(
                "name",
                object_id,
            )

            lookup[object_id] = (
                obj,
                name,
            )

            graph.add_node(
                object_id,
                name=name,
                object_type=obj.get(
                    "_dashboard_object_type",
                    "unknown",
                ),
            )

        # ACL relationships.
        for target in objects:

            target_id = target.get(
                "ObjectIdentifier"
            )

            if not target_id:
                continue

            target_name = lookup.get(
                target_id,
                (None, target_id),
            )[1]

            for ace in target.get(
                "Aces",
                [],
            ):

                relationship = ace.get(
                    "RightName"
                )

                source_id = ace.get(
                    "PrincipalSID"
                )

                if (
                    not relationship
                    or not source_id
                ):
                    continue

                if (
                    relationship
                    not in WALKABLE_RELATIONSHIPS
                ):
                    continue

                if source_id not in lookup:
                    continue

                source_name = lookup[
                    source_id
                ][1]

                graph.add_edge(
                    source_id,
                    target_id,
                    relationship=relationship,
                    source_name=source_name,
                    target_name=target_name,
                )

        # Group membership.
        for group in objects:

            if group.get(
                "_dashboard_object_type"
            ) != "groups":
                continue

            group_id = group.get(
                "ObjectIdentifier"
            )

            if not group_id:
                continue

            group_name = lookup.get(
                group_id,
                (None, group_id),
            )[1]

            for member in group.get(
                "Members",
                [],
            ):

                member_id = member.get(
                    "ObjectIdentifier"
                )

                if (
                    not member_id
                    or member_id not in lookup
                ):
                    continue

                member_name = lookup[
                    member_id
                ][1]

                graph.add_edge(
                    member_id,
                    group_id,
                    relationship="MemberOf",
                    source_name=member_name,
                    target_name=group_name,
                )

    if graph.number_of_nodes() == 0:
        raise ValueError(
            "No compatible BloodHound objects were found."
        )

    return graph


# ---------------------------------------------------------
# Uploaded graph detection
# ---------------------------------------------------------

def load_uploaded_graph(uploaded_file):

    filename = (
        uploaded_file.name.lower()
    )

    if filename.endswith(".csv"):
        return (
            load_csv_graph(uploaded_file),
            "Generic CSV graph",
            False,
        )

    if filename.endswith(".graphml"):
        return (
            load_graphml(uploaded_file),
            "Generic GraphML graph",
            False,
        )

    if filename.endswith(".json"):
        return (
            load_json_graph(uploaded_file),
            "Generic JSON graph",
            False,
        )

    if filename.endswith(".zip"):

        return (
            load_bloodhound_zip(
                uploaded_file
            ),
            "BloodHound / SharpHound collection",
            True,
        )

    raise ValueError(
        "Supported formats: CSV, JSON, GraphML, ZIP."
    )


# ---------------------------------------------------------
# Path helpers
# ---------------------------------------------------------

def get_direct_relationships(
    graph,
    source,
    target,
):

    relationships = []

    edge_data = graph.get_edge_data(
        source,
        target,
    )

    if not edge_data:
        return relationships

    for edge_key, data in edge_data.items():

        relationships.append(
            (
                edge_key,
                data.get(
                    "relationship",
                    "Unknown",
                ),
            )
        )

    return relationships


def find_unreachable_pair(graph):

    nodes = list(graph.nodes())

    for source in nodes:

        for target in nodes:

            if source == target:
                continue

            if not nx.has_path(
                graph,
                source,
                target,
            ):

                return source, target

    return None


def find_reachable_pair(graph):

    nodes = list(graph.nodes())

    for source in nodes:

        for target in nodes:

            if source == target:
                continue

            if nx.has_path(
                graph,
                source,
                target,
            ):

                return source, target

    return None


# ---------------------------------------------------------
# Graph visualization
# ---------------------------------------------------------

def create_subgraph_for_display(
    graph,
    source=None,
    target=None,
    depth=2,
):

    selected = set()

    if source in graph:
        selected.add(source)

    if target in graph:
        selected.add(target)

    if not selected:

        return graph

    nodes = set(selected)

    for node in list(selected):

        reachable = nx.single_source_shortest_path_length(
            graph,
            node,
            cutoff=depth,
        )

        nodes.update(
            reachable.keys()
        )

    return graph.subgraph(nodes).copy()


def graph_to_dot(graph):

    lines = [
        "digraph G {",
        'rankdir="LR";',
        'node [shape=box, style="rounded"];',
    ]

    for node, data in graph.nodes(
        data=True
    ):

        name = str(
            data.get(
                "name",
                node,
            )
        ).replace(
            '"',
            "'",
        )

        lines.append(
            f'"{node}" '
            f'[label="{name}"];'
        )

    for source, target, data in graph.edges(
        data=True
    ):

        relationship = str(
            data.get(
                "relationship",
                "Unknown",
            )
        ).replace(
            '"',
            "'",
        )

        lines.append(
            f'"{source}" -> "{target}" '
            f'[label="{relationship}"];'
        )

    lines.append("}")

    return "\n".join(lines)


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "graph" not in st.session_state:

    if ESSOS_DIR.exists():

        st.session_state.graph = (
            build_attack_graph(
                ESSOS_DIR
            )
        )

        st.session_state.source_type = (
            "ESSOS SharpHound Dataset"
        )

        st.session_state.analysis_supported = True

    else:

        st.session_state.graph = (
            nx.MultiDiGraph()
        )

        st.session_state.source_type = (
            "No graph loaded"
        )

        st.session_state.analysis_supported = False


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("StealthPath")

st.markdown(
    "Detection-Aware Attack Path Planning in Active Directory"
)

st.divider()


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.header("Graph Input")

    input_mode = st.radio(
        "Data source",
        [
            "ESSOS Dataset",
            "Upload Graph",
        ],
    )

    if input_mode == "Upload Graph":

        uploaded_file = st.file_uploader(
            "Upload graph",
            type=[
                "csv",
                "json",
                "graphml",
                "zip",
            ],
            help=(
                "CSV, JSON and GraphML are "
                "supported for generic graph "
                "visualization. ZIP supports "
                "compatible BloodHound/"
                "SharpHound collections."
            ),
        )

        if uploaded_file:

            try:

                (
                    uploaded_graph,
                    uploaded_type,
                    attack_graph_ready,
                ) = load_uploaded_graph(
                    uploaded_file
                )

                st.session_state.graph = (
                    uploaded_graph
                )

                st.session_state.source_type = (
                    uploaded_type
                )

                st.session_state.analysis_supported = (
                    attack_graph_ready
                )

                st.success(
                    "Graph loaded successfully."
                )

            except Exception as error:

                st.error(
                    f"Could not load graph: {error}"
                )

    else:

        if ESSOS_DIR.exists():

            st.session_state.graph = (
                build_attack_graph(
                    ESSOS_DIR
                )
            )

            st.session_state.source_type = (
                "ESSOS SharpHound Dataset"
            )

            st.session_state.analysis_supported = (
                True
            )

        else:

            st.warning(
                "ESSOS dataset was not found."
            )

    st.divider()

    st.header("Graph View")

    graph = st.session_state.graph

    node_names = [
        get_node_name(
            graph,
            node,
        )
        for node in graph.nodes()
    ]

    if node_names:

        selected_name = st.selectbox(
            "Selected node",
            sorted(node_names),
        )

        selected_node = get_node_by_name(
            graph,
            selected_name,
        )

        depth = st.slider(
            "Graph depth",
            min_value=1,
            max_value=3,
            value=1,
        )

    else:

        selected_node = None
        depth = 1


# ---------------------------------------------------------
# Main graph reference
# ---------------------------------------------------------

graph = st.session_state.graph


# ---------------------------------------------------------
# Overview
# ---------------------------------------------------------

st.header("Graph Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Nodes",
        graph.number_of_nodes(),
    )

with col2:
    st.metric(
        "Edges",
        graph.number_of_edges(),
    )

with col3:
    st.metric(
        "Node Types",
        len(
            get_node_type_counts(
                graph
            )
        ),
    )

with col4:
    st.metric(
        "Relationships",
        len(
            get_relationship_counts(
                graph
            )
        ),
    )

st.caption(
    f"Data source: {st.session_state.source_type}"
)


# ---------------------------------------------------------
# Graph structure
# ---------------------------------------------------------

st.header("Graph Structure")

structure_col1, structure_col2 = st.columns(2)

with structure_col1:

    st.subheader("Node Types")

    node_type_counts = (
        get_node_type_counts(graph)
    )

    if node_type_counts:

        st.dataframe(
            [
                {
                    "Node Type": node_type,
                    "Count": count,
                }
                for node_type, count in sorted(
                    node_type_counts.items()
                )
            ],
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info("No nodes available.")


with structure_col2:

    st.subheader("Relationships")

    relationship_counts = (
        get_relationship_counts(graph)
    )

    if relationship_counts:

        st.dataframe(
            [
                {
                    "Relationship": relationship,
                    "Count": count,
                }
                for relationship, count in sorted(
                    relationship_counts.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            ],
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info("No relationships available.")


# ---------------------------------------------------------
# Graph visualization
# ---------------------------------------------------------

st.header("Graph Visualization")

display_graph = create_subgraph_for_display(
    graph,
    source=selected_node,
    depth=depth,
)

if display_graph.number_of_nodes() > 0:

    st.graphviz_chart(
        graph_to_dot(
            display_graph
        )
    )

    st.caption(
        "Visualization shows the selected node "
        "and nearby directed relationships."
    )

else:

    st.info(
        "Select a node to explore the graph."
    )


# ---------------------------------------------------------
# Source and target
# ---------------------------------------------------------

st.header("Source & Target")

if graph.number_of_nodes() >= 2:

    names = sorted(
        [
            get_node_name(
                graph,
                node,
            )
            for node in graph.nodes()
        ]
    )

    source_name = st.selectbox(
        "Source node",
        names,
        key="source_selector",
    )

    target_name = st.selectbox(
        "Target node",
        names,
        index=min(
            1,
            len(names) - 1,
        ),
        key="target_selector",
    )

    source = get_node_by_name(
        graph,
        source_name,
    )

    target = get_node_by_name(
        graph,
        target_name,
    )

else:

    source = None
    target = None

    st.info(
        "At least two nodes are required."
    )


# ---------------------------------------------------------
# Planner comparison
# ---------------------------------------------------------

st.header("Planner Comparison")

planner_col1, planner_col2, planner_col3 = st.columns(3)

with planner_col1:

    st.subheader("Shortest Path")

    st.write(
        "Minimizes the number of graph transitions."
    )

    if (
        source
        and target
        and source != target
    ):

        try:

            shortest = find_shortest_path(
                graph,
                source,
                target,
            )

            st.success(
                f"Path found: {shortest.length} hops"
            )

            st.write(
                f"Cost: {shortest.cost}"
            )

        except nx.NetworkXNoPath:

            st.warning(
                "No path exists between the selected nodes."
            )

        except Exception as error:

            st.error(
                f"Shortest-path analysis is "
                f"not available for this graph: "
                f"{error}"
            )

with planner_col2:

    st.subheader("Risk-Weighted")

    st.write(
        "Uses detection-aware transition costs."
    )

    st.info(
        "Not implemented yet."
    )

with planner_col3:

    st.subheader("Reinforcement Learning")

    st.write(
        "Learns a path-selection policy from experience."
    )

    st.info(
        "Not implemented yet."
    )


# ---------------------------------------------------------
# Attack path details
# ---------------------------------------------------------

st.header("Attack-Path Result")

if (
    source
    and target
    and source != target
):

    try:

        shortest = find_shortest_path(
            graph,
            source,
            target,
        )

        st.subheader(
            "Shortest-Path Baseline"
        )

        for index in range(
            shortest.length
        ):

            current = (
                shortest.nodes[index]
            )

            next_node = (
                shortest.nodes[index + 1]
            )

            edge_key = (
                shortest.edges[index]
            )

            edge_data = graph.get_edge_data(
                current,
                next_node,
                key=edge_key,
            )

            relationship = (
                edge_data.get(
                    "relationship",
                    "Unknown",
                )
                if edge_data
                else "Unknown"
            )

            st.write(
                f"**{get_node_name(graph, current)}** "
                f"→ `{relationship}` → "
                f"**{get_node_name(graph, next_node)}**"
            )

    except nx.NetworkXNoPath:

        st.info(
            "No directed path exists between "
            "the selected source and target."
        )

    except Exception as error:

        st.warning(
            f"Path result unavailable: {error}"
        )

else:

    st.info(
        "Select different source and target nodes "
        "to test a path."
    )


# ---------------------------------------------------------
# Transition inspection
# ---------------------------------------------------------

st.header("Available Transitions")

if selected_node:

    transitions = get_available_transitions(
        graph,
        selected_node,
    )

    if transitions:

        transition_rows = []

        for transition in transitions:

            transition_rows.append(
                {
                    "Target": get_node_name(
                        graph,
                        transition["target"],
                    ),
                    "Relationship": transition[
                        "relationship"
                    ],
                }
            )

        st.dataframe(
            transition_rows,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "The selected node has no outgoing "
            "walkable transitions in the current graph."
        )


# ---------------------------------------------------------
# Analysis readiness
# ---------------------------------------------------------

st.header("Analysis Readiness")

status_col1, status_col2 = st.columns(2)

with status_col1:

    st.subheader("Graph")

    st.write(
        "Graph loaded: Yes"
        if graph.number_of_nodes() > 0
        else "Graph loaded: No"
    )

    st.write(
        f"Nodes detected: {graph.number_of_nodes()}"
    )

    st.write(
        f"Edges detected: {graph.number_of_edges()}"
    )

    if st.session_state.analysis_supported:

        st.write(
            "Attack-graph compatible: Yes"
        )

    else:

        st.write(
            "Attack-graph compatible: "
            "Not established"
        )


with status_col2:

    st.subheader("StealthPath Components")

    st.write(
        "Graph construction: Implemented"
    )

    st.write(
        "Attack transitions: Implemented"
    )

    st.write(
        "Shortest-path baseline: Implemented"
    )

    st.write(
        "Risk/detection model: Pending"
    )

    st.write(
        "Adaptive/RL planner: Pending"
    )


# ---------------------------------------------------------
# Research status
# ---------------------------------------------------------

st.header("Research Status")

st.markdown(
    """
    **Current verified components**

    - Real ESSOS SharpHound graph loading
    - Attack-transition extraction
    - Shortest-path baseline
    - Graph structure inspection
    - Source-to-target path testing
    - Graph visualization
    - Generic graph upload and structure visualization

    **Still under development**

    - Evidence-backed detection/visibility cost model
    - Risk-weighted planner
    - Reinforcement-learning planner
    - Comparative evaluation
    """
)

st.caption(
    "Generic uploaded graphs are not automatically treated "
    "as validated Active Directory attack graphs."
)