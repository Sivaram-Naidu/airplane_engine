"""
US customary -> SI conversions for display.

pyCycle computes internally in US units (lbf, lbm/s, degR, ft). We keep the model in
those units and convert only at the output boundary, the same way an app stores
UTC and converts to local time only in the UI.

All factors are exact by definition (NIST SP 811, Appendix B, 2008 edition):
  1 lbm  = 0.45359237 kg          (exact, international pound, 1959)
  1 lbf  = 4.4482216152605 N      (exact: 1 lbm x standard gravity 9.80665 m/s^2)
  1 ft   = 0.3048 m               (exact)
  1 degR = 5/9 K                  (exact; both scales start at absolute zero)
  1 hp   = 745.69987158227022 W   (mechanical horsepower, 550 ft*lbf/s)
  1 psi  = 6894.757293168 Pa      (lbf/in^2)
"""

LBM_TO_KG = 0.45359237
LBF_TO_N = 4.4482216152605
FT_TO_M = 0.3048
DEGR_TO_K = 5.0 / 9.0
HP_TO_KW = 0.74569987158227022
PSI_TO_KPA = 6.894757293168

# TSFC: lbm of fuel per hour per lbf of thrust -> grams per second per kN of thrust.
# = 453.59237 g / (4.4482216152605e-3 kN * 3600 s) ~= 28.3254
TSFC_US_TO_SI = (LBM_TO_KG * 1000.0) / (LBF_TO_N / 1000.0 * 3600.0)


def lbf_to_kn(x):
    return x * LBF_TO_N / 1000.0


def lbm_s_to_kg_s(x):
    return x * LBM_TO_KG


def degr_to_k(x):
    return x * DEGR_TO_K


def degr_to_c(x):
    return degr_to_k(x) - 273.15


def ft_to_m(x):
    return x * FT_TO_M


def hp_to_kw(x):
    return x * HP_TO_KW


def psi_to_kpa(x):
    return x * PSI_TO_KPA


def tsfc_us_to_si(x):
    """lbm/(lbf*h) -> g/(kN*s)."""
    return x * TSFC_US_TO_SI
