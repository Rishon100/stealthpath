def get_available_transitions(graph, current_node):
    """
    Return all outgoing attack-path transitions
    available from the current node.
    """

    transitions = []

    for _, target, edge_key, data in graph.out_edges(
        current_node,
        keys=True,
        data=True,
    ):
        transitions.append({
            "target": target,
            "edge_key": edge_key,
            "relationship": data.get("relationship"),
            "target_name": data.get("target_name"),
        })

    return transitions