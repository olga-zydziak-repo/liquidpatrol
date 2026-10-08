# ANEKS_DET-4 — werdykt kampanii C i NOGI DET + kanon + KSIĘGA + zamknięcie (CO-DET)

CC · 08.10.2026 · łańcuch DET (po STOP-DET4, commity d914eaa0→37eeb370→35f6e531 na origin).
Aneks zamykający, samowykonalny (§8): sesja wykonuje CO-DET i STOP; zero bootów — loty
nogi zakończone na 37/≤45.

## §1. Przyjęcie STOP-DET4

Przyjęte po weryfikacji CC z repo wykonaniem: ARCH-1 bajt-w-bajt (953f4df4…); zakres
commitów = korzeń + results/DET/**; liczniki przeliczone NIEZALEŻNIE z detS4_pairs.json:
n_common 48, pass(B) 47, pass(V2) 13, **Δ=34**; sceno-świeże 46/Δ=33; bearing-0 12/12;
split TRAIN 32/9 · VAL 8/4 · TEST 7/0; refuse 0/0 w obu ramionach, gałęzie puste,
stop_flags puste; telemetria ramion zgodna z raportem (B err_fresh 0.676/1.280 med na 48
epizodach; V2 0.418/0.648 na 22 epizodach z próbkami); lista 13 passów V2 odtworzona
(c00×4, c04×4, c07_s04, c08×4); c10_s01 w r3_V2 FAIL d_min 0.517 potwierdzony
z manifestu. Nota konstrukcyjna client_e2e_full (przechwyt driverem, zero zmian kodu)
— przyjęta. 24/24 booty VALID, zapas 0/3, jedna sesja. Wykonanie wzorcowe.

## §2. WERDYKT KAMPANII C (zdanie zamrożone PRE_2A §4 + obowiązkowa dekompozycja)

**Δ = 34 ≥ 10 ⇒ „percepcja limituje wykonanie: −34/48 par; mechanizm z telemetrii."**
Dekompozycja (obowiązkowa przy każdym cytowaniu): **wszystkie 35 porażek V2 to brak
akwizycji** — 29 epizodów ślepych (cel z bearing 90/180/270° nigdy nie wszedł w stożek
sztywnej kamery przy dronie w zawisie; 0 boxów), 6 akwizycji spóźnionych/utraconych.
**Ani jedna porażka nie jest błędem jakości tracku** — po akwizycji percepcja uczona
jest DOKŁADNIEJSZA od wyroczni (err_fresh med per epizod 0.418/0.648 m vs FeedB
0.676/1.280). Bearing 0°: V2 12/12. FEED_EXPIRE 8/48 — dropouty marginalne.

## §3. Rozstrzygnięcie smoke-vs-kampania (klasa przyrządowa, do rejestru)

Smoke S3 przeszedł c10_s01 (t_entry=0.0), kampania padła na tej samej parze
(d_min 0.517). Mechanizm: **lock przed epizodem jest artefaktem choreografii bootu** —
w boocie 1-epizodowym cel wchodzi w stożek podczas rozbiegu (spawn/pozycjonowanie przy
żywej percepcji); w boocie 4-epizodowym teleport międzyepizodowy nie przecina stożka,
a nos zostaje po poprzednim epizodzie. Ten sam artefakt dał 5 wczesnych locków
w passach kampanii (falsy-zero t_entry, raport §9.4). Wnioski: smoke jednoepizodowy
NIE jest reprezentatywny dla geometrii akwizycji (wpis do rejestru klas, obok „tryb
testowany ≠ tryb lotny"); **zdolności poszukiwawczej system NIE MA — akwizycja zachodzi
wtedy, gdy cel sam wejdzie w stożek.** To ostrzejsze i uczciwsze brzmienie niż
„akwizycja zależy od geometrii wejścia" — i ono wchodzi do kanonu.

## §4. WERDYKT NOGI DET (całość — trzy rzeczy zmierzone, każda z mechanizmem)

1. **Fine-tune na darmowych etykietach projekcyjnych z GT naprawia ogniwo DETEKCJI**
   wskazane przez 2A: offline T2 p95 1.365 m na held-out komórkach (bramka PASS,
   zapas 2.2×), top-1-na-celu 100/99.8 % vs 10.3 % maksimum zero-shot; w locie po
   akwizycji track lepszy od szumionej wyroczni. Koszt treningu: 0.73 h GPU, zero
   ręcznych etykiet.
2. **Architektura osobnego procesu usuwa kontencję runtime** (6.7–7.2 → 14.71 Hz przy
   tych samych bajtach rdzenia; E2E p95 0.084 s), a przyrząd bramki T i tor lotny
   dzielą bajty z konstrukcji (FeedVision read-only + wstrzyknięty detektor).
3. **Kampania kosztu percepcji z PRE_2A w końcu POLECIAŁA** (48/48 par ważnych) i dała
   odpowiedź: Δ=34/48, w całości akwizycyjny (§2–§3). Bezpieczeństwo: breach 0,
   REFUSE 0 (każda gałąź), fałszywe odmowy pod szumem percepcji 0 — w 24 bootach
   kampanii i 37 bootach całej nogi.

**Noga DET: CLOSED — „detektor naprawiony i zmierzony; runtime rozwiązany architekturą;
koszt pełnej percepcji = akwizycja, nie śledzenie".**

## §5. KANON ROSZCZEŃ DET — obowiązujący

**WOLNO** (każde zdanie niesie: SITL, rendering syntetyczny, mono-zasięg ze znanym
rozmiarem, detektor doszkolony na klatkach tego symulatora i tej sceny — komórki
held-out w bramce T, tło naziemne, geometria c-siatki, NCP):
- zdania 1–3 z §4 verbatim, z liczbami;
- „dron lata na kamerze, GDY cel wejdzie w stożek sztywnej kamery — bearing 0°: 12/12,
  po akwizycji track dokładniejszy od wyroczni" — zdanie ZAWSZE z geometrią;
- „Δ=34/48; mechanizm: brak zachowania poszukiwawczego (29/35 porażek = cel nigdy
  w kadrze)";
- „pierwsza kampania parowana wyrocznia-vs-percepcja w programie: 48/48 par ważnych,
  zero powtórek".

**NIE WOLNO:**
- „dron lata na kamerze" bez kwalifikatora akwizycji;
- przypisywać Δ detektorowi, zasięgowi ani dropoutom tracku — telemetria mówi
  przeciwnie (dekompozycja §2 obowiązkowa);
- „percepcja gorsza od wyroczni" jako ogólność — po akwizycji jest LEPSZA; koszt
  siedzi w polu widzenia, nie w estymacji;
- wnioskować lukę generalizacji detektora z TEST 0/8 kampanii (artefakt geometrii
  komórek c06/c09; werdykt generalizacji niesie bramka T i err po akwizycji
  0.61–1.49 m);
- cytować d_min <1 m jako naruszenie bezpieczeństwa — kolizja nie jest przedmiotem
  osłony (geofence/POS); d_min pozostaje miarą opisową, jak w całym programie;
- ekstrapolacji na realne sensory/warunki (PRE_2A §4 verbatim).

## §6. Rozliczenie predykcji (do KSIĘGI, sekcja NOGA DET)

**P-DET-1 ✓** (0.55; dolot 12/12 w 1 sesji) · **P-DET-2 ✓** (0.80; v8n bez eskalacji,
T1 z sufitem) · **P-DET-3 ✓** (0.75; T2 1.365) · **P-DET-4 ✓** (0.50; smoke za 1.
podejściem) · **P-DET-5 ✗** (0.55; Δ=34 zamiast ≤4) · pod-predykcja REFUSE ≥1 (0.20):
nie zaszła — zaszła strona 0.80 (REFUSE=0). **Suma nogi: 4✓/1✗.** Kalibracja CC, wpis:
prawo dwukierunkowe z ANEKS_2A-4 potwierdzone WEWNĄTRZ jednej nogi — komponent uczony
znów przebił oczekiwania (detektor > wyrocznia), gotowość SYSTEMOWA znów przeszacowana;
doprecyzowanie reguły: „gotowość systemowa" obejmuje geometrię sensoryczną (pole
widzenia, choreografia akwizycji), nie tylko integrację software'ową.

## §7. Rejestr odchyleń nogi (do RAPORT_DET §7)

Kadencja bimodalna zrzutu/przetwarzania 7.6/14.7 Hz per boot (S1 i S4; narzędziowa,
nie bramkująca; ANEKS_DET-1 §2a); errata kosmetyczna F3 tabeli S1 (59, nie 62);
ogon zbliżeniowy d<6 m (pasmo poniżej korpusu treningowego Z p5 6.5 m; w porażkach
kampanii NIE uczestniczy); client_e2e per-epizod — właściwość klienta FROZEN, przechwyt
driverem (zero zmian kodu); artefakt granicy epizodu w maximach err (nazwany przed
lotami); falsy-zero t_entry; **smoke jednoepizodowy niereprezentatywny dla akwizycji
(§3 — nowa klasa rejestru)**.

## §8. Zlecenie CO-DET — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git log origin/master..HEAD` puste ⇒ dalej; inny stan ⇒ STOP. Pliki (lista
zamknięta): korzeń `ANEKS_DET-4.md` (ARCH-1, verbatim, pierwszy w commicie); NOWY
`results/DET/RAPORT_DET.md`: §1 werdykt §4 verbatim; §2 łańcuch S0→S4 z liczbami
(recon/PRE/dolot/trening/bramka T/smoke/kampania, odsyłacze do raportów); §3 kampania
(tabela 48 par przez odsyłacz, Δ, dekompozycje per bearing/split/sceno-świeżość);
§4 mechanizm akwizycji + rozstrzygnięcie smoke (§3 tego aneksu); §5 kanon §5 verbatim
z nagłówkiem „KANON OBOWIĄZUJĄCY — ANEKS_DET-4"; §6 predykcje §6; §7 odchylenia §7;
§8 roadmapa: **AKW (akwizycja)** jako pozycja katalogu z triggerem „przed jakimkolwiek
roszczeniem pełnogeometrycznym kamery": skan yaw w zawisie przedakwizycyjnym jako
zachowanie warstwy misji PRZED ENTRY (nie zmiana sieci, nie zmiana osłony), warianty
pre-aim/gimbal jako alternatywy; aktywa gotowe: cały tor V2, kampania-wzorzec do
powtórki parowanej AKW-vs-bez, 29 ślepych epizodów jako zbiór odniesienia. EDYCJE:
`results/KSIEGA_PREDYKCJI.md` — sekcja NOGA DET wg §6 (4✓/1✗ + pod-predykcja + obie
noty kalibracyjne); `KIERUNKI_PO_PLANIE.md` — detektor-v2 → CLOSED z odsyłaczem,
dopisana pozycja AKW z triggerem. Raport płaski: diff-stat, pełna treść RAPORT_DET.md,
porcelain. STOP. Push = Olga („wypchnięte").

## §9. Status i dalej

**Noga DET: CLOSED** z chwilą commita CO-DET i pushu. Bilans: 37/≤45 bootów, 5 sesji
(1 GPU + 4 lotne), 3 dni kalendarzowe; przyniosła: naprawiony pomiarem detektor
(za darmo etykietowo), rozwiązaną architekturą kontencję, pierwszą wykonaną kampanię
wyrocznia-vs-percepcja i twardą lokalizację następnego ogniwa (akwizycja). Program
wraca do trybu katalogu; breach 0 / REFUSE 0 pozostaje prawdą o wszystkim, co
kiedykolwiek poleciało uzbrojone. Rekomendacja na następny wybór jest jawna już teraz:
**AKW** ma najkrótszą ścieżkę od Δ=34 do „dron lata na kamerze w pełnej geometrii" —
jedno zachowanie przedakwizycyjne, zero nowych komponentów uczonych, ewaluacja
i kampania-wzorzec gotowe. Wybór nogi należy do trybu katalogu, nie do tego aneksu.
