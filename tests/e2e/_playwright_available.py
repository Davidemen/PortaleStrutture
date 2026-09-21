"""Whether `pytest-playwright` is installed in the current interpreter.

`pytest-playwright` is intentionally not a project dependency (DESIGN_SPEC §6.E): the suite
must still be importable so the default `pytest` run (`-m 'not e2e'`) never breaks.
"""
import importlib.util

PLAYWRIGHT_AVAILABLE = importlib.util.find_spec("playwright") is not None
