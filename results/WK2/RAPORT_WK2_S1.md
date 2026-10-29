# RAPORT_WK2_S1 — noga WK-II „opór realny", sesja S1: poziom G (k ≈ 0.49 /s), wiatr 0 / 1.5 / 3 m/s

CC-wykonawca · 29.10.2026 · PROMPT_WK2_S1 + PRE_WK2 (sha256 f83973c6…c505, commit 1 nogi `f68b51e9`).
**Booty: 6/≤18** (G0 2, G1.5 2, G3 2; dolecenia 0, powtórki 0). Breach 0, REFUSE 0, sejwy GEOFENCE 0.
Bramka G0 przeszła; schodek S nie ruszył. **Kandydat werdyktu: V-A2.**

## §0. Bramka wejścia

- ARCH-1: `PRE_WK2.md` verbatim, sha256 `f83973c6b88151bfa9bd7364b6a817a77f0c3ab8d63392d61278778e8b4fc505`
  PASS. Commit 1 nogi to `f68b51e9` (osobny, pierwszy).
- origin/master == HEAD == 0d2a5926 (STOP-WK2R); gate pusty; porcelain czysty poza `??` DEMO_C.
- FROZEN, sha zgodne:
  - komplet z PROMPT_WK_S1 §0.3: profil a68a450b, sonda 8df528bb, pin mono_cam 3354ae1e, FREEZE_DET,
    x500_base 13c9174d, w_judge e68040ae, sędzia 8ec0fcfb, bench 05137098, ncp 0337d5ea,
    net_controller e8c1b658, fantom_scan e435ed7e, rejestr 87203d29, akw_scan b94cdeae;
  - piny osłony 5/5, certy 9/9;
  - `wk_boot.sh` ecf8071c, `wk_judge.py` c33c3ff8, `wk2_gen_world.py` 632db3c1, `wk2_k.py` 09e4b440;
  - światy `world_wk2_s063_s0` 73205686 i `world_wk2_k055_s0` ff60c065.

## §1. Budowa (0 bootów, wyłącznie nowe pliki)

1. **Światy wiatrowe poziomu G** (generator reconu `wk2_gen_world.py`, s = 0.63, +x ENU).
   sha zapisane PRZED pierwszym lotem:

| świat | wiatr ENU | sha256 |
|---|---|---|
| `worlds/world_wk2_s063_s1p5.sdf` | (1.5, 0, 0) | `b8a9c8b7de4c99390e8e37322eb559ea5871777e4190a1ffaa40cc7325563722` |
| `worlds/world_wk2_s063_s3.sdf` | (3, 0, 0) | `f8ccc51ca0e47a1a8edaf7418cc6882a89786cd17d6701c9716150698014b164` |

   Diff względem `world_wk2_s063_s0.sdf` to wyłącznie `<world name>` i `<linear_velocity>`.
   `gz sdf --check`: Valid ×2. Światy wiatrowe poziomu S nie zostały wygenerowane (schodek nie ruszył).
2. **Binaria x500_base:** obecne z nogi WK (nieśledzone), `model.sdf` 13c9174d bez zmian.
3. **Kontrola oporu** `results/WK2/tools/wk2_kcontrol.py` importuje `wk2_k.measure` (09e4b440).
   Oczekiwane k z kalibracji: s 0.63 → 0.4939, s 0.46 → 0.3219; tolerancja ±20%.
4. **ODCHYLENIE NAZWANE, driver** (decyzja Olgi 29.10, pytanie przed budową):
   - PRE_WK2 §2 każe latać `results/WK/tools/wk_boot.sh` „bez zmian, WORLD parametrem". Ten driver
     odrzuca każdy świat spoza `world_wk_{s0,s1p5,s3}` (`wk_boot.sh:29-34`, exit 5) i pisze do
     `results/WK/booty`, wbrew REPO-2 z PROMPT §0.3.
   - Zbudowany został **NOWY** `results/WK2/tools/wk2_boot.sh` jako kopia `wk_boot.sh` (ten nietknięty).
     Pełny diff ma 4 hunki:
     - **D0 nagłówek:** opis kopii i odchylenia;
     - **użycie:** przykład `world_wk2_*`;
     - **D2 katalog:** `OUTDIR` i `MONLOG` w `results/WK2/booty`, `mkdir -p results/WK2/booty`;
     - **D1 lista światów:** `case` z czterema światami WK2 i zaszytymi sha (73205686, b8a9c8b7,
       f8ccc51c, ff60c065); inny świat ⇒ ODMOWA.
   - Reszta to litera `wk_boot.sh`: piny przed bootem, prepend `GZ_SIM_RESOURCE_PATH`, sonda, profil,
     proc_gate, cooldown, blok `wk` w manifeście.
5. Pomiary opisowe:
   - `results/WK2/tools/wk2_styczna.py`: składowa styczna komendy i zrealizowana w fazie orbity,
     geometria z GT intruza. Odtwarza liczby ANEKS_WK-1 §1.3 (WK0: komenda 1.62–1.70, realizacja ~0.84;
     stock 1.90–1.97 / ~1.05).
   - Sędziowanie i porównanie z bazą stock: narzędzia nogi WK uruchamiane bez zmian
     (`wk_judge.py`, `wk_describe.py`, `wk_baza.py`).

## §2. Booty

| # | boot | świat (sha) | epizody | piny mono_cam / x500_base | sonda preflight | V2′ (dsim/dwall) | k [1/s] (CI95) | kontrola oporu |
|---|---|---|---|---|---|---|---|---|
| 1 | g0_b1 | s063_s0 (73205686) | c00–c03 | 3354ae1e / 13c9174d | PASS | 4/4 | 0.4943 (0.4924–0.4958) | **OK** (+0.1%) |
| 2 | g0_b2 | s063_s0 (73205686) | c04–c07 | jw. | PASS | 4/4 (0.902–1.003) | 0.4912 (0.4893–0.4932) | **OK** (−0.6%) |
| 3 | g15_b1 | s063_s1p5 (b8a9c8b7) | c00–c03 | jw. | PASS | 4/4 (0.925–0.954) | 0.4933 | n/d (wiatr), opisowo |
| 4 | g3_b1 | s063_s3 (f8ccc51c) | c00–c03 | jw. | PASS | 4/4 (0.927–0.943) | 0.4908 | n/d (wiatr), opisowo |
| 5 | g15_b2 | s063_s1p5 (b8a9c8b7) | c04–c07 | jw. | PASS | 4/4 (0.965–0.988) | 0.4900 | n/d (wiatr), opisowo |
| 6 | g3_b2 | s063_s3 (f8ccc51c) | c04–c07 | jw. | PASS | 4/4 (0.998–1.000) | 0.4860 | n/d (wiatr), opisowo |

Każdy boot: `rc=0`, `finalize=0`, PIN OK (mono_cam, x500_base, sha świata) w logu drivera,
world_hash.txt zgodny z sha świata. Kolejność z przeplotem zgodnie z PROMPT §2.3:
G1.5 b1 → G3 b1 → G1.5 b2 → G3 b2.

**Wiatr działa i opór liczy się względem powietrza (opisowo, z kontroli oporu).** Bilans `wk2_k` zakłada
wiatr 0, więc stały wiatr w trafia do wyrazu wolnego jako k·w.

| poziom | wyraz wolny E [m/s²] | k·w przewidywane |
|---|---|---|
| G1.5 | **0.745 / 0.747** | 0.74 / 0.735 |
| G3 | **1.491 / 1.489** | 1.47 / 1.46 |

Zgodność wynosi 1–2%. Gdyby opór wirników (stock, 0.117) liczył się względem ziemi, wyraz wolny
przy 3 m/s wyniósłby ~1.13. To rozstrzyga punkt niezmierzony w RECON_WK2 §R1: **cały opór, także
wirnikowy, liczy się względem powietrza.** k w światach wiatrowych 0.486–0.493 jest zgodne
z kalibracją.

## §3. Werdykty per epizod

Sędzia bazowy 8ec0fcfb, GT z manifestu. „Świadek" = gt_intruder po filtrze ERRATUM-DMIN.
Kolumny: t_entry [s] / frac pasma / sweep [°] / d_min pełny | świadek [m].

**G0 (wiatr 0): pełny 8/8 · świadek 8/8**

| scen. | pełny | świadek | t_entry | frac | sweep | d_min |
|---|---|---|---|---|---|---|
| c00 | ✓ | ✓ | 3.84 | 1.000 | 801.5 | 8.00 |
| c01 | ✓ | ✓ | 7.80 | 1.000 | 796.2 | 7.88 |
| c02 | ✓ | ✓ | 12.10 | 1.000 | 833.8 | 7.86 |
| c03 | ✓ | ✓ | 16.52 | 1.000 | 828.9 | 7.80 |
| c04 | ✓ | ✓ | 3.10 | 1.000 | 803.5 | 7.31 |
| c05 | ✓ | ✓ | 5.28 | 1.000 | 748.2 | 7.90 |
| c06 | ✓ | ✓ | 9.07 | 1.000 | 763.2 | 6.30 \| 7.37 |
| c07 | ✓ | ✓ | 9.69 | 1.000 | 680.3 | 8.27 |

**G1.5 (1.5 m/s): pełny 6/8 · świadek 6/8**

| scen. | pełny | świadek | powody | t_entry | frac | sweep | d_min |
|---|---|---|---|---|---|---|---|
| c00 | ✓ | ✓ | — | 3.86 | 1.000 | 824.4 | 7.56 |
| c01 | ✓ | ✓ | — | 11.43 | 1.000 | 743.5 | 7.38 |
| c02 | ✓ | ✓ | — | 15.02 | 1.000 | 861.6 | 7.57 |
| c03 | ✗ | ✗ | a_entry / a_entry | **33.64** | 1.000 | 819.4 | 7.50 |
| c04 | ✓ | ✓ | — | 3.02 | 1.000 | 823.8 | 7.17 |
| c05 | ✓ | ✓ | — | 7.98 | 1.000 | 797.6 | 7.22 |
| c06 | ✗ | ✗ | c_sweep+d_dmin / c_sweep+d_dmin | 10.62 | 0.865 | **573.0** | **3.57** |
| c07 | ✓ | ✓ | — | 8.56 | 1.000 | 683.7 | 7.89 |

**G3 (3 m/s): pełny 7/8 · świadek 8/8**

| scen. | pełny | świadek | powody | t_entry | frac | sweep | d_min |
|---|---|---|---|---|---|---|---|
| c00 | ✓ | ✓ | — | 3.74 | 1.000 | 843.4 | 7.25 |
| c01 | ✓ | ✓ | — | 9.24 | 1.000 | 829.2 | 7.19 |
| c02 | ✓ | ✓ | — | 15.37 | 1.000 | 871.8 | 7.10 |
| c03 | ✓ | ✓ | — | 17.20 | 1.000 | 841.7 | 7.18 |
| c04 | ✓ | ✓ | — | 3.12 | 1.000 | 836.6 | 6.87 |
| c05 | ✓ | ✓ | — | 6.49 | 1.000 | 804.6 | 6.98 |
| c06 | ✓ | ✓ | — | 9.42 | 1.000 | 802.2 | 6.57 |
| c07 | **✗** | **✓** | b_frac / — | 10.85 (świadek) | 1.000 (świadek) | 724.0 | 7.59 |

- **Zdarzenia GEOFENCE: 0** we wszystkich 24 epizodach. REFUSE czegokolwiek: 0. Breach: 0.
- **Rozjazd pełny/świadek:**
  - G3 c07: świadek zdejmuje artefakt teleportu ERRATUM-DMIN; pełny ma `b_frac`.
  - G0 c06: zmienia się tylko d_min, werdykt nie.
  - Żaden rozjazd nie rozstrzyga bramki ani werdyktu (G3: 8/8 i 7/8, oba ≥ 6/8).

## §4. Decyzje bramek (mechanicznie, PRE §2 / PROMPT §2.2)

1. **Bramka G0:** świadek 8/8 (pełny 8/8) ≥ 6/8 ⇒ krok 3: G1.5 i G3 z przeplotem. Schodek S nie ruszył.
2. Po G1.5 i G3 ⇒ STOP-WK2-1. Twarde STOPy nie zaszły: breach 0, REFUSE(POS) 0, GEOFENCE 0,
   kontrola oporu 2/2 OK, budżet 6/18.

## §5. Kandydat werdyktu (mechanicznie z PRE §3): **V-A2** (G0 8/8 ≥ 6 ∧ G3 8/8 ≥ 6, ze świadkiem)

> „NCP-20 prowadzi pełną misję na własnej kamerze przy oporze z górnego końca realnego pasma
> (k ≈ 0.49 /s) i stałym wietrze do 3 m/s: D6 **8/8 · 6/8 · 8/8** (0 / 1.5 / 3 m/s), breach 0,
> sejwy **0**."

Kwalifikator obowiązkowy (PRE §5): k zmierzone (0.486–0.494 /s per boot), pasmo z PX4 i literatury,
stały wektor wiatru, komórki v ≤ 0.5. Bez filtra-świadka: 8/8 · 6/8 · 7/8.

**Mechanizm (opisowo):**

- **Obieg przestał być wąskim gardłem.** Stosunek sweep G0 do bazy stock (FANTOM S2 r1_V2 / r2_V2,
  te same scenariusze, świadek) wynosi 0.80–1.05, mediana **0.858**. W nodze WK (k = 1.05) było
  0.62–0.83, mediana 0.665. Najniższy sweep G0 to 680° (próg 630°).
- **Składowa styczna** (mediana z 8 epizodów na poziom):

| | komenda [m/s] | zrealizowana [m/s] | realizacja |
|---|---|---|---|
| G0 | 1.84 | 1.74 | 0.94 |
| G1.5 | 1.86 | 1.74 | 0.95 |
| G3 | 1.87 | 1.76 | 0.94 |
| stock | 1.96 | 2.06 | 1.05 |
| WK0 (k = 1.05) | 1.62–1.70 | 1.38–1.44 | ~0.84 |

  Sieć komenderuje ~6% mniej niż w stocku, a autopilot realizuje ~94% komendy.
- **Porażki G1.5 nie są dynamiką wiatru:**
  - **c03 `a_entry`:** pierwszy track_valid po 30.7 s, wejście w pasmo po 33.6 s (limit 25 s).
    To opóźniona akwizycja (percepcja/skan). Obieg potem był pełny: sweep 819°, frac 1.0.
  - **c06 `c_sweep`+`d_dmin`:** utrata tracka ~24 s (t_rel 1.1–25.7 s, 484 z 1879 ticków w hold).
    Cel v = 0.5 zbliżył się, a po ponownej akwizycji d_min = 3.57 m przy t_rel 26.4 s
    (d_h 3.21, Δz 1.55). Skrócony obieg dał sweep 573°.
  - Ten sam scenariusz zdał przy 0 i przy 3 m/s. Zależność od wiatru jest **niemonotoniczna**
    (6/8 przy 1.5, 8/8 przy 3), co wskazuje na wariancję akwizycji/tracka, a nie na wiatr.

## §6. Pomiary opisowe (PRE §3, nie bramki)

| boot | przechył w locie p50 / p95 [°] | przechył hold p50 [°] | ciąg_E hold | klatki mti_ok | ENTRY | cel w kadrze (min per ep.) | alt_max EKF [m] |
|---|---|---|---|---|---|---|---|
| g0_b1 / b2 | 5.4 / 7.6 · 5.5 / 7.9 | 0.36 | 0.000 | 64.6% / 65.0% | 5 / 6 | 1.000 | 12.6–13.7 |
| g15_b1 / b2 | 7.7 / 11.4 · 6.6 / 11.1 | 4.3 | −0.075 | 61.6% / 65.1% | 5 / 5 | 0.990 | 11.7–12.7 |
| g3_b1 / b2 | 10.9 / 14.9 · 10.4 / 15.0 | 8.6 | −0.149 | 64.5% / 67.7% | 4 / 5 | 0.993 | 13.5–14.1 |
| baza stock FANTOM r1/r2 V2 | 3.3 / 6.6–8.5 | 0.5 | — | 80.0–81.6% | 4 / 6 | — | — |
| noga WK (k 1.05), WK0 | 8.7 / 12.2 | 0.8 | — | 62.9–64.5% | 4 / 6 | 1.000 | — |

- **Przechył hold:** 4.3° przy 1.5 m/s i 8.6° przy 3 m/s, czyli ∝ k·w (atan(0.49·3/9.81) = 8.5°).
  Ciąg_E < 0: dron pochyla się pod wiatr.
- **Pełzanie: brak.** alt_max ≤ 14.1 m, GEOFENCE 0.
- **Czas do pierwszego track_valid:** 0.0 s w 17/24 epizodów (track przeżywa z poprzedniego epizodu).
  Pozostałe: 8.7–14.2 s, oraz 30.7 s (G1.5 c03).
- **Klatki z MTI ok:** 62–68% na wszystkich poziomach G, wobec 80–82% w stocku i 63–65% w WK0.
  Różnica wobec stocku występuje już bez wiatru i nie rośnie z wiatrem.

## §7. Statusy

- **Kandydat werdyktu V-A2.** D6 (świadek): G0 **8/8**, G1.5 **6/8**, G3 **8/8**
  (pełny: 8/8 · 6/8 · 7/8).
- **k per poziom:** G0 0.494 / 0.491; G1.5 0.493 / 0.490; G3 0.491 / 0.486.
- Sejwy osłony **0**, breach **0**, REFUSE **0**.
- Booty: **6/≤18** (dolecenia V2′ 0, powtórki 0).
- KSIĘGA (wstępnie, do ANEKS_WK2-1):
  - P-WK2-1 (G0 ≥ 6/8) ✓;
  - P-WK2-2 (G3 ≥ 6/8) ✓;
  - P-WK2-3 (mediana sweep G0/stock ≥ 0.85) ✓ — 0.858, margines 0.008;
  - P-WK2-4 (breach 0) ✓.

## §8. Artefakty

- `worlds/world_wk2_s063_s1p5.sdf`, `worlds/world_wk2_s063_s3.sdf`
- `results/WK2/tools/{wk2_boot.sh, wk2_kcontrol.py, wk2_styczna.py}`
- `results/WK2/booty/{g0_b1, g0_b2, g15_b1, g15_b2, g3_b1, g3_b2}/` (bez `boot.ulg`, gitignore)
  + logi driverów
- `judge_G0.json`, `judge_G15.json`, `judge_G3.json`, `kcontrol.json`, `styczna.json`, `describe.json`,
  `baza_G0_vs_stock.json`
