# RAPORT_DEMO_C — demo dla widza: trzy akty na prawdziwej kamerze — STOP-DEMOC-1

CC-wykonawca · 26.10.2026 · wykonanie PROMPT_DEMO_C. **Budżet: 3/≤6 bootów
(d1_proba, d2_akty12, d3_akt3), komplet 3 aktów za pierwszym podejściem —
śmierć §4 NIE zaszła. Zero inscenizacji: każdy klip = JEDNO CIĄGŁE okno czasu
epizodu sędziowanego (zero cięć wewnątrz, zero przyspieszeń), zegar epizodu
wypalony.** Zero edycji czegokolwiek istniejącego; nowe pliki wyłącznie
`results/DEMO_C/**`.

## §1. Bramka i reżim — PASS

origin=e6da8995 (CO-PERC2) ✓ gate pusty ✓ porcelain czysty ✓; piny 5/5, certy
9/9; FROZEN komplet + FREEZE_PERC2_OPS (sonda 8df528bb, profil a68a450b, pin
model.sdf 3354ae1e…). Kolizja nazwy DEMOC: brak. **Każdy boot w reżimie OPS:**
pin model.sdf + world_hash PRZED stackiem (3× PIN OK), profil FastDDS dla mostu
obrazu, percep ORAZ zrzutników klatek (GUARD sha profilu w driverze), **sonda
kadencji przed uzbrojeniem: PASS 3/3 za pierwszym podejściem** (dt_p50 0.068,
frac 0.000–0.002), wynik w manifestach (`democ.sondy[]`).

## §2. Mapping take → epizod → werdykt (pełne liczby: `democ_werdykty.json`)

Akty 1–2 sędziowane PEŁNĄ LITERĄ zamrożonego sędziego (przyrząd 1:1
z `perc2_s2_analyze` nogi PERC2: bench_judge **8ec0fcfb** importem, **GT intruza
z MANIFESTU** — reguła erratum, **świadek |ned−cmd|_xy>1 m OBOK**); akt 3
kryterium kampanii K2.

| akt | take | boot | epizod | VALID | breach | REFUSE | werdykt | d_min (sędzia / pokładowo) | świadek | t_acq | w montażu |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | d1_proba | c08_s03 | ✓ | 0 | 0 | **D6 PASS** | 5.613 / 5.654 | 0/3143 | 0.73 s | **TAK** [0–32 s] |
| 1 | 2 | d2_akty12 | c08_s04 | ✓ | 0 | 0 | **D6 PASS** | 6.819 / 6.868 | 0/3145 | 0.72 s | nie (zapasowy, równorzędny) |
| 2 | 1 | d2_akty12 | c10_s02 | ✓ | 0 | 0 | **D6 PASS** | 5.256 / 4.669 | 2/3387 | 8.85 s | **TAK** [0–34 s] |
| 3 | 1 | d3_akt3 | c03_s01 | ✓ | 0 | — | **kryterium K2 PASS** | — | — | — | **TAK** [22.7–46.5 s] |

**Akt 3 (liczby z trace):** denial (EKF2_GPS_CTRL=0) wstrzyknięty @32.66 s
epizodu → **REFUSE(POS_DEGRADED) +0.100 s** → zejście D5 → **touchdown +9.84 s**,
breach 0, **REFUSE przed denialem: 0** (twardy STOP §1.4 interpretowany literą
aktu: REFUSE(POS) PO wstrzykniętym denialu = sędziowane zachowanie osłony —
kryterium K2; REFUSE przed denialem lub w aktach 1–2 = STOP; zmierzone: nie
wystąpił). Kadencja lotu we wszystkich ujęciach: dt_p50 0.064–0.068 / frac 0.0.
**Lista odrzuconych take'ów: PUSTA** (4/4 ujęcia VALID z werdyktem pozytywnym;
take 2 aktu 1 nie wszedł do montażu wyłącznie jako równorzędny zapas — wybrano
take 1 z próby generalnej; żadnego kręcenia do skutku).

## §3. Sposób zrzutu świata i kamery (mechanizm nazwany)

- **Świat:** mechanizm DEMO-B/V3 — `FILM=1` w run_boot (most kamery filmowej
  world_demo_A3 `film` 1280×720@30, run_boot.sh:114-120) + rejestrator klatek
  wg STEMPLA SIM (wzór `results/DEMO_V3/tools/film_recorder.py`; nowa kopia
  `democ_framedump.py` — jedyne zmiany: zapis JPG q90 zamiast .npy + mono8).
  **Poprawka zmierzona w D1:** most filmowy startowany przez run_boot ma
  transporty domyślne — klatka 2.76 MB gubiła się (world 4.3 fps, dt 0.13–0.26);
  od D3 driver podmienia go na most z profilem FastDDS (world stabilnie
  ~7.7 fps, dt 0.13 stałe). Render świata w klipach: ZOH (ostatnia klatka ≤ t,
  staleness ≤0.5 s) — klatki trzymane, nigdy fabrykowane.
- **Kamera pokładowa:** ten sam `democ_framedump.py` na topiku imagera
  (640×480 mono, pełne 14.7 kl/s — pokrycie zmierzone: dt 0.064/0.068 bez luk);
  w klipach upscale **×2 nearest-neighbor** (uczciwy pixel-look). Ramki
  detektora WYŁĄCZNIE z percep_feed (dopasowanie po t_frame ≤10 ms), rysowane
  tylko w aktach 1–2.
- **Split-screen:** świat lewa (miniatura 640×360 + panel telemetrii), kamera
  prawa (1280×960). **Odchylenie jawne (akt 3):** kamera filmowa świata jest
  wykadrowana na centroid aktu A3 DEMO (komentarz world_demo_A3.sdf:1278) —
  strefa orbity/zejścia leży na krawędzi jej kadru i dron bywa poza kadrem;
  widokiem głównym aktu 3 jest więc SUROWA kamera pokładowa (bez ramek — napis
  „percepcja EMULOWANA w tym akcie (obraz pokładowy = podgląd, nie karmi
  sterowania)" wypalony przez cały akt; zejście widoczne w obrazie i w dużym
  odczycie WYSOKOŚĆ z trace GT), świat pozostaje w miniaturze.

## §4. Montaż

`DEMO_C.mp4`: **98.4 s** (akty 31.8 + 33.7 + 23.9 s + plansza 9.0 s; przedział
90–130 s ✓), 1920×1080 @10 fps; napisy PL wypalone (DejaVuSans; overlay per akt),
plansza finałowa TEKSTEM FROZEN z §3.4; osobny `DEMO_C_en.srt` (czasy sklejki).
**Odchylenie jawne od litery §3.4 („ffmpeg"):** ffmpeg nie istnieje na hoście —
montaż `cv2.VideoWriter` mp4v, precedens kanoniczny DEMO_V3
(RAPORT_DEMO_V3: „mp4v (cv2, bez ffmpeg)"). Zero przyspieszeń ⇒ podpis „×N"
bezprzedmiotowy; zero cięć wewnątrz epizodów ⇒ zegar ciągły w każdym akcie.

**Pliki wideo — ŁĄCZNIE 46 MB > 25 MB ⇒ wg §5 zostają NA DYSKU (pełne ścieżki
+ sha256); commit bez mp4:**

| plik (na dysku) | sha256 |
|---|---|
| `results/DEMO_C/DEMO_C.mp4` (98.4 s, 23 MB) | `cdc160806f44f84712aab8c13666214c0b9a843bf9bd80dd8d749480f32471ca` |
| `results/DEMO_C/clips/akt1_c08_s03.mp4` | `8b8617ce580e6178bc744d8937e40fac08142720377af5c239bd82799b9bff1d` |
| `results/DEMO_C/clips/akt2_c10_s02.mp4` | `4c8f9a5b33fec351ace86d8e96df3eab00d19c2c1c4039897ae0f9b858bfccf6` |
| `results/DEMO_C/clips/akt3_c03_s01.mp4` | `f658adb18cf7ac00e9915e5d1c4ec06d803d709650b431b8b37c90d890fa3239` |

(Klatki jpg ujęć zostają na dysku w `booty/*/cam/frames`, `booty/*/world/frames`
— commit niesie `frames_index.jsonl` + komplet metadanych do odtworzenia
werdyktów: manifesty z sondy[]/pin, percep_feed, demo, trace, qlog.)

## §5. Narzędzia (sha256, 16)

| plik | sha | rola |
|---|---|---|
| `tools/democ_boot.sh` | 29cd4f5625edd044 | driver dwutrybowy (AKT12 = reżim perc2_s2; AKT3 = reżim run_k2_boot + shadow-percep do sondy) |
| `tools/democ_framedump.py` | 413301f52ecf13f2 | zrzutnik jpg (mechanizm film_recorder DEMO_V3) |
| `tools/democ_overlay.py` | 324b0b052ff5d796 | render klipu aktu (okno ciągłe, overlay, napisy PL) |
| `tools/democ_cut.py` | 90bf04462c7d6e40 | sklejka + plansza FROZEN + DEMO_C_en.srt |
| `tools/democ_judge.py` | 5d315c2013003d82 | werdykty ujęć (sędzia FROZEN + świadek; kryterium K2) |

## §6. STOP

Commit: narzędzia + raport + `democ_werdykty.json` + `DEMO_C_en.srt` + artefakty
ujęć (3 booty: manifesty/percep_feed/demo/trace/qlog/sondy/indeksy klatek).
**Push = Olga („wypchnięte" — CC weryfikuje ujęcia sędzią z repo, ZANIM mp4
pójdzie na zewnątrz).** **STOP-DEMOC-1.**
