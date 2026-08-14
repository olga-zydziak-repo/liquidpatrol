# RAPORT_LIVEFED_CHAR — charakteryzacja percepcji w locie (B0–B3)

Data: 2026-08-15. Reżim: charakteryzacja (NIE build dźwigni). Habitat H.1 (ANEKS-H) zweryfikowany PER BIEG:
**HEADLESS dowód** (`headless_proof.txt`: `GUI_PROCS=[brak]`, gz `-s`), **RTF ~1.0**, **time-jump = 0** we
wszystkich biegach, gz **8.14.0**, backend **mesa-D3D12**. Kryteria bramki `PRE_R02C` NIETYKALNE; `θ_conf=0.1635`
niezmieniony. Etykiety przyrządów: `mav` (MAVSDK), `monotonic_local`. Artefakty: `results/R02/livefed/{B0,B1,B2,B3}/`.

## Wynik zbiorczy

| krok | pytanie | wynik |
|---|---|---|
| **B0** | czy detektor widzi cel w locie | **TAK, ale słabo:** coverage_seen=1.0, true-conf max 0.105 / p50 0.029 @7m — **< θ_conf 0.16** |
| **B1** | attitude pod OBSERVE-motion | **jitter-dominant:** pitch std 6.08°, abs_max 21.2° (bias 1.54°) → **0b (gimbal)** |
| **B2** | chmury conf vs θ, sweep 5–11 m | **admit@θ = 0.0 na KAŻDYM zasięgu** (cel widziany zawsze, conf nigdy ≥ θ); **ε_FP=0 trzyma** |
| **B3** | stall pętli decyzyjnej pod motion | **max 1.05 ticka**, 0 stalli >4t → **N=6 wystarcza** (3× margines = 3.2t) |

## B0 — SONDA (1 lot, zawis, intruz dead-ahead 7 m, detektor w pętli)

`results/R02/livefed/B0/run1/`. Detektor YOLO-World `set_classes(['drone'])`, conf_floor 0.001. 17 klatek
detektora (~1 Hz), cel dead-ahead (projekcja ~centrum), overlay `frame_overlay.png`.
- **true-target conf** (box w R0.18 od centrum): **max 0.1046, p50 0.0285, min 0.0092** — **poniżej θ_conf 0.1635**.
- **coverage_seen = 1.0** (cel wykryty jako box w KAŻDEJ klatce), noise (boxy poza) p50 0.0022 ≪ θ.
- att zawisu: pitch 5.76° (dryf); RTF 1.0; frame_min 31 (cel wyrenderowany).

**Predykcja prerejestrowana CC (~0.15, sygnał obecny cienki margines): CZĘŚCIOWO — sygnał obecny (coverage 1.0),
ale conf NIŻSZY (max 0.10 < θ), nie „zdrowo wyższy".** → „zapaść sygnału" z §3f **NIE była wyłącznie artefaktem**;
sygnał w locie jest realny lecz słaby. (Nota: historyczne 0.045–0.081 „sygnał w locie" mierzyło szum bez
wyrenderowanego celu — ANEKS-H.2; nie priory.)

## B1 — pitch/jitter pod OBSERVE-motion (rider C-A1/A2)

`results/R02/livefed/B1/run1/`. Profil krążenia (velocity 2.5 m/s N/E, zmiany kierunku), attitude `mav` ~20 Hz.
- **Zawis (baseline):** pitch mean −0.69°, **std 0.21°**, abs_max 1.2° (zgodne z R0.2 ~0.6°).
- **Ruch OBSERVE:** pitch mean −0.45° (**BIAS mały**), **std 6.08°** (**JITTER duży**), **abs_max 21.2°**;
  roll mean −1.54°, std 5.34°, abs_max 22.7°.
- **bias 1.54° vs jitter 6.08° → REKOMENDACJA: 0b (gimbal)** (reguła PRE_R02C zastosowana, NIE budowana).
  Uzasadnienie mechanizmu: transjenty ±21° pitchu + elewacja celu ~12° **przekraczają pół-V-FOV (~26.5°)** →
  cel WYPADA z kadru w przyspieszeniach. 0a (stały offset) NIE pomaga (zaburzenie jest zmienne, nie stałe).

## B2 — re-charakteryzacja θ_conf: obie chmury w locie, sweep dystansu

`results/R02/livefed/B2/run1/`. Jeden zawis, cel dead-ahead na 5/7/9/11 m + faza SZUMU (cel odsunięty −60 m).
**θ_conf NIETYKALNY — mierzę położenie chmur względem progu 0.1635.**

| zasięg | target_conf max / p50 | coverage_seen | **coverage_admit@θ** |
|---|---|---|---|
| 5 m | 0.056 / 0.051 | 1.0 | **0.0** |
| 7 m | 0.023 / 0.016 | 1.0 | **0.0** |
| 9 m | 0.009 / 0.006 | 1.0 | **0.0** |
| 11 m | 0.011 / 0.008 | 1.0 | **0.0** |
| **SZUM** (pusta scena) | noise max 0.033, p50 0.003 | — | **ε_FP@θ = 0** (0 klatek) |

- **Sygnał chmura leży CAŁA poniżej θ_conf** na każdym zasięgu; maleje z odległością (5 m najwyżej).
- **Szum chmura (max 0.033) też poniżej θ_conf** → **ε_FP = 0 trzyma** przy istniejącym progu.
- (B0 @7m max 0.105 vs B2 @7m max 0.023: różnica z attitude/kadrowania — B0 pitch 5.76° vs B2 −0.71°;
  robust median @7m ~0.02–0.03. Obie zgodne: **conf ≪ θ_conf**.)

**Osiągalność kryteriów na samym conf:**
- **(+) ≥7 m, coverage ≥0.8 przez conf≥θ_conf: NIEOSIĄGALNE** — admit@θ = 0.0 na wszystkich zasięgach.
- **(−) ε_FP = 0: OSIĄGALNE / trzyma** — szum nigdy nie sięga θ_conf.
- To jest **dopuszczalny wynik (nie porażka)**: conf-floor pada, **ENTRY musi stanąć na STRUKTURZE + MTI
  (rider C-A4)**, `θ_conf` niezmieniony, ε_FP=0 nadal egzekwowane.

## B3 — re-derywacja N dead-mana pod OBSERVE-motion

`results/R02/livefed/B3/run1/`. Pętla decyzyjna 20 Hz (`shield.step` + telemetria) pod ruchem; `monotonic_local`.
- **n=352, max 0.0524 s = 1.05 ticka, p99 1.04 t, 0 stalli >4t, 0 >6t.** Zgodne z baseline R3 (1.06 t) — pętla
  decyzyjna NIE stalluje pod OBSERVE-motion (detektor osobny proces).
- **REKOMENDACJA: N=6 (0.30 s) WYSTARCZA** — 3× margines nad max = 3.2 t < 6. `DEADMAN_TICKS` NIEZMIENIONE (zgodnie
  z zakazem); zmiana i tak niepotrzebna.

## Rekomendacja rutowania (do ratyfikacji Olgi)

1. **Dźwignia kamerowa: 0b (GIMBAL).** B1 jitter-dominant (±21° transjenty pod motion) wyrzucają cel z FOV;
   stabilizacja gimbala utrzymuje cel w kadrze podczas OBSERVE. 0a (offset) nie adresuje jittera.
2. **MTI jako AND-gate: TAK, KONIECZNE.** Conf nigdy nie sięga θ_conf (B0/B2) → conf-floor nie może być bramą ENTRY;
   ENTRY na kandydacie STRUKTURALNYM ∧ MTI (rider C-A4/A3), ε_FP=0 egzekwowane (trzyma się, bo szum < θ).
3. **N: bez zmian (N=6 adekwatne, 3× margines).** Re-cert niepotrzebny z tego tytułu.
4. **Droga: BUILD dźwigni PRZED bramką.** Prosto do bramki dwustronnej NIE — kryterium (+) na samym conf jest
   nieosiągalne (admit@θ=0.0); bez 0b (utrzymanie FOV) + MTI/struktura (ENTRY) coverage ≥0.8 nie przejdzie.

## Otwarte pozycje

- **Poziom conf jest niski z powodu ROZMIARU celu** (mesh x500 ~0.6 m @7 m ≈ 30 px; YOLO-World „drone" na 30 px
  jest słaby). **Gimbal (0b) centruje/stabilizuje, ale NIE zwiększa liczby pikseli** → conf-floor prawdopodobnie
  pozostanie < θ nawet z gimbalem. To wzmacnia rutowanie: **realna brama ENTRY = struktura + MTI, nie conf.**
- Rozbieżność B0/B2 @7m (0.105 vs 0.023) — czułość conf na attitude/kadrowanie; wartość robust = mediana ~0.02–0.03.
- Przyczyna oryginalnego FAIL §3f/§6 pozostaje **niedomknięta mechanizmem** (ANEKS-H; warunek korelujący GUI-on;
  E2 obaliło kontencję CPU) — nie wpływa na powyższe (habitat H.1 czysty we wszystkich biegach B0–B3).

## STOP — decyzje do ratyfikacji
(1) dźwignia kamerowa **0b (gimbal)**; (2) MTI jako AND-gate **TAK**; (3) N **bez zmian (=6)**; (4) **build dźwigni
przed bramką** (nie prosto do bramki). Sesja bramkowa i noga D — osobne prompty po ratyfikacji. **Push = Olga.**
