#!/usr/bin/env python3
"""results/ORTO_RECON/tools/orto_uklad.py — przeliczenie WGS84 (φ, λ) → PL-1992 (EPSG:2180) i odwrotnie (PROMPT_ORTO_S0 R1; 0 bootów).

Odwzorowanie Gaussa–Krügera na elipsoidzie GRS80 (a = 6 378 137 m, f = 1/298.257222101), południk osiowy 19°E, k0 = 0.9993,
x = N + (−5 300 000), y = E + 500 000 (EPSG:2180: oś 1 = northing x, oś 2 = easting y). Także PL-2000 strefa 6 (EPSG:2177: λ0 = 18°E,
k0 = 0.999923, y = E + 6 500 000) — arkusze edycji w układzie 2000 (wgs84_do_tm / tm_do_wgs84 z nazwą układu jak w WFS uklad_xy). Szeregi Krügera do n⁶ (dokładność ≪ 1 mm
w pasie Polski). Na stanowisku nie ma pyproj ani GDAL — wzory własne; sprawdzian: punkt wewnątrz poligonu arkusza zwróconego przez WFS
w EPSG:2180 dla zapytania w EPSG:4326 (orto_r1.py) oraz odwrotność do 1e-9°.
"""
import math

A_ELL = 6378137.0
F_ELL = 1 / 298.257222101
LON0 = math.radians(19.0)
K0 = 0.9993
FN, FE = -5300000.0, 500000.0

_n = F_ELL / (2 - F_ELL)
_A = A_ELL / (1 + _n) * (1 + _n ** 2 / 4 + _n ** 4 / 64 + _n ** 6 / 256)
_al = [None,
       _n / 2 - 2 * _n ** 2 / 3 + 5 * _n ** 3 / 16 + 41 * _n ** 4 / 180 - 127 * _n ** 5 / 288 + 7891 * _n ** 6 / 37800,
       13 * _n ** 2 / 48 - 3 * _n ** 3 / 5 + 557 * _n ** 4 / 1440 + 281 * _n ** 5 / 630 - 1983433 * _n ** 6 / 1935360,
       61 * _n ** 3 / 240 - 103 * _n ** 4 / 140 + 15061 * _n ** 5 / 26880 + 167603 * _n ** 6 / 181440,
       49561 * _n ** 4 / 161280 - 179 * _n ** 5 / 168 + 6601661 * _n ** 6 / 7257600,
       34729 * _n ** 5 / 80640 - 3418889 * _n ** 6 / 1995840,
       212378941 * _n ** 6 / 319334400]
_be = [None,
       _n / 2 - 2 * _n ** 2 / 3 + 37 * _n ** 3 / 96 - _n ** 4 / 360 - 81 * _n ** 5 / 512 + 96199 * _n ** 6 / 604800,
       _n ** 2 / 48 + _n ** 3 / 15 - 437 * _n ** 4 / 1440 + 46 * _n ** 5 / 105 - 1118711 * _n ** 6 / 3870720,
       17 * _n ** 3 / 480 - 37 * _n ** 4 / 840 - 209 * _n ** 5 / 4480 + 5569 * _n ** 6 / 90720,
       4397 * _n ** 4 / 161280 - 11 * _n ** 5 / 504 - 830251 * _n ** 6 / 7257600,
       4583 * _n ** 5 / 161280 - 108847 * _n ** 6 / 3991680,
       20648693 * _n ** 6 / 638668800]
_e = math.sqrt(F_ELL * (2 - F_ELL))


UKLADY = {"PL-1992": (math.radians(19.0), 0.9993, -5300000.0, 500000.0),             # EPSG:2180
          "PL-2000:S6": (math.radians(18.0), 0.999923, 0.0, 6500000.0)}            # EPSG:2177 (strefa 6, λ0 = 18°E)


def wgs84_do_tm(lat, lon, uklad="PL-1992"):
    """(φ, λ) w stopniach → (x northing, y easting) w układzie TM z UKLADY [m]."""
    lon0, k0, fn, fe = UKLADY[uklad]
    phi, lam = math.radians(lat), math.radians(lon) - lon0
    t = math.sinh(math.atanh(math.sin(phi)) - _e * math.atanh(_e * math.sin(phi)))
    xi = math.atan2(t, math.cos(lam))
    eta = math.atanh(math.sin(lam) / math.sqrt(1 + t * t))
    E = eta + sum(_al[j] * math.cos(2 * j * xi) * math.sinh(2 * j * eta) for j in range(1, 7))
    N = xi + sum(_al[j] * math.sin(2 * j * xi) * math.cosh(2 * j * eta) for j in range(1, 7))
    return k0 * _A * N + fn, k0 * _A * E + fe


def tm_do_wgs84(x, y, uklad="PL-1992"):
    lon0, k0, fn, fe = UKLADY[uklad]
    la, lo = _odwrot((x - fn) / (k0 * _A), (y - fe) / (k0 * _A))
    return la, math.degrees(math.radians(lo) + lon0)


def wgs84_do_2180(lat, lon):
    """(φ, λ) w stopniach → (x northing, y easting) EPSG:2180 [m]."""
    phi, lam = math.radians(lat), math.radians(lon) - LON0
    t = math.sinh(math.atanh(math.sin(phi)) - _e * math.atanh(_e * math.sin(phi)))
    xi = math.atan2(t, math.cos(lam))
    eta = math.atanh(math.sin(lam) / math.sqrt(1 + t * t))
    E = eta + sum(_al[j] * math.cos(2 * j * xi) * math.sinh(2 * j * eta) for j in range(1, 7))
    N = xi + sum(_al[j] * math.sin(2 * j * xi) * math.cosh(2 * j * eta) for j in range(1, 7))
    return K0 * _A * N + FN, K0 * _A * E + FE


def p2180_do_wgs84(x, y):
    """(x northing, y easting) EPSG:2180 → (φ, λ) w stopniach."""
    la, lo = _odwrot((x - FN) / (K0 * _A), (y - FE) / (K0 * _A))
    return la, math.degrees(math.radians(lo) + LON0)


def _odwrot(xi, eta):
    """(ξ, η) znormalizowane → (φ [°], Δλ [°] od południka osiowego)."""
    xi_ = xi - sum(_be[j] * math.sin(2 * j * xi) * math.cosh(2 * j * eta) for j in range(1, 7))
    eta_ = eta - sum(_be[j] * math.cos(2 * j * xi) * math.sinh(2 * j * eta) for j in range(1, 7))
    chi = math.asin(math.sin(xi_) / math.cosh(eta_))
    lam = math.atan2(math.sinh(eta_), math.cos(xi_))
    t0 = math.tan(chi)
    t = t0
    for _ in range(20):                                    # odwrócenie szerokości konforemnej (Newton)
        s = t / math.sqrt(1 + t * t)
        sig = math.sinh(_e * math.atanh(_e * s))
        tau = t * math.sqrt(1 + sig * sig) - sig * math.sqrt(1 + t * t)
        dtau = (t0 - tau) / math.sqrt(1 + tau * tau) * (1 + (1 - _e ** 2) * t * t) / ((1 - _e ** 2) * math.sqrt(1 + t * t))
        t += dtau
        if abs(dtau) < 1e-14:
            break
    return math.degrees(math.atan(t)), math.degrees(lam)


if __name__ == "__main__":
    for lat, lon in ((51.1015, 17.0870), (51.1125, 17.0840), (51.1027, 16.8858), (52.0, 19.0)):
        x, y = wgs84_do_2180(lat, lon)
        la, lo = p2180_do_wgs84(x, y)
        print(lat, lon, "→", round(x, 3), round(y, 3), "odwrotność Δ", f"{abs(la - lat):.2e}", f"{abs(lo - lon):.2e}")
        x2, y2 = wgs84_do_tm(lat, lon, "PL-2000:S6")
        la2, lo2 = tm_do_wgs84(x2, y2, "PL-2000:S6")
        print("   PL-2000:S6", round(x2, 3), round(y2, 3), "odwrotność Δ", f"{abs(la2 - lat):.2e}", f"{abs(lo2 - lon):.2e}")
