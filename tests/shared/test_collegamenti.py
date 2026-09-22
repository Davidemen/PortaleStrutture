"""Typed links between tools (phase 5): an output (or forwarded input) field declares
`provides: "<chiave>"`, an input field declares `accepts: "<chiave>"`; the registry resolves who feeds
whom, and its checks guarantee every key has both ends and compatible values."""
from typing import Literal

import pytest
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.collegamenti import problemi, raccogli, valori_forniti
from strutture.shared.report import success
from strutture.shared.tool import Tool, discover

pytestmark = pytest.mark.unit


class SitoIn(BaseModel):
    model_config = ConfigDict(frozen=True)
    ag_g: float = Field(json_schema_extra={"provides": "sito.ag_g"})
    suolo: Literal["A", "B", "C"] = Field(default="B", json_schema_extra={"provides": "sito.suolo"})


class Amplificazione(BaseModel):
    model_config = ConfigDict(frozen=True)
    s: float = Field(json_schema_extra={"provides": "sito.s"})


class SitoOut(BaseModel):
    model_config = ConfigDict(frozen=True)
    amplificazione: Amplificazione
    righe: tuple[Amplificazione, ...] = ()  # rows never provide: a link value must be one scalar


class MuroIn(BaseModel):
    model_config = ConfigDict(frozen=True)
    ag_g: float = Field(json_schema_extra={"accepts": "sito.ag_g"})
    s: float = Field(default=1.0, json_schema_extra={"accepts": "sito.s"})
    suolo: Literal["A", "B", "C", "D", "E"] = Field(default="C", json_schema_extra={"accepts": "sito.suolo"})


class Vuoto(BaseModel):
    model_config = ConfigDict(frozen=True)
    x: float = 0.0


def _run_sito(inputs: SitoIn):
    return success(SitoOut(amplificazione=Amplificazione(s=1.2 * inputs.ag_g)), inputs)


SITO = Tool("sito", "Sito", "Prova", "-", SitoIn, SitoOut, _run_sito)
MURO = Tool("muro", "Muro", "Prova", "-", MuroIn, Vuoto, lambda i: success(Vuoto(), i))
TOOLS = {SITO.name: SITO, MURO.name: MURO}


def test_registry_pairs_every_key_with_its_providers_and_consumers() -> None:
    registro = raccogli(TOOLS)
    assert set(registro) == {"sito.ag_g", "sito.s", "sito.suolo"}
    ag = registro["sito.ag_g"]
    assert [(f.strumento, f.percorso, f.ingresso) for f in ag.fornitori] == [("sito", "ag_g", True)]
    assert [(c.strumento, c.campo) for c in ag.consumatori] == [("muro", "ag_g")]
    s = registro["sito.s"]
    assert [(f.strumento, f.percorso, f.ingresso) for f in s.fornitori] == [("sito", "amplificazione.s", False)]


def test_values_provided_by_a_run_are_read_from_inputs_echo_and_data() -> None:
    from strutture.shared.tool import execute

    report = execute(SITO, {"ag_g": 0.25}).model_dump(mode="json")
    assert valori_forniti(SITO, report) == {"sito.ag_g": 0.25, "sito.suolo": "B", "sito.s": pytest.approx(0.3)}


def test_a_failed_run_provides_only_its_inputs() -> None:
    assert valori_forniti(SITO, {"ok": False, "data": None, "inputs_echo": {"ag_g": 0.1, "suolo": "A"}}) == {"sito.ag_g": 0.1, "sito.suolo": "A"}


def test_no_problems_on_a_consistent_registry() -> None:
    assert problemi(TOOLS) == ()


def test_a_key_without_consumer_or_without_provider_is_a_problem() -> None:
    class SoloIn(BaseModel):
        model_config = ConfigDict(frozen=True)
        q: float = Field(json_schema_extra={"accepts": "orfano.q"})
        p: float = Field(json_schema_extra={"provides": "morto.p"})

    solo = Tool("solo", "Solo", "Prova", "-", SoloIn, Vuoto, lambda i: success(Vuoto(), i))
    trovati = problemi({**TOOLS, "solo": solo})
    assert "orfano.q: accettata da solo.q ma nessuno strumento la fornisce" in trovati
    assert "morto.p: fornita da solo.p ma nessuno strumento la accetta" in trovati


def test_enum_values_of_the_provider_must_be_accepted_by_the_consumer() -> None:
    class StrettoIn(BaseModel):
        model_config = ConfigDict(frozen=True)
        suolo: Literal["A", "B"] = Field(default="A", json_schema_extra={"accepts": "sito.suolo"})

    stretto = Tool("stretto", "Stretto", "Prova", "-", StrettoIn, Vuoto, lambda i: success(Vuoto(), i))
    (problema,) = problemi({**TOOLS, "stretto": stretto})
    assert problema == "sito.suolo: sito.suolo fornisce il valore 'C' che stretto.suolo non accetta"


def test_malformed_key_is_a_problem() -> None:
    class BruttaIn(BaseModel):
        model_config = ConfigDict(frozen=True)
        x: float = Field(json_schema_extra={"provides": "Sito AG"})

    brutta = Tool("brutta", "Brutta", "Prova", "-", BruttaIn, Vuoto, lambda i: success(Vuoto(), i))
    assert any("chiave 'Sito AG' non valida" in p for p in problemi({"brutta": brutta, **TOOLS}))


def test_the_real_registry_is_consistent_and_has_the_first_links() -> None:
    tools = discover()
    assert problemi(tools) == ()
    registro = raccogli(tools)
    assert {c.strumento for c in registro["sito.ag_g"].consumatori} >= {"muro-sostegno", "fond-trave-collegamento"}
    assert {f.strumento for f in registro["sito.ag_g"].fornitori} >= {"sisma-parametri-sito"}
    assert [c.strumento for c in registro["trave.sigma_s_rara_MPa"].consumatori] == ["ca-sle-limitazione-tensioni"]


def test_the_section_tool_feeds_the_column_tools_with_its_governing_m_rd() -> None:
    registro = raccogli(discover())
    link = registro["sezione.mrd_x_kNm"]
    assert [(f.strumento, f.percorso) for f in link.fornitori] == [("ca-sezione-dominio-mn", "resistenze_governante.mrd_x_pos_kNm")]
    assert {c.strumento for c in link.consumatori} == {"ca-pilastro-rettangolare", "ca-pilastro-circolare"}
