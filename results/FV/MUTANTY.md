# MUTANTY — katalog mutacji lustra (M-krok, ANEKS_FV-1 §5) — PREREJESTRACJA (CM1)

Cel M-kroku: dowieść, że różnicówka `tests_fv_diff.py` (siatka `fv_diff_grid.json` + fuzz {0..4} 10⁵/fn)
WIDZI błędy klas, które ma łapać — zanim na jej wierności postawimy dowód O2. Mutacje WYŁĄCZNIE w
pamięci (`tests_fv_mutants.py`); `fv_mirror.py` na dysku NIETKNIĘTY. Oracle = PRODUKCJA (`r01/shield.py`,
`r03/controllers/safe_descend.py`). Mutant WYKRYTY ⇔ ≥1 rozbieżność mutant-lustro↔produkcja na
siatce+fuzz. Kryterium M3: 100% wykrytych; przeżywający ⇒ punkty domykające `fv_diff_grid2.json`
(commit przed ponownym biegiem), ≤3 iteracje (S2-C).

Cztery klasy mutacji (ANEKS_FV-1 §5): (i) `<`↔`<=`/strictness na progu · (ii) ±1 na stałych
całkowitych/licznikach · (iii) negacja pojedynczego warunku · (iv) zamiana kolejności dwóch gałęzi.

**LISTA NIETYKALNA po CM1** (rozszerzenie = osobny commit z notą, nie podmiana — S2-B).

Uwaga o pokryciu klas: klasa (ii) nie ma miejsca zastosowania w `geofence_violation` (progi to
PARAMETRY r_e/v_e/v_max, brak literałów całkowitych) ani w `safe_descend_step` (profil to stałe
zmiennoprzecinkowe) — 0 mutantów (ii) tam, jawnie. `braking_dist` ma jedną operację progową (clamp
v_max przez `min`) — jeden mutant (min↔max), zaklasyfikowany jako (i)-analog „strictness/kierunek progu".

## braking_dist — fv_mirror.py:28-31
| id | miejsce | klasa | opis |
|----|---------|-------|------|
| bd_clamp_min_max | :30 `min(...,v_max)` | (i)* | min ↔ max (kierunek clampu progu v_max) |

## geofence_violation — fv_mirror.py:35-48
| id | miejsce | klasa | opis |
|----|---------|-------|------|
| gf_re_strict   | :41 `tr > r_e`               | (i)   | `>` → `>=` |
| gf_pr_strict   | :44 `pr+brake > r_e`         | (i)   | `>` → `>=` |
| gf_vet_strict  | :46 `abs(target_z) > v_e`    | (i)   | `>` → `>=` |
| gf_vep_strict  | :46 `abs(pos_z) > v_e`       | (i)   | `>` → `>=` |
| gf_neg_re      | :41 warunek                  | (iii) | negacja `tr > r_e` |
| gf_neg_pr      | :44 warunek                  | (iii) | negacja `pr+brake > r_e` |
| gf_neg_ve      | :46 warunek                  | (iii) | negacja `(abs(tz)>v_e) or (abs(pz)>v_e)` |
| gf_swap_re_pr  | :41 ↔ :44 bloki              | (iv)  | zamiana kolejności bramki R_E-cel i R_E-pozycja+hamowanie |
| gf_swap_pr_ve  | :44 ↔ :46 bloki              | (iv)  | zamiana kolejności bramki pozycja+hamowanie i pionu |

## pos_monitor_step — fv_mirror.py:58-76
| id | miejsce | klasa | opis |
|----|---------|-------|------|
| pm_deb_strict       | :66 `>= debounce_ticks` | (i)   | `>=` → `>` |
| pm_hyst_strict      | :73 `>= hyst_ticks`     | (i)   | `>=` → `>` |
| pm_deb_plus1        | :66 debounce_ticks      | (ii)  | próg → debounce_ticks+1 |
| pm_deb_minus1       | :66 debounce_ticks      | (ii)  | próg → debounce_ticks−1 |
| pm_hyst_plus1       | :73 hyst_ticks          | (ii)  | próg → hyst_ticks+1 |
| pm_hyst_minus1      | :73 hyst_ticks          | (ii)  | próg → hyst_ticks−1 |
| pm_badinc2          | :64 `pos_bad += 1`      | (ii)  | `+= 1` → `+= 2` |
| pm_neg_flag         | :63 `if pos_flag`       | (iii) | negacja gałęzi pos_flag |
| pm_neg_refuse_guard | :66 `not pos_refuse`    | (iii) | usunięcie `not` (guard wejścia) |
| pm_neg_refuse_exit  | :71 `if pos_refuse`     | (iii) | negacja guardu wyjścia |
| pm_swap_branches    | :63 ↔ :69 bloki         | (iv)  | zamiana bloku True i else |

## safe_descend_step_mirror — fv_mirror.py:85-104
| id | miejsce | klasa | opis |
|----|---------|-------|------|
| sd_fast_strict    | :94 `el < desc_fast_dur`  | (i)   | `<` → `<=` |
| sd_total_strict   | :102 `el >= desc_total`   | (i)   | `>=` → `>` |
| sd_neg_descending | :89 `not st["descending"]`| (iii) | negacja guardu init |
| sd_neg_hswitch    | :97 `not st["h_switched"]`| (iii) | negacja guardu h_switch |
| sd_neg_td         | :102 `not st["td"]`       | (iii) | negacja guardu touchdown |
| sd_swap_phase     | :94-100 przypis vdesc     | (iv)  | zamiana v_desc_fast ↔ v_desc_land |

**Razem: 27 mutantów** (braking 1 · geofence 9 · pos_monitor 11 · safe_descend 6).
Wyniki per mutant (M4) + iteracje grid2 → sekcja „## Wyniki M" dopisana w CM2 (lista powyżej nietykalna).

## Wyniki M (CM2) — bieg `tests_fv_mutants.py run`

Oracle = produkcja. Sanity IDENTITY (mut='none') = 0 rozbieżności (szablon wierny). **WYKRYTE 27/27 = 100%.**
Zero przeżywających ⇒ `fv_diff_grid2.json` NIEPOTRZEBNA (0 iteracji grid2). Wykrycie (early-exit, pierwsza rozbieżność):

| mutant | funkcja | wykryty przez |
|--------|---------|---------------|
| bd_clamp_min_max | braking | siatka braking_dist#0 |
| gf_re_strict | geofence | siatka geofence#2 |
| gf_pr_strict | geofence | siatka geofence#7 |
| gf_vet_strict | geofence | siatka geofence#11 |
| gf_vep_strict | geofence | siatka geofence#12 |
| gf_neg_re | geofence | siatka geofence#0 |
| gf_neg_pr | geofence | siatka geofence#0 |
| gf_neg_ve | geofence | siatka geofence#0 |
| gf_swap_re_pr | geofence | fuzz seed0#2 |
| gf_swap_pr_ve | geofence | fuzz seed0#6 |
| pm_deb_strict | pos_monitor | siatka pos_monitor#0 |
| pm_hyst_strict | pos_monitor | siatka pos_monitor#3 |
| pm_deb_plus1 | pos_monitor | siatka pos_monitor#0 |
| pm_deb_minus1 | pos_monitor | siatka pos_monitor#0 |
| pm_hyst_plus1 | pos_monitor | siatka pos_monitor#3 |
| pm_hyst_minus1 | pos_monitor | siatka pos_monitor#3 |
| pm_badinc2 | pos_monitor | siatka pos_monitor#0 |
| pm_neg_flag | pos_monitor | siatka pos_monitor#0 |
| pm_neg_refuse_guard | pos_monitor | siatka pos_monitor#0 |
| pm_neg_refuse_exit | pos_monitor | siatka pos_monitor#3 |
| pm_swap_branches | pos_monitor | siatka pos_monitor#0 |
| sd_fast_strict | safe_descend | siatka safe_descend#0 |
| sd_total_strict | safe_descend | siatka safe_descend#1 |
| sd_neg_descending | safe_descend | siatka safe_descend#0 (crash el=now−None ⇒ wykrycie) |
| sd_neg_hswitch | safe_descend | siatka safe_descend#0 |
| sd_neg_td | safe_descend | siatka safe_descend#1 |
| sd_swap_phase | safe_descend | siatka safe_descend#0 |

Nota: `pm_neg_flag` (iii) i `pm_swap_branches` (iv) są behawioralnie zbieżne (negacja selektora `if pos_flag`
= zamiana bloku True↔else) — dwa wpisy katalogu, oba zabite; różnią się KLASĄ mutacji, nie efektem.
Wykrycie dominująco przez siatkę deterministyczną (25/27); tylko dwa swap-mutanty geofence wymagały fuzz
(potrzeba dwóch warunków bramki prawdziwych jednocześnie przy różnych detalach — brzegowa siatka trafia
progi pojedynczo). **M5:** finalny bieg pełnej różnicówki (siatka+fuzz 4×10⁵+fikstura 4221/1791) na
niemutowanym lustrze = 0 rozbieżności.
