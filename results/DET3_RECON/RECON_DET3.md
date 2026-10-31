# RECON_DET3 — recon pozycji PERCEPCJA-II (iii) „daleki wzrok / detektor-v3" — STOP-DET3R

Egzekutor · 31.10.2026 · wykonanie PROMPT_DET3_S0. **0 lotów sieci, 0 treningu, 0 edycji
istniejących plików; nowe pliki wyłącznie `results/DET3_RECON/**`.** Sonda R4: **0 bootów** (decyzja Olgi,
§R4). FROZEN importowane READ-ONLY albo uruchamiane bez zmian
(det_replay de0feb37 jako subprocess; det_labels 8f7430cd, r02/mti.py 0889ab39,
poscig_recon, coverage_real jako importy).

**WYNIK GŁÓWNY:**

1. **R1 — zasięg NIE jest wąskim gardłem obecnej siatki (do 14.9 m, granicy korpusu).**
   Żaden składnik nie gubi celu wcześniej niż przy 14.9 m, gdy porównuje się klatki
   o tym samym czasie od wejścia celu w kadr. Pozorny spadek MTI i `fresh` na 12–15 m
   w tabeli zbiorczej to efekt **pierwszej sekundy po wejściu celu w kadr**: rozgrzewka
   pary MTI (delta 3 + persystencja 3/4) i ENTRY k=3. Przy dt 0–1 s ten sam spadek
   (~50%) jest też na 8–10 m. Przy dt 1–2 s na 12–15 m: YOLO 11/11, MTI(admisja) 10/11,
   fresh 10/11. Kwalifikator: ogon jest cienki — 52 klatki z Z ≥ 12 m z 9 bootów,
   9 klatek z 14–15 m z 3 bootów; **powyżej 14.9 m korpus nie ma ani jednej klatki.**
2. **Detektor widzi cel tam, gdzie misja go traci — pada admisja, nie wzrok.** FANTOM S2 V2,
   48 epizodów, okno przed pierwszą świeżą klatką: top-1 det_v2 na celu w **257/263**
   klatkach rampy skanu (|yaw_rate| > 15°/s) i 89/92 w stare. Na 12–15 m wynik to 93/93,
   na 15–18 m 3/3. Każdy z 6 epizodów T6 miał cel na detektorze w rampie 6–29 s przed
   pierwszą fresh (pierwsze trafienie w rampie 1.08–29.32 s, fresh 19.42–31.10 s).
3. **R3: litera admisji nie zawiera żadnego progu odległości, rozmiaru boxa ani conf,**
   który odrzuci detekcję z 25 m. Jedyny warunek rozmiaru to box zdegenerowany
   w_px ≤ 1 (feed_vision.py:65), a box ma 22.5 px przy 30 m. Detektor-v3 to nowe wagi
   plus **nowe pliki-kopie toru** (det_v2/percep_proc/feed_vision_proc mają det_v2
   wpisany na sztywno), bez zmiany progów admisji.
4. **R5: na obecnej siatce (range0 15 m) daleki wzrok nie zmienia nic.** Okno radialnego
   celu v=1.0 to [0, 10.0 s] przy dowolnym D ≥ 15 m. Daleki wzrok ma sens wyłącznie
   w **nowej rodzinie scenariuszy**: przy range0 25/30 m gwarancję daje D ≥ 18.2 m
   (CH87) / 20.1 m (CH0) dla v=1.0, a dla v=0.5 wystarcza D ≥ 11.6–12.6 m, czyli
   stan dzisiejszy. **Warunkiem jest MTI działające na 20 m, a rachunek idealny mówi,
   że w zawisie MTI z ruchu własnego celu tam nie widzi** (§R2). Empirycznie MTI
   działa dalej, niż mówi ten rachunek, dzięki residuum derotacji (§R2c). Rozstrzygnąć
   to może tylko pomiar.
5. **Wariant A (wskazówka kierunku) jest dźwignią NIEZALEŻNĄ od zasięgu, ale na T6 nie
   konwertuje w obecnym skanie.** Pierwsze trafienie w rampie wyprzedza pierwsze
   trafienie w stare tylko o 0.2–1.9 s, bo rampa przechodzi przez azymut celu tuż przed
   stare. Zysk wymagałby innej choreografii („obrót ciągły do trafienia YOLO"), a to
   jest liga dźwigni TRANSIT R3 (zamknięta sufitem), nie detektora.

## §0. Bramka wejścia — PASS

`git fetch` → origin/master == **3ed3f06b** == HEAD; `origin/master..HEAD` pusty; porcelain
czysty poza nazwanymi `??` (results/DEMO_C/*, sprzed sesji). Sha8 przeliczone i ZGODNE:
det_v2.pt **775ead15** · det_labels **8f7430cd** · det_replay **de0feb37** · make_dataset
**e958cc48** · detS1_boot.sh **a7313b3c** · r02/mti.py **0889ab39** · percep_proc **38a3a765** ·
feed_registry **ee1481f9**. Korpus DET: `labels_set_sha256` w dataset_manifest = **33dbebba**.
Uwaga: sha pliku dataset_manifest.json to 9fe3aae6; 33dbebba to sha zbioru etykiet zapisane
w środku, zgodnie z ANEKS_DET-1:54. BENCH manifest: range0 15.0 / disk_r 18.0 / z_intr 10.0.
**Higiena zegara:** WSL uruchomiony 31.10 15:58; próbnik realtime−monotonic przez 75 s przed
pracą: 0 skoków > 50 ms, dryf 0.000 s. Deskowe części tego reconu nie zależą od zegara.

**Liczność korpusu:** NEW (D01–D12, DET S1) = **6 154** pozytywów (zgodnie z promptem); ALL
(+ stary korpus 2A: A1, A1b, A2, A2b) = 6 502, z czego w replayu 6 499 (3 klatki A1b bez
own_q ±0.1 s, odrzucone przez det_replay). Wszystkie jpg na dysku.

## §R1. Czy zasięg jest wąskim gardłem dziś

**Przyrząd** (`tools/det3_r1.py`): per boot (1) `det_replay.py` de0feb37 BEZ ZMIAN
(subprocess) z det_v2 → per klatka box/conf/mti_ok/fresh/trk_pos_ned (rdzeń FeedVision,
ten sam tor co lot); (2) przebieg MTI-only na tych samych klatkach i pozach: MTITracker
FROZEN (persystencja) + motion_components FROZEN (surowe) + diagnostyka z min_area_px=1
(parametr wywołania). YOLO na celu = środek top-1 w boxie etykiety (det_replay.py:149-157).
MTI ściśle = centroid komponentu w boxie etykiety ±3 px. MTI(admisja) = `mti_ok` lotu
(koincydencja środka ≤ 0.12, r02/config_r02.py:106).
**Kotwica:** D10_c09_s08 (TEST) odtworzony co do liczby: err p50/p95 1.202/1.344, top-1
575/576, identycznie z `results/DET/replay_TEST_v8n_D10_c09_s08.json`.
Agregacja: `tools/det3_r1_agg.py` → `r1/r1_tabela.json`.

**Tabela R1 — korpus NEW (6 154), wszystkie fazy:**

| Z [m] | n (boot) | YOLO top-1 na celu | conf p50 | err fresh p50/p95 [m] (n) | fresh | MTI ściśle (surowe / persyst.) | MTI(admisja) lotu | blob [px] p50 · frakcja <8 px | box etykiety p50 [px] |
|---|---|---|---|---|---|---|---|---|---|
| 6–8 | 1958 (12) | 0.999 | 0.781 | 0.505/1.492 (1958) | 1.000 | 0.715 / 0.701 | 0.970 | 1739 · 0.285 | 89×18 |
| 8–10 | 3986 (12) | 0.998 | 0.783 | 0.562/1.535 (3976) | 0.997 | 0.690 / 0.683 | 0.990 | 1144 · 0.310 | 79×16 |
| 10–12 | 142 (12) | 1.000 | 0.785 | 0.677/1.500 (118) | 0.831 | 0.732 / 0.655 | 0.845 | 905 · 0.268 | 64×13 |
| 12–14 | 43 (9) | 0.930 | 0.744 | 1.172/1.843 (19) | 0.442 | 0.512 / 0.395 | 0.535 | 107 · 0.488 | 54×11 |
| 14–15 | 9 (3) | 0.889 | 0.629 | 1.729/1.730 (4) | 0.444 | 0.889 / 0.667 | 0.667 | 427 · 0.111 | 46×9 |

(0–6 m: 16 klatek, YOLO 1.000. Osobno: TEST/VAL/TRAIN w `r1_tabela.json`. TRAIN to
in-sample dla det_v2. Na TEST c06+c09 YOLO na 12–15 m = 10/11.)

**Faza `approach` (NEW, 206 klatek, cały ogon ≥ 12 m jest w niej: 47/52):** YOLO
0.983/1.000/0.930/0.750 dla 8–10/10–12/12–14/14–15 m; MTI(admisja) 0.933/0.778/0.535/0.750.

**Kontrola czasu od wejścia celu w kadr** (dt = t − pierwsza klatka OK bootu; komórki
yolo · MTI(admisja) · fresh):

| dt | Z 8–10 | Z 10–12 | Z 12–15 |
|---|---|---|---|
| 0–1 s | 16/16 · 12/16 · 8/16 | 44/44 · 22/44 · 21/44 | 37/41 · 19/41 · 13/41 |
| 1–2 s | 32/32 · 32/32 · 30/32 | 23/23 · 23/23 · 22/23 | **11/11 · 10/11 · 10/11** |
| 2–3 s | 23/23 · 22/23 · 23/23 | 6/6 · 6/6 · 6/6 | — |
| ≥ 6 s | 3785/3791 · 3763/3791 · 3791/3791 | 69/69 · 69/69 · 69/69 | — |

Spadek w pierwszej sekundzie jest jednakowy we wszystkich przedziałach Z (MTI 50–75%,
fresh 30–50%). Po pierwszej sekundzie 12–15 m nie odstaje od 8–10 m. 4 chybienia YOLO
przy Z ≥ 12 m przypadają w całości na dt ≤ 0.33 s (D02 ×2, D06, D10; conf 0.34–0.69).
Na całym korpusie chybień jest 11 / 6 499.
**MTI ściśle ~0.7 jest płaskie w Z (6–15 m)**: to cecha definicji, nie zasięgu. Dotknięty
blob ma setki do tysięcy px, co oznacza, że komponent obejmuje sylwetkę i residuum tła.
Po rozgrzewce (dt ≥ 1 s) **żaden blob na celu nie ma 1–7 px** (p10 217–694 px), więc
min_area 8 nie jest ograniczeniem do 15 m.

**WERDYKT R1 (jedno zdanie):** do granicy korpusu 14.9 m **żaden składnik nie traci celu
pierwszy** — YOLO trzyma 0.93/0.89 na 12–14/14–15 m (błędy wyłącznie w pierwszych 0.33 s),
a MTI(admisja) i fresh po pierwszej sekundzie od wejścia celu w kadr trzymają 10/11 na
12–15 m, tak jak na 8–10 m; spadek w tabeli zbiorczej to rozgrzewka toru po wejściu celu
w kadr, nie zasięg; ponad 14.9 m danych nie ma.
**Konsekwencja wg zasady nadrzędnej:** zasięg nie jest problemem obecnej siatki, więc
§R5 dotyczy wyłącznie nowej rodziny scenariuszy (albo wariantu A). Próg literalny promptu
(„oba ≥ 0.9 do 15 m") jest spełniony w ujęciu z kontrolą dt (YOLO 48/52 = 0.92 zbiorczo;
MTI(admisja) 10/11 przy dt 1–2 s). Bez kontroli dt nie jest spełniony dla MTI (0.56 zbiorczo).
Rozstrzygam na korzyść ujęcia z kontrolą, bo kontrast przy dt 0–1 s istnieje także na 8–10 m.

## §R2. Rachunek fizyczny 15–30 m

`tools/det3_r2r5_rachunek.py` → `r2r5_rachunek.json`; kontrast `tools/det3_r2_kontrast.py`
→ `r2_kontrast.json`; koszt inferencji `tools/det3_r2_imgsz.py` → `r2_imgsz.json`.

**(a) Box pinhole** (f 270, W 2.5, H 0.5; det_labels.py:33-34): 15 m **45.0×9.0** · 20 m
**33.75×6.75** · 25 m **27.0×5.4** · 30 m **22.5×4.5** px. Oczekiwania promptu potwierdzone.
Korpus det_v2 najmniejszy box: ~45×9 (14.9 m).

**(b) Ruch pozorny** (para MTI = delta 3 klatki, r02/mti.py:129; Δt = 0.204 s przy 14.7 Hz,
0.6 s przy 5 Hz):

| | 20 m styczny px/kl · px/parę | 30 m styczny px/kl · px/parę | radialny, przyrost na stronę px/parę 20 / 30 m |
|---|---|---|---|
| 14.7 Hz, v=0.5 | 0.46 · 1.38 | 0.31 · 0.92 | 0.086 / 0.038 |
| 14.7 Hz, v=1.0 | 0.92 · 2.76 | 0.61 · 1.84 | 0.17 / 0.08 |
| 5 Hz, v=0.5 | 1.35 · 4.05 | 0.90 · 2.70 | 0.25 / 0.11 |
| 5 Hz, v=1.0 | 2.70 · 8.10 | 1.80 · 5.40 | 0.51 / 0.23 |

**(c) MTI fizycznie — model idealny** (obserwator nieruchomy, derotacja idealna): pasek
różnicy na krawędzi celu ma szerokość przesunięcia d. `MORPH_OPEN 3×3` (r02/mti.py:31) usuwa
struktury węższe niż 3 px, więc warunek widoczności to d ≥ 3 px ∧ h ≥ 3 px. Wysokość nie
ogranicza do **45 m**. Maksymalny zasięg MTI z ruchu własnego celu:

| | styczny | radialny |
|---|---|---|
| 14.7 Hz, v=0.5 | **9.2 m** | 3.4 m |
| 14.7 Hz, v=1.0 | **18.4 m** | 4.8 m |
| 5 Hz, v=0.5 | 27.0 m | 5.8 m |
| 5 Hz, v=1.0 | 54.0 m | 8.2 m |

**Kontrast nie jest ograniczeniem:** na 12–15 m cel stoi na tle nieba (tło p50 213 DN,
kontrast p50 187, p10 111 wobec diff_thr 22). Na 6–10 m tło jest ciemniejsze (80–83),
kontrast p50 37–43, ≥ 22 w 85–90% klatek.
**Konfrontacja z danymi:** model idealny jest za pesymistyczny. Dane go przekraczają:
MTI(admisja) 10/11 na 12–15 m przy dt 1–2 s (faza approach, dron w ruchu), a admisje
kontrolne TRANSIT w zawisie/stare 5 Hz przy dh do 15 m (RECON_TRANSIT §R1 „Kalibracja").
Kanał, który to umożliwia, to **residuum derotacji** (kołysanie zawisu, rozjazd czasu
klatka↔attitude): przesuwa ostry cel na jasnym niebie, a tło nieba, jednolite, nie daje
różnicy. **To oznacza, że MTI na dystansie zależy od mechanizmu, który nie jest ani
zaprojektowany, ani zmierzony w funkcji Z.** RECON_TRANSIT nazwał to „loterią
czołową" (radialna admisja 4/7 przy 5 Hz). Rachunek nie rozstrzyga MTI na 20–30 m;
rozstrzyga pomiar (§R4).
Paradoks kadencji: niższa kadencja zwiększa przesunięcie na parę (5 Hz: 3× więcej px/parę),
ale wydłuża czas do ENTRY k=3 (0.6 s → ~1.8 s). Ten efekt nie wpływa na werdykt, zapisuję go do PRE.

**(d) Koszt inferencji vs imgsz** (det_v2, 200 klatek D10 TEST, RTX 5070 Ti Laptop, GPU
puste ⇒ DOLNA granica czasu w locie; wagi trenowane przy 640, inne imgsz to zero-shot skali):

| imgsz | ms/klatkę p50 / p95 / max | top-1 na celu |
|---|---|---|
| 640 | **5.18** / 13.15 / 18.82 | 200/200 |
| 960 | **8.44** / 14.44 / 28.22 | 200/200 |
| 1280 | **14.41** / 16.29 / 21.60 | 196/200 |

Wszystkie są daleko pod ~60 ms. W locie push_frame (YOLO + MTI + admisja) mierzył 16–20 ms
przy 640 (FREEZE_PERC2_OPS:39), więc przy 1280 przewiduję ~25–30 ms, czyli też poniżej
68 ms. **imgsz nie zabija kadencji.** Kadencję limituje transport DDS (FREEZE_PERC2_OPS),
nie GPU. Eskalacja imgsz 960 jest więc dopuszczalna czasowo. Czasu v8s nie mierzyłem: wagi bazowe
są w .b0deps, ale bez fine-tune (zakaz treningu) dałyby tylko czas, bez czułości.

## §R3. Litera admisji vs statystyka

Pas **[5, 18] m jest progiem EMPIRYCZNYM** (RECON_TRANSIT §R3: „progi EMPIRYCZNE
z kampanii"), nie kodem. Pełna lista warunków w torze detekcja → admisja → kanał:

| warunek | plik:linia | zależy od Z / rozmiaru / conf? | przy 25 m |
|---|---|---|---|
| top-1 po max conf, conf=0.001 (bez progu) | harness/feed_vision.py:107; harness/det_v2.py:6-8; det_replay.py:63 | conf — **brak progu** | przechodzi |
| conf-floor θ_conf | r02/target_channel.py:129 | conf — **nieaktywny** gdy entry_require_mti=True (FeedVision wymusza: feed_vision.py:125-126) | n/d |
| edge-margin ≥ 0.10 | r02/target_channel.py:124; r02/config_r02.py:36 | położenie w kadrze, nie Z | przechodzi |
| koincydencja MTI ≤ 0.12 | r02/target_channel.py:126-128; r02/config_r02.py:106 | pośrednio (czy MTI widzi) | **zależy od MTI** |
| ENTRY k=3, ruch ≤ 0.15 | r02/config_r02.py:27,30 | nie | przechodzi |
| MTI: diff_thr 22, open 3×3, min_area 8, max_area 0.20, persist 3/4 ≤ 0.10 | r02/mti.py:30-40,109 | **fizycznie tak (§R2c)**, literą nie | patrz §R2/§R4 |
| pinhole: odrzuć w_px ≤ 1 | harness/feed_vision.py:65 | rozmiar ≤ 1 px | 27 px, przechodzi |
| REFRESH w oknie predykcji 3.0 m | harness/feed_vision.py:56,202-216 | nie literą; **jitter zasięgu rośnie jak Z²** (σ_Z ≈ Z²/(f·W)·σ_w = 0.93 m/px przy 25 m) | ryzyko, nie odrzut |
| cechy sieci: surowe rel, bez obcięcia | bench/features.py:22-33 | nie | przechodzi (poza rozkładem treningowym NCP — ryzyko konsumenta) |
| percep_proc | harness/percep_proc.py (176 linii) | **zero** progów Z/rozmiaru/conf (grep) | — |

**Werdykt R3:** detektor-v3 **NIE wymaga zmiany progów admisji** (era percepcji bez zmian).
Wymaga natomiast nowych plików toru, nie tylko wag: `harness/det_v2.py:21-22` ma ścieżkę
i sha wag wpisane na sztywno (guard SR-2), a `harness/percep_proc.py:94-97`
i `harness/feed_vision_proc.py:33-34` importują `DetV2`/`feed_sha_v2` po nazwie. Ścieżka bez
edycji to kopie z jedną zmianą: `det_v3.py` (sha v3), `percep_proc_v3.py`,
`feed_vision_proc_v3.py`, nowy `feed_sha_v3`, wpis rejestru additive. Wzór: det_v2 obok
detektora świata.

## §R4. Dane na 15–30 m — projekt i sonda

**STAN SONDY: NIEODBYTA (0/≤2 bootów) — decyzja Olgi 31.10 „STOP bez sondy”.** Powody: R1 rozstrzygnął
zasadę nadrzędną bez lotu, sonda wymagała nowego kontrolera, manifestu i drivera, a §0.3
(`wsl --shutdown` przed każdym bootem) przerywa sesję. Poniżej projekt i predykcja do
wykorzystania, jeśli pozycja zostanie wznowiona.

**Projekt kolekcji (dla S1 i dla sondy):**
- **Manifest NOWY** `results/DET3_RECON/det3_manifest.json` (stary BENCH nietknięty;
  bench_flight czyta `BENCH_MANIFEST`, bench/bench_flight.py:53). Ten sam format epizodu
  (segmenty, `position_at`, bench/scenarios.py:96-110). Intruz na okręgu R ∈ {15, 20, 25, 30} m
  wokół home, z = 10 m, **styczny v=0.5** (heading = bearing ± 90°, odcinki
  odnawiane tak, by |r| ≤ R+0.5), 4 azymuty startowe {0, 90, 180, 270}°. Epizod 60 s;
  przy v=0.5 łuk ma 30 m, czyli 57–115° kątowo, więc tło zmienia się w kadrze.
- **Kontroler NOWY** `r03/controllers/det3_stare.py` (`det3_stare`, wpis rejestru
  `r03/controllers/__init__.py` additive, SR-9): zawis na home (wysokość jak hold
  ławki), yaw = azymut `trk_pos_ned` z **FEED=B** (GT-fed, jak DET S1), zero pościgu,
  |v| ≤ 0.3 m/s na utrzymanie pozycji. Percepcja, admisja, MTI i piny nietknięte; zrzut
  klatek w shadow jak DET S1 (`shadow_feed_live.py --frames-hz 1000`).
- **Driver NOWY** `results/DET3_RECON/tools/det3_boot.sh` = kopia detS1_boot.sh a7313b3c
  z trzema zmianami: CONTROLLER=det3_stare, BENCH_MANIFEST=det3_manifest, OUTDIR pod
  DET3_RECON; reżim OPS (profil a68a450b, sonda 8df528bb przed armed, pin mono_cam 3354ae1e)
  + **próbnik dwuzegarowy** 90 s (realtime−monotonic) z zapisem obu do manifestu bootu.
- **Etykiety:** det_labels 8f7430cd z `--z-max 35` (parametr wywołania, det_labels.py:139).
- **Sonda:** 1 boot = 2 epizody (R=20 i R=30, azymut 0). Miary: cel w kadrze, ile
  pozytywów, rozkład Z, 5 PNG na odległość (`--sample`), **zero-shot det_v2** (top-1 na celu,
  conf, err) i **MTI** (ściśle / admisja / blob px) z `det3_r1.py` bez zmian.
- Wycena S1: 4 R × 4 azymuty = 16 epizodów; ~2 epizody/boot ⇒ 6–8 bootów. Przy
  ~14.7 Hz × 60 s × 16 ≈ 14 000 klatek, z czego ~70% z celem w kadrze ⇒ ~9 000 pozytywów.

**Predykcja przed sondą (zapisana teraz, do rozliczenia):**
- det_v2 zero-shot: top-1 na celu ≥ 0.8 przy 20 m (box 34×7, ~75% najmniejszego boxa
  w treningu), 0.4–0.7 przy 30 m (22×4.5; stride 8 v8n daje ~3×0.6 komórki).
- MTI w zawisie przy 14.7 Hz, v=0.5 stycznie: z ruchu własnego **0** na obu dystansach
  (1.38/0.92 px/parę < 3). Jeśli MTI(admisja) > 0.3, to działa kanał residuum, nie ruch
  celu. To samo w sobie jest wynikiem: admisja na dystansie zależałaby wtedy od kołysania.

## §R5. Co daleki wzrok zmienia w misji

`r2r5_rachunek.json` (arytmetyka okna), `r5_rampa.json` (wariant A, dane FANTOM S2).

**(a) Obecna siatka (range0 15 m):** okno admisji radialnego v=1.0 to **[0, 9.99 s] przy
każdym D ≥ 15 m** (cel startuje na 15 m), przegląd 11.15 s > 9.99 s (RECON_TRANSIT). Daleki
wzrok **nic** nie zmienia; R1 nie wykazał zgubienia celu na 12–15 m, więc nie ma też zysku
„pewniejszej admisji w pierwszych sekundach".

**(b) Nowa rodzina range0 25/30 m (v=1.0 radialnie):** okno [(R0−D)/v, (R0−5.01)/v]:

| R0 \ D | 15 m | 20 m | 25 m | 30 m |
|---|---|---|---|---|
| 25 m | [10.0, 20.0] = 10.0 s ✗ | [5.0, 20.0] = 15.0 s ✓ | 20.0 s ✓ | 20.0 s ✓ |
| 30 m | [15.0, 25.0] = 10.0 s ✗ | [10.0, 25.0] = 15.0 s ✓ | 20.0 s ✓ | 25.0 s ✓ |

✓ = długość ≥ maks. przerwa rewizyty azymutu + stare (CH87: 12.0 + 1.2 = 13.2 s).
Ogólnie **D_min = 5 + v·(G + 1.2)**: v=1.0 → **18.2 m (CH87) / 20.1 m (CH0)**; v=0.5 →
11.6 / 12.6 m (spełnione dziś). **Przy D = 15 m (dziś) nowa rodzina ma ten sam deficyt co
obecna siatka** (okno 10 s); dopiero D ≈ 20 m daje gwarancję. Warunkiem jest działający
MTI na 20 m (§R2c, §R4), bo admisja to struktura ∧ MTI.

**(c) Wariant A — wskazówka kierunku:** dane FANTOM S2 V2 przed akwizycją:

| | rampa (>15°/s) | stare |
|---|---|---|
| top-1 na celu / cel w kadrze | **257/263 (0.977)** | 89/92 (0.967) |
| 12–15 m | 93/93 | 34/34 |
| 15–18 m | 3/3 | — |

Epizody z trafieniem w rampie przed pierwszą fresh: **44/48**. T6 (wszystkie FAIL):
pierwsze trafienie w rampie c08_s03 1.08 · c08_s04 2.48 · c10_s02 9.03 · c11_s02 29.32 ·
c11_s03 12.80 · c11_s04 12.35 s, a pierwsza fresh 19.42–31.10 s. **Detektor widzi; pada
admisja.** Wariant A na T6 w obecnym skanie: trafienie w rampie wyprzedza trafienie
w stare tylko o 0.19–1.85 s (rampa zahacza o azymut celu tuż przed stare), a dla c11 wypada
po t\* (10.75–10.91 s). **Nie konwertuje.** Klasa c08 (cel w stare od 1.3 s, pada MTI czołowe)
w ogóle nie potrzebuje wskazówki. Zysk dawałaby choreografia „obrót ciągły aż do
trafienia YOLO, potem stare": pokrycie FOV 360° przy 60°/s i FOV 99.4° = (360−99.4)/60 =
4.3 s (+ dwell 2.0) wobec 11.15 s. To jednak **liga TRANSIT R3** (choreografia; pozycja
zamknięta sufitem z argumentem „loteria MTI czołowa"), **niezależna od zasięgu**, i nadal
nie usuwa loterii MTI dla celu radialnego.

**Który sens nogi jest wart lotów po R1/R5:** **nie „obecna siatka"** (zero zysku). **Nie
„wariant A jako dalekie widzenie"** (dźwignia jest choreograficzna, nie zasięgowa).
**Ewentualnie „nowa rodzina range0 25/30 m"**, ale tylko jeśli MTI działa na 20 m. Bez tego
detektor-v3 sam nie otwiera okna admisji. Wąskim gardłem całego łańcucha jest **koincydencja
MTI na celu radialnym**, nie zasięg detektora. Ta sama diagnoza co TRANSIT (ii-a).

## §R6. Wycena i śmierci (propozycja dla PRE; rozstrzyga CC/Olga)

- **Śmierć przy biurku (warunek z promptu):** „R1 ≥ 0.9 na 12–15 m dla obu ∧ Olga nie chce
  nowej rodziny scenariuszy". **Pierwszy człon jest spełniony** (z kontrolą dt; §R1).
  Drugi należy do Olgi.
- **Jeśli nowa rodzina TAK:** zanim cokolwiek zostanie zebrane, w kolejności:
  **S0′ = sonda R4** (1–2 booty: MTI i det_v2 zero-shot na 20/30 m w zawisie). Nowa śmierć
  tania i wcześnie: **MTI(admisja) na 20 m < 0.7 ⇒ detektor-v3 bez sensu** (okno
  i tak się nie otworzy; pozycja przechodzi do MTI/choreografii, nie do detektora). Dopiero
  potem S1 = kolekcja ≤ 6 bootów + trening det_v3 (FREEZE_DET: v8n, 640, seed 1, jedna
  eskalacja: imgsz 960 albo v8s) + bramka offline. Proponowane progi: det_v3 ≥ 0.8 na 20 m
  i ≥ 0.6 na 25 m na bootach odłożonych (split po boocie); brak regresji z bliska: T2 pooled
  p95 ≤ 1.365 × 1.10 = 1.50 m na TEST c06+c09, czułość 6–15 m ≥ det_v2 − 0.02 (det_v2
  na TEST: 1.000/1.000/1.000/0.909 dla 6–8/8–10/10–12/12–15). S2 = loty sieci na nowej
  rodzinie ≤ 12 (warunek wejścia: NOWY manifest range0 25/30 m i para odniesienia det_v2 na
  tym samym manifeście). Nazwane ryzyko konsumenta: NCP trenowany na |rel| ≤ ~18 m, a 30 m
  jest poza rozkładem (bench/features.py bez normalizacji zakresu).
- **Budżet:** S0′ 1–2 · S1 6 · S2 ≤ 12 ⇒ ≤ 20; oczekiwane 9–14.
- **Wycena nogi alternatywnej, która trafia w nazwane wąskie gardło** (dla katalogu, nie
  dla tego PRE): MTI czołowe (TRANSIT ii-a) + choreografia „obrót do trafienia YOLO". Obie
  pozycje zamknięte wcześniej; R5c daje im nową liczbę: detektor widzi cel w rampie
  w 97.7% klatek przed akwizycją.

## Pliki (wyłącznie nowe)

- `tools/det3_r1.py`, `tools/det3_r1_agg.py`, `tools/det3_r2_imgsz.py`,
  `tools/det3_r2_kontrast.py`, `tools/det3_r2r5_rachunek.py`, `tools/det3_r5_rampa.py`
- `r1/*.frames.jsonl` (16), `r1/*.replay.json(.replay.jsonl)` (16), `r1/r1_tabela.json`
- `r2_imgsz.json`, `r2_kontrast.json`, `r2r5_rachunek.json`, `r5_rampa.json`
