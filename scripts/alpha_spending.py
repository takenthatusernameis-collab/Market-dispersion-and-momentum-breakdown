"""Sequential alpha-spending rule for repeated sealed forward-block looks.

Protocol 6 (docs/research_protocol.md) requires:

    "For future ongoing blocks, freeze each new block and evaluate it once.
    Number sequential looks and apply a predeclared alpha-spending rule such as
    alpha_k = 0.05 / (k * (k + 1))."

This module is the single implementation of that rule. It is deliberately
stdlib-only (no numpy/pandas) so it can be imported by the test suite in any
environment, and it is pure arithmetic: it takes a declared family alpha and a
sequential look index k (1-based) and returns the per-look significance level,
the cumulative spend and the running remaining budget. Nothing here touches
market data, so it cannot introduce look-ahead or outcome-informed choices.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class AlphaSpendResult:
    """Outcome of one alpha-spending query for sequential look k."""

    k: int
    family_alpha: float
    alpha_k: float
    cumulative_spend: float
    remaining_budget: float
    rule: str = "alpha_k = 0.05 / (k * (k + 1))"

    def as_dict(self) -> dict:
        return {
            "k": self.k,
            "family_alpha": self.family_alpha,
            "alpha_k": self.alpha_k,
            "cumulative_spend": self.cumulative_spend,
            "remaining_budget": self.remaining_budget,
            "rule": self.rule,
        }


def alpha_for_look(k: int, family_alpha: float = 0.05) -> float:
    """Per-look significance level for the k-th sequential forward-block look.

    alpha_k = family_alpha / (k * (k + 1))

    The series sums to family_alpha over k = 1..inf, so the family-wise error
    rate is controlled exactly at `family_alpha` in the limit and is strictly
    below it for any finite number of looks.
    """
    if k < 1:
        raise ValueError("k must be a positive integer (1-based sequential look)")
    if not (0.0 < family_alpha <= 1.0):
        raise ValueError("family_alpha must be in (0, 1]")
    return family_alpha / (k * (k + 1))


def cumulative_spend(k: int, family_alpha: float = 0.05) -> float:
    """Sum of alpha_j for j = 1..k, i.e. the budget consumed after k looks."""
    if k < 1:
        return 0.0
    return sum(alpha_for_look(j, family_alpha) for j in range(1, k + 1))


def evaluate_look(k: int, family_alpha: float = 0.05) -> AlphaSpendResult:
    """Full per-look query: alpha_k, cumulative spend and remaining budget."""
    alpha_k = alpha_for_look(k, family_alpha)
    spent = cumulative_spend(k, family_alpha)
    return AlphaSpendResult(
        k=k,
        family_alpha=family_alpha,
        alpha_k=alpha_k,
        cumulative_spend=spent,
        remaining_budget=family_alpha - spent,
    )


def evaluate_sequence(looks: Sequence[int], family_alpha: float = 0.05) -> list[AlphaSpendResult]:
    """Evaluate the rule for an ordered sequence of look indices.

    `looks` is the chronological list of look numbers actually taken (e.g.
    [1, 2, 3]); the spend for each is computed from its own index, not from its
    position in this list, so a skipped look consumes no budget.
    """
    return [evaluate_look(int(k), family_alpha) for k in looks]


def family_budget_exhausted(k: int, family_alpha: float = 0.05, tolerance: float = 1e-12) -> bool:
    """True once cumulative spend has consumed the whole family budget.

    In practice the series only asymptotically reaches family_alpha, so this
    is effectively never true for finite k; it is provided so callers can
    assert the invariant explicitly rather than assume it.
    """
    return cumulative_spend(k, family_alpha) >= family_alpha - tolerance


def verify_budget_invariant(max_k: int = 10_000, family_alpha: float = 0.05) -> bool:
    """Sanity check: cumulative spend is monotone and bounded by family_alpha."""
    previous = 0.0
    for k in range(1, max_k + 1):
        current = cumulative_spend(k, family_alpha)
        if current < previous - 1e-15:
            return False
        if current > family_alpha + 1e-12:
            return False
        previous = current
    return True

def verify_budget_invariant(max_k: int = 1000, family_alpha: float = 0.05) -> bool:
    """Verify that cumulative spend never exceeds family_alpha and approaches it."""
    if max_k < 1:
        return True
    spent = 0.0
    for k in range(1, max_k + 1):
        alpha_k = alpha_for_look(k, family_alpha)
        spent += alpha_k
        if spent > family_alpha + 1e-12:
            return False
    return True


def family_budget_exhausted(k: int, family_alpha: float = 0.05, tol: float = 1e-12) -> bool:
    """Return True if budget exhausted at or before k (within tolerance)."""
    if k < 1:
        return False
    spent = cumulative_spend(k, family_alpha)
    return spent >= family_alpha - tol


def evaluate_sequence(look_indices: Sequence[int], family_alpha: float = 0.05) -> list[AlphaSpendResult]:
    """Evaluate a sequence of look indices (may skip). Spend is keyed by index."""
    results = []
    for k in look_indices:
        alpha_k = alpha_for_look(k, family_alpha)
        # cumulative spend is sum of alpha_j for j in look_indices seen so far?
        # Test says: "spend after looks 1 and 3 == spend(1) + spend(3)" - so cumulative spend accumulates alpha_k for each look in sequence
        spent_so_far = sum(alpha_for_look(ki, family_alpha) for ki in look_indices[:look_indices.index(k) + 1]) if False else None
    # Simpler: track running total
    running = 0.0
    results = []
    # easier to iterate by index
    for idx, k in enumerate(look_indices):
        alpha_k = alpha_for_look(k, family_alpha)
        running += alpha_k
        results.append(AlphaSpendResult(
            k=k,
            family_alpha=family_alpha,
            alpha_k=alpha_k,
            cumulative_spend=running,
            remaining_budget=family_alpha - running,
        ))
    return results
