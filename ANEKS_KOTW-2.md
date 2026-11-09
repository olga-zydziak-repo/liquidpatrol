# ANEKS_KOTW-2 — obwód 0/576 ⇒ prereg zachodzi: KOTW CLOSED W CAŁOŚCI (0 bootów); granica zmierzona: pozioma kamera nie ma pozycji kotwic dającej naraz krótką przerwę i bliski zasięg

CC · 8.11.2026 · łańcuch KOTW, po STOP-KOTWR2 (f4b01cfb + fb7415c5 na
origin). Aneks zamykający nogę. Sygnały bez numeru odrzucasz.

## §1. Weryfikacja CC z repo

- Bramki: ANEKS_KOTW-1 w korzeniu **byte-check PASS** (bd5d3332),
  KSIĘGA §3 reconu 1 verbatim i append-only względem HEAD~2; zakres r2
  czysty (nowe pliki wyłącznie `results/KOTW_RECON/r2/**`, 0 bootów).
- Cztery narzędzia r2 uruchomione u CC z wywołaniami z raportu:
  `kotw2_r2r5.py` (na committed raw: `r1p_obwod.json`,
  `r2p_poprawka.json`, `r5p_pila.json` **identyczne bajtowo**),
  `kotw2_yaw.py` i `kotw2_r4_szersze.py` **identyczne bajtowo**.
  `kotw2_obwod.py`: wszystkie liczby identyczne; 96/~tysięcy okien ma
  inną etykietę `faza` — mechanizm nazwany: `faza_dom` łamie remis
  dominanty przez `max(set(seg), key=count)`, a porządek iteracji po
  zbiorze zależy od środowiska (hash). Zero wpływu: agregat policzony
  z MOJEGO raw daje **576/576 wpisów kombinacji identycznych**
  z committed, w tym dopuszczalne 0/576. Znalezisko, nie wada liczb.
- Niezależna kontrola CC (własny kod GT/kwaternionów, bez narzędzi
  wykonawcy): c05_s01 (najgorszy epizod reconu 1) przy n 6 / R_a 32 /
  h 2 — max przerwa 3.1 s (≤ 9.44 s maksimum siatki, spójne) i zasięg
  do najbliższej widocznej kotwicy p50 32.2 / max 45.0 m — dalekie
  zasięgi potwierdzone niezależnie.
- Arytmetyka decydująca z zamrożonej krzywej 2d (ae19f66c):
  ε_b(9) = 3.105 ⇒ budżet na poprawkę w komórce najgorszej orbity
  5.17 − 3.105 − 1.524 = **0.54 m**, a poprawka z obwodu ma **2.50 m
  w wariancie optymistycznym** (4.6× za dużo). Suma 2.50 + 3.105 +
  1.524 = 7.12 > 5.17 — zgodnie z raportem.

## §2. Werdykt i granica zmierzona

**Prereg zachodzi** (PROMPT_KOTW_R2 §R6′, ANEKS_KOTW-1 §2: jedyna
reformulacja, trzeciego podejścia nie ma): 0/576 kombinacji
dopuszczalnych ⇒ **KOTW CLOSED W CAŁOŚCI, za 0 bootów** — dziewiąte
zamknięcie przy biurku w programie, drugie w tej nodze.

Granica, którą oba recony razem mierzą:

- **Środek przegrywa na czasie:** najdłuższa przerwa orbity 37.1 s
  (CC niezależnie: 38.6 s) ⇒ ε_b(37) 4.567 + Δ_D5 1.524 = 6.09 > 5.79
  przy idealnej poprawce.
- **Obwód przegrywa na dokładności:** przerwy spadają do 9.4 s
  (start ~0 s, widoczność 87% orbity — hipoteza geometryczna reconu 2
  potwierdzona), ale kotwica jest wtedy w 23–44 m (p50 29 m), skąd
  pozioma kamera daje poprawkę 2.5 m przy budżecie 0.54 m.
- **Para kotwic nie ratuje:** usuwa błąd kursu, lecz radialny błąd
  elewacyjny przy płytkiej depresji mnoży się słabą geometrią
  przecięcia — najlepszy tryb „2" domyka 5/48 komórek.
- **Bias yaw jest prawdziwy:** rozdzielony od dopasowania czasu
  (opóźnienie niespójne co do znaku), stały bias estymatora przy
  zdrowym GNSS −0.6…−5.1°, δψ_ZMIERZ = 5.8° — słusznie w budżecie.
- **R4′:** w literalnym paśmie admisyjnym [5, 18] m przejęcia tracku
  geometrycznie niemożliwe (0 próbek / 24 geometrie); koincydencja
  ≤ 5° z intruzem na 18–45 m do 8.3% próbek orbity — pasmo nie jest
  zmierzoną granicą detekcji, więc każda przyszła kotwica w polu
  widzenia wymaga bramki pozycji przewidywanej jako warunku PRE.

Zdanie graniczne do kanonu: **przy poziomej kamerze misji nie istnieje
rozmieszczenie kotwic dające jednocześnie krótką przerwę widoczności
i zasięg, z którego poprawka mieści się w budżecie komórki.** Dźwignie
poza FROZEN/misją, nazwane i nieotwarte: kamera pochylona lub druga
w dół, okresowe „spojrzenie wstecz" w trajektorii, kotwice obwodowe
z lepszym źródłem kursu.

## §3. KSIĘGA (append-only przy commicie §CO)

```
## KOTW recon 2 i zamknięcie nogi (ANEKS_KOTW-2, 8.11.2026): obwód
0/576 ⇒ KOTW CLOSED W CAŁOŚCI (0 bootów)
- Obwód naprawia czas (najgorsza przerwa orbity 37→9.4 s, start ~0 s,
  widoczność 87%), ale nie dokładność: poprawka z 23–44 m to 2.5 m
  optymistycznie przy budżecie 0.54 m w komórce najgorszej orbity;
  para kotwic 5/48 (geometria przecięcia mnoży błąd elewacyjny).
  Granica: pozioma kamera nie daje naraz krótkiej przerwy i bliskiego
  zasięgu. Dziewiąte zamknięcie przy biurku; cała noga za 0 bootów.
- Bias yaw −3° z S4 rozdzielony: prawdziwy błąd estymatora
  (−0.6…−5.1°, δψ 5.8°), nie artefakt dopasowania czasu.
- R4′: przejęcie tracku w paśmie [5, 18] m geometrycznie niemożliwe
  z obwodu; koincydencja ≤ 5° na 18–45 m do 8.3% próbek ⇒ bramka
  pozycji przewidywanej warunkiem PRE każdej przyszłej kotwicy.
- ✗ kalibracyjne CC ×2 (rozmowa, nie prereg): szanse domknięcia piły
  dawane na 0.5–0.6 i 0.6 — wynik 0/27 i 0/576; za optymistycznie
  o geometrii spojrzenia, drugi raz w tej samej nodze.
- Wykonawca: obie sesje deskowe czyste (bramki, zakresy, prereg
  wykonany co do litery). Znalezisko CC bez wpływu na liczby: remis
  dominanty fazy w kotw2_obwod.py łamany porządkiem zbioru
  (zależnym od środowiska) — 96 etykiet, werdykt 576/576 niezmienny.
```

## §4. KIERUNKI (append-only przy commicie §CO)

```
## Dopisek stanu katalogu — 8.11.2026 (CO-KOTW-2, ANEKS_KOTW-2)
- **KOTW (kotwica wizyjna: lot bez limitu czasu po utracie GNSS) —
  CLOSED W CAŁOŚCI, 0 bootów.** Otwarta i zamknięta 8.11 dwoma
  reconami przy biurku: środek strefy przegrywa na czasie (przerwa
  37.1 s ⇒ 6.09 > 5.79 m przy idealnej poprawce), obwód na dokładności
  (przerwa 9.4 s, ale poprawka 2.5 m z 23–44 m przy budżecie 0.54 m);
  para kotwic 5/48. Zdanie graniczne: przy poziomej kamerze misji nie
  istnieje rozmieszczenie kotwic dające naraz krótką przerwę
  i bliski zasięg. Prereg ANEKS_KOTW-1 §2 wykonany: trzeciego
  podejścia nie ma. Dźwignie nazwane, NIEOTWARTE (wymagają zmiany
  misji/FROZEN, czyli nowej pozycji katalogu): kamera pochylona lub
  druga w dół, okresowe spojrzenie wstecz, kotwice obwodowe z lepszym
  źródłem kursu. Znaleziska przechodnie: bias yaw estymatora
  prawdziwy (δψ 5.8°), bramka pozycji przewidywanej warunkiem PRE
  każdej kotwicy w polu widzenia.
- Katalog: 2d zamknięta budżetem czasu (T* = 22 s), KOTW zamknięta
  granicą geometrii. Breach 0 / REFUSE(POS) fałszywych 0 programowo
  bez zmian (~190 bootów programu; noga KOTW 0).
```

## §CO

Bramka: origin/master == **fb7415c5**. Jeden commit: korzeń
`ANEKS_KOTW-2.md` verbatim (byte-check sha256 z wiadomości CC),
`results/KSIEGA_PREDYKCJI.md` += §3, `KIERUNKI_PO_PLANIE.md` += §4.
Raport płaski, STOP. Push = Olga; CC sprawdza byte-check i append-only,
potem aktualizuje raport programu (poza repo).
