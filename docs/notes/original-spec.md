# Original Spec Notes

## One-Liner

NLP pipeline that turns NYC 311 complaint records into structured intelligence by extracting topics, detecting anomalies, and surfacing gaps between what residents report and what agencies resolve.

## Core Idea

The package should move beyond the built-in complaint taxonomy and help users understand what is happening inside broad complaint categories and where those patterns are changing over time.

## Expected Library Surface

- Socrata-backed data loading
- complaint text topic extraction
- temporal anomaly detection
- geography-aware aggregations and exports
- CLI and notebook workflows

## Key Technical Choices

- start with TF-IDF plus clustering
- keep methods interpretable
- handle noisy short text carefully
- favor reproducibility over flashy model complexity

## Intended Showcase Value

This project is meant to demonstrate:

- practical NLP on messy public-sector text
- integration of text, time, and geography
- public, reusable analytical tooling
- thoughtful framing for decision-makers rather than a pure demo
