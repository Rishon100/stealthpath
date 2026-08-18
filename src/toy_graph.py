import networkx as nx

graph = nx.Graph()

# Path 1
graph.add_edge("START", "A",weight = 5)
graph.add_edge("A", "B",weight = 5)
graph.add_edge("B", "TARGET",weight = 5)

# Path 2
graph.add_edge("START", "C",weight = 1)
graph.add_edge("C", "D",weight = 1)
graph.add_edge("D", "E",weight = 1)
graph.add_edge("E", "TARGET",weight = 1)

path = nx.shortest_path(graph, "START", "TARGET",weight='weight')
total_cost = nx.path_weight(graph, path, weight="weight")

print("Risk-weighted path:", path)
print("Number of hops:", len(path) - 1)
print("Total detection cost:", total_cost)