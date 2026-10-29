# RAPORT_WK_S1 — noga WIATR-KAMERA, sesja S1: budowa, dym, etap A (WK0), bramka

CC-wykonawca · 29.10.2026 · PROMPT_WK_S1 + PRE_WK (sha256 281750e7…abebd, commit 1 nogi `8229e185`).
**Booty: 3/≤9** (dym 1 + WK0 2). Breach 0, REFUSE 0. **Bramka etapu A NIE przechodzi ⇒ STOP-WK1,
ścieżka V-C; etap B (1.5 / 3 m/s) nie poleciał.**

## §0. Bramka wejścia

- ARCH-1: `PRE_WK.md` verbatim, sha256 `281750e7cff6e6352f0377e3461989fc31e00075460d6395e4e8e53f8faabebd`
  PASS, commit 1 nogi `8229e185` (osobny, pierwszy).
- origin/master == HEAD == 4d7d5196; gate pusty; porcelain czysty poza `??` DEMO_C.
- FROZEN, sha zgodne:
  - reżim OPS: profil a68a450b, sonda 8df528bb, pin mono_cam 3354ae1e (pełny);
  - FREEZE_DET: det_v2 775ead15, det_v2.py e801f7d5, percep_proc 38a3a765, feed_vision_proc 79633489,
    feed_registry ee1481f9, det_labels 8f7430cd, det_replay de0feb37, make_dataset e958cc48,
    detS1_boot a7313b3c;
  - x500_base 13c9174d, w_judge e68040ae, sędzia 8ec0fcfb, bench 05137098;
  - sieć i kontrolery: ncp 0337d5ea, net_controller e8c1b658, fantom_scan e435ed7e, rejestr 87203d29,
    akw_scan b94cdeae;
  - piny osłony 5/5 (SHIELD FROZEN True), certy 9/9 PASS, world_hash.sh zgodny z HEAD;
  - światy reconu: s0 4c179a14, s1p5 9713a8b1, s3 3a605ca3.

## §1. Budowa (0 bootów, wyłącznie nowe pliki)

1. **Światy:** `worlds/world_wk_{s0,s1p5,s3}.sdf` są nowymi plikami, skopiowanymi bajt w bajt
   z `results/WK_RECON/worlds/`. sha 4c179a14 / 9713a8b1 / 3a605ca3 są identyczne z reconem.
2. **Binaria modelu wiatrowego:** `cp -rn` ze stocku według README do
   `worlds/wind_models/x500_base/{meshes,materials,thumbnails,LICENSE}`. Pliki są nieśledzone
   (`worlds/wind_models/.gitignore`), a sha `x500_base/model.sdf` = 13c9174d bez zmian.
3. **Driver** `results/WK/tools/wk_boot.sh` (sha ecf8071c) to kopia
   `results/PERC2/tools/perc2_s2_boot.sh`. Pełny diff ma 66 linii i 9 hunków:

| hunk | linie (orig → nowy) | nazwa | treść |
|---|---|---|---|
| H1 | 2-4 → 2-7 | nagłówek | opis kopii i listy zmian; nagłówek oryginału zachowany niżej |
| H2 | 18-19 → 21-22 | użycie | 4. argument WORLD |
| H3 | 22-24 → 25-27 | argumenty + katalog wyjścia | `WORLD="${4}"`, OUTDIR i MONLOG w `results/WK/booty/` |
| H4 | 26 → 29-36 | WORLD + oczekiwane sha | `case` na trzy światy WK (inny ⇒ ODMOWA), ścieżka i pin x500_base 13c9174d |
| H5 | 31 → 41 | katalog wyjścia | `mkdir -p results/WK/booty` |
| H6 | +67-76 | piny i sha świata PRZED bootem | pin x500_base, obecność `meshes/`, sha świata; rozjazd ⇒ exit 6 (STOP bootu) |
| H7 | +98-100 | prepend ścieżki zasobów | `GZ_SIM_RESOURCE_PATH=worlds/wind_models:…` (wzór w_launcher.sh:42) + dowód w `.gz_resource_path` |
| H8 | 137 → 160, +163 | argumenty manifestu | przekazanie WORLD, sha świata, pinu x500_base |
| H9 | +208-211 | blok `wk` w manifeście | świat, sha świata, oba piny, ścieżka zasobów |

   Poza tymi hunkami litera oryginału zostaje bez zmian: etykieta `KIND=perc2`, prefiksy logów
   `perc2S2`, sonda, profil, proc_gate, cooldown, REPO-2. Diff jest w commicie (oba pliki w repo).
4. **Sędziowanie** `results/WK/tools/wk_judge.py` (c33c3ff8) importuje sędziego 8ec0fcfb,
   helpery w_judge e68040ae (`median_err_before_trip`, `EPS_FALSE`=2.0) oraz `load_boot`/`DEV_GATE`
   ze `results/POSCIG_RECON/tools/erratum_sweep.py`.
   - D6 liczy dwa razy: pełny i ze świadkiem (|ned − cmd_ned|_xy ≤ 1 m), z refuse/breach
     z `episode_end`.
   - GEOFENCE klasyfikuje jako PRAWDZIWY ⇔ mediany |EKF−GT| poziomo **i** pionowo < 2.0 m.
     Kierunek jest jawny: `w_judge.classify()` ocenia REFUSE(POS), gdzie ta sama liczba czyta się
     odwrotnie.
   - **Test na sucho:**
     - PERC2 S2 bA_c08 + bB_c1011: `repro_manifest` 8/8 (success_D6 i d_min co do 0.01 m).
     - Świadek odtwarza znane flipy c08_s03/s04.
     - Kontrola klasyfikatora na W L3 net_s02 (GEOFENCE z ANEKS_W-2): PRAWDZIWY,
       mediana pionu 0.0238 m (ANEKS: 0.024).

Narzędzia opisowe: `wk_describe.py` (07bf3fae; kontrole dymu + pomiary opisowe, rzut na kadr
z reconu `wk_r3_view.py`) i `wk_baza.py` (bbb8f918; porównanie z bazą stock na tych samych
scenariuszach).

## §2. Booty

| # | boot | świat (sha) | epizody | piny (mono_cam / x500_base) | world_hash.txt | sonda preflight | V2′ | breach / REFUSE |
|---|---|---|---|---|---|---|---|---|
| 1 | dym_s3 | world_wk_s3 (3a605ca3) | c00_s01 | 3354ae1e / 13c9174d | 3a605ca3 | PASS dt 0.068, frac 0.000 | 1/1 | 0 / 0 |
| 2 | wk0_b1 | world_wk_s0 (4c179a14) | c00–c03 s01 | 3354ae1e / 13c9174d | 4c179a14 | PASS dt 0.068, frac 0.002 | 4/4 | 0 / 0 |
| 3 | wk0_b2 | world_wk_s0 (4c179a14) | c04–c07 s01 | 3354ae1e / 13c9174d | 4c179a14 | PASS dt 0.068, frac 0.002 | **3/4** | 0 / 0 |

Każdy boot: `rc=0`, `finalize=0`, `[augment] world_hash=True ulog_sha=True model_in_state=True`.
Sonda przeszła za pierwszym razem, uzbrojenie było po sondzie.

### Dym (PRE §2.1, poza D6): **PASS za pierwszym podejściem**

| kontrola | wynik |
|---|---|
| model ładuje wiatr | w zawisie (ticki hold, n = 18) oś ciągu ma składową E średnio **−0.256** (dron pochyla się pod wiatr +x ENU), przechył hold p50 **14.5°** / p95 16.8° (baza stock FANTOM S2: 0.5°); dryf w hold p50 0.07 m / p95 0.26 m; przechył w locie p50 19.3° / p95 26.6° |
| sonda k = 1 | PASS przed uzbrojeniem (dt_p50 0.068 s/klatkę, frac > 0.10 = 0.0, 14.71 Hz) |
| ≥ 1 admisja | **3 × ENTRY** w percep_feed |
| world_hash + oba piny w manifeście | tak (blok `wk` + `perc2`) |
| V2′ ≥ 0.90 | 1/1 (dsim/dwall 0.933) |

Opisowo: epizod c00_s01 przy 3 m/s miał D6 PASS (d_min 6.29 m), cel był w kadrze w 92.9% ticków,
alt_max 14.8 m, mti_ok 46.4% klatek.

## §3. Etap A — WK0 (wiatr 0, habitat z oporem): werdykty per epizod

Sędzia bazowy 8ec0fcfb, GT z manifestu. Kolumna „świadek" = gt_intruder po filtrze ERRATUM-DMIN.

| scenariusz | V2′ | D6 pełny | D6 świadek | powody (pełny / świadek) | t_entry [s] | frac pasma | sweep [°] | d_min [m] |
|---|---|---|---|---|---|---|---|---|
| c00_s01 | ✓ | ✗ | ✗ | c_sweep / c_sweep | 4.29 | 1.000 | 601.7 | 7.95 |
| c01_s01 | ✓ | ✗ | ✗ | c_sweep / c_sweep | 8.22 | 1.000 | 616.0 | 7.84 |
| c02_s01 | ✓ | ✗ | ✗ | a_entry / a_entry | 27.35 | 1.000 | 681.2 | 7.47 |
| c03_s01 | ✓ | **✓** | **✓** | — | 15.16 | 1.000 | 659.1 | 7.77 |
| c04_s01 | **✗** (dsim/dwall 0.8905) | **✓** | **✓** | — | 3.33 | 1.000 | 639.2 | 7.32 |
| c05_s01 | ✓ | ✗ | ✗ | c_sweep / c_sweep | 6.40 | 1.000 | 601.7 | 7.00 |
| c06_s01 | ✓ | ✗ | ✗ | c_sweep / c_sweep | 7.94 | 1.000 | 576.4 | 7.26 |
| c07_s01 | ✓ | ✗ | ✗ | b_frac+c_sweep / c_sweep | 0.0 / 13.88 | 0.809 / 1.000 | 469.8 / 524.2 | 8.06 |

**WK0 = 2/8 D6 (pełny 2/8, świadek 2/8); wśród epizodów ważnych V2′: 1/7.**

- Rozjazd pełny/świadek dotyczy wyłącznie powodów porażki c07 (świadek zdejmuje fałszywe
  t_entry = 0.0). Żadnego werdyktu D6 nie zmienia, więc adjudykacja nie jest potrzebna.
- **Zdarzenia GEOFENCE: 0.** Brak REFUSE czegokolwiek, brak breach.

## §4. Decyzja bramki (mechanicznie, PRE §2.2 / PROMPT §2.3)

WK0 (świadek) = **2/8 < 6/8 ⇒ STOP-WK1, ścieżka V-C; etapu B nie latam.**

- Bramka nie zależy od rozstrzygnięć granicznych: przy 7 epizodach ważnych daje 1/7, przy 8 daje 2/8.
- Pełny i świadek dają ten sam wynik. Powtórka c04 (V2′ ✗) dałaby maksymalnie 2/8.

**ODCHYLENIE NAZWANE (powtórka):** PRE pozwala na jedną powtórkę bootu nieważnego na poziom.
wk0_b2 ma 3/4 epizodów ważnych (c04: dsim/dwall 0.8905 < 0.90). Powtórki nie zużyłem, bo żaden
jej wynik nie zmienia bramki (2/8 albo 1/7 < 6/8). Decyzja o jej sensie należy do CC.

## §5. Kandydat werdyktu (mechanicznie z PRE §3): **V-C**

> „sam habitat z oporem łamie misję kamerową sieci uczonej bez oporu: **2/8**" + mechanizm z danych:

**Mechanizm (opisowo, `baza_wk0_vs_stock.json`): opór spowalnia obieg, nie wzrok ani pościg.**

Na tych samych 8 scenariuszach (c00–c07 × s01) kamerowa baza stock (FANTOM S2 V2, ten sam
kontroler, sędzia ze świadkiem) zdaje **8/8**, ze sweep **767–996°**. W WK0:

- **sweep 524–681°, czyli 0.62–0.83 × stock** (mediana 0.665). Próg D6 to 630°, więc 5/6 porażek
  to `c_sweep`. Sieć krąży o około 1/3 wolniej kątowo.
- **frac pasma 1.000 w 8/8** (świadek): sieć trzyma dystans 6–10 m bez zarzutu.
- **d_min 7.0–8.1 m**: żadnych zbliżeń.
- **Cel w kadrze 100% ticków w 8/8 epizodów**; brak pełzania (alt_max 11.5–13.0 m według EKF,
  13.0–14.2 m według GT; mediany cmd_vz −0.06…+0.04 m/s). Przewidywane w reconie pełzanie w trybie
  kamerowym przy wietrze 0 nie wystąpiło.
- Jedna porażka `a_entry` (c02): pierwszy track_valid po 24.3 s (stock: wejście 12.6 s).
  To opóźniona akwizycja, a nie dynamika orbity.

To ta sama ścieżka porażki co w kampanii W (rejudge CC: NCP padał na `c_sweep` przy 0 m/s na c11).
Teraz jest zmierzona na własnej kamerze i na komórkach v ≤ 0.5.

## §6. Pomiary opisowe (PRE §3, nie bramki)

| boot | przechył w locie p50 / p95 [°] | przechył hold p50 [°] | klatki z mti_ok | ENTRY | w kadrze |
|---|---|---|---|---|---|
| dym_s3 (3 m/s) | 19.3 / 26.6 | 14.5 | 46.4% | 3 | 92.9% |
| wk0_b1 (0 m/s) | 8.7 / 12.2 | 0.8 | 62.9% | 4 | 100% ×4 |
| wk0_b2 (0 m/s) | 8.8 / 12.1 | 0.8 | 64.5% | 6 | 100% ×4 |
| baza stock FANTOM r1_V2 / r2_V2 | 3.4 / 6.6 · 3.3 / 8.5 | 0.5 | 81.6% / 80.0% | 4 / 6 | — |

- **Przechył w locie przy wietrze 0** to ~8.7° wobec ~3.3° na stocku: opór wymaga większego
  pochylenia przy tej samej komendzie prędkości. Zgadza się z reconem (W L0 ~9°).
- **Odsetek klatek z MTI ok** przy wietrze 0 to 63–65% wobec 80–82% na stocku, a w dymie przy
  3 m/s 46%. Mierzone tylko opisowo: WK1.5 i WK3 nie poleciały, więc porównanie „przy wietrze
  wobec WK0" ma jedną próbkę z dymu.
- **Ważność czasu (V2′):** dsim/dwall w złożonym świecie wynosi 0.89–0.94, a na stocku w PERC2 S2
  ~0.995. Jeden epizod (c04) spadł pod 0.90. Złożony świat (WindEffects + kamera) pracuje blisko
  progu ważności.
- Czas do pierwszego track_valid: 0.0 s w 5/8 epizodów (track przeżywa z poprzedniego epizodu),
  oraz 8.5 / 12.4 / 24.3 s.

## §7. Statusy

- **Kandydat werdyktu: V-C**. Etap A daje WK0 = 2/8 D6 (świadek; pełny 2/8; ważne V2′ 1/7).
  Mechanizm: sweep 0.62–0.83 × stock przy frac 1.000, d_min ≥ 7.0 m i celu w kadrze 100%.
- Etap B (WK1.5 / WK3): nie poleciał (bramka).
- Sejwy osłony: **0**. Breach: **0**. REFUSE: **0**.
- Booty: **3 / ≤ 9** (dym 1, WK0 2, powtórki 0).
- KSIĘGA (do ANEKS_WK-1, wstępnie): P-WK-1 ✓, P-WK-2 ✗, P-WK-3 n.r., P-WK-4 ✓, P-WK-5 ✗.

## §8. Artefakty

- `worlds/world_wk_{s0,s1p5,s3}.sdf`
- `results/WK/tools/{wk_boot.sh, wk_judge.py, wk_describe.py, wk_baza.py}`
- `results/WK/booty/{dym_s3, wk0_b1, wk0_b2}/` (bez `boot.ulg` — gitignore, jak w PERC2) + logi driverów
- `judge_wk0.json`, `dym_judge.json`, `describe_wk0.json`, `dym_describe.json`,
  `describe_baza_fantom.json`, `baza_wk0_vs_stock.json`
