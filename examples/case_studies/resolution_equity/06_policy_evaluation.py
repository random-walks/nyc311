#!/usr/bin/env python3
"""Step 6: Policy evaluation -- changepoints and interrupted time series.

Combines two complementary methods to assess policy impacts on 311
complaint volume:

1. **PELT changepoint detection** (Killick et al., 2012) identifies
   structural breaks in the city-wide monthly complaint series.
2. **Interrupted time series** (Bernal et al., 2017) estimates the
   level and trend changes associated with the rat containerization
   mandate (effective 2024-03-01).
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import (
    interpret_changepoints,
    interpret_its,
)

import pandas as pd

from nyc311.stats import detect_changepoints, interrupted_time_series


def main() -> None:
    panel_path = Path(__file__).parent / "data" / "panel.parquet"
    if not panel_path.exists():
        print("Panel not found. Run 02_build_panel.py first.")
        return

    df = pd.read_parquet(panel_path)
    city_monthly = df.groupby("period")["complaint_count"].sum()
    city_monthly.index = pd.to_datetime(city_monthly.index)
    city_monthly = city_monthly.sort_index()

    # ── 1. Changepoint detection ─────────────────────────────────────
    print("=" * 72)
    print("1. PELT Changepoint Detection")
    print("=" * 72)

    cp_result = detect_changepoints(city_monthly, method="pelt")

    known_events = {
        "COVID-19 lockdown": date(2020, 3, 22),
        "Phase 1 reopening": date(2020, 6, 8),
        "Phase 4 reopening": date(2020, 7, 20),
        "Rat containerization mandate": date(2024, 3, 1),
    }

    print(interpret_changepoints(cp_result, known_events))

    # ── 2. Interrupted time series ───────────────────────────────────
    print("\n" + "=" * 72)
    print("2. Interrupted Time Series: Rat Containerization Mandate")
    print("   Intervention date: 2024-03-01")
    print("=" * 72)

    intervention = date(2024, 3, 1)
    its_result = interrupted_time_series(city_monthly, intervention)

    print(interpret_its(its_result))

    print("\nFull model summary:")
    print(its_result.model_summary)

    # ── Figures ──────────────────────────────────────────────────────
    figures_dir = Path(__file__).parent / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib.pyplot as plt

        # Figure 1: Changepoints
        fig, ax = plt.subplots(figsize=(12, 5))
        city_monthly.plot(ax=ax, label="Monthly complaints", color="steelblue")
        for bp_date in cp_result.breakpoint_dates:
            ax.axvline(pd.Timestamp(bp_date), color="red", linestyle="--", alpha=0.7)
        ax.set_title("City-Wide Monthly 311 Complaints with Detected Changepoints")
        ax.set_ylabel("Complaint Count")
        ax.legend()
        fig.tight_layout()
        fig.savefig(figures_dir / "changepoints.png", dpi=150)
        print(f"\n  Figure saved: {figures_dir / 'changepoints.png'}")
        plt.close(fig)

        # Figure 2: ITS with intervention line
        fig, ax = plt.subplots(figsize=(12, 5))
        city_monthly.plot(ax=ax, label="Monthly complaints", color="steelblue")
        ax.axvline(
            pd.Timestamp(intervention),
            color="darkred",
            linestyle="--",
            linewidth=2,
            label="Rat containerization mandate",
        )

        # Shade pre/post regions
        ax.axvspan(
            city_monthly.index.min(),
            pd.Timestamp(intervention),
            alpha=0.05,
            color="blue",
            label="Pre-intervention",
        )
        ax.axvspan(
            pd.Timestamp(intervention),
            city_monthly.index.max(),
            alpha=0.05,
            color="red",
            label="Post-intervention",
        )

        ax.set_title("Interrupted Time Series: Rat Containerization Mandate")
        ax.set_ylabel("Complaint Count")
        ax.legend(loc="upper left")
        fig.tight_layout()
        fig.savefig(figures_dir / "its_mandate.png", dpi=150)
        print(f"  Figure saved: {figures_dir / 'its_mandate.png'}")
        plt.close(fig)

    except ImportError:
        print("  (matplotlib not available; skipping figures)")


if __name__ == "__main__":
    main()
