"""riepilogo_per_strumento (WORKBENCH_SPEC §25.2): the raw per-`stato` tally counts every entry
(GET /api/divergences/riepilogo, unchanged), but `correzioni`/`correzioni_ramo_nessuno` exclude
`tipo == "da_verificare"` doubts -- `shared/stato_progetto/provvisorio.py` must never see a doubt
counted as a correction pending/approved/rejected."""
import pytest

from strutture.shared.divergences.models import Divergence
from strutture.shared.divergences.riepilogo import riepilogo_per_strumento
from strutture.storage.models import Signoff, Stato


class _Signoffs:
    def __init__(self, stati: dict[str, str]) -> None:
        self._stati = stati

    def get(self, divergence_id: str) -> Signoff:
        return Signoff(
            divergence_id=divergence_id, stato=self._stati.get(divergence_id, "da_confermare"),
            sigla="ab", nota="", revisione=1,
        )


DUBBIO = Divergence(
    id="muro-sostegno/capacita-portante", titolo="Capacità portante", tipo="da_verificare",
    strumenti=("muro-sostegno",), foglio="Da verificare", corretto="Da verificare",
)
CORREZIONE = Divergence(
    id="muro-sostegno/copriferro", titolo="Copriferro minimo", tipo="errore_foglio",
    strumenti=("muro-sostegno",), ramo="nessuno", motivo_senza_ramo="Sempre corretto, nessun caso Excel",
    foglio="Usa 20 mm", corretto="Da NTC2018",
)


@pytest.mark.unit
def test_pending_doubt_is_not_counted_as_a_correction() -> None:
    voce = riepilogo_per_strumento((DUBBIO,), _Signoffs({}))["muro-sostegno"]
    assert voce["da_confermare"] == 1  # GET /api/divergences/riepilogo: unchanged, counts the doubt
    assert voce["da_verificare"] == 1
    assert voce["correzioni"]["da_confermare"] == 0  # but never as a pending CORRECTION
    assert voce["correzioni_ramo_nessuno"]["da_confermare"] == 0


@pytest.mark.unit
def test_a_real_correction_alongside_a_doubt_still_counts_normally() -> None:
    voce = riepilogo_per_strumento((DUBBIO, CORREZIONE), _Signoffs({}))["muro-sostegno"]
    assert voce["da_confermare"] == 2  # both pending, the doubt included
    assert voce["correzioni"]["da_confermare"] == 1  # only the real correction
    assert voce["correzioni_ramo_nessuno"]["da_confermare"] == 1
    assert voce["da_verificare"] == 1
