# PRE_2A — prerejestracja nogi 2A: percepcja w pętli (kamera → detektor → feed)

CC · 03.10.2026 · po RECON_2A (commit e4bd980). Kryteria, progi, decyzje projektowe
i zdania kanonu zamrożone PONIŻEJ, przed jedną linią kodu nogi i pierwszym bootem.
Ratyfikacja Olgi ⇒ PROMPT_2A_S1 (build, zero lotów). **Pierwszy boot lotny nogi (S2)
dopiero po wysyłce warstwy 0** — PROMPT_2A_S2 wydam po potwierdzeniu wysyłki noty.

## §1. Pytanie nogi

Ile kosztuje zejście z wyroczni na własne zmysły: te same scenariusze, ten sam kontroler
(NCP 0337d5ea), ta sama osłona — raz z feedem emulowanym (FEED-B: 10 Hz / 0.2 s / σ 0.5 m),
raz z feedem percepcyjnym (FEED-V: kamera pokładowa → detektor → track → NED), parowane
per scenariusz. Sędziowie są feed-niezależni (RECON R1), więc Δ mierzy wyłącznie percepcję.

## §2. Decyzje projektowe (ratyfikowane tym PRE)

- **D1 — ogniwo box→NED: pinhole + znany rozmiar celu.** Zasięg z szerokości boxa
  (Z = f_px·W_real/w_px; W_real z SDF intruza — jawny prior klasy celu), kierunek z (cx,cy)
  + pozy własnej. Uzasadnienie: platforma zostaje BAJT-W-BAJT ta sama co we wszystkich
  kampaniach (x500_mono_cam lata w ławce od zawsze — RECON R3), a mono-zasięg to uczciwa,
  najsłabsza-rozsądna wersja percepcji; dystanse orbity (~8.7 m) działają na naszą korzyść.
  x500_depth = plan B jako OSOBNA decyzja (zmiana płatowca = zmiana habitatu — lekcja
  enable_wind), nie cichy fallback. Dekompozycję błędu kierunek-vs-zasięg raportuje etap B.
- **D2 — admisja tracku: struktura∧MTI przed wejściem do feedu** (wzór D/r02; ENTRY k=3,
  sufit wieku jak TargetChannel). YOLO-World strzela na tło (RECON R8) — bez bramy
  admisyjnej etap C mieszałby „percepcję" z „filtrem". FP przed admisją nie tykają tracku.
- **D3 — kamera STOCK:** 99.7° / 640×480 / 15 Hz, montaż sztywny przód, ZERO zmian
  w drzewie PX4. Desk R5: f90 orbit NCP = 1.000, zapas elewacji >2× — geometria nie jest
  blokerem; bramka A potwierdza w locie (pitch nielogowany — stąd D5).
- **D4 — detektor zamrożony:** YOLO-World yolov8s-worldv2 sha 9b2c17ab, pretrained,
  **zero treningu/fine-tune w tej nodze**; imgsz 640, classes=["drone"] jak B0. Kadencja
  celu FEED-V = koperta FeedB: świeże próbki ~10 Hz, opóźnienie ≤0.2 s — żeby Δ w etapie C
  mierzył JAKOŚĆ percepcji, nie inną architekturę czasową. trk_vel: regresja 1 s jak FeedB;
  track_valid/age: semantyka kontraktu bez zmian (utrata ⇒ hover-hold konsumenta).
- **D5 — logowanie orientacji drona** (quat) w trace: pole addytywne — bez niego atrybucja
  kadrowania w locie jest niewykonalna (RECON R4).
- **D6 — rejestr producentów feedu** wzorem SR-9 + **baza bench_flight zamrożona:**
  sha wejściowy `3a52e19f` do FREEZE_2A; dokładnie DWIE edycje tego pliku w całej nodze,
  obie addytywne, diff verbatim w raporcie S1: (i) wybór producenta z rejestru po FEED=env,
  default B zachowuje dzisiejsze zachowanie; (ii) zapis orientacji (D5). Każda inna
  potrzeba edycji ⇒ STOP i pytanie.

## §3. Etapy i bramki (progi zamrożone)

**S1 — build (zero lotów):** rejestr + FEED-V (D1/D2/D4) + D5 + sędzia percepcji offline
+ testy; echo-freeze parametrów przed commitem wag czegokolwiek nie ma — freeze dotyczy
sha narzędzi: FREEZE_2A (yolo, feed_vision, bench_flight przed/po, parametry kamery).

**Etap A — 2 booty SHADOW (S2):** lot NORMALNY na FEED-B (kontroler nie widzi percepcji),
a obok żywy tor kamera→bridge→YOLO→box→NED loguje się równolegle. Scenariusze: c08_s03
(najgorszy desk f60) + 1 nominalny (c11_s01). Bramki A (wszystkie trzy):
(i) pokrycie kadru RZECZYWISTE ≥ 0.90 frakcji ticków w orbicie i ≥ 0.90 w approach;
(ii) V2′ bootu z pełnym stackiem percepcji: dsw ≥ 0.90 — przy FAIL dozwolony JEDEN retry
z det 5 Hz (wariant zapisany tu, z góry); FAIL także przy 5 Hz ⇒ STOP;
(iii) orientacja w trace obecna i sensowna. Dodatkowo (opisowo): czy always_on renderuje
w baseline (pytanie R3). Shadow-log z A = surowiec etapu B.

**Etap B — sędzia percepcji offline (0 bootów):** na shadow-logach i klatkach z A, błąd
e(t)=|trk_pos_ned−GT| przepisem R4, na tickach track_valid. Bramki B:
(i) kadencja świeżych próbek ≥ 8 Hz (p50); (ii) opóźnienie end-to-end p95 ≤ 0.25 s;
(iii) błąd pozycji p95 ≤ 3.0 m (punkt odniesienia: FeedB p95 1.258 m — „gorszy-ale-znany").
**ŚMIERĆ KIERUNKU (prereg): FAIL (i) lub (ii) ⇒ noga kończy się raportem „percepcja
limituje czasowo w SITL"** — publikowalne, bez etapu C. FAIL samego (iii): C LECI (pytanie
C dotyczy zachowania systemu, nie urody feedu), kanon niesie zmierzony błąd; wyjątek
ekonomiczny z góry: p95 > 6.0 m ⇒ C skrócone do sondy 2 bootów zamiast kampanii.

**Etap C — kampania parowana (S3/S4):** smoke 1 boot FEED-V, potem 12 rund × 2 booty
(FEED-B, FEED-V) × NCP, blok 4 scenariuszy stały w rundzie (siatka 48 jak LIQ), rotacja
kolejności, V2′, boot INVALID ⇒ 1 powtórka ⇒ wypadanie parowe; n_common < 40 ⇒ STOP.
Osłona uzbrojona bez zmian; REFUSE = wynik epizodu + wpis z gałęzią (fałszywe odmowy pod
szumem percepcji = osobny licznik — pytanie nogi W wraca w ostrzejszej wersji);
REFUSE(POS) lub breach ⇒ STOP. Telemetria per epizod: błąd feedu vs GT, dropouty, z_max.

## §4. Werdykty etapu C (liczniki na wspólnych ważnych; bez języka istotności)

Δ = pass(FEED-B) − pass(FEED-V) na 48 parach:
- **Δ ≤ 4 ⇒** „system przeżywa zejście z wyroczni: koszt percepcji ≤4/48 na sparowanych
  scenariuszach (SITL, rendering syntetyczny, mono-zasięg ze znanym rozmiarem celu)".
- **Δ ≥ 10 ⇒** „percepcja limituje wykonanie: −Δ/48 par; mechanizm z dekompozycji B
  (kierunek/zasięg/dropouty)".
- **5–9 ⇒** strefa opisowa, bez zdania rozstrzygającego.
- FEED-V lepszy o ≥3 ⇒ zdanie jawne (i podejrzliwość wobec przyrządu — wpis).
Każdy wynik niesie: SITL, rendering syntetyczny (percepcja w symulatorze jest ŁATWIEJSZA),
detektor pretrained bez treningu na symie, geometria c-siatki, NCP jako kontroler.
ZAKAZ: ekstrapolacji na realne sensory/warunki; „sieć widzi" bez kwalifikatora toru;
mieszania wyniku C z filtrem admisyjnym (dekompozycja B obowiązkowa przy cytowaniu).

## §5. Budżet i rytm

A 2 + smoke 1 + C 24 + powtórki/zapas 4 = **≤31 bootów; ≤3 sesje lotne** (+S1 build bez
lotów). Przekroczenie ⇒ STOP. Dysk: klatki tylko w A (decymacja, ≤0.1 GB/boot). Wyłączność,
cooldowny ≥300 s, manifesty 1. klasy, kind=2a. Kolejność zewnętrzna: S1 może iść od zaraz;
**S2 (pierwszy lot) po wysyłce noty** — bramka w moich rękach (wydanie PROMPT_2A_S2).

## §6. Pliki dotykane (lista zamknięta)

Korzeń: `PRE_2A.md` (ARCH-1, pierwszy commit S1). NOWE: producent `harness/feed_vision.py`
(pinhole+admisja+filtr+kontrakt R1), rejestr feedów (nowy moduł wzorem SR-9), sędzia
percepcji `results/2A/tools/**`, `results/2A/FREEZE_2A.md`, `results/2A/**`. EDYCJE
istniejących: WYŁĄCZNIE `bench/bench_flight.py` w dwóch miejscach z §2-D6 (diff verbatim).
Read-only: `r02/detector_node.py`/`target_channel.py`/`mti.py` (adaptacja = NOWY plik,
nie edycja). NIETYKALNE: sędziowie lotu, features, shield+piny, wagi, światy, run_boot.sh,
konsumenci feedu (orbit/net/gru/mlp20).

## §7. Predykcje CC (do KSIĘGI przy zamknięciu; z jawną korektą na udokumentowany
kierunek moich błędów — pięć ✗ niedoszacowania przy zerze przeciwnych)

- **P-2A-1:** bramka A przechodzi w ≤2 bootach (pokrycie + dsw) — p≈0.75.
- **P-2A-2:** bramka B czasowa (kadencja+latencja) PASS — p≈0.7.
- **P-2A-3:** błąd FEED-V p95 ≤ 3.0 m — p≈0.55 (mono-zasięg z ~20-px boxa to najsłabsze
  ogniwo; krótkie dystanse orbity pomagają).
- **P-2A-4:** werdykt C: Δ ≤ 4 — p≈0.5; strefa 5–9 — p≈0.25; Δ ≥ 10 — p≈0.25.
- **P-2A-5:** ≥1 REFUSE jakiejkolwiek gałęzi pod FEED-V w kampanii — p≈0.25.

## §8. Po ratyfikacji

„Ratyfikuję" ⇒ PROMPT_2A_S1 (build + FREEZE_2A + sędzia percepcji + testy; zero bootów).
S2 (etap A+B) po wysyłce warstwy 0; S3/S4 kampania. Zamknięcie: RAPORT_2A + ANEKS_2A-n
(werdykt §4, dekompozycja błędu, kanon, KSIĘGA). Noga jest odporna na wynik: „przeżywa
zejście z wyroczni", „percepcja limituje czasowo" i „percepcja limituje dokładnością" są
trzema różnymi, publikowalnymi zdaniami — żadne nie wymaga naciągania.
