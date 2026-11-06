# ANEKS_KONT-3 — S2 zamknięte werdyktem Y-a: mechanizm odjazdu = skok yaw akcji D5; zamrożenie T* = 22 s, Δ_D5 = 1.524 m, R_nom = 27.51 m, koszt bariery 0/48; noga idzie do S3

CC · 6.11.2026 · łańcuch KONT, po STOP-KONT2f (7744881d na origin).
Zamraża liczby charakteryzacji (PRE §3) i zamyka etap S2. Wklejany RAZEM
z PROMPT_KONT_S3. Sygnały bez numeru odrzucasz.

## §1. Weryfikacja CC z repo

- **Werdykt Y-a przyjęty.** Przeliczenie niezależne CC (własny kod,
  trace): skoki zejść Y 0.73 / 0.45 / 0.30 m przy kontrolach 1.47 /
  1.21 / 2.04 (wykonawca: 0.72/0.46/0.31 przy 1.54/1.20/2.20 — różnice
  metody, ten sam werdykt 3/3 poniżej kontroli). Headingi w chwili
  decyzji 76.6° / −29.1° / −101.3°, obrót w zejściu ≤ 0.2° — czynnik
  yaw był naprawdę testowany, na dużych kątach. Rozdział pełny: 5/5
  ponad kontrolą przy yaw = 0, 3/3 poniżej przy trzymaniu, zakresy
  prędkości stycznej się pokrywają.
- **`kont_s2_freeze_bf.py` uruchomiony u CC: wynik identyczny bajtowo**
  z `s2_freeze_bf.json` (sha256 ae19f66c…). Arytmetyka sprawdzona:
  Δ_D5 = 1.5 × 1.016 = 1.524; R_nom = 32 − 2.85 − 0.116 − 1.524 = 27.51;
  koszt 0/48 (r_max siatki 26.16 < 27.51); koszyk 21 = 5.262 ≤ 5.79 <
  koszyk 22 = 5.849.
- V2′ 0.95–0.96, zegar 0 skoków, breach 0, REFUSE 0, przeskoki
  w powietrzu 0/8, n ważnych = 8. Budżet S2′ 8/12, noga 24/45.
- Odstępstwa wykonawcy przyjęte: STOP-KONT2-WYJATEK po ostatnim locie
  (bug nakładki na błysku `cs_in_air`, stan poprawny 8/8, poprawka
  `kont_d4_y2.py`), freeze uruchomiony przed rozstrzygnięciem (bez
  wpływu), dwa pliki poza listą (`kont_s2y_boot.sh`, `kont_d4_y2.py`).

## §2. Zamrożenie (FROZEN; obowiązuje S3, S4 i cytowanie)

- **Krzywa ε_b:** obwiednia z `s2_freeze_bf.json` sha256
  **ae19f66c6807de6c…** (plik w repo jest nośnikiem; żadnych przeliczeń
  w S3/S4). ε_b(0⁺) = 0.116 m.
- **Δ_D5 = 1.524 m** (zejście = D5 z trzymaniem yaw; stara Δ profilu
  yaw = 0 wynosi 4.203 m i zostaje w raportach jako kontrast).
- **Semantyka T\* (doprecyzowanie brzegowe, żeby P9_kont nie miało
  dwuznaczności):** KONT trwa, dopóki t_KONT < T\*; REFUSE(POS) odpala
  w t_KONT = T\* albo wcześniej przy naruszeniu bariery. Gwarancja
  pokrywa koszyki 0…T\*−1: dla każdego k ≤ 21 zachodzi ε_b(k) + Δ_D5 ≤
  m_p50 = 5.79. **T\* = 22 s.**
- **Bariera w locie:** ALLOW w KONT ⇔ t_KONT < 22 ∧ r_est ≤ 32 − 2.85 −
  ε_b(⌊t_KONT⌋) − 1.524. **Bariera nominalna: r_est ≤ R_nom = 27.51 m**
  przez cały lot w reżimie KONT (koszt zmierzony: 0/48 scenariuszy
  siatki).
- **Akcja terminalna KONT = D5 + trzymanie yaw** (heading z chwili
  decyzji, trzymany do przyziemienia). Produkcyjne D5 poza reżimem KONT
  bez zmian (yaw = 0) — kanon K2/R0.3a nietknięty.
- **Założenie A-kont ([A4]):** ε(t) ≤ ε_b(t) w kontynuacji i Δ ≤ Δ_D5
  w zejściu, zmierzone na 8/3 lotach; w S4 walidowane w locie,
  przekroczenie = FAIL nogi, nie strojenie. Mechanizm odjazdu wewnątrz
  filtra: [MECHANIZM NIEZMIERZONY] — twierdzenie wiąże akcję, nie
  wyjaśnienie.

## §3. Mechanizm do kanonu (zdanie cytowalne S2)

„Pod przepływem optycznym o budżecie kontynuacji nie decydowała fuzja
w locie (orbita: ε ≤ 2.5 m przez 70 s w 7/8 lotów, najgorszy 4.0 m),
tylko nienazwana od R0.3a własność akcji zejścia: komenda D5 obraca
drona do yaw = 0, a obrót 51–134° przy 1.6–3.1 rad/s pod przepływem
kosztuje jednorazowo 1.3–3.7 m błędu pozycji (korelacja obrót–odjazd
0.84–0.91, prędkość–odjazd ~0). Trzymanie yaw usuwa odjazd w 3/3 zejść.
SITL, grunt z dekalem, bez wiatru; n = 8/5/3."

## §4. KSIĘGA (append-only przy CO-S2; P-KONT-5/6 rozliczy zamknięcie nogi)

```
## KONT S2 zamknięte Y-a (ANEKS_KONT-3, 6.11.2026): T* = 22 s, Δ_D5 =
1.524 m, R_nom = 27.51 m, koszt bariery 0/48; mechanizm = skok yaw D5
- P-KONT-3 (0.55, T* ≥ 30 s) — ✗ (22 s). P-KONT-4 (0.45, koszt 0) — ✓
  (0/48 przy R_nom 27.51).
- ✗ kalibracyjne CC (seria S2): R-3 „skala przepływu" (obalona S2.0);
  „samozatrucie BSON" (obalone S2b); „sygnatura resetu pozycji"
  (liczniki 0); hipoteza timestamp_sample 0 (obalona D4a); §3B 2B
  „równoczesność jedynym wspólnym czynnikiem" (fałsz — skok yaw);
  rachunkowe: kolejka 1c §4 7≠8 lotów, zdanie Z „≤2.4 m" zamiast
  „≤2.5 m". Diagnoza właściwego czynnika: wykonawca (NOTA-2B), nie CC.
- Wady wykonawcy nazwane: d4c bez rozkładu osi rate (S2e wskazał
  hamowanie); dry-run launchera ręczny zamiast skryptem (8 min);
  klucz verdict/werdykt; nakładka d4_y na błysku cs_in_air (po lotach,
  stan skorygowany); freeze przed rozstrzygnięciem reguły.
- Infrastruktura do S4: launcher s2y obowiązkowy (gz przed PX4);
  bias na limicie 0.15 w 3/6 bootów s2d i restart watchdoga na ziemi
  2/6 — mechanizm niezmierzony, bias przy odcięciu w normie 8/8;
  próbnik zegara + timesyncd stop bez zmian.
- Lekcja: akcja bezpieczna ma więcej stopni swobody niż jej opis —
  yaw = 0 siedział w D5 od R0.3a i był łagodny pod GNSS i zliczeniem;
  nowy estymator zmienia koszt starych akcji. Przy każdej zmianie
  źródła pozycji audytować WSZYSTKIE składowe komend akcji osłony,
  nie tylko tę mierzoną.
```

## §5. CO-S2 (razem z bramką S3; jeden commit dokumentowy)

Bramka: origin/master == **7744881d**. Pliki: korzeń `ANEKS_KONT-3.md`
(verbatim, byte-check sha256 z wiadomości CC); `results/KSIEGA_PREDYKCJI.md`
append-only §4. Commit: `KONT [CO-S2]: zamrożenie Y-a (ANEKS_KONT-3),
KSIĘGA`. Potem sesja S3 według PROMPT_KONT_S3 (ten sam wieczór albo
osobny — bez znaczenia, 0 bootów). Push = Olga.
