RAPORT_W_S2 — STOP-W2: R-NC boot-0 rozbity PRZED lotem (CONTROLLER=route niewykonalny w zamrożonym przyrządzie)
==============================================================================================================
CC · 28.09.2026 · PROMPT_W_S2 · autoryzacja ANEKS_W-1. Raport STOP (nie raport kampanii —
kampania W-B NIE wystartowała; zero epizodów kryterialnych, zero REFUSE, zero breach).

Hashe S1 (ANEKS_W-1 §1, linia pierwsza per prompt §0.1):
`2529c5a0b9060653f311f79793d70bb71ed1111d` [CB] · `d7663100879ea7283ad9bd645ce2d1ba2dd79438` [CW-A].
Commit C-F (FREEZE_W): `c1fb143deabe51344890536d8eb57a30c91df88d` — wykonany i WYPCHNIĘTY.


§0. Stan zastany i bramka wejścia
---------------------------------
Sesja bieżąca (28.09) jest WZNOWIENIEM: poprzednia sesja S2 (20–21.09) wykonała §1 (C-F)
i odpaliła boot-0 R-NC, po czym urwała się na jego crashu bez raportu i bez commitu artefaktów
(katalog `results/W/camp/diag_boot0/` untracked, bez manifestu).

- §0.1: `git fetch` → `git log origin/master..HEAD` PUSTE ⇒ „dalej" (S1 + C-F wypchnięte).
- §0.3 integralność freeze: sha256 wszystkich 11 plików tabeli FREEZE_W §1 przeliczone
  z drzewa roboczego — **11/11 zgodne** (w_judge e68040ae… · tests_w_judge 00886e9f… ·
  w_launcher 28df8928… · w_tilt b22be3d0… · tests_w_arm_always f0b189f5… · bench_flight
  3a52e19f… · s0 921bdda7… · s1p5 b8380e8a… · s3 73214a2d… · s4p5 cf9df7b8… ·
  x500_base/model.sdf 13c9174d…). Przyrząd NIE był cicho zmieniany.
- Zero zmian kodu w tej sesji (S2-A). Zero nowych bootów w tej sesji (STOP §2 niżej
  rozpoznany PRZED jakimkolwiek startem).


§1. Boot-0 R-NC (20.09, sesja poprzednia) — przebieg faktograficzny
-------------------------------------------------------------------
OUTDIR `results/W/camp/diag_boot0/` (przez w_launcher: lock, pgrep czysty, proc_gate CLEAN
loadavg=0.26). Stack wstał normalnie: MicroXRCEAgent OK, PX4 SITL model gz_x500_mono_cam,
world=world_wind_s3 HEADLESS=1, rtf_sampler na /world/world_wind_s3/clock, b4_state
orphans 0/0.

Moduł lotu FLIGHT=bench: **crash przed uzbrojeniem** — `act.log` (verbatim, koniec śladu):

    File ".../bench/bench_flight.py", line 201, in main
      ctrl_sha = controller_sha(make_controller(CONTROLLER, params=exec_params, orbit_dir="CCW", vmax=V_MAX))
    File ".../r03/controllers/__init__.py", line 28, in make_controller
      return cls(**kw)
    TypeError: RouteFollower.__init__() got an unexpected keyword argument 'params'

Skutki: `trace.jsonl` 0 linii, BRAK manifestu, BRAK ulog, zero armu, zero lotu. Nie było
drugiego podejścia (`diag_boot0_r` nie istnieje).


§2. Atrybucja defektu — fakty z kodu (bez interpretacji ponad źródła)
---------------------------------------------------------------------
1. Rejestr `r03/controllers/__init__.py`: `route`→RouteFollower · `orbit`→OrbitExecutor ·
   `net`→NetController.
2. `RouteFollower.__init__(self, wps, vmax, alt, wp_reach_m=1.0)` (route_follower.py:24) —
   kontroler TRASY gate_r03; NIE przyjmuje `params`/`orbit_dir`/`home_ned`.
3. Zamrożony `bench_flight.py` woła fabrykę bezwarunkowo z `params=…, orbit_dir=…`
   (linie 201 i 306) ⇒ `CONTROLLER=route` z FLIGHT=bench crashuje DETERMINISTYCZNIE,
   zawsze, przed armem. To nie jest flake ani habitat.
4. `bench_flight.py:56`: `CONTROLLER = os.environ.get("CONTROLLER", "orbit")` (docstring:
   „CONTROLLER (orbit)"). Gałąź `bench)` run_boot.sh nie nadpisuje env ⇒ crash DOWODZI,
   że poprzednia sesja jawnie ustawiła `CONTROLLER=route` — czyli wykonała ANEKS_W-1 §3
   LITERALNIE (S2-B), zgodnie z literą protokołu.
5. Historia ławki (grep meta w results/K2 + results/NET + results/BENCH): ramię
   deterministyczne ZAWSZE `controller: "orbit"` (OrbitExecutor, controller_sha
   840514361e4ae5e93ddbb0dd31a7dae81832805b90abccc334d84bbd043730d4; 35+ epizodów),
   ramię uczone `"net"`. Wartość `route` z FLIGHT=bench nie poleciała nigdy.
6. PRE_W §2 (ratyfikowane) nazywa ramiona: „**route-executor**, NCP-20". ANEKS_W-1 §3
   literalizuje to jako `CONTROLLER=route`. W przestrzeni nazw przyrzędu ławki egzekutor
   deterministyczny to `orbit`; `route` to inny byt (kontroler trasy r03).

Wniosek: defekt NIE leży w zamrożonym kodzie (przyrząd działa dla orbit/net jak w K2/NET),
lecz w RATYFIKOWANYM PARAMETRZE protokołu (ANEKS_W-1 §3 / PROMPT_W_S2 §2): wartość
`CONTROLLER=route` jest niewykonalna. Klasa erratum nazewniczego („liczba/nazwa bez
pokrycia w przyrządzie"), wykryta na boot-0, przed jakimkolwiek pomiarem kryterialnym.

§2a. Dlaczego STOP, a nie cicha podmiana na `orbit`
- S2-B: „R-NC wykonywana LITERALNIE — żadnego strojenia". Podmiana parametru = odstępstwo
  od litery ratyfikowanej.
- PROMPT §0.3: defekt ujawniony po freeze ⇒ STOP i pytanie — nigdy cicha poprawka.
- Precedens K1 (ANEKS_K1-19 F3a): STOP = pytanie PRZED edycją treści ratyfikowanej.
Intencja PRE_W §2 („route-executor" = egzekutor deterministyczny = `orbit`) jest moim
zdaniem jednoznaczna, ale rozstrzygnięcie należy do ratyfikacji, nie do CC.


§3. Pytania do ratyfikacji (oczekuję ANEKS_W-1a albo rozstrzygnięcia w ANEKS_W-2)
---------------------------------------------------------------------------------
Q1. Czy „route-executor" z PRE_W §2 wykonuje się jako `CONTROLLER=orbit` (OrbitExecutor,
    sha 84051436…, jedyny egzekutor deterministyczny ławki)? Ramię nadal raportowane
    w siatce jako „executor"; `net` bez zmian. [propozycja CC: TAK]
Q2. Budżet ≤27 bootów LOTNYCH (ANEKS_W-1 §4): czy crash boot-0 liczy się do budżetu?
    Zero armu i zero lotu (trace pusty, brak manifestu), ale cykl bootowy env został
    zużyty. [propozycja CC: NIE liczy się jako lotny — analogia diag/env-fail z K1 SR-K5
    „ważność, nie proxy"; odnotowany osobno]
Q3. R-NC „≤2 podejścia" (H2-b, próg wznoszenia): czy próba z 20.09 konsumuje 1. podejście?
    Pomiar wznoszenia w ogóle nie zaszedł (crash przed armem). [propozycja CC: NIE —
    podejścia liczą się od pierwszego startu wykonalnego; po ratyfikacji Q1 boot-0 idzie
    od zera: `diag_boot0_r` jako pierwsze podejście, guard §9 blokuje reuse katalogu
    z manifestem — tu manifestu brak, ale katalog z artefaktami crashu zostaje committed
    jako ślad, więc retry idzie do NOWEGO katalogu `diag_boot0_r`]
Do decyzji: zero bootów przed numerowaną ratyfikacją (sygnały bez numeru odrzucam).


§4. Uzupełnienie danych W-A (PROMPT §0.5 / ANEKS_W-1 §2 — zero relotów)
------------------------------------------------------------------------
Z istniejących artefaktów `results/W/probe/**` (wa_metrics.json: ekf_eph_max;
habitat.json: hover_seg.dsim_dwall, hover_seg.min_rtf) — przeliczone w tej sesji,
zgodne 1:1 z tabelą ANEKS_W-1 §2:

| boot | poziom | eph_max | Δsim/Δwall | min_rtf |
|---------|-----------|--------|--------|--------|
| 1 s0    | 0.0       | 0.1536 | 0.9437 | 0.0146 |
| 2 s1p5  | 1.5       | 0.1535 | 0.9353 | 0.0057 |
| 3 s3    | 3.0       | 0.1524 | 0.9364 | 0.0018 |
| 3b s3   | 3.0 retry | 0.1524 | 0.9581 | 0.0316 |
| 4 s4p5  | 4.5       | 0.1524 | 0.9875 | 0.0091 |

Habitaty W-A 5/5 INVALID (Δsim/Δwall<0.95 na 4/5, głębokie dipy min_rtf) — env-bound,
niebramkujące w W-A (kalibracja); zgodne z ANEKS_W-1 §2.


§5. Budżet i stan siatki
------------------------
Epizody kryterialne wykonane: **0/18**. Booty lotne zużyte w S2: **0** (crash 20.09 bez
lotu — klasyfikacja per Q2). Budżet ANEKS_W-1 §4: pozostaje ≤27 lotnych (przy Q2=NIE).
R-NC nierozstrzygnięta ⇒ skład siatki (18 vs 12) NIEZNANY. Statystyka habitatów kampanii:
brak (zero epizodów).


§6. Higiena repo (REPO-1 / S2-F)
--------------------------------
`git status --porcelain` na wejściu sesji:

    ?? results/W/camp/

Po tej sesji: commit artefaktów crashu boot-0 (`results/W/camp/diag_boot0/`, po ścieżce,
bez ulog — ulog nie powstał) + niniejszy raport ⇒ drzewo czyste. Pliki dotknięte w sesji:
WYŁĄCZNIE `results/W/RAPORT_W_S2.md` (nowy). Lista zamknięta §0.4 dotrzymana. Push = Olga.
