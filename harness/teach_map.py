#!/usr/bin/env python3
"""harness/teach_map.py — producent poprawki z mapy własnego lotu (PRE_TEACH §4–§5, PROMPT_TEACH_S1 §1.1). Nowy plik.

Używany WYŁĄCZNIE w gałęzi TEACH_MODE=1 procesu harness/nadir_obs.py (obok NADIR_MODE=1) zamiast harness/nadir_fix.Rama;
interfejs producenta ramy jak Rama: stan d_ne, t_fix, p_fix_ne, seq; obserwacja klatki → datagram stanu ramy (ten sam kształt
co dotąd: t „fx”, seq, t_frame, ok, tryb „jeden”, kosz 0, p_fix_ne, p_ekf_fix, d_ne, t_fix). Szczegóły klatki trafiają do
`self.rejestr` (wiersz rejestru, nie datagram).

Tor odniesienia (READ-ONLY, import, nie kopia): results/TEACH_RECON2/tools/teach2.py z ad1e71fd (sha256 07925633…) i jego zależności
results/TEACH_RECON/tools/teach_r34.py (Dop: SIFT po CLAHE, knn 2 + iloraz 0.8, RANSAC podobieństwa; pokrycie; stałe),
results/ORTO_RECON/tools/orto_r2.py (Kam: kamera w dół z przypiętego modelu x500_nadir2_flow) i orto_r3.py (Prost: prostowanie przy
postawie i wysokości EKF, 0.1 m/px, ±15 m). Cechy wyłącznie SIFT (PRE_TEACH §3.3), mapa M4 (§4).
Trzy fazy (PROMPT_TEACH_S1 §1.1):
  mapa         (flaga GNSS = 1; klatki z EKF i wysokością −z_EKF ≥ 6 m jak seria „przed” reconu): decyzja klatki kluczowej z pozy
               EKF (pokrycie śladu < 70 %, siatka 0.5 m), cechy kadru, wiązania. Klatka wchodzi do mapy dopiero po nadejściu
               następnej klatki z flagą 1 albo przy zamknięciu, gdy jej czas < chwila flagi (bufor jednej klatki — żadna klatka
               z czasem ≥ chwila flagi nie wchodzi do mapy, nawet gdy wiadomość flagi spóźni się wobec obrazu);
  zamknięcie   (pierwsza klatka przy fladze 0): zbiór wiązań jak w definicji reconu (każdy kadr mapy z ≤ 3 klatkami kluczowymi
               o największym pokryciu przewidywanym z EKF spośród wszystkich wybranych do flagi, pokrycie ≥ 30 %, kadr kluczowy
               z sobą samym r = 0) i georeferencja M4 (teach2.rozwiaz: Gauss–Newton 6 iteracji, wagi 1 / 5 / 0.05, skala 1),
               rozwiązana raz. Dopasowania wiązań liczone z wyprzedzeniem w fazie mapy: przy kadrze — z klatkami jego bieżącej
               trójki; przy nowej klatce kluczowej k — z kadrami, do których trójki k wchodzi (trójka zbioru rosnącego zmienia
               się tylko o nową klatkę, więc w chwili zamknięcia wszystkie pary są policzone; brakująca para liczona wtedy
               i zliczana w rejestrze);
  lokalizacja  (każdy kadr po zamknięciu): łańcuch teach2.lancuch dla M4 / SIFT — pred = EKF + Δ, τ = t − t_fix (t_fix od chwili
               flagi), kandydaci: do 3 klatek kluczowych o największym pokryciu > 0, poprawka z klatki o największej liczbie
               zgodnych, reguła a12_geo0_g1.5 (zgodne ≥ 12 ∧ |poprawka − pred| ≤ 1.5 + 3τ). Wariant pokrycia kandydatów
               (PROMPT_TEACH_S1 §4 W4): „K” jak recon (oba kwadraty o boku kadru bieżącego) albo „K′” (kwadrat kadru z bieżącej
               wysokości i kwadrat klatki kluczowej z wysokości, na której powstała; część wspólna / pole kwadratu kadru).
Przed pierwszą przyjętą poprawką Δ = 0 i t_fix datagramu = None (osłona liczy τ od wejścia w utratę, pole braku poprawki).
Obraz wejściowy: BGR (jak render reconu z cv2.imread); proces nadir_obs konwertuje RGB z gz do BGR.
PROMPT_TEACH_S2 §1 (TEACH-S2): F2 — klatka w utracie przy mapie bez żadnego kadru nie zamyka mapy (bufor pusty albo kadr z bufora
z czasem ≥ chwila flagi — odrzucony), wiersz ma fazę „przed_mapa”; zamknięcie raz, przy pierwszej klatce w utracie z mapą niepustą.
F3 — rejestr zamknięcia (georef) niesie pełną listę wiązań [czas kadru, klatka kluczowa, r_E, r_N, zgodne, przyjęte].
ANEKS_TEACH-3 §3.2 (TEACH-3): w locie producent dostaje flagę jako stan przy klatce, bez chwili flagi (t_flagi=None); utrata = flaga 0
przy klatce; kadr z bufora wtedy nie wchodzi do mapy (wchodzi tylko, gdy po nim nadeszła klatka z flagą 1); chwila zamknięcia = czas
pierwszej klatki w utracie i od niej τ. Tryb cienia i replay z podaną chwilą bez zmian.
"""
from __future__ import annotations

import hashlib
import math
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TOR = os.path.join(ROOT, "results/TEACH_RECON2/tools")
if _TOR not in sys.path:
    sys.path.insert(0, _TOR)
import teach2 as T2                                     # noqa: E402  tor odniesienia (READ-ONLY)

T = T2.T                                                # teach_r34: Dop, pokrycie, stałe
R2, R3, NF = T2.R2, T2.R3, T2.NF
RODZAJ = "K1_SIFT"
WARIANT_MAPY = "M4"
H_MIN = 6.0                                             # seria „przed” reconu (results/TEACH_RECON/tools/teach_r2.H_MIN)
WARIANTY_K = ("K", "K′")
PLIKI_TORU = ("results/TEACH_RECON2/tools/teach2.py", "results/TEACH_RECON/tools/teach_r34.py",
              "results/ORTO_RECON/tools/orto_r2.py", "results/ORTO_RECON/tools/orto_r3.py")
SHA_TEACH2 = "07925633a8447c1d7b1bfa0beba0c8d514ce92a869d4e666047a61c5dd5d744d"


def sumy_toru():
    return {p: hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest() for p in PLIKI_TORU}


def kan_sha(obj):
    """sha256 kanonicznego JSON (sort_keys, separatory zwarte) — suma results/TEACH/s1/tor.json (wzór tabel NAD3)."""
    import json
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def pokrycie_k2(p, a, q, ak):
    """K′: pole części wspólnej kwadratu kadru (środek p, pół-bok a) i kwadratu klatki kluczowej (q, ak) / pole kwadratu kadru."""
    ox = max(0.0, min(p[0] + a, q[0] + ak) - max(p[0] - a, q[0] - ak))
    oy = max(0.0, min(p[1] + a, q[1] + ak) - max(p[1] - a, q[1] - ak))
    return ox * oy / (4 * a * a)


class Producent:
    """Producent: klatka → mapa / zamknięcie / lokalizacja → datagram stanu ramy. Jeden obiekt na proces nadir_obs."""

    def __init__(self, wariant="K", maska=None):
        assert wariant in WARIANTY_K, wariant
        assert sumy_toru()[PLIKI_TORU[0]] == SHA_TEACH2, "sha toru odniesienia teach2.py"
        self.wariant = wariant
        self.kam = R2.Kam(R2.kamera())
        self.pr = R3.Prost(self.kam)
        self.D = T.Dop(RODZAJ)
        self.maska = maska                          # stała maska obrazu (uint8 H × W, 0 = piksel pominięty) albo None
        su = np.arange(16) * (self.kam.W - 1) / 15
        sv = np.arange(12) * (self.kam.H - 1) / 11
        self._su, self._sv = su.astype(int), sv.astype(int)
        # mapa
        self.kadry = []                             # kadry mapy: {sim, cam_ekf, a, f, kf (indeks albo None)}
        self.kf = []                                # klatki kluczowe: {sim, cam_ekf, a, f, n (indeks kadru)}
        self.pokryte = set()
        self.dop = {}                               # (n kadru, k) → wynik Dop.dopasuj
        self.trojka = {}                            # n kadru → bieżąca trójka (lista k) wśród klatek kluczowych
        self.bufor = None                           # kadr czekający na potwierdzenie flagi
        # zamknięcie
        self.zamknieta = False
        self.n_zamkniec = 0
        self.t_flagi = None
        self.G = None
        self.wz = None
        self.georef = None
        # lokalizacja
        self.d_en = np.zeros(2)
        self.t_fix_int = None                       # t_fix łańcucha (od chwili flagi)
        # stan ramy (datagram)
        self.d_ne = [0.0, 0.0]
        self.t_fix = None
        self.p_fix_ne = None
        self.seq = 0
        self.n_fix = {"jeden": 0}
        self.n_kadrow_po = 0
        self.rejestr = None

    # --- wspólne
    def _przygotuj(self, obraz, ekf_q, ekf_pos):
        """Jak teach2.Lot.przygotuj bez renderu (kadr z kamery): prostowanie przy pozie EKF, punkt pod kamerą, pół-bok a."""
        Re = NF.ekf_R(ekf_q)
        rect, mask, off = self.pr(obraz, ekf_q, ekf_pos)
        if self.maska is not None:
            m = self.pr(self.maska, ekf_q, ekf_pos)[0]
            mask = np.where(m > 0, mask, 0).astype(np.uint8)
        ekf_en = np.array([ekf_pos[1], ekf_pos[0]])
        Ce = Re @ self.kam.t_link
        hc_e = -ekf_pos[2] + Ce[2]
        return {"rect": rect, "mask": mask, "off": np.asarray(off), "ekf_en": ekf_en, "cam_ekf": ekf_en + np.asarray(off),
                "a": hc_e * (self.kam.H / 2) / self.kam.F}

    def _klatka_kluczowa(self, ekf_q, ekf_pos):
        """Kopia warunku teach2.Lot.klatki_kluczowe dla jednego kadru (decyzja z pozy EKF); aktualizuje pokrycie przy przyjęciu."""
        kam = self.kam
        Re = NF.ekf_R(ekf_q)
        Ce, Rke = kam.poza(np.array([ekf_pos[1], ekf_pos[0], -ekf_pos[2]]), Re)
        E, Nn = kam.grunt(Ce, Rke)
        Es, Ns = E[np.ix_(self._sv, self._su)], Nn[np.ix_(self._sv, self._su)]
        ok = np.isfinite(Es)
        if not ok.any():
            return False
        x0, x1, y0, y1 = Es[ok].min(), Es[ok].max(), Ns[ok].min(), Ns[ok].max()
        import cv2
        poly = np.stack([Es[ok], Ns[ok]], 1).astype(np.float32)
        hull = cv2.convexHull(poly)
        xs = np.arange(math.floor(x0 / T.SIATKA_KF), math.ceil(x1 / T.SIATKA_KF) + 1)
        ys = np.arange(math.floor(y0 / T.SIATKA_KF), math.ceil(y1 / T.SIATKA_KF) + 1)
        komorki = {(int(i), int(j)) for i in xs for j in ys
                   if cv2.pointPolygonTest(hull, (float(i * T.SIATKA_KF), float(j * T.SIATKA_KF)), False) >= 0}
        if not komorki:
            return False
        frac = len(komorki & self.pokryte) / len(komorki)
        if frac < T.PROG_KF:
            self.pokryte |= komorki
            return True
        return False

    def _top3(self, n):
        x = self.kadry[n]
        kand = sorted(((T.pokrycie(x["cam_ekf"], y["cam_ekf"], x["a"]), i) for i, y in enumerate(self.kf)), reverse=True)
        return kand[:T.N_KAND]

    def _dopasuj(self, n, k):
        if (n, k) not in self.dop:
            self.dop[(n, k)] = self.D.dopasuj(self.kadry[n]["f"], self.kf[k]["f"])
        return self.dop[(n, k)]

    # --- faza mapy
    def _wlacz_do_mapy(self, b):
        """Kadr z bufora wchodzi do mapy: decyzja klatki kluczowej, dopasowania wyprzedzające."""
        t0 = time.perf_counter()
        n = len(self.kadry)
        jest_kf = self._klatka_kluczowa(b["ekf_q"], b["ekf_pos"])
        x = self._przygotuj(b["obraz"], b["ekf_q"], b["ekf_pos"])
        f = self.D.cechy(x["rect"], x["mask"])
        t1 = time.perf_counter()
        self.kadry.append({"sim": b["sim"], "cam_ekf": x["cam_ekf"], "a": x["a"], "f": f, "kf": None})
        n_dop = 0
        if jest_kf:
            k = len(self.kf)
            self.kf.append({"sim": b["sim"], "cam_ekf": x["cam_ekf"], "a": x["a"], "f": f, "n": n})
            self.kadry[n]["kf"] = k
            for j in range(n):                                   # kadry, do których trójki wchodzi nowa klatka kluczowa
                tr = self._top3(j)
                if any(i == k and p >= T2.POKR_WIAZ for p, i in tr) and (j, k) not in self.dop:
                    self._dopasuj(j, k); n_dop += 1
        for p, i in self._top3(n):
            if p >= T2.POKR_WIAZ and i != self.kadry[n]["kf"] and (n, i) not in self.dop:
                self._dopasuj(n, i); n_dop += 1
        t2 = time.perf_counter()
        return {"n": n, "sim": b["sim"], "kf": self.kadry[n]["kf"], "n_dop": n_dop, "ms_cechy": round((t1 - t0) * 1e3, 2),
                "ms_dop": round((t2 - t1) * 1e3, 2)}

    # --- zamknięcie
    def _zamknij(self, t_flagi):
        t0 = time.perf_counter()
        self.t_flagi = float(t_flagi)
        wz, n_pozno = [], 0
        for n, x in enumerate(self.kadry):                      # kolejność i kształt wierszy jak teach2.wiazania
            sam = x["kf"]
            kand = [i for p, i in self._top3(n) if p >= T2.POKR_WIAZ]
            if sam is not None and sam not in kand:
                kand = [sam] + kand[:T.N_KAND - 1]
            for i in kand:
                if i == sam:
                    wz.append([round(x["sim"], 3), i, 0.0, 0.0, None, 1, x["cam_ekf"].tolist()])
                    continue
                if (n, i) not in self.dop:
                    n_pozno += 1
                w = self._dopasuj(n, i)
                if w is None:
                    wz.append([round(x["sim"], 3), i, None, None, 0, 0, x["cam_ekf"].tolist()])
                    continue
                d_ekf = float(np.linalg.norm(x["cam_ekf"] - self.kf[i]["cam_ekf"]))
                ok = w[0] >= T.A_MIN and abs(math.hypot(*w[1]) - d_ekf) <= T2.TOL_ODL
                wz.append([round(x["sim"], 3), i, round(w[1][0], 4), round(w[1][1], 4), w[0], int(ok), x["cam_ekf"].tolist()])
        t1 = time.perf_counter()
        self.G = T2.rozwiaz(self.kf, wz, WARIANT_MAPY) if self.kf else np.zeros((0, 3))
        t2 = time.perf_counter()
        self.wz = wz
        self.zamknieta = True
        self.n_zamkniec += 1
        self.t_fix_int = self.t_flagi
        for x in self.kadry:                                    # cechy kadrów nie-kluczowych zbędne po zamknięciu
            if x["kf"] is None:
                x["f"] = None
        self.dop = {}
        self.georef = {"t_flagi": round(self.t_flagi, 4), "n_kadrow_mapy": len(self.kadry), "n_kf": len(self.kf),
                       "n_wiazan": len(wz), "n_wiazan_przyjetych": sum(w[5] for w in wz), "n_dop_pozno": n_pozno,
                       "ms_wiazania": round((t1 - t0) * 1e3, 2), "ms_rozwiazanie": round((t2 - t1) * 1e3, 2),
                       "ms_zamkniecie": round((t2 - t0) * 1e3, 2), "wariant_K": self.wariant,
                       "kf": [{"k": k, "sim": round(y["sim"], 3), "cam_ekf": [round(float(v), 4) for v in y["cam_ekf"]],
                               "a": round(float(y["a"]), 4), "theta_deg": round(math.degrees(float(self.G[k, 0])), 6),
                               "t": [round(float(v), 6) for v in self.G[k, 1:]],
                               "n_wiazan": sum(1 for w in wz if w[1] == k and w[5])} for k, y in enumerate(self.kf)],
                       "wiazania": [w[:6] for w in wz]}                                     # TEACH-S2 F3
        return self.georef

    # --- lokalizacja
    def _lokalizuj(self, t_frame, obraz, ekf_q, ekf_pos, rec):
        t0 = time.perf_counter()
        x = self._przygotuj(obraz, ekf_q, ekf_pos)
        fx = self.D.cechy(x["rect"], x["mask"])
        t1 = time.perf_counter()
        G = self.G
        pred = x["ekf_en"] + self.d_en
        tau = t_frame - self.t_fix_int
        pc = pred + x["off"]
        if self.wariant == "K":
            kand = sorted(((T.pokrycie(pc, G[i, 1:], x["a"]), i) for i in range(len(self.kf))), reverse=True)
        else:
            kand = sorted(((pokrycie_k2(pc, x["a"], G[i, 1:], self.kf[i]["a"]), i) for i in range(len(self.kf))), reverse=True)
        kand = [i for p, i in kand[:T.N_KAND] if p > 0]
        best = None
        for i in kand:
            w = self.D.dopasuj(fx, self.kf[i]["f"])
            if w is not None and (best is None or w[0] > best[1][0]):
                best = (i, w)
        t2 = time.perf_counter()
        reg = {"faza": "lok", "tau": round(tau, 6), "kand": kand, "k": None, "r": None, "zgodne": None, "innowacja": None,
               "ok": 0, "ms_cechy": round((t1 - t0) * 1e3, 2), "ms_dop": round((t2 - t1) * 1e3, 2)}
        if best is None:
            rec["powod"] = "brak_dopasowania"
            return reg
        i, w = best
        cam = T.rz(G[i, 0]) @ np.array(w[1]) + G[i, 1:]
        fix = cam - x["off"]
        innow = float(np.linalg.norm(fix - pred))
        ok = w[0] >= T.A_MIN and innow <= T.G0 + R3.VR * tau
        reg.update(k=i, r=[round(float(w[1][0]), 6), round(float(w[1][1]), 6)], zgodne=int(w[0]), innowacja=round(innow, 6),
                   ok=int(ok), fix_en=[round(float(fix[0]), 6), round(float(fix[1]), 6)])
        if not ok:
            rec["powod"] = "regula"
            return reg
        self.d_en = fix - x["ekf_en"]
        self.t_fix_int = float(t_frame)
        p_fix_ne = [float(fix[1]), float(fix[0])]
        self.d_ne = [p_fix_ne[0] - ekf_pos[0], p_fix_ne[1] - ekf_pos[1]]
        self.t_fix = float(t_frame)
        self.p_fix_ne = p_fix_ne
        self.n_fix["jeden"] += 1
        rec.update(ok=True, tryb="jeden", kosz=0, p_fix_ne=[round(v, 4) for v in p_fix_ne],
                   p_ekf_fix=[round(float(v), 4) for v in ekf_pos])
        return reg

    # --- wejście
    def obserwacja(self, t_frame, obraz, ekf_q, ekf_pos, gnss, t_flagi=None):
        """Jedna klatka: t_frame (czas sim), obraz BGR, migawka EKF (q FRD→NED, pozycja NED), flaga GNSS (1 / 0 / None = nieznana,
        traktowana jak 1) i chwila flagi (czas sim spadku cs_gnss_pos, gdy znana). Zwraca datagram; rejestr w self.rejestr."""
        self.seq += 1
        rec = {"t": "fx", "seq": self.seq, "t_frame": round(float(t_frame), 4), "ok": False, "tryb": None, "zrodlo": "teach"}
        utrata = (gnss is not None and not gnss) or (t_flagi is not None and float(t_frame) >= float(t_flagi))
        if not self.zamknieta and not utrata:
            reg = {"faza": "mapa"}
            if self.bufor is not None:                          # nowsza klatka z flagą 1 ⇒ kadr z bufora do mapy
                reg["wlaczony"] = self._wlacz_do_mapy(self.bufor)
                self.bufor = None
            if ekf_q is None or ekf_pos is None:
                reg["pominiety"] = "brak_ekf"
            elif -ekf_pos[2] < H_MIN:
                reg["pominiety"] = "wysokosc"
            else:
                self.bufor = {"sim": float(t_frame), "obraz": obraz, "ekf_q": ekf_q, "ekf_pos": ekf_pos}
                reg["bufor"] = round(float(t_frame), 4)
            rec["powod"] = "mapa"
            self.rejestr = reg
            return self._stan(rec)
        # TEACH-3: bez podanej chwili flagi (lot) kadr z bufora nie wchodzi do mapy; chwila zamknięcia = czas tej klatki
        tf = float(t_flagi) if t_flagi is not None else float(t_frame)
        z_bufora = t_flagi is not None and self.bufor is not None and self.bufor["sim"] < tf
        if not self.zamknieta:                                  # TEACH-S2 F2: pusta mapa się nie zamyka
            if not self.kadry and not z_bufora:
                reg = {"faza": "przed_mapa"}
                if self.bufor is not None:
                    reg["odrzucony_z_bufora"] = round(self.bufor["sim"], 4)
                self.bufor = None
                rec["powod"] = "przed_mapa"
                self.rejestr = reg
                return self._stan(rec)
        reg = {"faza": "lok"}
        if not self.zamknieta:                                  # pierwsza klatka przy fladze 0: zamknięcie mapy
            tz0 = time.perf_counter()
            if z_bufora:                                        # TEACH-3
                reg["wlaczony"] = self._wlacz_do_mapy(self.bufor)
            elif self.bufor is not None:
                reg["odrzucony_z_bufora"] = round(self.bufor["sim"], 4)
            self.bufor = None
            self._zamknij(tf)
            reg["georef"] = self.georef
            reg["ms_od_flagi_do_georef"] = round((time.perf_counter() - tz0) * 1e3, 2)
        if ekf_q is None or ekf_pos is None:
            rec["powod"] = "brak_ekf"
            self.rejestr = reg
            return self._stan(rec)
        if not self.kf:
            rec["powod"] = "pusta_mapa"
            self.rejestr = reg
            return self._stan(rec)
        self.n_kadrow_po += 1
        reg.update(self._lokalizuj(float(t_frame), obraz, ekf_q, ekf_pos, rec))
        self.rejestr = reg
        return self._stan(rec)

    def _stan(self, rec):
        rec["d_ne"] = [round(self.d_ne[0], 6), round(self.d_ne[1], 6)]
        rec["t_fix"] = None if self.t_fix is None else round(self.t_fix, 4)
        return rec

    def echo(self):
        return {"zrodlo": "teach", "mapa": WARIANT_MAPY, "cechy": RODZAJ, "wariant_K": self.wariant, "h_min": H_MIN,
                "maska": self.maska is not None, "sumy_toru": sumy_toru()}
