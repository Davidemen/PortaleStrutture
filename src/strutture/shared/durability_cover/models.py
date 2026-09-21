"""Literal types for exposure/durability lookups shared by the CA tool group."""
from typing import Literal

# Sheet 'Tabelle' col I/N — UNI 11104 exposure classes (durability, not the seismic X0/XC*
# used by ntc_site_seismic).
ExposureClass = Literal["X0", "XC1", "XC2", "XC3", "XC4"]

# Tabelle!M57:M61 "Gruppo" a/b/c -> "Condizioni ambientali".
EnvironmentalCondition = Literal["ordinarie", "aggressive", "molto aggressive"]

LoadCombination = Literal["frequente", "quasi permanente"]

ReinforcementSensitivity = Literal["sensibile", "poco sensibile"]

ReinforcementType = Literal["ordinaria", "precompressa"]

# NTC2018 §4.1.2.2.4.5 crack-width classes.
CrackWidthClass = Literal["w1", "w2", "w3"]

StructuralClass = Literal[1, 2, 3, 4, 5, 6]
