# ANEKS_NADIR-1 — po STOP-NADIR1-TEMPO: śmierć S1 po literze zapisana, przyczyna zmierzona (drugi render); naprawa: kadencja z pomiaru A/B {5, 3, 2} Hz, montaż pod płozy, manifest v2 dla 7 węzłów; potem b2′/b3′

CC · 9.11.2026 · łańcuch NADIR, po STOP-NADIR1-TEMPO + A/B (4603ee90
na origin). Sygnały bez numeru odrzucasz.

## §1. Weryfikacja CC z repo

- **PRE byte-check: PASS** — `PRE_NADIR.md` na origin ma sha256
  7cf25ca4…b00aea, identyczny z plikiem CC („sha ok"; flaga
  z commita 320467ef zamknięta). KSIĘGA §4 verbatim, append-only.
- A/B przeliczone u CC z surowych próbek rtf: mediany per przebieg
  0.598 / 0.687 / 0.588 / 0.682 ⇒ koszt renderu+detekcji **11–13%
  przy ~9.6 Hz** (okna wykonawcy: 0.617/0.695, 11%). Przeniesienie na
  bazę 0.97 daje 0.84–0.86 — zgodne z b2 (0.8536). Werdykt A/B stoi:
  **przyczyna = drugi render, nie stanowisko.**
- R1 PASS odczytany (0 px poza maską 10/10; model-wariant bitowo jak
  oryginał; przepływ nie widzi znaczników 10/10). Manifest: 37 węzłów,
  7 kolizji z bryłami. R3 statycznie 0.02–0.37 m przy 27 detekcjach —
  w modelu; pełna weryfikacja R3 u CC po lotach.
- Wady wykonawcy z raportu (runner stdout, pierwsza maska kadłuba,
  errata „nie ma OpenCV") — nazwane, zero bootów, zero skażeń.

## §2. Rozstrzygnięcia

1. **Werdykt:** śmierć S1 po literze tempa — zapisana. Sonda zadziałała
   zgodnie z rolą: koszt renderu wyszedł przed jakimkolwiek lotem,
   bramka przerwała boot przed uzbrojeniem. Naprawa aneksem, litera
   śmierci S1 bez zmian (tempo sądzone po nowej kadencji).
2. **Kadencja nadir — z pomiaru, nie z deklaracji.** Rachunek CC:
   koszt ~1.1–1.3%/Hz przy 9.6 Hz ⇒ liniowo 5 Hz ≈ 6% ≈ tempo 0.91 —
   rekomendacja 5–7.5 Hz prawdopodobnie pada; składnik stały kosztu
   może to zmienić, więc mierzymy. **Procedura (0 bootów lotnych,
   wzór B0):** A/B naprzemienny jak dotąd dla kadencji **{5, 3, 2} Hz**
   (2 przebiegi × 120 s na wariant; detekcja włączona jak w locie).
   Wybór: najwyższa kadencja z przeniesionym tempem ≥ **0.94**
   (baza = mediana tempa bootów trybu wydajnego, 0.97; zapas 0.01 na
   wariancję sesji). Żadna ≥ 0.93 ⇒ STOP — kandydat na śmierć nogi
   na koszcie renderu, nazwany wprost. Poniżej 2 Hz nie schodzimy:
   ziarno τ 0.5 s podnosi τ_max misji do ~1.5 s przy kryterium
   S4(e) ≤ 2 s — rezerwa się kończy. Wybrana kadencja → `pin_nadir`
   v2, FROZEN.
3. **Montaż kamery: pod płozy** (zmiana litery PRE §2.2 tym aneksem).
   16.9% martwego stożka w origin base_link to znana przed lotami
   strata pokrycia — usuwamy ją, nie mierzymy jej skutków. Offset
   montażu do `pin_nadir` v2; maska kadłuba zmierzona ponownie
   w sesji gołego gz przy A/B (ta sama metoda dwóch póz). Wymóg:
   maska w stożku centralnym ≤ 2%.
4. **Manifest v2 — 7 węzłów pod bryłami** (zmiana litery PRE §2.1 tym
   aneksem): węzły id 1, 4, 7, 14, 24, 27, 31 przesunięte minimalnie
   do wolnego miejsca (≤ s/2 od węzła idealnego, geometrycznie wolne
   od brył świata — asercja vs SDF). Pozycje rzeczywiste w manifeście
   są prawdą poprawki (znacznik ma znaną pozycję; idealna siatka była
   narzędziem reconu, nie wymogiem matematyki). Manifest v2 FROZEN po
   tym etapie.
5. **Desk-bramka przed bootami (0 bootów):** pokrycie przeliczone
   narzędziem reconu na manifeście v2 + masce montażu v2 (znacznik
   w masce = niewidoczny, konserwatywnie): wymóg **≥ 1 znacznik
   w ≥ 99.9% próbek misji ∧ τ_max ≤ 2 s** (s10, fazy misji, pełna
   postawa). FAIL ⇒ STOP przed lotami.
6. **visibility_flags przepływu: przyjęte** (decyzja wykonawcy z S1 —
   dobra). Litera PRE §2.4 „ε_b bez zmian" wymaga, by kamera przepływu
   widziała świat dokładnie jak w 2d; w systemie rzeczywistym znaczniki
   w polu przepływu raczej poprawiają teksturę (kierunek
   konserwatywny). Dopisek do granicy ambicji nogi: „przepływ nie
   widzi znaczników — wybór SITL zachowujący zamrożoną krzywę dryfu".
7. **OpenCV: pin 4.6.0 systemowe** (rejestrator bez `.b0deps`).
   Errata wykonawcy do RECON_NADIR §R4(ii) przyjęta — w przód.
8. **Budżet:** S1 2/4; zostają b2′ (epizod c08) i b3′ (epizod z innej
   komórki) — 4/4, zero rezerwy S1. **Opcja na jedno słowo:
   „ratyfikuję N1"** ⇒ S1 ≤ 5 (1 boot z luzu nogi; limit nogi ≤ 30
   bez zmian). Rekomendacja CC: ratyfikować — luz przed serią, nie
   w jej środku (lekcja 4e).

## §3. KSIĘGA (append-only przy commicie §CO)

```
## NADIR S1 — STOP tempa i naprawa (ANEKS_NADIR-1, 9.11.2026)
- Bramka tempa przerwała pierwszy boot epizodowy przed uzbrojeniem
  (0.854 < 0.93); A/B gołego gz rozdzielił hipotezy: drugi render +
  detekcja kosztują 11–13% przy ~9.6 Hz (CC przeliczył z surowych
  próbek). Zero lotów spalonych; sonda wykryła koszt przed serią.
- ✗ projektowe CC ×2: (i) prompty reconu i S1 nie kazały sprawdzić
  kolizji węzłów siatki z bryłami świata — 7/37 pod skrzynkami
  i budynkiem wyszło dopiero w sondzie; (ii) montaż kamery w origin
  base_link przypięty w PRE bez rachunku zasłony kadłuba — 16.9%
  stożka wyszło w b1. Obie naprawy aneksem przed lotami.
- Wykonawca: R1 identyczność 10/10 domknięta porządnie; decyzja
  visibility_flags (przepływ nie widzi znaczników — litera ε_b)
  przyjęta jako dobra; wady drobne nazwane (runner stdout, pierwsza
  maska, errata OpenCV) — żadna nie zużyła bootu ani nie skaziła
  liczb.
```

## §CO

Bramka: origin/master == **4603ee90**. Commit 1: korzeń
`ANEKS_NADIR-1.md` verbatim (byte-check sha256 z wiadomości CC) +
KSIĘGA §3 append-only. Potem w tej samej sesji, w kolejności:
(1) A/B kadencji {5, 3, 2} Hz + wybór wg §2.2; (2) montaż v2 + maska;
(3) manifest v2 + asercja; (4) desk-bramka pokrycia §2.5 — wszystko
0 bootów; raport cząstkowy w `results/NADIR/s1/NAPRAWA_N1.md`.
Bramki przechodzą ⇒ **b2′ i b3′ wg PROMPT_NADIR_S1 §R** (litera
pomiarów i śmierci bez zmian) i raport STOP-NADIR1F. Dowolna bramka
FAIL ⇒ STOP bez lotów. Push = Olga.
