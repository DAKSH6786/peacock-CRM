"""Content Strategy relationship graph.

    Brand -> Topic -> Subtopic -> Entity -> Keyword -> Search Query ->
    AI Prompt -> Content Page

Every node is built from real inputs already computed elsewhere in Peacock
One (crawled headings/entities, the LLM Keyword Map, AI Visibility Command
Center queries, and the client's own crawled pages) — the *edges* connecting
them are a deterministic content-planning heuristic (ordinal pairing / text
containment), not a claim of measured semantic distance.
"""

from __future__ import annotations

from content_intelligence.models import ContentGraph, ContentGraphEdge, ContentGraphNode


def _slug(text: str) -> str:
    return "_".join(text.lower().split())[:60]


def build_content_graph(
    *,
    brand: str,
    topics: list[str],
    entities: list[str],
    keywords: list[str],
    queries: list[tuple[str, str]],  # (query_text, intent)
    pages: list[tuple[str, str]],  # (url, title)
) -> ContentGraph:
    nodes: list[ContentGraphNode] = []
    edges: list[ContentGraphEdge] = []
    seen: set[tuple[str, str]] = set()

    def add_node(kind: str, label: str) -> str:
        key = _slug(label) or kind
        if (kind, key) not in seen:
            seen.add((kind, key))
            nodes.append(ContentGraphNode(kind=kind, key=key, label=label))
        return key

    def add_edge(from_kind: str, from_key: str, to_kind: str, to_key: str) -> None:
        edges.append(ContentGraphEdge(from_kind=from_kind, from_key=from_key, to_kind=to_kind, to_key=to_key))

    brand_key = add_node("brand", brand)

    topic_keys = [add_node("topic", t) for t in topics[:8]]
    for tk in topic_keys:
        add_edge("brand", brand_key, "topic", tk)

    # Pair consecutive topics as topic -> subtopic for a lightweight hierarchy.
    subtopic_keys: list[str] = []
    for i, t in enumerate(topics[:8]):
        if i + 1 < len(topics):
            sub_label = topics[i + 1]
            sub_key = add_node("subtopic", sub_label)
            subtopic_keys.append(sub_key)
            add_edge("topic", topic_keys[i], "subtopic", sub_key)

    entity_keys = [add_node("entity", e) for e in entities[:10]]
    anchor_topics = subtopic_keys or topic_keys
    # Connect each topic to a slice of entities (round-robin) for a usable, non-empty graph.
    for i, ek in enumerate(entity_keys):
        if anchor_topics:
            parent_kind = "subtopic" if subtopic_keys else "topic"
            add_edge(parent_kind, anchor_topics[i % len(anchor_topics)], "entity", ek)

    keyword_keys = [add_node("keyword", k) for k in keywords[:12]]
    for i, kk in enumerate(keyword_keys):
        if entity_keys:
            add_edge("entity", entity_keys[i % len(entity_keys)], "keyword", kk)

    query_keys: list[str] = []
    prompt_keys: list[str] = []
    for query_text, intent in queries[:8]:
        qk = add_node("query", query_text)
        pk = add_node("prompt", f"[{intent}] {query_text}")
        query_keys.append(qk)
        prompt_keys.append(pk)
        if keyword_keys:
            add_edge("keyword", keyword_keys[len(query_keys) % len(keyword_keys)], "query", qk)
        add_edge("query", qk, "prompt", pk)

    page_keys = [add_node("page", title or url) for url, title in pages[:10]]
    for i, pgk in enumerate(page_keys):
        if prompt_keys:
            add_edge("prompt", prompt_keys[i % len(prompt_keys)], "page", pgk)

    return ContentGraph(nodes=nodes, edges=edges)
