#!/usr/bin/env python3
"""Step 3: STL seasonal decomposition of city-wide complaint series.

Decomposes monthly complaint totals into trend, seasonal, and residual
components (Cleveland et al., 1990).
"""

from pathlib import Path

import pandas as pd

from nyc311.stats import seasonal_decompose


def main() -> None:
    panel_path = Path(__file__).parent / "data" / "panel.parquet"
    if not panel_path.exists():
        print("Panel not found. Run 02_build_panel.py first.")
        return

    df = pd.read_parquet(panel_path)
    city_monthly = df.groupby("period")["complaint_count"].sum()
    city_monthly.index = pd.to_datetime(city_monthly.index)
    city_monthly = city_monthly.sort_index()

    print("Running STL decomposition (period=12) ...")
    result = seasonal_decompose(city_monthly, period=12)

    print(f"  Trend range: {result.trend.min():.0f} -- {result.trend.max():.0f}")
    print(f"  Seasonal amplitude: {result.seasonal.max() - result.seasonal.min():.0f}")
    print(f"  Residual std: {result.residual.std():.1f}")

    figures_dir = Path(__file__).parent / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
        city_monthly.plot(ax=axes[0], title="Observed")
        result.trend.plot(ax=axes[1], title="Trend")
        result.seasonal.plot(ax=axes[2], title="Seasonal")
        result.residual.plot(ax=axes[3], title="Residual")
        fig.tight_layout()
        fig.savefig(figures_dir / "stl_decomposition.png", dpi=150)
        print(f"\n  Figure saved: {figures_dir / 'stl_decomposition.png'}")
        plt.close(fig)
    except ImportError:
        print("  (matplotlib not available; skipping figure)")


if __name__ == "__main__":
    main()
