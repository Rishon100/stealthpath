from dataclasses import dataclass


@dataclass(frozen=True)
class Path:
    """
    Represents one concrete path through the graph.

    nodes:
        Node IDs visited by the path.

    edges:
        Specific NetworkX edge keys used between those nodes.

    cost:
        Total cost of the path.

    planner:
        Name of the planner that produced the path.
    """

    nodes: tuple
    edges: tuple
    cost: float
    planner: str = ""

    @property
    def length(self):
        """Return the number of graph transitions."""
        return len(self.edges)

    def validate(self, graph):
        """Check that the edges really connect the nodes in the path."""

        if len(self.edges) != len(self.nodes) - 1:
            raise ValueError(
                "Number of edges must equal number of nodes minus one."
            )

        for index, edge_key in enumerate(self.edges):
            source = self.nodes[index]
            target = self.nodes[index + 1]

            edge_data = graph.get_edge_data(
                source,
                target,
                key=edge_key
            )

            if edge_data is None:
                raise ValueError(
                    f"Edge {edge_key} does not connect "
                    f"{source} to {target}."
                )