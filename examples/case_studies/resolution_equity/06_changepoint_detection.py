#!/usr/bin/env python3
"""Step 6: Changepoint detection for structural breaks.

Applies the PELT algorithm (Killick et al., 2012) to city-wide monthly
complaint volume to identify structural breaks corresponding to known
events (COVID-19 lockdown, reopening phases, policy changes).
"""

from pathlib import Path

import pandas as pd

from nyc311.stats import detect_changepoints


def main() -> None:
    panel_path = Path(__file__).parent / "data" / "panel.parquet"
    if not panel_path.exists():
        print("Panel not found. Run 02_build_panel.py first.")
        return

    df = pd.read_parquet(panel_path)
    city_monthly = df.groupby("period")["complaint_count"].sum()
    city_monthly.index = pd.to_datetime(city_monthly.index)
    city_monthly = city_monthly.sort_index()

    print("Running PELT changepoint detection ...")
    result = detect_changepoints(city_monthly, method="pelt")

    print(f"  Segments: {result.n_segments}")
    print(f"  Penalty: {result.penalty:.2f}")
    print(f"  Breakpoints: {len(result.breakpoints)}")

    known_events = {
        "COVID-19 lockdown": "2020-03-22",
        "Phase 1 reopening": "2020-06-08",
        "Phase 4 reopening": "2020-07-20",
        "Rat containerization mandate": "2024-03-01",
    }

    for bp_date in result.breakpoint_dates:
        nearest_event = None
        min_delta = 90
        for name, event_date in known_events.items():
            delta = abs((bp_date - pd.Timestamp(event_date).date()).days)
            if delta < min_delta:
                min_delta = delta
                nearest_event = name
        label = f" <- {nearest_event} ({min_delta}d)" if nearest_event else ""
        print(f"  {bp_date.isoformat()}{label}")

    # Export
    figures_dir = Path(__file__).parent / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(12, 5))
        city_monthly.plot(ax=ax, label="Monthly complaints", color="steelblue")
        for bp_date in result.breakpoint_dates:
            ax.axvline(pd.Timestamp(bp_date), color="red", linestyle="--", alpha=0.7)
        ax.set_title("City-Wide Monthly 311 Complaints with Detected Changepoints")
        ax.set_ylabel("Complaint Count")
        ax.legend()
        fig.tight_layout()
        fig.savefig(figures_dir / "changepoints.png", dpi=150)
        print(f"\n  Figure saved: {figures_dir / 'changepoints.png'}")
        plt.close(fig)
    except ImportError:
        print("  (matplotlib not available; skipping figure)")


if __name__ == "__main__":
    main()
