"""Step: total self-weight of the pile cap, factored for the unfavourable case (docs/specs/
fond-plinti-pali.md Tool-1 step 10, `Footing check!AR24`): `AX/1000*BY/1000*H/1000*25*gammaG1 + G1`.

`G1` (`AR26`) is the sheet's own **job-specific hardcoded** extra load (backfill/paving on top of
the plinth) — the spec explicitly calls this out as "must be exposed as a free-form user input in
the Python port, not hardcoded" (docs/specs/fond-plinti-pali.md "Constants baked into formulas");
`carico_aggiuntivo_kN` is that input, defaulting to 0."""
GAMMA_CALCESTRUZZO_KNM3 = 25.0  # buried literal in AR24 (`*25`), matching plinti_isolati's own constant.


def peso_proprio_kN(
    ax_m: float, by_m: float, h_plinto_m: float, gamma_g1: float, carico_aggiuntivo_kN: float,
    *, gamma_calcestruzzo_knm3: float = GAMMA_CALCESTRUZZO_KNM3,
) -> float:
    """Total unfavourable-case self-weight of the plinth slab plus the user's extra load, in kN."""
    if ax_m <= 0 or by_m <= 0 or h_plinto_m <= 0:
        raise ValueError(f"ax_m, by_m, h_plinto_m must be > 0, got {ax_m}, {by_m}, {h_plinto_m}")
    if gamma_g1 <= 0:
        raise ValueError(f"gamma_g1 must be > 0, got {gamma_g1}")
    volume_m3 = ax_m * by_m * h_plinto_m
    return volume_m3 * gamma_calcestruzzo_knm3 * gamma_g1 + carico_aggiuntivo_kN
