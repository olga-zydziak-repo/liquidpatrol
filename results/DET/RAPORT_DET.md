# RAPORT_DET — noga DET „detektor-v2": raport zbiorczy i zamknięcie (CO-DET)

CC · 08.10.2026 · wykonanie ANEKS_DET-4 §8. Łańcuch nogi: RECON_DET (S0, 06.10) →
PRE_DET (ratyf. 06.10, ARCH-1 579ff1b) → S1 narzędzia+dolot+etykiety (RAPORT_DET_S1)
→ ANEKS_DET-1 → S2 trening+bramka T (RAPORT_DET_S2, 0 bootów, GPU) → ANEKS_DET-2 →
S3 build FEED=V2+smoke (RAPORT_DET_S3) → ANEKS_DET-3 → S4 kampania C (RAPORT_DET_S4)
→ ANEKS_DET-4 (ten raport). Booty lotne VALID: **37 z ≤45** (12 dolot + 1 smoke +
24 kampania; wszystkie pule powtórek NIETKNIĘTE: 0/2 · 0/2 · 0/3). **Breach 0
i REFUSE 0 we wszystkich 37.** Bilans: 5 sesji (1 GPU + 4 lotne), 3 dni kalendarzowe.

## §1. WERDYKT NOGI (ANEKS_DET-4 §4 verbatim)

1. **Fine-tune na darmowych etykietach projekcyjnych z GT naprawia ogniwo DETEKCJI**
   wskazane przez 2A: offline T2 p95 1.365 m na held-out komórkach (bramka PASS,
   zapas 2.2×), top-1-na-celu 100/99.8 % vs 10.3 % maksimum zero-shot; w locie po
   akwizycji track lepszy od szumionej wyroczni. Koszt treningu: 0.73 h GPU, zero
   ręcznych etykiet.
2. **Architektura osobnego procesu usuwa kontencję runtime** (6.7–7.2 → 14.71 Hz przy
   tych samych bajtach rdzenia; E2E p95 0.084 s), a przyrząd bramki T i tor lotny
   dzielą bajty z konstrukcji (FeedVision read-only + wstrzyknięty detektor).
3. **Kampania kosztu percepcji z PRE_2A w końcu POLECIAŁA** (48/48 par ważnych) i dała
   odpowiedź: Δ=34/48, w całości akwizycyjny (§3–§4 tego raportu). Bezpieczeństwo:
   breach 0, REFUSE 0 (każda gałąź), fałszywe odmowy pod szumem percepcji 0 —
   w 24 bootach kampanii i 37 bootach całej nogi.

**Noga DET: CLOSED — „detektor naprawiony i zmierzony; runtime rozwiązany architekturą;
koszt pełnej percepcji = akwizycja, nie śledzenie".**

## §2. Łańcuch S0→S4 — liczby per etap (odsyłacze do raportów)

- **S0 recon** (`results/DET_RECON/RECON_DET.md`, 0 bootów): pipeline etykiet
  projekcyjnych z GT zbudowany i zwalidowany (projekcja 1:1 z kanonu coverage_real;
  inwentarz 637 jpg z er 2A); sweep zero-shot YOLO: top-1-na-celu **maksimum 10.3 %**
  — potwierdzenie atrybucji 2A i sufit bazowy dla treningu.
- **PRE_DET** (ratyf. 06.10, ARCH-1 commit 579ff1b): split komórek FROZEN przed
  zebraniem korpusu (TRAIN c00/c01/c03/c05/c07/c08/c10/c11 · VAL c02/c04 · TEST
  c06/c09), przepis treningu FROZEN, bramki T1/T2, predykcje P-DET-1…5 z jawną
  korektą kierunkową z ANEKS_2A-4.
- **S1 dolot+etykiety** (`RAPORT_DET_S1.md`): dolot **12/12 VALID za 1. podejściem**
  (pula 0/2); korpus 6 154 pozytywy + 59 negatywów przy pełnej kadencji ~15 Hz;
  bramka wizualna etykiet PASS 60/60; frakcja nieba 0.10 % ⇒ kwalifikator „na tle
  naziemnym" obowiązuje; dataset TRAIN 4 344 / VAL 1 095 / TEST 1 275.
- **S2 trening+bramka T** (`RAPORT_DET_S2.md`, 0 bootów): v8n seed 1, 99 epok,
  0.733 h GPU, eskalacja v8s NIEuruchomiona (VAL p95 0.725/0.778); TEST dotknięty
  dokładnie RAZ: **T2 err p95 pooled 1.365 m ≤ 3.0 ⇒ PASS** (zapas 2.2×), T1
  top-1-na-celu **100.0 / 99.8 %** (próg 80 %); model finalny `net/frozen/det_v2.pt`
  sha 775ead15.
- **S3 build+smoke** (`RAPORT_DET_S3.md`): percepcja w OSOBNYM PROCESIE (rdzeń
  FeedVision acc81df7 READ-ONLY + wstrzyknięty DetV2; klient bez rclpy; wpis rejestru
  V2 additive; feed_sha_v2 8015bd12); smoke 1 boot, naprawczych 0/2: **kadencja
  14.71 Hz ≥ 8 PASS** (kontencja in-process 6.7–7.2 Hz rozwiązana architekturą),
  **E2E p95 0.084 s ≤ 0.25 PASS**; opisowo err tracku w locie 0.335/0.716 m —
  pierwszy lot programu z zamkniętą pętlą na uczonym detektorze.
- **S4 kampania C** (`RAPORT_DET_S4.md`): 12 rund × {FEED-B, FEED-V2} × NCP za
  JEDNYM podejściem — 24/24 booty VALID (nr 14–37, zapas 0/3), **n_common 48/48**;
  **pass(B)=47 · pass(V2)=13 · Δ=34**.

## §3. Kampania C — Δ i dekompozycje

Tabela 48 par: `results/DET/RAPORT_DET_S4.md` §3 (dane: `results/DET/camp/detS4_pairs.json`).

**WERDYKT (zdanie zamrożone PRE_2A §4): Δ = 34 ≥ 10 ⇒ „percepcja limituje wykonanie:
−34/48 par; mechanizm z telemetrii."** Dekompozycja obowiązkowa przy każdym cytowaniu
(§4). Kwalifikatory każdego cytowania: SITL, rendering syntetyczny, mono-zasięg ze
znanym rozmiarem, detektor doszkolony na klatkach tego symulatora i tej sceny,
geometria c-siatki, NCP; zakaz ekstrapolacji na realne sensory/warunki (PRE_2A §4).

- **Per bearing:** komórki bearing 0° (c00/c04/c08): V2 **12/12 PASS**, Δ=0; cała
  Δ pochodzi z bearing 90/180/270° (jedyny pass V2 poza bearing 0°: c07_s04,
  t_entry 26.9 s).
- **Per split detektora:** TRAIN 32 pary: B 32 / V2 9 · VAL 8: B 8 / V2 4 · TEST 8:
  B 7 / V2 0. TEST 0/8 to artefakt geometrii komórek (c06 bearing 180°, c09 bearing
  90°), nie dowód luki generalizacji — track w c06/c09 po akwizycji err_fresh p95
  0.61–1.49 m.
- **Sceno-świeżość (prereg ANEKS_DET-3 §2):** 46 par sceno-świeżych: Δ=33; 2 pary
  scene-in-train różne losy (c08_s03 V2 ✓ bearing 0°, c11_s01 V2 ✗ ślepy zawis) —
  o wyniku decyduje geometria akwizycji, nie znajomość sceny przez detektor.
- **Jedyna porażka B:** c09_s03 (d_min 1.17 m przy WYROCZNI, scenariusz intrinsycznie
  trudny; V2 też FAIL ⇒ para nie wnosi do Δ).
- **S-BEZP:** breach 0 we wszystkich 96 epizodach obu ramion; REFUSE 0/0 per gałąź;
  fałszywe odmowy pod szumem percepcji 0; d_min pozostaje miarą opisową
  (min 0.339 m c10_s03 V2).

## §4. Mechanizm akwizycji + rozstrzygnięcie smoke-vs-kampania (ANEKS_DET-4 §2–§3)

**Wszystkie 35 porażek V2 to brak akwizycji** — 29 epizodów ślepych (cel z bearing
90/180/270° nigdy nie wszedł w stożek sztywnej kamery FOV 99.7° przy dronie
w zawisie; 0 boxów), 6 akwizycji spóźnionych/utraconych (t_entry 14–20 s lub przelot
w ślepej fazie, d_min 0.34–1.5 m). **Ani jedna porażka nie jest błędem jakości
tracku** — po akwizycji percepcja uczona jest DOKŁADNIEJSZA od wyroczni (err_fresh
med per epizod 0.418/0.648 m vs FeedB 0.676/1.280). FEED_EXPIRE 8/48 — dropouty
marginalne. Koszt NIE siedzi w ogniwie kierunek/zasięg/dropout — siedzi w polu
widzenia toru akwizycji (kamera sztywna + zawis bez skanowania).

**Rozstrzygnięcie smoke-vs-kampania (klasa przyrządowa, do rejestru):** smoke S3
przeszedł c10_s01 (t_entry=0.0), kampania padła na tej samej parze (d_min 0.517).
Mechanizm: lock przed epizodem jest artefaktem choreografii bootu — w boocie
1-epizodowym cel wchodzi w stożek podczas rozbiegu (spawn/pozycjonowanie przy żywej
percepcji); w boocie 4-epizodowym teleport międzyepizodowy nie przecina stożka,
a nos zostaje po poprzednim epizodzie. Ten sam artefakt dał 5 wczesnych locków
w passach kampanii (falsy-zero t_entry, RAPORT_DET_S4 §9.4). Wniosek do rejestru
klas (obok „tryb testowany ≠ tryb lotny"): **smoke jednoepizodowy NIE jest
reprezentatywny dla geometrii akwizycji**. Brzmienie kanoniczne: **zdolności
poszukiwawczej system NIE MA — akwizycja zachodzi wtedy, gdy cel sam wejdzie
w stożek.**

## §5. KANON OBOWIĄZUJĄCY — ANEKS_DET-4 (verbatim §5)

**WOLNO** (każde zdanie niesie: SITL, rendering syntetyczny, mono-zasięg ze znanym
rozmiarem, detektor doszkolony na klatkach tego symulatora i tej sceny — komórki
held-out w bramce T, tło naziemne, geometria c-siatki, NCP):
- zdania 1–3 z werdyktu (§1 tego raportu) verbatim, z liczbami;
- „dron lata na kamerze, GDY cel wejdzie w stożek sztywnej kamery — bearing 0°: 12/12,
  po akwizycji track dokładniejszy od wyroczni" — zdanie ZAWSZE z geometrią;
- „Δ=34/48; mechanizm: brak zachowania poszukiwawczego (29/35 porażek = cel nigdy
  w kadrze)";
- „pierwsza kampania parowana wyrocznia-vs-percepcja w programie: 48/48 par ważnych,
  zero powtórek".

**NIE WOLNO:**
- „dron lata na kamerze" bez kwalifikatora akwizycji;
- przypisywać Δ detektorowi, zasięgowi ani dropoutom tracku — telemetria mówi
  przeciwnie (dekompozycja §4 obowiązkowa);
- „percepcja gorsza od wyroczni" jako ogólność — po akwizycji jest LEPSZA; koszt
  siedzi w polu widzenia, nie w estymacji;
- wnioskować lukę generalizacji detektora z TEST 0/8 kampanii (artefakt geometrii
  komórek c06/c09; werdykt generalizacji niesie bramka T i err po akwizycji
  0.61–1.49 m);
- cytować d_min <1 m jako naruszenie bezpieczeństwa — kolizja nie jest przedmiotem
  osłony (geofence/POS); d_min pozostaje miarą opisową, jak w całym programie;
- ekstrapolacji na realne sensory/warunki (PRE_2A §4 verbatim).

## §6. Rozliczenie predykcji (ANEKS_DET-4 §6; pełny zapis w KSIEGA_PREDYKCJI sekcja NOGA DET)

**P-DET-1 ✓** (0.55; dolot 12/12 w 1 sesji) · **P-DET-2 ✓** (0.80; v8n bez eskalacji,
T1 z sufitem) · **P-DET-3 ✓** (0.75; T2 1.365) · **P-DET-4 ✓** (0.50; smoke za 1.
podejściem) · **P-DET-5 ✗** (0.55; Δ=34 zamiast ≤4) · pod-predykcja REFUSE ≥1 (0.20):
nie zaszła — zaszła strona 0.80 (REFUSE=0). **Suma nogi: 4✓/1✗.** Kalibracja CC:
prawo dwukierunkowe z ANEKS_2A-4 potwierdzone WEWNĄTRZ jednej nogi — komponent uczony
znów przebił oczekiwania (detektor > wyrocznia), gotowość SYSTEMOWA znów przeszacowana;
doprecyzowanie reguły: „gotowość systemowa" obejmuje geometrię sensoryczną (pole
widzenia, choreografia akwizycji), nie tylko integrację software'ową.

## §7. Rejestr odchyleń nogi (ANEKS_DET-4 §7)

1. Kadencja bimodalna zrzutu/przetwarzania 7.6/14.7 Hz per boot (S1 i S4; narzędziowa,
   nie bramkująca; ANEKS_DET-1 §2a).
2. Errata kosmetyczna F3 tabeli S1 (59, nie 62).
3. Ogon zbliżeniowy d<6 m (pasmo poniżej korpusu treningowego Z p5 6.5 m; w porażkach
   kampanii NIE uczestniczy — ANEKS_DET-3 §2, RAPORT_DET_S4 §6).
4. client_e2e per-epizod — właściwość klienta FROZEN, przechwyt driverem (zero zmian
   kodu; RAPORT_DET_S4 §1).
5. Artefakt granicy epizodu w maximach err (nazwany przed lotami, commit 37eeb370).
6. Falsy-zero t_entry (lock przed epizodem logowany jako null).
7. **Smoke jednoepizodowy niereprezentatywny dla akwizycji (§4 — nowa klasa
   rejestru).**

## §8. Roadmapa: AKW (akwizycja) — pozycja katalogu, NIE otwierana tym raportem

**Trigger:** przed jakimkolwiek roszczeniem pełnogeometrycznym kamery („dron lata na
kamerze w pełnej geometrii").
**Zakres:** skan yaw w zawisie przedakwizycyjnym jako zachowanie warstwy misji PRZED
ENTRY (nie zmiana sieci, nie zmiana osłony); warianty pre-aim/gimbal jako alternatywy.
**Aktywa gotowe (z DET, zero dodatkowej budowy):**
- cały tor V2: det_v2.pt 775ead15 + percep_proc/feed_vision_proc + wpis rejestru V2
  (feed_sha_v2 8015bd12), FROZEN;
- kampania-wzorzec do powtórki parowanej AKW-vs-bez (narzędzia detS4_*, siatka 48,
  sędziowanie i parowanie gotowe);
- 29 ślepych epizodów kampanii jako zbiór odniesienia (zero akwizycji do pobicia).

Porcelain przy CO-DET: tylko {ANEKS_DET-4.md, results/DET/RAPORT_DET.md,
results/KSIEGA_PREDYKCJI.md, KIERUNKI_PO_PLANIE.md} — jeden commit, zero bootów.
Push = Olga. STOP.
