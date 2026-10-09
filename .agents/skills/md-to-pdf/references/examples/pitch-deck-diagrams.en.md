---
template: pitch-deck
lang: en
---
# Synthetic Process Deck

PDF diagram layout fixture.

---

## A short sequence makes progress visible

```diagram
{"type":"timeline","title":"Sample project milestones","events":[{"date":"Jan","label":"Draft"},{"date":"Feb","label":"Review"},{"date":"Mar","label":"Trial"},{"date":"Apr","label":"Decision"}]}
```

---

## A review leads to two possible actions

```diagram
{"type":"flowchart","title":"Sample review path","nodes":[{"id":"start","label":"Receive draft"},{"id":"review","label":"Review evidence"},{"id":"revise","label":"Revise"},{"id":"approve","label":"Approve"}],"edges":[{"from":"start","to":"review"},{"from":"review","to":"revise","label":"Needs work"},{"from":"review","to":"approve","label":"Ready"}]}
```

---

## Next step

Review source evidence before applying this diagram to a real process.
