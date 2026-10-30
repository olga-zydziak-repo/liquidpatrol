# RAPORT_WK3_S1 — noga WK-III „porywy": P1 → bramka → P2 (STOP-WK3-1)

Wykonawca · 30.10.2026 · PRE_WK3 (`8bc3d19f`, ARCH-1 sha256 3758b86f… PASS) + PROMPT_WK3_S1.
Sieć NCP-20 (wagi 0337d5ea), net_fantom (rejestr 87203d29), FEED=V2, reżim OPS. Habitat s = 0.63
(k ≈ 0.49 /s), sinus deterministyczny, komórki c00–c07 × s01 (v ≤ 0.5).

**Kandydat werdyktu (mechanicznie z PRE §3): V-A3** — P1 8/8 ≥ 6/8 ∧ P2 7/8 ≥ 6/8.
Booty **4/≤8** (P1 2 + P2 2; dolecenia/powtórki 0). Breach 0, REFUSE 0 (POS 0, GEOFENCE 0), V2′ 16/16.

## §0. Bramka wejścia

- ARCH-1: `PRE_WK3.md` bajt w bajt, sha256 `3758b86f49555d969f181bc0a39d0743f59bf00ebfc9fdeb390e037bc90f76e4`
  = oczekiwany ⇒ commit 1 nogi `8bc3d19f` (osobny, pierwszy).
- `git fetch`: origin/master = `3274d21b` (STOP-WK3R); `origin/master..HEAD` puste; porcelain czysty poza
  `?? results/DEMO_C/**`.
- FROZEN (sha8, sprawdzone przed pierwszym bootem): profil FastDDS a68a450b, sonda 8df528bb, mono_cam
  model.sdf 3354ae1e, x500_base (wind) 13c9174d, bench_judge 8ec0fcfb, ncp.npz 0337d5ea, net_controller
  e8c1b658, rejestr 87203d29, wk_judge c33c3ff8, wk2_k 09e4b440, wk_r3_view b733f1c1, wk2_boot.sh cf0959ef,
  światy world_wk3_p1 fe96b096, world_wk3_p2 e47ef380.
- **Odchylenie nazwane (drobne):** PROMPT §0.3 każe sprawdzić `wk3_gust.py` „sha z RECON_WK3", a RECON_WK3
  tego sha nie podaje. Plik niezmieniony od commita reconu `3274d21b` (`git diff 3274d21b` pusty):
  sha256 **12ea2f2f…** — wpisane tutaj jako wartość odniesienia.

## §1. Budowa (0 bootów)

### §1.1 Driver `results/WK3/tools/wk3_boot.sh` (sha256 039e368c…) — pełny diff wobec `wk2_boot.sh` cf0959ef

```
1a2,6                                   [H1: nagłówek — opis kopii; (D3) komunikaty]
> # results/WK3/tools/wk3_boot.sh — driver bootu nogi WK-III „porywy" (PRE_WK3 §2, PROMPT_WK3_S1 §1.1). KOPIA
> # results/WK2/tools/wk2_boot.sh (cf0959ef, nietknięty) ze zmianami WYŁĄCZNIE: (D1) lista światów = world_wk3_p1 /
> # world_wk3_p2 z pełnym sha (inny świat ⇒ ODMOWA), (D2) katalog wyjścia results/WK3/booty (REPO-2),
> # (D3) komunikaty. Piny, profil, sonda, blok manifestu nietknięte.
> # --- nagłówek kopii (wk2_boot.sh) ---
28,29c33,34                             [H2: (D3) komunikat użycia]
< # Użycie: wk2_boot.sh <BOOT_N> <NAZWA_pod_results/WK2/booty> <EP_IDS_csv> <WORLD=world_wk2_*>
< #   np.:  wk2_boot.sh 1 g0_b1 0,1,2,3 world_wk2_s063_s0
---
> # Użycie: wk3_boot.sh <BOOT_N> <NAZWA_pod_results/WK3/booty> <EP_IDS_csv> <WORLD=world_wk3_p1|world_wk3_p2>
> #   np.:  wk3_boot.sh 1 p1_b1 0,1,2,3 world_wk3_p1
33,34c38,39                             [H3: (D2) katalog wyjścia i log monitora]
< OUTDIR="$ROOT/results/WK2/booty/$NAME"
< MONLOG="$ROOT/results/WK2/booty/wk2_monitor.log"
---
> OUTDIR="$ROOT/results/WK3/booty/$NAME"
> MONLOG="$ROOT/results/WK3/booty/wk3_monitor.log"
37,41c42,44                             [H4: (D1) lista światów z pełnym sha + ODMOWA]
<   world_wk2_s063_s0)   WORLD_SHA_EXPECTED="73205686cb62b303b4fb85225b6a07abfce9991ea4b0222126b663c0346787c3";;
<   world_wk2_s063_s1p5) WORLD_SHA_EXPECTED="b8a9c8b7de4c99390e8e37322eb559ea5871777e4190a1ffaa40cc7325563722";;
<   world_wk2_s063_s3)   WORLD_SHA_EXPECTED="f8ccc51ca0e47a1a8edaf7418cc6882a89786cd17d6701c9716150698014b164";;
<   world_wk2_k055_s0)   WORLD_SHA_EXPECTED="ff60c065e2767d0ff1126bd6911920952c3d7023020ee9c4f5d1388b21bbdbd3";;
<   *) echo "[wk2 $NAME] GUARD: WORLD=$WORLD spoza listy światów WK2 — ODMOWA"; exit 5;;
---
>   world_wk3_p1) WORLD_SHA_EXPECTED="fe96b0965ccce76aa49db44cd1d5200761356a7a1829efc996359a90e69f2105";;
>   world_wk3_p2) WORLD_SHA_EXPECTED="e47ef38030c5095d9a5f09e86349a07a2aadda5c7ec2c085d906553dcbb179dc";;
>   *) echo "[wk3 $NAME] GUARD: WORLD=$WORLD spoza listy światów WK3 — ODMOWA"; exit 5;;
49c52                                   [H5: (D2) mkdir katalogu wyjścia]
< mkdir -p "$ROOT/results/WK2/booty"
---
> mkdir -p "$ROOT/results/WK3/booty"
```

Piny, guard profilu, sonda, blok manifestu (`fantom`/`feed_v2`/`perc2`/`wk`) — bez zmian.

### §1.2 Kontrola oporu
`results/WK3_RECON/tools/wk3_gust.py` (12ea2f2f) bez zmian, wywołanie per boot z literą świata:
P1 `2 0.4 8 0 1` (W0, A, Pm, Ad, Pd; Ad = 0 ⇒ Pd nieużywany), P2 `2 0.8 4 30 11`. Wartość kontrolna =
`k_przy_wietrze_z_litery_bez_wyrazu`; oczekiwane 0.494 /s, tolerancja ±20%.

### §1.3 Cel w kadrze — `results/WK3/tools/wk3_kadr.py` (sha256 55875787…, zamrożony przed lotami, `wk3_freeze.log`)

DEFINICJA (verbatim z narzędzia):

> Tick = wiersz demo.jsonl (tick inferencji sieci) epizodu. GT celu = najbliższy wiersz gt_intruder.jsonl
> (|Δt_sim| ≤ 0.1 s) PRZEFILTROWANY świadkiem ERRATUM-DMIN (|ned − cmd_ned| ≤ 1 m; tick bez świadka
> wypada z mianownika i jest liczony osobno). Orientacja drona = najbliższy vehicle_attitude z ulogu
> (most czasu t_sim = ulog_us·1e-6, sprawdzany jak wk_r3_view: mediana |z_ulog − own_z| < 0.10 m).
> Rzut geometrią wk_r3_view.project (FX/FY/CX/CY z r02/mti.py, CAM_OFF_FRD z harness/feed_vision.py).
> „W KADRZE" ⇔ wk_r3_view.in_frame: cel przed kamerą (z_opt > 0) i środek celu w prostokącie obrazu
> zwężonym o margines MTI 10 px z każdej strony — pionowo = pół-pole 40.4° po marginesie, poziomo = pole
> kamery po marginesie. Kierunek wypadnięcia: DÓŁ (v ≥ IMG_H − 10), GÓRA (v ≤ 10), BOK (u poza pasem
> przy v w pasie, albo z_opt ≤ 0 = za kamerą).
> „Wypadnięcie poprzedza utratę tracka": utrata = przejście track_valid true → false; poprzedza, gdy
> w oknie [t_utraty − 2.0 s, t_utraty] jest ≥ 1 tick poza kadrem.

Importuje `wk_r3_view.py` (b733f1c1), nie kopiuje. Przechył per epizod liczony na tych samych tickach
(z R[2,2] orientacji). Most czasu OK we wszystkich 4 bootach (mediana |Δz| 0.0004–0.0005 m).

### §1.4 Binaria
`worlds/wind_models/x500_base/meshes` obecne (README, nieśledzone); pin 13c9174d w logu każdego bootu.

## §2. Booty

| boot | świat (sha8) | epizody | pin mono_cam / x500_base | sonda | V2′ (dsim/dwall) | k (litera) | odch. |
|---|---|---|---|---|---|---|---|
| p1_b1 | world_wk3_p1 fe96b096 | c00–c03 | 3354ae1e / 13c9174d OK | PASS (14.7 Hz) | 4/4 (0.9985–0.9999) | 0.4949 | +0.2% |
| p1_b2 | world_wk3_p1 fe96b096 | c04–c07 | OK / OK | PASS | 4/4 (0.9986–1.0000) | 0.4948 | +0.2% |
| p2_b1 | world_wk3_p2 e47ef380 | c00–c03 | OK / OK | PASS | 4/4 (0.9987–1.0000) | 0.4962 | +0.5% |
| p2_b2 | world_wk3_p2 e47ef380 | c04–c07 | OK / OK | PASS | 4/4 (0.9986–1.0000) | 0.4946 | +0.1% |

Kontrola oporu 4/4 w tolerancji (maks. +0.5%). Metodą „wiatr stały" (zabronioną, tylko dla porównania):
0.481 / 0.477 / 0.431 / 0.415 — zaniżenie −3 / −3 / −13 / −16%, zgodnie z reconem R3.
Wiatr odtworzony przez drona sieci (sinus przy okresie z litery): P1 średnia 2.02, amplituda 0.813 / 0.814
(litera 0.8); P2 1.638 / 1.641 (litera 1.6), kierunek ±29.9° / ±30.7° (litera ±30°), faza ≤ 3.2°.

## §3. Werdykty per epizod (sędzia bazowy 8ec0fcfb; pełny | świadek ERRATUM-DMIN)

**P1** (`judge_P1.json`): świadek **8/8**, pełny 6/8.

| ep. | pełny | świadek | t_entry [s] | frac 6–10 | sweep [°] | d_min [m] |
|---|---|---|---|---|---|---|
| c00 | ✓ | ✓ | 3.72 | 1.00 | 764.6 | 7.14 |
| c01 | ✓ | ✓ | 6.65 | 1.00 | 830.1 | 7.29 |
| c02 | ✓ | ✓ | 11.73 | 1.00 | 874.2 | 7.26 |
| c03 | ✓ | ✓ | 16.32 | 1.00 | 842.1 | 7.16 |
| c04 | ✓ | ✓ | 3.14 | 1.00 | 811.7 | 6.35 |
| c05 | ✓ | ✓ | 5.20 | 1.00 | 801.5 | 6.87 |
| c06 | ✗ b_frac | ✓ | 10.54 | 1.00 | 806.3 | 6.75 |
| c07 | ✗ b_frac | ✓ | 11.54 | 1.00 | 715.0 | 7.89 |

Rozjazd c06/c07: bez filtra pierwsze próbki GT (przed ustawieniem celu, odrzucone przez świadka: 2 i 1)
dają t_entry 0.0 i frac 0.849 / 0.838 < 0.85 — ta sama klasa artefaktu co G3 c07 w WK-II (ANEKS_WK2-1 §1.3).
**Bramki nie rozstrzyga** (pełny 6/8 i świadek 8/8 — oba ≥ 6/8).

**P2** (`judge_P2.json`): świadek **7/8**, pełny **7/8** (zgodne).

| ep. | pełny | świadek | t_entry [s] | frac 6–10 | sweep [°] | d_min [m] |
|---|---|---|---|---|---|---|
| c00 | ✓ | ✓ | 3.04 | 1.00 | 812.0 | 7.20 |
| c01 | ✗ a_entry | ✗ a_entry | **26.22** | 1.00 | 838.2 | 7.14 |
| c02 | ✓ | ✓ | 13.08 | 1.00 | 828.4 | 6.53 |
| c03 | ✓ | ✓ | 15.50 | 1.00 | 843.3 | 7.32 |
| c04 | ✓ | ✓ | 2.46 | 1.00 | 812.7 | 6.96 |
| c05 | ✓ | ✓ | 5.29 | 1.00 | 799.5 | 7.17 |
| c06 | ✓ | ✓ | 9.47 | 1.00 | 819.9 | 6.54 |
| c07 | ✓ | ✓ | 11.30 | 1.00 | 735.7 | 7.70 |

**Porażka P2 c01 — mechanizm z logów: akwizycja na 15 m, nie kadr i nie przechył.** Track startowy
wygasa w t_rel 2.95 s (jak w każdym c01: WK-II G0/G1.5/G3 i P1 — przerwa 0.7–3.3 s), po czym ponowna
akwizycja trwa **20.5 s** (2.95 → 23.4 s), cel nieruchomy na 14.4–15.1 m, faza hold. W tej przerwie cel był
w kadrze przez 172 ticki (~8 s; skan go przeprowadza przez obraz), bokiem poza kadrem 208, dołem 22;
przechył maks. 9.5°. Po akwizycji wejście w pas po 26.22 s (limit 25 s), potem pełna orbita (sweep 838°,
frac 1.00, d_min 7.14). Klasa = G1.5 c03 z WK-II (akwizycja 30.7 s) i sufit dalekiego wzroku (PERCEPCJA-II);
przy n = 1 nie odróżnię wpływu porywu na detekcję od wariancji.

GEOFENCE: 0 prawdziwych / 0 fałszywych w obu profilach. Breach 0. REFUSE(POS) 0.

## §4. Przechył i kadr per epizod (definicja §1.3)

Kolumny: poza kadrem (razem / dół / góra / bok), ticki bez świadka, utraty tracka t_rel, utraty
poprzedzone wypadnięciem, przechył p50 / p95 / max [°] (`kadr.json`).

| boot | ep. | poza | dół | góra | bok | bez św. | utraty | poprzedzone | przechył |
|---|---|---|---|---|---|---|---|---|---|
| p1_b1 | c00 | 0.009 | 0 | 0.001 | 0.008 | 0 | — | — | 6.9 / 12.4 / 17.3 |
| p1_b1 | c01 | 0.042 | 0.031 | 0 | 0.011 | 0 | 2.85 | 2.85 | 6.5 / 12.3 / 18.2 |
| p1_b1 | c02 | 0.098 | 0.002 | 0 | 0.096 | 0 | — | — | 7.4 / 12.6 / 22.2 |
| p1_b1 | c03 | 0.141 | 0 | 0.001 | 0.140 | 1 | — | — | 8.0 / 12.6 / 26.5 |
| p1_b2 | c04 | 0.009 | 0 | 0.003 | 0.006 | 0 | — | — | 7.3 / 14.5 / 17.6 |
| p1_b2 | c05 | 0.042 | 0.008 | 0 | 0.035 | 2 | 3.22 | 3.22 | 6.8 / 14.0 / 17.4 |
| p1_b2 | c06 | 0.106 | 0.002 | 0 | 0.104 | 2 | 1.93 | 1.93 | 7.5 / 12.8 / 19.7 |
| p1_b2 | c07 | 0.147 | 0 | 0.028 | 0.119 | 2 | 3.00 | 3.00 | 7.1 / 11.9 / 23.2 |
| p2_b1 | c00 | 0.000 | 0 | 0 | 0 | 0 | — | — | 8.5 / 13.8 / 19.5 |
| p2_b1 | c01 ✗ | 0.152 | 0.037 | 0 | 0.115 | 2 | 2.95 | 2.95 | 7.3 / 13.2 / 18.3 |
| p2_b1 | c02 | 0.093 | 0.004 | 0 | 0.090 | 3 | — | — | 7.9 / 13.7 / 24.3 |
| p2_b1 | c03 | 0.143 | 0 | 0.007 | 0.137 | 0 | — | — | 8.1 / 13.3 / 25.9 |
| p2_b2 | c04 | 0.000 | 0 | 0 | 0 | 0 | — | — | 8.7 / 14.2 / 18.2 |
| p2_b2 | c05 | 0.047 | 0.040 | 0 | 0.008 | 2 | 3.16 | 3.16 | 7.6 / 13.8 / 16.3 |
| p2_b2 | c06 | 0.105 | 0 | 0 | 0.105 | 2 | 0.21 | 0.21 | 7.9 / 13.7 / 20.2 |
| p2_b2 | c07 | 0.149 | 0 | 0.033 | 0.116 | 0 | 2.95 | 2.95 | 7.1 / 13.6 / 21.1 |

Epizody z celem poza kadrem ≥ 5% ticków: P1 4/8, P2 5/8. **Odniesienie WK-II przy stałym wietrze, ta sama
definicja** (`kadr_ref_WK2.json`): G1.5 5/8, G3 4/8; dół maks. 3.1–3.4% (P1 3.1%, P2 4.0%); przechył maks.
24.2–29.5° (P1 26.5°, P2 25.9°). Odsetek poza kadrem to w 85% BOK (dół 10%, góra 5%; suma po epizodach P1+P2) (faza hold/skan przed akwizycją
i obrót na cel), nie dół. Wszystkie „utraty poprzedzone wypadnięciem" leżą w t_rel 0.2–3.2 s = wygaśnięcie
tracka startowego przy celu bokiem (przechył w chwili utraty ≤ 9°) — wzór obecny także w WK-II.
**Ryzyko nazwane z reconu (przechył do 34.6° u nauczyciela) w lotach sieci nie zaszło:** maks. przechył
sieci w P2 25.9° (orbita p95 13.5–13.9°), poniżej pół-pola 40.4°; żadna porażka nie jest poprzedzona
wypadnięciem z kadru dołem.

Przechył w fazie orbity (wk3_gust, p50 / p95 / max): P1 7.6 / 12.4–13.4 / 14.7–23.4; P2 8.0–8.2 /
13.5–13.9 / 19.5–21.3.

## §5. Pomiary opisowe

- **Sweep / stock** (baza FANTOM S2 r1_V2/r2_V2, świadek; `baza_P*_vs_stock.json`): mediana **P1 0.897,
  P2 0.885** (WK-II: G0 0.858, G1.5 0.834, G3 0.895). Sweep per scenariusz wobec WK-II: P1/P2 w paśmie
  G1.5/G3 (715–874° vs 683–872°; bez porażki G1.5 c06 573°).
- **Składowa styczna** (`styczna.json`, mediany per profil): komenda 1.851 / 1.845 m/s, zrealizowana
  1.765 / 1.721, realizacja 0.945 / 0.923 (WK-II: komenda 1.84–1.87, realizacja 0.94).
- **Akwizycja** (pierwszy ważny track, t_rel): c00/c01/c04–c07 — track od startu; c02 8.6 / 10.1 s,
  c03 13.4 / 12.4 s (P1 / P2) — te same komórki późne co w poprzednich nogach. Wyjątek: P2 c01 (§3).
- **k per boot:** §2.

## §6. Bramka i kandydat werdyktu

- Bramka P1 (świadek): **8/8 ≥ 6/8 ⇒ P2** (pełny 6/8 — też ≥ 6/8; rozjazd nierozstrzygający).
- P2 (świadek): **7/8 ≥ 6/8**.
- **Kandydat: V-A3** (P1 ≥ 6/8 ∧ P2 ≥ 6/8). Do zdania z PRE §3: D6 a/8 · b/8 = **8/8 · 7/8**, breach 0,
  sejwy 0.

## §7. Pliki (wyłącznie nowe)

- `results/WK3/tools/wk3_boot.sh` (039e368c), `results/WK3/tools/wk3_kadr.py` (55875787), `wk3_freeze.log`
- `results/WK3/booty/{p1_b1,p1_b2,p2_b1,p2_b2}/**` (+ `_launch.log`, `wk3_monitor.log`), `booty_*_driver.log`
- `judge_P1.json`, `judge_P2.json`, `kgust_{p1_b1,p1_b2,p2_b1,p2_b2}.json`, `kadr.json`, `kadr_ref_WK2.json`,
  `baza_P1_vs_stock.json`, `baza_P2_vs_stock.json`, `styczna.json` (wk2_styczna.py, import bez zmian)

ZERO edycji istniejących plików. Push = Olga.
