"""Adapt Kami timeline/flowchart composition ideas to project-owned SVG output.

Upstream attribution and MIT terms: assets/diagrams/KAMI-MIT-NOTICE.txt.
The palette, type, and data-to-geometry implementation here are project-owned.
"""
from __future__ import annotations

import html
import json
from collections import deque

from markdown_it.token import Token


def _text(value: object, name: str, limit: int = 32) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValueError(f"Diagram {name} must be 1–{limit} characters")
    return value.strip()


def _timeline(data: dict) -> str:
    events = data.get("events")
    if not isinstance(events, list) or not 2 <= len(events) <= 6:
        raise ValueError("Timeline needs 2–6 events")
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 270" role="img">',
             '<line x1="45" y1="135" x2="755" y2="135" stroke="#8695a1" stroke-width="2"/>']
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError("Timeline event must be an object")
        date = html.escape(_text(event.get("date"), "date", 18))
        label = html.escape(_text(event.get("label"), "label", 24))
        x = 75 + 650 * index / (len(events) - 1)
        upper = index % 2 == 0
        line_end = 63 if upper else 207
        date_y = 48 if upper else 225
        label_y = 68 if upper else 245
        parts.append(f'<line x1="{x:.1f}" y1="135" x2="{x:.1f}" y2="{line_end}" stroke="#8695a1" stroke-dasharray="4 3"/>')
        parts.append(f'<circle cx="{x:.1f}" cy="135" r="6" fill="#245a7a"/>')
        parts.append(f'<text x="{x:.1f}" y="{date_y}" text-anchor="middle" font-size="14" fill="#52606c">{date}</text>')
        parts.append(f'<text x="{x:.1f}" y="{label_y}" text-anchor="middle" font-size="16" fill="#18212b">{label}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _flowchart(data: dict) -> str:
    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(nodes, list) or not 2 <= len(nodes) <= 6 or not isinstance(edges, list) or not edges:
        raise ValueError("Flowchart needs 2–6 nodes and at least one edge")
    labels = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("Flowchart node must be an object")
        key = _text(node.get("id"), "node id", 20)
        if key in labels:
            raise ValueError(f"Duplicate flowchart node id: {key}")
        labels[key] = _text(node.get("label"), "node label", 24)
    incoming = {key: 0 for key in labels}
    adjacency = {key: [] for key in labels}
    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("Flowchart edge must be an object")
        source, target = edge.get("from"), edge.get("to")
        if source not in labels or target not in labels or source == target:
            raise ValueError("Flowchart edge must connect two distinct known nodes")
        adjacency[source].append(target)
        incoming[target] += 1
        if "label" in edge:
            _text(edge["label"], "edge label", 16)
    queue = deque(key for key in labels if incoming[key] == 0)
    depth = {key: 0 for key in queue}
    visited = 0
    while queue:
        key = queue.popleft()
        visited += 1
        for target in adjacency[key]:
            depth[target] = max(depth.get(target, 0), depth[key] + 1)
            incoming[target] -= 1
            if incoming[target] == 0:
                queue.append(target)
    if visited != len(labels):
        raise ValueError("Flowchart connections must be acyclic")
    layers = {}
    for key in labels:
        layers.setdefault(depth[key], []).append(key)
    max_depth = max(layers)
    height = max(290, 120 + 125 * max_depth)
    position = {}
    for level, keys in layers.items():
        for index, key in enumerate(keys):
            position[key] = (800 * (index + 1) / (len(keys) + 1), 65 + 125 * level)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 {height}" role="img">',
             '<defs><marker id="diagram-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="none" stroke="#245a7a" stroke-width="1.5"/></marker></defs>']
    for edge in edges:
        source, target = edge["from"], edge["to"]
        x1, y1 = position[source]
        x2, y2 = position[target]
        parts.append(f'<line x1="{x1:.1f}" y1="{y1 + 26:.1f}" x2="{x2:.1f}" y2="{y2 - 32:.1f}" stroke="#245a7a" stroke-width="2" marker-end="url(#diagram-arrow)"/>')
        if edge.get("label"):
            parts.append(f'<text x="{(x1 + x2) / 2:.1f}" y="{(y1 + y2) / 2 - 4:.1f}" text-anchor="middle" font-size="13" fill="#52606c">{html.escape(edge["label"])}</text>')
    for key, label in labels.items():
        x, y = position[key]
        parts.append(f'<rect x="{x - 90:.1f}" y="{y - 26:.1f}" width="180" height="52" rx="8" fill="#f2f6f8" stroke="#245a7a" stroke-width="2"/>')
        parts.append(f'<text x="{x:.1f}" y="{y + 5:.1f}" text-anchor="middle" font-size="16" fill="#18212b">{html.escape(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def render(raw: str) -> str:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid diagram JSON: {error.msg}") from error
    if not isinstance(data, dict) or data.get("type") not in {"timeline", "flowchart"}:
        raise ValueError("Diagram type must be timeline or flowchart")
    title = html.escape(_text(data.get("title"), "title", 100))
    svg = _timeline(data) if data["type"] == "timeline" else _flowchart(data)
    return f'<figure class="generated-diagram {data["type"]}-diagram" aria-label="{title}"><figcaption>{title}</figcaption>{svg}</figure>'


def replace_diagram_fences(tokens: list[Token]) -> None:
    for token in tokens:
        if token.type == "fence" and token.info.strip() == "diagram":
            token.type = "html_block"
            token.content = render(token.content) + "\n"
