"""PhD-level statistical modeling for NYC 311 complaint analysis."""

from nyc311.stats._changepoint import ChangepointResult, detect_changepoints
from nyc311.stats._decomposition import DecompositionResult, seasonal_decompose
from nyc311.stats._its import ITSResult, interrupted_time_series
from nyc311.stats._panel_models import (
    PanelRegressionResult,
    panel_fixed_effects,
    panel_random_effects,
)
from nyc311.stats._spatial import (
    LISAResult,
    MoranResult,
    global_morans_i,
    local_morans_i,
)

__all__ = [
    "ChangepointResult",
    "DecompositionResult",
    "ITSResult",
    "LISAResult",
    "MoranResult",
    "PanelRegressionResult",
    "detect_changepoints",
    "global_morans_i",
    "interrupted_time_series",
    "local_morans_i",
    "panel_fixed_effects",
    "panel_random_effects",
    "seasonal_decompose",
]
