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
    if not isinstance(chart, dict) or chart.get("type") not in {"bar", "line", "metric", "donut", "waterfall"}:
        raise ValueError("Chart type must be bar, line, metric, donut, or waterfall")
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
        if chart["type"] == "waterfall":
            value = item.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Waterfall values must be finite numbers")
        else:
            _number(item.get("value"))
    if len({item["label"] for item in data}) != len(data):
        raise ValueError("Chart labels must be unique")
    if "unit" in chart and not isinstance(chart["unit"], str):
        raise ValueError("Chart unit must be a string")
    if chart["type"] == "donut" and sum(item["value"] for item in data) <= 0:
        raise ValueError("Donut chart total must be positive")
    return chart


def render(raw: str, font_family: str = "Geist") -> str:
    chart = _parse(raw)
    kind = chart["type"]
    data = chart["data"]
    title = html.escape(chart["title"])
    unit = html.escape(chart.get("unit", ""))
    if kind == "metric":
        items = "".join(f'<div class="metric"><strong>{html.escape(_number(item["value"]))}{unit}</strong>'
                        f'<span>{html.escape(item["label"])}</span></div>' for item in data)
        return f'<figure class="generated-chart metric-chart" role="img" aria-label="{title}"><figcaption>{title}</figcaption><div class="metrics">{items}</div></figure>'
    if kind == "donut":
        total = sum(item["value"] for item in data)
        palette = ("#444444", "#555555", "#666666", "#777777", "#888888", "#999999", "#aaaaaa", "#bbbbbb", "#cccccc", "#777777", "#888888", "#999999")
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 360" role="img">']
        offset = 0.0
        for index, item in enumerate(data):
            fraction = item["value"] / total
            if fraction:
                parts.append(f'<circle cx="205" cy="180" r="100" fill="none" stroke="{palette[index]}" stroke-width="56" stroke-dasharray="{fraction * 628.319:.3f} 628.319" stroke-dashoffset="{-offset * 628.319:.3f}" transform="rotate(-90 205 180)"/>')
            offset += fraction
            y = 35 + index * 26
            parts.append(f'<rect x="360" y="{y - 12}" width="14" height="14" fill="{palette[index]}"/>')
            parts.append(f'<text x="384" y="{y}" font-size="14" fill="#222222">{html.escape(item["label"])}: {html.escape(_number(item["value"]) + chart.get("unit", ""))}</text>')
        parts.append('</svg>')
        svg = "".join(parts).replace("<text ", f'<text font-family="{html.escape(font_family, quote=True)}" ')
        return f'<figure class="generated-chart donut-chart"><figcaption>{title}</figcaption>{svg}</figure>'
    if kind == "waterfall":
        totals = [0]
        for item in data:
            totals.append(totals[-1] + item["value"])
        low, high = min(totals), max(totals)
        span = high - low or 1
        left, top, plot_width, plot_height = 65, 25, 710, 210
        def y(value: float) -> float:
            return top + plot_height * (high - value) / span
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 310" role="img">']
        zero = y(0)
        parts.append(f'<line x1="{left}" y1="{zero:.1f}" x2="775" y2="{zero:.1f}" stroke="#999999"/>')
        step = plot_width / len(data)
        for index, item in enumerate(data):
            x = left + step * (index + .5)
            y1, y2 = y(totals[index]), y(totals[index + 1])
            parts.append(f'<rect x="{x - step * .29:.1f}" y="{min(y1,y2):.1f}" width="{step * .58:.1f}" height="{max(abs(y2-y1), 1):.1f}" fill="{("#555555" if item["value"] >= 0 else "#999999")}"/>')
            if index + 1 < len(data):
                parts.append(f'<line x1="{x + step * .29:.1f}" y1="{y2:.1f}" x2="{x + step * .71:.1f}" y2="{y2:.1f}" stroke="#999999" stroke-dasharray="3 3"/>')
            parts.append(f'<text x="{x:.1f}" y="{max(15, min(y1,y2) - 7):.1f}" text-anchor="middle" font-size="14" fill="#222222">{html.escape(str(item["value"]) + chart.get("unit", ""))}</text>')
            parts.append(f'<text x="{x:.1f}" y="276" text-anchor="middle" font-size="13" fill="#222222">{html.escape(item["label"])}</text>')
        parts.append('</svg>')
        svg = "".join(parts).replace("<text ", f'<text font-family="{html.escape(font_family, quote=True)}" ')
        return f'<figure class="generated-chart waterfall-chart"><figcaption>{title}</figcaption>{svg}</figure>'
    maximum = max(item["value"] for item in data) or 1
    width = 800
    height = 310
    left, right, top, bottom = 65, 25, 25, 75
    plot_width = width - left - right
    plot_height = height - top - bottom
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">',
             f'<line x1="{left}" y1="{top + plot_height}" x2="{width - right}" y2="{top + plot_height}" stroke="#666666"/>']
    positions = []
    for index, item in enumerate(data):
        x = left + plot_width * (index + 0.5) / len(data)
        y = top + plot_height * (1 - item["value"] / maximum)
        positions.append((x, y))
        label = html.escape(item["label"])
        value = html.escape(_number(item["value"]) + chart.get("unit", ""))
        if kind == "bar":
            bar_width = plot_width / len(data) * 0.58
            parts.append(f'<rect x="{x - bar_width / 2:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{top + plot_height - y:.1f}" fill="#555555"/>')
        parts.append(f'<text x="{x:.1f}" y="{max(14, y - 8):.1f}" text-anchor="middle" font-size="14" fill="#222222">{value}</text>')
        parts.append(f'<text x="{x:.1f}" y="{height - 34}" text-anchor="middle" font-size="13" fill="#222222">{label}</text>')
    if kind == "line":
        points = " ".join(f"{x:.1f},{y:.1f}" for x, y in positions)
        parts.append(f'<polyline points="{points}" fill="none" stroke="#555555" stroke-width="4"/>')
        parts.extend(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#555555"/>' for x, y in positions)
    parts.append("</svg>")
    svg = "".join(parts).replace("<text ", f'<text font-family="{html.escape(font_family, quote=True)}" ')
    return (f'<figure class="generated-chart {kind}-chart"><figcaption>{title}</figcaption>'
            + svg + "</figure>")


def replace_chart_fences(tokens: list[Token], font_family: str = "Geist") -> None:
    for token in tokens:
        if token.type == "fence" and token.info.strip() == "chart":
            token.type = "html_block"
            token.content = render(token.content, font_family) + "\n"
