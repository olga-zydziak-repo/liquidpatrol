"""r02/observe_guidance.py — naprowadzanie OBSERVE (bearing-only, pierścień D_safe) — R4/§2.4.

Estymata celu w NED z detekcji obrazowej (BEZ rdzenia uczonego — R-DIV-3): rzut **bearing-only**
kierunku z `(cx,cy)` kanału na STAŁĄ wysokość intruza, potem setpoint na **pierścieniu D_safe**
(dron trzyma dystans, „bez zbliżania" — §2.4). Setpoint OBSERVE jest zwykłym `target` NED podanym
osłonie z `mode=M_OBSERVE`: R-G (geofence) NADRZĘDNY łapie go za płotem (G3) — tu NIE clampujemy do
R_E (to zadanie osłony), respektujemy tylko wysokość patrolu i „nie zbliżaj się" (D_safe).

Założenia geometryczne (jawnie, do rewizji pomiarem bramki):
  - kamera boresight = body +x (do przodu), poziomo; obrót świata przez yaw drona (z telemetrii);
  - hfov=1.74 rad (mono_cam/model.sdf), vfov z aspektu obrazu;
  - intruz na stałej wysokości INTRUDER_ALT (z SDF aktora); dron na ALT_M.
NED: x=Północ, y=Wschód, z=Dół. yaw=0 → nos na Północ (+x).

R02-A3: OBSERVE respektuje v_max/clampy — setpoint to POZYCJA (PX4 clampuje prędkość MPC_XY_VEL_MAX);
guidance nie proponuje teleportu (krok ograniczony do horyzontu D_safe wokół estymaty).
"""
from __future__ import annotations
import math

from r02.config_r02 import (IMG_W, IMG_H, D_SAFE_M, INTRUDER_ALT_M, ALT_M)

HFOV = 1.74                                   # rad (mono_cam/model.sdf)
VFOV = 2.0 * math.atan(math.tan(HFOV / 2.0) * (IMG_H / IMG_W))   # z aspektu 320×240


def bearing_from_pixel(cx, cy):
    """Kąty (az, el) wiązki względem boresightu kamery (body). cx,cy ∈[0,1] (0.5=środek).
    az>0 = cel na prawo (−y? patrz world), el>0 = cel powyżej. Model liniowy tan-FOV."""
    # offset od środka w [-0.5,0.5]; +x_pix w prawo, +y_pix w dół
    dx = (cx - 0.5)
    dy = (cy - 0.5)
    az = math.atan(2.0 * dx * math.tan(HFOV / 2.0))     # azymut (lewo/prawo)
    el = math.atan(2.0 * (-dy) * math.tan(VFOV / 2.0))  # elewacja (góra/dół); −dy bo piksel-y w dół
    return az, el


def estimate_intruder_ned(pos, yaw, cx, cy, intruder_alt=INTRUDER_ALT_M):
    """Estymata pozycji intruza w NED (bearing-only rzut na wysokość intruza).
    pos: [N,E,D] drona; yaw: rad (0=Północ); (cx,cy): środek boxa z kanału.
    Zwraca (N,E,D) intruza LUB None gdy wiązka nie schodzi do płaszczyzny (el prowadzi w górę,
    a intruz poniżej — brak przecięcia)."""
    az, el = bearing_from_pixel(cx, cy)
    # kierunek wiązki w body: przód=+x, prawo=+y (NED body), w dół=+z
    # az obraca wokół osi z (yaw-podobnie), el podnosi/opuszcza
    # wektor body:
    bx = math.cos(el) * math.cos(az)
    by = math.cos(el) * math.sin(az)
    bz = -math.sin(el)                     # el>0 (cel wyżej) → wiązka w górę → z<0 (NED dół dodatni)
    # obrót do świata przez yaw (wokół z, NED)
    wx = math.cos(yaw) * bx - math.sin(yaw) * by
    wy = math.sin(yaw) * bx + math.cos(yaw) * by
    wz = bz
    # przecięcie z płaszczyzną z = -intruder_alt (NED down); dron na pos[2]
    dz_plane = (-intruder_alt) - pos[2]
    if abs(wz) < 1e-6:
        # wiązka pozioma — użyj rzutu na stały zasięg (fallback: D_safe przed dronem)
        t = D_SAFE_M
    else:
        t = dz_plane / wz
        if t <= 0:
            # wiązka odchodzi od płaszczyzny intruza — brak sensownego przecięcia
            return None
    return (pos[0] + t * wx, pos[1] + t * wy, -intruder_alt)


def observe_setpoint(pos, yaw, channel_val, d_safe=D_SAFE_M, alt=ALT_M):
    """Setpoint OBSERVE (NED) = pierścień D_safe między dronem a estymatą intruza (dystans, bez
    zbliżania). channel_val: ChannelValue (cx,cy,...) z kanału. Zwraca [N,E,D] LUB None (brak estymaty).
    Gdy dron już dalej niż D_safe — trzyma bieżącą pozycję poziomą (nie zbliża się); gdy bliżej —
    cofa się na pierścień. Wysokość = ALT patrolu (z=-alt)."""
    if channel_val is None:
        return None
    est = estimate_intruder_ned(pos, yaw, channel_val.cx, channel_val.cy)
    if est is None:
        return None
    ex, ey = est[0], est[1]
    dx, dy = pos[0] - ex, pos[1] - ey
    d = math.hypot(dx, dy)
    if d < 1e-3:
        # dron na estymacie (degenerat) — cofnij na północ o D_safe deterministycznie
        return [ex - d_safe, ey, -alt]
    # punkt na pierścieniu D_safe od intruza, po linii intruz→dron
    ux, uy = dx / d, dy / d
    sp_x = ex + ux * d_safe
    sp_y = ey + uy * d_safe
    return [sp_x, sp_y, -alt]


def distance_to_estimate(pos, yaw, channel_val):
    """Dystans poziomy dron↔estymata (do metryki G2: d≥D_safe)."""
    if channel_val is None:
        return None
    est = estimate_intruder_ned(pos, yaw, channel_val.cx, channel_val.cy)
    if est is None:
        return None
    return math.hypot(pos[0] - est[0], pos[1] - est[1])


class ObserveController:
    """Stanowy kontroler OBSERVE — ZOH ESTYMATY ŚWIATA (nie piksela).

    ZNALEZISKO R3 (harness): bearing-only daje KIERUNEK w chwili detekcji. Punkt świata liczy się
    rzutując piksel przez pozę Z TEJ KLATKI. Reprojekcja starego piksela przez BIEŻĄCĄ pozę między
    detekcjami obraca estymatę z yaw drona → dodatnie sprzężenie yaw → WIROWANIE. Poprawnie: estymatę
    NED zamrażamy w chwili świeżej detekcji (poza z tej klatki) i naprowadzamy na STAŁY punkt świata
    aż do następnej detekcji (ZOH estymaty, spójny z ZOH-age kanału).

    Użycie: `on_detection(pos, yaw, box)` przy KAŻDEJ świeżej klatce z boxem (ENTRY/REFRESH);
    `setpoint(pos)` / `yaw_cmd(pos)` w każdym ticku osłony; `reset()` przy EXPIRE."""

    # margines standoff NAD twardą podłogą D_safe: naprowadzanie celuje w d_safe+margin, by przy
    # nieświeżej (ZOH ≤1 s) estymacie i dyskretnym ruchu (v_max) transienty NIE zeszły pod D_safe.
    # Kryterium bramki pozostaje na D_safe (twarda podłoga); guidance projektowane z zapasem.
    STANDOFF_MARGIN_M = 1.5

    def __init__(self, d_safe=D_SAFE_M, alt=ALT_M):
        self.d_safe = d_safe; self.alt = alt
        self.ring = d_safe + self.STANDOFF_MARGIN_M
        self.est = None                    # zamrożony punkt świata (N,E,D)

    def reset(self):
        self.est = None

    def on_detection(self, pos, yaw, box):
        """Świeża detekcja → przelicz i ZAMROŹ estymatę świata (poza z TEJ klatki)."""
        if box is None:
            return
        est = estimate_intruder_ned(pos, yaw, box.cx, box.cy)
        if est is not None:
            self.est = est

    def has_estimate(self):
        return self.est is not None

    def setpoint(self, pos):
        """Setpoint na pierścieniu D_safe wokół ZAMROŻONEJ estymaty (poziomy dystans, bez zbliżania)."""
        if self.est is None:
            return None
        ex, ey = self.est[0], self.est[1]
        dx, dy = pos[0] - ex, pos[1] - ey
        d = math.hypot(dx, dy)
        if d < 1e-3:
            return [ex - self.ring, ey, -self.alt]
        ux, uy = dx / d, dy / d
        return [ex + ux * self.ring, ey + uy * self.ring, -self.alt]   # pierścień d_safe+margin

    def yaw_cmd(self, pos):
        """Kurs na ZAMROŻONĄ estymatę (utrzymanie celu w FOV; stabilny — stały punkt świata)."""
        if self.est is None:
            return None
        return math.atan2(self.est[1] - pos[1], self.est[0] - pos[0])

    def h_distance(self, pos):
        """Poziomy dystans dron↔zamrożona estymata (metryka G2: d≥D_safe)."""
        if self.est is None:
            return None
        return math.hypot(pos[0] - self.est[0], pos[1] - self.est[1])
