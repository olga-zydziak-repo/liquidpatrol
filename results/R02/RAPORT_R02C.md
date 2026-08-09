# RAPORT_R02C — tor C build C-A1: re-atrybucja §3f → AWARIA RENDERU (escape hatch)

Data: 2026-08-09. Reżim: build toru C, krok 1 (rider C-A1). **§3f OBALONE.** Kryteria bez zmian; θ_conf nietknięty.

---

## 1. WYNIK C-A1 — §3f („kadrowanie kamery") OBALONE

Rider C-A1 (krok 1 = re-atrybucja): rozszerzono `exec_lib.att()` o pitch/roll; scenariusz `C1` (zawis,
intruz statyczny, detektor żywy, projekcja pełno-attitude + capture klatki + analiza pikseli).

**Pomiar (C1b, poza intruza POTWIERDZONA gz [7,0,11.5] RPY0):**
- pitch zawisu **mean 0.61°, abs_max 1.46°** (≪ 26–30° potrzebne do klipu przy V-FOV 83°); yaw **0.15°**
  (dron patrzy na intruza); proj_cx **0.5** (centrum); frames_in_fov **1.0** → cel geometrycznie w kadrze.
- Klatka = **jednolite niebo** (górna połowa 218, rozrzut 0, ZERO pikseli intruza); detector_conf **0.018**.

**§3f („intruz klipowany pitchem kadru", iteracja 6) — NIEDOWIEDZIONE i OBALONE.** Pitch jest ~0, cel
wycelowany i w FOV, a mimo to NIEOBECNY w obrazie. To **AWARIA RENDERU**, nie kadrowanie/aiming/detektor.
**Gimbal (dźwignia 0a/0b) NIEPOTRZEBNY.**

## 2. MECHANIZM + MINIMALNA PARA REPRO (rider 1)

Instrument: `run_gate_r02.sh` param `INTRUDER_SPAWN`/`SKIP_SETPOSE`/`SPAWN_SDF`; scenariusz `C1`. 7 lotów.

**PARA REPRO — jedna zmienna (wysokość kamery):**
| kamera | intruz 7 m | render |
|---|---|---|
| **NAZIEMNA** (~0.3 m, sonda static) | ten sam `intruder_model.sdf` | **RENDERUJE** — `static.png`: rozpoznawalny quadek, cy 0.36, 25 px, conf **0.154** |
| **POWIETRZNA** (~9 m, bramka) | ten sam model | **NIE renderuje** — jednolite niebo 218, 0 px, conf ~0.02 |

**WYKLUCZENIA (wszystkie zmienne KONFIGURACJI modelu — żadna nie jest przyczyną):**
| zmienna | test | wynik airborne |
|---|---|---|
| set_pose | spawn WPROST w (7,0,11.5) bez set_pose | nie renderuje |
| static-flag | `intruder_phys.sdf` (non-static + inercja + kolizja) | nie renderuje |
| wysokość intruza | z=7 (poniżej drona) | nie renderuje |
| spawn-method | `intruder_world` w PLIKU ŚWIATA (present-at-init) | nie renderuje |

**Kontrola:** dron (śmigła, present-at-init) I ground_plane **RENDERUJĄ** airborne → sensor kamery działa,
ale **nie renderuje modelu mesh intruza na dystansie dla PODNIESIONEGO sensora**.

**MECHANIZM (nazwany):** gz-sim — podniesiony/powietrzny sensor kamery nie renderuje modelu-intruza
(mesh `x500_base`) na dystansie ~7 m, choć renderuje model-nosiciel (dron) i statyczny grunt. Niezależne
od spawn-method, static-flag, wysokości intruza, typu modelu. **Klasa: SILNIKOWA (gz-sim rendering), nie
konfiguracja modelu** → rider 5 (escape hatch): **STOP z ustaleniami+opcjami**, bez brnięcia w internals gz.

## 3. RETRO-AUDYT skażonych liczb (rider 3)

Skażenie = pomiar wymagał **wyrenderowanego intruza w locie** (którego NIE było — kamera powietrzna).

**UNIEWAŻNIONE (do powtórzenia po fixie renderu):**
| pomiar | dlaczego skażony |
|---|---|
| **G2a/G2b live** (conf 0.045–0.047, n_entry=0, „porażka detekcji") | boxy = szum; cel NIE istniał w kadrze — nie porażka detekcji, lecz brak renderu |
| **§3f / §1a atrybucja** („kadrowanie / tło gruntu zabija detekcję", iteracja 6) | artefakt braku renderu, NIE tło/pitch |
| **§3d migotanie conf ~θ_conf** (rider 1 iter.4, statyczny) | statyczny renderował — ale interpretacja „koperta detekcji w locie" skażona |
| **CHAR2 sygnał w locie** | intruz nie renderowany w locie |
| **R4 baseline sygnału w locie** (0.045–0.081) | j.w. |
| **koperta A7 „zasięg detekcji w locie"** | nigdy nie mierzona z wyrenderowanym celem w locie |

**WAŻNE (nie wymagały renderu intruza w locie — pozostają):**
| pomiar | dlaczego ważny |
|---|---|
| **chmura szumu w locie + ε_FP=0** (G1, G1-A6) | pusta scena — intruz niepotrzebny |
| **sweep statyczny** (conf 0.169–0.214 @5–9 m) | kamera NAZIEMNA renderowała (static.png) — ważny jako statyczny (nie jako próg lotu) |
| **cała teza GT-fed** (G2/G3/G4/G5 + nieregularność, certy, dead-man, G5 warstwa-0, R3 stalle) | omija detektor/kamerę — niezależna od renderu |
| **B0 detektor** (latencja/VRAM), R1-A **static** mini-sanity (conf 0.177 naziemnie) | pomiary naziemne/latencyjne |

## 4. SCENE-SANITY GUARD (rider 2) — trwała bariera, WDROŻONA

`scene_sanity_intruder()` + `Runner.preflight_scene_sanity()`: na starcie scenariusza LIVE projektuje pozę
intruza (pełne attitude) → jeśli w FOV, asercja niezerowych ciemnych pikseli w regionie. **Regresja renderu
(intruz w STANIE, brak w OBRAZIE) = GUARD_FAIL, nie wynik detekcji.** Twarda bariera (live enforce; GT-fed
pomija; `SCENE_SANITY=off` = świadoma zgoda). Wpięta w G2. Unit-test (bez SITL): airborne pusta → FAIL,
ground static → PASS. Wzorzec certs_selfcheck: ten błąd nigdy więcej nie przejdzie jako wynik detekcji.

## 5. OPCJE (escape hatch, rider 5) — do decyzji Olgi

Mechanizm silnikowy → nie brnę w internals. Opcje na następną sesję/cykl:

- **O1 — silnik renderu:** przełącz gz `ogre2`↔`ogre` / sprawdź wersję gz-sim 8.x (znane błędy sensor-render
  dla dodawanych/przemieszczanych modeli); test scene-sanity guard jako kryterium. Ryzyko: patch/wersja.
- **O2 — `<scene>`/sensor SDF:** parametry renderu (shadows, sky, visibility_mask, `<render_engine>`) w świecie
  / sensorze — TANIE do przetestowania (config, nie silnik), jeśli któryś przywraca render airborne.
- **O3 — obejście przez pozycję:** jeśli render działa tylko blisko origin/nisko — przeprojektuj geometrię
  bramki (kamera+intruz nisko, zachowując elewację ~12°) — ale to zmienia kopertę A7 (koszt: re-freeze).
- **O4 — zaakceptuj GT-fed jako tryb walidacji tezy** (już PASS), a live-fed detection uplift ZAWIEŚ do
  naprawy renderu symulatora (osobny recon fidelity). Tor C (detekcja) przedwczesny póki harness niewierny.

**Rekomendacja:** najpierw **O2** (tanie, config) → jeśli nie domyka, **O1** (silnik) w budżecie 1 sesji;
równolegle **O4** jako stan bazowy (teza obroniona GT-fed, guard chroni przed regresją). Dźwignie 0/2/R2-alt
pozostają ZAWIESZONE (celowały w nie-problem). θ_conf i kryterium dwustronne bez zmian.

## 6. STOP

Escape hatch uruchomiony (mechanizm silnikowy). Ustalenia + para repro + retro-audyt + guard dostarczone;
opcje O1–O4 do decyzji. Commity `12d74dd` (mechanizm), `407b1ee` (guard). Push = Olga. PRE_R02C-rev1: §7.
