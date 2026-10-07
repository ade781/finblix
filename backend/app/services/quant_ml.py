"""
Shared, leakage-safe ML toolkit for Finblix direction models.

Pipeline (fit_direction_model):
  1. Chronological holdout split with a purge gap of `horizon` bars.
  2. ATR-scaled deadband labels: train only on moves larger than k * volatility.
  3. Feature pruning on the training part only (purged-CV permutation importance
     + correlation filter).
  4. Candidate selection (regularized logistic / shallow GBDT / shallow RF / soft vote)
     by purged walk-forward CV AUC.
  5. Platt calibration fitted on out-of-fold probabilities.
  6. High-conviction threshold chosen on out-of-fold data (Wilson lower bound),
     never on the test set.
  7. Honest holdout report: accuracy on every bar and on significant moves, AUC,
     Brier, majority baseline, confusion matrix, block-bootstrap 95% CIs.
  8. Deployed model is refit on train+test with the same recipe.
"""
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple
import time

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, confusion_matrix, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler

EPS = 1e-6


# ---------------------------------------------------------------- labels
def deadband_labels(fwd_ret: pd.Series, scale: pd.Series, k: float) -> pd.Series:
    """1 if fwd_ret > k*scale, 0 if < -k*scale, NaN inside the band or when unknown."""
    thr = k * scale
    y = pd.Series(np.nan, index=fwd_ret.index)
    y[fwd_ret > thr] = 1.0
    y[fwd_ret < -thr] = 0.0
    y[fwd_ret.isna() | scale.isna()] = np.nan
    return y


# ---------------------------------------------------------------- CV
def purged_walk_forward_splits(pos: np.ndarray, n_splits: int, horizon: int, embargo: int = 0,
                               min_train_frac: float = 0.4, min_train: int = 60
                               ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
    """
    Expanding-window walk-forward folds over sample bar positions `pos` (sorted).
    Training samples whose label window [p+1, p+horizon] reaches into the test
    block are purged; `embargo` adds extra bars of gap.
    """
    pos = np.asarray(pos)
    lo, hi = int(pos[0]), int(pos[-1]) + 1
    first_test = lo + int((hi - lo) * min_train_frac)
    block = max(1, (hi - first_test) // n_splits)
    for k in range(n_splits):
        t0 = first_test + k * block
        t1 = hi if k == n_splits - 1 else t0 + block
        train_idx = np.where(pos < t0 - horizon - embargo)[0]
        test_idx = np.where((pos >= t0) & (pos < t1))[0]
        if len(train_idx) >= min_train and len(test_idx) > 0:
            yield train_idx, test_idx


# ---------------------------------------------------------------- models
class CalibratedModel:
    """Base classifier + Platt scaling fitted on out-of-fold probabilities."""

    def __init__(self, base, a: float = 1.0, b: float = 0.0):
        self.base = base
        self.a = a
        self.b = b
        self.classes_ = np.array([0, 1])

    @staticmethod
    def _logit(p: np.ndarray) -> np.ndarray:
        p = np.clip(p, EPS, 1 - EPS)
        return np.log(p / (1 - p))

    def raw_proba(self, X) -> np.ndarray:
        return self.base.predict_proba(X)[:, 1]

    def predict_proba(self, X) -> np.ndarray:
        p = 1.0 / (1.0 + np.exp(-(self.a * self._logit(self.raw_proba(X)) + self.b)))
        return np.column_stack([1 - p, p])

    def predict(self, X) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


def fit_platt(raw_p: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    lr = LogisticRegression(C=1.0)
    lr.fit(CalibratedModel._logit(raw_p).reshape(-1, 1), y)
    return float(lr.coef_[0, 0]), float(lr.intercept_[0])


def candidate_models(n_train: int, random_state: int = 42) -> Dict[str, Any]:
    from sklearn.model_selection import RandomizedSearchCV
    from sklearn.feature_selection import SelectFromModel
    
    leaf = int(max(30, n_train // 60))
    # Use class_weight='balanced' to handle imbalanced long/short trades
    logreg = make_pipeline(RobustScaler(), LogisticRegression(C=0.05, max_iter=3000, class_weight='balanced'))
    
    # Base HGB
    hgb_base = HistGradientBoostingClassifier(
        max_iter=200, early_stopping=False, random_state=random_state, class_weight='balanced'
    )
    
    # Hyperparameter search space for HGB
    param_dist = {
        'learning_rate': [0.01, 0.03, 0.05, 0.1],
        'max_depth': [3, 4, 5, 7],
        'max_leaf_nodes': [8, 15, 31],
        'min_samples_leaf': [leaf, max(10, leaf//2), leaf*2],
        'l2_regularization': [0.0, 1.0, 5.0, 10.0]
    }
    
    # Fast regularized HistGBM
    hgb_fast = HistGradientBoostingClassifier(
        learning_rate=0.03, max_iter=160, max_depth=4, max_leaf_nodes=12,
        min_samples_leaf=leaf, l2_regularization=4.0, random_state=random_state,
        class_weight='balanced'
    )

    # Random Forest with shallow depth to avoid overfitting
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=4, min_samples_leaf=leaf, max_features="sqrt",
        n_jobs=1, random_state=random_state, class_weight='balanced'
    )

    models_dict = {
        "logreg": logreg,
        "hist_gbm": hgb_fast,
        "rf": rf,
    }

    # Add SOTA LightGBM & XGBoost
    lgb_model = None
    try:
        import lightgbm as lgb
        lgb_model = lgb.LGBMClassifier(
            n_estimators=180, learning_rate=0.03, max_depth=4, num_leaves=12,
            min_child_samples=max(15, leaf // 2), subsample=0.85, colsample_bytree=0.85,
            reg_alpha=0.5, reg_lambda=2.0, random_state=random_state, verbosity=-1
        )
        models_dict["lightgbm"] = lgb_model
    except Exception:
        pass

    xgb_model = None
    try:
        import xgboost as xgb
        xgb_model = xgb.XGBClassifier(
            n_estimators=180, learning_rate=0.03, max_depth=3, subsample=0.85,
            colsample_bytree=0.85, reg_alpha=0.5, reg_lambda=3.0,
            random_state=random_state, eval_metric="logloss"
        )
        models_dict["xgboost"] = xgb_model
    except Exception:
        pass

    # Soft Voting Ensemble
    if lgb_model is not None and xgb_model is not None:
        vote = VotingClassifier([
            ("lgb", clone(lgb_model)),
            ("xgb", clone(xgb_model)),
            ("hgb", clone(hgb_fast))
        ], voting="soft")
    else:
        vote = VotingClassifier([
            ("lr", clone(logreg)),
            ("hgb", clone(hgb_fast)),
            ("rf", clone(rf))
        ], voting="soft")
    models_dict["soft_vote"] = vote

    # Stacking Classifier
    from sklearn.ensemble import StackingClassifier
    stack_estimators = [("hgb", clone(hgb_fast)), ("rf", clone(rf))]
    if lgb_model is not None:
        stack_estimators.append(("lgb", clone(lgb_model)))
    if xgb_model is not None:
        stack_estimators.append(("xgb", clone(xgb_model)))

    stacking = StackingClassifier(
        estimators=stack_estimators,
        final_estimator=LogisticRegression(C=0.1, max_iter=1000),
        cv=3, n_jobs=1
    )
    models_dict["stacking"] = stacking

    return models_dict


def _safe_auc(y, p) -> float:
    try:
        return float(roc_auc_score(y, p))
    except ValueError:
        return 0.5


def oof_predict(model, X: np.ndarray, y: np.ndarray, splits: Sequence[Tuple[np.ndarray, np.ndarray]]
                ) -> Tuple[np.ndarray, np.ndarray]:
    """Out-of-fold raw P(up). Returns (indices covered, probabilities)."""
    idx_all, p_all = [], []
    for tr, te in splits:
        if len(np.unique(y[tr])) < 2:
            continue
        m = clone(model).fit(X[tr], y[tr])
        idx_all.append(te)
        p_all.append(m.predict_proba(X[te])[:, 1])
    if not idx_all:
        return np.array([], dtype=int), np.array([])
    return np.concatenate(idx_all), np.concatenate(p_all)


# ---------------------------------------------------------------- feature selection
def select_features(X: pd.DataFrame, y: np.ndarray, splits, max_features: int = 15,
                    min_features: int = 6, corr_limit: float = 0.85, random_state: int = 42
                    ) -> Tuple[List[str], List[Dict[str, float]]]:
    cols = [c for c in X.columns if X[c].std() > 1e-12]
    Xv = X[cols].values
    probe = HistGradientBoostingClassifier(
        learning_rate=0.05, max_iter=100, max_depth=3, min_samples_leaf=max(30, len(X) // 60),
        l2_regularization=5.0, random_state=random_state,
    )
    imp = np.zeros(len(cols))
    n_folds = 0
    for tr, te in splits:
        if len(np.unique(y[tr])) < 2 or len(np.unique(y[te])) < 2:
            continue
        m = clone(probe).fit(Xv[tr], y[tr])
        r = permutation_importance(m, Xv[te], y[te], scoring="roc_auc", n_repeats=4,
                                   random_state=random_state, n_jobs=1)
        imp += r.importances_mean
        n_folds += 1
    imp /= max(1, n_folds)
    order = list(np.argsort(-imp))

    corr = X[cols].corr(method="spearman").abs().fillna(0).values
    chosen: List[int] = []
    for i in order:
        if len(chosen) >= max_features:
            break
        if imp[i] <= 0 and len(chosen) >= min_features:
            break
        if all(corr[i, j] < corr_limit for j in chosen):
            chosen.append(i)
    ranking = [{"feature": cols[i], "importance": round(float(imp[i]) * 100, 3)} for i in order]
    return [cols[i] for i in chosen], ranking


# ---------------------------------------------------------------- thresholds & stats
def wilson_lower(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    p = k / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    rad = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float((centre - rad) / den)


def choose_conviction_threshold(p: np.ndarray, y: np.ndarray, min_coverage: float = 0.10,
                                min_count: int = 30) -> Dict[str, float]:
    """Pick the confidence cut-off maximising the Wilson lower bound of accuracy on OOF data."""
    conf = np.maximum(p, 1 - p)
    correct = ((p >= 0.5).astype(int) == y)
    best = {"threshold": 0.5, "oof_accuracy": float(correct.mean()) if len(y) else 0.0,
            "oof_coverage": 1.0, "wilson_lower": wilson_lower(int(correct.sum()), len(y))}
    for t in np.arange(0.51, 0.76, 0.01):
        m = conf >= t
        n = int(m.sum())
        if n < min_count or n / max(1, len(y)) < min_coverage:
            continue
        lb = wilson_lower(int(correct[m].sum()), n)
        if lb > best["wilson_lower"]:
            best = {"threshold": round(float(t), 2), "oof_accuracy": float(correct[m].mean()),
                    "oof_coverage": n / len(y), "wilson_lower": lb}
    return best


def block_bootstrap_ci(values: np.ndarray, block: int, n_boot: int = 1000, seed: int = 0
                       ) -> Tuple[float, float]:
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    block = int(max(1, min(block, n)))
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(n_boot, nb))
    idx = (starts[:, :, None] + np.arange(block)).reshape(n_boot, -1)[:, :n]
    means = values[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def pct(x: float) -> float:
    return round(float(x) * 100, 2)


# ---------------------------------------------------------------- main entry point
def _fit_recipe(X: pd.DataFrame, y: np.ndarray, pos: np.ndarray, horizon: int, n_splits: int,
                max_features: int, random_state: int, fixed_features: Optional[List[str]] = None,
                fixed_model: Optional[str] = None) -> Dict[str, Any]:
    splits = list(purged_walk_forward_splits(pos, n_splits, horizon))
    if len(splits) < 2:
        raise ValueError(f"Not enough data for purged CV ({len(X)} samples)")

    if fixed_features is None:
        print(f"   [ML] Selecting top features from {len(X.columns)} candidate columns across {len(splits)} folds...")
        features, ranking = select_features(X, y, splits, max_features=max_features, random_state=random_state)
        print(f"   [ML] Selected {len(features)} features: {features[:5]}...")
    else:
        features, ranking = fixed_features, []
    Xs = X[features].values

    cands = candidate_models(len(X), random_state)
    cv_scores: Dict[str, Dict[str, float]] = {}
    oof_cache: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
    names = [fixed_model] if fixed_model else list(cands.keys())
    print(f"   [ML] Evaluating {len(names)} candidate model architectures...")
    for name in names:
        t_cand = time.time()
        idx, p = oof_predict(cands[name], Xs, y, splits)
        oof_cache[name] = (idx, p)
        cv_scores[name] = {"auc": _safe_auc(y[idx], p), "accuracy": float(accuracy_score(y[idx], p >= 0.5))}
        print(f"      -> {name:<12}: AUC={cv_scores[name]['auc']*100:.2f}%, Acc={cv_scores[name]['accuracy']*100:.2f}% ({time.time()-t_cand:.2f}s)")
    # Composite score prioritizing directional accuracy while rewarding high discriminative AUC
    best = max(names, key=lambda n: (cv_scores[n]["accuracy"] * 0.6 + cv_scores[n]["auc"] * 0.4))
    print(f"   [ML] Winner Architecture: {best}")

    idx, raw = oof_cache[best]
    a, b = fit_platt(raw, y[idx])
    base = clone(cands[best]).fit(Xs, y)
    model = CalibratedModel(base, a, b)
    p_cal = 1.0 / (1.0 + np.exp(-(a * CalibratedModel._logit(raw) + b)))
    thr = choose_conviction_threshold(p_cal, y[idx])
    return {
        "model": model, "features": features, "ranking": ranking, "model_name": best,
        "cv_scores": cv_scores, "oof_auc": cv_scores[best]["auc"],
        "oof_accuracy": cv_scores[best]["accuracy"], "threshold": thr,
    }


def fit_direction_model(feat: pd.DataFrame, candidate_cols: List[str], fwd_ret: pd.Series,
                        scale: pd.Series, horizon: int, k_deadband: float = 0.25,
                        test_frac: float = 0.2, n_splits: int = 5, max_features: int = 15,
                        times: Optional[pd.Series] = None, random_state: int = 42) -> Dict[str, Any]:
    """
    feat: one row per bar (chronological). fwd_ret: return from this bar's close to `horizon`
    bars later. scale: per-bar volatility for the same horizon (e.g. atr_norm*sqrt(horizon)).
    """
    feat = feat.reset_index(drop=True)
    fwd_ret = fwd_ret.reset_index(drop=True)
    scale = scale.reset_index(drop=True)
    pos_all = np.arange(len(feat))
    X_all = feat[candidate_cols].replace([np.inf, -np.inf], np.nan)
    valid = X_all.notna().all(axis=1) & fwd_ret.notna()
    y_dead = deadband_labels(fwd_ret, scale, k_deadband)

    valid_pos = pos_all[valid.values]
    if len(valid_pos) < 200:
        raise ValueError(f"Too few valid samples ({len(valid_pos)})")
    test_start = int(valid_pos[int(len(valid_pos) * (1 - test_frac))])

    train_mask = valid & y_dead.notna() & (pos_all < test_start - horizon)
    test_mask = valid & (pos_all >= test_start)

    Xtr = X_all[train_mask].reset_index(drop=True)
    ytr = y_dead[train_mask].astype(int).values
    ptr = pos_all[train_mask.values]
    fit = _fit_recipe(Xtr, ytr, ptr, horizon, n_splits, max_features, random_state)
    model, features = fit["model"], fit["features"]

    # ---- holdout evaluation (every bar, real sign)
    Xte = X_all.loc[test_mask, features].values
    p_te = model.predict_proba(Xte)[:, 1]
    pred = (p_te >= 0.5).astype(int)
    y_sign = (fwd_ret[test_mask].values > 0).astype(int)
    correct = (pred == y_sign).astype(float)
    sig = y_dead[test_mask].notna().values
    y_sig = y_dead[test_mask].values[sig].astype(int)
    conf = np.maximum(p_te, 1 - p_te)
    hc = conf >= fit["threshold"]["threshold"]
    majority = max(y_sign.mean(), 1 - y_sign.mean())
    ci_lo, ci_hi = block_bootstrap_ci(correct, block=max(horizon, 5))
    hc_ci = block_bootstrap_ci(correct[hc], block=max(horizon, 5)) if hc.sum() else (0.0, 0.0)
    train_pred = model.predict(Xtr[features].values)

    metrics = {
        "model_name": fit["model_name"],
        "n_features": len(features),
        "samples_trained": int(train_mask.sum()),
        "samples_tested": int(test_mask.sum()),
        "deadband_k": k_deadband,
        "deadband_train_coverage_pct": pct(train_mask.sum() / max(1, (valid & (pos_all < test_start - horizon)).sum())),
        "train_accuracy_pct": pct(accuracy_score(ytr, train_pred)),
        "cv_auc_pct": pct(fit["oof_auc"]),
        "cv_accuracy_pct": pct(fit["oof_accuracy"]),
        "cv_candidates": {k: {"auc_pct": pct(v["auc"]), "accuracy_pct": pct(v["accuracy"])} for k, v in fit["cv_scores"].items()},
        "test_accuracy_pct": pct(correct.mean()),
        "test_accuracy_ci95_pct": [pct(ci_lo), pct(ci_hi)],
        "test_majority_baseline_pct": pct(majority),
        "test_edge_vs_baseline_pct": pct(correct.mean() - majority),
        "test_accuracy_significant_moves_pct": pct(accuracy_score(y_sig, pred[sig])) if sig.sum() else None,
        "test_significant_moves_count": int(sig.sum()),
        "test_auc_pct": pct(_safe_auc(y_sign, p_te)),
        "test_brier": round(float(brier_score_loss(y_sign, p_te)), 4),
        "confusion_matrix": confusion_matrix(y_sign, pred, labels=[0, 1]).tolist(),
        "hc_threshold": fit["threshold"]["threshold"],
        "hc_oof_accuracy_pct": pct(fit["threshold"]["oof_accuracy"]),
        "hc_oof_coverage_pct": pct(fit["threshold"]["oof_coverage"]),
        "hc_test_accuracy_pct": pct(correct[hc].mean()) if hc.sum() else None,
        "hc_test_accuracy_ci95_pct": [pct(hc_ci[0]), pct(hc_ci[1])] if hc.sum() else None,
        "hc_test_count": int(hc.sum()),
        "hc_test_coverage_pct": pct(hc.mean()),
    }

    test_log = []
    if times is not None:
        t_te = times.reset_index(drop=True)[test_mask].values
        f_te = fwd_ret[test_mask].values
        for t, p, yv, f in zip(t_te, p_te, y_sign, f_te):
            test_log.append({"time": int(t), "prob_up": round(float(p), 4), "actual_up": int(yv),
                             "fwd_ret": round(float(f), 6)})

    # ---- deploy: refit same recipe on all labelled data (features + model family fixed)
    all_mask = valid & y_dead.notna() & (pos_all < len(feat) - horizon)
    Xall = X_all[all_mask].reset_index(drop=True)
    final = _fit_recipe(Xall, y_dead[all_mask].astype(int).values, pos_all[all_mask.values], horizon,
                        n_splits, max_features, random_state, fixed_features=features,
                        fixed_model=fit["model_name"])
    metrics["deployed_threshold"] = final["threshold"]["threshold"]
    metrics["is_validated"] = bool(
        metrics["test_auc_pct"] > 51.0 and metrics["test_edge_vs_baseline_pct"] > -1.0 and metrics["cv_auc_pct"] > 51.0
    )

    return {
        "model": final["model"],
        "features": features,
        "feature_ranking": fit["ranking"],
        "metrics": metrics,
        "hc_threshold": final["threshold"]["threshold"],
        "test_log": test_log,
    }


def conviction_tier(prob_up: float, hc_threshold: float, neutral_band: float = 0.03) -> str:
    conf = max(prob_up, 1 - prob_up)
    if conf >= hc_threshold and hc_threshold > 0.5:
        return "HIGH"
    if conf < 0.5 + neutral_band:
        return "NO_TRADE"
    return "MODERATE"
