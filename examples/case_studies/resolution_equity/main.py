"""Entry point for the resolution-equity case study.

This shim satisfies the ``examples/`` contract documented in
``docs/examples.md`` (one ``main.py`` per example) while keeping the real
analysis in ``run_analysis.py`` so the numbered scripts remain runnable
on their own.
"""

from __future__ import annotations

from run_analysis import main

if __name__ == "__main__":
    main()
