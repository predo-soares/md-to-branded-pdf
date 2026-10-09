---
template: long-document
lang: en
---
# Project Atlas Research Note

This synthetic document demonstrates a report with chapters, a figure, a table, and a reference link. The names and values are invented for layout testing.

## 1. Context

The project team observed a long first-run path in a fictional product. This note describes how a small research effort could identify the points where new users need more context. The proposed work uses interviews, task observation, and a review of existing support material. Each method answers a different question, and the findings are kept separate until the team compares them.

The first chapter establishes the audience and the task. A new user arrives with a goal, reads a short introduction, and then chooses a starting action. The study records whether that choice is clear. It also records places where labels, instructions, or page structure cause hesitation. This description is intentionally generic; it does not claim a result for a real organization.

The team then prepares a small set of realistic scenarios. The scenarios include a straightforward task, a task with unfamiliar terminology, and a task that requires finding help. Participants are asked to explain what they expect before they act. The moderator records the visible outcome and avoids correcting the participant during the task.

## 2. Method

The study combines short interviews with observed tasks. Interview questions ask about the participant's goal and prior experience. Observed tasks focus on what the interface makes possible without extra explanation. The team can compare these notes with a [methods reference](https://example.org/methods) while keeping source observations distinct from interpretation.

![Three-stage synthetic research flow](figure.svg)
*Figure 1. A synthetic sequence from interview to observation to synthesis.*

| Stage | Input | Output |
| --- | --- | --- |
| Interview | Participant goal | Goal statement |
| Observation | Task attempt | Notes on friction |
| Synthesis | Tagged notes | Questions for design |

The table summarizes the artifacts produced at each stage. It is not a claim that the activities have already happened. The team can adjust the schedule if recruitment takes longer than expected, while preserving the distinction between evidence and interpretation. Each interview note has a source identifier so later summaries remain traceable.

The observation session uses the same scenario wording for each participant. A facilitator notes where the participant pauses, what they say, and which screen they inspect. The team avoids inferring intent from a pause alone. After each session, the notes are reviewed for missing context before anyone writes a recommendation.

### Evidence handling

Each note receives a synthetic identifier and a short description of the task context. The team records direct observations separately from later interpretations. If a participant changes direction, the record includes the visible action and the explanation they gave, without assigning a motive that was not stated.

| Evidence type | Example record | Limit |
| --- | --- | --- |
| Screen action | Opened the help panel | Does not explain intent alone |
| Spoken comment | Asked what a label meant | Depends on scenario wording |
| Task outcome | Reached the sample end state | Does not measure long-term use |

The review includes contrary examples. If one participant moves through the same step without hesitation, that case remains in the summary. This makes the later recommendation easier to challenge and reduces the chance that the report overstates a small pattern.

## 3. Synthesis and next steps

The team groups observations by task and by the kind of help a participant sought. A pattern is recorded only when its supporting notes can be found. Conflicting observations remain visible rather than being averaged away. The resulting summary identifies candidate changes, the evidence behind each candidate, and the questions still open.

The first recommendation might simplify one step in the onboarding path. Another might change terminology or move help text closer to the decision point. Each recommendation is framed as a hypothesis for a follow-up test. The document closes with a review of what was learned, what remains uncertain, and which small experiment should happen next.

For a later iteration, the team can add more chapters without changing the paper size or reducing typography. New sections follow the same hierarchy and paginate naturally. Tables repeat their headers when they continue on a later page, and figures stay together where the renderer supports that behavior.

## 4. Review questions

Before sharing the note, the team checks that every conclusion has a supporting observation, every link points to the intended source, and all synthetic values are labeled as examples. A reviewer can then mark a finding as supported, uncertain, or out of scope. The final recommendation should be small enough to test without assuming that the first study settled the broader problem.
