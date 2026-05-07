import numpy as np


def extract_strokes(skel_img):

    if skel_img is None:
        return []

    h, w = skel_img.shape

    # ===================== COLLECT POINTS =====================
    points = set()

    for y in range(h):
        for x in range(w):
            if skel_img[y, x] > 0:
                points.add((x, y))

    if len(points) == 0:
        return []

    # ===================== BUILD GRAPH =====================
    graph = {p: [] for p in points}

    directions = [
        (-1,-1),(0,-1),(1,-1),
        (-1,0),       (1,0),
        (-1,1),(0,1),(1,1)
    ]

    for (x, y) in points:
        for dx, dy in directions:
            nb = (x + dx, y + dy)
            if nb in points:
                graph[(x, y)].append(nb)

    # ===================== FIND ENDPOINTS =====================
    endpoints = [p for p in graph if len(graph[p]) == 1]

    visited = set()
    strokes = []

    def trace(start, next_node):
        path = [start, next_node]
        prev = start
        current = next_node

        while True:
            neighbors = graph[current]
            candidates = [n for n in neighbors if n != prev]

            if len(candidates) != 1:
                break

            nxt = candidates[0]

            edge = (current, nxt)
            if edge in visited:
                break

            visited.add((current, nxt))
            visited.add((nxt, current))

            path.append(nxt)
            prev = current
            current = nxt

        return path

    # ===================== TRACE FROM ENDPOINTS =====================
    for ep in endpoints:
        for nb in graph[ep]:
            if (ep, nb) in visited:
                continue
            strokes.append(trace(ep, nb))

    # ===================== HANDLE LOOPS =====================
    for p in graph:
        for nb in graph[p]:
            if (p, nb) in visited:
                continue
            strokes.append(trace(p, nb))

    # ===================== CONVERT =====================
    lines = []
    for stroke in strokes:
        lines.append([(x, y) for (x, y) in stroke])

    return lines  # 🔥 GUARANTEED RETURN