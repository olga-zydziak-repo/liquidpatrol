# RECON_WK — recon nogi WIATR-KAMERA (S0): czy NCP-20 prowadzi pełną misję na własnej kamerze w wietrze

CC-wykonawca · 29.10.2026 · PROMPT_WK_S0. **0 bootów** (R6 niewykonany — §R6), zero treningu,
zero kampanii, zero edycji istniejących plików; nowe pliki wyłącznie `results/WK_RECON/**`.

## §0. Bramka

- origin/master == HEAD == **6a980abf** (CO-XAI2); `origin/master..HEAD` pusty; porcelain
  wyłącznie `??` wideo/klatki DEMO_C.
- FROZEN wykonaniem, sha256 zgodne. Prefiksy 8: pin `mono_cam/model.sdf` 3354ae1e (pełny
  zgodny); profil a68a450b; sonda 8df528bb; det_v2 775ead15; percep_proc 38a3a765;
  feed_vision_proc 79633489; feed_registry ee1481f9; det_labels 8f7430cd; det_replay de0feb37;
  sędzia 8ec0fcfb; bench 05137098; ncp 0337d5ea; net_controller e8c1b658; fantom_scan e435ed7e;
  rejestr 87203d29; akw_scan b94cdeae. FREEZE_W: w_judge e68040ae, w_launcher 28df8928,
  światy s0/s1p5/s3/s4p5 921bdda7/b8380e8a/73214a2d/cf9df7b8,
  `worlds/wind_models/x500_base/model.sdf` 13c9174d. Piny osłony 5/5 (`k1/k1_shield_pins.py`:
  SHIELD FROZEN True). Certy 9/9 (`r01.proofs.certs_selfcheck`: PASS). `harness/world_hash.sh`
  zgodny z HEAD.

## §R1. KOMPOZYCJA — werdykt: **WYKONALNE bez edycji zamrożonych** (wyłącznie nowe pliki)

**(a) Jak wiatr wchodzi do symulacji w nodze W (litera):**
- Świat: `gz-sim-wind-effects-system` + `<wind><linear_velocity>` w SDF świata
  (`worlds/world_wind_s3.sdf:21-26`). Generator dokłada też 13 systemów z server.config,
  bo gdy świat deklaruje jakikolwiek `<plugin>`, gz ignoruje server.config
  (`worlds/gen_world_wind.py:20-22,38-52`).
- Dron: kopia **bazowego `x500_base`**, nie mono_cam. `worlds/wind_models/x500_base/model.sdf:21`
  to jedyny diff względem stocku, czyli `<enable_wind>true</enable_wind>` na `base_link`.
  Rozwiązywana jest prependem `GZ_SIM_RESOURCE_PATH` (`tools/w_launcher.sh:42`).
- Łańcuch include: stock `x500_mono_cam/model.sdf` → `<uri>x500</uri>` + `model://mono_cam`.
  Stock `x500/model.sdf` → `model://x500_base`. Kopia podmienia więc tylko x500_base.
  **Pin `mono_cam/model.sdf` 3354ae1e pozostaje nietknięty.**
- `harness/run_boot.sh:102` startuje ZAWSZE `MODEL=gz_x500_mono_cam`, więc kampania W latała
  już dronem z kamerą. Kamera nie karmiła kontrolera: feed był emulowany, feed_sha da9ef2f4.

**(b) Konfiguracja misji kamerowej w reżimie OPS (litera):**
- `results/PERC2/tools/perc2_s2_boot.sh:26` ma `WORLD=world_demo_A3`
  (habitat percepcyjny FROZEN, sha adc91803).
- `:81` ustawia `CONTROLLER=net_fantom` (rejestr `r03/controllers/__init__.py:30`, FantomScan
  e435ed7e → AkwScan b94cdeae → NetController e8c1b658), `NET_ARM=ncp`, `FEED=V2`, `INTRUDER=1`.
- `:99-106` uruchamia most obrazu i `harness/percep_proc.py --world $WORLD` z profilem FastDDS
  a68a450b. `:110` puszcza sondę kadencji 8df528bb PRZED uzbrojeniem.
- `:51-55` pinuje model.sdf.
- DEMO-C ma ten sam reżim (`results/DEMO_C/tools/democ_v3_boot.sh:20,57-59`).

**(c) Minimalne złożenie (nowe pliki):**
1. **Światy `world_wk_{s0,s1p5,s3}`** = A3 + ten sam blok 13 systemów + WindEffects + `<wind>`.
   Wygenerowane w tym reconie do `results/WK_RECON/worlds/`
   (`tools/wk_gen_world.py`, blok systemów importowany READ-ONLY z gen_world_wind).
   - Diff względem A3 to WYŁĄCZNIE linia `<world name>` oraz wstawiony blok plugin+wind.
     Teren, tekstury i grunt są bajt-identyczne, więc habitat percepcyjny jest zachowany.
   - `gz sdf --check`: Valid ×3.
   - sha256: s0 4c179a14, s1p5 9713a8b1, s3 3a605ca3.
   - Blok systemów = `server.config` verbatim
     (`PX4-Autopilot/src/modules/simulation/gz_bridge/server.config`), więc renderowanie
     pracuje na tym samym stosie.
2. **Model z wiatrem:** ponowne użycie zamrożonej kopii FREEZE_W 13c9174d (READ-ONLY, przez
   prepend `GZ_SIM_RESOURCE_PATH`). Lokalnie **brakuje binariów** (`meshes/` itd.,
   gitignorowane: `worlds/wind_models/.gitignore:3`). Regeneracja kopią ze stocku według
   README (`cp -rn …`) tworzy nieśledzone pliki, nie edytuje zamrożonych.
3. **Driver bootu:** NOWY plik, kopia `perc2_s2_boot.sh`, w której zmieniają się tylko:
   `WORLD=world_wk_*`, prepend `GZ_SIM_RESOURCE_PATH`, pin x500_base 13c9174d obok pinu
   mono_cam, sha świata WK w manifeście.
   - `percep_proc --world` i topik `MONO` niosą nazwę świata (`perc2_s2_boot.sh:27,105`);
     to parametr drivera, nie edycja.

**Zamrożone artefakty, które by się ZMIENIŁY: ŻADEN.** Piny zachowane. Pod przyszły FREEZE_WK
przypiąć: x500_base 13c9174d (pin W, teraz także w lidze kamerowej), światy WK ×3 oraz sha
nowego drivera.

**Jedyna kolizja zakresu:** `harness/world_hash.sh:11-22` (FROZEN; wołany przez run_boot.sh:98)
szuka świata WYŁĄCZNIE w `worlds/<W>.sdf` albo w stocku PX4 (i kopiuje go do PX4). Lot
w świecie WK wymaga więc nowego pliku w `worlds/`. Dla nogi to nowy plik, więc **punkt
odroczenia NIE zachodzi**. Dla tego reconu to plik poza `results/WK_RECON/**`, stąd R6 = 0
bootów (§R6). Obejście przez katalog stocku PX4 dałoby w manifeście `stock:` i fałszywą
prowieniencję, więc odrzucone.

Intruz nie dostaje wiatru: `r02/intruder_model.sdf` nie ma `enable_wind`, a ruch jest
kinematyczny przez `set_pose` (`harness/intruder_motion.py:4`).

## §R2. PEŁZANIE WYSOKOŚCI — werdykt: **pełzanie WYŁĄCZNIE w habitacie wiatrowym; na modelu stock go nie ma**

Narzędzie `tools/wk_r2_creep.py` → `r2_episodes.json`: 560 epizodów ze 164 bootów, ticki
aktywne cmd_v_ned ≠ 0.

| klasa | n | alt_max max | n z alt_max > 15 m | nachylenie alt(t) p50 |
|---|---|---|---|---|
| W, wiatrowy, NCP (L0/L1.5/L3) | 8 | **19.78** | **4/8** | 0.029 m/s |
| W, wiatrowy, egzekutor | 9 | 12.15 | 0/9 | 0.007 |
| stock, NCP, feed emulowany (LIQ/NET/DET-B/AKW-B/FANTOM-B/DEMO-C akt3) | 285 | 14.38 | 0/285 | 0.006 |
| stock, NCP, kamera V2 (DET S4/AKW S3/FANTOM S2/PERC2 S2/DEMO-C) | 157 | 15.21 | 1/157 | 0.008 |
| stock, NCP, wyłącznie c11 (emul + V2) | 37 | 13.57 | 0/37 | 0.012 |

Fisher jednostronny (4/8 vs 1/442 epizodów > 15 m): p = 2.1·10⁻⁷.

**Para kontrolna = nota-trigger ANEKS_W-2 §3, rozstrzygnięta za 0 bootów.**
- LIQ (ramię `net`, NCP) i kampania W mają **identyczny** harness 3a52e19f, kontroler
  e8c1b658, parametry egzekutora 5a724499 i feed da9ef2f4.
- Fizyka światów v1 (baza W) i A3 jest identyczna (diff bloku `<physics>` pusty).
- Różnice, które zostają: kopia modelu z `enable_wind`, wysokość startu (W alt0 8.4–10.1 m wobec
  10.0 m) i flaga `W_ARM_ALWAYS`, która dotyka wyłącznie uzbrojenia osłony.
- LIQ NCP: 48 epizodów, alt_max ≤ 13.8 m. W L0 (wiatr 0): alt_max 18.45 / 14.43 / 15.68 m.

**Zdanie dopuszczalne:** „pełzanie NCP jest własnością PARY sieć × habitat wiatrowy
(enable_wind), a nie sieci na modelu stock". Kwalifikator: wysokość startu nierozdzielona.
Egzekutor w tym samym habitacie nie pełza.

**Ryzyko dla nogi złożonej:**
- Czas dojścia do V_E = 20 m (`r01/config.py:31`) przy zmierzonym tempie wynosi 77 s
  (L3 s02, faktyczny GEOFENCE po 68 s) i 87 s (L0 s01). Pozostałe 6/8 epizodów W potrzebują
  264–872 s.
- Okno aktywne epizodu to ~72 s (T_orb 70 s), więc 2/8 epizodów W dochodzi w nim do obwiedni.
- Oczekiwanie dla nogi w habitacie wiatrowym: **~1–2/8 epizodów kończy się sejwem osłony
  (GEOFENCE) zamiast misją**, także na poziomie 0.

## §R3. PRZECHYŁ × KAMERA — werdykt: **przechył do 3 m/s nie wyrzuca celu z kadru; wyrzuca go pełzanie**

**Litera:**
- Rzut ramki na NED używa **pełnej orientacji** (kwaternion FRD→NED; `harness/feed_vision.py:74-78`).
  W percep_proc to rdzeń FeedVision z `push_own(…, q)` (`harness/percep_proc.py:93-129`).
- Para klatka↔stan to „ostatni stan pokładowy" (`feed_vision.py:152,193`). Rozjazd czasowy nie
  jest zmierzony.
- Głębia Z = f·W/w_px (`feed_vision.py:65`) nie zależy od przechyłu.
- Błąd pozycji od przechyłu przy rzucie samym yaw nie dotyczy, bo rzut nie jest samym yaw.
- Kamera: hfov 1.74 rad, 640×480, 15 Hz (`mono_cam/model.sdf:53-64`), oś pozioma
  (pitch 0 w `x500_mono_cam/model.sdf`); fy = 270 (`r02/mti.py:18`).
- Pół-kąt pionowy wynosi **41.6°**. Po odjęciu marginesu MTI 10 px (`r02/mti.py:33,113-116`)
  zostaje **40.4°**.

**Pomiar przy biurku (`tools/wk_r3_view.py` → `r3_view.json`):**
- Metoda: GT intruza rzutowany na kadr przy zapisanej orientacji z ulogu. Most czasu
  ulog↔t_sim sprawdzony per boot: mediana |Δz| ≤ 0.0012 m.
- **Zastrzeżenie kursu:** kampania W latała harnessem 3a52e19f SPRZED naprawy N1
  (jednostki yaw rad→deg, 5af1e542 05.10). Jej kurs nie jest kursem trybu kamerowego:
  surowa frakcja w kadrze to 0–38%.
- Dlatego **synteza kursu**: wektor ciągu z ulogu zachowany, kurs obrócony na cel.
  Walidacja na lotach kamerowych daje synteza = oryginał (1.0/1.0; 0.988/0.993; 1.0/1.0 ×3).

| W, epizod | przechył p50/p95 [°] | alt p95 [m] | w kadrze (synteza) | poza kadrem |
|---|---|---|---|---|
| L0 net s01 / s02 / s03 | 7.8–9.3 / ~13.7 | 18.3 / 14.3 / 15.3 | **0.889** / 1.000 / **0.953** | dołem 11.1% / 0 / 4.7% |
| L1.5 net s01–s03 | 8.7–11.6 / ~20.6 | 13.5 / 16.4 / 12.4 | 1.000 / 0.994 / 1.000 | dołem ≤ 0.6% |
| L3 net s01 / s02 | 16.1 / 21.4, p95 ~27 | 13.1 / 19.3 | 1.000 / **0.921** | dołem 0 / 7.9% |
| egzekutor, 8 epizodów L0–L3 | 10–21 / 16–29 | 12.0–12.2 | 1.000 (L3 s02 0.972) | ≤ 2.8% |
| baza stock, kamera (PERC2 S2 ×2, FANTOM ×3) | 3.3–4.1 / 9–12 | 12.7–13.2 | 0.993–1.000 | — |

- **Straty kadru występują wyłącznie w epizodach z pełzaniem** (alt p95 ≥ 15 m) i zawsze dołem.
- Przy 3 m/s bez pełzania (net L3 s01, alt p95 13.1 m, przechył p95 27.9°) cel jest w kadrze
  w 100% ticków.
- Przechył od samego habitatu: przy wietrze 0 wynosi ~9° (W L0), a w stocku ~4° (LIQ, ta sama
  epoka harnessu). Opór aerodynamiczny przy `enable_wind` działa już przy wektorze 0.

**Wrażliwość MTI/derotacji** (`tools/wk_r3_rate.py` → `r3_rate.json`):
- Mierzone tempo obrotu kadłuba |ω| w oknach aktywnych.
- W wynosi **23–26 / 55–68°/s (p50/p95), płasko na poziomach 0/1.5/3**, tak samo jak LIQ
  stock z tej samej epoki (22 / 58°/s).
- Loty kamerowe po N1 mają 11–14 / 24–33°/s.
- **Tempo obrotu wyznacza epoka harnessu (zachowanie yaw), nie wiatr.** Na danych W nie da się
  przypisać wiatrowi wzrostu obciążenia derotacji. Rezyduum derotacji pod wiatrem w trybie
  kamerowym jest NIEZMIERZONE; mierzy je dopiero lot.

## §R4. BAZA ODNIESIENIA

- **Kamera bez wiatru w reżimie OPS:**
  - PERC2 S2 (8 epizodów; c08 2/4, c10 1/1, c11 0/3).
  - DEMO-C (5 epizodów, wszystkie PASS; dwa nie należą do siatki: w00a, m01).
  - Zastrzeżenie (z R2/R3): to **inny habitat**. Bez `enable_wind` przechył to ~4° zamiast ~9°,
    pełzania brak, a próbka nie pokrywa komórek v ≤ 0.5. **Jako baza nogi wiatrowej się nie
    nadaje.**
- **Efekt samego habitatu na misję** (para LIQ ↔ W L0, identyczny harness, feed emulowany,
  komórka c11):
  - NCP: stock 3/4 D6 (LIQ r3/r9/r12 PASS, r6 d_min 1.26 FAIL), wiatrowy przy 0 m/s **0/3**
    (sweep 368–515° < 630°).
  - Egzekutor: stock 120/120 (ERRATUM_DMIN), wiatrowy przy 0 m/s **0/3** (b_frac 0.70–0.82).
  - ⇒ **Sparowane ramię wiatr 0 w złożonym świecie jest OBOWIĄZKOWE.** Bez niego całą
    degradację przypisze się wiatrowi, choć część daje habitat.
  - Koszt: tyle co jeden poziom (§R5).
- **Oczekiwanie pod wiatrem z feedu emulowanego (W, D6 per poziom):**
  - NCP 0/3, 0/3, 0/2; egzekutor 0/3, 0/3, 0/2. **Nieinformatywne:** c11 to komórka sufitowa,
    a padają oba ramiona już na L0.
  - Ciągłe miary NCP: frac pasma 0.83–0.90 bez trendu; sweep 368–563° bez trendu.
  - **d_min pogarsza się:** L0 5.6–7.0 m, L1.5 1.7/6.7/3.4 m, L3 1.9/6.0 m.
    Egzekutor też schodzi poniżej 4 m od L0.

## §R5. PROJEKT KAMPANII + WYCENA (PROPOZYCJE — rozstrzyga PRE)

**Komórki:**
- **c00–c07** (v ∈ {0, 0.5}, 4 kierunki). Baza kamerowa NCP w tych komórkach: FANTOM S2 V2
  28/29 D6, AKW S3 V2 32/36.
- **Wyłączone i oznaczone jako sufit:** c08–c11 (v = 1.0). Kamera: FANTOM 6/15, AKW 5/16.
  **c11/270° to zmierzony sufit profilu misji** (ANEKS_TRANSIT-1 §2; PERC2 c11 0/3; W c11 0/16
  oba ramiona). Wiatr nie może dostać winy za geometrię.

**Poziomy:** {0 sparowane, 1.5, 3} m/s, jeden stały kierunek +x ENU (wschód), jak W. Orbita
omiata wszystkie kierunki względne.

**Ziarna:** blok 1, s01 (wariant A) albo s01+s02 (wariant B).

**Ramiona:**
- NCP w konfiguracji kamerowej `net_fantom` + FEED=V2 (bez zmian rejestru).
- Nauczyciel jako odniesienie:
  - wycena: `orbit` + FEED emulowany (precedens W) daje dynamiczną referencję habitatu bez
    kamery;
  - `orbit` + FEED=V2 to terytorium nielatane. Egzekutor nie ma skanu ani kwarantanny, więc
    akwizycja byłaby konfundowana. **Nie przesądzam.**

**Ważność i reżim:**
- V2′ ≥ 0.90 (D9).
- Sonda kadencji k = 1 (FREEZE_PERC2_OPS, PASS przed uzbrojeniem).
- Piny: mono_cam 3354ae1e + x500_base 13c9174d + świat WK per poziom.
- Proc_gate, cooldown, REPO-2.

**Twarde STOPy:** breach ⇒ STOP; REFUSE(POS) ⇒ STOP; budżet ⇒ STOP.

**Propozycja protokołu REFUSE(GEOFENCE)** (precedens W, ANEKS_W-2 §2: REFUSE był tam zamrożonym
STOP, s03 nielatane):
- skoro R2 przewiduje ~1–2/8 GEOFENCE z pełzania także na poziomie 0, to **prawdziwy GEOFENCE**
  (estymator zdrowy według kryterium w_judge) = epizod WAŻNY, wynik = sejw osłony
  (D6 FAIL, liczony osobno);
- **fałszywy** (estymator) ⇒ STOP.

**Booty** (4 epizody na boot; rachunek nie zawiera bootu dymnego):

| wariant | NCP-kamera | + nauczyciel emul (opcja) | + dym |
|---|---|---|---|
| A: 8 komórek × 1 ziarno × 3 poziomy = 24 ep. | 6 | +6 | +1–2 |
| B: 8 × 2 ziarna × 3 = 48 ep. | 12 | +12 | +1–2 |

**Propozycje kryterium/śmierci (dla PRE):**
- WK0 (wiatr 0) < 6/8 D6 ⇒ habitat sam łamie misję kamerową. Noga kończy się zdaniem
  o habitacie, nie o wietrze.
- Różnica netto WK0 → WK3 jako miara wiatru.
- Breach 0 jako warunek konieczny.

## §R6. DYM — **NIEWYKONANY, 0 bootów**

- Warunek „po R1 PASS" jest spełniony. Lot w świecie WK wymaga jednak pliku `worlds/world_wk_*.sdf`,
  bo `world_hash.sh` (FROZEN) nie przyjmuje innej lokalizacji, a PROMPT §1 ogranicza nowe pliki
  do `results/WK_RECON/**`.
- Do tego regeneracja binariów modelu wiatrowego (nieśledzone pliki w `worlds/wind_models/`).
- Recon tego nie robi. Dym to **pierwszy krok nogi** (PRE_WK):
  - jeden lot w world_wk_s3, intruz statyczny (c00), oś ładowania `enable_wind`;
  - dryf i przechył z ulogu, sonda k = 1, ≥ 1 admisja, world_hash + oba piny w manifeście;
  - twarde STOPy verbatim.
- Przy biurku zrobione to, co wolno: światy wygenerowane, diff zweryfikowany, `gz sdf --check` Valid.

## §R7. GRANICE + REKOMENDACJA

**Zdanie, które noga mogłaby dać:** „NCP-20 prowadzi pełną misję na własnej kamerze w habitacie
z modelem aerodynamicznym, przy stałym wektorze wiatru 0 / 1.5 / 3 m/s z jednego kierunku, na
komórkach v ≤ 0.5: D6 x/8, y/8, z/8 (sparowane z wiatrem 0), breach 0, sejwy osłony n".

**Czego nie da:**
- porywów ani turbulencji (wektor stały);
- realnego sprzętu;
- komórek v = 1.0 (sufit profilu);
- pomiaru samego wiatru bez ramienia 0 w tym habitacie.

Kanon W obowiązuje: **zakaz „odporny na wiatr"**. Zdanie o pełzaniu wyłącznie w formie z §R2.

**Rekomendacja: GO z wyceną, wariant A (6 bootów NCP + 1–2 dym, opcjonalnie +6 nauczyciela
emul).** Punkt odroczenia nie zachodzi, bo złożenie to wyłącznie nowe pliki.

Ryzyka nazwane przed PRE:
1. Pełzanie w habitacie daje ~1–2/8 sejwów GEOFENCE i straty kadru dołem do ~11% ticków
   w epizodzie pełzającym. Wymaga protokołu GEOFENCE.
2. Sam habitat przy 0 m/s może obniżyć D6. Sparowane WK0 jest obowiązkowe; śmierć według §R5
   jest kandydatem.
3. Rezyduum derotacji pod wiatrem jest niezmierzone (R3); mierzy je dym.

## Artefakty

- `tools/wk_r2_creep.py`, `tools/wk_r3_view.py`, `tools/wk_r3_rate.py`, `tools/wk_gen_world.py`
- `r2_episodes.json` (560 epizodów), `r3_view.json`, `r3_rate.json`
- `worlds/world_wk_s0.sdf`, `worlds/world_wk_s1p5.sdf`, `worlds/world_wk_s3.sdf`
  (wyłącznie w `results/WK_RECON/`)
