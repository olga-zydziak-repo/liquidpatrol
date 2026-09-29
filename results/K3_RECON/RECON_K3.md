# RECON_K3 — kontrola architektury (liquid vs rekurencja vs okno) + sonda STOCK: rozpoznanie

LiquidPatrol · CC · 29.09.2026 · PROMPT_K3_S0 · sesja WYŁĄCZNIE rozpoznawcza (zero treningu,
zero bootów, zero zmian w plikach istniejących; jedyne nowe pliki = ten raport + tools/).
STOP-K3R po tym raporcie; PRE_K3 pisze CC, ratyfikuje Olga.

## §0. Bramka wejścia i FROZEN (wykonaniem)
- origin/master = `0480e01` (domknięcie dema: ANEKS_DEMO3-2 C1–C3 + ANEKS_DEMO3-3 SHORT
  w RAPORT_DEMO_V3, rc1 zachowany) — push Olgi potwierdzony; ahead pusty; porcelain pusty.
- **Piny 5/5**: `k1_shield_pins.check_shield_frozen()` → True (shield.py `1c584964…`,
  r03/config.py `4c440e42…`, gate_run_r03.py `5647ae20…`, base.py `7fc45cf2…`,
  safe_descend.py `e3c1040b…` — want==got 5/5).
- **Certy 9/9**: `python3 -m r01.proofs.certs_selfcheck` → „WERDYKT: PASS (9/9 zgodne)".
- **Sha 4/4**: bench_judge.py `8ec0fcfb` · features.py `9adc1505` · ncp.npz `0337d5ea` ·
  mlp.npz `1d190023` — zgodne z brzmieniem promptu.

## R2.1 Tor treningu NCP-20
- **Pliki**: `net/train.py` (wejście: `python -m net.train ncp|mlp`; Adam ręczny + MSE,
  numpy-only — zero torch/jax), `net/models.py` (architektury), `net/dataset.py` (loader),
  `net/d0_dataset.py` (inwentarz + podział), `net/train_config.json` (hiperparametry
  ZAMROŻONE w N-B1, nagłówek pliku).
- **Zbiór**: WYŁĄCZNIE 114 udanych demonstracji D6 = pierwsza WAŻNA (V2′) próba per
  scenariusz (`net/dataset.py:1-8`); **114 = 44 (blok1) + 70 (blok2)** — policzone
  wykonaniem `resolve_first_valid()` (blok-listy `d0_dataset.py:18-22`, CAMP =
  `results/BENCH/campaign` — dane W REPO). „44+70" z promptu = podział na bloki lotów
  kampanii ławki, nie train/val.
- **Podział ZASZYTY** (`d0_dataset.py:27-32`, nie-CLI, N2): TEST = seed%4==0 (ziarna 4,8),
  VAL = seed 2, TRAIN = reszta ⇒ epizody D6: **TRAIN 81 · VAL 10 · TEST 23**.
- **Cechy**: `from bench.features import features` — **IMPORT, nigdy kopia** (SR-2,
  `net/dataset.py:23`); te same cechy w locie (`net_controller` używa modelu z zapisanymi
  input_mean/std; standaryzacja ze statystyk TRAIN zapisana w npz — `train.py` docstring).
  Wejście 8 cech, cel = `cmd_v_ned` (3D).
- **Hiperparametry NCP** (`train_config.json`): hidden 20, bb 20, lr 0.003, epochs 1000,
  **seed 1**, grad_clip 5.0, β1/β2 0.9/0.999, lr_schedule milestones [500,800] γ 0.5.
  Selekcja checkpointu WYŁĄCZNIE na VAL. curves.json: 1000 epok train+val (zapisane).
- **Historia strojenia** (uczciwie, do budżetu kontroli w PRE): hiperparametry zamrożone
  PRZED pierwszą epoką (N-B1), z JEDNĄ naprawą przyrządu po fakcie — `_nb3` w configu:
  ANEKS_NET-1 §3.1 cap epok 200→1000 + harmonogram lr („val malał do capu"). Czyli budżet
  strojenia NCP = zamrożony zestaw + 1 korekta klasy „przyrząd" (nie grid-search). Kontrole
  w PRE dostają dokładnie tyle: zamrożony config + prawo do identycznej klasy naprawy.
- **Odtwarzalność**: numpy 1.26.4, brak requirements.txt (ryzyko R-3 niżej); trening
  deterministyczny z ziarna (RandomState(seed)); dane w repo; czas treningu NIEZAPISANY
  (curves bez wall-time) — CPU-bound, patrz R2.8.

## R2.2 mlp.npz 1d190023
- **Architektura** (`net/models.py:31-45` + npz): TinyMLP, okno **k=5**, IN=8 → din=40,
  2×hidden 32 (tanh), głowa 3 (tanh·vmax) — **2467 parametrów** (z npz; +29.6% vs NCP —
  istniejąca kontrola też NIE była param-matched, do odnotowania w PRE).
- **Trening**: ten sam `net/train.py` (gałąź mlp), config: hidden 32, k 5, lr 0.001,
  batch 512, epochs 80, seed 1 (curves: 80 epok).
- **Werdykt poz. 3 (offline) verbatim** (`results/NET/RAPORT_NET_S1.md:24`): „Bramka N3(i):
  9/12 (OBA ziarna) / 12/12 (którekolwiek) / 21/24 epizody — WERDYKT ZALEŻNY OD REGUŁY
  AGREGACJI"; rozstrzygnięcie reguły w ANEKS_NET-1.
- **Czy latał w pętli ławki: TAK** — kampania F2 poz. 4: 12 bootów `f2_mlp_b1..b12`
  (48 epizodów), wynik **8/48 FAIL** (`results/NET/FLY/RAPORT_NET.md:17,47-49`); rozjazd
  offline 21/24 vs lot 8/48 = znalezisko „model punktowy optymistyczny dla MLP".
- **Co wolno mówić** (RAPORT_NET §11): zdanie kanonu o pamięci-przez-okno („…której
  pamięć-przez-okno 0.25 s nie przeżywa (8/48) — przy TYM zadaniu, feedzie i czystej
  imitacji"); ZAKAZ „liquid > MLP w ogólności" — k=5 to jeden punkt przestrzeni okien
  (dokładnie stąd nota kontroli GRU, ANEKS_NET-4 §3). ⇒ **MLP-k20 = NOWY trening** tym samym
  torem (nowa klasa okna), nie rozszerzenie mlp.npz.

## R2.3 Interfejs kontrolera ławki
- **Wartości CONTROLLER= z kodu** (`r03/controllers/__init__.py:18-20`): `"route"` →
  RouteFollower · `"orbit"` → OrbitExecutor · `"net"` → NetController. Fabryka
  `make_controller(name, **kw)` `:24-28`; docstring `:7`: „Rejestr rozszerza ławka/sieć
  DOPISANIEM klasy — bez dotykania osłony/pętli (SR-9)". Pętla ławki woła fabrykę
  z `params=exec_params, orbit_dir=…, vmax=…` (`bench/bench_flight.py:201,306`).
- **Ramię sieciowe** (`r03/controllers/net_controller.py`): wybór wag przez env
  `NET_ARM=ncp|mlp` (`:52-54`), wagi `net/frozen/<arm>.npz` (`:55`), **guard tożsamości:
  sha256 pliku wag vs `FREEZE_SHA` (`:29-33`), rozjazd ⇒ RuntimeError „ODMOWA LOTU (SR-2)"
  (`:59-61`)**. Kontrakt: `set_feed(fs)` + `step(tick, own, vel, now_sim, …)` → dict
  z `v_ned`/`tgt_ned`/`extra.phase` (wzór wywołania `bench_flight.py:349-352`); stan
  wewnętrzny resetowany per epizod (`reset()`: h=0 dla ncp, okno zer dla mlp `:69-75`).
- **Co DODAĆ dla GRU/MLP-k20 bez dotykania frozen**: (a) klasy modeli — NOWY plik (np.
  `net/models_k3.py`: GRU21, MLPk20) — `net/models.py` bez zmian; (b) NOWY kontroler-plik
  (np. `r03/controllers/k3_controller.py` z własnym FREEZE_SHA_K3) albo rozszerzenie
  net_controller — **rekomendacja: nowy plik** (net_controller.py to przyrząd zamkniętej
  nogi NET; nie jest pinowany, ale kanon NET cytuje jego guard — nie dotykamy); (c) DOPISKA
  dwóch wpisów do rejestru `__init__.py:18-20` (np. `"gru"`, `"mlpk20"`) — plik NIE jest
  pinowany i jest do tego zaprojektowany (SR-9); to jedyna edycja istniejącego pliku,
  addytywna, do jawnej ratyfikacji w PRE; (d) trening: gałęzie `gru|mlpk20` w NOWYM
  wrapperze treningu (import z net/train.py albo kopia toru — patrz ryzyko R-2).
- Piny osłony NIE obejmują żadnego z powyższych (SHIELD_PINS = shield/config/gate/base/
  safe_descend — `k1/k1_shield_pins.py:18-33`).

## R2.4 Budżet parametrów (skrypt: `results/K3_RECON/tools/count_params.py`, uruchomiony)
| model | parametry | vs NCP |
|-------|-----------|--------|
| **ncp.npz (NCP20)** | **1903** | — |
| mlp.npz (TinyMLP k=5, h=32) | 2467 | +29.6% (istniejąca kontrola poza budżetem 5%) |
| **GRU h=21** (p=3h²+30h+3; 1 bias/gate, konwencja repo) | **1956** | **+2.8% ✓** |
| GRU h=20 / h=22 | 1803 / 2115 | −5.3% / +11.0% (poza) |
| **MLP k=20, h=11** (p=h²+165h+3, din=160, 2×hidden jak TinyMLP) | **1939** | **+1.9% ✓** |
| MLP k=20, h=10 / h=12 | 1753 / 2127 | −7.9% / +11.8% (poza) |
| (wariant: MLP k=20 h=14 = 2509, +1.7% vs mlp.npz — gdyby PRE matchował do STAREJ kontroli) |
Kandydaci spełniający |Δ|≤5% wobec NCP: **GRU h=21 (1956)** i **MLP-k20 h=11 (1939)**.

## R2.5 Siatka i kosztorys (z manifestów, nie z pamięci)
- Siatka F2 nogi NET: **48 epizodów per ramię** = 12 bootów × 4 epizody/boot
  (`results/NET/FLY/f2_{ncp,mlp}_b1..b12/manifest.json`: 24× `"n_episodes": 4`);
  parowanie per scenariusz, przeplot ramion per boot (sekwencja f2_* naprzemienna);
  do tego 2 booty diag `boot0m`/`boot0n` i 9 bootów f3 (świeże ziarna, poza siatką
  kryterialną). Ponowienia w F2: 0 (brak sufiksów r).
- **Kosztorys K3**: 2 nowe ramiona × 12 bootów = **24 kryterialne** + **2 diag boot-0**
  (wzór boot0m/n — smoke nowych kontrolerów przed siatką) + **sonda STOCK 1–2** + zapas
  ponowień 2 (F2 miało 0, BENCH miało 2) ⇒ **28–30 bootów**. Czas: boot 4-epizodowy
  ~10–12 min + cooldown 300 s ≈ 16 min/boot ⇒ sama siatka ~6.5 h, całość **~8 h czystego
  lotu** ⇒ **2 sesje lotne realnie, 3 z zapasem; 1 sesja NIEREALNA.** Wstępna „~24 booty /
  1–2 sesje" z promptu: liczba bootów zaniżona o diag+sondę+zapas (24→28–30), dolna liczba
  sesji (1) odpada.

## R2.6 Sędziowie
`bench/bench_judge.py` i `bench/features.py`: **zero** wystąpień controller/arm/NET_ARM
(grep pusty) — sędzia sądzi geometrię GT/RTF, cechy liczą się z demo-wierszy niezależnie od
ramienia. **Żadna zmiana sędziów nie jest potrzebna** dla nowych ramion. (Jedyne odniesienie
do ramienia w torze danych: `demo.jsonl.controller` — pole opisowe manifestu, nie sędzia.)

## R2.7 Sonda STOCK (mechanizm z dowodem)
- Mechanizm wiatro-czułości drona w nodze W: **prepend** `tools/w_launcher.sh:42`:
  `export GZ_SIM_RESOURCE_PATH="$ROOT/worlds/wind_models${GZ_SIM_RESOURCE_PATH:+:…}"` —
  kopia `worlds/wind_models/x500_base/model.sdf` (enable_wind, sha `13c9174d` w FREEZE_W)
  PRZESŁANIA stockowy `PX4-Autopilot/Tools/simulation/gz/models/x500_base` (istnieje,
  sprawdzone ls). Nikt inny w torze bootów nie ustawia GZ_SIM_RESOURCE_PATH (grep po repo:
  tylko w_launcher + generatory światów + stare recony).
- **Bieg „world_wind_s0 + stock"**: ten sam `world_wind_s0.sdf` BAJT-W-BAJT (lot legalny,
  plik nietykalny — FREEZE_W), FLIGHT=bench, c11, ziarna kampanii W, CONTROLLER=net,
  W_ARM_ALWAYS=1, **bez prependu wind_models**. Przeszkoda: prepend w w_launcher jest
  BEZWARUNKOWY, a w_launcher jest FROZEN ⇒ sondy NIE da się poprowadzić przez w_launcher
  bez modyfikacji. **Rozwiązanie do PRE: NOWY plik-launcher** (np.
  `results/K3_RECON/tools/… → tools/k3_launcher.sh` w S1) = w_launcher minus linia 42
  (lock+pgrep+guard OUTDIR zachowane 1:1), echo GZ_SIM_RESOURCE_PATH do manifestu jako
  dowód „stock". Świat pozostaje byte-identyczny — jedyną zmienną jest model (dokładnie
  wymóg ANEKS_W-2 §3).
- Nota: sonda ma sens porównawczy wobec **kampanii W L0/net** (ta sama komórka c11, ziarna
  s01–s03, ten sam świat s0) — świeże z_max stock vs z_max 12.4–18.5 z modelu enable_wind.

## R2.8 Trening na hoście
- Tor treningu jest **numpy-only** (`net/train.py`: ręczny Adam, `net/models.py`: ręczny
  backprop; import tylko numpy) ⇒ **GPU niepotrzebne i nieużywane**; pytanie o GPU w WSL2
  bezprzedmiotowe dla tego toru. numpy 1.26.4.
- Czas treningu: NIEZAPISANY w artefaktach (curves.json = same krzywe; eval.json bez
  wall-time). Rozmiar problemu: TRAIN 81 epizodów × ~1.4k ticków, NCP 1000 epok BPTT
  w numpy — rząd dziesiątek minut do ~2 h CPU (do zmierzenia w S1; zero treningu teraz).
- **Rozdział trening↔boot**: trening nie dotyka SITL/gz/PX4 (czysty CPU+RAM), ale host
  jeden i proc_gate bootów bramkuje load (CLEAN wymaga load1<1.5) ⇒ polityka do PRE:
  trening WYŁĄCZNIE poza oknami bootów (przed sesją lotną albo po), nigdy równolegle
  z bootem; przed startem serii bootów `pgrep python.*net.train` pusty + loadavg w normie.

## R2.9 Higiena hosta i nazwa
- Dysk: **768 GB wolnego** (po DEMO_V3 z ~11 GB klatek lokalnych) — zapas wielokrotny.
- Procesy: host czysty (pgrep gz/px4/agent pusty na wejściu recon); cooldowny nieaktywne
  (ostatni boot = akt3/take_2 wczoraj-dziś, >300 s temu).
- **Kolizja nazwy „K3": ISTNIEJE, dwuznaczna** — (1) **SR-K3** = stop-rule „sędzia po
  pierwszym biegu nietknięty" (PRE_K1.md:174, ANEKS_SHA, ANEKS_K1-1 — żywa reguła,
  cytowana); (2) **KIERUNKI_SOTA.md:38 „K3 — Wierność sim-to-real"** = INNY kierunek
  katalogu niż ta noga (ta noga = kierunek 1a „kontrola architektury"). Ryzyko pomyłki
  w przyszłych grepach/cytatach realne. **Do decyzji PRE: nazwa nogi** (zostawić K3
  z glosariuszem, albo np. „NETC"/„ARCH" — rekomendacja CC: zmienić, koszt zero przed
  startem, po starcie rośnie).

## §R. Ryzyka dla „identycznego toru" (PRE musi znać przed zamrożeniem)
- **R-1 (parytet budżetu)**: mlp.npz (2467) już jest +29.6% vs NCP — „identyczny budżet"
  nigdy nie obowiązywał starej kontroli; PRE musi zdefiniować, czy kontrole K3 matchują do
  NCP (rekomendacja: tak, ±5% — kandydaci gotowi), i jak o tym mówić przy porównaniach
  z mlp.npz.
- **R-2 (tor treningu a nowe architektury)**: `net/train.py` ma gałęzie ncp|mlp zaszyte
  (model, format batchy: sekwencje vs okna). GRU potrzebuje toru sekwencyjnego (jak ncp),
  MLP-k20 okien k=20 (parametr `windows(split,k)` w dataset.py JEST parametryzowany —
  `dataset.py:11`). „Identyczny tor" = te same dane/podział/strata/Adam/selekcja-VAL/
  budżet epok; wymaga NOWEGO wrappera (import funkcji z net/, zero edycji net/train.py) —
  dosłowna bit-identyczność pętli treningu jest niemożliwa między architekturami i PRE
  powinien zdefiniować „identyczność" jako listę inwariantów (dane, split, MSE, Adam+clip,
  selekcja VAL, cap epok, seed, standaryzacja TRAIN).
- **R-3 (środowisko)**: brak requirements.txt; odtwarzalność wisi na numpy 1.26.4 —
  odnotować wersje w PRE (koszt zero).
- **R-4 (cap epok)**: NCP dostał naprawę przyrządu 200→1000 (ANEKS_NET-1 §3.1). Kontrole
  muszą dostać ten sam cap 1000 + to samo prawo do naprawy klasy „val malał do capu" —
  inaczej asymetria budżetu treningu.
- **R-5 (seed treningu)**: seed=1 wszędzie; PRE: kontrole też seed=1 (żadnych multi-seed
  wyścigów bez symetrii dla NCP).
- **R-6 (sonda a wyłączność)**: sonda STOCK wymaga nowego launchera (R2.7) — plik nowy,
  ale ratyfikacja brzmienia w PRE, żeby nie powtórzyć klasy „fallback niezweryfikowany".

## §S. Status
STOP-K3R. Zero bootów, zero treningu, zero zmian w istniejących plikach (jedyna edycja
przyszłościowa zidentyfikowana jako wymagana: +2 wpisy rejestru kontrolerów — ODŁOŻONA do
PRE/S1). Nowe pliki: ten raport + `tools/count_params.py`. Czeka: **PRE_K3** (numerowany);
sygnały bez numeru odrzucam. Push = Olga.
