"""Shared helpers for rendering jellycell tearsheets from case-study output.

Bridges the nyc311.stats result dataclasses used by the two
production case studies onto the
:mod:`factor_factory.jellycell.tearsheets` templates, which expect
``artifacts/<family>_results.json`` files in factor-factory's Result
schema.

The bridge is **lossy by design**: nyc311's homegrown results carry
fields that factor-factory's schemas don't (unit weights, full
counterfactual trajectories, event-study coefficient vectors). The
tearsheet gets the headline numbers (ATT / SE / CI / p); the full
nyc311 ``analysis_results.json`` remains the authoritative artifact
for the study.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _serialize_scm(scm: dict[str, Any]) -> dict[str, Any]:
    """Translate a nyc311 ``synthetic_control`` dict to ff's ScmResult shape."""
    return {
        "method": "nyc311_scm",
        "att": scm.get("att"),
        "se": None,
        "ci_95_lower": None,
        "ci_95_upper": None,
        "p_value": scm.get("placebo_p_value"),
        "n": len(scm.get("periods", [])),
        "unit_weights": scm.get("donor_weights"),
        "diagnostics": {
            "pre_treatment_mspe": scm.get("pre_treatment_mspe"),
            "treated_unit": scm.get("treated_unit"),
            "model_summary": scm.get("model_summary"),
        },
    }


def _serialize_staggered_did(sdid: dict[str, Any]) -> dict[str, Any]:
    """Translate a nyc311 ``staggered_did`` dict to ff's DidResult shape."""
    lo = sdid.get("aggregated_ci_lower")
    hi = sdid.get("aggregated_ci_upper")
    n_groups = sdid.get("n_groups") or 0
    n_periods = sdid.get("n_periods") or 0
    return {
        "method": "nyc311_cs_staggered",
        "att": sdid.get("aggregated_att"),
        "se": sdid.get("aggregated_se"),
        "ci_95_lower": lo,
        "ci_95_upper": hi,
        "p_value": sdid.get("aggregated_p_value"),
        "n": n_groups * n_periods,
        "cohort_atts": None,
        "cohort_ses": None,
        "diagnostics": {
            "n_groups": n_groups,
            "n_periods": n_periods,
            "group_time_atts_count": len(sdid.get("group_time_atts", [])),
        },
    }


def _serialize_rdd(rdd: dict[str, Any]) -> dict[str, Any]:
    """Translate a nyc311 ``rdd`` dict to ff's RddResult shape."""
    n_left = rdd.get("n_effective_left") or 0
    n_right = rdd.get("n_effective_right") or 0
    return {
        "method": "nyc311_rdd_cct",
        "att": rdd.get("treatment_effect"),
        "se": rdd.get("se_robust"),
        "ci_95_lower": rdd.get("ci_lower"),
        "ci_95_upper": rdd.get("ci_upper"),
        "p_value": rdd.get("p_value"),
        "n": n_left + n_right,
        "diagnostics": {
            "bandwidth_left": rdd.get("bandwidth_left"),
            "bandwidth_right": rdd.get("bandwidth_right"),
            "kernel": rdd.get("kernel"),
        },
    }


def _serialize_its(its: dict[str, Any]) -> dict[str, Any]:
    """Translate an ITS result into a DiD-compatible row (level change as ATT)."""
    return {
        "method": "nyc311_its_segmented",
        "att": its.get("level_change"),
        "se": None,
        "ci_95_lower": None,
        "ci_95_upper": None,
        "p_value": its.get("p_value_level"),
        "n": its.get("n") or 0,
        "diagnostics": {
            "pre_trend": its.get("pre_trend"),
            "post_trend": its.get("post_trend"),
            "trend_change": its.get("trend_change"),
            "p_value_trend": its.get("p_value_trend"),
        },
    }


def write_factor_factory_artifacts(
    analysis_results: dict[str, Any],
    artifacts_dir: Path,
) -> list[str]:
    """Write ``<family>_results.json`` files for every engine we can bridge.

    Args:
        analysis_results: The nyc311 case-study ``analysis_results.json``
            dict.
        artifacts_dir: Target directory; created if missing.

    Returns:
        List of file names written, relative to ``artifacts_dir``.
    """
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    scm = analysis_results.get("synthetic_control")
    if scm:
        path = artifacts_dir / "scm_results.json"
        path.write_text(json.dumps([_serialize_scm(scm)], indent=2, default=str))
        written.append(path.name)

    sdid = analysis_results.get("staggered_did")
    if sdid:
        path = artifacts_dir / "did_results.json"
        path.write_text(
            json.dumps([_serialize_staggered_did(sdid)], indent=2, default=str)
        )
        written.append(path.name)

    rdd = analysis_results.get("rdd")
    if rdd:
        path = artifacts_dir / "rdd_results.json"
        path.write_text(json.dumps([_serialize_rdd(rdd)], indent=2, default=str))
        written.append(path.name)

    its = analysis_results.get("policy_evaluation") or analysis_results.get("its")
    if its and its.get("level_change") is not None:
        path = artifacts_dir / "did_results.json"
        # Append ITS row to DiD results (or create if absent)
        existing: list[dict[str, Any]] = []
        if path.exists():
            existing = json.loads(path.read_text())
        existing.append(_serialize_its(its))
        path.write_text(json.dumps(existing, indent=2, default=str))
        if path.name not in written:
            written.append(path.name)

    return written


def ensure_jellycell_toml(project_root: Path, name: str) -> None:
    """Write a minimal ``jellycell.toml`` if one is missing."""
    toml_path = project_root / "jellycell.toml"
    if toml_path.exists():
        return
    toml_path.write_text(
        f'[project]\nname = "{name}"\n\n'
        '[paths]\nartifacts = "artifacts"\nmanuscripts = "manuscripts"\ndata = "data"\n'
    )


def _project_display_name(project_root: Path) -> str:
    """Return the stable [project].name from jellycell.toml, or the dir name."""
    toml_path = project_root / "jellycell.toml"
    if toml_path.exists():
        import tomllib

        data = tomllib.loads(toml_path.read_text())
        name = data.get("project", {}).get("name")
        if name:
            return str(name)
    return project_root.name


def render_all_tearsheets(project_root: Path) -> list[str]:
    """Render the five jellycell tearsheets into ``project_root/manuscripts/``.

    Passes a stable display name via ``template_overrides`` so the
    committed tearsheets don't embed the local absolute path —
    jellycell's rendered HTML site is then reproducible from git
    without diff-churn across contributors' machines.

    Args:
        project_root: The case-study directory (where
            ``jellycell.toml`` lives).

    Returns:
        List of rendered filenames. Failures are printed and skipped.
    """
    from factor_factory.jellycell import tearsheets

    rendered: list[str] = []
    project_dir = str(project_root)
    display_name = _project_display_name(project_root)
    # Pin the "generated_at" stamp to a stable string so committed
    # tearsheets don't diff on every regeneration across contributors'
    # machines and clocks. The git commit SHA + time are the true
    # provenance for reviewers.
    overrides = {
        "project": display_name,
        "generated_at": "committed (regenerate with run_analysis.py)",
    }
    for renderer in (
        tearsheets.methodology,
        tearsheets.diagnostics,
        tearsheets.findings,
        tearsheets.audit,
        tearsheets.manuscript,
    ):
        try:
            path = renderer(
                project_dir,
                overwrite=True,
                template_overrides=overrides,
            )
            rendered.append(path.name)
        except Exception as exc:
            print(f"  tearsheet {renderer.__name__} FAILED: {exc}")

    return rendered


__all__ = [
    "ensure_jellycell_toml",
    "render_all_tearsheets",
    "write_factor_factory_artifacts",
]
