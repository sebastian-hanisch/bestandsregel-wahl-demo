"""Lücke einer Regel gegen die exakte Rückwärtsrechnung, in Prozent der Kosten der Rückwärtsrechnung.

Lücke = Kosten der Regel / Kosten der DP - 1, mal 100. Die Kosten sind Kosten je Periode im stationären Betrieb einschließlich Fixkosten.
Die Funktion rechnet mit `Fraction` exakt (Handbeispiele) und mit `float` (Messraster)."""

from fractions import Fraction


def gap(g_rule, g_dp):
    """Lücke in Prozent der DP-Kosten; ein Bruch bleibt ein Bruch. DP-Kosten von 0 oder weniger haben keine Lücke (ValueError)."""
    if g_dp <= 0:
        raise ValueError("Die Kosten der DP müssen positiv sein: die Lücke ist in Prozent dieser Kosten definiert.")
    if isinstance(g_rule, Fraction) or isinstance(g_dp, Fraction):
        return 100 * (Fraction(g_rule) / Fraction(g_dp) - 1)
    return 100.0 * (g_rule / g_dp - 1.0)


def clip_noise(value: float, tol: float = 1e-6) -> float:
    """Rechenrauschen um 0 (die Regel kann die DP nicht unterbieten) auf genau 0 setzen; echte negative Werte bleiben stehen."""
    return 0.0 if abs(value) < tol else value
