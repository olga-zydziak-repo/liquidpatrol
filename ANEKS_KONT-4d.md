# ANEKS_KONT-4d — po STOP-KONT4-V2P: kanoniczne V2′ w kolejce i analizie, bramka tempa symulacji w settle przed uzbrojeniem, boot nieważny liczy się (zostaje 16/15)

CC · 8.11.2026 · łańcuch KONT, po STOP-KONT4-V2P (commit d6f3363f —
bramka tego aneksu wymaga go na origin). Kryteria i zamrożenia bez
zmian; to aneks narzędziowy. Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP i rozstrzygnięcia

1. **Poprawka kolejki i analizy na kanoniczne V2′: ZATWIERDZONA.**
   V2′ liczone dokładnie jak sędzia (rtf_stream, wall, D9), per epizod;
   kolejka po każdym boocie czyta werdykt ważności i planuje dolecenie
   nieważnych. Obie wady wykonawcy (brak kontroli V2′ w kolejce, inna
   metoda w analizie) do KSIĘGI przy zamknięciu nogi; wynik tego bootu
   nie został przez nie skażony, bo kierunek błędu był ten sam.
2. **nom_b1_r3 nieważny i liczy się do budżetu** (stos wstał, lot był).
   S4 4/20, noga 28/45; zostaje 16 bootów na 15 pozycji. Epizody tego
   bootu wchodzą do raportu wyłącznie opisowo (mitygacja: 1 restart,
   6.41°, bias 0.00013; nominal 4/4 bez fałszywych wejść i naruszeń,
   r_GT ≤ 23.44) — do ramienia (−) NIE liczą się, nominały lecą od
   nowa jako ważne.
3. **Bramka tempa symulacji przed uzbrojeniem: ZATWIERDZONA.**
   W settle pomiar Δsim/Δwall w oknie ≥ 30 s (z istniejącego próbnika
   dwuzegarowego); **próg ≥ 0.93** (margines do kryterium 0.90; zdrowe
   stanowisko chodzi 0.95–0.97, chory boot miał 0.861 w settle przy
   0.856–0.887 w locie — settle przewiduje lot). Poniżej progu ⇒ boot
   przerwany PRZED uzbrojeniem (liczy się do budżetu, kosztuje minuty
   zamiast nieważnego lotu), remedium operatora: `wsl --shutdown`
   i świeża sesja (akcja Olgi, nazwana). **2 kolejne przerwania bramką
   tempa ⇒ STOP-KONT4-STANOWISKO.** Wartość pomiaru w manifeście
   każdego bootu.
4. Nota opisowa przyjęta: model z przepływem obniża zapas RTF
   (S2 0.95–0.97 wobec kanonu ~1.0); przyczyna spowolnienia tego
   jednego bootu niezmierzona i nieścigana, bramka §1.3 zarządza
   ryzykiem zamiast go wyjaśniać.

## §CO

Bramka: origin/master == **d6f3363f**. Commit 1: korzeń
`ANEKS_KONT-4d.md` verbatim (byte-check sha256 z wiadomości CC) +
poprawki §1.1 i §1.3 (nowe kopie kolejki/analizy albo edycja plików
bez wyprodukowanych ważnych lotów — wybór wykonawcy, nazwany
w commicie). Potem booty: nom_b1_r4, nom_b2_r2, nom_b3, 12 cięć;
raport STOP-KONT4 jak w PROMPT_KONT_S4. Push = Olga. CC przy pushu
STOP-KONT4 weryfikuje też liczby V2P i D5-diag z ulogów.
