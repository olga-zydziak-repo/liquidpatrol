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

---

## Montaż v3.1 — panel „JAK ROZPOZNAJE" + admisja krok-po-kroku (dopisek po STOP-DEMOC-3; wykonanie PROMPT_DEMOC_V31; wszystko wyżej NIETKNIĘTE)

**Zero nowych bootów, zero SITL; te same ujęcia v3; werdykty i etykiety BEZ
ZMIAN.** Nowy overlay WYŁĄCZNIE z istniejących logów (percep_feed + akt4*_sig
+ demo/trace/gt + democ_werdykty). STOP-DEMOC-3 był już zacommitowany
(`466573eb`) ⇒ v3.1 idzie osobnym commitem z tym dopiskiem.

**§1 — akty 4a/4b, żywy panel reguły** (w miejscu pola ETYKIETA): trzy wiersze
warunków z wartościami per klatka („w ruchu" speed>0.30 / „nie zbliża się"
v_rad<0.30 / „nie był <5 m" dh_min≥5.0, ✓/✗) + „licznik: X.X / 12 s → —/WABIK/
ODWOŁANA". Dane per klatka = `akt4a/4b_sig.jsonl` (wiersze wyliczone
klasyfikatorem FROZEN `475c972e` przy STOP-DEMOC-3 — te same rachunki, które
policzyły etykietę; v3.1 niczego nie przelicza nową literą). **Kotwica
w kodzie (asercja):** rekonstrukcja licznika z jsonl odtwarza t_flag/t_revoke
z `akt4*_sig.json` ≤10 ms (zaokrąglenia t_sim w jsonl): 4a flaga 151.34 vs
151.338; 4b flaga 133.256 vs 133.258, odwołanie 144.408 = 144.408.
**Jawność niepełności wyświetlania:** reguła FROZEN ma CZTERY człony —
czwarty (dh<18 m, strefa) w OBU ujęciach zawsze prawdziwy (dh_max 10.96 m /
15.55 m), nie wiąże i nie jest wyświetlany; koniunkcja trzech pokazanych
warunków == W klatka-w-klatkę w 100% wierszy obu jsonl (sprawdzone). Licznik
rośnie tylko przy komplecie ✓ i zeruje się na piku szumu (widoczne w 4a);
po zapadnięciu flagi licznik pokazuje 12.0/12 wygaszony (reguła jednostrzałowa
— flaga zapada raz), warunki dalej żywe. **4b — mechanizm cofnięcia NA
EKRANIE:** przy ataku „nie zbliża się" przeskakuje na ✗ (v_rad +1.04 @32.5 s),
potem „nie był <5 m" na ✗ (min 4.99 m) ⇒ ODWOŁANA (33.3 s zegara). Napis
uczciwości („…nie steruje dronem") bez zmian, wypalony cały akt.

**§2 — akt 1, admisja krok-po-kroku** (klip aktu 1 ZRERENDEROWANY z tych
samych klatek ujęcia d1_proba/c08_s03; tor v2 1:1 — Panel z democ_topdown
importem, napisy PL i HUD bez zmian): zwolnienie ×0.5 na fragmencie zegara
0.2–3.2 s (3.0 s ujęcia → 6.0 s ekranu) z plakietką „TEMPO ×0.5" (plakietka
odtąd także dla tempa <1); sekwencja 4 podpisów, kotwice WYLICZANE z logów
w narzędziu (nie z ręki): (1) „ramka detektora — conf 0.77" = pierwsza klatka
epizodu z boxem conf≥0.5 (sim 115.964, zegar 0.48 s); (2) „3 zgodne klatki:
centralność + ruch (brama admisji k=3)" = pierwszy run 3 kolejnych klatek
fresh (116.16/116.228/116.292 — dwie bramkowane koniunkcją admisyjną gate=mti,
trzecia oknem predykcji gate=window; litera bramy k=3 = r02/target_channel,
READ-ONLY); (3) „ADMISJA → TRACK (t_acq sędziego 0.73 s)" — t_acq z
`democ_werdykty.json`; (4) „sieć płynna prowadzi — APPROACH 0.7 s → ORBITA
2.5 s" = przejścia faz z demo.jsonl (116.208/117.956). Kroki pojawiają się na
kotwicach sim z dostojnością ≥1.1 s ekranu, panel znika po 16 s klipu.
**Jawność mechanizmu:** formalny ENTRY-once kanału zaszedł w tym ujęciu 0.57 s
PRZED zegarem epizodu (sim 114.908, intruz już w świecie przed episode_start);
w oknie klipu widoczne są bramkowane REFRESH-e tej samej koniunkcji admisyjnej
— sekwencja podpisów nazywa mechanizm bramy (k=3: centralność+ruch) liczbami
z tego feedu i nie twierdzi, że ev=ENTRY pada w kadrze.

**Montaż:** `DEMO_C_v31.mp4` **166.0 s** ≤ 180 (akt 1 v31 35.3 s; akty 2–3 =
klipy v2 z dysku bez rerenderu 34.1+23.9; akt 4a 29.6 + 4b 34.1 — segmenty
TEMPO 1:1 z v3; plansza 9 s = tekst FROZEN v3 BEZ ZMIAN); 1920×1080@10, tor
cv2 mp4v (odchylenie jawne jak v1–v3), `DEMO_C_v31_en.srt` (bloki aktu 1
przepisane pod sekwencję admisji + po jednym bloku o panelu reguły w 4a/4b).
SHORT: w PROMPT opcjonalny — NIE wykonany. Łącznie >25 MB ⇒ **NA DYSKU**,
sha256:

| plik (na dysku) | sha256 |
|---|---|
| `results/DEMO_C/DEMO_C_v31.mp4` (166.0 s, 47 MB) | `b912c8b3369ff61b5677604a1e7a57507336279ff145c901e0fee5853aaffda5` |
| `clips/akt1_v31.mp4` | `7cad3d1535651b220c1c53430d0985d6c969971e0ddbd6c1e10ee7c05dc3f1cd` |
| `clips/akt4a_v31.mp4` | `ade5b5643b6afdaa6a03dfb8ab750b5bf9700513aad0ede66963174b2640adc1` |
| `clips/akt4b_v31.mp4` | `ed16c110b386190a519b5df9401e31ee2d34230404d3bf89aeccfae3a0b70b31` |

**Narzędzia NOWE — dwa pliki (v1/v2/v3, democ_topdown i democ_cut* NIETKNIĘTE;
wszystkie FROZEN importem albo wcale):** `tools/democ_overlay_v31.py`
`b7128e80b61e417e` (tryb akt1 + tryby 4a/4b; wbudowana kopia Panel4 z v3;
kotwica licznika asercją), `tools/democ_cut_v31.py` `c7064a4a78e399fc`
(sklejka + srt; plansza FROZEN 1:1 z cut_v3 — §3 PROMPT mówił o jednym nowym
pliku, drugi doszedł, bo cut_v3 ma zaszyte nazwy wyjść v3 i jego użycie
nadpisałoby DEMO_C_v3.mp4 — odchylenie jawne, zero edycji istniejących).
Jedyna poprawka w toku montażu: format `dh_min` na 2 miejsca (zaokrąglenie
„5.0" przy ✗ myliło przy wartości 4.99). Werdykty, sig-i, manifesty, klatki:
BEZ ZMIAN. **Push = Olga („wypchnięte" — CC weryfikuje dopisek i ogląda v3.1
z załącznika). STOP-DEMOC-31.**

---

## Montaż v4 / AKT 5 „W głowie sieci" (dopisek po STOP-DEMOC-31; wykonanie PROMPT_DEMOC_V4; wszystko wyżej NIETKNIĘTE)

**Zero nowych bootów; werdykty ujęć BEZ ZMIAN.** Bramka: origin==HEAD ==
`7564a98e` (CO-XAI; `ANEKS_XAI-1.md` byte-check `65ef4393…` PASS). Aktywacje
odtworzone replayem: **xai_replay `ac9551ab` IMPORTEM**, wagi ncp `0337d5ea`
kopią; FREEZE_XAI obowiązuje na ekranie (wyłącznie T1/T2, oba PROVED; T3/T4
nie wchodzą; zero roszczeń D6).

- **Źródło ujęcia (bez zmian):** boot `d2_akty12`, epizod **c10_s02**
  (ujęcie aktu 2, VALID, D6 PASS — §2 wyżej); te same klatki (lewa połowa =
  gotowy klip `akt2_v2.mp4` pomniejszony ×0.5, z własnym HUD) i ten sam
  `demo.jsonl`; synchronizacja klatka↔tick po czasie, wzór v3.1.
- **KOTWICA REPLAYU TEGO UJĘCIA** (próg STOP >1e-2 — nie zaszedł):
  p50 **5.71·10⁻⁴** / p95 **1.18·10⁻³** / max **2.33·10⁻³** m/s,
  granica hold/inferencja **0 rozjazdów** (1533 ticki, 1361 inferencji);
  p95 wypalona w napisie uczciwości („…nakładka nie steruje dronem").
- **Baza PCA:** loadings nie są zapisane literą w JSON-ach atlasu ⇒
  przeliczona DETERMINISTYCZNIE z korpusu atlasu (48 ep. LIQ NCP po erratum,
  indeks `erratum_sweep.json`, pula h na tickach inferencji, SVD po
  centrowaniu, znak: max|ładunek| dodatni) → **`xai_pca_base.json`**
  (67 586 ticków). **Kotwica bazy (asercja):** frakcje wariancji top5 ==
  `xai_atlas_ncp.json` co do 4 miejsc; top2 = **87.8%** (podpis na ekranie).
- **Role neuronów na ekranie** (z atlasu c_role, podpisane „role z korelacji
  (opisowe)"): n0 „kierunek na cel (sin)" |r|=0.953 · n5 „(cos)" |r|=0.892 ·
  n11 „cel względny N (rel_x)" |r|=0.913.
- **AKT 5 = 38.2 s** [segmenty: 0–7.5 ×1 / 7.5–11.5 ×0.5 (akwizycja+wejście
  w orbitę, plakietka TEMPO ×0.5; lewa połowa: klatka klipu duplikowana —
  zwolnienie materiału 10 fps) / 11.5–34 ×1; okno przycięte do długości
  klipu v2 — zegary lewo/prawo zgodne co do klatki]. Prawa połowa:
  przestrzeń stanu h(t)→PCA (kolor per faza scan/approach/orbita jak
  w atlasie; **jasny ogon 8 s + wygaszony ślad skumulowany — DODATEK
  MONTAŻOWY nazwany: okres orbity ~30 s, sam ogon 8 s nie pokazałby
  pierścienia**; podpis „stabilny cykl = decyzja «krążę»" przy 10–24 s),
  pasek 20 neuronów, linia twierdzeń (stała): „dowiedzione: |komenda| <
  3 m/s (T1) · stan ograniczony |h|<1 (T2) — status PROVED, różnicówka
  0/74 708 ticków".
- **Montaż:** `DEMO_C_v4.mp4` **204.2 s** ≤ 240 (v3.1 bez planszy 157.0 +
  akt 5 38.2 + plansza 9.0); plansza v4 = tekst v3.1 + linia „Sterownik:
  20 neuronów — dowiedzione twierdzenia o ograniczoności (T1/T2), aktywacje
  audytowalne replayem." (wstawiona przed wierszem zamykającym). Tor cv2
  mp4v (odchylenie jawne jak v1–v3.1). Napisy PL wypalone;
  **`DEMO_C_v4_en.srt` NOWY plik** (edycja `DEMO_C_en.srt` zakazana literą
  „zero edycji istniejących" — odchylenie nazwane; bloki = v3.1 + akt 5 +
  plansza v4). **SHORT wykonany (tani):** `DEMO_C_v4_SHORT.mp4` 14.1 s =
  segment pierścienia [6–34 s] ×2 z plakietką TEMPO ×2 (render, nie
  frame-skip). Wideo łącznie >25 MB ⇒ **NA DYSKU**, sha256:

| plik (na dysku) | sha256 |
|---|---|
| `results/DEMO_C/DEMO_C_v4.mp4` (204.2 s, 59 MB) | `128ff4e4d114c40f9d4d81d3b236fcd350c606085821952665903507fd9ae462` |
| `results/DEMO_C/DEMO_C_v4_SHORT.mp4` (14.1 s, 4.5 MB) | `faa8cf521587bf7dc547afd0985eda358dc35e92282d7bc1461e00a16898974b` |
| `clips/akt5_v4.mp4` (38.2 s) | `4e76b0f0baf869abe25c129fd123c47b46943e3905b2cbe89cf3587dd59ee356` |

**Narzędzie NOWE (v1–v3.1 NIETYKALNE):** `tools/democ_overlay_v4.py`
(tryby pca-base / akt5 / cut). W commicie: narzędzie + `xai_pca_base.json`
+ `DEMO_C_v4_en.srt` + ten dopisek. Klatki/wideo na dysku (celowe `??`).
**STOP-DEMOC-4.**

---

## Montaż v5 — „sieć przez całe demo" (dopisek po seansie Olgi nad v4; wszystko wyżej NIETKNIĘTE)

**Uwaga z seansu (ratyfikatorka): „na v4 nie widać nic, jeśli chodzi
o wyjaśnialność" + prośba o widok sieci przez całe demo i lepszy widok
neuronów.** v4 NIE wyszło poza repo (push nie zaszedł) — v5 zastępuje v4
PRZED publikacją; werdykty ujęć i wszystkie liczby BEZ ZMIAN; zero bootów;
aktywacje wyłącznie replayem (xai_replay `ac9551ab` importem).

- **MINI-MÓZG W ROGU AKTÓW 1 / 2 / 4a / 4b (NOWE):** panel „W GŁOWIE SIECI
  (replay)" 312×236 px — 20 neuronów (puls: promień ∝|h_i|, kolor = znak)
  + 3 wyjścia; NAKŁADKA NA GOTOWE KLIPY v3.1/v2 (zero re-renderu aktów,
  narzędzia v1–v4 nietknięte); mapping klatka→t_sim odtworzony z segmentów
  TEMPO każdego klipu (litera raportów; asercja liczby klatek PASS 4/4:
  353/341/296/341). Podpis stały: „20 neuronów · nie steruje dronem".
  **AKT 3 celowo BEZ nakładki:** NCP tam leci (controller `net`), ale po
  REFUSE(POS) steruje OSŁONA (zejście D5) — pas sieci sugerowałby widzowi
  sterowanie siecią podczas manewru osłony.
- **AKT 5 — nowy widok (38.2 s, te same segmenty i kotwice co v4):**
  (1) pierścień PCA z zoomem na medianę projekcji ujęcia + ślad skumulowany
  + ogon 8 s; (2) kompas „kierunek na cel" z lotu obok pierścienia (krążą
  razem); (3) **nakładka dwóch krzywych NA ŻYWO: neuron n0 vs sin(kierunku
  na cel) z lotu — |r| POLICZONA Z TEGO UJĘCIA = 0.96** (atlas 0.95;
  podpis „opisowe"); (4) **„ŻYWA SIEĆ"**: graf 8 wejść (podpisane) →
  20 neuronów (puls) → komenda [vn ve vd] z wartościami; krawędzie =
  top-3 |Wo| per wyjście (struktura stała z wag); (5) sekwencja 4 kroków
  wzorem admisji v3.1 (kotwice: skan / akwizycja 8.9 s / orbita / n0≈sin).
  Kotwica ujęcia bez zmian: p95 1.18·10⁻³ (wypalona); linia twierdzeń
  i napis uczciwości bez zmian (tylko T1/T2, zasada cytowania FREEZE_XAI).
- **Montaż:** `DEMO_C_v5.mp4` **204.2 s** ≤ 240 (akty 1/2/4a/4b z mini-
  mózgiem, akt 3 oryginalny v2, akt 5 v5, plansza v4 bez zmian);
  `DEMO_C_v5_en.srt` (bloki v3.1 + akt 5 + plansza v4); **SHORT:**
  `DEMO_C_v5_SHORT.mp4` 14.1 s = segment pierścienia [6–34]×2 nowym
  widokiem (TEMPO ×2 wypalone). Wideo >25 MB łącznie ⇒ **NA DYSKU**
  (+ kopie na pulpicie), sha256:

| plik (na dysku) | sha256 |
|---|---|
| `results/DEMO_C/DEMO_C_v5.mp4` (204.2 s, 63 MB) | `a5b999bddce4c6731eaa723d3792949ec5009a89aca47c97289a0843152691e4` |
| `results/DEMO_C/DEMO_C_v5_SHORT.mp4` (14.1 s) | `41a82761579ded56a838e5163388eb26d15fe89944751ec5d7dfbc4294316c32` |
| `clips/akt1_v5.mp4` | `27edd74f507d270d79418e87de36f23bc658e1a419805b1e0ed0b695a252bcf9` |
| `clips/akt2_v5.mp4` | `016fa4fa67e95075c3bb45cad092c884db3351383a3251126b1776c28752b63e` |
| `clips/akt4a_v5.mp4` | `eb25a5bbebccba5170360ab2aa9d32bba68de5ab258e4c1ae9ed1b161286f9a6` |
| `clips/akt4b_v5.mp4` | `79a92de2b674174bbbcee4387923d5ee37490c05c0e98712008c3ca7137f092e` |
| `clips/akt5_v5.mp4` (38.2 s) | `c11d3afb4e526cd8eff44302e6b9c1b4ff6be3416ea92fa24c0f12021c0e573f` |

**Narzędzie NOWE:** `tools/democ_overlay_v5.py` `1da85a7c295ae049`
(brain-clip / akt5 / cut; v1–v4 nietykalne). Status v4: pliki wideo v4
zostają na dysku jako historia montażu (sha w dopisku wyżej), do publikacji
idzie v5. **STOP-DEMOC-5.**

### Errata napisu uczciwości v5 (pytanie Olgi na seansie; dopisek append-only)

Napis mini-panelu „20 neuronów · nie steruje dronem" był MYLĄCY (przeczenie
przyklejało się do sieci, a sieć NCP-20 WŁAŚNIE steruje dronem w aktach
1/2/4a/4b i w ujęciu aktu 5 — intencją było: nakładka/panel z repleyu nie
steruje niczym). Poprawione na jednoznaczne: mini-panel „W GŁOWIE SIECI —
ta sieć PROWADZI lot" / „panel = replay zapisu (nie steruje)"; akt 5:
„sieć NCP-20 PROWADZIŁA ten lot; panel aktywacji odtworzony deterministycznie
z zapisu (replay) — sam niczym nie steruje". Pliki v5 PODMIENIONE przed
publikacją (push nie zaszedł); poza napisami zero zmian. Nowe sha256:

| plik (na dysku) | sha256 |
|---|---|
| `DEMO_C_v5.mp4` (204.2 s) | `f437b26a53b887571cd1f7b790a6b5512069e08fa53a047f352179adaef2bb13` |
| `DEMO_C_v5_SHORT.mp4` (14.1 s) | `05a0a935117f7e6ab25cea42cbd7e69412acb46254cfbef4c7e024083641ca1c` |
| `clips/akt1_v5.mp4` | `6e996199d5daab0d…` · `akt2_v5` `2c19dc2c911b51f9…` · `akt4a_v5` `0b0202b00bcefd7e…` · `akt4b_v5` `47840c98e525bb48…` · `akt5_v5` `4202d2cb2db84c21…` |

Narzędzie: `democ_overlay_v5.py` po erracie `ec59c027dd0a338a`.

---

## Akt 6 (v6) „Wiatr" + errata planszy (dopisek po STOP-DEMOC-5; wykonanie PROMPT_DEMOC_V6; wszystko wyżej NIETKNIĘTE)

**Bramka:** origin == HEAD == `cef1e214` (CO-WK3), w korzeniu `ANEKS_WK3-1.md`, byte-check
`f32eb8e7…0550ab` PASS. `origin/master..HEAD` było puste, w porcelain tylko nazwane `??` (wideo, jpg).
Pierwsza próba bramki (przed CO-WK3) zakończyła się STOP §0.1, bez bootów.
Piny w logu każdego bootu: mono_cam `3354ae1e`, x500_base (wind) `13c9174d`, świat `world_wk3_p2`
`e47ef380` (pełne sha), profil FastDDS `a68a450b`. Sonda przed uzbrojeniem PASS 2/2 (15.6 Hz).

**Wybór ujęcia: P2 c04_s01** (cel ruchomy v 0.5, start czołowo 15 m). W nodze WK-III to najczystszy
epizod z c04–c07: track od startu bez utraty, 0% ticków z celem poza kadrem, t_entry 2.46 s, D6 pełny
i ze świadkiem ✓. Komórki c05–c07 miały utratę tracka startowego albo 10–15% ticków z celem poza kadrem.

**Booty 2/≤2. Mapping take → epizod → kryteria** (`s6_wiatr/akt6_werdykty.json`; sędzia
`wk_judge.py` c33c3ff8 = bench_judge 8ec0fcfb + świadek ERRATUM-DMIN obok; k = `wk3_gust.py` 12ea2f2f
z literą P2 `2 0.8 4 30 11`):

| take | boot | epizod | V2′ (dsim/dwall) | breach / REFUSE | D6 pełny | D6 świadek | sweep | d_min | t_entry | frac 6–10 | k (litera) | ujęcie | w montażu |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | take1_c04 | c04_s01 | ✓ 0.950 | 0 / 0 | **✗ c_sweep** | ✗ c_sweep | 570.0° | 6.849 | 2.86 s | 1.00 | 0.490 (−0.8%) | **odrzucone** | nie |
| 2 | take2_c04 | c04_s01 | ✓ 0.951 | 0 / 0 | **✓** | **✓** (odrzuconych 0) | 800.6° | 7.098 | 2.64 s | 1.00 | 0.492 (−0.4%) | **VALID** | **TAK** |

**Lista odrzuconych take'ów: take 1.** Epizod był ważny, ale **D6 FAIL literą sędziego (sweep 570°)**.
Zapisuję to wprost. To nie jest porażka akwizycji: track był ważny przez cały epizod, a od 2.8 s dron
był w fazie ORBIT. Orbita szła jednak wolniej i dwa razy zawróciła: narastający kąt wokół celu po
70 s wyniósł −179° wobec −555° w WK3 p2_b2 tego samego scenariusza. Mediana |v| 1.35 m/s wobec 1.80,
|komendy| 1.60 wobec 2.02.
Czynnika nie przypisuję (n = 1). Różnice reżimu wobec lotów WK-III nazywam:
- zrzut klatek, kamera pełna + świat 10 fps: dsim/dwall 0.950–0.951 wobec 0.9986 w WK-III;
- start epizodu przesunięty o 0.55 s w fazie sinusa porywu (okres 4 s);
- dwa krótkie rendery na sucho overlayu (na boocie WK3) szły równolegle z bootem 1 w fazie przed
  uzbrojeniem i skończyły się ok. 1 min przed startem epizodu (09:34:15 wobec ok. 09:35). Bootu 2
  nie obciążało nic.
Take 2 zrobiono w warunkach identycznych (ten sam scenariusz, driver i zrzut), bez strojenia.
**Wynik reżimu demo pod wiatrem P2: 1/2 epizodów D6.** Linii planszy „15/16" to nie dotyczy, bo ona
cytuje kampanię WK-III, a demo nie jest kampanią. Liczba jest tu jednak zapisana, żeby nie zniknęła.

**Driver `tools/democ_v6_boot.sh` (sha256 `fef9ac92a5a11342…`)** to kopia `democ_v3_boot.sh`
(nietkniętego) z blokiem WK z `wk3_boot.sh` 039e368c (nietkniętego). Pełny diff
(`diff democ_v3_boot.sh democ_v6_boot.sh`), hunki nazwane:
- **H1 nagłówek/użycie:** `1a2,10`, `13c22`.
- **H2 bez BENCH_MANIFEST + H3 katalog s6_wiatr:** `16,18c25,27`, `25c37`.
  H2: manifest domyślny `results/BENCH/scenario_manifest.json`, ten sam co w lotach WK-III.
- **H4 świat + piny WK:** `20c29,32`, `37,38c49,55`. Pin x500_base, katalog meshes i sha świata są
  sprawdzane PRZED cooldownem; rozjazd = STOP.
- **H5 GZ_SIM_RESOURCE_PATH:** `54a72,74`.
- **H6 KIND=democ_v6, bez BENCH_MANIFEST w env:** `57,58c77,78`.
- **H7 blok manifestu `democ_v6` + `wk`:** `127c147`, `129c149`, `131c151`, `136c156`, `141,142c161,166`.
- **H8 etykiety logu democV3→democV6 + samowykluczenie `democ_v6_boot`:** `28c40`, `31,34c43,46`,
  `42c59`, `46c63`, `49c66`, `63c83`, `101c121`, `106c126`, `108c128`, `112c132`, `124c144`, `144c168`,
  `146c170`. Ścieżka `/tmp/pg_democv3_$BN.log` zostaje z kopii (kosmetyka, bez wpływu).

```diff
1a2,10
> # results/DEMO_C/tools/democ_v6_boot.sh — driver bootu AKTU 6 „Wiatr" (PROMPT_DEMOC_V6 §1). KOPIA
> # democ_v3_boot.sh (nietknięty) + blok WK z results/WK3/tools/wk3_boot.sh (039e368c, nietknięty):
> #   (H1) nagłówek/użycie; (H2) bez BENCH_MANIFEST (manifest domyślny = scenariusze P2 nogi WK-III);
> #   (H3) katalog results/DEMO_C/s6_wiatr (§0.3), log democ_v6_monitor.log;
> #   (H4) WORLD=world_wk3_p2 z pełnym sha + pin x500_base (wind) 13c9174d obok pinu mono_cam (rozjazd = STOP);
> #   (H5) prepend GZ_SIM_RESOURCE_PATH na worlds/wind_models (wzór wk3_boot.sh); (H6) KIND=democ_v6;
> #   (H7) blok manifestu democ_v6 + "wk" (sha świata, piny) — litera bloku "wk" z wk3_boot.sh;
> #   (H8) samowykluczenie procesowe / etykiety logu.
> # --- nagłówek kopii (democ_v3_boot.sh) ---
13c22
< # Użycie: democ_v3_boot.sh <BOOT_N> <NAZWA> <EP_IDS_csv> <BENCH_MANIFEST>
---
> # Użycie: democ_v6_boot.sh <BOOT_N> <NAZWA> <EP_IDS_csv>   (np. 1 take1_c04 4)
16,18c25,27
< BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; EPIDS="${3:?EP_IDS}"; BMAN="${4:?BENCH_MANIFEST}"
< OUTDIR="$ROOT/results/DEMO_C/s3_wabik/$NAME"
< MONLOG="$ROOT/results/DEMO_C/s3_wabik/democ_v3_monitor.log"
---
> BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; EPIDS="${3:?EP_IDS}"
> OUTDIR="$ROOT/results/DEMO_C/s6_wiatr/$NAME"
> MONLOG="$ROOT/results/DEMO_C/s6_wiatr/democ_v6_monitor.log"
20c29,32
< WORLD=world_demo_A3
---
> WORLD=world_wk3_p2
> WORLD_SHA_EXPECTED="e47ef38030c5095d9a5f09e86349a07a2aadda5c7ec2c085d906553dcbb179dc"
> WIND_SDF="$ROOT/worlds/wind_models/x500_base/model.sdf"
> WIND_PIN_EXPECTED="13c9174d4195b730e594d2c9b1de9041492885aaffdb1895bbbe787476b7e214"
25c37
< mkdir -p "$ROOT/results/DEMO_C/s3_wabik"
---
> mkdir -p "$ROOT/results/DEMO_C/s6_wiatr"
28c40
<   echo "[democV3 $NAME] GUARD: DEMOC_FASTDDS_PROFILE nieustawiony — ODMOWA" | tee -a "$MONLOG"; exit 5
---
>   echo "[democV6 $NAME] GUARD: DEMOC_FASTDDS_PROFILE nieustawiony — ODMOWA" | tee -a "$MONLOG"; exit 5
31,34c43,46
< [ "$PSHA" != "$PROFIL_SHA16" ] && { echo "[democV3 $NAME] GUARD: profil sha=$PSHA — ODMOWA" | tee -a "$MONLOG"; exit 5; }
< [ -f "$OUTDIR/manifest.json" ] && { echo "[democV3 $NAME] REPO-2: manifest istnieje — ODMOWA" | tee -a "$MONLOG"; exit 4; }
< COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc|framedump' 2>/dev/null | grep -v -e "$$" -e democ_v3_boot -e pgrep)"
< [ -n "$COLL" ] && { echo "[democV3 $NAME] ENV-BLOCK kolizja:" | tee -a "$MONLOG"; echo "$COLL" | tee -a "$MONLOG"; exit 3; }
---
> [ "$PSHA" != "$PROFIL_SHA16" ] && { echo "[democV6 $NAME] GUARD: profil sha=$PSHA — ODMOWA" | tee -a "$MONLOG"; exit 5; }
> [ -f "$OUTDIR/manifest.json" ] && { echo "[democV6 $NAME] REPO-2: manifest istnieje — ODMOWA" | tee -a "$MONLOG"; exit 4; }
> COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc|framedump' 2>/dev/null | grep -v -e "$$" -e democ_v6_boot -e pgrep)"
> [ -n "$COLL" ] && { echo "[democV6 $NAME] ENV-BLOCK kolizja:" | tee -a "$MONLOG"; echo "$COLL" | tee -a "$MONLOG"; exit 3; }
37,38c49,55
< [ "$PIN_GOT" != "$PIN_EXPECTED" ] && { echo "[democV3 $NAME] PIN FAIL model.sdf — STOP" | tee -a "$MONLOG"; exit 6; }
< echo "[democV3 $NAME] PIN OK profil=$PSHA eps=$EPIDS bman=$BMAN" | tee -a "$MONLOG"
---
> [ "$PIN_GOT" != "$PIN_EXPECTED" ] && { echo "[democV6 $NAME] PIN FAIL model.sdf — STOP" | tee -a "$MONLOG"; exit 6; }
> WIND_PIN_GOT="$(sha256sum "$WIND_SDF" | cut -d' ' -f1)"
> [ "$WIND_PIN_GOT" != "$WIND_PIN_EXPECTED" ] && { echo "[democV6 $NAME] PIN FAIL x500_base (wind) got=$WIND_PIN_GOT — STOP" | tee -a "$MONLOG"; exit 6; }
> [ -d "$ROOT/worlds/wind_models/x500_base/meshes" ] || { echo "[democV6 $NAME] brak x500_base/meshes — STOP" | tee -a "$MONLOG"; exit 6; }
> WORLD_SHA_GOT="$(sha256sum "$ROOT/worlds/$WORLD.sdf" | cut -d' ' -f1)"
> [ "$WORLD_SHA_GOT" != "$WORLD_SHA_EXPECTED" ] && { echo "[democV6 $NAME] SHA ŚWIATA FAIL $WORLD got=$WORLD_SHA_GOT — STOP" | tee -a "$MONLOG"; exit 6; }
> echo "[democV6 $NAME] PIN OK mono_cam=${PIN_GOT:0:8} x500_base(wind)=${WIND_PIN_GOT:0:8} świat $WORLD=$WORLD_SHA_GOT profil=$PSHA eps=$EPIDS" | tee -a "$MONLOG"
42c59
< echo "[democV3 $NAME $(date +%H:%M:%S)] cooldown ${rem}s" | tee -a "$MONLOG"; sleep $rem
---
> echo "[democV6 $NAME $(date +%H:%M:%S)] cooldown ${rem}s" | tee -a "$MONLOG"; sleep $rem
46c63
<   else streak=0; echo "[democV3 $NAME $(date +%H:%M:%S)] brudny: $(head -1 /tmp/pg_democv3_$BN.log)" >> "$MONLOG"; fi
---
>   else streak=0; echo "[democV6 $NAME $(date +%H:%M:%S)] brudny: $(head -1 /tmp/pg_democv3_$BN.log)" >> "$MONLOG"; fi
49c66
< echo "[democV3 $NAME $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"
---
> echo "[democV6 $NAME $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"
54a72,74
> # prepend modelu z enable_wind (blok WK z wk3_boot.sh; gz_env.sh dopisuje stock PO naszym)
> export GZ_SIM_RESOURCE_PATH="$ROOT/worlds/wind_models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"
> echo "GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH" > "$OUTDIR/.gz_resource_path"
57,58c77,78
< env FLIGHT=bench CONTROLLER=net_fantom NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=1 KIND=democ_v3 \
<   BENCH_MANIFEST="$BMAN" BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPIDS" \
---
> env FLIGHT=bench CONTROLLER=net_fantom NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=1 KIND=democ_v6 \
>   BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPIDS" \
63c83
< echo "[democV3 $NAME] run_boot pid=$BOOT" | tee -a "$MONLOG"
---
> echo "[democV6 $NAME] run_boot pid=$BOOT" | tee -a "$MONLOG"
101c121
<   echo "[democV3 $NAME] przed uzbrojeniem: bridge=$BR percep=$PP cam=$FD world=${WR:-brak} filmbr=${FBR:-brak} — sonda 35 s" | tee -a "$MONLOG"
---
>   echo "[democV6 $NAME] przed uzbrojeniem: bridge=$BR percep=$PP cam=$FD world=${WR:-brak} filmbr=${FBR:-brak} — sonda 35 s" | tee -a "$MONLOG"
106c126
<   echo "[democV3 $NAME $(date +%H:%M:%S)] sonda preflight rc=$SONDA_RC (0=PASS)" | tee -a "$MONLOG"
---
>   echo "[democV6 $NAME $(date +%H:%M:%S)] sonda preflight rc=$SONDA_RC (0=PASS)" | tee -a "$MONLOG"
108c128
<     echo "[democV3 $NAME] SONDA FAIL — boot NIE uzbraja się" | tee -a "$MONLOG"
---
>     echo "[democV6 $NAME] SONDA FAIL — boot NIE uzbraja się" | tee -a "$MONLOG"
112c132
<   echo "[democV3 $NAME] topic kamery nie wstał — kill" | tee -a "$MONLOG"
---
>   echo "[democV6 $NAME] topic kamery nie wstał — kill" | tee -a "$MONLOG"
124c144
< echo "[democV3 $NAME $(date +%H:%M:%S)] wrapper rc=$RC sonda_rc=$SONDA_RC" | tee -a "$MONLOG"
---
> echo "[democV6 $NAME $(date +%H:%M:%S)] wrapper rc=$RC sonda_rc=$SONDA_RC" | tee -a "$MONLOG"
127c147
< python3 - "$OUTDIR" "$SONDA_RC" "$PIN_GOT" <<'PY'
---
> python3 - "$OUTDIR" "$SONDA_RC" "$PIN_GOT" "$WORLD" "$WORLD_SHA_GOT" "$WIND_PIN_GOT" <<'PY'
129c149
< outdir, src, pin = sys.argv[1:4]
---
> outdir, src, pin, wk_world, wk_world_sha, wk_wind_pin = sys.argv[1:7]
131c151
< m = json.load(open(mp)) if os.path.exists(mp) else {"kind": "democ_v3", "armed": False}
---
> m = json.load(open(mp)) if os.path.exists(mp) else {"kind": "democ_v6", "armed": False}
136c156
< m["democ_v3"] = {"pin_mono_cam_model_sdf": pin,
---
> m["democ_v6"] = {"pin_mono_cam_model_sdf": pin,
141,142c161,166
<                  "nota": "AKT 4: jeden obiekt w swiecie (scenariusz wabika grany torem intruza, "
<                          "litera WABIK S2); klasyfikator wabik_sig v1 475c972e POSTHOC — nie steruje"}
---
>                  "nota": "AKT 6 Wiatr: scenariusz P2 nogi WK-III (manifest domyslny), swiat world_wk3_p2, "
>                          "NCP net_fantom FEED=V2, framedump cam pelne + swiat 10 fps"}
> m["wk"] = {"world": wk_world, "world_sha256": wk_world_sha,
>            "pin_x500_base_wind_model_sdf": wk_wind_pin, "pin_mono_cam_model_sdf": pin,
>            "gz_resource_path": open(os.path.join(outdir, ".gz_resource_path")).read().strip()
>                                if os.path.exists(os.path.join(outdir, ".gz_resource_path")) else None}
144c168
< print(f"[democV3] manifest: sonda_rc={src}")
---
> print(f"[democV6] manifest: sonda_rc={src}")
146c170
< echo "[democV3 $NAME] DONE rc=$RC → $OUTDIR" | tee -a "$MONLOG"; exit "$RC"
---
> echo "[democV6 $NAME] DONE rc=$RC → $OUTDIR" | tee -a "$MONLOG"; exit "$RC"
```

**Overlay `tools/democ_overlay_v6.py` (sha256 `25bd3f5177b14d9d…`)** to NOWY plik. Importuje tylko do
odczytu `democ_topdown.Panel`, helpery v2, mini-mózg v5, `xai_replay` ac9551ab i `wk2_k.load` 09e4b440.
Klatki aktu to tor v2 1:1: panel taktyczny + HUD + kamera ×2 NN, ramki det_v2 wyłącznie z percep_feed.
Do tego mini-mózg „W GŁOWIE SIECI — ta sieć PROWADZI lot / panel = replay zapisu (nie steruje)".
**Kotwica replayu tego ujęcia** (asercja, próg 1e-2): p50 6.11·10⁻⁴, p95 **1.16·10⁻³**,
max 2.08·10⁻³ m/s (1430 ticków, 1415 inferencji). Elementy §2:
1. **Strzałka wiatru** na panelu (prawy dolny róg, poza R_E). Liczona z **litery świata** wzorem
   z `wk3_gust.py`: |w| = 2(1 + 0.8 sin(2πt/4)), θ = 30° sin(2πt/11), w_NED = (|w| sin θ, |w| cos θ),
   t = t_sim. Dron odtworzył tę literę w WK-III (RAPORT_WK3_S1 §2). Pokazuje aktualne |w| i θ oraz
   podpis stały §2 verbatim + „strzałka = dokąd wieje".
2. **Przechył z zapisu lotu:** vehicle_attitude ulogu, acos(R[2,2]), wyłącznie w oknie epizodu
   (lekcja ANEKS_WK3-1 §3). Na ekranie bieżący kąt i „maks. w epizodzie dotąd". W tym ujęciu
   p50 8.2°, maks. **20.0°** w epizodzie. W samej orbicie wg wk3_gust 8.2 / 13.7 / 16.4°.
3. **Pasek porywu:** |w|(t) z litery, ostatnie 20 s, linie 0.4/2.0/3.6, znacznik „teraz".

Napis uczciwości §2 jest wypalony przez cały akt (pas nad kamerą). Napisy narracyjne idą verbatim
z §2, w kolejności 0–8 / 8–17 / 17–(koniec−9) / ostatnie 9 s. Napis „orbita trzyma: dystans
6–10 m przez całe okno" potwierdza sędzia: frac 6–10 = 1.00, d_min 7.10. „Odporny na wiatr" nie
pada nigdzie. **Segmenty tempa:** 0–8 s ×1 / 8.1–64 s **×2** (plakietka „TEMPO ×2") / 64.1–72 s ×1.
Okno kończy się 0.6 s przed końcem epizodu, zegar epizodu jest ciągły i wypalony. Akt trwa
**44.1 s**, klatki kamery 441/441.
**Poprawka w toku (nazwana):** cv2 nie renderuje „·", więc stopka panelu `democ_topdown`
(„panel taktyczny (GT) ?? siatka 5 m", tak samo w aktach 1–2 v2) jest w akcie 6 zamalowana
i napisana ponownie przez PIL. Akty 1–5 zostają bez zmian.

**§3 errata planszy (obowiązkowa).** Linia v3/v4 „Wabiki: rozpoznawane po zachowaniu — zero
fałszywych alarmów w pomiarach." była nadmiarowa. Zero dotyczy wyłącznie celów ATAKUJĄCYCH:
0/3 w locie (RAPORT_WABIK_S2) i 0 w 26 wariantach (WABIK-II). Na 115 zwykłych lotach NULL
zamrożona reguła kończy z etykietą w **13** (**FREEZE_WABIK**: NULL@12 — 23/115 ever / 13/115
końcowa; wolne krążące cele v = 0.5 to granica nierozróżnialności). **Plansza v6** to plansza v4
z linią FROZEN §3 verbatim. Linię złamano na dwa wiersze bez zmiany słowa (inaczej przekracza
szerokość kadru). Przed wierszem zamykającym dochodzi linia „Wiatr zmienny do 3.6 m/s na kamerze:
15/16 misji." (WK-III: P1 8/8 + P2 7/8). Tak samo poprawiony blok planszy w `DEMO_C_v6_en.srt`.
Wersje v3–v5 na dysku zostają z linią sprzed erraty jako historia montażu. **Do publikacji
idzie v6.**

**§4 montaż:** `DEMO_C_v6.mp4` **248.3 s** ≤ 250. Składa się z v5 po erracie (sha `f437b26a…`,
sprawdzone) bez planszy, 195.2 s, + akt 6 44.1 s + plansza v6 9 s. Format 1920×1080@10, tor cv2 mp4v
(odchylenie jawne jak w v1–v5: ffmpeg nie istnieje). `DEMO_C_v6_en.srt` to NOWY plik: bloki v5 bez
planszy + 4 bloki aktu 6 + plansza v6. SHORT v6 nie powstał (opcjonalny). Wideo ma > 25 MB, więc
zostaje **NA DYSKU** (kopie na pulpicie jak przy v5). sha256:

| plik (na dysku) | sha256 |
|---|---|
| `results/DEMO_C/DEMO_C_v6.mp4` (248.3 s, 79 MB) | `5033018bf7e6f1b87d8efbac99182fee9f29a0e4018b0f68c9e510fe4f3336b6` |
| `results/DEMO_C/clips/akt6_v6.mp4` (44.1 s, 17 MB) | `bfca966b4255f32a37f0d251076bd994ac114db65d6321378ccf4baa2a3bfab8` |
| `results/DEMO_C/DEMO_C_v6_en.srt` (w commicie) | `885dbb1c8a9aeb47f0f124264cc5e0da69163f122cf96f5cd6f283b2fba354be` |

**W commicie:** `tools/democ_v6_boot.sh`, `tools/democ_overlay_v6.py`, `DEMO_C_v6_en.srt`,
`s6_wiatr/` (manifesty z blokami `democ_v6` / `wk`, demo, trace, gt_intruder, percep_feed,
frames_index, sondy; boot.ulg wg gitignore, ulog_sha w manifeście), `judge_take{1,2}.json`,
`kgust_take{1,2}.json`, `akt6_werdykty.json`, logi drivera, ten dopisek. Klatki jpg i mp4
zostają na dysku (celowe `??`). Edycje istniejących plików: wyłącznie ten dopisek (append-only).
**Push = Olga („wypchnięte"). CC przed publikacją weryfikuje kryteria i k z repo oraz ogląda v6
z załącznika.** **STOP-DEMOC-6.**
