# RAPORT_AKW_S1 — STOP-AKW1: build net_akw + testy przedlotowe + smoke bramkowy

Wykonawca · 09.10.2026 · wykonanie PROMPT_AKW_S1 (PRE_AKW ratyfikowany 09.10).
**Werdykt sesji: bramka A <3/3 po powtórce ⇒ STOP-ANEKS (PRE §4: „inżynieria profilu,
nie śmierć"); mechanizm nazwany i zmierzony rozstrzygająco: admisja bramy percepcji
pod rotacją zależy od OBROTU MIĘDZYKLATKOWEGO ω/kadencja — 2.0°/klatkę admituje,
3.96°/klatkę admituje ZERO.** S-BEZP czyste w obu bootach (breach 0, REFUSE 0).

## §0. Bramka wejścia

Wykonana przy ratyfikacji (przed ARCH-1): `git fetch` → HEAD = origin/master =
`21102888` (STOP-AKWR), `origin/master..HEAD` puste, porcelain pełny pusty; piny 5/5
(k1_shield_pins PASS), certy 9/9 (certs_selfcheck PASS), sha PRE §1 przeliczone 9/9
zgodne (bench 05137098/8ec0fcfb · feed_vision acc81df7 · det_v2 775ead15/e801f7d5 ·
percep 38a3a765 · klient 79633489 · rejestr feedów ee1481f9 · ncp 0337d5ea ·
net_controller e8c1b658 bajtowo bez zmian — wrapper go importuje).

**ARCH-1:** `PRE_AKW.md` w korzeniu VERBATIM — commit `b1f77856`, pierwszy sesji.
ODCHYLENIE JAWNE #1: pierwotny commit ARCH-1 zawierał §8 zmieniony o adnotację
ratyfikacji (błąd wykonawcy — edycja ratyfikowanego dokumentu); naprawione
`git commit --amend` do bajtów VERBATIM **przed jakimkolwiek kolejnym commitem
i przed pushem** (historia lokalnie liniowa, nic nie nadpisano na origin).

## §1. Build (commit `50f83cf5`, przed lotami)

- **`r03/controllers/akw_scan.py` (NOWY)** — sha256
  `2237cc7ca10fc696ae4e07214716f0be16c76847422108ab82ba8fcf57cd06dd`.
  `AkwScan(SetpointSource)`, `name="net_akw"`, wewnętrzny `NetController(**kw)`
  (guard SR-2 sha wag nietknięty, biegnie w konstruktorze delegata); `step()` deleguje,
  podmiana WYŁĄCZNIE pola `yaw` przy `extra.phase=="hold"`; ψ_last = ostatnio
  WYEMITOWANY yaw per tick (track: atan2 delegata; skan: rampa); hold → dwell 2.0 s na
  ψ_last → rampa ψ(t)=ψ_last+ω·t_skanu, ω=30°/s ciągła CCW (konwencja kodu: yaw atan2
  ROSNĄCY, jak orbit_executor CCW); rampa wewnętrznie unwrapped, emisja wrap (−π,π];
  `reset()` zeruje stan skanu i ψ_last=0.0. Env `AKW_*` wyłącznie diagnostyczne
  (driver bramkowy ODMAWIA lotu przy ustawionych).
- **`r03/controllers/__init__.py`** — DOKŁADNIE 2 linie additive, sha po wpisie
  `4f58d204630b9cf8db3bfb9a98b480c7c24552c8c7632eee9373c18b7cbd656a`; diff verbatim:

```diff
+from r03.controllers.akw_scan import AkwScan
@@
     "mlp20": LiqMlp20,      # LIQ (PRE_LIQ §7, SR-9): kontrola okna k=20, wagi net/frozen/mlp20.npz
+    "net_akw": AkwScan,     # AKW (PRE_AKW §2, SR-9): skan yaw w hold, delegat NetController (wagi ncp FROZEN)
```

- **Driver `results/AKW/tools/akwS1_boot.sh`** (sha `fcff9b30…`, kopia detS4_boot
  FROZEN-nietkniętego; jedyna zmiana funkcjonalna: `CONTROLLER=net_akw`; jawne dodatki
  niefunkcjonalne: `KIND=akw` [etykieta finalize], guard ODMOWY przy env `AKW_*`,
  blok `akw` w manifeście, ścieżki `results/AKW/camp`). Analiza:
  `akw_analyze.py` (sha `e9b3bdfb…`, kopia detS4_analyze + sędzia pełny t_entry_s
  przez `judge_boot` frozen, telemetria skanu, klasyfikacja ENTRY F1/F2/F3 jak R3,
  yaw-sanity z boot.ulg; zwalidowany na kopii r1_V2 DET w scratchpadzie — odtwarza
  c00 PASS t_entry 4.16 / c01–c03 ślepe co do liczby). **FREEZE_AKW.md** init.

## §2. Testy przedlotowe — `results/AKW/tools/test_pre_akw.py`: 12/12 PASS

1. **Pass-through bajtowy:** replay logów DET r1 — ramię B 5714 tików + demo V2
   3754 tików + **411 ważnych tracków V2 wprost z percep_feed**; per tick phase≠hold
   cmd AkwScan == cmd NetController co do KAŻDEGO pola; na tickach hold różnica
   WYŁĄCZNIE w yaw. 2. **Profil:** rampa 30°/s (tol. 1e−9), dwell 2.0 s, wrap przy ±π
   (pełny obrót 360°), wznowienie od ψ_last (nigdy powrót do 0), reakwizycja ⇒ nowy
   dwell, reset ⇒ ψ_last=0.0. 3. **Rejestr:** `make_controller("net_akw")` działa,
   `controller_sha` = sha akw_scan.py; regresja `make_controller("net")` nietknięta.

**Istniejące pytest: 210 passed, 0 failed** (bench/net/harness/r01/r02/r03/tools +
FV; `r01/brake_test.py` i `r02/test_deadman.py` nie kolekcjonują się gołym pythonem
[rclpy] — stan habitatu sprzed nogi, pod ROS env zbierają 0 testów pytest).

## §3. Smoke bramkowy — booty 2 i 3 (+ launch 1 przerwany)

**ODCHYLENIE JAWNE #2:** launch 1 (smoke) wystartował po ratyfikacji PRE a PRZED
nadejściem PROMPT_AKW_S1; przerwany przeze mnie W TRAKCIE epizodów dla wyrównania
do litery PROMPT (ψ_last=0.0 w reset, nazwy plików, test percep_feed). Zero werdyktu;
artefakty `camp/aborted_launch1_pre_prompt/**` z ABORT_NOTE; host po teardown
proc_gate CLEAN; cooldown przestemplowany. Liczony w budżecie.

Reżim obu bootów: pełne uzbrojenie, GZ_IP, proc_gate SUSTAINED CLEAN 3×30 s,
cooldown ≥300 s, manifesty 1. klasy (controller `net_akw`, controller_sha `2237cc7c…`,
weights ncp `0337d5ea…`, **feed_sha `8015bd12…`**, sha logów percep/klienta),
rc=0 / finalize=0 w obu.

### Boot 2 — `camp/smoke_r1_V2` (smoke właściwy; kadencja 14.71 Hz = 2.04°/klatkę @30°/s)

| epizod | bearing | ważność (V2′∧żywość) | t_first_track [s] | ENTRY t_rel [s] (klasa) | t_entry sędzia [s] | bramka A ≤20 s | stopnie skanu do boxu | d_min [m] | breach/REFUSE |
|---|---|---|---|---|---|---|---|---|---|
| c00_s01 (kontrolny) | 0° | ✓ | 0.072 (lock F2, fantom) | 61.204 (F1_cel) | 63.756 | — (opisowy; **D6 FAIL**) | 1776° (~5 obr.) | 8.631 | 0/0 |
| c01_s01 | 90° | ✓ | 0.0 (lock na starcie) | 7.26 (F1_cel) | **10.024** | **✓** | 158° | 8.312 | 0/0 |
| c02_s01 | 180° | ✓ | 21.232 (ZE SKANU) | 21.184 (F1_cel) | **23.904** | **✗ (o 3.9 s)** | 576° (1.6 obr.) | 8.164 | 0/0 |
| c03_s01 | 270° | ✓ | 12.76 (ZE SKANU) | 12.688 (F1_cel) | **15.46** | **✓** | 321° (0.9 obr.) | 7.932 | 0/0 |

- **A: 2/3** ⇒ JEDNA powtórka z puli (PRE §4). **B: PASS** — kadencja p50 **14.71 Hz**
  (≥8), E2E p95 **0.080 s** (≤0.25; n_e2e 2739). **C: PASS** — breach 0, REFUSE 0/0
  per gałąź.
- Opisowo: oscylacje skan↔ENTRY 0–1 tik hold w 5 s po akwizycji (brak oscylacji
  właściwej); **FP tła 0** — wszystkie ENTRY w epizodach F1_cel (err vs GT 0.88–2.84 m),
  jedyny ENTRY poza oknami @107.78 = **F2** (lock przed epizodem na pozycji staging
  intruza, okno GT puste — dokładnie mechanizm DET-4 §3 / R3 7/7); err_fresh po
  akwizycji na ślepych p50 0.16–0.22 / p95 0.26–0.35 (lepiej niż DET 0.418/0.648);
  sanity profilu z ulog: 28% czasu rotacji w 25–35°/s, 6336° omiecione; z_max 12.9,
  r_max ≤23.5.
- **Mechanizm c00 (kontrolny FAIL, nowy wgląd):** lock przedepizodowy F2 na fantomie
  (−1.0, 6.6 — staging) → track stale, hold od t_rel 0.65 → skan startuje OD ψ_last
  wskazującego fantom; reakwizycja celu statycznego (v_intr=0) zajęła ~5 obrotów mimo
  celu w stożku co obrót — admisja wieloprzebiegowa pod rotacją (ślepa plamka nazwana
  w recon: „transit przez kadr replay nie mierzy"). W DET c00 przechodził, bo nos
  stał na północy i cel po teleporcie wpadał w kadr bez rotacji.

### Boot 3 — `camp/smoke_r1_V2_rep` (powtórka; kadencja 7.58 Hz = 3.96°/klatkę @30°/s)

| epizod | ważność | t_first_track | ENTRY | t_entry | bramka A |
|---|---|---|---|---|---|
| c00_s01 | ✓ | 1.632 | 1.552 (F1_cel) | **4.34** (**D6 PASS**, jak DET) | — |
| c01_s01 | ✓ | 0.0 (lock F2, FEED_EXPIRE) | — | — | ✗ |
| c02_s01 | ✓ | — | — | — | ✗ |
| c03_s01 | ✗ (valid_V2p False: dsim_dwall 0.8835, 2 deep-stalle) | — | — | — | ✗ |

- **A: 0/3.** **B: FAIL literą** — kadencja p50 **7.58 Hz** (<8; wolny mod znanej
  bimodalności narzędziowej ANEKS_DET-1 §2a / RAPORT_DET_S4 §9.1 — ryzyko nazwane
  w tej sesji PRZED lotami); E2E p95 0.084 ✓. **C: PASS** — breach 0, REFUSE 0.
- Percep żył cały boot (1435 klatek, push_frame p50 13.9 ms); profil fizycznie
  wzorcowy (ulog: p50 rotacji **29.9°/s**, 59% czasu rotacji w paśmie 25–35, 4469°).

### Mechanizm rozstrzygający (liczbami, oba booty, epizody ślepe c01–c03)

| boot | kadencja p50 | obrót/klatkę @30°/s | klatki z boxem | admisje fresh | admisja |
|---|---|---|---|---|---|
| 2 | 14.71 Hz | **2.04°** | 1925 | **1823** (gate mti 1799 + window 24) | 94.7% |
| 3 | 7.58 Hz | **3.96°** | 235 | **0** | **0.0%** |

**Brama struktura∧MTI admituje przy ~2°/klatkę i odcina całkowicie przy ~4°/klatkę.**
Zmienna sprawcza = ω·dt (obrót międzyklatkowy), nie samo ω: pasmo R3 „10–25°/s czyste"
mierzyło mieszankę kadencji (10–25°/s @14.7 Hz = 0.7–1.7°/klatkę). Profil ω=30°/s jest
więc kompatybilny WYŁĄCZNIE z szybkim modem kadencji; wolny mod (≈połowa bootów
w DET S4) czyni akwizycję ze skanu niemożliwą. Kierunek inżynierski (decyzja ANEKS,
nie moja): ω=15°/s (wariant awaryjny z recon) daje 1.98°/klatkę w WOLNYM modzie
(=zmierzonemu pasmu pracy), kosztem worst-case czekania 18.2 s (budżet R5.7 vs
sędzia 25 s pozostaje dodatni, bramka smoke 20 s do rozstrzygnięcia w ANEKS).

## §4. Werdykt bramek i rytm

- **A: 2/3 → powtórka → 0/3 ⇒ <3/3 po powtórce ⇒ STOP-ANEKS** (PRE §4 verbatim:
  inżynieria profilu, nie śmierć nogi). KAMPANIA NIEZWOLNIONA (zakaz PROMPT §5
  respektowany — zero lotów poza §3).
- **B: PASS na boocie 2** (14.71 Hz / 0.080 s); **FAIL literą na boocie 3** z przyczyny
  narzędziowej nazwanej przed lotami (bimodalność kadencji; detektor nie jest limitem:
  push_frame p50 13.9 ms).
- **C: PASS 2/2 bootów** — breach 0, REFUSE 0/0 per gałąź (oczekiwanie konstrukcyjne
  trafione); program: breach 0 / REFUSE 0 we wszystkim, co kiedykolwiek poleciało
  uzbrojone — pozostaje prawdą (+2 booty uzbrojone).
- P-AKW-1 (smoke A+B+C za pierwszym bootem, p 0.50) — NIE zaszła (rozliczenie
  w KSIĘDZE przy zamknięciu nogi). P-AKW-2 (zero FP tła) — w smoke TRZYMA SIĘ
  (0 potwierdzonych; F2 ≠ tło). P-AKW-5 (REFUSE 0) — trzyma się.

## §5. Budżet i porcelain

Launches sesji: **3/≤3** (1 przerwany jawnie + smoke + powtórka); booty nogi 3/≤30.
Commity sesji: `b1f77856` (ARCH-1) → `50f83cf5` (build+testy) → ten (smoke+raport).
Porcelain po commicie: pusty (weryfikacja wykonaniem przy STOP). **Push = Olga.**
Czekam na **ANEKS_AKW-1** (werdykt smoke; inżynieria profilu / zwolnienie lub
przeprojektowanie kampanii). STOP.
