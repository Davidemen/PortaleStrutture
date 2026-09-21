"""Divergence register: models, loader and the `legacy()` code marker."""
from .loader import DATA_DIR, load_register, register_by_id
from .marker import legacy
from .models import Divergence, Tipo

__all__ = ["DATA_DIR", "Divergence", "Tipo", "legacy", "load_register", "register_by_id"]
