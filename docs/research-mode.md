# Peacock Research Mode

Experimental method in the product — a **search intelligence laboratory** for serious enterprise users.

Moves Peacock from SEO software toward controlled analyses.

## Example research question

> Does adding proprietary statistics increase AI citation probability?

## What Peacock can do

| Phase | Capability |
| --- | --- |
| Hypothesis | Define a testable claim |
| Metric | Choose a research metric (e.g. AI citation probability) |
| Pages | Select treatment + control pages |
| Prompts | Select prompt set / clusters |
| Baseline | Collect baseline observations |
| Treatment | Measure after intervention |
| Repeat observations | Multiple rounds |
| Uncertainty | Band + rationale (not fake certainty) |
| Findings | Verdict + evidence + next step |

Completed phases are recorded on every study.

## Caution

Research Mode **does not** auto-conclude that treatment caused the lift. Findings include uncertainty and `auto_causal_conclusion_rejected=true`.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/research-mode/catalog` | Phases, metrics, verdicts, warnings |
| `GET` | `/research-mode/preview` | Demo study for the example question |
| `POST` | `/research-mode/studies` | Run / persist a controlled study |
| `GET` | `/research-mode/studies/{id}` | Retrieve study |

## UI

`/research` — Peacock Research Mode laboratory surface (linked from Command Centre)

## Tables

`research_studies`, `rm_pages`, `rm_prompts`, `rm_observations`, `rm_findings`
