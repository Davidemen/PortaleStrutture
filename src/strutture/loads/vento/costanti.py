"""Named constants from the `Vento` sheet, tied to their NTC2018/Circolare clause."""

AIR_DENSITY_KG_M3 = 1.25  # Vento!H35, §3.3.6
PA_TO_KN_M2 = 1000.0  # Pa -> kN/m2 conversion used throughout §3.3.6
REFERENCE_RETURN_PERIOD_YEARS = 50.0  # Vento!H15's baked-in TR=50 renormalisation baseline; legacy_compat only
ALTITUDE_WARNING_THRESHOLD_M = 1500.0  # §3.3.1 note, Vento!L8
MAX_SEZIONI_SENZA_AVVISO = 1000  # Tabelle!M1/N1: soglia oltre la quale il foglio storicamente avvisa (non blocca)
