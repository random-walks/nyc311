"""Composable factor pipeline for NYC 311 complaint analysis."""

from nyc311.factors._advanced import EquityGapFactor, SpatialLagFactor
from nyc311.factors._base import Factor, FactorContext, Pipeline, PipelineResult
from nyc311.factors._builtin import (
    AnomalyScoreFactor,
    ComplaintVolumeFactor,
    RecurrenceFactor,
    ResolutionTimeFactor,
    ResponseRateFactor,
    SeasonalityFactor,
    TopicConcentrationFactor,
)
from nyc311.factors._factor_factory import dispatch_factor_factory_engine

__all__ = [
    "AnomalyScoreFactor",
    "ComplaintVolumeFactor",
    "EquityGapFactor",
    "Factor",
    "FactorContext",
    "Pipeline",
    "PipelineResult",
    "RecurrenceFactor",
    "ResolutionTimeFactor",
    "ResponseRateFactor",
    "SeasonalityFactor",
    "SpatialLagFactor",
    "TopicConcentrationFactor",
    "dispatch_factor_factory_engine",
]
