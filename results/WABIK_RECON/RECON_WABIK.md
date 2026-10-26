# RECON_WABIK — recon pozycji WABIKI / DALEKI WZROK (rozpoznanie wabika + detektor-v3 + manewrujący cel) — STOP-WABIKR

CC · 26.10.2026 · wykonanie PROMPT_WABIK_S0. **Zero bootów, zero SITL, zero
treningu, zero edycji istniejących plików**; narzędzia NOWE w
`results/WABIK_RECON/tools/` (wabik_r2 / wabik_r4), dane wyłącznie z istniejących
artefaktów (demo.jsonl 3 kampanii × oba ramiona, manifest ławki, litera kodu).
Czeka decyzja CC: **PRE_WABIK dla wybranej ścieżki ALBO aneks odraczający**.

**WYNIK GŁÓWNY (uprzedzając szczegóły):**

1. **Instancjacja wabika jest TANIA i nie dotyka niczego zamrożonego:** intruz
   żyje jako spawn RUNTIME (EntityFactory) modelu-wizualiów bez fizyki, pozą
   steruje zewnętrzny pusher — druga instancja pod nazwą „wabik" + własny
   pusher-kopia + własny plik trajektorii to komplet; world_hash, bench,
   manifest FROZEN — nietknięte (§R1, tabela dróg).
2. **Baseline NULL sygnatur policzony (263 epizody, oba ramiona):** najsilniejszy
   kandydat na dyskryminator to **„czy track schodzi pod 5 m"** (cele poważne
   v=1.0: 88/90 schodzi; v=0.5: 61/89; **v=0: 0/84 — darmowy test FP złapał
   klasę stacjonarną** ⇒ klasyfikacja musi być warunkowa na ruchu). Krzywizna
   NIE separuje (dzisiejsze cele SAME skręcają skokowo między segmentami:
   course_rate_p95 pool p50=281°/s), a kurs tick-po-ticku jest zdominowany
   szumem estymaty (B: ~2855°/s przed wygładzeniem) — cechy wymagają okna ≥1 s.
3. **Manewr NIE obniża sufitu TRANSIT — twierdzenie formą zamkniętą:** dla
   |v|≤1 zachodzi |d dh/dt|≤1, więc zejście 15→5 m trwa ≥10.0 s — prosta
   radialna siatki JEST najgorszym przypadkiem czasowym; każdy manewr
   wchodzący pod 5 m WYDŁUŻA okno admisji (cięciwa b=5: 34.6 s; loiter: całe
   110 s), a „obniżyć" można wyłącznie nie wchodząc pod 5 m — wtedy d_min=b≥5
   i separacja D6 trzyma bez akwizycji: groźbą przestaje być tor, zostaje
   ROZPOZNANIE (dokładnie liga tej pozycji).
4. **Punkt odroczenia NIE zachodzi** — ścieżka (i) sygnatura-desk kosztuje
   0 bootów (baseline NULL już jest), ścieżka (iii) wabik-w-świecie nie dotyka
   zamrożonych. Rekomendacja kolejności w §R6.

## §0. Bramka wejścia — PASS

`git fetch` → origin/master = **2bd041d2 (STOP-DEMOC-2)** ✓ · `origin/master..HEAD`
puste ✓ · porcelain czysty (poza celowymi `??` wideo/klatek DEMO_C nazwanymi
w RAPORT_DEMO_C) ✓. FROZEN wykonaniem: piny 5/5 (SHIELD FROZEN True), certy 9/9;
sędzia 8ec0fcfb · bench 05137098 · fantom_scan e435ed7e · rejestr 87203d29 ·
ncp 0337d5ea · FREEZE_DET (det_v2.pt 775ead15, percep_proc 38a3a765,
feed_registry ee1481f9, **det_labels 8f7430cd**, **det_replay de0feb37**) ·
**FREEZE_PERC2_OPS** (sonda 8df528bb, profil a68a450b, pin model.sdf 3354ae1e…).
**Zapis do raportu (warunek z CO-PERC2): każdy przyszły boot tej nogi lata
w reżimie OPS** (checklist hosta + pin model.sdf + profil FastDDS + sonda
kadencji przed uzbrojeniem). Reguła erratum obowiązuje (dystanse z manifestu,
świadek obok — w tym recon rachunki sędziowane nie występują; cechy R2 liczone
ze strumienia tracka, nie z GT). **Kolizja nazwy „WABIK": brak w kodzie**
(wzmianki wyłącznie w aneksach/KIERUNKACH/RECON-ach jako słowo); rekomendacja:
env `WABIK_*`, katalog `results/WABIK/`.

## §R1. Wabik w świecie — instancjacja (litera)

**Jak dziś żyje intruz:**
- **Model:** `r02/intruder_model.sdf` — prymitywy ~2.4 m span, grafit, 
  **`<static>true</static>`, wyłącznie wizuale (bez kolizji/inercji)** — pozę
  steruje zewnętrzny proces (nagłówek pliku, :1-8).
- **Spawn: RUNTIME, nie świat** — `gz service /world/$W/create` EntityFactory
  z `sdf_filename=r02/intruder_model.sdf, name="intruder"`
  (harness/run_boot.sh:122-124, przy INTRUDER=1). Plik świata NIE zawiera
  intruza ⇒ **world_hash (hash worlds/*.sdf) jest NIEWRAŻLIWY na spawny
  runtime** — drugi obiekt NIE zmienia ery porównywalności.
- **Ruch:** bench_flight startuje podproces `harness.intruder_motion`
  (bench_flight.py:228-232), który czyta manifest (`--manifest`,
  intruder_motion.py:122-127) i pcha `set_pose` @20 Hz wg
  `position_at(ep, t_rel)` (interpolacja LINIOWA po segmentach —
  bench/scenarios.py:87-99); GT = poza ZASTOSOWANA z pose/info do
  gt_intruder.jsonl.

**Tabela dróg drugiego obiektu latającego:**

| droga | jak | dotyk zamrożonych | koszt | nota |
|---|---|---|---|---|
| **(a) druga instancja tego samego modelu** | spawn EntityFactory `name="wabik"`, ten sam sdf; NOWY pusher `wabik_motion.py` (wzór intruder_motion: set_pose 20 Hz + log cmd/applied) z WŁASNYM plikiem trajektorii | **ŻADEN** (world_hash bez zmian; bench/manifest/harness nietknięte; sędzia liczy separację wyłącznie vs intruz — wabik poza werdyktem, rola = test FP percepcji/sygnatury, nazwane) | 1 nowy tool + driver-kopia | wabik WIZUALNIE IDENTYCZNY — rozróżnialny wyłącznie zachowaniem (czysta liga R2) |
| **(b) odrębny wizualnie** | NOWY własny sdf (wzór intruder_model: prymitywy, inna sylwetka/rozmiar — np. płatowiec/balon), spawn jw. | ŻADEN (nowy plik) | +1 plik sdf vs (a) | assety PX4 gz (rc_cessna, standard_vtol…) istnieją, ale niosą pluginy/fizykę — czyściej własne wizualia; otwiera pytanie o korpus 2-klasowy (R3) |
| **(c) edycja świata** | wpis w worlds/*.sdf | **world_hash ZMIENIONY = nowa era porównywalności** (każdy manifest kampanii niesie world_hash adc91803…) | — | **NIE-droga: zbędna** — spawn runtime wystarcza; wymieniona dla kompletności |

**Scenariusze manewrowe — droga ADDITIVE bez dotyku kodu:** bench czyta manifest
z env `BENCH_MANIFEST` (bench_flight.py:53), intruder_motion z `--manifest`
(:122) — **nowy PLIK manifestu** (istniejący FROZEN nietknięty) z segmentami
w ISTNIEJĄCEJ semantyce (t0,t1,x0,y0,heading,v — position_at liniowe) wystarcza:
łuk/zygzak/loiter aproksymowane POLILINIĄ, zero zmian w position_at/intruder_motion.

## §R2. Sygnatura ruchu — dyskryminator + BASELINE NULL (`r2_null.json`, 263 epizody)

**Cechy liczalne ONLINE** (wyłącznie ze strumienia feedu: demo.jsonl
trk_pos_ned/track_valid; zero GT w cechach; okno różnicowe 1.0 s): prędkość
radialna do home (v_rad), tempo zbliżania (frac_closing, próg 0.3 m/s), czas
w pasie [5,18] i w strefie <18 m, moduł prędkości, **minimalne dh tracka**
(dh_min_track), zmienność kursu (course_rate — na kursie WYGŁADZONYM oknem 1 s,
próbkowanie ≥0.5 s). **Reakcja na manewr obrońcy = cecha interakcyjna —
nieliczalna z dzisiejszych logów (nazwana, nieobecna).**

**Baseline NULL (pula V2+B, 3 kampanie; per ramię i kampania w JSON):**

| cecha | p5 | p50 | p95 |
|---|---|---|---|
| v_rad_p50 [m/s] | −0.271 | 0.004 | 0.289 |
| course_rate_p95 [°/s] | 39.8 | 281.3 | 336.8 |
| frac_closing | 0.003 | 0.376 | 0.498 |
| t_in_band_s | 42.6 | 60.5 | 73.1 |
| t_in_zone_s | 57.4 | 72.0 | 74.3 |
| speed_p50 [m/s] | 0.068 | 0.939 | 1.262 |
| dh_min_track [m] | 0.06 | 4.13 | 14.42 |

**Odczyty uczciwe:** (1) **krzywizna NIE separuje** — generator siatki skręca
SKOKOWO między segmentami (scenarios.py:55-66), więc null ma wysokie
course_rate_p95; klasyfikator „wabik bo manewruje" FP-owałby na dzisiejszych
celach poważnych. (2) Kurs tick-po-ticku jest ZDOMINOWANY szumem estymaty
(ramię B przed wygładzeniem: p50 ~2855 °/s dla celów lecących prosto) — każda
cecha kątowa wymaga okna ≥1 s. (3) **Najsilniejszy kandydat: zejście pod 5 m**
— v=1.0: 88/90 epizodów schodzi, v=0.5: 61/89, **v=0: 0/84** ⇒ darmowy test FP
złapał klasę stacjonarną siatki: dyskryminator musi być WARUNKOWY
(ruchomy ∧ nie schodzi ∧ krąży w strefie ⇒ wabik-kandydat; stacjonarny = osobna
klasa). (4) Cechy całoepizodowe słabo separują też dlatego, że cele poważne PO
dojściu do centrum również krążą (v_rad_p50≈0) — sygnatura powinna patrzeć na
okno PRZED pierwszym zejściem pod 5 m. **Gdzie żyłaby klasyfikacja:** NOWY
moduł obok percepcji — ramię additive w rejestrze feedów (wzór `_mk_v2`,
feed_registry.py:36-53), konsumujące ten sam strumień trk; zarys, zero budowy.

## §R3. Daleki wzrok (detektor-v3) — wycena przypięta

- **Kolekcja 15–40 m:** scenariusze kolekcyjne w driver-kopii (bez sędziego;
  wzór detS1_boot FROZEN a7313b3c w FREEZE_DET); koszt wzorcem ery DET:
  **12 bootów → 8 036 klatek** ⇒ na siatkę dystansów 15–40 m × azymuty przy
  hover: **~4–6 bootów** (zawis + cel stacjonarny na siatce Z — ekspozycja
  kontrolowana; przypomnienie z RECON_PERC2 §R2: w locie bojowym korpus
  ekspozycji kończy się na ~16 m, kolekcja MUSI wystawić dystanse jawnie).
- **Taśma etykiet na dystansie — litera:** det_labels (FROZEN 8f7430cd)
  projektuje box z GT pinhole'em `w_px = FX·W_REAL/Z` (det_labels.py:44-60);
  `z_max` to PARAMETR konstruktora/CLI (det_labels.py:86-128, `--z-max`
  domyślnie 60) — **działa na każdym Z bez zmian**.
- **Trening:** v8n pod NOWĄ nazwą **det_v3** (receptura FROZEN FREEZE_DET
  §runtime jako wzór verbatim; precedens kosztu 0.733 h).
- **Ewaluacja PRZED jakimkolwiek lotem:** det_replay (FROZEN de0feb37)
  + bramka T wzór DET; **regresja na starym korpusie ZABRONIONA progiem**.
- **Decyzja klasowa (uzależniona od R1):** droga (a) wabik identyczny ⇒ v3
  zostaje **1-klasowy** (czysty zasięg), rozróżnienie w całości behawioralne
  (R2); droga (b) ⇒ otwiera się pytanie o korpus 2-klasowy (druga klasa
  wymaga klatek wabika w kolekcji). Uwaga ortogonalności: dla rozpoznania
  wabika drogą (a) v3 NIE jest potrzebny — v3 adresuje daleki wzrok/sufit.
- **Poza ligą (litera z PERC2):** rozdzielczość sensora i FX=270 nietykalne
  (mono_cam/model.sdf pod pinem 3354ae1e; intrinsics w r02/mti.py:18-20).

## §R4. Manewrujący cel — generator i arytmetyka sufitu (`r4_rezydencja.json`)

**Generator dziś:** prosta radialna w PIERWSZYM segmencie (start r=15>14 ⇒
heading na home, scenarios.py:52-54), potem segmenty losowe liniowe o stałym
v (scenarios.py:55-66); position_at = interpolacja liniowa (87-99). Droga
additive do manewrów: §R1 (nowy plik manifestu + polilinie).

**Arytmetyka rezydencji w pasie admisji [5,18] m (v=1.0; baseline 10.0 s):**

| rodzina | parametr | rezydencja [s] | nota |
|---|---|---|---|
| prosta radialna (siatka) | — | **10.0** | minimum; litera TRANSIT |
| **DOLNA GRANICA (twierdzenie)** | dowolny tor \|v\|≤1 | **≥10.0** | \|d dh/dt\| ≤ \|v\| ≤ 1 ⇒ 15→5 m trwa ≥10 s |
| styczny przelot (cięciwa) | b=5/8/12/15/17 m | 34.6/32.2/26.8/19.9/11.8 | d_min=b≥5 ⇒ **pod 5 m nie wchodzi — D6-separacja niezagrożona bez akwizycji** |
| łuk (ogr. krzywizna) | R_c=5/10/20 m | ≥10.0/15.7/15.7 | łuk tylko wydłuża |
| loiter na promieniu | r0∈[5,18] | cały epizod (110 s) | okno admisji NIEOGRANICZONE |
| zygzak \|v\|≤1 | dowolny | ≥10 + wydłużenie | postęp radialny ≤ v |

**Wniosek:** manewr może sufit TRANSIT wyłącznie PODNIEŚĆ (dłuższe okna) albo
uczynić bezprzedmiotowym (nie wchodzi pod 5 m ⇒ separacja trzyma; zagrożeniem
zostaje samo rozpoznanie zamiaru). **Co kampanie już dowiodły:** orbity
trzymały na celach RUCHOMYCH radialnych v≤1.0 (DET S4/AKW S3/FANTOM S2 + S2
PERC2 — pościg i orbita po akwizycji, d_min 4.9–6.9 na kontrolach).
**Niezmierzone:** zmiana kursu celu POD orbitą (reakcja egzekutora orbity na
manewr śledzonego celu) — wymaga lotów; nazwane jako pomiar ścieżki (iii).

## §R5. Granica zakresu (guard)

Ta noga = **ROZPOZNANIE** (percepcja na dystansie + sygnatura ruchu). Warstwa
DECYZJI/EKONOMII odpowiedzi — czego NIE ścigać, priorytety przy wielu celach,
koszt energetyczny odpowiedzi — to **OSOBNA pozycja katalogu:
„ODPOWIEDŹ-EKONOMIA (decyzja wielocelowa)"**; trigger: po zmierzonym
rozpoznaniu sygnaturą w locie ALBO przed jakimkolwiek roszczeniem wielocelowym.
NIE otwierana tym reconem (reguła: domykanie nad mnożeniem).

## §R6. Wycena ścieżek + rekomendacja

| ścieżka | booty | dotyk zamrożonych | co daje / czego NIE dowodzi |
|---|---|---|---|
| **(i) sygnatura-desk-first** | **0** | żaden | DAJE: baseline NULL (ten recon, 263 epizody), progi wstępne klasyfikatora warunkowego (ruch ∧ dh_min ∧ okno-przed-zejściem), darmowy test FP (klasa v=0 złapana już teraz); NIE dowodzi: TP na wabiku (w danych nie ma ani jednego wabika), reakcji na manewr obrońcy |
| **(ii) v3-kolekcja** | 4–6 kolekcyjnych (zero werdyktowych) + trening + offline | żaden (nowe pliki; det_v3 nowa nazwa; bramka T przed lotem) | daleki wzrok >15 m (adres sufitu TRANSIT przez wcześniejszą akwizycję), substrat pod przyszłe 2-klasowe; materiał demo |
| **(iii) wabik-w-świecie + manewry** | smoke 1 + testy 2–4 (reżim OPS) | żaden (spawn runtime, nowe pliki, nowy manifest additive) | TP sygnatury na realnym wabiku, FP percepcji na drugim obiekcie, pomiar „manewr pod orbitą" (§R4-niezmierzone); materiał demo (dwa obiekty w kadrze) |

**Kolejność rekomendowana:** **(i) → (iii) → (ii)**: (i) jest skonsumowane tym
reconem (NULL gotowy); (iii) jako pierwsza sesja lotna nogi — 3–5 bootów kupuje
jedyne, czego desk nie da (TP wabika + manewr pod orbitą), na drodze (a) bez
dotykania czegokolwiek; (ii) równolegle/następnie na trigger dalekiego wzroku
(ortogonalne do rozpoznania przy drodze (a)). **Propozycja sufitu bootów nogi:
≤32** (smoke 1 + testy ≤4 + kolekcja ≤6 + ewentualna kampania werdyktowa 24+3
TYLKO osobną decyzją — nieprekomitowana). **Punkt odroczenia z nagłówka: NIE
zachodzi** (ścieżki (i)/(iii) mieszczą się w skali bez nieodwracalnego dotyku
zamrożonego świata/bencha; (c)-edycja świata nazwana jako NIE-droga).

## Artefakty

`results/WABIK_RECON/`: **RECON_WABIK.md** (ten plik) · `r2_null.json`
(263 epizody: cechy per epizod + agregaty p5/p50/p95 per pula/ramię/kampania) ·
`r4_rezydencja.json` (twierdzenie + tabela rodzin) · `tools/wabik_r2.py` ·
`tools/wabik_r4.py`. **Zero bootów. Push = Olga („wypchnięte" — CC czyta
z repo).** Po STOP: CC pisze PRE_WABIK (progi dwuwarstwowe wzór FANTOM/PERC2,
śmierć prereg, predykcje-wskaźniki, jednostki jawne, ewaluacja offline przed
lotami, **reżim OPS w każdym boocie**) ALBO aneks odraczający. **STOP-WABIKR.**
