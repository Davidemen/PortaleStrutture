"""Sisma — NTC 2018 §3.2 seismic action spectrum tools.

Thin wrapper package: the site-hazard chain (Cu/VR/TR, Ss/Cc/ST/S, TB/TC/TD) is implemented once
in `strutture.shared.ntc_site_seismic` and only composed here. This package adds the pieces that
are specific to `sisma` and not reused elsewhere: comune enrichment, the η/q/q,v/η,v structural
factors (§3.2.3.5, §7.3.1, §7.3.3.2), and the Se(T)/Sd(T) spectrum sampling (§3.2.3.2.1).

See `docs/specs/sisma.md` and `docs/divergences/sisma.md`.
"""
