# RAPORT_R1 — aktor-intruz w świecie (R0.2, PRE §2.1)

Data: 2026-08-07. Reżim: budowa, krok R1. Poprzednik: B0 PASS (`RAPORT_B0.md`).
Artefakty: `r02/intruder_model.sdf`, `r02/intruder_driver.py`, `r02/capture_frame.py`,
`r02/sample_intruder_pose.py`, `results/R02/r1_frames/{base,intruder,intruder_bbox}.png`.

## WERDYKT R1: **PASS (podejście MODEL)** — z jednym znaleziskiem blokującym (aktor) i jednym ryzykiem do decyzji (detekcja)

Intruz kinematyczny jako **model** (nie gz `<actor>`): spawnuje się bez crashu, jest **widoczny na
kamerze**, `set_pose` działa → deterministyczny sterownik pozy `f(sim_time)` wykonalny i
zademonstrowany. Determinizm/powtarzalność (PRE §2.1) spełnione konstrukcyjnie.

## 1. Znalezisko blokujące (rozwiązane pivotem): gz `<actor>` bez `<skin>` WYWALA serwer

Pierwsze podejście — intruz jako SDF `<actor>` ze skryptową trajektorią + box `<visual>` (bez `<skin>`)
— **segfaultuje serwer gz**:
```
[Err] [MeshManager.cc:150] Invalid mesh filename extension [.../r02/__default__]
Segmentation fault in SceneBroadcaster::PoseUpdate   (ruby signal 11, CaptureCrash serwera)
```
gz próbuje załadować domyślny skin-mesh `__default__`, pada na rozszerzeniu, SceneBroadcaster segfaultuje
na pozie aktora. **Ważna korekta diagnozy:** obserwowany wcześniej „brak topiku kamery" był **SKUTKIEM
padu serwera** (który zabił render sensorów), a NIE osobnym błędem kamery — na czystym stacku (bez aktora)
kamera publikuje `.../imager/image` normalnie, zegar krokuje. **Pivot:** intruz = zwykły `<model>`
(PRE §2.1 mówi „kinematyczny MODEL … pose-scripted … SetPose", nie gz `<actor>`). `r02/intruder_actor.sdf`
pozostawiony jako **SUPERSEDED** (znacznik w pliku). Aktor `<actor>` wymaga mesha-skinu/animacji —
nieadekwatny do prostego intruza.

## 2. Weryfikacja podejścia MODEL (r02/intruder_model.sdf)

Model statyczny (physics OFF — brak grawitacji/dynamiki), wizual = ciemny quad-UAV (kadłub+ramiona).
Świeży stack `run_stack.sh` (gz_x500_mono_cam), kamera zmostkowana (BEST_EFFORT).

| Test | Wynik |
|---|---|
| **Serwer stabilny** (bez aktora) | zegar krokuje (t: 209→211), topik `imager/image` publikuje, 0 crash-markerów |
| **Spawn modelu** (`gz create`) | `data: true`, serwer **przeżył** (0 markerów) |
| **`set_pose` na modelu statycznym** | `data: true` — pozę można ustawiać (sterownik wykonalny) |
| **Widoczność na kamerze** | klatka bazowa min=158 → z intruzem **min=19** (ciemne piksele); **337 px zmienionych** (0.11% kadru), bbox x[279–333] y[190–247] w obrazie 640×480 |
| **Ruch sterowany deterministyczny** | y=−6 → środek_x=**512** (prawo); y=+6 → środek_x=**109** (lewo) — pozycja w obrazie = przewidywalna funkcja komendy y (=f(sim_t)) |

**Determinizm (PRE §2.1):** `r02/intruder_driver.py` liczy pozę = `f(sim_time)` (trójkątna fala po y,
prędkość v, okres 2·span/v) i ustawia przez `set_pose`. Poza jest **czystą funkcją sim-time** (bez
fizyki/losu) ⇒ ta sama sim-time ⇒ ta sama poza między biegami. Trajektorię per-scenariusz podmienia
się parametrami (seed=ID scenariusza).

Klatki: `results/R02/r1_frames/{base,intruder,intruder_bbox}.png`.

## 3. RYZYKO DO DECYZJI (bramka→decyzja): detektor słabo wykrywa prosty box-intruz

Bonus-pomiar (poza zakresem R1, sygnał do G1/G2): YOLO-World `set_classes(["drone"])` na klatce
z intruzem-boxem zwrócił **1 box z conf = 0.001** (podłoga progu) — czyli **nie rozpoznaje** prostego
ciemnego prostopadłościanu jako „drona". To spodziewane: YOLO-World uczony na realnych obrazach, a
intruz to prymitywny box. **Konsekwencja dla G1/G2:**
- Per **R02-A1** kanał nie ma progu conf (detektor publikuje top-1 box zawsze) → na scenie bez realnego
  UAV top-1 box może być **szumem/fałszywym lockiem** (ryzyko dla G1: 0 ENTRY bez intruza).
- **Opcje (decyzja Olgi):**
  1. **Realistyczny mesh UAV** jako wizual intruza (lepsza detekcja; koszt: asset .dae/.glb + render) —
     zalecane jeśli G2 ma wykazać wiarygodną detekcję.
  2. **Zostać przy boxie** i zaakceptować, że detekcja może być słaba → wynik G2 może być NEGATYWNY
     (pełnoprawny wynik: „detektor nie łapie intruza na tej scenie"), zgodnie z SR-5.
  3. **Detektor dostrojony/jednoklasowy** pod sylwetkę intruza (poza YOLO-World) — większy zakres.

To ryzyko **nie blokuje R1** (aktor istnieje, deterministyczny, widoczny), ale **przesądza kształt G2**
→ wymaga decyzji przed budową kanału/bramki.

## 4. Higiena
- Stack posprzątany po każdej próbie (0 procesów, VRAM=0).
- Reguła operacyjna potwierdzona: `mkdir -p $LOGDIR` przed redirectem `run_stack.sh`; teardown po PID
  (nie `pkill -f ruby` — zabija powłokę sesji).

## 5. Następny krok (po decyzji o intruzie §3)
R3: węzeł detektora + kanał 5-dim ZOH-age BEZ conf (A1) → R4 OBSERVE + re-cert (selfcheck → P1/P4/P5
na 7 liściach) → bramka G1–G5. Rozdzielczość kamery: domyślna modelu 640×480 (rgb8); pod detektor/most
rozważyć 320×240 (< sufit 256 KB, R0.1 §6) — do ustalenia w R3.
