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
