# Project Brief

## Problem

NYC 311 has huge public value, but the most important signal often lives in
short, messy text fields and in localized time patterns that are hard to see in
the standard complaint taxonomy.

## Intended Users

- city and agency analysts
- community boards
- journalists
- urban researchers
- civic technologists

## Product Shape

`nyc311` should become a reusable Python package that:

1. loads filtered slices of NYC 311 data
2. extracts fine-grained topics from complaint text
3. surfaces trend, anomaly, and resolution-gap outputs by geography

## Why This Is Worth Building

There are plenty of 311 analyses and notebooks, but there is not an obvious
popular package that turns NYC 311 complaint intelligence into a reusable CLI
and library workflow.

## Positioning

Do not position this as a generic LLM wrapper for civic text.

Position it as a reproducible complaint-intelligence toolkit that helps people
answer questions like:

- what residents are actually complaining about within a broad complaint type
- which topics are emerging in a neighborhood
- where complaint resolution appears to lag behind complaint volume
