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
             '<line x1="45" y1="135" x2="755" y2="135" stroke="#999999" stroke-width="2"/>']
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
        parts.append(f'<line x1="{x:.1f}" y1="135" x2="{x:.1f}" y2="{line_end}" stroke="#999999" stroke-dasharray="4 3"/>')
        parts.append(f'<circle cx="{x:.1f}" cy="135" r="6" fill="#555555"/>')
        parts.append(f'<text x="{x:.1f}" y="{date_y}" text-anchor="middle" font-size="14" fill="#666666">{date}</text>')
        parts.append(f'<text x="{x:.1f}" y="{label_y}" text-anchor="middle" font-size="16" fill="#222222">{label}</text>')
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
             '<defs><marker id="diagram-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="none" stroke="#555555" stroke-width="1.5"/></marker></defs>']
    for edge in edges:
        source, target = edge["from"], edge["to"]
        x1, y1 = position[source]
        x2, y2 = position[target]
        parts.append(f'<line x1="{x1:.1f}" y1="{y1 + 26:.1f}" x2="{x2:.1f}" y2="{y2 - 32:.1f}" stroke="#555555" stroke-width="2" marker-end="url(#diagram-arrow)"/>')
        if edge.get("label"):
            parts.append(f'<text x="{(x1 + x2) / 2:.1f}" y="{(y1 + y2) / 2 - 4:.1f}" text-anchor="middle" font-size="13" fill="#666666">{html.escape(edge["label"])}</text>')
    for key, label in labels.items():
        x, y = position[key]
        parts.append(f'<rect x="{x - 90:.1f}" y="{y - 26:.1f}" width="180" height="52" rx="8" fill="#f2f2f2" stroke="#777777" stroke-width="2"/>')
        parts.append(f'<text x="{x:.1f}" y="{y + 5:.1f}" text-anchor="middle" font-size="16" fill="#222222">{html.escape(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _quadrant(data: dict) -> str:
    items = data.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 8:
        raise ValueError("Quadrant needs 1–8 items")
    x_label = html.escape(_text(data.get("x_label"), "x axis", 24))
    y_label = html.escape(_text(data.get("y_label"), "y axis", 24))
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 410" role="img">',
             '<rect x="95" y="25" width="610" height="310" fill="#f2f2f2"/>',
             '<line x1="400" y1="25" x2="400" y2="335" stroke="#999999"/>',
             '<line x1="95" y1="180" x2="705" y2="180" stroke="#999999"/>',
             f'<text x="400" y="385" text-anchor="middle" font-size="16" fill="#222222">{x_label} (low to high)</text>',
             f'<text x="95" y="18" font-size="16" fill="#222222">{y_label} (low to high)</text>']
    cells = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Quadrant item must be an object")
        label = html.escape(_text(item.get("label"), "item label", 20))
        x, y = item.get("x"), item.get("y")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 1 for v in (x, y)):
            raise ValueError("Quadrant x and y must be numbers from 0 to 1")
        cell = (round(x * 6), round(y * 4))
        if cell in cells:
            raise ValueError("Quadrant items are too close; adjust their coordinates")
        cells.add(cell)
        px, py = 95 + 610 * x, 335 - 310 * y
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6" fill="#555555"/>')
        parts.append(f'<text x="{px:.1f}" y="{py - 10:.1f}" text-anchor="middle" font-size="14" fill="#222222">{label}</text>')
    return "".join(parts) + '</svg>'


def _layer_stack(data: dict) -> str:
    layers = data.get("layers")
    if not isinstance(layers, list) or not 2 <= len(layers) <= 6:
        raise ValueError("Layer stack needs 2–6 layers")
    height = 55 + 72 * len(layers)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 {height}" role="img">']
    for index, layer in enumerate(layers):
        if not isinstance(layer, dict):
            raise ValueError("Layer must be an object")
        label = html.escape(_text(layer.get("label"), "layer label", 32))
        detail = html.escape(_text(layer.get("detail"), "layer detail", 55))
        y = 25 + index * 72
        parts.append(f'<rect x="95" y="{y}" width="610" height="58" rx="7" fill="{("#e6e6e6" if index % 2 == 0 else "#f2f2f2")}" stroke="#777777"/>')
        parts.append(f'<text x="115" y="{y + 24}" font-size="17" font-weight="bold" fill="#222222">{label}</text>')
        parts.append(f'<text x="115" y="{y + 44}" font-size="13" fill="#666666">{detail}</text>')
    return "".join(parts) + '</svg>'


def _swimlane(data: dict) -> str:
    lanes = data.get("lanes")
    steps = data.get("steps")
    if not isinstance(lanes, list) or not 2 <= len(lanes) <= 4 or not isinstance(steps, list) or not 2 <= len(steps) <= 6:
        raise ValueError("Swimlane needs 2–4 lanes and 2–6 steps")
    lane_names = [_text(lane, "lane", 22) for lane in lanes]
    if len(set(lane_names)) != len(lane_names):
        raise ValueError("Swimlane lanes must be unique")
    height = 50 + 100 * len(lanes)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 {height}" role="img">']
    for index, lane in enumerate(lane_names):
        y = 25 + index * 100
        parts.append(f'<rect x="25" y="{y}" width="750" height="90" fill="{("#f2f2f2" if index % 2 == 0 else "#ffffff")}" stroke="#cccccc"/>')
        parts.append(f'<text x="38" y="{y + 48}" font-size="15" fill="#222222">{html.escape(lane)}</text>')
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or step.get("lane") not in lane_names:
            raise ValueError("Swimlane step must name a known lane")
        label = html.escape(_text(step.get("label"), "step label", 20))
        x = 200 + index * 530 / max(1, len(steps) - 1)
        y = 25 + lane_names.index(step["lane"]) * 100 + 45
        parts.append(f'<rect x="{x - 38:.1f}" y="{y - 23}" width="76" height="46" rx="6" fill="#e6e6e6" stroke="#777777"/>')
        parts.append(f'<text x="{x:.1f}" y="{y + 5}" text-anchor="middle" font-size="12" fill="#222222">{label}</text>')
        if index:
            prev = steps[index - 1]
            py = 25 + lane_names.index(prev["lane"]) * 100 + 45
            px = 200 + (index - 1) * 530 / max(1, len(steps) - 1)
            parts.append(f'<line x1="{px + 39:.1f}" y1="{py:.1f}" x2="{x - 39:.1f}" y2="{y:.1f}" stroke="#777777" stroke-width="2"/>')
    return "".join(parts) + '</svg>'


def render(raw: str, font_family: str = "Geist") -> str:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid diagram JSON: {error.msg}") from error
    renderers = {"timeline": _timeline, "flowchart": _flowchart, "quadrant": _quadrant,
                 "layer-stack": _layer_stack, "swimlane": _swimlane}
    if not isinstance(data, dict) or data.get("type") not in renderers:
        raise ValueError("Diagram type must be timeline, flowchart, quadrant, layer-stack, or swimlane")
    title = html.escape(_text(data.get("title"), "title", 100))
    svg = renderers[data["type"]](data)
    svg = svg.replace("<text ", f'<text font-family="{html.escape(font_family, quote=True)}" ')
    return f'<figure class="generated-diagram {data["type"]}-diagram" aria-label="{title}"><figcaption>{title}</figcaption>{svg}</figure>'


def replace_diagram_fences(tokens: list[Token], font_family: str = "Geist") -> None:
    for token in tokens:
        if token.type == "fence" and token.info.strip() == "diagram":
            token.type = "html_block"
            token.content = render(token.content, font_family) + "\n"
