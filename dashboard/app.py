import sys
from pathlib import Path

# ---------------------------------------------------------
# Make the project root visible to Python
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


import streamlit as st
import networkx as nx

from src.graph.bloodhound_graph import build_attack_graph
from src.graph.attack_transitions import get_available_transitions
from src.planners.shortest_path import find_shortest_path


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DATA_DIR = PROJECT_ROOT / "data" / "ESSOS_20240410083816"


# ---------------------------------------------------------
# Page setup
# ---------------------------------------------------------

st.set_page_config(
    page_title="StealthPath",
    layout="wide",
)


# ---------------------------------------------------------
# Styling
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    .stApp {
        background-color: #ffffff;
        color: #000000;
    }

    h1, h2, h3 {
        color: #000000;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .header-box {
        border-bottom: 2px solid #000000;
        padding-bottom: 18px;
        margin-bottom: 25px;
    }

    .info-box {
        border: 1px solid #000000;
        padding: 18px;
        margin-bottom: 15px;
        background: #ffffff;
    }

    .metric-box {
        border: 1px solid #000000;
        padding: 16px;
        text-align: center;
        background: #ffffff;
    }

    .metric-number {
        font-size: 28px;
        font-weight: 600;
    }

    .metric-label {
        font-size: 13px;
        margin-top: 4px;
    }

    .status-box {
        border: 1px solid #000000;
        padding: 18px;
        margin: 8px 0;
        background: #ffffff;
        min-height: 120px;
    }

    .path-step {
        border: 1px solid #000000;
        padding: 12px;
        margin: 5px 0;
        text-align: center;
        font-weight: 600;
        background: #ffffff;
    }

    .path-relation {
        text-align: center;
        padding: 6px;
        font-size: 13px;
    }

    .guide-box {
        border-left: 3px solid #000000;
        padding: 12px 16px;
        margin: 10px 0 20px 0;
        background: #fafafa;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Load graph
# ---------------------------------------------------------

@st.cache_resource
def load_graph():
    return build_attack_graph(DATA_DIR)


graph = load_graph()


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def get_node_name(node):
    """
    Return the human-readable BloodHound name.

    The internal ObjectIdentifier is only used when
    no readable name is available.
    """

    name = graph.nodes[node].get("name")

    if name:
        return str(name)

    return f"Unknown Node ({node})"


def get_node_type(node):
    """
    Return the object type stored in the graph.
    """

    return graph.nodes[node].get(
        "object_type",
        "Unknown",
    )


def get_node_by_name(name):
    """
    Find a node using its display name.
    """

    for node, data in graph.nodes(data=True):

        if data.get("name") == name:
            return node

    return None


def get_direct_relationships(
    graph,
    source,
    target,
):
    """
    Find all direct relationships from source to target.

    Multiple relationships may exist between the same
    pair of nodes.
    """

    edge_data = graph.get_edge_data(
        source,
        target,
    )

    if not edge_data:
        return []

    relationships = []

    for data in edge_data.values():

        relationship = data.get(
            "relationship",
            "Unknown",
        )

        relationships.append(
            relationship
        )

    return sorted(set(relationships))


def find_unreachable_pair(graph):
    """
    Find a pair of different nodes for which no directed
    path exists in the current graph.

    The pair is calculated from the actual ESSOS graph.
    """

    nodes = list(graph.nodes)

    for source in nodes:

        reachable_nodes = nx.descendants(
            graph,
            source,
        )

        for target in nodes:

            if source == target:
                continue

            if target not in reachable_nodes:

                return source, target

    return None, None


def find_reachable_pair(graph):
    """
    Find a directed source-target pair from the actual graph.

    The known ESSOS demonstration path is preferred.
    """

    source = get_node_by_name(
        "VAGRANT@ESSOS.LOCAL"
    )

    target = get_node_by_name(
        "DOMAIN ADMINS@ESSOS.LOCAL"
    )

    if (
        source is not None
        and target is not None
        and nx.has_path(
            graph,
            source,
            target,
        )
    ):

        return source, target

    # Fallback: find any reachable pair.
    for source in graph.nodes:

        reachable_nodes = nx.descendants(
            graph,
            source,
        )

        if reachable_nodes:

            target = next(
                iter(reachable_nodes)
            )

            return source, target

    return None, None


# ---------------------------------------------------------
# Graph visualization
# ---------------------------------------------------------

def build_attack_graph_view(
    graph,
    center_node,
    depth=2,
    max_nodes=40,
):
    """
    Create a readable visualization of the graph around
    the selected node.

    This only creates a visualization subgraph.
    The original graph is not modified.
    """

    nodes_by_distance = (
        nx.single_source_shortest_path_length(
            graph,
            center_node,
            cutoff=depth,
        )
    )

    selected_nodes = sorted(
        nodes_by_distance,
        key=lambda node: nodes_by_distance[node],
    )[:max_nodes]

    subgraph = graph.subgraph(
        selected_nodes
    ).copy()

    # -----------------------------------------------------
    # Graphviz DOT
    # -----------------------------------------------------

    dot = [
        "digraph G {",
        "rankdir=LR;",
        'graph [pad="0.4", nodesep="0.5", ranksep="0.8"];',
        'node [shape=box, style="rounded", fontname="Arial"];',
        'edge [fontname="Arial", fontsize=9];',
    ]

    # Graphviz uses simple internal IDs.
    # These are not displayed to the user.
    node_ids = {
        node: f"n{index}"
        for index, node in enumerate(
            subgraph.nodes
        )
    }

    # -----------------------------------------------------
    # Nodes
    # -----------------------------------------------------

    for node in subgraph.nodes:

        graph_id = node_ids[node]

        name = get_node_name(node)
        node_type = get_node_type(node)

        safe_name = (
            str(name)
            .replace('"', '\\"')
            .replace("\n", " ")
        )

        safe_type = (
            str(node_type)
            .replace('"', '\\"')
            .replace("\n", " ")
        )

        label = (
            f"{safe_name}\\n"
            f"[{safe_type}]"
        )

        if node == center_node:

            dot.append(
                f'{graph_id} '
                f'[label="{label}\\nSELECTED", '
                f'penwidth=3];'
            )

        else:

            dot.append(
                f'{graph_id} '
                f'[label="{label}"];'
            )

    # -----------------------------------------------------
    # Edges
    # -----------------------------------------------------

    for source, target in subgraph.edges():

        edge_data = subgraph.get_edge_data(
            source,
            target,
        )

        if not edge_data:
            continue

        relationships = sorted(
            {
                data.get(
                    "relationship",
                    "Unknown",
                )
                for data in edge_data.values()
            }
        )

        relationship_text = ", ".join(
            relationships
        )

        safe_relationship = (
            relationship_text
            .replace('"', '\\"')
            .replace("\n", " ")
        )

        dot.append(
            f'{node_ids[source]} -> '
            f'{node_ids[target]} '
            f'[label="{safe_relationship}"];'
        )

    dot.append("}")

    return "\n".join(dot), subgraph


# ---------------------------------------------------------
# Path visualization
# ---------------------------------------------------------

def show_path(graph, path):

    for index, edge_key in enumerate(
        path.edges
    ):

        current = path.nodes[index]
        next_node = path.nodes[index + 1]

        edge = graph.get_edge_data(
            current,
            next_node,
            key=edge_key,
        )

        relationship = edge.get(
            "relationship",
            "Unknown",
        )

        st.markdown(
            f"""
            <div class="path-step">
                {get_node_name(current)}
            </div>

            <div class="path-relation">
                ↓ {relationship} ↓
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="path-step">
            {get_node_name(path.nodes[-1])}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Find demonstration pairs
# ---------------------------------------------------------

reachable_source, reachable_target = (
    find_reachable_pair(graph)
)

unreachable_source, unreachable_target = (
    find_unreachable_pair(graph)
)


reachable_source_name = (
    get_node_name(reachable_source)
    if reachable_source is not None
    else None
)

reachable_target_name = (
    get_node_name(reachable_target)
    if reachable_target is not None
    else None
)

unreachable_source_name = (
    get_node_name(unreachable_source)
    if unreachable_source is not None
    else None
)

unreachable_target_name = (
    get_node_name(unreachable_target)
    if unreachable_target is not None
    else None
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="header-box">
        <h1>STEALTHPATH</h1>
        <p>
            Comparative Attack Path Planning Under
            Adaptive Defender Visibility
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

st.sidebar.title("Dashboard Controls")

st.sidebar.markdown(
    "Use the controls below to explore the graph "
    "and test attack-path connectivity."
)


# =========================================================
# SIDEBAR — GRAPH VIEW
# =========================================================

st.sidebar.subheader("1. Graph View")

st.sidebar.caption(
    "Controls the attack graph displayed above."
)


node_names = sorted(
    get_node_name(node)
    for node in graph.nodes
)


selected_name = st.sidebar.selectbox(
    "Node to Explore",
    node_names,
)


selected_node = get_node_by_name(
    selected_name
)


depth = st.sidebar.slider(
    "Graph Depth",
    min_value=1,
    max_value=3,
    value=2,
)


st.sidebar.caption(
    "Graph depth controls how many relationship "
    "levels around the selected node are displayed."
)


# =========================================================
# SIDEBAR — PATH TEST
# =========================================================

st.sidebar.subheader("2. Path Test")

st.sidebar.caption(
    "Controls the source and target used for "
    "connectivity testing."
)


test_mode = st.sidebar.radio(
    "Test Case",
    [
        "Verified Reachable Case",
        "Graph-Verified Unreachable Case",
        "Custom Source and Target",
    ],
)


# ---------------------------------------------------------
# Determine source and target
# ---------------------------------------------------------

if test_mode == "Verified Reachable Case":

    source_name = reachable_source_name
    target_name = reachable_target_name

    st.sidebar.info(
        "This uses the verified ESSOS path "
        "VAGRANT → DOMAIN ADMINS when available."
    )


elif test_mode == "Graph-Verified Unreachable Case":

    source_name = unreachable_source_name
    target_name = unreachable_target_name

    st.sidebar.info(
        "This pair is automatically selected "
        "from the current ESSOS graph so that "
        "no directed path exists."
    )


else:

    source_name = st.sidebar.selectbox(
        "Source",
        node_names,
        key="custom_source",
    )

    target_name = st.sidebar.selectbox(
        "Target",
        node_names,
        key="custom_target",
    )


# ---------------------------------------------------------
# Validate demo pair availability
# ---------------------------------------------------------

if source_name is None or target_name is None:

    st.error(
        "A suitable source-target pair could not "
        "be found in the current graph."
    )

    st.stop()


source = get_node_by_name(
    source_name
)

target = get_node_by_name(
    target_name
)


# ---------------------------------------------------------
# Sidebar explanation
# ---------------------------------------------------------

st.sidebar.divider()

st.sidebar.subheader("What the controls mean")

st.sidebar.write(
    "**Node to Explore:** "
    "Selects the center of the graph visualization."
)

st.sidebar.write(
    "**Graph Depth:** "
    "Controls how many relationship levels are shown "
    "around that node."
)

st.sidebar.write(
    "**Source:** "
    "The node where the attacker starts."
)

st.sidebar.write(
    "**Target:** "
    "The node the attacker is trying to reach."
)

st.sidebar.write(
    "**Direct Relationship:** "
    "Checks whether one edge directly connects "
    "source to target."
)

st.sidebar.write(
    "**Directed Path:** "
    "Checks whether a sequence of outgoing "
    "relationships can connect source to target."
)


# =========================================================
# MAIN — ATTACK GRAPH
# =========================================================

st.header("1. Attack Graph")

st.markdown(
    """
    <div class="guide-box">
        This is the real ESSOS BloodHound graph loaded by
        StealthPath. Select a node from the sidebar to
        explore its surrounding relationships.
    </div>
    """,
    unsafe_allow_html=True,
)


dot_graph, displayed_graph = (
    build_attack_graph_view(
        graph,
        selected_node,
        depth=depth,
    )
)


st.graphviz_chart(
    dot_graph,
    use_container_width=True,
)


# ---------------------------------------------------------
# Graph statistics
# ---------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-number">
                {graph.number_of_nodes()}
            </div>
            <div class="metric-label">
                Total Nodes
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with col2:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-number">
                {graph.number_of_edges()}
            </div>
            <div class="metric-label">
                Walkable Edges
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with col3:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-number">
                {displayed_graph.number_of_nodes()}
            </div>
            <div class="metric-label">
                Displayed Nodes
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with col4:

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-number">
                {displayed_graph.number_of_edges()}
            </div>
            <div class="metric-label">
                Displayed Edges
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# MAIN — SELECTED NODE
# =========================================================

st.header("2. Selected Node")

node_col1, node_col2 = st.columns(2)

with node_col1:

    st.markdown(
        f"""
        <div class="info-box">
            <strong>Node Name</strong><br><br>
            {get_node_name(selected_node)}
        </div>
        """,
        unsafe_allow_html=True,
    )


with node_col2:

    st.markdown(
        f"""
        <div class="info-box">
            <strong>Node Type</strong><br><br>
            {get_node_type(selected_node)}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# MAIN — AVAILABLE TRANSITIONS
# =========================================================

st.header("3. Available Attack Transitions")

st.write(
    "These are the outgoing walkable relationships "
    "available from the selected node."
)


transitions = get_available_transitions(
    graph,
    selected_node,
)


if not transitions:

    st.info(
        "No outgoing walkable transitions were found "
        "from this node in the current graph."
    )

else:

    transition_rows = []

    for transition in transitions:

        transition_rows.append(
            {
                "Target": transition[
                    "target_name"
                ],
                "Relationship": transition[
                    "relationship"
                ],
                # "Edge Key": transition[
                #     "edge_key"
                # ],
            }
        )

    st.dataframe(
        transition_rows,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# MAIN — PATH EXPLORER
# =========================================================

st.header("4. Attack Path Explorer")

st.markdown(
    """
    <div class="guide-box">
        <strong>Source</strong> = where the attacker starts.<br>
        <strong>Target</strong> = the node the attacker wants to reach.<br>
        <strong>Direct relationship</strong> = one edge directly connects them.<br>
        <strong>Directed path</strong> = one or more outgoing relationships connect them.
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Display selected source and target
# ---------------------------------------------------------

path_col1, path_col2 = st.columns(2)

with path_col1:

    st.markdown(
        f"""
        <div class="info-box">
            <strong>Source</strong><br><br>
            {source_name}
        </div>
        """,
        unsafe_allow_html=True,
    )


with path_col2:

    st.markdown(
        f"""
        <div class="info-box">
            <strong>Target</strong><br><br>
            {target_name}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# CONNECTIVITY CHECK
# =========================================================

st.subheader("Connectivity Check")


if source == target:

    st.info(
        "Source and target are the same node. "
        "Choose two different nodes for a path test."
    )

else:

    direct_relationships = (
        get_direct_relationships(
            graph,
            source,
            target,
        )
    )

    has_direct_relationship = (
        len(direct_relationships) > 0
    )

    has_directed_path = nx.has_path(
        graph,
        source,
        target,
    )


    check_col1, check_col2 = st.columns(2)


    # -----------------------------------------------------
    # Direct relationship
    # -----------------------------------------------------

    with check_col1:

        if has_direct_relationship:

            relationship_text = ", ".join(
                direct_relationships
            )

            st.markdown(
                f"""
                <div class="status-box">
                    <strong>Direct Relationship</strong>
                    <br><br>
                    Yes
                    <br><br>
                    Relationship(s):
                    {relationship_text}
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                """
                <div class="status-box">
                    <strong>Direct Relationship</strong>
                    <br><br>
                    No
                    <br><br>
                    No single outgoing edge connects
                    the selected source directly to
                    the selected target.
                </div>
                """,
                unsafe_allow_html=True,
            )


    # -----------------------------------------------------
    # Directed path
    # -----------------------------------------------------

    with check_col2:

        if has_directed_path:

            try:

                hop_count = nx.shortest_path_length(
                    graph,
                    source,
                    target,
                )

            except Exception:

                hop_count = "Available"


            st.markdown(
                f"""
                <div class="status-box">
                    <strong>Directed Path</strong>
                    <br><br>
                    Yes
                    <br><br>
                    A directed path exists from
                    source to target.
                    <br><br>
                    Minimum graph distance:
                    {hop_count} transition(s)
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                """
                <div class="status-box">
                    <strong>Directed Path</strong>
                    <br><br>
                    No
                    <br><br>
                    No directed attack path exists
                    from source to target in the
                    current graph.
                </div>
                """,
                unsafe_allow_html=True,
            )


# =========================================================
# CALCULATE SHORTEST PATH
# =========================================================

if st.button(
    "Calculate Shortest Path",
    use_container_width=True,
):

    if source == target:

        st.warning(
            "Source and target must be different."
        )

    elif not nx.has_path(
        graph,
        source,
        target,
    ):

        st.error(
            "No directed path exists between "
            "the selected source and target."
        )

        st.caption(
            "The current directed attack graph contains "
            "no sequence of walkable relationships from "
            "the selected source to the selected target."
        )

    else:

        try:

            path = find_shortest_path(
                graph,
                source,
                target,
            )


            st.success(
                f"Shortest path found: "
                f"{path.length} transitions"
            )


            result_col1, result_col2, result_col3 = (
                st.columns(3)
            )


            with result_col1:

                st.metric(
                    "Planner",
                    path.planner,
                )


            with result_col2:

                st.metric(
                    "Transitions",
                    path.length,
                )


            with result_col3:

                st.metric(
                    "Cost",
                    path.cost,
                )


            st.subheader("Path")

            show_path(
                graph,
                path,
            )


        except nx.NetworkXNoPath:

            st.error(
                "No directed path exists between "
                "the selected source and target."
            )


        except Exception as error:

            st.error(
                f"Path calculation failed: {error}"
            )


# =========================================================
# MAIN — IMPLEMENTED COMPONENTS
# =========================================================

st.header("5. Implemented Components")

implemented = [
    "ESSOS SharpHound graph construction",
    "Walkable attack-transition extraction",
    "Multi-edge / edge-key representation",
    "Path representation and validation",
    "Shortest-path baseline",
    "Directed connectivity checking",
    "Human-readable attack-graph visualization",
    "Verified reachable and unreachable test cases",
    "Automated test suite: 16 tests passing",
]


for item in implemented:

    st.write(
        f"— {item}"
    )


# =========================================================
# MAIN — PROJECT STATUS
# =========================================================

st.header("6. Current Project Status")

st.markdown(
    """
    <div class="info-box">

    <strong>Currently implemented and verified:</strong>

    <br><br>

    Real ESSOS BloodHound graph loading,
    walkable attack-transition extraction,
    edge-aware path representation,
    shortest-path baseline,
    directed connectivity checking,
    and dashboard visualization.

    <br><br>

    <strong>Not yet represented as completed:</strong>

    <br><br>

    Risk-aware planning, detection/visibility costs,
    and reinforcement-learning attack-path planning.

    These components are deliberately not presented
    as completed results.

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "StealthPath Review 1 Prototype | "
    "ESSOS BloodHound graph and verified shortest-path components"
)