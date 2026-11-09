# ANEKS_NADIR-2 — S2 czyste (0 przekroczeń ε_b w 440 oknach bez GNSS, sieć na p_corr 4/4); FREEZE obwiedni poprawki per koszyk + litera przyjęcia r_h < 8 m; rozstrzygnięcia trzech punktów; S4 dostaje kryterium (g)

CC · 9.11.2026 · łańcuch NADIR, po STOP-NADIR2 (7b2eb6b9 na origin).
Sygnały bez numeru odrzucasz.

## §1. Weryfikacja CC z repo

- Okna R1 przeliczone niezależnie z `rama.jsonl` (podział po zdarzeniu
  `denial` z trace): G 724 / N 440 wobec 723/439 (±1 okno graniczne
  przy denial) — **0 przekroczeń ε_b w oknach bez GNSS w 4/4 cięciach**
  potwierdzone. Konwencja nazwana: CC liczył przyrost w 2D (max 0.84),
  wykonawca w 3D z wkładem wysokości (max 0.94) — miara wykonawcy
  konserwatywniejsza, werdykt wspólny. Do dalszych etapów obowiązuje
  miara wykonawcy (3D).
- Poprawki misji przeliczone z GT interpolowanym w t_fix: max per boot
  0.381 / 0.234 / 0.205 / 0.165, p95 0.095–0.135 — zgodne z koszykami
  raportu (globalny max 0.388 = ta sama obserwacja c08, Δ 7 mm
  z interpolacji). Walidacja sucha i identyczność świata v2 odczytane
  (passthrough 21 604 wiersze / 0 różnic).
- Werdykt S2 stoi: **żadna śmierć S2 nie zachodzi.** P-NADIR-2 (0.75,
  warunek ważności B przechodzi) — ✓.

## §2. FREEZE obwiedni poprawki (reguła PRE §3: 1.5 × max użytej
poprawki, oba reżimy, żywy tor detekcji; FROZEN od tego aneksu)

| koszyk r_h [m] | max zmierzony | **ε_fix_freeze** |
|---|---|---|
| 0–2 | 0.203 | **0.305** |
| 2–4 | 0.195 | **0.293** |
| 4–6 | 0.151 | **0.227** |
| 6–8 | 0.388 | **0.582** |

**Litera przyjęcia obserwacji — rozszerzenie (zmiana PRE §2.3 tym
aneksem):** obserwacja przyjęta dodatkowo wymaga **r_h < 8 m**.
Mechanizm: koszyki 8–10 (0 danych) i 10+ (n = 1) nie mają zmierzonej
obwiedni; dalsza obserwacja jest odrzucana, rama trzyma poprzednią
poprawkę przy rosnącym τ — co bariera konsumuje uczciwie przez
ε_b(⌊τ⌋). Rachunek nie pustoszeje: najwęższa komórka (c08_s02,
m = 2.99): 0.582 + ε_b(0) 0.323 + Δ_D5 1.524 = **2.43 ≤ 2.99**
(zapas 0.56); przy τ w koszyku 1: 2.57 ≤ 2.99. Zmierzone w S2
u_max 2.02–2.24 — spójne.

## §3. Rozstrzygnięcia trzech punktów z STOP-NADIR2

1. **Opóźnienie ENTRY przy tracku zastanym (c08, +5.9 s): przyjęte,
   nazwane.** Bramka odrzuca odświeżenie-teleport na pozie startowej —
   dokładnie klasę przejęcia, przed którą stoi; ENTRY przychodzi po
   wygaśnięciu starego tracku. Artefakt startu epizodu SITL (teleport
   intruza), nie wada bramki; przy epizodach 110 s koszt pomijalny.
   S4 raportuje czas ENTRY per epizod (obserwowalna, bez progu).
2. **c11: litera KONT (b) 1.06 na krzywej 2d — poza literą NADIR,
   wpis do KSIĘGI.** Druga instancja (po c11_s01 w KONT) obwiedni
   nauczyciela za ciasnej długohoryzontowo w rodzinie c11, ten sam
   EKF, bez wpływu nakładki. NADIR konsumuje ε_b wyłącznie w prefiksie
   okien τ (zmierzony margines: max 0.94 przy 440 oknach) — właśnie
   dlatego długohoryzontowa ciasnota 2d nie dotyka tej nogi. Założenie
   to wchodzi do P9_nadir jako A-nadir i do litery S4 jako (g).
3. **c11: V2′ = 0.923: cięcie ważne dla miar geometrycznych (R1, R2,
   R4 — per tick, niewrażliwe na RTF w locksteppie), nazwane przy
   miarach czasowych (R3; czasy ENTRY c11 6.74 vs 6.75 — bez
   odchylenia).** Dane c11 wchodzą do FREEZE (konserwatywnie — więcej
   danych). Powtórki nie ma — budżet S2 wykorzystany 6/6.

**Litera S4 — dodatek (zmiana PRE §3 tym aneksem, wzmocnienie):**
kryterium **(g): zero przekroczeń ε_b(⌊τ⌋) w oknach między
poprawkami** (miara 3D wykonawcy, fazy misji) — warunek ważności B
mierzony dalej tam, gdzie sądzi się dowód.

## §4. KSIĘGA (append-only przy commicie §CO)

```
## NADIR S2 — charakteryzacja piły (ANEKS_NADIR-2, 9.11.2026)
- 4 cięcia GNSS pod osłoną 2d: 0 przekroczeń ε_b w 440 oknach bez
  GNSS (max 0.94 miarą 3D; CC niezależnie 0.84 w 2D); sieć na p_corr:
  ENTRY i orbita do REFUSE(T*) 4/4, kontynuacja 21.96–21.97 s; skoki
  p_corr ~5× szum GNSS i sieć je znosi; u_max 2.02–2.24 przy
  m 2.99–10.33. P-NADIR-2 (0.75) ✓.
- FREEZE: ε_fix_freeze per koszyk 0.305/0.293/0.227/0.582 m
  (1.5 × max użytej poprawki, oba reżimy); litera przyjęcia + r_h<8 m.
- Bias kursu estymatora stały w epizodzie, różny między bootami
  (−1.5…−4.6°), nie dryfuje po cięciu (trend ≤0.27°/s); para znaczników
  (87% poprawek) zdejmuje go z namiaru — potwierdzenie mechanizmu
  z reconu KOTW R2 na żywym torze.
- Trzecia instancja „zadany ≠ faktyczny" w rodzinie c11: obwiednia
  nauczyciela 2d przekroczona o 6% długohoryzontowo (ten sam EKF, bez
  nakładki); NADIR nieczuły — konsumuje ε_b tylko w prefiksie okien.
- ✗ projektowe CC: PROMPT_NADIR_S2 §R żądał „2 cięcia na boot" wbrew
  literze drivera KONT (cięcie kończy boot zejściem) — wychwycone
  przez wykonawcę przed spaleniem boota; decyzja: 1 cięcie/boot.
  ✗ metodyczne CC (weryfikacja S1F): miara odległości tracku od
  znacznika liczona poziomo zamiast 3D — 2 fałszywe trafienia,
  skorygowane w tej samej turze, litera wykonawcy słuszna.
- Wykonawca: przyczyną braku summary rejestratora była własna
  procedura sprzątania launchera z S1 (znaleziona i naprawiona,
  a91bb94e); jedno kryterium walidacji suchej postawione źle
  i poprawione przed lotami (nazwane w raporcie); strażnik kolizji
  zablokował start od słowa w linii poleceń (0 bootów). Dwa booty
  przerwane bramką tempa przed uzbrojeniem (0.910/0.925) — remedium
  operatora (restart WSL) skuteczne, wzór 4e.
```

## §CO

Bramka: origin/master == **7b2eb6b9**. Commit 1: korzeń
`ANEKS_NADIR-2.md` verbatim (byte-check sha256 z wiadomości CC) +
KSIĘGA §4 append-only. Potem PROMPT_NADIR_S3 (wklejany razem — jego
§0 wymaga tego commitu). Push = Olga.
