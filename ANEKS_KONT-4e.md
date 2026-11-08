# ANEKS_KONT-4e — po STOP-KONT4-TEMPO: wcześniejsze zatrzymanie przyjęte, licznik bramki tempa zeruje się po remedium operatora, wolny boot tuż po restarcie = STOP od razu; opcjonalny 1 boot luzu do ratyfikacji

CC · 8.11.2026 · łańcuch KONT, po STOP-KONT4-TEMPO (commity 5e34049c,
997782fc — bramka wymaga ich na origin). Sygnały bez numeru odrzucasz.

## §1. Rozstrzygnięcia

1. **Zatrzymanie kolejki przed drugim przerwaniem: przyjęte jako
   nazwane, słuszne odstępstwo.** Cel reguły 4d §1.3 (nie palić budżetu
   w pętli na niezmienionym stanowisku) został spełniony lepiej niż jej
   litera.
2. **Licznik przerwań bramką tempa zeruje się po remedium operatora**
   (`wsl --shutdown` + świeża sesja). Uzasadnienie: restart zmienia
   stan, którego dotyczy licznik. **Ale wolny boot bezpośrednio po
   restarcie ⇒ STOP-KONT4-STANOWISKO natychmiast** — remedium
   nieskuteczne to inny sygnał niż stanowisko zmęczone sesją i nie
   wymaga drugiego potwierdzenia za cenę boota.
3. Zapis stanu: bramka tempa zadziałała zgodnie z projektem (0.876
   przy progu 0.93; wcześniejsze booty sesji 0.957–0.972). Przyczyna
   spowolnienia pozostaje niezmierzona i nieścigana (4d §1.4).
4. **Budżet — opcja na jedno słowo Olgi:** zostało 15 bootów na 15
   pozycji, zero luzu. **„ratyfikuję 4e"** ⇒ S4 ≤ 21, w ramach
   nietkniętego limitu nogi PRE ≤ 45 (noga maks. 29 + 16 = 45);
   bez ratyfikacji S4 zostaje ≤ 20 i pierwsze dolecenie oznacza STOP
   budżetu. Rekomendacja CC: ratyfikować — to ostatni luz, o jaki
   można prosić bez ruszania limitu nogi, i lepiej mieć go przed serią
   niż wracać do tej decyzji w jej środku.

## §CO

Bramka: origin/master == **997782fc**. Sekwencja: (1) Olga:
`wsl --shutdown`, świeża sesja; (2) commit 1: korzeń `ANEKS_KONT-4e.md`
verbatim (byte-check sha256 z wiadomości CC) + budżet kolejki według
ratyfikacji; (3) kolejka od nom_b2_r2 (nom_b1_r4 przerwany liczy się,
5/20): nominały, 12 cięć, raport STOP-KONT4 jak w PROMPT_KONT_S4.
Push = Olga.
