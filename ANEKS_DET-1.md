# ANEKS_DET-1 — przyjęcie STOP-DET1, odchylenie kadencji nazwane, ZWOLNIENIE TRENINGU (S2)

CC · 06.10.2026 · łańcuch DET (po STOP-DET1, commity 579ff1b→12d2b59→aab2e6f na origin).
Samowykonalny: §4 (sesja S2, ZERO bootów). Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-DET1

Przyjęte po weryfikacji CC z repo wykonaniem, nie lekturą: ARCH-1 bajt-w-bajt zgodny
z ratyfikowanym PRE_DET (sha256 007e6f29…); zakres commitów = korzeń + results/DET/**,
zero artefaktów treningu; etykiety przeliczone z plików: **6 154 pozytywy + 59 negatywów**
zgodnie ×12 bootów; split przeliczony z manifestu: TRAIN 4 157+187 / VAL 1 078+17 /
TEST 1 267+8, c06+c09=test, stary korpus wyłącznie-train, dataset.yaml bez TEST;
T4 PASS potwierdzony z artefaktu (p95 31.489 ∈ [20.45, 81.8], na-celu 10.4%, admisja
żywa, wykonany PRZED dolotem); manifesty ×12: refuse 0, breach false, weights 0337d5ea,
feed_sha B identyczny z 2A (da9ef2f4), frames_set_sha ×12 zgodne z tabelą, proc_gate
CLEAN; żywość ≥100 przeliczona z meta ×12 (163–275 — różnice ±9 vs raport to inne t0
okna, obie strony z zapasem); FREEZE_DET kompletny (wagi bazowe f59b3d83/1f47a78b
z rozmiarami, narzędzia, przepis); próbka PNG obejrzana, w tym boot testowy D07 —
etykieta na sylwetce. Wykonanie wzorcowe; pula powtórek 0/2.

## §2. Odchylenia przyjęte (rejestr nogi)

**(a) Kadencja zrzutu BIMODALNA, nie „pełna ~15 Hz" (ustalenie CC z meta.jsonl;
klasa: narzędzie):** dt p50 kolejnych klatek = 0.068 s (14.7 Hz) w 5 bootach
(D03, D07, D10, D11, D12) i **0.132 s (7.6 Hz — dokładnie co druga klatka) w 7 bootach**
(D01, D02, D04–D06, D08, D09). Mechanizm spójny z shadow_summary: wall/klatkę p50
15 ms, p95 55 ms — cykl okresowo przekracza okno 66 ms i pętla osiada na co-drugiej
klatce; to driver/narzędzie, nie frozen. Konsekwencje ocenione:
- trening: bez wpływu (6 154 pozytywów ≫ potrzebne; klatki to nadal te same rozkłady);
- **bramka T: nienaruszona — OBA booty TEST (D07, D10) są pełnej kadencji 14.7 Hz**,
  replay konsumuje rzeczywiste dt bez resamplingu;
- VAL: D03 pełny, D05 połówkowy ⇒ dynamika admisji na D05 odrobinę surowsza (k=3 trwa
  0.39 s zamiast 0.2 s) — bias KONSERWATYWNY na decyzji eskalacji, akceptowalny;
- zdanie „wierny replay 15 Hz" wolno odnosić do 5 bootów pełnej kadencji; dla 7
  pozostałych dt=0.132 s (i tak 4× lepiej niż 0.528 recon).
Litera PRE §2 („pełnej kadencji 15 Hz") niedotrzymana w 7/12 bootach — wpis jawny,
bez powtórek (gate'owała żywość, nie kadencja; korpus wystarczający).

**(b) Errata kosmetyczna tabeli raportu:** kolumna F3 sumuje do 62, kanon ze stats.json:
**F3 = 59 (out_of_fov 19 + behind 40) = dokładnie liczba negatywów**; suma flag
6 154+692+1 131+59 = 8 036 = jpg co do klatki. Liczby kanoniczne = stats.json;
D06/D10 mają F3=0.

## §3. Rozliczenie bieżące

**P-DET-1 ✓** (dolot 12/12 VALID w jednej sesji bez puli; p 0.55 po korekcie ↓) —
pierwsza trafiona predykcja integracyjna od czasu wprowadzenia reguły kalibracyjnej;
formalne rozliczenie przy zamknięciu. Program: breach 0 / REFUSE 0 pozostaje prawdą
o wszystkim, co kiedykolwiek poleciało uzbrojone (teraz 12 bootów więcej).

## §4. ZWOLNIENIE TRENINGU — sesja S2 (zero bootów, GPU; wykonanie w jednej sesji)

1. **Bramka:** origin/master zawiera aab2e6f; ahead pusty; porcelain pełny; FROZEN
   wykonaniem (w tym det_labels 8f7430cd, det_replay de0feb37, labels_set_sha 33dbebba
   — re-hash przed treningiem; rozjazd ⇒ STOP).
2. **ARCH-1:** ten plik → korzeń VERBATIM, pierwszy commit.
3. **Trening v8n** przepisem FROZEN (FREEZE_DET/PRE §4 — bez jednego odstępstwa;
   fallback OOM batch→8 zliczony). Selekcja: best.pt fitness ultralytics na VAL.
4. **Replay VAL** (det_replay, rzeczywiste dt): err p95, T1, rozkład admisji per komórka
   (c02/c04 osobno — nota kadencji D05 z §2a przy interpretacji).
   **Eskalacja v8s (RAZ, PRE §4): WYŁĄCZNIE gdy VAL err p95 > 3.0 m.**
5. **Model finalny** = przy eskalacji ten z niższym err p95 na VAL (remis ⇒ v8n);
   **TEST RAZ zawsze** (werdykt nogi musi nieść liczbę TEST, także w strefach §8 PRE):
   replay c06+c09 → **T2 err p95 (nośnik: ≤3.0 kampania odblokowana / 3.0–6.0 strefa
   ANEKS-sonda / >6.0 po eskalacji = ŚMIERĆ-DET)**, T1 top-1-na-celu (próg opisowy 80%),
   θ\* wybrany na VAL i raportowany na TEST (do runtime NIE wchodzi). Po TEST żadnych
   dalszych treningów/ewaluacji — cokolwiek wyszło.
6. **Artefakty:** `net/frozen/det_v2.pt` + sha do FREEZE_DET (model finalny, nawet gdy
   bramka padła — forensyka); replay jsonl/json do results/DET/; krzywe treningu
   (podsumowanie liczbowe, nie katalog runs/).
7. **STOP-DET2:** commit (raport `results/DET/RAPORT_DET_S2.md`: przebieg treningu
   [czas, epoki, fallbacki], tabela VAL per model, TEST raz z trzema liczbami, decyzja
   eskalacji z przyczyną, FREEZE_DET update, porcelain). Push = Olga („wypchnięte").
   Dalej: **ANEKS_DET-2** (werdykt bramki T; przy PASS — zwolnienie budowy V2 i smoke S3).
   STOP.

ZAKAZ w S2: bootów i SITL; dotykania TEST przed krokiem 5; zmian dataset/etykiet;
więcej niż jednego runu na architekturę; jakiejkolwiek edycji plików FROZEN.
