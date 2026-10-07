# ANEKS_DET-3 — smoke PASS; ogon zbliżeniowy nazwany; ZWOLNIENIE KAMPANII C (S4)

CC · 07.10.2026 · łańcuch DET (po STOP-DET3, commity 0b8570c→6962c30→b7a5cab na origin).
Samowykonalny: §3 (sesje S4). Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-DET3

Przyjęte po weryfikacji CC z repo wykonaniem: ARCH-1 bajt-w-bajt (93be88e8…); zakres
commitów = korzeń + 3 nowe pliki harness + rejestr + results/DET/**; **rejestr: diff
przeczytany — wpis V2 czysto additive, B/V nietknięte** (2629bc40→ee1481f9); **wspólne
bajty potwierdzone grepem: percep_proc.py:93 `from harness.feed_vision import
FeedVision` (acc81df7 READ-ONLY), zero definicji MTI/admisji w pliku; det_v2.py bez
progu bramkującego** (conf=0.001 to podłoga telemetryczna ultralytics, top-1 = argmax).
Liczby przeliczone z surowych logów: kadencja 14.71 Hz (877 klatek, dt p50 0.0680),
E2E p95 0.084 s (n=626), err w locie 0.336/0.718/4.879 (n=489 vs 488 — brzeg okna GT),
feed_sha 8015bd12 w manifeście Z PROCESU ŁAWKI, V2′ dsw 0.9698, refuse 0, breach false,
d_min 2.018. Testy przedlotowe 4/4. Wykonanie wzorcowe; naprawczych 0/2.

## §2. Werdykt smoke: PASS — oraz ustalenie CC z surowych danych: OGON ZBLIŻENIOWY

**Obie bramki runtime PASS z zapasem (14.71≥8; 0.084≤0.25), S-BEZP czyste, żywość ALIVE
⇒ warunek 2/2 kampanii C SPEŁNIONY.** Wnioski mechanizmowe raportu przyjęte: kontencję
usunęła architektura (6.7–7.2 → 14.71 Hz przy tych samych bajtach rdzenia); separator
po doszkoleniu działa w pętli zamkniętej (fresh 521/877 przez nietkniętą bramę).
**P-DET-4 ✓** (formalnie przy zamknięciu; noga 4/4).

**Ogon zbliżeniowy (ustalenie CC, opisowe):** wszystkie próbki err >1.5 m leżą w JEDNYM
oknie t_rel 25.5–26.3 s, tuż po bliskim przelocie (d_min 2.06 @ 21.4); dystans w oknie
~3.8 m, boxy świeże z conf 0.00–0.20 (normalnie ~0.79) przy krawędzi kadru, Z z
szerokości 4–7 m ⇒ err 3.5–4.9 m; po otwarciu dystansu samonaprawa <1 m. Mechanizm:
**zasięg zszedł PONIŻEJ pasma treningowego (korpus Z p5 = 6.5 m)** + przycięty box łamie
pinhole znanej szerokości. Klasyfikacja: właściwość rozkładu treningowego i geometrii
bliskiego pola, nie defekt budowy; w nodze BEZ zmian (admisja/wagi/progi frozen); wpis
do rejestru zjawisk. Konsekwencja prerejestrowana: telemetria kampanii niesie OPISOWO
err w paśmie d<6 m osobno (pole analizy przy interpretacji Δ, NIE kryterium).

**Druga prerejestracja uczciwości (ustalenie CC, zanim poleci kampania):** stary korpus
2A w TRAIN zawiera klatki ze scenariuszy c08_s03 i c11_s01 — a OBA leżą w siatce
kampanii (r9 i r3). Dolot był rozłączny z kampanią (blok 2), ale te dwa scenariusze
bloku 1 NIE są detektorowi sceno-świeże (≈172+176 pozytywów w treningu). Werdykt Δ
liczy się na 48 parach VERBATIM (progi PRE_2A nietykalne); raport S4 niesie opisową
dekompozycję: Δ na 46 parach sceno-świeżych osobno. Przypis prerejestrowany TERAZ,
żeby nie był post-hoc.

## §3. Wykonanie S4 — KAMPANIA C (24 booty + zapas 3; 1–2 sesje lotne)

1. **Bramka:** origin/master zawiera b7a5cab; ahead pusty; porcelain pełny; FROZEN
   wykonaniem (det_v2 775ead15, feed_sha_v2 8015bd12, rejestr ee1481f9, feed_vision
   acc81df7, bench_flight 05137098, ncp 0337d5ea, piny 5/5, certy 9/9).
2. **ARCH-1:** ten plik → korzeń VERBATIM, pierwszy commit.
3. **Konfiguracja (PRE_2A §3-C VERBATIM, podmiana FEED-V→FEED-V2):** 12 rund × 2 booty
   {FEED-B, FEED-V2} × NCP; **siatka 48 i przydział rund JAK LIQ (zweryfikowany z repo
   przez CC):** r1 c00–c03×s01 · r2 c04–c07×s01 · r3 c08–c11×s01 · r4–r6 analogicznie
   ×s02 · r7–r9 ×s03 · r10–r12 ×s04. Rotacja kolejności ramion naprzemienna per runda
   (nieparzyste B→V2, parzyste V2→B). Reżim bootów jak dolot/smoke: driver etapowy,
   GZ_IP=127.0.0.1, proc_gate, cooldown ≥300 s, wyłączność, manifesty 1. klasy
   (weights 0337d5ea, feed_sha per ramię, sha logów percep/klienta w bootach V2).
4. **Ważność:** V2′ per boot; booty V2 dodatkowo **żywość feedu VERBATIM ANEKS_2A-3 §4**
   (martwy feed = NIEWAŻNY instrumentowo, nie wchodzi do par). Boot INVALID ⇒ 1 powtórka
   z zapasu (3) ⇒ dalej wypadanie parowe (do Δ wchodzą epizody wspólnie ważne);
   **n_common < 40 ⇒ STOP.**
5. **S-BEZP:** osłona uzbrojona bez zmian; **REFUSE = wynik epizodu + wpis z gałęzią**
   (fałszywe odmowy pod szumem percepcji = osobny licznik — pytanie nogi W w ostrzejszej
   wersji); **REFUSE(POS) lub breach ⇒ STOP natychmiast.**
6. **Telemetria per epizod:** err feedu vs GT (p50/p95/max), frakcja fresh,
   FEED_EXPIRE/dropouty, z_max, r_max, d_min, **err w paśmie d<6 m osobno (opisowo,
   §2)**.
7. **Werdykty (progi VERBATIM PRE_2A §4), Δ = pass(B) − pass(V2) na 48 parach:**
   Δ≤4 ⇒ „system przeżywa zejście z wyroczni: koszt percepcji ≤4/48 na sparowanych
   scenariuszach"; Δ≥10 ⇒ „percepcja limituje wykonanie: −Δ/48, mechanizm z telemetrii";
   5–9 ⇒ strefa opisowa; V2 lepszy o ≥3 ⇒ zdanie jawne + podejrzliwość wobec przyrządu.
   Kwalifikatory każdego cytowania: SITL, rendering syntetyczny, mono-zasięg ze znanym
   rozmiarem, **detektor doszkolony na klatkach tego symulatora i tej sceny (komórki
   held-out w bramce T; 46/48 par sceno-świeżych, przypis §2)**, geometria c-siatki,
   NCP. Dekompozycje opisowe w raporcie: Δ na 46 parach sceno-świeżych; Δ per komórka
   z oznaczeniem TRAIN/VAL/TEST; udział ogona d<6 m w porażkach V2, jeśli wystąpią.
8. **Rytm:** przerwanie WYŁĄCZNIE na granicy rundy; przy przerwie STOP-DET4a = raport
   stanu częściowego BEZ interpretacji Δ; żadnych decyzji na podstawie cząstkowych
   liczników — kampania leci do 12 rund, chyba że zadziała twardy STOP (breach,
   REFUSE(POS), n_common<40, budżet). Budżet nogi po S4: ≤40 z ≤45.
9. **STOP-DET4:** commit (manifesty par, narzędzie parowania, `results/DET/RAPORT_DET_S4.md`:
   tabela 48 par, Δ z licznikami, REFUSE per gałąź, telemetria zbiorcza, dekompozycje §7,
   porcelain). Push = Olga („wypchnięte"). Dalej: **ANEKS_DET-4** — werdykt Δ, kanon nogi,
   KSIĘGA, CO-DET (zamknięcie). STOP.

ZAKAZ w S4: jakichkolwiek zmian kodu, wag, progów, rejestru i dataset; treningu;
ewaluacji offline na TEST; lotów poza §3. Ogon zbliżeniowy NIE uprawnia do żadnej
interwencji w locie — jest opisem, nie usterką.
