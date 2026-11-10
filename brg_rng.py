"""Ganzzahliger Zufallserzeuger SplitMix64, vektorisiert über Pfade (unabhängig von der numpy-Version).

`numpy.random` ist zwischen Versionen nicht stabil; SplitMix64 ist reine 64-Bit-Ganzzahlarithmetik und liefert bei gleichem Zufalls-Seed überall dieselben
Zahlen. Jeder Pfad hat seinen eigenen Zustand; der Anfangszustand von Pfad i ist der Mix von (Seed, i)."""

import numpy as np

_GOLDEN = np.uint64(0x9E3779B97F4A7C15)
_M1 = np.uint64(0xBF58476D1CE4E5B9)
_M2 = np.uint64(0x94D049BB133111EB)
_SALT = np.uint64(0x2545F4914F6CDD1D)


def _mix(z):
    with np.errstate(over="ignore"):
        z = (z ^ (z >> np.uint64(30))) * _M1
        z = (z ^ (z >> np.uint64(27))) * _M2
        return z ^ (z >> np.uint64(31))


class SplitMix64:
    def __init__(self, seed: int, paths: int):
        with np.errstate(over="ignore"):
            # Der Zufalls-Seed wird erst durchmischt: sonst wäre Pfad i des Seeds s derselbe Pfad wie Pfad i + s des Seeds 0 (überlappende Ströme).
            base = _mix(np.uint64(seed & 0xFFFFFFFFFFFFFFFF) * _GOLDEN + _SALT)
            self.state = _mix(base + np.arange(1, paths + 1, dtype=np.uint64) * _GOLDEN)

    def next_uint64(self):
        with np.errstate(over="ignore"):
            self.state = self.state + _GOLDEN
        return _mix(self.state)

    def uniform(self):
        """Gleichverteilt auf [0, 1) mit 53 Bit."""
        return (self.next_uint64() >> np.uint64(11)).astype(np.float64) * (1.0 / 9007199254740992.0)

    def inverse_cdf(self, cdf):
        """Ziehung aus einer diskreten Verteilung durch Inversion der Verteilungsfunktion (cdf aufsteigend, letzter Wert 1)."""
        return np.minimum(np.searchsorted(cdf, self.uniform(), side="right"), len(cdf) - 1)
