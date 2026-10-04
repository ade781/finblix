import numpy as np
import pandas as pd
import pytest

from app.services.quant_ml import (
    block_bootstrap_ci, choose_conviction_threshold, conviction_tier, deadband_labels,
    fit_direction_model, purged_walk_forward_splits, wilson_lower,
)


def test_deadband_labels_band_and_nan():
    fwd = pd.Series([0.02, -0.02, 0.001, np.nan])
    scale = pd.Series([0.01, 0.01, 0.01, 0.01])
    y = deadband_labels(fwd, scale, k=0.5)
    assert y.iloc[0] == 1 and y.iloc[1] == 0
    assert np.isnan(y.iloc[2]) and np.isnan(y.iloc[3])


@pytest.mark.parametrize("horizon", [1, 12])
def test_purged_splits_never_leak_labels(horizon):
    pos = np.arange(1000)
    splits = list(purged_walk_forward_splits(pos, n_splits=5, horizon=horizon))
    assert len(splits) == 5
    for tr, te in splits:
        # every training label window [p+1, p+horizon] ends before the test block starts
        assert pos[tr].max() + horizon < pos[te].min()


def test_purged_splits_respect_gaps_in_positions():
    pos = np.array([p for p in range(600) if p % 3])  # deadband removes rows
    for tr, te in purged_walk_forward_splits(pos, 4, horizon=5):
        assert pos[tr].max() + 5 < pos[te].min()


def test_threshold_prefers_reliable_subset():
    rng = np.random.default_rng(0)
    p = rng.uniform(0, 1, 4000)
    conf = np.maximum(p, 1 - p)
    # labels agree with prediction mostly when confident
    agree = rng.uniform(0, 1, 4000) < np.where(conf > 0.65, 0.8, 0.5)
    y = np.where(agree, (p >= 0.5).astype(int), (p < 0.5).astype(int))
    res = choose_conviction_threshold(p, y)
    assert res["threshold"] >= 0.6
    assert res["oof_accuracy"] > 0.7


def test_wilson_and_bootstrap_bounds():
    assert wilson_lower(60, 100) < 0.6
    lo, hi = block_bootstrap_ci(np.r_[np.ones(60), np.zeros(40)], block=5)
    assert lo < 0.6 < hi


def test_conviction_tier():
    assert conviction_tier(0.70, 0.62) == "HIGH"
    assert conviction_tier(0.51, 0.62) == "NO_TRADE"
    assert conviction_tier(0.42, 0.62) == "MODERATE"


def _synthetic(n=1500, signal=True, seed=1):
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=n)
    noise = rng.normal(size=(n, 5))
    ret = (0.6 * x1 if signal else 0) * 0.01 + rng.normal(scale=0.01, size=n)
    feat = pd.DataFrame(noise, columns=[f"n{i}" for i in range(5)])
    feat["x1"] = x1
    fwd = pd.Series(ret)  # return realised over the next bar, known only in the future
    scale = pd.Series(np.full(n, 0.01))
    return feat, fwd, scale


def test_fit_direction_model_learns_signal():
    feat, fwd, scale = _synthetic()
    res = fit_direction_model(feat, list(feat.columns), fwd, scale, horizon=1, k_deadband=0.25,
                              times=pd.Series(np.arange(len(feat))))
    m = res["metrics"]
    assert "x1" in res["features"]
    assert m["test_accuracy_pct"] > 60
    assert m["test_auc_pct"] > 65
    assert m["is_validated"]
    assert len(res["test_log"]) == m["samples_tested"]
    p = res["model"].predict_proba(feat[res["features"]].values[:5])
    assert p.shape == (5, 2) and np.allclose(p.sum(1), 1)


def test_fit_direction_model_no_signal_is_not_validated_or_near_coinflip():
    feat, fwd, scale = _synthetic(signal=False, seed=7)
    res = fit_direction_model(feat, list(feat.columns), fwd, scale, horizon=1)
    m = res["metrics"]
    assert 40 < m["test_accuracy_pct"] < 60
    assert m["test_accuracy_ci95_pct"][0] < 55
