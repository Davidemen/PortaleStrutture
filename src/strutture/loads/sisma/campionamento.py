"""Parametric period sampling for the response spectrum (spec Tool 6).

The sheet builds its T-grid by stepping +0.05 s and inserting one exact breakpoint at T=TD
(Sisma!I58:I149), with a hardcoded last point at T=5 s — an artifact of the fixed 96-row layout,
not a modelling requirement (`docs/specs/sisma.md` Tool 6). Since Se(T)/Sd(T) are evaluated by
closed-form branch formulas that are valid at any T, this module instead produces a plain
arithmetic grid; callers needing to match a specific sheet row simply evaluate at that row's T.
"""


def campiona_periodi(t_start_s: float, t_end_s: float, step_s: float) -> tuple[float, ...]:
    """T = t_start, t_start+step, ..., up to (and including, if it lands exactly) t_end."""
    n_steps = round((t_end_s - t_start_s) / step_s)
    return tuple(round(t_start_s + i * step_s, 10) for i in range(n_steps + 1))
