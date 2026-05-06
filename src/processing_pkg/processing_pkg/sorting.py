import numpy as np


# ===================== GRAPH BUILDING =====================

def build_graph_from_skeleton(skel_img):
    """
    Convert binary skeleton image to graph using 8-connectivity
    """
    h, w = skel_img.shape
    points = []
    index_map = {}

    # assign index to each pixel
    idx = 0
    for y in range(h):
        for x in range(w):
            if skel_img[y, x] > 0:
                index_map[(x, y)] = idx
                points.append((x, y))
                idx += 1

    points = np.array(points, dtype=float)

    # build adjacency
    graph = {i: [] for i in range(len(points))}

    directions = [
        (-1, -1), (0, -1), (1, -1),
        (-1,  0),          (1,  0),
        (-1,  1), (0,  1), (1,  1)
    ]

    for (x, y), i in index_map.items():
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (nx, ny) in index_map:
                j = index_map[(nx, ny)]
                graph[i].append(j)

    return points, graph


# ===================== NODE CLASSIFICATION =====================

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


# ===================== TRACE LOGIC =====================

def trace_edge(graph, points, start, next_node, visited_edges):
    path = [start, next_node]
    prev = start
    current = next_node

    while True:
        neighbors = graph[current]
        candidates = [n for n in neighbors if n != prev]

        # STOP at junction or endpoint
        if len(neighbors) != 2:
            break

        if len(candidates) == 0:
            break

        nxt = candidates[0]

        edge = tuple(sorted((current, nxt)))
        if edge in visited_edges:
            break

        visited_edges.add(edge)

        path.append(nxt)
        prev = current
        current = nxt

    return path


# ===================== MAIN FUNCTION =====================

def extract_ordered_lines_from_skeleton(skel_img):
    """
    Input: binary skeleton image
    Output: list of ordered lines [(x,y), ...]
    """

    points, graph = build_graph_from_skeleton(skel_img)

    visited_edges = set()
    lines = []

    for i in graph:
        for j in graph[i]:
            edge = tuple(sorted((i, j)))

            if edge in visited_edges:
                continue

            visited_edges.add(edge)

            path = trace_edge(graph, points, i, j, visited_edges)

            if len(path) > 1:
                lines.append(points[path].tolist())

    return lines