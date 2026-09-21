"""Constants for NTC2018 §4.1.2.3.5.1 (shear resistance without transverse reinforcement)."""

GAMMA_C = 1.5  # §4.1.2.1.1.1, partial factor for concrete (sheet B5, fixed constant, not an input)
ALPHA_CC = 0.85  # §4.1.2.1.1.1, long-term/loading-rate reduction factor
FCK_FROM_RCK_FACTOR = 0.83  # §11.2.10.1, fck = 0.83*Rck
FCK_RCK_TOLLERANZA = 0.05  # docs/architecture-batch2.md §4, warn when direct fck (sheet v2) deviates >5% from 0.83*Rck
K_SIZE_FACTOR_MAX = 2.0  # §4.1.2.3.5.1, k = 1+sqrt(200/d) <= 2
VMIN_COEFF = 0.035  # §4.1.2.3.5.1, vmin = 0.035*k^1.5*sqrt(fck)
RHO_L_MAX = 0.02  # §4.1.2.3.5.1, rho_l capped at 0.02
SIGMA_CP_MAX_FACTOR = 0.2  # §4.1.2.3.5.1, sigma_cp capped at 0.2*fcd
VRD1_COEFF = 0.18  # §4.1.2.3.5.1, first term coefficient
VRD1_SIGMA_CP_COEFF = 0.15  # §4.1.2.3.5.1, sigma_cp contribution in VRd1
VRD2_SIGMA_CP_COEFF = 0.15  # §4.1.2.3.5.1, sigma_cp contribution in VRd2 (vmin term)
