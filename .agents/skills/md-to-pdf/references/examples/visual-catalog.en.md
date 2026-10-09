---
template: long-document
lang: en
---
# Synthetic Visual Catalog

All values and process names in this document are synthetic.

## Donut chart

```chart
{"type":"donut","title":"Sample allocation","unit":" tasks","data":[{"label":"Design","value":4},{"label":"Build","value":6},{"label":"Review","value":2}]}
```

## Waterfall chart

```chart
{"type":"waterfall","title":"Sample change in tasks","unit":" tasks","data":[{"label":"Added","value":8},{"label":"Removed","value":-3},{"label":"Revised","value":2}]}
```

## Quadrant

```diagram
{"type":"quadrant","title":"Sample priority map","x_label":"Effort","y_label":"Impact","items":[{"label":"Option A","x":0.25,"y":0.78},{"label":"Option B","x":0.72,"y":0.68},{"label":"Option C","x":0.35,"y":0.22}]}
```

## Layer stack

```diagram
{"type":"layer-stack","title":"Sample service layers","layers":[{"label":"Interface","detail":"Presentation and controls"},{"label":"Logic","detail":"Rules and coordination"},{"label":"Data","detail":"Storage and retrieval"}]}
```

## Swimlane

```diagram
{"type":"swimlane","title":"Sample review handoff","lanes":["Author","Reviewer","Owner"],"steps":[{"lane":"Author","label":"Draft"},{"lane":"Reviewer","label":"Review"},{"lane":"Author","label":"Revise"},{"lane":"Owner","label":"Approve"}]}
```
