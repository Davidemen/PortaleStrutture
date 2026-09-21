"""Oedometric (Terzaghi) settlement of a rectangular footing on layered soil — sheet `Edometrico`
(docs/specs/geo-cedimenti-edometrico.md). One composed `Tool` (`geo-cedimento-edometrico`), see
`tool.py`; step modules: `ingresso` (unit boundary), `carico` (q'), `tensione_indotta` (Δσ,
approssimato/Newmark), `modulo_edometrico` (Eed lookup), `righe` (per-slice ΔH,i), `profondita_critica`
(Z,crit), `cedimento` (wed(f))."""
