# RAPORT_LIVEFED_CHAR — charakteryzacja percepcji w locie (B0–B3)

Data: 2026-08-15. Reżim: charakteryzacja (NIE build dźwigni). Habitat H.1 (ANEKS-H) zweryfikowany PER BIEG:
**HEADLESS dowód** (`headless_proof.txt`: `GUI_PROCS=[brak]`, gz `-s`), **RTF ~1.0**, **time-jump = 0** we
wszystkich biegach, gz **8.14.0**, backend **mesa-D3D12**. Kryteria bramki `PRE_R02C` NIETYKALNE; `θ_conf=0.1635`
niezmieniony. Etykiety przyrządów: `mav` (MAVSDK), `monotonic_local`. Artefakty: `results/R02/livefed/{B0,B1,B2,B3}/`.

## Wynik zbiorczy

| krok | pytanie | wynik |
|---|---|---|
| **B0** | czy detektor widzi cel w locie | **TAK, ale słabo:** coverage_seen=1.0, true-conf max 0.105 / p50 0.029 @7m — **< θ_conf 0.16** |
| **B1** | attitude pod OBSERVE-motion | **jitter-dominant:** pitch std 6.08°, abs_max 21.2° (bias 1.54°) → ~~0b~~ **OBALONE przez A1** (skutek≠rozrzut) |
| **A1** | czy jitter wyrzuca cel z FOV (skutek) | **NIE:** coverage_seen geom 1.0 (N=336) / detektor 0.95, out_of_fov=0 → **0b ODRZUCONE DEFINITYWNIE** |
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

---

# A1 / A2 — DOMKNIĘCIA POMIAROWE (2026-08-15, po ratyfikacji Olgi)

Olga NIE ratyfikowała 0b (patrz niżej A1: reguła zamrożona PRZED pomiarem). conf-floor MARTWY (rider C-A4).
Poniżej dwa domknięcia; **liczby konfliktowe z §B1 rekomendacją — A1 JĄ OBALA.**

## A1 — dyskryminator 0b: `coverage_seen` POD OBSERVE-motion → **0b ODRZUCONE DEFINITYWNIE**

Pytanie: czy jitter attitude (±21° z §B1) wyrzuca cel z FOV pod ruchem? §B1 mierzył SAM attitude (rozrzut),
nie pokrycie — rekomendacja 0b z §B1 była **niedowiedziona co do skutku**. A1 mierzy skutek dwutorowo.
Habitat H.1 zweryfikowany (`A1/run1/`): HEADLESS (`GUI_PROCS=[brak]`, gz `-s`), RTF 1.0004→1.0001, time-jump=0.
**Nota ważności EKF (ANEKS-H, zaostrzenie E2):** 5 trafień `horizontal velocity unstable` — WSZYSTKIE PRZED
uzbrojeniem (px4.log l.44–81 < l.96 „Armed"); uzbrojenie SIĘ POWIODŁO (PX4 nie uzbroi przy niestabilnej
prędkości ⇒ EKF zdrowy w chwili arm) i **0 ostrzeżeń w locie/pomiarze** (l.95–108 czyste). To transjent
zbieżności pre-arm, NIE kontencja pod RTF=1.0 → **bieg WAŻNY** (nie „prawie ważny").

**Tor 1 — GEOMETRYCZNY (z artefaktów §B1, N=336, zero konfundu detektora/lagu):** `a1_geom_coverage.py`.
Dla KAŻDEJ próbki attitude motion umieszczam cel operacyjny dead-ahead (config_r02: R_h=6.84 m, Δalt=1.5 m,
3D=7.0 m, el_nom 12.4°; az_nominal=0 wg yaw próbki ⇒ izoluję pitch/roll), rzut `project_full_attitude`
(V-FOV 1.453 rad, ±41.6°). Wynik: **coverage_seen_geom = 1.0, frames_out_of_fov = 0**; el rzutu p50 12.8°,
p95 24.1°, **max 33.6° < 41.6°** (margines ~8°); edge_dist min 0.126 (nigdy przy krawędzi). Wariant
„cel poniżej": też 1.0. **Jitter NIE wyrzuca celu z FOV** — potwierdza arytmetykę noty ratyfikacyjnej Olgi
(21° pitch ≪ ~26° potrzebne do klipu celu +12–16°).

**Tor 2 — DETEKTOR W PĘTLI pod motion (świeży bieg headless, `a1_flight.py`):** cel CIĄGLE prze-stawiany
dead-ahead (re-placer ~8 Hz, geometria operacyjna), profil ruchu = §B1 (kwadrat V=2.5 m/s), parowanie
klatka↔attitude `monotonic` (pair_maxdt ≤0.077 s). Wynik:

| faza | n | coverage_seen | frames_out_of_fov (geom, paired att) | box_cy p50 (edge min) | true_conf p50/max |
|---|---|---|---|---|---|
| hover | 7 | **1.0** | 0 | 0.404 (0.324) | 0.085 / 0.111 |
| **motion** | 20 | **0.95** | **0** | 0.404 (0.255) | 0.081 / 0.162 |

**Werdykt reguły (zamrożona PRZED pomiarem):** motion `coverage_seen = 0.95 ≥ 0.95` ⇒ **0b ODRZUCONE
DEFINITYWNIE**; gimbal NIE wchodzi do programu (parkowany, SR-M4 wraca tylko decyzją Olgi). Tor geometryczny
(N=336, coverage 1.0) jest mocniejszym potwierdzeniem niż progowe 0.95 z N=20. **KLUCZOWE:
`frames_out_of_fov = 0` w OBU torach** — jedyny nietrafiony kadr (1/20) to zdarzenie DETEKCJI (motion-blur
na ~30 px celu / top-box poza ROI), NIE utrata kadrowania. Gimbal centruje, **nie usuwa blur ani nie dodaje
pikseli** → 0b nie zaadresowałby tej luki. Mechanizm strat = rozdzielczościowy (zgodnie z notą Olgi), nie
kadrowaniowy. *Predykcja prerejestrowana CC (≥0.95 → 0b odrzucone): TRAFIONA (przerywa serię 3 błędnych).*

## A2 — rozbieżność B0 vs B2 @7 m (0.105 vs 0.023): NAZWANA, z artefaktów (bez nowego biegu)

„Bliżej daje mniej" było pozorne — dotyczy tylko `max`, nie rozkładu. Rozbiór:
1. **Definicja/licznik: IDENTYCZNE — wykluczone.** Oba: box w R=0.18 od (0.5,0.5), `best = max conf w ROI`,
   `p50 = a[len//2]`, ten sam detektor `yolov8s-worldv2 'drone'` conf_floor 0.001 (b0_flight.py:143–153 ≡
   b2_flight.py:72–89). Rozbieżność NIE jest artefaktem definicji.
2. **Zgłaszany `max` jest zawyżony liczebnością:** B0 `max` po **N=17** klatek vs B2 po **N=7**; maksimum
   rośnie z N. Stąd gros luki `max` (4.6×). **Statystyka odporna = mediana:** B0 p50 0.0285 vs B2 p50 0.0164
   = **1.74×** (ten sam rząd), oba ≪ θ_conf 0.1635.
3. **Reszta (1.74× na p50) = czułość ~30 px celu na POZĘ względem TŁA.** B0 (yaw 58.8°) vs B2 (yaw 95.56°)
   kadrują mikro-cel na innym płacie tła (linia horyzontu/grunt vs niebo); conf YOLO-World na 30 px „drone"
   silnie zależy od kontrastu tła — ta sama kruchość co „conf ≪ θ" (rozmiar celu, §Otwarte).
4. **Zastrzeżenie prowieniencji:** B0 `att_deg` (pitch 5.76°) to POJEDYNCZY odczyt migawkowy tuż po settle;
   §B1 pokazuje zdrowy zawis pitch −0.69°±0.21° (abs_max 1.2°) → 5.76° to transjent osiadania w chwili
   odczytu, NIE stan przez 15 s. Per-klatkowe attitude B0 NIE logowane → nie wolno przypisać luki p50
   wyłącznie attitude. **Nazwana reszta niepewności, nie zamieciona.**

**Wniosek (co idzie dalej):** obie chmury zgodne w rzeczy nośnej — cel widziany co klatkę (coverage 1.0),
**conf ≪ θ_conf na każdym zasięgu**, monotonicznie malejący z odległością. Rozbieżność żyje wyłącznie w
MAGNITUDZIE `max` (telemetria pasywna, niczego nie bramkuje — θ_conf nietykalny, conf-floor martwy C-A4).
**Liczbą, która idzie dalej, jest mediana odporna (~0.02–0.03 @7 m, oba ≪ θ), NIE `max`.** Bieg kontrolny
NIEpotrzebny.

## STOP — decyzje do ratyfikacji (zaktualizowane A1)
(1) ~~dźwignia kamerowa 0b (gimbal)~~ **0b ODRZUCONE DEFINITYWNIE (A1)** — gimbal poza programem (SR-M4);
(2) MTI jako AND-gate **TAK** (jedyna realna brama ENTRY — conf-floor martwy); (3) N **bez zmian (=6)**;
(4) **build dźwigni przed bramką**. Rozbieżność B0/B2 **nazwana** (A2). Sesja bramkowa i noga D — osobne
prompty po ratyfikacji. Część A: `a1_flight.py`+`a1_run.sh`+`a1_geom_coverage.py`. **Push = Olga.**
