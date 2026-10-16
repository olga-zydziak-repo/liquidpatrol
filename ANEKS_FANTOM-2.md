# ANEKS_FANTOM-2 — werdykt dwuwarstwowy (strefa opisowa z mechanizmem), KSIĘGA, decyzja o rezerwie + zamknięcie (CO-FANTOM)

CC · 16.10.2026 · łańcuch FANTOM (po STOP-FANTOM2, commity 6f955d59→cd58d8cb na
origin). Aneks zamykający, samowykonalny (§6): sesja wykonuje CO-FANTOM i STOP;
zero bootów — loty nogi zakończone na 28/≤30.

## §1. Przyjęcie STOP-FANTOM2

Przyjęte po weryfikacji CC z repo wykonaniem: ARCH-1 bajt-w-bajt (d464b17c…);
zakres = korzeń + results/FANTOM/** (1073 pliki, zero edycji poza nogą); liczniki
przeliczone NIEZALEŻNIE z fantom_pairs.json: **n_common 40 (dokładnie próg, twardy
STOP nie zaszedł), pass(B) 38, pass(V2) 31, Δ_new2 = 7**; stracone pary dokładnie
{c00_s02, c01_s02, c02_s02, c03_s02 — infra-pad r4_B} ∪ {c03_s01, c08_s01, c09_s01,
c11_s01 — środowiskowe}; regresja dokładnie **{c10_s02}**; dekompozycje odtworzone
(v: 0/1/6; bearing 2/1/2/2; sceno-świeże 39, Δ 6); z summary 27 bootów ×104
epizodów: **breach 0, stop_now 0, REFUSE 0**; bezpiecznik modu bez tripa (admisje
ślepych 96.3–98.9% ×14 bootów V2). Z telemetrii per epizod CC przeliczyła TWARDSZĄ
wersję wyniku głównego: **żywych fantomów w kampanii było 14 (ważne epizody) —
kwarantanna utrzymała 14/14** (13× wyjście C po predykacie, 1× przechwyt B realnego
celu; zero konsumpcji fantomu). Odchylenia środowiskowe (rundy 1–3: artefakt
próbnika RTF pod kontencją CPU + turbo po restarcie; diagnoza z trace przy
nietkniętej metryce; 3× PAUSE na granicach rund + restart hosta ⇒ rundy 4–12 zero
nieważności) — przyjęte jako klasa narzędziowa, wykonanie wzorcowe; trzecia moda
kadencji 5.10 Hz opisowa per ANEKS_AKW-1 §2; infra-pad r4_B narzędziowy.

## §2. WERDYKT DWUWARSTWOWY (zdania zamrożone PRE_FANTOM §5 — bez mieszania)

**Warstwa POZYCJI:** N6 przechodzi **3/6** (c01_s01, c06_s04, c08_s02 ✓; c05_s02,
c08_s03, c08_s04 ✗), regresje **1** (c10_s02). SUKCES (≥5/6 ∧ ≤1) NIE zaszedł;
ŚMIERĆ-FANTOM (≤2/6 ∨ ≥3) NIE zaszła ⇒ **STREFA OPISOWA**, dekompozycja obowiązkowa:

1. **Mechanizm startu epizodu jest DOMKNIĘTY POMIAREM:** kwarantanna utrzymała
   wszystkie 14 żywych fantomów kampanii (w tym 3/3 N6 podklasy poprzedni-epizod —
   jedyne ryzyko otwarte ANEKS_FANTOM-1 §3 zamknięte), akwizycje w epizodach
   fantomowych 6.6–9.9 s wobec 9.5–22.3 s ślepoty w AKW. Ślepy start z fantomu
   jako klasa porażki **przestał istnieć w danych**.
2. **Konwersja epizodowa 3/6, bo pozostałe ogniwo to POŚCIG:** wszystkie 3 porażki
   N6 mają wspólną sygnaturę — wczesna akwizycja (5.0–6.6 s) i przegrany pościg
   (v=1.0 ×2, v=0.5 ×1). To rezyduum klasy POŚCIG-V1, nie mechanizm startu.
   Kwalifikator uczciwy: podklasa parking-świata w kampanii NIE wystąpiła (0/3
   locków — loteria freshów przedstartowych); jej dowód lotny pozostaje ze smoke S1
   (żywy parking → przechwyt B@0.88 s → D6).
3. **Regresja c10_s02 nie jest kosztem kwarantanny** (q_exit C = czysty start,
   identyczny tryb jak w przebiegu AKW tej pary; t_entry 5.0, potem utrata pościgu)
   — wariancja pościgu na komórce granicznej (c10 w AKW 2/4). Saldo per para vs
   AKW: **+5/−1** (konwertują też pościgowe c09_s03 i c10_s01 — wariancja działa
   w obie strony).

**Warstwa SIATKI:** **Δ_new2 = 7** — strefa opisowa progów PRE_2A (5–9);
przewidywanie desku (~6) i przedział P-F-3 [5,8] trafione. Bearing PŁASKI
(2/1/2/2), **całe rezyduum w celu szybkim (v: 0/1/6)** — spójnie z kanonem AKW.
Dryf B równoważny (95.0% vs 95.8%; B-FAILe c09_s03/c11_s02, oba v=1.0, ten sam
pas trudności co w AKW); C-exity kwarantanny na wyroczni bez wpływu na wynik —
podejrzliwość wobec kwarantanny NIE aktywowana. Łańcuch **Δ: 34 → 12 → 7** ZAWSZE
z kwalifikatorem trzech kampanii i n_common (48/48/40).

## §3. KANON ROSZCZEŃ FANTOM — obowiązujący

**WOLNO** (kwalifikatory DET+AKW w całości + „kwarantanna startu K1"):
- „ślepy start z fantomu wyeliminowany: kwarantanna utrzymała 14/14 żywych fantomów
  kampanii + przechwyt żywego parkingu w smoke; akwizycje w epizodach fantomowych
  6.6–9.9 s vs 9.5–22.3 s ślepoty przed" — zdanie z kwalifikatorem podklasy parking
  (lotny dowód: smoke, nie kampania);
- „dron lata na kamerze w 31/40 wspólnie ważnych par pełnej geometrii (wyrocznia
  38/40); Δ_new2=7; rezyduum w całości pościgowe (v=1.0 niesie 6/7)";
- „Δ 34→12→7" wyłącznie z kwalifikatorem trzech kampanii i jawnym n_common=40;
- mechanizm regresji c10_s02 jako wariancja pościgu (nie koszt kwarantanny);
- koszt kwarantanny na wyroczni zmierzony i pomijalny (C-exity wg desku, pass(B)
  równoważne).

**NIE WOLNO:** „fantom-start rozwiązany" bez kwalifikatora podklasy parking;
cytować Δ_new2 bez n_common; przypisywać 3 porażek N6 mechanizmowi startu
(sygnatura pościgowa) ani regresji — kwarantannie; „pozycja osiągnęła SUKCES
progowy" (strefa opisowa — progi nie strzeliły w żadną stronę); porównań
międzykampanijnych bez kwalifikatora; ekstrapolacji na realne sensory (PRE_2A §4).

## §4. Rozliczenie predykcji (do KSIĘGI, sekcja NOGA FANTOM)

**P-F-1 ✓** (0.65; smoke za 1. podejściem) · **P-F-2 ✗** (0.60; konwersja 3/6
zamiast ≥5/6) · **P-F-3 ✓** (0.55; Δ_new2=7 ∈ [5,8]) · **P-F-4 ✗ literą** (0.75;
pass(B)=38 < 45 — mianownik skurczony środowiskowo; mechanizm predykcji
POTWIERDZONY wskaźnikiem 95.0% vs 95.8% i nieszkodliwością C-exitów) ·
**P-F-5 ✓** (0.85; breach 0 / REFUSE 0) · **P-F-6 NIEROZSTRZYGNIĘTA** (para
c09_s01 nieważna środowiskowo — poza n_common; opisowo: nieważny przebieg D6 ✓
przy 5.2 s). **Suma: 3✓ / 2✗ / 1 n.r.** Kalibracja CC, dwa wpisy: (a) P-F-2 —
dowód pościgu przenosi się tylko w obrębie tego samego reżimu opóźnienia
akwizycji (DET-PASS c08 przy akwizycji ~0 s nie dowodzi pościgu po akwizycji
5 s); (b) P-F-4 — predykcje o ramionach formułować jako WSKAŹNIKI albo
warunkowo na n_common, nigdy jako liczności bezwzględne, bo mianownik może
skurczyć się narzędziowo.

## §5. Decyzja o rezerwie programowej (2 booty): NIE LATAMY straconych par

Booty kupują wyłącznie informację zmieniającą werdykty — tu żadna nie istnieje:
N6 w komplecie ważne (werdykt pozycji nietykalny); odzysk 4 par r4_B to komórki
v=0/0.5, gdzie obie strony przewidywalnie przechodzą (Δ bez zmian, strefa bez
zmian); 1 boot za samo rozstrzygnięcie P-F-6 nie zmienia żadnego werdyktu ani
kanonu. Rezerwa 2 wraca do programu nienaruszona. Straty par pozostają nazwane
w raporcie jako koszt środowiskowy z pełną diagnozą.

## §6. Zlecenie CO-FANTOM — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git log origin/master..HEAD` puste ⇒ dalej; inny stan ⇒ STOP. Pliki (lista
zamknięta): korzeń `ANEKS_FANTOM-2.md` (ARCH-1, verbatim, pierwszy w commicie);
NOWY `results/FANTOM/RAPORT_FANTOM.md`: §1 werdykt dwuwarstwowy §2 verbatim;
§2 łańcuch S0→S2 z liczbami (recon 6/6 desk → PRE → S1: K1 z reguły wyboru + smoke
→ S2 kampania, odsyłacze); §3 kampania (Δ_new2, dekompozycje, tabela par przez
odsyłacz, chronologia środowiskowa z §2 raportu S2); §4 mechanizmy (kwarantanna
14/14; sygnatura pościgowa porażek; c10_s02); §5 kanon §3 verbatim z nagłówkiem
„KANON OBOWIĄZUJĄCY — ANEKS_FANTOM-2"; §6 predykcje §4; §7 odchylenia (w tym
środowiskowe + decyzja §5); §8 roadmapa: **aktywa POŚCIG-V1 ROSNĄ** — 9 porażek V2
tej kampanii (wszystkie z wczesną akwizycją — pościg czysty, start wyeliminowany
jako zmienna zakłócająca) + 2 B-FAILe + telemetria trzech kampanii; trigger bez
zmian. EDYCJE: `results/KSIEGA_PREDYKCJI.md` — sekcja NOGA FANTOM wg §4 (3✓/2✗/1
n.r. + dwa wpisy kalibracyjne); `KIERUNKI_PO_PLANIE.md` — FANTOM-START → **CLOSED**
z odsyłaczem do RAPORT_FANTOM i jednozdaniowym werdyktem („mechanizm startu
domknięty pomiarem 14/14; konwersja epizodowa 3/6 ograniczona pościgiem; Δ 12→7");
przy wpisie POŚCIG-V1 dopisek aktywów jw. ŻADNYCH edycji raportów wstecz. Raport
płaski: diff-stat, pełna treść RAPORT_FANTOM.md i zmian KIERUNKÓW, porcelain.
STOP. Push = Olga („wypchnięte").

## §7. Status i dalej

**Noga FANTOM: CLOSED** z chwilą commita CO-FANTOM i pushu. Bilans: 28/≤30 bootów,
2 sesje lotne + 1 desk + recon, 4 dni od otwarcia pozycji; przyniosła: eliminację
ślepego startu (14/14), trzecią z rzędu redukcję Δ (34→12→7) i czystą mapę
rezyduum — **po raz pierwszy w programie całe pozostałe Δ ma JEDEN nazwany
mechanizm: pościg za celem szybkim** (POŚCIG-V1, liga sieci/egzekutora, dźwignia
[MECHANIZM NIEZMIERZONY] — recon od rachunku wykonalności z GT). Program wraca do
trybu katalogu; breach 0 / REFUSE 0 pozostaje prawdą o wszystkim, co kiedykolwiek
poleciało uzbrojone (teraz +28 bootów nogi FANTOM).
