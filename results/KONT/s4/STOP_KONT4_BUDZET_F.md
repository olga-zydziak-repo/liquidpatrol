# STOP-KONT4-BUDZET (kolejka f) — budżet S4 21/21 i noga 45/45 wyczerpane; 12/12 cięć ważnych, nominały 2/3: brak nom_b2 (wada wykonawcy)

8.11.2026 · kolejka `kont_s4_campaign_f.py` (`7967ac63`), start Olgi po STOP-KONT4-STANOWISKO i zmianie trybu zasilania
(cichy → wydajny; goły gz 0.9945, 0 zacięć) · 12:17–15:08 · kolejka zakończona `stop=None, pozostało=[]`, ale siatka
S4 NIEKOMPLETNA.

## Wada wykonawcy (główna)

Kolejkę f zbudowałam z `pozostało` kolejki e (`kampania_s4e2.json`). STOP-KONT4-STANOWISKO przerwał e po boocie
nom_b2_r3 PRZED dopisaniem dolecenia, więc `pozostało` nie zawierało nom_b2. Skutek: f miała 14 pozycji zamiast 15,
raportowałam „1 rezerwę” zamiast 0, a rezerwa poszła na dolecenie nom_b3. **nom_b2 (epizody 4–7) nie ma ani jednego
ważnego bootu** (nom_b2: asercja yaw; nom_b2_r3: bramka tempa). Lekcja: listę pozostałych pozycji liczyć z siatki minus
ważne booty, nigdy z `pozostało` przerwanej kolejki.

## Przebieg (21 bootów S4 łącznie; f: booty 7–21)

- Tempo: nom_b3 0.936 przed uzbrojeniem, potem 0.972–0.981 we wszystkich bootach; zegar 0 skoków przed każdym bootem.
- Mitygacja EKF 4c: 1 reinit w każdym boocie, yaw po reinicie 6.16–6.45° (przed: −5.4…17.27°), bias ≤ 0.00017.
- **nom_b3 nieważny** (V2′ epizodów 8/11: 0.878/0.890 < 0.90; bezpieczeństwo czyste) ⇒ dolecenie nom_b3_r2 (boot 21) ważny.
- Breach 0, REFUSE(POS) nominalny 0, R-G 0, R-G-NOM 0 w całej kolejce.

## Cięcia 12/12 ważne (V2′ 0.953–0.979)

| boot | t_entry | kontynuacja s | koniec | r_GT max | ε max | ε/ε_b | naruszeń ε | δ zejścia | (a–f) |
|---|---|---|---|---|---|---|---|---|---|
| c08_s01_r2 | 2.49 | 21.896 | R-KONT(T*) | 23.862 | 3.473 | 0.999 | 0 | 0.221 | ✓ |
| c08_s02 | 2.62 | 21.968 | R-KONT(T*) | 22.481 | 3.172 | 0.912 | 0 | 0.048 | ✓ |
| **c11_s01** | 6.81 | 21.972 | R-KONT(T*) | 23.082 | **3.872** | **1.113** | **548** | 0.069 | **b ✗** |
| c11_s02 | 6.75 | 21.972 | R-KONT(T*) | 19.780 | 2.566 | 0.852 | 0 | 0.437 | ✓ |
| c10_s01 | 4.48 | 21.988 | R-KONT(T*) | 15.858 | 2.924 | 0.876 | 0 | 0.056 | ✓ |
| c10_s02 | 4.37 | 21.972 | R-KONT(T*) | 22.053 | 3.370 | 0.969 | 0 | 0.929 | ✓ |
| c05_s01 | 2.47 | 21.988 | R-KONT(T*) | 20.434 | 2.813 | 0.806 | 0 | 0.030 | ✓ |
| c05_s02 | 2.38 | 21.956 | R-KONT(T*) | 15.184 | 3.003 | 0.863 | 0 | 0.734 | ✓ |
| c01_s01 | 2.80 | 21.984 | R-KONT(T*) | 23.195 | 2.443 | 0.745 | 0 | 0.019 | ✓ |
| c01_s02 | 2.84 | 21.980 | R-KONT(T*) | 23.220 | 2.684 | 0.772 | 0 | 0.193 | ✓ |
| c02_s01 | 8.86 | 21.968 | R-KONT(T*) | 23.321 | 3.121 | 0.897 | 0 | 0.114 | ✓ |
| c02_s02 | 6.95 | 21.968 | R-KONT(T*) | 23.337 | 3.275 | 0.942 | 0 | 0.062 | ✓ |

Wszystkie 12 kontynuacji zakończone R-KONT z przyczyną T* (21.90–21.99 s), dr_max 0.
**c11_s01: kryterium (b) FAIL** — ε przekracza obwiednię ε_b w 548 z 1411 ticków kontynuacji (pierwsze przekroczenie
przy t ≈ 14.9 s od flagi, max ε/ε_b 1.113); pozostałe kryteria ✓, ε przy REFUSE 3.247. Werdykt cięcia i nogi wg
PROMPT_KONT_S4 — do CC; nie orzekam.

## Nominały 2/3 ważne

| boot | epizody | REFUSE(POS) | ticki KONT | R-G-NOM | R-G | r_GT max | V2′ |
|---|---|---|---|---|---|---|---|
| nom_b1_r5 | 0–3 | 0 | 0 | 0 | 0 | 23.26–23.40 | 0.965–0.977 |
| nom_b3_r2 | 8–11 | 0 | 0 | 0 | 0 | 20.86–25.85 | 0.975–0.980 |
| nom_b2 | 4–7 | — brak ważnego bootu — | | | | | |

## Do decyzji CC

1. nom_b2: budżet S4 (21) i limit nogi (45) wyczerpane — dolecenie wymaga nowego budżetu albo orzeczenia S4 na 2/3 nominałów.
2. c11_s01 (b) FAIL: interpretacja wg PROMPT_KONT_S4.
