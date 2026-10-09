"""Render deterministic, accessible charts from JSON Markdown fences."""
from __future__ import annotations

import html
import json
import math

from markdown_it.token import Token


def _number(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("Chart values must be finite non-negative numbers")
    return str(value)


def _parse(raw: str) -> dict:
    try:
        chart = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid chart JSON: {error.msg}") from error
    if not isinstance(chart, dict) or chart.get("type") not in {"bar", "line", "metric"}:
        raise ValueError("Chart type must be bar, line, or metric")
    if not isinstance(chart.get("title"), str) or not chart["title"].strip():
        raise ValueError("Chart title must be a non-empty string")
    data = chart.get("data")
    if not isinstance(data, list) or not data:
        raise ValueError("Chart data must contain at least one item")
    if len(data) > 12:
        raise ValueError("Chart data is too dense: use at most 12 items per chart")
    for item in data:
        if not isinstance(item, dict) or not isinstance(item.get("label"), str) or not item["label"].strip():
            raise ValueError("Each chart item needs a non-empty label")
        _number(item.get("value"))
    if len({item["label"] for item in data}) != len(data):
        raise ValueError("Chart labels must be unique")
    if "unit" in chart and not isinstance(chart["unit"], str):
        raise ValueError("Chart unit must be a string")
    return chart


def render(raw: str) -> str:
    chart = _parse(raw)
    kind = chart["type"]
    data = chart["data"]
    title = html.escape(chart["title"])
    unit = html.escape(chart.get("unit", ""))
    if kind == "metric":
        items = "".join(f'<div class="metric"><strong>{html.escape(_number(item["value"]))}{unit}</strong>'
                        f'<span>{html.escape(item["label"])}</span></div>' for item in data)
        return f'<figure class="generated-chart metric-chart" role="img" aria-label="{title}"><figcaption>{title}</figcaption><div class="metrics">{items}</div></figure>'
    maximum = max(item["value"] for item in data) or 1
    width = 800
    height = 310
    left, right, top, bottom = 65, 25, 25, 75
    plot_width = width - left - right
    plot_height = height - top - bottom
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">',
             f'<line x1="{left}" y1="{top + plot_height}" x2="{width - right}" y2="{top + plot_height}" stroke="#52606c"/>']
    positions = []
    for index, item in enumerate(data):
        x = left + plot_width * (index + 0.5) / len(data)
        y = top + plot_height * (1 - item["value"] / maximum)
        positions.append((x, y))
        label = html.escape(item["label"])
        value = html.escape(_number(item["value"]) + chart.get("unit", ""))
        if kind == "bar":
            bar_width = plot_width / len(data) * 0.58
            parts.append(f'<rect x="{x - bar_width / 2:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{top + plot_height - y:.1f}" fill="#245a7a"/>')
        parts.append(f'<text x="{x:.1f}" y="{max(14, y - 8):.1f}" text-anchor="middle" font-size="14" fill="#18212b">{value}</text>')
        parts.append(f'<text x="{x:.1f}" y="{height - 34}" text-anchor="middle" font-size="13" fill="#18212b">{label}</text>')
    if kind == "line":
        points = " ".join(f"{x:.1f},{y:.1f}" for x, y in positions)
        parts.append(f'<polyline points="{points}" fill="none" stroke="#245a7a" stroke-width="4"/>')
        parts.extend(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#245a7a"/>' for x, y in positions)
    parts.append("</svg>")
    return (f'<figure class="generated-chart {kind}-chart"><figcaption>{title}</figcaption>'
            + "".join(parts) + "</figure>")


def replace_chart_fences(tokens: list[Token]) -> None:
    for token in tokens:
        if token.type == "fence" and token.info.strip() == "chart":
            token.type = "html_block"
            token.content = render(token.content) + "\n"
