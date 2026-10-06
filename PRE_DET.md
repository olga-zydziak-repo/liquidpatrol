# PRE_DET — zamrożenie nogi DET (detektor-v2): dane, split, trening, bramki, kampania, śmierć

CC · 06.10.2026 · łańcuch DET (po STOP-DETR, commit 11bf694 na origin — zweryfikowany
przez CC wykonaniem: etykiety 348+153 przeliczone z plików, sweep 10.3% przeliczony
NIEZALEŻNIE z sweep_raw.jsonl [36/348], filtry F1=58/F2=78/F3=153 sumują się do 637,
Z p5/p50/p95 = 6.1/7.9/9.6 m, IoU-tabela zgodna ×4, próbki PNG obejrzane, kanon projekcji
importowany 1:1, commit dotyka wyłącznie results/DET_RECON/**). Dokument przed-pomiarowy:
po ratyfikacji Olgi kryteria są ZAMROŻONE. Sygnały bez numeru wykonawca odrzuca.

## §0. Pytanie nogi i zakres

**Pytanie:** czy detektor DOSZKOLONY na etykietach projekcyjnych z GT (za darmo, bez
ręcznego labelowania) naprawia ogniwo, które 2A wskazała jako limitujące — i czy po tej
naprawie system przechodzi zamrożoną, nielataną kampanię C z PRE_2A (koszt zejścia
z wyroczni na percepcję)?

**Jedna zmiana naraz:** jedyną zmienianą częścią toru percepcji jest DETEKTOR (+ miejsce
wykonania: osobny proces, §6). Admisja D2 (struktura∧MTI, ENTRY k=3), brama REFRESH (N2),
starzenie θ_age, semantyka track_valid>1.0 s ⇒ hover-hold, pinhole f_px=270/W_real=2.5,
kontrakt set_feed — **VERBATIM z FREEZE_2A, zero edycji**. Mechanizmy bezpieczeństwa
zmierzone w C2 (szatkowanie pogoni) są zachowane KONSTRUKCYJNIE, bo to te same bajty.

**Poza zakresem (jawnie):** gimbal/pre-aim; zmiany admisji (w tym próg conf w runtime —
θ* liczony wyłącznie opisowo offline); korpus nieba (jeśli frakcja nieba w dolocie <5%,
każde zdanie bramek niesie kwalifikator „na tle naziemnym"); osłona, sędziowie, wagi
sieci sterującej — nietykalne.

## §1. FROZEN wejściowe

Piny 5/5, certy 9/9, bench_judge 8ec0fcfb, features 9adc1505, ncp 0337d5ea (CONTROLLER
wszystkich lotów nogi), feed_vision acc81df7 (FEED=V zostaje w repo do forensyki, NIE
lata w tej nodze), bench_flight 05137098 (ZERO edycji), percep_judge 363c37b7,
coverage_real 53453371, **det_labels.py 8f7430cd (narzędzie etykiet — FROZEN od teraz;
edycja = STOP-ANEKS)**. Rejestr feedów: wpis FEED=V2 WYŁĄCZNIE additive (klasa SR-9,
wzór rejestru kontrolerów LIQ).

## §2. D1 — Dane

**Korpus istniejący:** 637 klatek / 4 booty 2A (c08, c11) z etykietami z recon
(348 pozytywów + 153 negatywy F3; filtry F1–F4 verbatim z RECON_DET §R2) — wchodzi
WYŁĄCZNIE do TRAIN (uzasadnienie w §3). Decymacja 2 Hz i mieszanka sprzed/po N1 —
odnotowane, akceptowalne dla TRAIN.

**Dolot (sesja S1, SHADOW — lot na FEED=B jak S2, CONTROLLER=net 0337d5ea):**
**12 bootów, po jednym na komórkę, scenariusze BLOKU 2 regułą s = 5 + (idx mod 6):**

| c00_s05 | c01_s06 | c02_s07 | c03_s08 | c04_s09 | c05_s10 |
|---|---|---|---|---|---|
| **c06_s05** | **c07_s06** | **c08_s07** | **c09_s08** | **c10_s09** | **c11_s10** |

Własności reguły (sprawdzone przed zamrożeniem): zero kolizji z korpusem 2A (c08_s03,
c11_s01); **zero przecięcia ze scenariuszami kampanii C (blok 1, s01–s04)** — zbiór
treningowy detektora i loty werdyktowe są rozłączne co do scenariusza; seed niesie
scenariusz (sYY ⇒ seed YY, bench/scenarios.py). Nota: lot scenariuszy bloku 2 nie
narusza świeżości SIECI (sieć zamrożona, niczego się tu nie uczy); świeżość DETEKTORA
niesie split komórkowy (§3).

- Zrzut klatek **PEŁNEJ kadencji 15 Hz** (usunięcie decymacji w NARZĘDZIU-driverze zrzutu;
  run_boot.sh i pliki FROZEN nietknięte). Klatki lokalnie (gitignore), **sha zbioru per
  boot do manifestu** jak S2.
- Ważność per boot: **V2′** + **żywość zrzutu (prereg, klasa V2′): ≥100 klatek zapisanych
  w pierwszych 30 s epizodu**; brak ⇒ boot NIEWAŻNY instrumentowo, diagnoza zamiast
  drugiego ślepego. INVALID ⇒ powtórka z puli (≤2 na dolot), scenariusz wg reguły +1
  w bloku 2.
- **Etykiety nowego korpusu:** det_labels.py 8f7430cd bez edycji; filtry F1–F4 zliczone
  per boot; **H_REAL=0.5 m FROZEN** (prior zwalidowany IoU 0.49–0.60 w recon; korekta
  tylko przez ANEKS). Próbka wizualna: **5 PNG/boot (60 łącznie) do repo**.
- **Bramka wizualna etykiet (przed treningiem):** jeśli w ≥2 bootach ≥2/5 PNG pokazuje
  etykietę rażąco obok sylwetki (okluzja/prior) ⇒ STOP-ANEKS zamiast treningu.
- Frakcja nieba na nowym korpusie zliczona klasyfikatorem pierścienia z recon (opisowo;
  konsekwencja kwalifikatora — §0).

## §3. D2 — Split uczciwości (held-out KOMÓRKI; wylosowany pod zamrożoną regułą, wynik zamrożony)

Reguła (wykonana przez CC przed tym dokumentem, odtwarzalna): c08 i c11 → TRAIN
wymuszone (ich stare klatki 2A są użyteczne wyłącznie treningowo — każdy inny przydział
to przeciek albo strata korpusu); pula pozostałych 10 komórek,
`numpy.default_rng(20261006)`: najpierw TEST 2, potem VAL 2.

- **TEST: c06, c09** · **VAL: c02, c04** · **TRAIN: c00 c01 c03 c05 c07 c08 c10 c11**
- Weryfikacja struktury (siatka = v_intr {0,0.5,1.0} × bearing {0,90,180,270}): TRAIN
  pokrywa wszystkie 3 prędkości i wszystkie 4 bearingi; komórki TEST to niewidziane
  KOMBINACJE widzianych czynników — właściwy test generalizacji, nie ekstrapolacja.
- Negatywy (puste etykiety F3) uczestniczą w TRAIN/VAL/TEST swoich komórek (tło).
- Stare klatki 2 Hz NIGDY w VAL/TEST (są z komórek TRAIN z konstrukcji).
- **Komórki TEST dotknięte dokładnie RAZ** — finalnym modelem (§5); wszystkie decyzje
  (selekcja, eskalacja, θ*) zapadają na VAL.

## §4. D3/D4 — Architektura i tor treningu (verbatim, seed)

- **Ścieżka główna: fine-tune `yolov8n.pt` jednoklasowo** („intruder"), imgsz 640 (tryb
  runtime; @1280 nie wchodzi — dyscyplina selekcji). **Eskalacja pre-autoryzowana RAZ:**
  v8s tym samym przepisem, WYŁĄCZNIE gdy v8n nie przejdzie progu błędu na VAL (§5);
  trzeciej architektury nie ma — dalej działa §8.
- **Pobranie wag bazowych yolov8n.pt + yolov8s.pt — RATYFIKOWANE TYM PRE** (zmiana
  inwentarza wag; sha256 obu do FREEZE_DET przy S1, PRZED pierwszym treningiem).
  Fine-tune worldv2 odrzucony (tor tekstowy zbędny w locie).
- **Licencja (decyzja jawna):** ultralytics AGPL-3.0 — akceptowana dla tej nogi (badania
  SITL, bez dystrybucji binarnej; tor 2A już na ultralytics). Alternatywa torchvision/BSD
  zostaje w katalogu na wypadek wymogu license-clean runtime.
- **Przepis treningu (FROZEN):** ultralytics 8.4.115 (pin .b0deps), torch 2.11.0+cu128;
  `model=yolov8n.pt data=<dataset.yaml nc=1> epochs=100 imgsz=640 batch=16 seed=1
  deterministic=True device=0 workers=4 patience=30 cache=False`; **cała reszta =
  domyślne 8.4.115** (wersja pinowana ⇒ domyślne są zamrożone przez pin). Fallback OOM
  pre-autoryzowany: batch 16→8 (zliczony, do raportu). **Jeden run na architekturę,
  seed 1 — zero sweepów ziaren.**
- **Selekcja:** best.pt wg domyślnego fitness ultralytics na VAL (= komórki VAL w yaml).
  TEST nieobecny w yaml treningu.
- Dataset budowany narzędziem (results/DET/tools/make_dataset.py): manifest z licznościami
  per komórka/boot + sha. Finalne wagi: `net/frozen/det_v2.pt` + sha do FREEZE_DET.

## §5. Bramka T — werdykt treningu OFFLINE przez replay admisyjny (semantyka sędziego 2A)

**Przyrząd: det_replay.py (nowe narzędzie, FROZEN przy S1)** — przepuszcza sekwencje
klatek 15 Hz przez: detektor-v2 → MTI → admisję D2 → pinhole → TargetChannel
(importy r02 READ-ONLY, te same bajty co lot), z pozą/quat z logów; mierzy błąd
e(t)=|trk_pos_ned−GT| na próbkach świeżych — **ta sama populacja (post-admisja) i ta
sama matematyka, którą bramka B PRE_2A mierzyła na shadow-logach.** Progi dziedziczone
VERBATIM, żadnych nowych liczb.

**Walidacja przyrządu (prereg, klasa „tryb testowany ≠ tryb lotny"):** przed użyciem na
nowym korpusie replay odtwarza S2b-A2b z YOLO-World jako detektorem; wymagane: p95 błędu
replay ∈ [0.5×, 2×] zmierzonego w locie (40.9 m) i zgodność jakościowa frakcji na-celu.
Poza pasmem ⇒ STOP-ANEKS (przyrząd, nie wynik).

**Bramka T na komórkach TEST (finalny model, jedno przejście):**
- **T2 (nośnik werdyktu): err p95 ≤ 3.0 m** (verbatim PRE_2A B-iii; odniesienie FeedB
  1.258 m bez zmian).
- **T1 (mechanizm, opisowy z nazwanym progiem): top-1-na-celu ≥80%** klatek z celem
  w FOV (próg nazwany w PROMPT_DET_S0 R3 jako „zmienia kształt nogi"; nośnikiem śmierci
  NIE jest).
- **θ\*** (opisowy): próg conf wybrany na VAL, raportowany TP/FP na TEST — **do runtime
  NIE wchodzi** (admisja bez zmian, §0).
- Kolejność: v8n → replay na VAL → (fail progu błędu ⇒ eskalacja v8s → replay VAL) →
  model finalny → **TEST raz**.

**Naprawa klasy erraty B(i) — definicje kadencji rozdzielone (prereg):** (a) **kadencja
przetwarzania klatek** [Hz, czysto czasowa, pre-admisja] — nośnik każdego zdania
„limituje czasowo"; (b) kadencja próbek świeżych [jakość∧czas, zależna od bramy] —
wyłącznie opisowa. Bramki runtime (§6) gate'ują (a). Nigdy więcej progu na metryce,
której semantykę zmienia ratyfikowana interwencja.

## §6. D5 — Runtime: percepcja w OSOBNYM PROCESIE (FEED=V2) + smoke

- **Budowa (S3):** proces potomny percepcji (detektor-v2 + MTI + admisja + pinhole +
  TargetChannel — rdzeń jak feed_vision, te same importy r02) publikujący próbki tracku
  po **UDS jsonl** (wzór shadow_feed_live S2 — dowód wykonaniem: E2E p95 0.044–0.052 s
  w osobnym procesie); cienki klient `FeedVisionProc` w rejestrze jako **FEED=V2**
  (additive). Kontrakt set_feed — dict VERBATIM (trk_pos_ned, trk_vel_ned, track_age_s,
  track_valid, feed_sha; feed_sha V2 = hash parametrów + sha wag det_v2). Decymacji
  pos/att nie dodajemy (minimalny diff względem dowiedzionego wzoru; w osobnym procesie
  kontencja egzekutora bencha nie dotyczy percepcji).
- **Smoke (1–2 booty): FEED=V2, CONTROLLER=net, scenariusz c10_s01** (komórka TRAIN,
  blok 1). Ważność V2′ + żywość feedu (ANEKS_2A-3 §4 verbatim: ≥1 świeża LUB ≥10 klatek
  w 30 s). **Bramki runtime live (dziedziczone):** kadencja przetwarzania (def. (a) §5)
  **≥8 Hz p50**; opóźnienie end-to-end (stempel klatki → próbka u klienta) **p95 ≤0.25 s**.
  Opisowo: kadencja świeżych, err vs GT (echo T2), rozkład admisji.
- **S-BEZP smoke (kryterialne):** breach R_E=0 wymagane; REFUSE per gałąź = wpis;
  REFUSE(POS) ⇒ STOP.
- **Śmierć czasowa PRE_2A NIE przenosi się automatem:** po dowodzie wykonaniem (shadow
  14.7 Hz w osobnym procesie) fail kadencji/latencji w smoke klasyfikuje się jako defekt
  budowy — ≤2 podejścia naprawcze (w budżecie), potem ANEKS decyzyjny. Werdyktu
  „percepcja limituje czasowo" nie wolno ogłosić z tej nogi bez pomiaru obalającego
  dowód shadow.

## §7. Kampania C — verbatim z PRE_2A, jedna podmiana

Kampania C **zamrożona w PRE_2A i nielatana** leci w S4 dokładnie wg PRE_2A §3-C/§4,
z JEDNĄ podmianą: **FEED-V → FEED-V2**. Dla jednoznaczności, progi werdyktu verbatim:
12 rund × 2 booty (FEED-B, FEED-V2) × NCP, blok 4 scenariuszy stały w rundzie (siatka 48
jak LIQ), rotacja kolejności, V2′, INVALID ⇒ 1 powtórka ⇒ wypadanie parowe; n_common<40
⇒ STOP; osłona uzbrojona bez zmian; REFUSE = wynik epizodu + wpis z gałęzią; REFUSE(POS)
lub breach ⇒ STOP. **Δ = pass(B) − pass(V2) na 48 parach: Δ≤4 ⇒ „system przeżywa zejście
z wyroczni"; Δ≥10 ⇒ „percepcja limituje wykonanie"; 5–9 strefa opisowa; V2 lepszy o ≥3 ⇒
zdanie jawne + podejrzliwość wobec przyrządu.** Smoke tej nogi (§6) zastępuje smoke
z PRE_2A.

**Warunek odpalenia kampanii:** T2 PASS na TEST (§5) ∧ smoke PASS (§6). Kwalifikatory
każdego zdania kampanii (aktualizacja względem 2A, uczciwie): SITL, rendering
syntetyczny, mono-zasięg ze znanym rozmiarem, **detektor DOSZKOLONY na klatkach z tego
samego symulatora i tej samej sceny (komórki testowe held-out; scenariusze kampanii
rozłączne ze zbiorem treningowym)**, geometria c-siatki, NCP. Zakazy PRE_2A §4 bez zmian.

## §8. Śmierć kierunku i wyjątki (prereg)

- **ŚMIERĆ-DET:** po v8n ORAZ jednej eskalacji v8s, replay na TEST daje **err p95 >6.0 m**
  (granica wyjątku ekonomicznego PRE_2A — żadnych nowych liczb) ⇒ werdykt „**fine-tune na
  etykietach projekcyjnych nie wystarcza tej scenie**" — publikowalny negatyw; noga
  zamyka się BEZ lotów; kampania C wraca do katalogu jako zamrożona-nielatana.
- **Strefa 3.0 < p95 ≤ 6.0 m:** śmierć nie zapada; kampania NIE leci w pełni (wyjątek
  ekonomiczny verbatim); **domyślnie sonda 2 bootów** (wzór C-sondy 2A: S-BEZP
  kryterialne + S-MISJA opisowe, pierwsze loty na uczonym detektorze) — ANEKS może
  zamienić sondę na zamknięcie, nie odwrotnie.
- Bramka wizualna etykiet (§2) i walidacja replay (§5) to STOP-y przyrządowe (ANEKS),
  nie śmierci.
- Przekroczenie budżetu (§9) ⇒ STOP. Wyjątek ekonomiczny i reżim powtórek — jak 2A.

## §9. Budżet, sesje, pliki (lista zamknięta), higiena

**Booty lotne: dolot 12 (+≤2 powtórki) + smoke ≤2 (+≤2 naprawcze §6) + kampania 24
(+zapas 3) ⇒ twardy sufit ≤45, oczekiwane 38–41; 3–4 sesje lotne + 1 sesja GPU (0 bootów).**
Rytm: **S1** narzędzia (zrzut 15 Hz, make_dataset, det_replay + walidacja na S2b) + dolot
+ etykiety + 60 PNG + bramka wizualna + FREEZE_DET (sha wag bazowych) → STOP-DET1;
**S2** trening + replay VAL(/eskalacja) + TEST raz + werdykt T → STOP-DET2 (0 bootów);
**S3** build V2 + testy + smoke → STOP-DET3; **S4** kampania C (albo sonda/zamknięcie
wg §8) → STOP-DET4. Po każdym STOP: push Olgi, weryfikacja CC z repo, ANEKS numerowany.

**Pliki.** Korzeń: PRE_DET.md (ARCH-1, pierwszy commit S1). NOWE: `results/DET/**`
(FREEZE_DET.md, raporty, tools), `harness/det_v2.py`, `harness/percep_proc.py`,
`harness/feed_vision_proc.py`, `net/frozen/det_v2.pt` (po S2). EDYCJE istniejących:
**WYŁĄCZNIE** rejestr feedów — wpis additive FEED=V2. ZERO edycji: bench_flight,
feed_vision, r02/**, osłona, sędziowie, wagi sieci. Narzędzie-driver zrzutu = tool.

**Higiena:** env prefiks `DETV2_`; katalog wyników `results/DET/`; dysk ~0.5 GB lokalnie
(gitignore + sha); nota numpy 2.4.4 (B0SP) / 1.26.4 jak 2A; manifesty 1. klasy; cooldowny
≥300 s; proc_gate; GZ_IP=127.0.0.1 w driverze etapowym.

## §10. Predykcje CC (reguła 9: NIE są priorami; nowa reguła kalibracyjna z ANEKS_2A-4 §4
zastosowana jawnie: bramki techniczno-integracyjne ↓, wyniki komponentu uczonego ↑)

- **P-DET-1** (integracyjna ↓ z 0.70): dolot 12/12 VALID w jednej sesji, bez puli — **p 0.55**
- **P-DET-2** (uczona ↑ z 0.65): v8n BEZ eskalacji osiąga T1 ≥80% na TEST — **p 0.80**
- **P-DET-3** (uczona ↑ z 0.60): model finalny przechodzi T2 ≤3.0 m na TEST — **p 0.75**
- **P-DET-4** (integracyjna ↓ z 0.70): smoke przechodzi obie bramki runtime za 1. podejściem — **p 0.50**
- **P-DET-5** (warunkowa — liczy się tylko, jeśli kampania leci): Δ≤4 — **p 0.55**;
  pod-predykcja: ≥1 REFUSE jakiejkolwiek gałęzi pod V2 w kampanii — **p 0.20**
  (spadek z P-2A-5 0.25: REFUSE=0 we wszystkim dotąd latanym).

Rozliczenie przy zamknięciu w KSIĘDZE, sekcja NOGA DET.

## §11. Ratyfikacja

Czekam na **„ratyfikuję"** Olgi. Po ratyfikacji wydaję **PROMPT_DET_S1** (build narzędzi
+ dolot + etykiety; zero treningu — trening dopiero w S2 po STOP-DET1 i moim ANEKS-ie).
Zmiany po ratyfikacji wyłącznie ANEKS-em numerowanym.
