# RAPORT_FANTOM — noga FANTOM (czysty start epizodu: kwarantanna K1) — CLOSED

Wykonawca · 16.10.2026 · CO-FANTOM per ANEKS_FANTOM-2 §6. Pozycja FANTOM-START
otwarta decyzją Olgi 12.10 (z ANEKS_REAKW-1 §4), PRE_FANTOM ratyfikowane 15.10,
zamknięta ANEKS_FANTOM-2. Bilans: **28/≤30 bootów, 2 sesje lotne + 1 desk + recon,
4 dni; breach 0 / REFUSE 0 we wszystkich 28 uzbrojonych bootach nogi.**

## §1. WERDYKT DWUWARSTWOWY (ANEKS_FANTOM-2 §2, verbatim; zdania zamrożone PRE_FANTOM §5)

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
   locków); jej dowód lotny pozostaje ze smoke S1 (żywy parking → przechwyt
   B@0.88 s → D6).
3. **Regresja c10_s02 nie jest kosztem kwarantanny** (q_exit C = czysty start,
   identyczny tryb jak w przebiegu AKW tej pary) — wariancja pościgu na komórce
   granicznej (c10 w AKW 2/4). Saldo per para vs AKW: **+5/−1**.

**Warstwa SIATKI:** **Δ_new2 = 7** — strefa opisowa progów PRE_2A (5–9);
przewidywanie desku (~6) i przedział P-F-3 [5,8] trafione. Bearing PŁASKI
(2/1/2/2), **całe rezyduum w celu szybkim (v: 0/1/6)**. Dryf B równoważny (95.0%
vs 95.8%); podejrzliwość wobec kwarantanny NIE aktywowana. Łańcuch **Δ: 34 → 12 →
7** ZAWSZE z kwalifikatorem trzech kampanii i n_common (48/48/40).

## §2. Łańcuch S0→S2 (liczby + odsyłacze)

- **S0 RECON** (`results/FANTOM_RECON/RECON_FANTOM.md`, 15c31143): dźwignia
  zmierzona deskiem — konwersja górna 6/6 (3×c08 dowód DET-PASS; siostry 3/3);
  mechanizm w 2 podklasach (parking-świata przy 1. epizodzie bootu / koniec
  poprzedniego epizodu; expire ~1 s; ślepota 9.5–26.8 s); marker startu darmowy =
  reset() (bench_flight.py:312); rodzina choreografii odrzucona rachunkiem.
- **PRE_FANTOM** (ratyf. 15.10; ARCH-1 a7f3073c): kwarantanna konsumenta
  w net_fantom; predykaty K2/K1 z mechaniczną regułą wyboru; werdykty DWUWARSTWOWE
  (pierwsza prerejestracja epizodowa programu); sufit ≤30.
- **S1** (`RAPORT_FANTOM_S1.md`, 017421ed): budowa `fantom_scan.py` e435ed7e
  (delegacja AkwScan b94cdeae; rejestr 87203d29); T1 12/12 (świadek-delegat +
  wprost-na-ślepych; delegat rekurencyjny — nota wykonawcza); **T2: reguła wyboru
  zadziałała PRZECIW preferencji — K2 padł na (ii)** (c05_s04 bez odświeżeń 3 s,
  pomiar surowy) ⇒ **K1 FROZEN** (A/B/C; T_q=3.0, D_JUMP=5.0; koszt C-exitów na B
  nazwany deskiem: 12/48, +3 s); smoke PASS za 1. podejściem: żywy parking →
  B@0.88 → D6 ✓ (AKW: 26.8 s FAIL); c01_s01 → 5.9 s → D6 ✓; kontrola c09_s01 bez
  regresji (5.34 vs pred 5.6).
- **S2 kampania** (`RAPORT_FANTOM_S2.md`, cd58d8cb): 12×{B,V2} oba ramiona
  net_fantom, 27 launches (24+3, w tym infra-pad r4_B), 28 bootów nogi;
  **n_common=40 dokładnie na progu**, pass(B)=38, pass(V2)=31, **Δ_new2=7**;
  N6 3/6, regresje 1; kwarantanna 14/14 żywych fantomów; bezpiecznik modu bez
  tripa; breach 0 ×27, REFUSE 0.

## §3. Kampania S2 — liczby i chronologia środowiskowa

Werdykt liczbowy i dekompozycje: §1. Tabela 48 par i telemetria per epizod
(fantom@t0 żywy/martwy/brak + d_spawn + age, q_exit powód/czas, t_entry, mod per
boot): `RAPORT_FANTOM_S2.md` §4–§5 + `camp/fantom_pairs.json` +
`camp/fantomS2_telemetry.json`. Chronologia środowiskowa (RAPORT_FANTOM_S2 §2):
rundy 1–3 pod degradacją (artefakt próbnika RTF pod kontencją CPU, turbo
nieaktywne po restarcie hosta; fizyka 1.0 z trace — diagnoza bez dotykania frozen
metryki; 3× PAUSE + sonda mediany dsim + restart hosta) → rundy 4–12 zdrowe
(dsim 1.012–1.046, zero nieważności); trzecia moda kadencji 5.10 Hz (opisowa);
infra-pad r4_B (spawn timeout); straty par 8/8 limitu (4 środowiskowe + 4 infra).

## §4. Mechanizmy (trzy, z liczbami)

1. **Kwarantanna startu (K1) działa: 14/14 żywych fantomów utrzymanych** (13×
   wyjście C po predykacie, 1× przechwyt B realnego celu; zero konsumpcji
   fantomu) + żywy parking przechwycony w smoke (B@0.88). Akwizycje w epizodach
   fantomowych 6.6–9.9 s vs 9.5–22.3 s ślepoty w AKW — klasa „ślepy start
   z fantomu" zniknęła z danych. Koszt na wyroczni zgodny z deskiem (C-exity,
   pass(B) równoważne).
2. **Sygnatura pościgowa porażek:** 3 porażki N6 (i 9 porażek V2 kampanii ogółem)
   mają wczesną akwizycję i przegrany pościg — start wyeliminowany jako zmienna
   zakłócająca; rezyduum w całości POŚCIG-V1 (v=1.0 niesie 6/7 Δ_new2).
3. **Regresja c10_s02 = wariancja pościgu** (czysty start w obu kampaniach;
   komórka graniczna c10 w AKW 2/4); saldo per para +5/−1.

## §5. KANON OBOWIĄZUJĄCY — ANEKS_FANTOM-2 (§3 verbatim)

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

## §6. Predykcje (rozliczenie ANEKS_FANTOM-2 §4)

**P-F-1 ✓** (0.65) · **P-F-2 ✗** (0.60; 3/6 zamiast ≥5/6) · **P-F-3 ✓** (0.55;
Δ_new2=7 ∈ [5,8]) · **P-F-4 ✗ literą** (0.75; pass(B)=38<45 przy mianowniku
skurczonym środowiskowo; mechanizm potwierdzony wskaźnikiem 95.0% vs 95.8%) ·
**P-F-5 ✓** (0.85) · **P-F-6 n.r.** (para poza n_common; opisowo D6 ✓ @5.2 s).
**Suma: 3✓/2✗/1 n.r.** Wpisy kalibracyjne: (a) dowód pościgu przenosi się tylko
w obrębie tego samego reżimu opóźnienia akwizycji; (b) predykcje o ramionach jako
WSKAŹNIKI albo warunkowo na n_common — nigdy liczności bezwzględne.

## §7. Rejestr odchyleń nogi

Degradacja środowiska rund 1–3 (artefakt próbnika RTF; diagnoza z trace przy
nietkniętej metryce; 3× PAUSE + sonda + restart hosta — wykonanie wzorcowe per
ANEKS_FANTOM-2 §1) · trzecia moda kadencji 5.10 Hz (opisowa per ANEKS_AKW-1 §2) ·
infra-pad r4_B (spawn timeout, narzędziowy) · straty par 8/8 limitu — koszt
środowiskowy z pełną diagnozą · podklasa parking nie wystąpiła w kampanii
(kwalifikator kanonu) · K2→K1 regułą wyboru (założenie PRE o lock-real obalone
pomiarem — wniosek systemowy w ANEKS_FANTOM-1 §2) · „+1 linia" rejestru = 2 linie
fizyczne (precedens net_akw) · print drivera S1 (kosmetyka, poprawiony w S2) ·
**decyzja o rezerwie (ANEKS_FANTOM-2 §5): NIE latamy straconych par — booty kupują
wyłącznie informację zmieniającą werdykty, a tu żadna nie istnieje; rezerwa 2
wraca do programu nienaruszona.**

## §8. Roadmapa — aktywa POŚCIG-V1 ROSNĄ

Pozycja katalogu **POŚCIG-V1** (trigger bez zmian: przed roszczeniem pełnej siatki
z celem szybkim; dźwignia [MECHANIZM NIEZMIERZONY] — recon od rachunku wykonalności
z GT). Aktywa po tej nodze: **9 porażek V2 kampanii FANTOM — wszystkie z wczesną
akwizycją (pościg czysty: start wyeliminowany jako zmienna zakłócająca)** + 2
B-FAILe (wyrocznia pada tak samo — v=1.0) + telemetria trzech kampanii
(DET S4 / AKW S3 / FANTOM S2) + kwarantanna K1 FROZEN e435ed7e w rejestrze.
Po raz pierwszy w programie całe pozostałe Δ ma JEDEN nazwany mechanizm.
