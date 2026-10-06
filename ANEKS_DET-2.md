# ANEKS_DET-2 — werdykt bramki T: PASS; zwolnienie budowy FEED=V2 i smoke (S3)

CC · 07.10.2026 · łańcuch DET (po STOP-DET2, commity 9a838eb→c86ec13 na origin).
Samowykonalny: §4 (sesja S3). Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-DET2

Przyjęte po weryfikacji CC z repo WŁASNYM kodem, nie lekturą raportu: ARCH-1 bajt-w-bajt
(fbc9cd8a…); zakres commitów = korzeń + net/frozen/det_v2.pt + results/DET/**;
**T2 pooled odtworzone niezależnie z surowych trk_pos_ned vs gt_intruder.jsonl:
p50 1.218 / p95 1.365 / max 1.843 — co do milimetra** pod kanoniczną regułą okna GT
(n 1263 vs 1262 — tolerancja brzegu okna, bez wpływu; poza oknem GT ogon 16 próbek
odrzucany z konstrukcji, jak w pipeline etykiet); **T1 przeliczone własnym center-in-box:
691/691 (c06) i 575/576 (c09)** — zgodne co do klatki; θ\*/train_summary/T2_test_pooled
zgodne z artefaktami; det_v2.pt w repo, sha 775ead15… = FREEZE_DET wiersz FINALNY;
eskalacja nie zaszła z przyczyną liczbową (VAL 0.725/0.778); TEST dotknięty raz;
yolo26n.pt — nota higieniczna przyjęta (artefakt AMP-checku trenera, usunięty, poza
inwentarzem). Wykonanie wzorcowe, zero bootów.

## §2. WERDYKT BRAMKI T — PASS (formalnie)

- **T2 (nośnik): PASS** — err p95 pooled 1.365 m ≤ 3.0 na held-out komórkach c06+c09,
  zapas 2.2×, poziom referencji FeedB (1.258 m). **Kampania C: warunek 1/2 SPEŁNIONY.**
- **T1 (mechanizm): PASS z sufitem** — 100.0 % / 99.8 % top-1-na-celu vs 3–12 % w locie
  2A i 10.3 % maksimum sweepa zero-shot. Separator, którego nie było, istnieje po
  doszkoleniu.
- **θ\* (opisowy): separacja NIEPEŁNA** — na VAL 2 boxy tła, jeden z conf 0.8055 > θ\*;
  na TEST TP 99.9 % / FP 0.08 %. To potwierdza zamrożoną decyzję: **θ do runtime NIE
  wchodzi**, jedynym filtrem pozostaje admisja struktura∧MTI (bajty bez zmian).
- Zdanie robocze (pełny kanon przy zamknięciu nogi, kwalifikatory PRE §0/§7 obowiązują
  w każdym cytowaniu): „fine-tune na darmowych etykietach projekcyjnych z GT naprawia
  ogniwo detektora w tej scenie: p95 1.365 m na niewidzianych komórkach, top-1 ~100 %".
- Rozliczenie bieżące: **P-DET-2 ✓, P-DET-3 ✓** (formalnie przy zamknięciu; noga dotąd 3/3).

**Niezmierzone pozostaje (jawnie):** replay to pętla OTWARTA — klatki pochodzą z lotów
sterowanych FeedB, trajektoria nie reagowała na błędy detektora. Lot na FEED=V2 domyka
pętlę. Smoke mierzy dokładnie to ryzyko (P-DET-4 wycenione 0.50).

## §3. Wymóg konstrukcyjny S3 — WSPÓLNE BAJTY przyrządu i toru lotnego

det_replay (de0feb37) dowiódł wzoru: rdzeń FeedVision (acc81df7) importowany READ-ONLY
+ detektor wstrzykiwany. Proces percepcji lotnej MUSI używać tego samego wzoru — **ZAKAZ
reimplementacji MTI/admisji/pinhole/REFRESH/starzenia**. Wtedy bramka T i lot różnią się
wyłącznie źródłem klatek (dysk vs topic) i detektorem… którym jest ten sam det_v2.
Domknięcie klasy „tryb testowany ≠ tryb lotny" konstrukcją, nie testem.

## §4. Wykonanie S3 (jedna sesja; booty: smoke ≤2 + naprawcze ≤2)

1. **Bramka:** origin/master zawiera c86ec13; ahead pusty; porcelain pełny; FROZEN
   wykonaniem (det_v2 775ead15, feed_vision acc81df7, bench_flight 05137098,
   det_replay de0feb37, rejestr feedów sprzed edycji).
2. **ARCH-1:** ten plik → korzeń VERBATIM, pierwszy commit.
3. **Budowa (PRE §6 + §3 wyżej):** NOWE pliki: `harness/det_v2.py` (wrapper wag
   775ead15, imgsz 640, bez progu conf); `harness/percep_proc.py` (proces potomny:
   własny kontekst rclpy + DEDYKOWANY egzekutor — lekcja N3-C; subskrypcje
   obraz+pos+att; rdzeń FeedVision read-only z wstrzykniętym det_v2; publikacja próbek
   tracku po UDS jsonl — wzór shadow); `harness/feed_vision_proc.py` (cienki klient
   FeedVisionProc: odczyt NIEBLOKUJĄCY, zero egzekutorów w wątku bencha; kontrakt
   set_feed dict VERBATIM — trk_pos_ned, trk_vel_ned, track_age_s, track_valid,
   feed_sha; semantyka track_valid>1.0 s ⇒ hover-hold konsumenta NIETKNIĘTA).
   EDYCJA istniejących: WYŁĄCZNIE rejestr feedów, wpis FEED=V2 additive. **feed_sha V2
   = hash(params ∪ sha det_v2) → FREEZE_DET.** Teardown: driver zabija proces percepcji
   po bootcie (zero sierot, proc_gate czysty).
   **Testy przed lotem (pytest):** kontrakt dict; cykl życia (spawn→publish→kill);
   test klasy kolizji egzekutora (wątek-lustro bencha + klient, wzór test_aneks3);
   latencja offline na strumieniu z dysku (sanity ≪ 0.25 s).
4. **Smoke: 1–2 booty, FEED=V2, CONTROLLER=net (0337d5ea), scenariusz c10_s01**
   (FROZEN PRE §6), pełne uzbrojenie. Ważność: V2′ + żywość feedu VERBATIM ANEKS_2A-3 §4
   (≥1 świeża LUB ≥10 klatek w 30 s). **Bramki runtime:** kadencja PRZETWARZANIA klatek
   ≥8 Hz p50 (def. (a) PRE §5 — czysto czasowa, pre-admisja); opóźnienie end-to-end
   (stempel klatki → próbka u klienta) p95 ≤0.25 s. **S-BEZP (kryterialne):** breach
   R_E=0 wymagane; REFUSE per gałąź = wpis; REFUSE(POS) ⇒ STOP. Opisowo (bez progów):
   kadencja świeżych (def. b), **err tracku vs GT w locie — pierwsze zamknięto-pętlowe
   echo T2**, rozkład admisji, r_max/z_max, frakcja hover-hold.
   Fail bramki runtime = defekt budowy (PRE §6): ≤2 booty naprawcze, potem STOP i ANEKS;
   zdania „percepcja limituje czasowo" nie wolno wypowiedzieć bez obalenia dowodu shadow.
5. **STOP-DET3:** commit (kod+testy+booty+`results/DET/RAPORT_DET_S3.md`: budowa
   [co importowane, co nowe], feed_sha V2, tabela smoke z bramkami i S-BEZP, żywość,
   porcelain). Push = Olga („wypchnięte"). Dalej: **ANEKS_DET-3** (werdykt smoke; przy
   PASS — zwolnienie KAMPANII C per PRE §7: 12 rund × {B, V2}). STOP.

ZAKAZ w S3: edycji plików FROZEN (feed_vision, bench_flight, r02/**, det_labels,
det_replay, det_v2.pt); jakiegokolwiek treningu/ewaluacji na TEST; dodawania progu conf
do toru lotnego; zmian progów bramek; lotów poza §4.4. Budżet po S3: ≤16 z ≤45.
