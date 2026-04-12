#!/usr/bin/env python3
"""Step 7: Compile all results into FINDINGS.md and analysis_results.json."""

from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import (
    compile_findings_md,
    interpret_event_study,
    interpret_power,
    interpret_rdd,
    interpret_staggered_did,
    interpret_synthetic_control,
)

DATA_DIR = Path(__file__).parent / "data"
FINDINGS_PATH = Path(__file__).parent / "FINDINGS.md"


def _serialize(obj: Any) -> Any:
    """Make an object JSON-serializable."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _serialize(getattr(obj, k)) for k in obj.__dataclass_fields__}
    if isinstance(obj, dict):
        return {str(k): _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(i) for i in obj]
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


def format_p_str(p: float) -> str:
    """Short p-value string for summary bullets."""
    if p < 0.001:
        return "p < 0.001"
    return f"p = {p:.3f}"


def run(results: dict) -> str:
    """Generate FINDINGS.md and JSON output."""
    sections: list[tuple[str, str]] = []

    # Panel summary
    panel = results.get("panel")
    if panel:
        sections.append(
            (
                "Data",
                f"Real NYC 311 Rodent complaint data fetched from NYC Open Data "
                f"(Socrata dataset erm2-nwe9). Balanced panel: "
                f"{len(panel.unit_ids)} community districts x "
                f"{len(panel.periods)} monthly periods "
                f"({len(panel.observations)} observations total). "
                f"Treatment: rat containerization mandate pilot applied to "
                f"{len(panel.treatment_events[0].treated_units)} Manhattan districts "
                f"beginning {panel.treatment_events[0].treatment_date}.",
            )
        )

    # Descriptive
    desc = results.get("descriptive")
    if desc:
        sections.append(
            (
                "Descriptive Profile",
                f"{desc['n_records']:,} rodent complaints analyzed "
                f"({desc['n_resolved']:,} resolved, "
                f"{desc['resolution_rate']:.1%} resolution rate).\n\n"
                f"Factor pipeline (mean across all district-month cells): "
                f"complaint volume = {desc['mean_volume']:.1f}, "
                f"response rate = {desc['mean_response_rate']:.3f}, "
                f"topic concentration (HHI) = {desc['mean_topic_concentration']:.4f}, "
                f"recurrence rate = {desc['mean_recurrence_rate']:.3f}.",
            )
        )

    # Temporal
    temporal = results.get("temporal")
    if temporal:
        stl = temporal.get("stl", {})
        anom = temporal.get("anomalies", {})
        cp = temporal.get("changepoints", {})
        parts = []
        if stl:
            parts.append(
                f"STL decomposition reveals peak rodent complaints in "
                f"{stl.get('peak_month', '?')} and a trough in "
                f"{stl.get('trough_month', '?')} "
                f"(seasonal amplitude: {stl.get('seasonal_amplitude', 0):,.0f})."
            )
        if anom:
            n = anom.get("n_anomalies", 0)
            if n > 0:
                dates = ", ".join(anom.get("dates", [])[:5])
                parts.append(f"{n} anomalous month(s) detected: {dates}.")
            else:
                parts.append("No anomalous months detected.")
        if cp:
            n_bp = cp.get("n_breakpoints", 0)
            bp_dates = ", ".join(cp.get("breakpoint_dates", []))
            parts.append(
                f"PELT changepoint detection identified {n_bp} structural "
                f"break(s): {bp_dates}."
                if n_bp > 0
                else "No structural breaks detected."
            )
        sections.append(("Temporal Patterns", "\n\n".join(parts)))

    # Spatial
    spatial = results.get("spatial")
    if spatial:
        parts = []
        mi = spatial.get("moran_i")
        mp = spatial.get("moran_p")
        if mi is not None:
            sig = "significant" if (mp or 1) < 0.05 else "not significant"
            parts.append(
                f"Global Moran's I = {mi:.4f} (p = {mp:.4f}): "
                f"spatial autocorrelation is {sig}."
            )
        clusters = spatial.get("lisa_clusters", {})
        if clusters:
            parts.append(
                "LISA clusters: "
                + ", ".join(f"{k}: {v}" for k, v in sorted(clusters.items()))
            )
        tt = spatial.get("theil_total")
        tb = spatial.get("theil_between")
        if tt is not None:
            bpct = (tb / tt * 100) if tt > 0 else 0
            parts.append(
                f"Theil T inequality index: {tt:.4f} ({bpct:.0f}% between-borough)."
            )
        sections.append(("Spatial Patterns", "\n\n".join(parts)))

    # Synthetic control
    sc = results.get("synthetic_control")
    if sc:
        sections.append(("Synthetic Control", interpret_synthetic_control(sc)))

    # Staggered DiD
    did = results.get("staggered_did")
    if did:
        sections.append(
            (
                "Staggered Difference-in-Differences",
                interpret_staggered_did(did),
            )
        )

    # Event study
    es = results.get("event_study")
    if es:
        sections.append(("Event Study", interpret_event_study(es)))

    # RDD
    rdd = results.get("rdd")
    if rdd:
        sections.append(("Regression Discontinuity", interpret_rdd(rdd)))

    # Power analysis
    power = results.get("power")
    if power:
        sections.append(("Power Analysis", interpret_power(power)))

    # Synthesis
    synthesis_parts = ["### Summary of Evidence", ""]
    if sc:
        synthesis_parts.append(
            f"- **Synthetic control**: ATT = {sc.att:+.1f} complaints/month"
        )
    if did:
        synthesis_parts.append(
            f"- **Staggered DiD**: ATT = {did.aggregated_att:+.1f} "
            f"({format_p_str(did.aggregated_p_value)})"
        )
    if rdd:
        synthesis_parts.append(
            f"- **RDD**: effect = {rdd.treatment_effect:+.1f} "
            f"({format_p_str(rdd.p_value)})"
        )
    if power:
        synthesis_parts.append(
            f"- **MDE**: {power.mde:.1f} (80% power at alpha = 0.05)"
        )
    sections.append(("Synthesis", "\n".join(synthesis_parts)))

    # Limitations
    sections.append(
        (
            "Limitations",
            "- Treatment assignment is based on reported pilot rollout dates; "
            "exact enforcement timing may vary by district.\n"
            "- The RDD running variable uses haversine distance from the "
            "treated-zone centroid, not the precise mandate boundary polygon.\n"
            "- Rodent complaints reflect reporting behavior, not underlying "
            "rodent populations; reporting propensity may shift with policy "
            "awareness.\n"
            "- The panel uses monthly frequency, which may smooth out "
            "short-term policy dynamics.",
        )
    )

    md = compile_findings_md(
        title="Rat Containerization Policy Evaluation: Findings",
        date_str=date.today().isoformat(),
        toolkit_version="v0.4.0",
        sections=sections,
    )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FINDINGS_PATH.write_text(md, encoding="utf-8")
    print(f"  FINDINGS.md written to {FINDINGS_PATH}")

    json_results = {k: _serialize(v) for k, v in results.items() if k != "panel"}
    json_path = DATA_DIR / "analysis_results.json"
    json_path.write_text(
        json.dumps(json_results, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"  JSON results written to {json_path}")

    return md


if __name__ == "__main__":
    print("Step 7 requires results from prior steps. Use run_analysis.py.")
