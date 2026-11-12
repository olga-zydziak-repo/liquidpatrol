# STOP-NAD2-4 — lot długi NAD2: 600.516 s bez GNSS nad polem znaczników, bez odmowy w misji; B1–B4 bez naruszeń; e_corr płaski, błąd własny EKF i bias kursu rosną

12.11.2026 · wykonawca · PROMPT_NAD2_S4 (sha256 a2740a4a PASS) z ANEKS_NAD2-3 (sha256 210d2d8d PASS). **1 boot z 2 (rezerwa
nieużyta), poza budżetem nogi (18/22 bez zmian). Breach 0, REFUSE(POS) fałszywy 0, STOP globalny żaden.**

## Wynik

| | |
|---|---|
| lot | `L_c10_s01` — c10_s01 (epizod 10), cięcie jak w bramce (KONT_INJECT_T 30, t_inj_sim 176.3 s) |
| bez GNSS | **600.516 s** od `t_inj_sim` do planowego zejścia (nastawa 600.5 s), potem zejście i przyziemienie GT |
| odmowa | **brak w misji** (0 ticków KONT_REFUSE przed zejściem, 0 zdarzeń refuse); w zejściu 26 ticków KONT_REFUSE (τ*, jak w bramce) |
| B1 | PASS — 12 270 ticków utraty (12 246 ocenionych), 0 przekroczeń, max e_corr/U **0.412**, max e_corr 0.538 m |
| B2 | PASS — margines do R_E min **7.635 m** |
| B3 | PASS — r_est = \|p_corr\| w 12 270/12 270 ticków |
| B4 | PASS — nav_state 14 i failsafe 0 od flagi do przyziemienia; REFUSE(POS) 0 |
| D1 (bramkowe, informacyjnie) | kontynuacja 600.516 s, track 1.000, pasmo 0.980, 0 REFUSE w misji |
| sprawdziany (s1)–(s3) | 100% |
| tempo | bramka bootu 0.9778 (próg 0.93); w przedziałach 0.966–0.979 |

## Obserwable per przedział 100 s od cięcia

Faza misji (przed `zejscie_planowe`); „600” = ostatnie 0.5 s nastawy; zejście osobno. Definicje jak analizator i raport S3
(`results/NAD2/tools/nad2_s4_raport.py`; wynik `L_c10_s01/obserwable_s4.json`).

| przedział [s] | e_corr p50/p95/max [m] | max e/U | a/1.5F | przyrost EKF/1.5G | bias kursu p50 [°] (pary) | błąd własny EKF p50/max [m] | zapas bariery min [m] | r_est max [m] | τ max [s] |
|---|---|---|---|---|---|---|---|---|---|
| 000 | 0.138/0.253/0.447 | 0.346 | 0.669 | 0.340 | −0.04 (500) | 2.374/3.664 | 2.445 | 23.948 | 0.224 |
| 100 | 0.095/0.203/0.399 | 0.309 | 0.485 | 0.305 | 2.68 (500) | 4.847/9.145 | 3.562 | 22.771 | 0.228 |
| 200 | 0.094/0.196/0.532 | 0.412 | 0.464 | 0.491 | 3.80 (499) | 8.456/11.825 | 4.284 | 22.109 | 0.232 |
| 300 | 0.081/0.193/0.537 | 0.335 | 0.371 | 0.460 | 5.04 (497) | 10.916/15.025 | 3.895 | 22.498 | 0.400 |
| 400 | 0.111/0.247/0.375 | 0.290 | 0.494 | 0.299 | 4.51 (500) | 13.102/16.512 | **1.864** | 24.529 | 0.228 |
| 500 | 0.091/0.203/0.367 | 0.283 | 0.435 | 0.302 | 5.28 (500) | 17.030/20.593 | 3.996 | 22.337 | 0.228 |
| 600 | 0.064/0.115/0.118 | 0.096 | 0.270 | 0.203 | 4.59 (3) | 15.388/15.632 | 16.442 | 9.951 | 0.168 |
| zejście | 0.108/0.178/0.234 | 0.190 | 0.398 | 0.257 | 4.99 (8) | 16.364/16.716 | 14.928 | 9.872 | 2.224 |

| przedział | przedziały τ (ticki) | tryby (ticki) | REFUSE ticki | klatki bez poprawki | track | pasmo | cs_opt_flow | cs_gnss_pos | nav_state | tempo |
|---|---|---|---|---|---|---|---|---|---|---|
| 000 | 0:2016 | para 2016 | 0 | 0/500 | 1.000 | 0.965 | 1.000 | 0.000 | [14] | 0.9680 |
| 100 | 0:2014 | para 2014 | 0 | 0/500 | 1.000 | 0.987 | 1.000 | 0.000 | [14] | 0.9701 |
| 200 | 0:2011 | para 2007, jeden 4 | 0 | 0/500 | 1.000 | 1.000 | 1.000 | 0.000 | [14] | 0.9711 |
| 300 | 0:2009, 1:4 | para 2005, jeden 8 | 0 | 1/500 | 1.000 | 0.960 | 1.000 | 0.000 | [14] | 0.9710 |
| 400 | 0:2008 | para 2008 | 0 | 0/500 | 1.000 | 0.970 | 1.000 | 0.000 | [14] | 0.9729 |
| 500 | 0:2005 | para 2005 | 0 | 0/500 | 1.000 | 1.000 | 1.000 | 0.000 | [14] | 0.9756 |
| 600 | 0:10 | para 10 | 0 | 0/3 | 1.000 | 1.000 | — | — | [14] | 0.9659 |
| zejście | 0:153, 1:4, 2:4, 3:4, 4:4, None:24 | para 36, jeden 157 | 26 | 82/119 | — | — | 1.000 | 0.000 | [14] | 0.9791 |

Co widać (bez progu):
- **e_corr płaski:** p95 0.19–0.25 m we wszystkich pełnych przedziałach, max e/U ≤ 0.412 (bramka: do 0.374).
- **Błąd własny EKF rośnie liniowo:** p50 od 2.4 do 17.0 m, max 20.6 m w 500–600 s. Fuzja przepływu (cs_opt_flow) przez
  cały lot 1.0, GNSS 0. Poprawka kamerą to kasuje — przesłanka konsumuje przyrost między poprawkami (≤ 0.49·1.5G), nie dryf
  bezwzględny.
- **Bias kursu z par rośnie:** mediana od −0.04° do 5.28°, 497–500 par na przedział. Nie przekłada się na e_corr.
- **Zapas bariery** min 1.864 m (400–500 s); w pierwszych 100 s 2.445 m (bramka c10_s01: 2.46 m). r_est max 24.53 m.
- **Klatki bez poprawki:** 1 w misji (300–400 s, τ max 0.400 s, bez odmowy).

## Predykcje (KSIĘGA, zapisane przed lotem w `87d1c0f3`) — rozliczenie wykonawcy, do potwierdzenia przez CC

Okna z `L_c10_s01/obserwable_s4_okna.json`: pierwsze 100 s = [t_inj, t_inj + 100), ostatnie 100 s = 100 s przed `zejscie_planowe`.

| | predykcja | wynik | |
|---|---|---|---|
| P-NAD2-L1 (0.70) | 600 s bez REFUSE w misji | 600.516 s, 0 REFUSE w misji | ✓ |
| P-NAD2-L2 (0.85) | B1–B4 bez naruszeń | 0 naruszeń | ✓ |
| P-NAD2-L3 (0.75) | p95 e_corr ostatnie 100 s ≤ 1.25 × pierwsze | 0.203 ≤ 1.25 × 0.253 = 0.316 m | ✓ |
| P-NAD2-L4 (0.60) | \|mediana biasu kursu\| ostatnie 100 s ≤ 3° | 5.28° | ✗ |

## Ruch intruza (ANEKS_NAD2-3 §2)

- **Pozycja 1** (ten sam generator i ziarno, 800 s, manifest `9e7d4ad3`): prefiks 200 s zgodny (|Δ| = 0 w 120 epizodach),
  **T2 FAIL** — jeden krok 0.1000206 m > v·0.1 + 1e-6 przy t = 677.1 s. Przyczyna: generator zaokrągla x0/y0 do 1e-4 m, co
  daje mikroskoki na granicach odcinków (do 2.0e-4 m). Ten sam artefakt jest we wzorze bramki (do 1.6e-4 m w 120 epizodach),
  ale tam na siatce 0.1 s nie przekracza progu. Wynik: `testy_s4_poz1.json`.
- **Pozycja 2 — poleciała:** wahadło po segmentach bramki [0, 200] s (w przód, wstecz, w przód, wstecz) do 800 s, manifest
  `scenario_manifest_s4L.json` sha256 `967e6799`. Nawroty co 200 s: zmiana kursu o 180° przy v = 1.0, bez skoku.
  Testy (`testy_s4.json`): T1 prefiks |Δ| = 0 · T2 max krok 0.1 m · T3 v = 1.0, r_max 17.956 m ≤ 18 · T4 intruder_motion na
  sucho do 799.98 s (manifest bramki: 199.98 s) · T5 wartości domyślne = bramka · T6 diff — patrz niżej. **PASS 6/6.**
- W locie: `gt_intruder.jsonl` 142.0–786.4 s sim (cały epizod), zero skoków komendy > 0.5 m, prędkość komendy ≤ 1.018 m/s,
  applied−cmd p95 0.108 m (shakeout: 0.10).
- Moja zmiana przy T4: pierwsza wersja testu bramkowała też krok komendy (próg v·0.02 + 1e-4, mój dodatek, nie z aneksu).
  Komendy są zaokrąglane do 1e-4 m, więc krok 0.020123 m nie przechodził w obu pozycjach. Zostawiłem go jako informację;
  ciągłość bramkuje T2.

## Stanowisko i infrastruktura

Bramka zdrowia A GO 0.9484 (1 próba), próbnik zegara 0 skoków, timesyncd zatrzymany na czas lotu i wznowiony przez kolejkę,
sonda preflight podłoga 10 Hz OK, bramka tempa bootu 0.9778. Linie „brudny” proc_gate: 0. Zawieszeń, env-blocków i przerwań
brak. Czas kolejki 15.6 min. Wyciąg ULG 5.14 MB (limit 10 MB przez env; domyślnie 3 MB). Log kolejki podaje „noga 23/24” — to
tylko etykieta numeru bootu (NOGA_PRZED 22); lot jest poza budżetem nogi.

## Diff kodu wobec bd975df5 (ANEKS_NAD2-3 §2, lista zamknięta)

Zamrożone (`harness/`, `r01/`, `r03/`, tabela, krok, launcher, analizator, sprawdziany, certy, manifest bramki,
`bench/scenarios.py`): diff pusty. Zmienione, wyłącznie odczyt env z domyślnymi wartościami bramki:
- `nad2_flight.py`: `T_CONT_S = float(os.environ.get("NAD2_T_CONT_S", "110.5"))`,
  `WALL_MAX_CUT_S = float(os.environ.get("NAD2_WALL_MAX_CUT_S", "300.0"))` (sha 35f2dd70 → 7d86609e);
- `nad2_boot.sh`: `S4MAN`/`S4MAN_SHA` z `NAD2_MANIFEST`/`NAD2_MANIFEST_SHA`; ścieżka manifestu w metadanych bootu z tej
  samej zmiennej (bez tego lot długi miałby w `manifest.json` ścieżkę bramki);
- `nad2_ulg.py`: `LIMIT` z `NAD2_ULG_LIMIT_MB` (dom. 3).

Meta lotu potwierdza: T_CONT_S 600.5, WALL_MAX_CUT_S 1000, manifest `967e6799`, tabela 6a118fd4, krok c6844f98, fix 3baa340e.

## Logi

`results/NAD2/s4/L_c10_s01/`: trace, rama i nadir_obs w gzip (4.1 / 2.2 / 0.9 MB), wyciąg ULG `ulg.jsonl.gz` 5.1 MB,
pozostałe pliki jak w bramce. Największy plik w repo: 8.5 MB (`demo.jsonl`). `boot.ulg` (238 MB) zostaje na dysku
(gitignore).

**Sygnał: STOP-NAD2-4.**
