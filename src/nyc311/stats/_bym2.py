"""BYM2 Bayesian small-area smoothing model.

Implements the Besag-York-Mollié model with the BYM2
reparameterization:

    Riebler, A., Sorbye, S. H., Simpson, D., & Rue, H. (2016). An
    intuitive Bayesian spatial model for disease mapping that accounts
    for scaling. *Statistical Methods in Medical Research*, 25(4),
    1145--1165.

    Besag, J., York, J., & Mollié, A. (1991). Bayesian image
    restoration, with two applications in spatial statistics.
    *Annals of the Institute of Statistical Mathematics*, 43(1),
    1--20.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BYM2Result:
    """Result of BYM2 small-area smoothing."""

    smoothed_rates: dict[str, float]
    credible_lower: dict[str, float]
    credible_upper: dict[str, float]
    mixing_parameter: float
    spatial_variance: float
    iid_variance: float
    unit_ids: tuple[str, ...]
    n_samples: int
    model_summary: str


def bym2_smooth(
    observed_counts: dict[str, int],
    expected_counts: dict[str, float],
    adjacency: dict[str, tuple[str, ...]],
    *,
    n_samples: int = 2000,
    n_tune: int = 1000,
    random_seed: int = 42,
) -> BYM2Result:
    """Smooth area-level rates with the BYM2 model.

    Estimates: y_i ~ Poisson(E_i * exp(mu + phi_i))

    where phi_i = sqrt(rho) * spatial_i + sqrt(1 - rho) * iid_i

    The mixing parameter rho controls the balance between spatially
    structured and unstructured random effects.

    Args:
        observed_counts: Mapping ``{unit_id: observed_count}``.
        expected_counts: Mapping ``{unit_id: expected_count}``.
        adjacency: Mapping ``{unit_id: (neighbor_ids,...)}``.
        n_samples: Number of posterior draws after tuning.
        n_tune: Number of warmup / tuning iterations.
        random_seed: Random seed for reproducibility.

    Returns:
        A :class:`BYM2Result` with smoothed rates, 95% credible
        intervals, and variance decomposition.

    Raises:
        ImportError: If pymc is not installed.
    """
    try:
        import numpy as np
        import pymc as pm
    except ImportError as exc:
        msg = (
            "pymc is required for bym2_smooth(). "
            "Install with: pip install nyc311[bayes]"
        )
        raise ImportError(msg) from exc

    unit_ids = sorted(observed_counts)
    n = len(unit_ids)
    uid_to_idx = {uid: i for i, uid in enumerate(unit_ids)}

    y = np.array([observed_counts[uid] for uid in unit_ids], dtype=float)
    e = np.array([expected_counts[uid] for uid in unit_ids], dtype=float)

    adj_pairs: list[tuple[int, int]] = []
    for uid in unit_ids:
        for nb in adjacency.get(uid, ()):
            if nb in uid_to_idx:
                i, j = uid_to_idx[uid], uid_to_idx[nb]
                if i < j:
                    adj_pairs.append((i, j))

    node1 = np.array([p[0] for p in adj_pairs])
    node2 = np.array([p[1] for p in adj_pairs])

    with pm.Model() as _model:
        mu = pm.Normal("mu", mu=0, sigma=1)
        sigma = pm.HalfNormal("sigma", sigma=1)
        rho = pm.Beta("rho", alpha=1, beta=1)

        theta = pm.Normal("theta", mu=0, sigma=1, shape=n)
        phi = pm.ICAR("phi", W=_build_adjacency_matrix(n, node1, node2))

        psi = pm.Deterministic(
            "psi",
            mu + sigma * (pm.math.sqrt(rho) * phi + pm.math.sqrt(1 - rho) * theta),
        )
        rate = pm.Deterministic("rate", pm.math.exp(psi))

        pm.Poisson("obs", mu=e * rate, observed=y)

        trace = pm.sample(
            draws=n_samples,
            tune=n_tune,
            random_seed=random_seed,
            progressbar=False,
            return_inferencedata=True,
        )

    rate_samples = trace.posterior["rate"].values.reshape(-1, n)
    smoothed = rate_samples.mean(axis=0)
    lower = np.percentile(rate_samples, 2.5, axis=0)
    upper = np.percentile(rate_samples, 97.5, axis=0)

    rho_samples = trace.posterior["rho"].values.flatten()
    sigma_samples = trace.posterior["sigma"].values.flatten()
    mixing = float(np.mean(rho_samples))
    total_var = float(np.mean(sigma_samples**2))
    spatial_var = mixing * total_var
    iid_var = (1 - mixing) * total_var

    summary = (
        f"BYM2: {n} areas, {len(adj_pairs)} edges\n"
        f"Mixing (rho): {mixing:.3f}\n"
        f"Total variance (sigma^2): {total_var:.4f}\n"
        f"Spatial / IID: {spatial_var:.4f} / {iid_var:.4f}"
    )

    return BYM2Result(
        smoothed_rates={uid: float(smoothed[i]) for i, uid in enumerate(unit_ids)},
        credible_lower={uid: float(lower[i]) for i, uid in enumerate(unit_ids)},
        credible_upper={uid: float(upper[i]) for i, uid in enumerate(unit_ids)},
        mixing_parameter=mixing,
        spatial_variance=spatial_var,
        iid_variance=iid_var,
        unit_ids=tuple(unit_ids),
        n_samples=n_samples,
        model_summary=summary,
    )


def _build_adjacency_matrix(n: int, node1: Any, node2: Any) -> Any:
    """Build a sparse adjacency matrix from edge lists."""
    import numpy as np

    w = np.zeros((n, n), dtype=float)
    for i, j in zip(node1, node2, strict=True):
        w[i, j] = 1.0
        w[j, i] = 1.0
    return w
