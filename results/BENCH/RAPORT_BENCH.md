# RAPORT_BENCH — ławka orbity pozycja 2, RAPORT KOŃCOWY (STOP-R3)

LiquidPatrol · CC 5.09.2026 · łańcuch: PRE_BENCH + ANEKS_BENCH-1/-1a/-2/-3 (wszystkie skuteczne)
świat `world_demo_A3` (adc91803) · FILM=0 · instrument ZAMROŻONY (frozen-7 + campaign_analyze `f31e81e3`/queue `89619514`/finalize `508856dc`/bench_flight `b8eb68ca`)

## §1. WERDYKT: (+) PASS ławki

Wobec PRE §1: **p_exec ≥ 0.80 na ≥36 ważnych ∧ 0 REFUSE ∧ 0 breach ∧ ≥90 udanych demonstracji** — WSZYSTKIE spełnione:

| kryterium | wymóg | wynik |
|---|---|---|
| p_exec (blok 1, mianownik poz.3) | ≥ 0.80 | **0.9167** [0.8045, 0.9671] ✓ |
| ważne epizody | ≥ 36 | 120 (48+72) ✓ |
| REFUSE w nominale | 0 | **0** (120 ep) ✓ |
| breach | 0 | **0** (120 ep) ✓ |
| zbiór udanych demonstracji | ≥ 90 | **114** (44+70) ✓ |

**(+) PASS — nauczyciel skryptowy ustanawia p_exec jako mianownik dla pozycji 3.**

## §2. Dwa bloki

| | blok 1 (ziarna 1–4) | blok 2 (ziarna 5–10) |
|---|---|---|
| epizody | 48 | 72 |
| sukcesy D6 | 44 | 70 |
| p_exec | 0.9167 | 0.9722 |
| Wilson 95% | [0.8045, 0.9671] | [0.9043, 0.9923] |
| mediana d_min | 7.678 | 7.739 |
| REFUSE / breach | 0 / 0 | 0 / 0 |
| UNRESOLVED | 0 | 0 |
| env-block (proc_gate) | 2 (boot9/10) | 2 (b2b6/b2b6r) |

**MIANOWNIK pozycji 3 (ANEKS-3 R1) = p_exec bloku 1 = 0.9167 [0.8045, 0.9671]** — blok 2 NIE przelicza mianownika.

**Bramka spójności (ANEKS-3 R2): SPÓJNE, brak STOP.** CI bloku 2 [0.9043,0.9923] NIE jest rozłączne poniżej CI bloku 1 [0.8045,0.9671] — nakłada się i leży wyżej. Blok 2 potwierdza blok 1 (jeśli coś, egzekutor był w bloku 2 nieco skuteczniejszy — rozkład ziaren, nie dryf instrumentu).

**Strażnik d_min międzysesyjny (ANEKS-2 R2): mediana 7.678 → 7.739 (W GÓRĘ)** — brak dryfu w dół, żaden sygnał STOP.

## §3. Klasa porażek — proximity wejścia (approach d_min<4)

6 porażek D6 na 120 epizodów, WSZYSTKIE z jednego powodu — separacja drona-intruz <4 m w fazie **approach** (<3 s, przed orbitą); orbit-phase d_min ≥7.18 m wszędzie:

| epizod | d_min | d_min_orbit | blok |
|---|---|---|---|
| c05_s01 | 2.988 | 7.597 | 1 |
| c07_s02 | 3.875 | 7.703 | 1 |
| c09_s02 | 1.179 | 7.288 | 1 |
| c09_s03 | 2.521 | 7.176 | 1 |
| c05_s08 | 2.861 | 7.706 | 2 |
| c09_s06 | 2.725 | 7.190 | 2 |

- **Wyłącznie komórki c05, c07, c09**, modulowane ziarnem (ta sama komórka bywa czysta w innym seedzie: c05 czyste w s05/s06/s09/s10; c07 czyste poza s02; c09 czyste w s01/s04/s05/s08/s09).
- frac (b) i sweep (c) NIGDY nie były przyczyną (frac mediana 1.0 oba bloki, min 0.95≥0.85; sweep min 781≥630).
- To NIE zerwanie osłony: breach (geofence R_E=32) = False wszędzie; d_min<4 = kryterium sukcesu epizodu D6(d)/D3, nie trigger STOP. Osłona chroni dom, nie separację od intruza.
- **P-BE3 (1. klasa porażek = frac) OBALONE** — klasa to trzecia oś: proximity wejścia egzekutora dla c05/c07/c09.

## §4. Strażnik R1 (sukces vs deep-stalle) — D9=V2′ czyste

- Blok 1: stall0 27/31, stall1+ **17/17** (100%); wszystkie porażki stall-FREE.
- Blok 2: stall0 13/13 (100%), stall1+ 57/59 (96.6%); 2 porażki mają blip-stalle (longest=0.0 s = szum próbnika, nie choroba mostu).
- Łącznie: brak niekorzystnej korelacji stall→porażka. Porażki to czysta geometria approach, niezależna od RTF. **Zdjęcie capu liczby stalli (V2′, ANEKS-1a R1) niczego nie zamiotło** — rewizja reguły niepotrzebna.

## §5. Higiena kampanii (kolejka C8 + proc_gate w boju)

- **120/120 scenariuszy rozwiązanych, 0 UNRESOLVED, oba bloki complete=True.** Cap attempt≤3 nietknięty (max użyty = 2).
- Requeue V2′-invalid (Δsim/Δwall<0.90): blok 1 c03_s01/c05_s01→att2, oba domknięte. Blok 2: 0.
- **4× ENV-BLOCK** (proc_gate §3/SR-6): dreamforge-arc (drugi projekt Olgi) — `run_a25` (blok1), `a26 run_d2` sonnet/qwen (blok2), 20–100% CPU. proc_gate zablokował KAŻDY przed startem; 16 epizodów = missing → re-append na ogon BEZ inkrementu (D8), **zero strat**. Auto-defer (monitor sustained-CLEAN 3×/30s po flappingu 100%-CPU) wznowił po zwolnieniu hosta. Nie ingerowano w dreamforge.
- 1× rc=134 teardown SIGABRT (b2b6r2) po pełnym finalize — boot ważny (manifest 1.klasy, 4/4 valid+D6, dane kompletne).
- Booty łącznie: 31 lotów kryterialnych + 4 env-block. W budżecie D8 (kampania ≤40 bootów/sesję; tu 2 sesje: blok1 13+2, blok2 18+2).

## §6. Predykcje CC (prerejestrowane PRE §6 + ANEKS-3 §3)

- P-BE1 ✓ (0.9167 ≥ 0.85) · P-BE2 ✓ (0 REFUSE) · P-BE3 ✗ (klasa = proximity wejścia) · P-BE4 ✓ (D9 odrzuca 4.2% ≤ 15%) · P-BE5 ✗ (bramka resetu trzymała; nic nie ucięło epizodów poza dsw-requeue)
- Kampania: **3 ✓ / 2 ✗**. Ławka łącznie z recon/build: **7 ✓ / 4 ✗** — poniżej progu „predykcje CC jako prior"; dane rządzą.

## §7. Nota diagnostyczna dla pozycji 3 (ANEKS-3 R4)

**Granica nauczyciela skryptowego = proximity wejścia w komórkach c05/c07/c09** (approach d_min<4, seed-zależny). Sieć ucząca się z tego zbioru (114 demonstracji) **odziedziczy tę granicę** — demonstracje tych komórek albo są sukcesami z bezpiecznym wejściem, albo (6 przypadków) zostały wykluczone ze zbioru „udanych" (PRE §4: do zbioru wchodzą tylko sukcesy D6). Utwardzanie wejścia egzekutora (np. profil podejścia zależny od geometrii startowej intruza) = **poza ławką** (SR-3, egzekutor zamrożony); należy do pozycji 3/5 jeśli CC uzna za potrzebne.

## §8. Artefakty i zamrożenie

- `campaign_aggregate.json` (blok 1), `campaign_aggregate_b2.json` (blok 2), `RAPORT_KAMPANIA_BLOK1.md`, ten raport.
- Instrument zamrożony bajt-w-bajt przez całą kampanię (frozen-7 + kampanii, potwierdzane przed każdą sesją).
- Kolejki: `queue_state.json` (blok1, complete), `queue_state_b2.json` (blok2, complete).

**STOP-R3 — czeka na ratyfikację CC: ogłoszenie (+) PASS ławki, potem PRE_NET (pozycja 3)** — tam otwarte pole DAgger (ANEKS-0 §3) i cap 2 sesji treningu wracają do Olgi.

## §9. Odchylenia (ANEKS_BENCH-4 §2 C1)

**O1 — hartowanie runnera sesji na flapping 100 %-CPU (odchylenie łagodne).**
Podczas bloku 2 dreamforge-arc `a26 run_d2` był zadaniem o utrzymanym ~100 % CPU z chwilowymi dipami. Pierwotny driver sesji czekał na pojedynczy odczyt `proc_gate CLEAN`, po czym popował paczkę i startował boot — łapał chwilowy dip (b2b6r ENV-BLOCK: CLEAN o 22:04:43 → a26 wrócił w 10 s → env-block). Utwardzenie: wymóg **SUSTAINED CLEAN = 3 kolejne odczyty `proc_gate CLEAN` w odstępach 30 s (~90 s); dowolny odczyt „brudny" zeruje streak do 0**. Dopiero po potwierdzeniu startuje pop+boot.

- **Plik:** `<scratchpad_sesji>/run_next_boot.sh` — **driver orkiestracji sesji, NIE w repozytorium, NIE w żadnym commicie** (efemeryczny; steruje KIEDY wywołać boot, nie zmienia werdyktu bramki).
- **Commit:** brak — plik nie jest wersjonowany w repo. Zapis semantyki i kodu = ten paragraf (jedyny trwały ślad).
- **`harness/run_boot.sh` i `harness/proc_gate.py`: NIETKNIĘTE** — zweryfikowane `git diff HEAD` puste, harness/ bez zmian. Sama bramka procesowa (§3/SR-6, blokująca boot wewnątrz wrappera) jest bajt-identyczna; runner tylko odracza WYWOŁANIE nietkniętej bramki, nie modyfikuje jej progu (>2 % CPU / loadavg>1,5) ani werdyktu. Dlatego diff verbatim (C1) nie dotyczy.
- **Wpływ:** ograniczony do decyzji o STARCIE bootu. Dane lotów, sędzia, kolejka, metryki D6/V2′ — nietknięte. 16 env-fail epizodów (4 env-blocki) wróciło do kolejki bez inkrementu (D8), zero strat; wszystkie później domknięte.

Semantyka „sustained" (fragment runnera, dla rekordu):
```
clean_streak=0
while [ $clean_streak -lt 3 ]; do
  if proc_gate --self $$ ; then clean_streak=$((clean_streak+1))   # CLEAN → +1
  else clean_streak=0 ; fi                                          # brudny → reset
  [ $clean_streak -lt 3 ] && sleep 30
done   # 3× CLEAN co 30s → dopiero teraz pop+boot
```
