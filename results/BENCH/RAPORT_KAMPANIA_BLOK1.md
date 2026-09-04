# RAPORT KAMPANII — BLOK 1 (48 epizodów) · ławka orbity pozycja 2

LiquidPatrol · CC 4.09.2026 · łańcuch: PRE_BENCH + ANEKS_BENCH-1/-1a/-2 (skuteczne) · świat `world_demo_A3` (adc91803) · FILM=0
Instrument ZAMROŻONY: frozen-7 + campaign_analyze `f31e81e3` / campaign_queue `89619514` / bench_finalize `508856dc` / bench_flight `b8eb68ca`.

## §1. Wynik główny

**p_exec = 44/48 = 0.9167 · Wilson 95% = [0.8045, 0.9671]** (D9=V2′, po pierwszej ważnej próbie każdego scenariusza).
n_resolved=48 · n_success(D6)=44 · **n_unresolved=0** · **REFUSE=0 · breach=0** w całej kampanii.
Dolna granica CI 0.8045 ≥ 0.80 — próg p_exec spełniony nawet konserwatywnie.

Metryki nienasycone (mediana + IQR, per PRE §2 D6):
- frac[6,10]: mediana 1.0000 · IQR[1.0000,1.0000] · min 0.9547 — **frac nigdy nie był przyczyną porażki** (wszędzie ≥0.85)
- sweep_deg: mediana 897.8 · IQR[889.3,922.0] · min 818.8 — **sweep nigdy nie był przyczyną** (wszędzie ≥630)
- d_min: mediana 7.678 · IQR[6.976,8.230] · min 1.179 — **jedyna oś porażek**

## §2. Klasa porażek — approach-phase d_min<4 (P-BE3 OBALONE)

4 porażki D6, WSZYSTKIE z jednego powodu — separacja drona-intruz <4 m w fazie **approach** (<3 s, przed orbitą):

| scenario | d_min | d_min_orbit | frac | sweep | inne człony D6 |
|---|---|---|---|---|---|
| c05_s01 | 2.988 | 7.597 | 1.0 | 942 | wszystkie PASS |
| c07_s02 | 3.875 | 7.703 | 0.965 | 910 | wszystkie PASS |
| c09_s02 | 1.179 | 7.288 | 1.0 | 835 | wszystkie PASS |
| c09_s03 | 2.521 | 7.176 | 1.0 | 846 | wszystkie PASS |

- **d_min_orbit ≥7.18 wszędzie** — orbita ustabilizowana jest bezpieczna; blisko robi się tylko na WEJŚCIU.
- Podatne komórki: **c05, c07, c09**, modulowane ziarnem (c09 dwukrotnie: s02 1.179, s03 2.521; c05 tylko s01; c07 tylko s02 — ta sama komórka bywa czysta w innym seedzie: c07_s01 8.29, c07_s03 7.67, c07_s04 8.23).
- **P-BE3 (pierwsza klasa porażek = frac-w-paśmie) FALSYFIKOWANE.** Klasa to trzecia oś: proximity wejścia, nie frac (b) ani czas wejścia (a).
- To NIE zerwanie osłony: breach = geofence R_E=32 (dom), tu False; d_min<4 = kryterium sukcesu epizodu D6(d)/D3, nie trigger STOP. Osłona nie REFUSE'uje za bliskość intruza (chroni dom, nie separację).

## §3. Strażnik R1 — stalle NIE ukrywają porażek (D9=V2′ czyste)

Kontrola ANEKS-1a §2 R1 (sukces vs deep-stalle): 
- stall0 (n=31): 27 sukcesów — **wszystkie 4 porażki są w grupie stall-FREE**
- stall1+ (n=17): **17/17 sukcesów (100%)**

Korelacja stall→porażka jest ODWROTNA do obawy: epizody z deep-stallami mają 100% sukcesu; porażki wystąpiły wyłącznie w epizodach bez stalli. **Stalle są niezależne od klasy porażek (geometria approach).** D9=V2′ (zdjęty cap liczby stalli) niczego nie zamiótł — rewizja reguły niepotrzebna.

## §4. Higiena kampanii (kolejka C8 + proc_gate)

- **48/48 scenariuszy rozwiązanych, 0 UNRESOLVED, complete=True.** Twardy cap attempt≤3 nietknięty (max attempt użyty = 2).
- Requeue V2′-invalid (Δsim/Δwall<0.90, spowolnienie env): c03_s01→att2 (potem valid+D6), c05_s01→att2 (valid, D6-fail geometria). 2 re-loty, oba domknięte.
- **2× ENV-BLOCK** (proc_gate §3): dreamforge-arc `run_a25` (drugi projekt Olgi, 20–86% CPU) w trakcie boot-9 i boot-10. proc_gate SR-6 zablokował oba PRZED startem; kolejka: 8 epizodów = missing → re-append na ogon BEZ inkrementu (D8), **zero strat**. Auto-defer (monitor proc_gate) wznowił po zwolnieniu hosta. Booty env-block zachowane jako rekord (boot9/boot10, kind=env-block).
- 13 lotów kryterialnych (boot1–8, 9r, 10r, 11–13) + 2 env-block. W budżecie D8 (≤40 bootów).
- **±1.5 osc + cooldowny ≥5 min + INTRUDER=1 + higiena mag/gps** — arm czysty we wszystkich 13 lotach.

## §5. Predykcje (prerejestrowane PRE §6)

- **P-BE1** p_exec ≥ 0.85 → **0.9167 TRAFIONA**
- **P-BE2** 0 REFUSE nominal → **0 TRAFIONA**
- **P-BE3** 1. klasa porażek = frac (b) → **CHYBIONA** (to approach-d_min)
- **P-BE4** D9 odrzuca ≤15% → 2/48 pierwszych prób V2′-invalid ≈ 4.2% → **TRAFIONA**

## §6. Werdykt

Wobec PRE §1 (+) PASS = p_exec≥0.80 na ≥36 ważnych ∧ 0 REFUSE ∧ 0 breach ∧ **zbiór ≥90 udanych demonstracji (train+test)**:
- p_exec 0.9167 ≥ 0.80 (CI dolne 0.8045) ✓ · 48 ważnych ≥ 36 ✓ · 0 REFUSE ✓ · 0 breach ✓
- **≥90 demonstracji: NIE domknięte blokiem 1** — 44 udane epizody. Zbiór ≥90 wymaga dalszych ziaren (k do 10/komórkę, PRE §3/D8 „dalsze ziarna do zbioru"). To osobny krok akumulacji, nie porażka.

**NIE jest to śmierć** (śmierć = p_exec<0.60). p_exec — MIANOWNIK dla pozycji 3 — **ustanowiony na 0.9167 [0.80, 0.97]**. Formalne ogłoszenie (+) PASS czeka na domknięcie zbioru ≥90 (decyzja CC: rozszerzyć ziarna vs zapisać p_exec jako ustanowiony i przejść do pozycji 3 z tym mianownikiem).

Nota diagnostyczna dla pozycji 3: nauczyciel skryptowy zawodzi wyłącznie na proximity wejścia dla komórek c05/c07/c09 — sieć ucząca się z tego zbioru odziedziczy tę granicę, chyba że wejście zostanie utwardzone (poza zakresem ławki, SR-3 zamrożony egzekutor).

## §7. d_min między sesjami (ANEKS-2 §2 R2)

Jedna sesja — brak porównania międzysesyjnego. Nota boot-0 vs reshakeout b2 (~0.4 m ciaśniej) pozostaje diagnostyczna. Mediana d_min sesji = 7.678. Przyszłe sesje: dryf mediany W DÓŁ = sygnał STOP (nie próg per-boot).
