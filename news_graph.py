from collections import deque


def build_keyword_graph(text, keywords=None):
    if keywords is None:
        keywords = [
            "government", "president", "minister", "official", "party",
            "election", "vote", "policy", "law", "court", "police",
            "military", "attack", "report", "source", "agency",
            "country", "nation", "people", "public", "statement",
            "economy", "market", "tax", "budget", "health",
            "education", "crime", "protest", "war", "peace",
            "india", "modi", "bjp", "congress", "parliament",
            "supreme", "investigation", "scandal", "corruption",
            "media", "journalist", "killed", "arrested", "crisis"
        ]

    text_lower = text.lower()
    sentences = text_lower.replace("!", ".").replace("?", ".").split(".")

    found_keywords = []
    keyword_freq = {}
    for kw in keywords:
        count = text_lower.count(kw)
        if count > 0:
            found_keywords.append(kw)
            keyword_freq[kw] = count

    graph = {kw: [] for kw in found_keywords}

    for sentence in sentences:
        sentence = sentence.strip()
        present_in_sentence = [kw for kw in found_keywords if kw in sentence]
        for i in range(len(present_in_sentence)):
            for j in range(i + 1, len(present_in_sentence)):
                kw1 = present_in_sentence[i]
                kw2 = present_in_sentence[j]
                if kw2 not in graph[kw1]:
                    graph[kw1].append(kw2)
                if kw1 not in graph[kw2]:
                    graph[kw2].append(kw1)

    return graph, keyword_freq


def bfs_traversal(graph, start):
    if start not in graph:
        return [], {}

    visited = set()
    queue = deque()
    queue.append((start, 0))
    visited.add(start)

    visited_order = []
    levels = {}

    while queue:
        node, level = queue.popleft()
        visited_order.append(node)
        levels[node] = level

        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, level + 1))

    return visited_order, levels


def dfs_traversal(graph, start):
    if start not in graph:
        return [], 0

    visited = set()
    stack = [start]
    visited_order = []
    back_edges = 0

    while stack:
        node = stack.pop()
        if node in visited:
            back_edges += 1
            continue
        visited.add(node)
        visited_order.append(node)

        for neighbor in reversed(graph[node]):
            if neighbor not in visited:
                stack.append(neighbor)
            else:
                back_edges += 1

    return visited_order, back_edges


def analyze_news_structure(text):
    graph, keyword_freq = build_keyword_graph(text)

    if len(graph) == 0:
        return {
            "num_keywords": 0,
            "num_connections": 0,
            "connected_components": 1,
            "max_depth": 0,
            "graph_density": 0.0,
            "structure_score": 0.0,
            "bfs_order": [],
            "dfs_order": [],
            "graph": {},
            "keyword_freq": {}
        }

    total_edges = sum(len(neighbors) for neighbors in graph.values()) // 2

    all_visited = set()
    components = 0
    max_depth = 0

    sorted_kws = sorted(keyword_freq.keys(), key=lambda k: keyword_freq[k], reverse=True)
    bfs_order_full = []

    for kw in sorted_kws:
        if kw not in all_visited:
            components += 1
            order, levels = bfs_traversal(graph, kw)
            bfs_order_full.extend(order)
            all_visited.update(order)
            if levels:
                max_depth = max(max_depth, max(levels.values()))

    dfs_order, back_edges = dfs_traversal(graph, sorted_kws[0])

    n = len(graph)
    max_possible = n * (n - 1) / 2 if n > 1 else 1
    density = total_edges / max_possible

    score = 0.0
    if n > 0:
        score = (min(n, 10) / 10) * 30
        score += min(density, 1.0) * 25
        score += (1.0 / max(components, 1)) * 25
        score += min(max_depth, 3) / 3 * 20

    return {
        "num_keywords": n,
        "num_connections": total_edges,
        "connected_components": components,
        "max_depth": max_depth,
        "graph_density": round(density, 3),
        "structure_score": round(score, 1),
        "bfs_order": bfs_order_full[:15],
        "dfs_order": dfs_order[:15],
        "graph": graph,
        "keyword_freq": keyword_freq
    }
