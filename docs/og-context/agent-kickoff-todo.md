# Agent Kickoff TODO

> Archived planning note: this page captures the original `v0.1` kickoff plan.
> For the active release framing, use the main docs for the upcoming `0.2.0a1`
> alpha.

## Goal

Get `nyc311` to a solid v0.1 foundation with:

- a clearly defined package surface
- working `NotImplementedError` placeholders wherever implementation has not
  landed yet
- one real happy-path analysis slice
- docs and tests that make the roadmap obvious

## Agent 1: Surface And Contracts

- Review `docs/notes/original-spec.md`, `docs/notes/gap-explination.md`, and
  `docs/mvp-roadmap.md`.
- Expand the package surface so every major concept in the spec has an obvious
  home.
- Keep unbuilt features explicit with typed placeholders and consistent
  `NotImplementedError` messages.
- Add module docstrings and API docs so contributors can see the target shape
  without reading planning notes first.

## Agent 2: Core Complaint Intelligence Happy Path

- Implement the narrowest useful slice of the package:
  - load date- and geography-filtered 311 data
  - cluster topics within one or a few complaint categories
  - aggregate outputs by geography
  - export at least one useful table or GeoJSON artifact
- Prefer transparent classical NLP over premature model complexity.
- Add tests around the first happy path rather than broad speculative
  infrastructure.

## Agent 3: v0.1 Docs, CLI, And Report Flow

- Turn the current placeholder CLI into a documented first command shape, even
  if only one subcommand works.
- Add or outline one notebook or report-card workflow for a community-district
  example.
- Tighten the README so the value proposition, methodology, and first successful
  workflow are immediately obvious.
- Keep the rest of the planned surface scaffolded and clearly marked as future
  work.

## Definition Of Done For The Next Pass

- importing the package shows a coherent target surface
- the happy path is small but real
- missing features fail loudly and consistently
- docs tell a contributor exactly what exists now versus later
