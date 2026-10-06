# ANEKS_2A-3 — ratyfikacja N3-C (egzekutor feedu), wynik C1 jako pomiar „dead feed", wznowienie sondy

CC · 06.10.2026 · łańcuch 2A (po STOP-2A3, commity f8a0f9c + 08fb987 — bramka §5 wymaga ich
na origin). Samowykonalny: §5. Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-2A3

Przyjęte (weryfikacja CC z repo po pushu, przed lotami — bramka §5 to wymusza). Wykonanie
wzorcowe: C2 nieспalony, repro offline 1:1 (spin_once na egzekutorze globalnym, który
bench_flight już spinuje ⇒ wątek feedu ginie na pierwszym wywołaniu; dowód współistnienia
dedykowanego SingleThreadedExecutor ze spinem globalnym 5/5), bloker nazwany w pliku
FROZEN, STOP zamiast trzeciej drogi. Klasyfikacja: defekt budowy S1 ujawnialny wyłącznie
przez tor LIVE w procesie pętli — S1 nie latał, S2/S2b karmiły shadow w OSOBNYM procesie,
więc żaden dotychczasowy test nie mógł go zobaczyć. Wpis do odchyleń nogi; klasa dopisana
do rejestru: „tryb testowany ≠ tryb lotny (proces/egzekutor)". Błąd drivera (PYTHONPATH →
ros2cli → most) przyjęty jako narzędziowy, naprawiony w v2.

## §2. Wynik C1 — przyjęty jako WAŻNY pomiar trybu „percepcja MARTWA"

C1 nie jest sondą, którą zamówiono (kłamiąca percepcja), ale jest uczciwym pomiarem
trzeciego trybu degradacji: całkowita utrata feedu od t0 ⇒ **hover-hold na home przez cały
epizod (track_valid 0/791), 0 REFUSE, 0 breach, r_max 0.2 m; intruz GT przeszedł 1.64 m
od ślepego drona**. Fail-silent → fail-safe z konstrukcji (semantyka utraty tracka).
Wchodzi do RAPORT_2A jako S-BEZP wariant „dead feed", obok przyszłego wariantu „lying
feed" z wznowionej sondy. Zdanie kanonu (przy zamknięciu) będzie rozróżniać te tryby.

## §3. Ratyfikacje

- **N3-C — PRZYJĘTE:** edycja FeedVisionLive: dedykowany SingleThreadedExecutor + własny
  wątek spin dla węzła feedu; rdzeń YOLO/MTI/admisja/pinhole NIETKNIĘTY. Diff verbatim
  w raporcie; nowy sha feed_vision i feed_sha do FREEZE_2A; test jednostkowy współistnienia
  ze spinem globalnym (wzór repro) do pytest.
- **Runtime-override w driverze — ODRZUCONE** z przyczyną z raportu: zmiana zachowania
  toru lotnego bez śladu w bajtach to dokładnie klasa, której program zakazuje.
- **Budżet:** C1 poleciał ⇒ liczy się (5 lotnych z ≤31). Wznowienie = C1r + C2 ⇒ po
  sondzie 7/31. Pula powtórek bez zmian.

## §4. Wznowienie sondy + warunek ŻYWOŚCI feedu (instrumentowy, prerejestrowany teraz)

C1r (c11_s01) + C2 (c08_s03), reżim ANEKS_2A-2 §3 bez JEDNEJ zmiany (S-BEZP kryterialne:
breach=0 wymagane, REFUSE per gałąź = wpis, REFUSE(POS) ⇒ STOP; S-MISJA opisowe).
NOWY warunek ważności INSTRUMENTU (żeby ślepy boot nigdy więcej nie udawał sondy):
w pierwszych 30 s epizodu feed musi wykazać życie — ≥1 świeża próbka tracku (choćby FP)
ALBO ≥10 klatek przetworzonych przez detektor (licznik w logu feedu). Brak ⇒ boot
NIEWAŻNY instrumentowo (nie wchodzi do S-BEZP, nie liczy się jako wynik sondy), przerwij
i diagnozuj zamiast latać drugi ślepy epizod. To jest warunek klasy V2′ (ważność
przyrządu), nie kryterium wyniku — stąd wolno go dodać przed pomiarem.

## §5. Wykonanie (jedna sesja)

1. Bramka: origin/master zawiera f8a0f9c i 08fb987 (brak ⇒ STOP, prośba o push); ahead
   pusty; porcelain pełny; FROZEN wykonaniem.
2. ARCH-1: ten plik → korzeń VERBATIM, pierwszy commit.
3. N3-C + test + FREEZE_2A update (sha przed/po, feed_sha).
4. Sonda §4: C1r + C2, driver v2, dowody żywości feedu w raporcie per boot.
5. STOP-2A4: commit (diff N3-C, test, booty, `results/2A/RAPORT_2A_S4.md` — S-BEZP
   z gałęziami, S-MISJA, żywość, porcelain). Push = Olga; „wypchnięte". Dalej:
   **ANEKS_2A-4** — zamknięcie nogi (werdykt całości, kanon z trzema trybami percepcji:
   zdrowa-w-kadrze / kłamiąca / martwa, KSIĘGA, CO-2A; detektor-v2 do katalogu). STOP.
