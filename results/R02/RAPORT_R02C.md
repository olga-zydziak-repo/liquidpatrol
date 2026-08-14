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

## 6. O2 SWEEP (decyzja Olgi: O2 + test zerowy; guard jako kryterium)

Wszystkie testy: world-SDF only, kamera POWIETRZNA, `SCENE_SANITY` guard = PASS/FAIL, jedna zmienna.

| test | zmienna | guard airborne |
|---|---|---|
| **rider 0 — cykl życia A** | world-file present-at-init (SKIP_CREATE) | **FAIL** (dark_px=0) |
| rider 0 — B / C | runtime-create / set_pose | FAIL (wcześniej) → **LIFECYCLE OBALONE** |
| **toggle #1** | shadows=off (scene+sun) | **FAIL** (nie shadows) |
| **Lot 1** (wariant 3) | BOX prymityw @ (7,0,11.5) | **FAIL** → NIE mesh-specific |
| **Lot 2** (wariant 3) | BOX nisko @ gz(10,0,2), elew −35° | **FAIL** → NIE wysokość celu |

**MECHANIZM (precyzyjny symptom — do issue-search w trackerze gz-sim):** podniesiony/powietrzny sensor
kamery gz (habitat **WSL2 / D3D12**, ogre2) **nie renderuje MAŁYCH obiektów** (~0.6 m, mesh LUB prymityw
box, dystans ~7–10 m, wysoko LUB nisko), choć renderuje **wielki `ground_plane`** i **bliskie śmigła
drona**; kamera **NAZIEMNA renderuje te same małe obiekty** (`static.png`). **Wykluczone:** model-config
(set_pose / static / typ / mesh-vs-box), cykl życia (world/create/set_pose), wysokość celu, shadows.
**Klasa: SILNIKOWA** (LOD / culling / scene-management dla podniesionego sensora na WSL2-D3D12).

## 7. DECYZJA — O4 (reguła Olgi z góry) + PRE_R02C-rev1

Reguła zamrożona przed lotami: „oba loty FAIL przy renderującym ground_plane → hipoteza rozmiaru/kubatury,
koniec zgadywania → **O4 baza GT-fed, engine jako osobny recon** z issue-search po pełnym symptomie".
Ziściła się. **DECYZJA: O4.**
- **Tor C detekcji ZAMKNIĘTY na bazie GT-fed** — teza osłona+OBSERVE obroniona (`RAPORT_R02.md`), certy 5/5,
  dead-man, G5 warstwa-0 — **nie zależą od renderu kamery**. **Scene-sanity guard** chroni przed regresją
  (żaden przyszły lot live nie zaraportuje detekcji bez widocznego intruza).
- **Live-fed detection uplift ZAWIESZONY** do naprawy fidelity symulatora (render małych obiektów dla
  podniesionego sensora). **ENGINE-RECON: PARKOWANY** (decyzja Olgi — NIE startować; osobny cykl na sygnał).

  **Przyszły zakres engine-reconu — trzy TANIE dyskryminatory (kolejność od najtańszego), guard jako kryterium:**
  1. **Software render llvmpipe** — ten sam scenariusz airborne pod software rendererem → rozdziela
     **gz-engine (ogre2) vs sterownik mesa-D3D12** (to habitat!). Skrypty fallbacku software istnieją od R0.0.
     Najtańszy, rozstrzyga „silnik gz" vs „sterownik WSL2".
  2. **GUI-view vs sensor-image** — porównaj widok GUI z pozy kamery powietrznej z obrazem sensora →
     rozdziela **„scena sensora"** od **„render w ogóle"** (czy GUI z tej samej pozy widzi mały obiekt).
  3. **`rgbd_camera` zamiast `camera`** — próba sensora rgbd (kanał koloru); w **gz-sensors #128** ścieżka
     rgbd była odporna tam, gdzie `camera`/`thermal` padały. **Hipoteza do testu, NIE diagnoza.**

  Plus: **issue-search w trackerze gz-sim po pełnym symptomie §6** (podniesiony sensor + małe obiekty na
  dystansie, WSL2/D3D12/ogre2). Render-engine `ogre2→ogre` / API-backend = habitat change (rider 2
  fingerprint); bump gz **tylko** z konkretnym issue upstream (ryzyko parowania PX4↔Harmonic — fundament R0.0).
- **Dźwignie 0/2/R2-alt** (gimbal/MTI/detektor) pozostają **bezprzedmiotowe** — celowały w nie-problem
  (percepcja), gdy przyczyną jest render. **θ_conf i kryterium dwustronne bez zmian.**

**Escape hatch domknięty w budżecie (~1 sesja, ~11 lotów).** Ustalenia + para repro + wykluczenia +
retro-audyt + guard + decyzja O4 dostarczone. Push = Olga; engine-recon = osobny cykl na Twój sygnał.

---

## 8. Prowieniencja §6 — pakiet, granice dowodu, errata (2026-08-09)

**Pakiet:** `results/R02/gate_live/C1_provenance/` (commit 7b58295 + niniejszy): światy §6 odtworzone
z kodu wstawień (as-run niezachowany — `default.sdf` był przywracany po każdym biegu; luka nazwana),
logi wykonawcy per bieg (`gate.log`/`trace.jsonl`/`px4.log`), klatki surowe: **uratowane 12/12 —
10 wariantów C1 (`C1_first`, `C1b`, `C1_direct`, `C1_phys`, `C1_z7`, `C1_world`, `C1_worldonly`,
`C1_noshadow`, `C1_box`, `C1_boxlow`) + `ATTR_static`/`ATTR_flight`; `.npy`+PNG 1:1 w `frames/`,
sha256/rozmiar/mtime w `frames_manifest.json`. Nic nie przepadło (`/tmp/r02` przeżyło do salvage'u).**

**Łańcuch dowodowy world-SDF:** `px4.log` każdego biegu potwierdza load
`…/PX4-Autopilot/Tools/simulation/gz/worlds/default.sdf` — czyli dokładnie pliku modyfikowanego
in-place; zero błędów parsera/meshy w logach; wstawka Lot 1/Lot 2 to prymityw box z materiałem inline
(brak zasobów zewnętrznych); `session_worldonly_trace.jsonl` bajt-identyczny z pierwotnie
committowanym `C1_lifecycle_worldonly.jsonl` (as-run). Ocena wierszy §6: Lot 1 („nie mesh-specific")
i Lot 2 („nie wysokość celu") — wysoka pewność; lifecycle A — wysoka-minus (meshe = te same URI
`model://x500_base`, które renderują na nosicielu w tym samym procesie serwera); shadows=off — SŁABY
(NULL bez kontroli pozytywnej zmiany pikselowej), nienośny dla mechanizmu.

**Granica dowodu (jawna):** dowód obrazowy (guard) nie rozróżnia „model w grafie sceny, nierenderowany"
od „model cicho niezainstancjonowany przy world-load". Dla ścieżki create-based obecność była
potwierdzana pozytywnie (`gz model -p` w runtime) — rdzeń symptomu stoi więc na create-path;
world-path replikuje go obrazowo. Instrument §6 nie wykonywał enumeracji sceny (odpytywał sztywno
nazwę `intruder`, w świecie był `intruder_world`) — naprawione forward-looking w A4.

**Nota [Err] (dla przyszłego issue-triage):** linie `[Err] [UserCommands.cc:1319] Unable to update the
pose … name[intruder]` we wszystkich biegach world-SDF (potwierdzone: `session_box_px4.log`,
`session_boxlow_px4.log`) to artefakt name-mismatch (skrypt wołał set_pose mimo SKIP_CREATE, celując
w nieistniejącą nazwę). **Nie jest to mechanizm awarii renderu.**

**Symptom (wersja EN, do ewentualnego zgłoszenia upstream przy engine-reconie):** *camera sensor on an
airborne/elevated model does not render small (~0.6 m) models — mesh or primitive box, runtime-created
or present in world SDF, target high or low, 7–13 m away — while rendering the vehicle's own close
geometry and the ground plane; a ground-level camera renders the same models. Runtime-created targets
confirmed present via `gz model -p`; world-SDF targets evidenced by loaded-world path + clean parse
(no scene-graph enumeration performed). Habitat: Gazebo Harmonic 8.14 / ogre2 / WSL2 mesa-D3D12.*

**Errata:** static conf = **0.154** (źródło: `static_meta.json`, `RAPORT_R02C §2`); `RAPORT_G_R02 §3f`
podaje 0.156 (linie 376/385/391/400/402/422) — źródłem liczby jest artefakt; 0.156 traktować jako
literówkę raportu.

## 8. REWIZJA (ENGINE-RECON E1/E2, 2026-08-11) — §6/§8 unieważnione wspólnym konfundem GUI

Konfirmator jednozmienny E1 (lot + headless, tylko GUI off vs §6) → intruz RENDERUJE z powietrza
(`results/R02/engine_recon/RAPORT_ENGINE_RECON.md`, dark_px 32–54, wzrokowo). Skutki dla §6/§8:

1. **§6 macierz sweepu — UNIEWAŻNIONA wspólnym warunkiem.** Wszystkie 5 testów (lifecycle A/B/C,
   shadows=off, Lot 1 BOX, Lot 2 BOX nisko) szło **GUI-on** — mierzyły JEDEN konfund (kontencja GUI), nie
   właściwość silnika. Wiersze „NIE mesh-specific / NIE wysokość celu / NIE lifecycle / NIE shadows" stają
   się **PUSTE** (nie rozróżniały niczego, bo wszystkie dzieliły GUI-on). **NIE kasuję** tabeli — zostaje jako
   historia rewizji (wzorzec A-drift→A-plateau→A-episode). Klasa „SILNIKOWA (LOD/culling/scene-management)"
   z §6 — **OBALONA** (E1 jednozmiennie; E2 obala też mechanizm CPU-lockstep).
2. **§8 / „MECHANIZM (precyzyjny symptom — do issue-search)" — WYCOFANY.** Symptom był artefaktem kontencji
   GUI w habitacie WSL2, nie bugiem gz. Pakiet issue-ready = **NIEAKTUALNY, nie przygotowany** — nic nie idzie
   upstream (silnik renderuje poprawnie headless, gz 8.14.0). Dyskryminatory D1/D2/D3/D4 z §7 — zbędne (przesłanka
   „silnik nie renderuje" fałszywa); D2/llvmpipe niepotrzebny.
3. **Status O4 — PRECYZYJNIE: NIE unieważnione.** Zamknięcie toru C stało na bazie **GT-fed** i ta teza STOI
   (osłona+OBSERVE, certy 5/5, dead-man, G5 — niezależne od renderu kamery). To **PONOWNE OTWARCIE ścieżki
   live-fed** (render z powietrza działa headless), NIE kompromitacja zamknięcia GT-fed.
4. **META-LEKCJA (rejestr).** Komponent WIZUALIZACJI (`gz sim -g`), formalnie POZA systemem pod testem, skaził
   DWA niezależne substraty — arming/EKF (R0.3a) ORAZ render (tor C §6) — i przez PIĘĆ testów udawał właściwość
   silnika. Groźniejsze niż przyrząd kłamiący: konfund **WSPÓLNY dla całego sweepu** nie ujawnia się przez
   wewnętrzną niespójność wyników (wszystkie FAIL „spójnie"). Wniosek operacyjny: **zmienne habitatu
   (GUI / kontencja CPU / RTF / zdrowie EKF) należą do ZAMROŻONEGO opisu warunków każdego pomiaru percepcyjnego**,
   na równi z wersją silnika. Zaostrzenie z E2: RTF+time-jump NIE wystarcza (kontencja CPU głodzi EKF przy RTF=1.0).
5. **Nota do RAPORT_R03A [A4]** (naniesiona osobno): GUI powodowało resety EKF → `ε_cap=37/4` mierzone GUI-on jest
   PODEJRZANE o zawyżenie; headless re-charakteryzacja siatki B1-bis może ZMNIEJSZYĆ cap i odzyskać część pola
   patrolu. NIE wykonywane tu (osobna noga, własne PRE).
