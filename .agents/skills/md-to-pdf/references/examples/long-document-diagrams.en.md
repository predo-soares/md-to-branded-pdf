---
template: long-document
lang: en
---
# Synthetic Process Notes

## Timeline

The dates and names below are fictional.

```diagram
{"type":"timeline","title":"Sample project milestones","events":[{"date":"Jan","label":"Draft"},{"date":"Feb","label":"Review"},{"date":"Mar","label":"Trial"},{"date":"Apr","label":"Decision"}]}
```

## Flowchart

The branches show a possible review path, not a real operating process.

```diagram
{"type":"flowchart","title":"Sample review path","nodes":[{"id":"start","label":"Receive draft"},{"id":"review","label":"Review evidence"},{"id":"revise","label":"Revise"},{"id":"approve","label":"Approve"}],"edges":[{"from":"start","to":"review"},{"from":"review","to":"revise","label":"Needs work"},{"from":"review","to":"approve","label":"Ready"}]}
```
