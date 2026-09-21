"""Esporta / Importa progetto: the only bridge between installs (no synchronisation). Pure functions; the
SQLite/memory repository does the actual writing."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from .interfaces import ProjectRepository
from .models import Elemento, Progetto, RevisioneElemento

FORMATO = "strutture-progetto"
VERSIONE_FORMATO = 1

ElementoConRevisioni = tuple[Elemento, tuple[RevisioneElemento, ...]]


class FormatoNonValido(ValueError):
    """The payload is not a `strutture-progetto` export, or its version is unsupported."""


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def esporta(progetto: Progetto, elementi: Iterable[ElementoConRevisioni], versione_app: str) -> dict:
    """Build the export payload for `progetto` and its elements (each with its full revision history)."""
    return {
        "formato": FORMATO,
        "versione": VERSIONE_FORMATO,
        "esportato": _utc_now_iso(),
        "app": versione_app,
        "progetto": _progetto_a_dict(progetto),
        "elementi": [_elemento_a_dict(elemento, revisioni) for elemento, revisioni in elementi],
    }


def _progetto_a_dict(progetto: Progetto) -> dict:
    return {
        "codice": progetto.codice,
        "nome": progetto.nome,
        "committente": progetto.committente,
        "note": progetto.note,
    }


def _elemento_a_dict(elemento: Elemento, revisioni: tuple[RevisioneElemento, ...]) -> dict:
    return {
        "strumento": elemento.strumento,
        "nome": elemento.nome,
        "inputs": elemento.inputs,
        "sintesi": elemento.sintesi,
        "stato": elemento.stato,
        "modalita": elemento.modalita,
        "versione_app": elemento.versione_app,
        "provenienza": elemento.provenienza,
        "revisioni": [
            {"revisione": r.revisione, "inputs": r.inputs, "sintesi": r.sintesi, "sigla": r.sigla,
             "nota": r.nota, "data": r.data}
            for r in revisioni
        ],
    }


def _valida_payload(payload: dict) -> None:
    if not isinstance(payload, dict) or "formato" not in payload:
        raise FormatoNonValido("file non riconosciuto: manca l'intestazione di formato")
    if payload.get("formato") != FORMATO:
        raise FormatoNonValido(f"formato non riconosciuto: atteso '{FORMATO}'")
    if payload.get("versione") != VERSIONE_FORMATO:
        raise FormatoNonValido(f"versione del formato non supportata: {payload.get('versione')!r}")
    progetto = payload.get("progetto")
    if not isinstance(progetto, dict) or not str(progetto.get("nome", "")).strip():
        raise FormatoNonValido("dati di progetto mancanti o incompleti (nome obbligatorio)")
    if not isinstance(payload.get("elementi", []), list):
        raise FormatoNonValido("l'elenco degli elementi non è valido")


def _nome_senza_conflitto(repository: ProjectRepository, codice: str, nome: str) -> str:
    oggi = _utc_now_iso()[:10]
    esistenti = repository.list_progetti(inclusi_eliminati=True)
    if any(p.codice == codice and p.nome == nome for p in esistenti):
        return f"{nome} (importato {oggi})"
    return nome


def importa(
    payload: dict, repository: ProjectRepository, strumenti_noti: frozenset[str]
) -> tuple[Progetto, tuple[str, ...]]:
    """Validate `payload`, create a NEW project (and its elements) with new ids, and never overwrite.

    Returns the created project and a tuple of Italian warning messages (e.g. unknown tools).
    """
    _valida_payload(payload)
    dati_progetto = payload["progetto"]
    codice = str(dati_progetto.get("codice", ""))
    nome = _nome_senza_conflitto(repository, codice, str(dati_progetto["nome"]))
    progetto = repository.crea_progetto(
        Progetto(codice=codice, nome=nome, committente=str(dati_progetto.get("committente", "")),
                  note=str(dati_progetto.get("note", "")))
    )

    avvisi: list[str] = []
    for dati_elemento in payload.get("elementi", []):
        avvisi.extend(_importa_elemento(repository, progetto.id, dati_elemento, strumenti_noti))
    return progetto, tuple(avvisi)


def _importa_elemento(
    repository: ProjectRepository, progetto_id: str, dati: dict, strumenti_noti: frozenset[str]
) -> list[str]:
    strumento = str(dati.get("strumento", ""))
    nome = str(dati.get("nome", ""))
    avvisi: list[str] = []
    if strumento not in strumenti_noti:
        avvisi.append(f"strumento sconosciuto '{strumento}': elemento '{nome}' importato comunque")
    repository.crea_elemento(
        Elemento(
            progetto_id=progetto_id,
            strumento=strumento,
            nome=nome,
            inputs=dict(dati.get("inputs", {})),
            sintesi=dict(dati.get("sintesi", {})),
            stato=dati.get("stato", "non_verificato"),
            modalita=dati.get("modalita", "standard"),
            versione_app=str(dati.get("versione_app", "")),
            provenienza=dict(dati.get("provenienza", {})),
        )
    )
    return avvisi
