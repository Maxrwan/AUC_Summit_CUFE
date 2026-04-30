import numpy as np
from scipy.spatial import KDTree

def classify_nodes(graph):
    endpoints, junctions, normals = [], [], []

    for node, neighbors in graph.items():
        deg = len(neighbors)
        if deg == 1:
            endpoints.append(node)
        elif deg == 2:
            normals.append(node)
        elif deg >= 3:
            junctions.append(node)

    return endpoints, normals, junctions


def best_next_node(points, prev, current, candidates):
    """
    Choose next node based on direction continuity
    """
    if prev is None:
        return candidates[0]

    v1 = points[current] - points[prev]
    v1 = v1 / (np.linalg.norm(v1) + 1e-8)

    best = None
    best_score = -np.inf

    for c in candidates:
        v2 = points[c] - points[current]
        v2 = v2 / (np.linalg.norm(v2) + 1e-8)

        score = np.dot(v1, v2)  # cosine similarity

        if score > best_score:
            best_score = score
            best = c

    return best

from scipy.spatial import KDTree
import numpy as np


def extract_ordered_lines(points, radius=1.5):
    points = np.array(points, dtype = float)
    tree = KDTree(points)

    graph = {i: [] for i in range(len(points))}
    for i, p in enumerate(points):
        dists, idxs = tree.query(p, k=5)  # get closest 5 points

        dists = np.atleast_1d(dists)
        idxs = np.atleast_1d(idxs)
        
        neighbors = []

        for j, dist in zip(idxs, dists):
            if i == j:
                continue
            if dist > radius:
                continue

            neighbors.append((int(j), float(dist)))

    # 🔥 KEEP ONLY THE 2 CLOSEST
        neighbors = sorted(neighbors, key=lambda x: x[1])[:2]

        graph[i] = [j for j, _ in neighbors]

    visited_edges = set()
    lines = []

    def trace_edge(start, next_node):
        path = [start, next_node]
        prev = start
        current = next_node

        while True:
            neighbors = graph[current]
            candidates = [n for n in neighbors if n != prev]

            # 🔥 STOP at junctions (this is the key)
            if len(neighbors) != 2:
                break
            
            if len(candidates) == 0:
                break
            
            # only one forward direction exists now
            nxt = candidates[0]

            edge = tuple(sorted((current, nxt)))
            if edge in visited_edges:
                break

            visited_edges.add(edge)

            path.append(nxt)
            prev = current
            current = nxt

        return path

    endpoints = [i for i in graph if len(graph[i]) == 1]
    junctions = [i for i in graph if len(graph[i]) >= 3]
    
    for i in graph:
        for j in graph[i]:
            edge = tuple(sorted((i, j)))
            if edge in visited_edges:
                continue

            visited_edges.add(edge)
            path = trace_edge(i, j)

            if len(path) > 1:
                lines.append(points[path].tolist()) 

    return lines