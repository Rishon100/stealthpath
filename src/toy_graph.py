import networkx as nx

graph = nx.Graph()

# Path 1
graph.add_edge("START", "A")
graph.add_edge("A", "B")
graph.add_edge("B", "TARGET")

# Path 2
graph.add_edge("START", "C")
graph.add_edge("C", "D")
graph.add_edge("D", "E")
graph.add_edge("E", "TARGET")

path = nx.shortest_path(graph, "START", "TARGET")

print("Shortest path:", path)
print("Number of hops:", len(path) - 1)