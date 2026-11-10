"""Nachfrageverteilung: Poisson, bei dmax abgeschnitten (der Rest der Wahrscheinlichkeit liegt auf dmax)."""

from math import exp, factorial

import numpy as np


def poisson_pmf(mean: float, dmax: int) -> np.ndarray:
    """Poisson(mean) auf 0..dmax; die Restmasse oberhalb dmax wird auf dmax gelegt, die Summe ist 1."""
    p = np.array([exp(-mean) * mean**k / factorial(k) for k in range(dmax + 1)])
    p[-1] += 1.0 - p.sum()
    return p
