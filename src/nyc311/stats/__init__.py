"""PhD-level statistical modeling for NYC 311 complaint analysis."""

from nyc311.stats._anomaly import STLAnomalyResult, detect_stl_anomalies
from nyc311.stats._bym2 import BYM2Result, bym2_smooth
from nyc311.stats._changepoint import ChangepointResult, detect_changepoints
from nyc311.stats._decomposition import DecompositionResult, seasonal_decompose
from nyc311.stats._equity import (
    OaxacaBlinderResult,
    TheilResult,
    oaxaca_blinder_decomposition,
    theil_index,
)
from nyc311.stats._gwr import GWRResult, geographically_weighted_regression
from nyc311.stats._hawkes import HawkesResult, fit_hawkes_process
from nyc311.stats._its import ITSResult, interrupted_time_series
from nyc311.stats._panel_models import (
    PanelRegressionResult,
    panel_fixed_effects,
    panel_random_effects,
)
from nyc311.stats._power import PowerResult, minimum_detectable_effect
from nyc311.stats._rdd import RDResult, regression_discontinuity
from nyc311.stats._reporting_bias import (
    LatentReportingResult,
    ReportingAdjustmentResult,
    latent_reporting_bias_em,
    reporting_rate_adjustment,
)
from nyc311.stats._spatial import (
    LISAResult,
    MoranResult,
    global_morans_i,
    local_morans_i,
)
from nyc311.stats._spatial_regression import (
    SpatialErrorResult,
    SpatialLagResult,
    spatial_error_model,
    spatial_lag_model,
)
from nyc311.stats._staggered_did import (
    EventStudyResult,
    GroupTimeATT,
    StaggeredDiDResult,
    event_study,
    staggered_did,
)
from nyc311.stats._synthetic_control import (
    SyntheticControlResult,
    synthetic_control,
)

__all__ = [
    "STLAnomalyResult",
    "BYM2Result",
    "ChangepointResult",
    "DecompositionResult",
    "EventStudyResult",
    "GWRResult",
    "GroupTimeATT",
    "HawkesResult",
    "ITSResult",
    "LISAResult",
    "LatentReportingResult",
    "MoranResult",
    "OaxacaBlinderResult",
    "PanelRegressionResult",
    "PowerResult",
    "RDResult",
    "ReportingAdjustmentResult",
    "SpatialErrorResult",
    "SpatialLagResult",
    "StaggeredDiDResult",
    "SyntheticControlResult",
    "TheilResult",
    "bym2_smooth",
    "detect_changepoints",
    "detect_stl_anomalies",
    "event_study",
    "fit_hawkes_process",
    "geographically_weighted_regression",
    "global_morans_i",
    "interrupted_time_series",
    "latent_reporting_bias_em",
    "local_morans_i",
    "minimum_detectable_effect",
    "oaxaca_blinder_decomposition",
    "panel_fixed_effects",
    "panel_random_effects",
    "regression_discontinuity",
    "reporting_rate_adjustment",
    "seasonal_decompose",
    "spatial_error_model",
    "spatial_lag_model",
    "staggered_did",
    "synthetic_control",
    "theil_index",
]
