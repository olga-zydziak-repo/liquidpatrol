"""r02/mti.py — MTI (moving-target indication) klasyczna wizja, ZERO komponentów uczonych (C-A3, PRE_MTI).

Potok (PRE_MTI R2): derotacja `H = K·R(Δq)·K⁻¹` (kompensacja ego-motion ROTACYJNEGO z XRCE vehicle_attitude;
translacja/paralaksa NIE kompensowana — nazwana słabość) → różnica klatek → próg → morfologia → komponenty
spójne → filtry (rozmiar, spójność czasowa). Filtry adresują WYŁĄCZNIE NAZWANE FP z inwentarza R2 (bez
dodawania filtrów bez nazwanego FP). Brama ENTRY = STRUKTURA ∧ MTI (nigdy MTI samodzielnie).

Intrinsics (PRE_MTI R1, z mono_cam/model.sdf): fx=fy=270, cx=320, cy=240, 640×480.
Kwaternion: `VehicleAttitude.q = [w,x,y,z]` rotacja FRD→NED (Hamilton). Kamera forward = body +X (FRD).
Ramka optyczna (CV): z=forward(+X_frd), x=right(+Y_frd), y=down(+Z_frd).
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import cv2

# --- intrinsics (PRE_MTI R1) -------------------------------------------------
FX = FY = 270.0
CX, CY = 320.0, 240.0
IMG_W, IMG_H = 640, 480
K = np.array([[FX, 0, CX], [0, FY, CY], [0, 0, 1]], dtype=np.float64)
K_INV = np.linalg.inv(K)
# FRD → OPT (stały): x_opt=y_frd, y_opt=z_frd, z_opt=x_frd
C_FRD2OPT = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], dtype=np.float64)


@dataclass(frozen=True)
class MTIParams:
    """Parametry potoku. KAŻDY filtr wskazuje NAZWANY FP z inwentarza R2 (bez ślepych filtrów)."""
    diff_thr: int = 22               # próg intensywności residuum
    open_k: int = 3                  # morfologia OPEN — usuwa sól/pieprz (residuum derotacji szybki-yaw)
    close_k: int = 5                 # morfologia CLOSE — spójność blobu
    border_erode: int = 10           # erozja ważnego regionu — FP: artefakt KRAWĘDZI kadru po warpie
    min_area_px: int = 8             # FP: drobne speckle residuum derotacji (szybki yaw)
    max_area_frac: float = 0.20      # FP: całokadrowa mis-kompensacja / pas horyzontu
    # spójność czasowa (track-before-detect): cel KOHERENTNY persystuje, paralaksa gruntu MIGOCZE.
    # persist_m/window podniesione (val1: 53 comp/klatkę paralaksy → potrzeba twardszej persystencji).
    persist_m: int = 3               # komponent w ≥m z ostatnich M klatek (potwierdzenie tracku)
    persist_window: int = 4          # M
    persist_move_thr: float = 0.10   # maks. ruch środka (znorm.) między klatkami dla „ten sam" komponent


def quat_to_R(q) -> np.ndarray:
    """Kwaternion [w,x,y,z] (Hamilton, FRD→NED) → macierz rotacji R_ned<-frd (3×3, ortonormalna)."""
    w, x, y, z = float(q[0]), float(q[1]), float(q[2]), float(q[3])
    n = (w * w + x * x + y * y + z * z) ** 0.5
    if n < 1e-9:
        return np.eye(3)
    w, x, y, z = w / n, x / n, y / n, z / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ], dtype=np.float64)


def rel_rotation_opt(q_prev, q_cur) -> np.ndarray:
    """Rotacja OPTYCZNA sceny NED-stałej z klatki[t-Δ] do klatki[t].
    R_rel_frd = R(q_cur)^T · R(q_prev)  (mapuje wektory body(t-Δ)→body(t) dla punktu stałego w NED).
    R_rel_opt = C · R_rel_frd · C^T."""
    R_prev = quat_to_R(q_prev); R_cur = quat_to_R(q_cur)
    R_rel_frd = R_cur.T @ R_prev
    return C_FRD2OPT @ R_rel_frd @ C_FRD2OPT.T


def homography(R_opt) -> np.ndarray:
    """H = K·R_opt·K⁻¹ — mapuje piksel klatki[t-Δ] → piksel klatki[t] (scena w nieskończoności)."""
    return K @ R_opt @ K_INV


def warp_prev(prev_frame, H):
    """Warp klatki[t-Δ] do ramki [t]. Zwraca (warped, valid_mask). valid=1 gdzie warp ma dane."""
    h, w = prev_frame.shape[:2]
    warped = cv2.warpPerspective(prev_frame, H, (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
    ones = np.full((h, w), 255, dtype=np.uint8)
    valid = cv2.warpPerspective(ones, H, (w, h), flags=cv2.INTER_NEAREST, borderValue=0)
    return warped, (valid > 127).astype(np.uint8)


def motion_components(prev_frame, q_prev, cur_frame, q_cur, params: MTIParams | None = None):
    """Derotacja→diff→próg→morfologia→komponenty. Zwraca (components, debug).
    components: lista {cx,cy,w,h,area_px,area_frac} znormalizowanych [0,1]. Bez uczenia."""
    p = params or MTIParams()
    prev = prev_frame if prev_frame.ndim == 2 else prev_frame[..., 0]
    cur = cur_frame if cur_frame.ndim == 2 else cur_frame[..., 0]
    h, w = cur.shape[:2]
    R_opt = rel_rotation_opt(q_prev, q_cur)
    H = homography(R_opt)
    warped, valid = warp_prev(prev, H)
    # erozja ważnego regionu — odetnij artefakt KRAWĘDZI kadru (NAZWANY FP). BORDER_CONSTANT=0 KONIECZNE:
    # przy warpie ~identyczności valid=pełne; domyślne BORDER_REPLICATE zostawiłoby krawędź (śmigła/artefakty
    # brzegu przeżywają). CONSTANT 0 traktuje brzeg kadru jako nieważny → erozja zawsze zjada margines.
    if p.border_erode > 0:
        vk = np.ones((p.border_erode * 2 + 1, p.border_erode * 2 + 1), np.uint8)
        valid = cv2.erode(valid, vk, borderType=cv2.BORDER_CONSTANT, borderValue=0)
    diff = cv2.absdiff(cur.astype(np.uint8), warped.astype(np.uint8))
    diff = diff * valid                      # tylko region z ważnymi danymi warp
    _, mask = cv2.threshold(diff, p.diff_thr, 255, cv2.THRESH_BINARY)
    if p.open_k > 1:
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((p.open_k, p.open_k), np.uint8))
    if p.close_k > 1:
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((p.close_k, p.close_k), np.uint8))
    n, _, stats, cent = cv2.connectedComponentsWithStats(mask, connectivity=8)
    max_area = p.max_area_frac * w * h
    m = p.border_erode                                   # margines krawędzi kadru
    comps = []
    for i in range(1, n):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < p.min_area_px or area > max_area:      # NAZWANE FP: speckle / całokadrowa
            continue
        bx, by, bw, bh = (stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP],
                          stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT])
        # NAZWANY FP: śmigła/artefakty KRAWĘDZI — odrzuć komponent DOTYKAJĄCY marginesu kadru
        # (cel operacyjny jest CENTRALNY — edge-margin struktury i tak by go wymagał).
        if m > 0 and (bx <= m or by <= m or bx + bw >= w - m or by + bh >= h - m):
            continue
        cxc, cyc = float(cent[i][0]), float(cent[i][1])
        comps.append({"cx": cxc / w, "cy": cyc / h, "w": bw / w, "h": bh / h,
                      "area_px": area, "area_frac": round(area / (w * h), 5)})
    dbg = {"n_raw": n - 1, "n_kept": len(comps), "diff_max": int(diff.max()),
           "valid_frac": round(float(valid.mean()), 3)}
    return comps, dbg


class MTITracker:
    """Strumieniowy MTI z buforem klatek + attitude (spójność czasowa). Używany przez detector_node.
    Parowanie klatka↔attitude wykonuje WOŁAJĄCY (XRCE vehicle_attitude, PRE_MTI R1) — tu dostaje już parę."""

    def __init__(self, params: MTIParams | None = None, delta: int = 3):
        # delta=3 klatki @15 Hz ≈ 200 ms — baseline dopasowany do dynamiki celu (~3 m/s → ~5 px @7 m);
        # delta=1 (66 ms) był za krótki (val1: cov_gate 0.61 — MTI ślepy przy niskim ruchu względnym).
        self.p = params or MTIParams()
        self.delta = delta                       # o ile klatek wstecz para
        self.buf = []                            # [(frame, q)] ostatnie klatki
        self.history = []                        # [lista komponentów] ostatnich okien (do spójności czasowej)

    def push(self, frame, q):
        """Dodaj klatkę+quaternion; zwróć komponenty MTI SPÓJNE CZASOWO (po filtrze persystencji)."""
        self.buf.append((frame, q))
        if len(self.buf) > self.delta + 1:
            self.buf.pop(0)
        if len(self.buf) < self.delta + 1:
            self.history.append([]); self._trim(); return [], {"warmup": True}
        prev_frame, q_prev = self.buf[0]
        cur_frame, q_cur = self.buf[-1]
        comps, dbg = motion_components(prev_frame, q_prev, cur_frame, q_cur, self.p)
        self.history.append(comps); self._trim()
        consistent = self._temporal_filter(comps)
        dbg["n_consistent"] = len(consistent)
        return consistent, dbg

    def _trim(self):
        if len(self.history) > self.p.persist_window:
            self.history.pop(0)

    def _temporal_filter(self, comps):
        """Zachowaj komponent obecny w ≥persist_m z ostatnich persist_window klatek blisko tej samej pozycji.
        NAZWANY FP: transient (residuum derotacji szybki-yaw, losowe speckle paralaksy) NIE persystuje."""
        if self.p.persist_m <= 1:
            return comps
        out = []
        for c in comps:
            hits = 0
            for past in self.history[-self.p.persist_window:]:
                if any(abs(pc["cx"] - c["cx"]) <= self.p.persist_move_thr and
                       abs(pc["cy"] - c["cy"]) <= self.p.persist_move_thr for pc in past):
                    hits += 1
            if hits >= self.p.persist_m:
                out.append(c)
        return out


def box_matches_component(box, components, center_thr: float = 0.12) -> bool:
    """STRUKTURA ∧ MTI: czy box strukturalny (cx,cy) pokrywa się z komponentem MTI (środek ≤ center_thr).
    box: obiekt z .cx/.cy lub krotka (cx,cy,...). Zwraca bool (koincydencja = MTI potwierdza kandydata)."""
    if box is None or not components:
        return False
    bcx = box.cx if hasattr(box, "cx") else box[0]
    bcy = box.cy if hasattr(box, "cy") else box[1]
    for c in components:
        if abs(c["cx"] - bcx) <= center_thr and abs(c["cy"] - bcy) <= center_thr:
            return True
    return False
