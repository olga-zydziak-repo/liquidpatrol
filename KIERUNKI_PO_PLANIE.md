# KIERUNKI_PO_PLANIE — kolejka nóg LiquidPatrol v2

CC · 10.09.2026 · stan wejściowy: pozycje 1–6 planu CLOSED, teza zmierzona z obu stron, piny 5/5,
ledger 12 wpisów. Reguła nadrzędna bez zmian: jedna noga naraz, każda z reconem i PRE, kryteria przed
pomiarem. Ten dokument jest KOLEJKĄ z triggerami, nie bufetem.

## Warstwa 0 — nie-nogi, do zrobienia najpierw (dni, nie tygodnie)

0a FOLLOW-UP SPRIND. Nie eksperyment — list. Brief z 30.08 obiecywał trajektorię; jest wykonana w 11 dni
z domknięciem tezy z obu stron. Materiał gotowy: brief + DEMO_V2.mp4 + RAPORT_NET + RAPORT_K2. Koszt:
pół wieczoru redakcji. Rekomendacja: teraz, póki daty są świeże. Kryterium porażki nie istnieje —
najgorszy wynik to brak odpowiedzi, a materiał i tak zostaje.

0b NOTA SYNTEZY (whitepaper wewnętrzny, kandydat na publiczny). Jeden dokument, który składa K1 + nogę
sieci + K2 w miniaturę assurance case: certyfikowana osłona + wymienny kontroler uczony + zmierzone
przejęcie + prowieniencja. To jest artefakt, który pracuje na Twój pivot niezależnie od SPRIND
(rozmowy, portfolio, ewentualna publikacja warsztatowa). Koszt: ~1 tydzień wieczorów, zero bootów.
Piszę szkielet na sygnał.

## Warstwa 1 — nogi wzmacniające istniejące roszczenia (tanie, dowodowe)

1a KONTROLA ARCHITEKTURY: GRU o budżecie ~1.9k parametrów + MLP k=20, ten sam zbiór, ten sam protokół
(wszystko istnieje: dane, sędziowie, kolejki). Pytanie: czy przewagę dała SPECYFIKA liquid, czy
jakakolwiek rekurencja, czy po prostu dłuższe okno. Trigger: decyzja o publicznym twierdzeniu
„pamięć-przez-dynamiką transferuje" — bez kontroli to twierdzenie nie przetrwa recenzji; z kontrolą
odwraca null LiquidWatch z mechanizmem. Koszt: 1–2 sesje + ~24 booty. Śmierć kierunku: GRU dorównuje
NCP ⇒ roszczenie spada do „rekurencja > okno" — nadal publikowalne, mniej efektowne. Każdy wynik
wartościowy, więc to najlepszy stosunek ceny do dowodu w katalogu.

1b WERYFIKACJA FORMALNA. Dwie części o różnej trudności: (i) osłona w Z3 — dowód, że implementacja
REFUSE/geofence odpowiada specyfikacji (Twój warsztat ProofGate przenosi się wprost; kod osłony jest
mały i pinowany, czyli stabilny cel); (ii) własności sieci — przy 1.9k parametrach i 8 wejściach
narzędzia weryfikacji sieci są w zasięgu; kandydackie własności: ograniczoność wyjścia (już
architektoniczna), zachowanie przy track_valid=0, monotoniczność składowej radialnej przy małym d.
Trigger: faza 2 SPRIND albo roszczenie publiczne. Koszt: 2–4 sesje, zero bootów. Śmierć: własność
niedowodliwa narzędziem ⇒ wynik częściowy (lista dowiedzionych + kontrprzykłady) — też raportowalny.

## Warstwa 2 — nogi nowej zdolności (każda zdejmuje jedną gwiazdkę z roszczeń)

2a PERCEPCJA W PĘTLI. Zastąpienie emulowanego feedu prawdziwym torem: kamera gz → detektor → tracker →
ten sam interfejs feedu (kontrakt już istnieje — feed był projektowany jako wymienny). To jest
największa pojedyncza gwiazdka w dzisiejszych roszczeniach („pod emulowanym feedem"). Wejście: artefakty
toru C. Koszt: duży, 2–3 tygodnie (detektor w pętli 20 Hz, latencja, kampania porównawcza feed-emulowany
vs feed-realny na tych samych ziarnach — parowanie gotowe). Śmierć: tracker nie trzyma kadencji/latencji
w kopercie SITL ⇒ wynik „percepcja limituje", ważny sam w sobie.

2b WIATR I RANDOMIZACJA DOMENY. Model wiatru w SITL + kampania odporności sieci i osłony. Tanie-średnie
(1 tydzień), a odpowiada na pytanie z rozmowy o lotnictwie: czy osłona zaczyna fałszywie odmawiać
w realnym szumie świata — bo jeśli tak, ścieżka 1:N pada na DOSTĘPNOŚCI, nie na bezpieczeństwie.
Ramię (−) z K4b daje bazę porównawczą. Śmierć: fałszywe REFUSE pod wiatrem = znalezisko pierwszej wagi.

2c INTRUZ ADWERSARYJNY (ucieka, manewruje przeciwko). Zmienia klasę zadania: nauczyciel skryptowy
przestaje wystarczać (pościg to nie orbita), więc to jest noga z nowym nauczycielem albo pierwszym
prawdziwym użyciem DAgger/RL. Duża (3+ tygodnie). Wejście: po 2a albo świadomie na feedzie emulowanym.

2d KONTYNUACJA PO UTRACIE GPS (nie lądowanie — powrót po zliczeniu/VIO). Jedyna noga, która ROZSZERZA
osłonę (nowa akcja bezpieczna ≠ D5), czyli dotyka certów i wymaga nowego dowodu klasy P2. Poważna,
dopiero po 1b(i), żeby rozszerzać rzecz już zweryfikowaną formalnie.

2e SPRZĘT / MULTI-DRON — poza horyzontem solo-SITL; trigger zewnętrzny (partner, finansowanie, faza
sprzętowa SPRIND). Zapisane, żeby istniało; nie planujemy, dopóki trigger nie padnie.

## Kolejność rekomendowana i kryterium wyboru

Najpierw 0a i 0b (dni, zero bootów, maksimum dźwigni na to, co już jest). Potem JEDNA noga, wybrana
jednym kryterium — co chcesz z programu mieć w horyzoncie 2 miesięcy:
- zdolność (system bliżej realności) ⇒ 2a percepcja, z 2b jako tanim przedsionkiem;
- dowód (faza 2 / rozmowy poważne) ⇒ 1b weryfikacja formalna;
- publikacja (twierdzenie o liquid) ⇒ 1a kontrola architektury.
Wszystko inne czeka w kolejce z triggerami. Otwarcie drugiej nogi przed zamknięciem pierwszej wymaga
zdania, które przekona CC — dotychczas takie zdanie nie padło ani razu zasadnie.

## Backlog §8 (bez zmian, porządkowe)

Polityka git dla .ulg (decyzja od tygodni odroczona, nieblokująca) · martwe inicjalizacje w gate (przy
następnym uprawnionym dotknięciu pinu) · allowlista procesów jako plik żywy · rozpoznawanie atrap
(nota z triggerem z 23.08, warunki bez zmian).
