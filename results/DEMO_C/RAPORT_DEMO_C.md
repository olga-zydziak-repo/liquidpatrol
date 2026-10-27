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

## Montaż v2 — panel taktyczny z góry (dopisek append-only; PROMPT_DEMO_C_V2, STOP-DEMOC-2)

**Zero nowych bootów; te same trzy ujęcia; werdykty ujęć BEZ ZMIAN** (§2 wyżej).
Dołożony panel taktyczny renderowany WYŁĄCZNIE z istniejących logów bootów
d1–d3 (trace/gt_intruder/demo/percep_feed), zsynchronizowany po t_sim — żyje
w tym samym zegarze i tych samych TEMPO ×n co reszta kadru.

- **Narzędzia NOWE (v1 nietykalne):** `tools/democ_topdown.py` (panel: północ
  w górę, siatka 5 m, strefa osłony R_E = 32 m podpisana — r01/config.py:30,
  home, dron/intruz = punkty z blaknącymi ogonami ~12 s, markery ENTRY /
  REFUSE(POS) / TOUCHDOWN trwałe po zajściu, etykieta „(GT)"; **filtr brzegu
  startu**: próbki świadka |ned−cmd|_xy>1 m nie są rysowane — ta sama reguła co
  u sędziego) oraz `tools/democ_overlay_v2.py` (kopia v1 + panel).
  `democ_cut.py` v1 użyty bez zmian (nowy plik cut niepotrzebny).
- **Układ (decyzja montażowa):** kamera pokładowa pozostaje widokiem głównym;
  panel taktyczny 640×640 zajmuje lewą kolumnę W MIEJSCE wkładki świata
  (miniatura świata była mało czytelna — kamera filmowa kadruje centroid A3,
  dron bywał poza kadrem — a kontekst przestrzenny daje teraz panel); HUD
  kompaktowy 640×324 pod panelem.
- **Akt 3 — wariant §1.4 z DWOMA punktami drona (weszedł):** obie serie są
  w logach — GT (trace t:gt) pełnym punktem, estymata nawigacji (demo.jsonl
  own_pos_ned, dostępna przez całe zejście do touchdown) punktem kropkowanym;
  po denialu estymata ODPŁYWA od prawdy (zmierzone |est−GT|_xy: 0.17 m
  @+1.6 s → 3.14 m @touchdown) — podpis w HUD i legendzie.
- **Wyjścia (napisy PL, plansza FROZEN i `DEMO_C_en.srt` bez zmian; tor cv2
  jak v1):** łącznie >25 MB ⇒ NA DYSKU, sha256:

| plik (na dysku) | sha256 |
|---|---|
| `results/DEMO_C/DEMO_C_v2.mp4` (99.1 s, 26 MB) | `e876e58fd535fe3aa8602e6c1856fcaa63ca8aa9959d5e3e0c75fbddbabcbad7` |
| `results/DEMO_C/DEMO_C_v2_SHORT.mp4` (54.2 s, 14 MB) | `ebe7391e0d32704d7030dfd395bb7c8236586a253714ed0d1e8fbc849d2ed8e5` |
| `clips/akt1_v2.mp4` | `160241d489c3a75908116b45258d790b051cbceed3bfd5bc38915efd59262eb7` |
| `clips/akt2_v2.mp4` | `f30254f34785fe80f468fc07cda7bf45644a9c7857f9e7aed5a5cc7196d1684a` |
| `clips/akt3_v2.mp4` | `98a909eb4390074379d7822e67522df1a7ff1de59db87e84b1c6372c50aefdfe` |
| `clips/akt1_v2_short.mp4` | `9ae7e5dea220a61bcb951a28700445c1dab281dfbb734b5907053455574a4812` |
| `clips/akt2_v2_short.mp4` | `ff2f0f61be43d25128d4037b7b0d9270cd25c6749d53bb2585cfba39f39f80a8` |
| `clips/akt3_v2_short.mp4` | `63920b884077ba5d8c80fe6bf5418e2c8fe745ee119d40209898db63563972e4` |

Segmenty SHORT v2 = 1:1 z NOTA_SHORT.md. **STOP-DEMOC-2.**

---

## Akt 4 (v3) — „Wabiki" (dopisek po STOP-DEMOC-2; wykonanie PROMPT_DEMOC_V3; RAPORT wyżej NIETKNIĘTY)

**Bramka:** origin=`dccc8804` (CO-WABIK2), gate pusty, porcelain czysty poza
nazwanymi `??`; FROZEN: wabik_sig v1 `475c972e`, manifesty `046fa12b`/`86268b02`,
sonda `8df528bb`, profil `a68a450b`, pin model.sdf `3354ae1e…`, SHIELD FROZEN.

**Booty: 2/≤4, komplet za pierwszym podejściem; breach 0 / REFUSE 0 w obu;
lista odrzuconych take'ów PUSTA.** Reżim OPS per boot (wzór 1:1 wabik_s1_boot):
pin model.sdf + world_hash PRZED stackiem (2× OK), profil FastDDS na moście
obrazu/percep/zrzutnikach, sonda kadencji przed uzbrojeniem PASS 2/2
(preflight rc=0; wynik w manifestach `democ_v3.sondy[]`). Kadencja LOTU:
dt_p50 0.064/0.068, frac>0.10 = 0.0 w obu. **Jeden obiekt w świecie naraz**
(litera WABIK S2): scenariusz wabika GRANY TOREM INTRUZA
(`BENCH_MANIFEST=results/WABIK/wabik_manifest_s2.json`), GT w `gt_intruder`.

**Mapping take→epizod→wynik** (przyrządy zamrożone importem —
`democ_v3_post.py`: etykieta = wabik_sig v1 `classify/feed_rows` 1:1 na
percep_feed lotu; werdykt = perc2_s2_analyze.analyze_boot, sędzia FROZEN
`8ec0fcfb`, GT manifest + świadek OBOK, SCEN.update wzorem wabik_s2_analyze):

- **AKT 4a** `w00a_s01` (boot d1, `s3_wabik/akt4a_loiter`): VALID, breach 0 /
  REFUSE 0; dron traci i ODZYSKUJE track skanem (t_acq sędziego 8.82 s),
  orbita obserwacyjna d_min 7.29 m; **etykieta WABIK: TAK, bez odwołania**
  (n_W 1036/1067 klatek, dh_min tracka 8.32 m > podłoga 5.0);
  t_do_flagi 31.81 s od pierwszej ważnej klatki trk (= 40.6 s zegara epizodu;
  dłużej niż 17.62 s tego wpisu w WABIK S2 — ta sama litera, inny lot: szum
  v_rad rwie streaki, mechanizm nazwany w RAPORT_WABIK_S2; flaga ZASZŁA).
  Świadek 0/3545. [montaż 0–12 ×1 / 12–34 ×3 / 34–44 ×1; flaga W CZASIE
  RZECZYWISTYM]
- **AKT 4b** `m01_s01` M-POD-ORBITĄ (boot d2, `s3_wabik/akt4b_orbita`):
  VALID, breach 0 / REFUSE 0; **flaga wstępna → cel zmienia zachowanie →
  ODWOŁANIE → pościg → D6 PASS sędzią pełną literą** — t_do_flagi 21.19 s /
  t_odwołania 32.34 s (dh_min tracka 4.99 < 5.0 łamie podłogę; zegar epizodu:
  flaga 21.9 s, odwołanie 33.1 s), t_entry 3.4 s, d_min sędziego 6.83 m
  (pokładowo 6.888). Świadek 0/3246. [montaż 0–4 ×1 / 4–18 ×2 / 18–26 ×1 /
  26–30 ×2 / 30–38 ×1 / 38–52 ×3; flaga i odwołanie W CZASIE RZECZYWISTYM]

**Uczciwość klasyfikatora:** etykieta wyliczona POSTHOC z percep_feed tego
lotu klasyfikatorem FROZEN `475c972e` (strumień 1:1 z live — równoważność
nazwana w RAPORT_WABIK_S1); napis „klasyfikator diagnostyczny — etykieta
wyliczona z zapisu lotu, nie steruje dronem" WYPALONY przez cały akt 4;
sekundnik od flagi jawny; przyspieszenia wyłącznie z plakietką „TEMPO ×N".

**Montaż:** `DEMO_C_v3.mp4` **162.8 s** ≤ 180 (akty 1–3 = gotowe klipy v2
z dysku bez rerenderu: 32.1+34.1+23.9 s; akt 4a 29.6 s + 4b 34.1 s; plansza
9 s = tekst FROZEN v1/v2 + NOWA linia FROZEN §3: „Wabiki: rozpoznawane po
zachowaniu — zero fałszywych alarmów w pomiarach."); 1920×1080@10, napisy PL
wypalone, `DEMO_C_v3_en.srt` z blokami aktu 4. Tor cv2 mp4v (odchylenie jawne
jak v1/v2: ffmpeg nie istnieje). Łącznie >25 MB ⇒ **NA DYSKU**, sha256:

| plik (na dysku) | sha256 |
|---|---|
| `results/DEMO_C/DEMO_C_v3.mp4` (162.8 s, 46 MB) | `83430d1138270a23ccba6e535e928976db5db99ce1cbbbd8b071aa1a7a74a286` |
| `clips/akt4a_v3.mp4` | `b831928dd321e7c1705969ca8cfe3b8cd562634821dba617c1bb918029b49580` |
| `clips/akt4b_v3.mp4` | `956836f6354c3bce7af724e79a9192a83c5770bc2253af8869a9e9b2ffd0491f` |

**Narzędzia NOWE (v1/v2 i democ_topdown NIETKNIĘTE):** `democ_v3_boot.sh`
(kopia wabik_s1_boot; zmiany deklarowane: katalog s3_wabik, TRAJ zawsze '-',
FILM=1 + democ_framedump cam/world + podmiana mostu filmowego na profilowany —
fix zmierzony DEMO-C D1), `democ_overlay_v3.py` (kopia toru v2 + WBUDOWANA
kopia panelu z obiektem pomarańczowym „wabik"/czerwonym „cel", wskaźnik
ETYKIETY, napis uczciwości; jedyna poprawka w toku: separator „·"→„/"
w stopce panelu — cv2.putText nie renderuje UTF-8), `democ_v3_post.py`,
`democ_cut_v3.py`. Artefakty: `s3_wabik/akt4a_loiter` + `akt4b_orbita`
(manifesty z blokiem `democ_v3{pin,sondy[],uzbrojony_po_sondzie}`,
percep_feed, demo, trace, gt_intruder, frames_index; boot.ulg wg polityki
gitignore, ulog_sha w manifestach), `akt4a/4b_sig.json(+jsonl)`,
`akt4_werdykty.json`. Klatki jpg NA DYSKU (celowe `??`). **STOP-DEMOC-3.**
