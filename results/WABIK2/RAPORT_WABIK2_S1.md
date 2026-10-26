# RAPORT_WABIK2_S1 — selekcja reguły czasowej OFFLINE — ŚMIERĆ S1 (STOP-WABIK2-1)

CC-wykonawca · 27.10.2026 · wykonanie PROMPT_WABIK2_S1 (PRE_WABIK2 ratyfikowany,
byte-check PASS `2a1bd2a8…ee7a`, commit 1 = `580eeb8e`). **Sesja w całości
deskowa: 0 bootów, 0 SITL, zero edycji istniejących plików.**

**WERDYKT — ŚMIERĆ S1 verbatim PRE §2.4 ZACHODZI:** żaden z 26 wariantów
zamkniętej przestrzeni A/B/C nie spełnia pełnego kryterium selekcji §2.2 ⇒
**„reguła czasowa nieosiągalna przy tym szumie toru bez zmiany cech"** —
zero lotów wydanych, pozycja wraca do katalogu z tabelą jako aktywem.
FREEZE_WABIK2 i manifest świeżych wariantów NIE powstają (nie ma czego mrozić
ani po co latać). Progi klatkowe FREEZE_WABIK i wabik_sig v1 — nietknięte.

**Struktura wyniku (trade-off zmierzony, nie brak danych):**

1. **Warianty ratujące TP płacą na populacji normalnej.** Najlepsze
   (B(θ=0.80,T=8 s)×C i B(θ=0.85,T=8 s)×C): TP **5/6 ≤15 s** (flagi w 8.38 s —
   wręcz szybkie; pada tylko w02b ZBLIŻ-8.5 m: 30.7 s), FP 0/3 ✓, ORB 2/2 ✓,
   ale **NULL-final 15/115 > próg ≤13/115**. Doszły dokładnie 2 epizody —
   `c07_s01` i `c05_s04`, obie klasa wędrowców v=0.5: próg FRAKCJI (0.8 w 8 s)
   jest dla wędrowca łatwiejszy niż próg CIĄGŁOŚCI 12 s, który ich część
   odsiewał pikami tak samo jak wabiki.
2. **Jedyny wariant poprawiający NULL nie ratuje TP.** C solo (zegar+reset od
   ciągłego segmentu): NULL-final **11/115** (lepiej niż baza 13), FP 0/3,
   ORB 2/2 — ale TP 1/6 (tylko w01b 12.54 s; reszta 15.5–21.0 s — piki v_rad
   nadal rwą ciągłość).
3. **Tolerancja przerw (A) prawie nic nie kupuje:** K=2/3/5 → TP 1–2/6
   (piki bywają dłuższe niż K klatek albo częstsze niż jeden na 12 s),
   a NULL-final rośnie do 15.
4. **Pareto:** w całej przestrzeni PRE zachodzi TP≥5/6 ⟺ NULL-final=15;
   NULL-final≤13 ⟺ TP≤4/6. Kryterium §2.2 wymaga obu naraz — zbiór pusty.

## §1. Bramki — PASS

Byte-check PRE `2a1bd2a8…` ✓ (commit 1 `580eeb8e`, osobny). origin=cd8f93bf ✓,
gate pusty ✓, porcelain czysty (poza nazwanymi ??) ✓; FROZEN komplet;
FREEZE_WABIK wykonaniem (wabik_sig v1 **475c972e** nietykalny — progi
klatkowe cytowane w nagłówku wabik_sig2).

## §2. Kotwica implementacyjna — PASS 11/11 co do liczb

Wariant bazowy wabik_sig2 odtworzył na feedach S2 nogi (i) wyniki wabik_sig v1
**identycznie co do etykiet (ever i końcowa) i czasów-do-flagi** we wszystkich
11 epizodach (w tym w00a 17.62 · w00b 20.99 · w01a 15.51 · w01b 24.88 ·
ORB 21.78/17.56 z odwołaniami) — narzędzie liczy tę samą literę.

## §3. Tabela selekcji (pełna, z odrzuconymi: `s1_tabela.json`)

| wariant | mech | TP≤15 /6 | ZBLIŻ /2 | FP /3 | ORB ok /2 | NULL ever/final | dopuszczony |
|---|---|---|---|---|---|---|---|
| baza (i) | 0 | 0 | 0 | 0 | 2 | 23/13 | – |
| A(K=2) · A(K=3) · A(K=5) | 1 | 1 · 1 · 2 | 0 | 0 | 2 | 30/15 | – |
| B(0.80, 8 s) | 1 | 4 | 1 | 0 | 2 | 34/15 | – |
| B(0.80, 10/12 s) | 1 | 3 · 3 | 0 | 0 | 2 | 33/15 | – |
| B(0.85, 8/10/12 s) | 1 | 4 · 3 · 3 | 1/0/0 | 0 | 2 | 33/15 · 33/15 · 32/15 | – |
| B(0.90, 8/10/12 s) | 1 | 3 · 3 · 3 | 0 | 0 | 2 | 33/15 · 32/15 · 31/15 | – |
| **C** | 1 | 1 | 0 | 0 | 2 | **21/11** | – (TP) |
| A(K)×C | 2 | 2 · 2 · 3 | 0 | 0 | 2 | 29/14 · 30/15 · 30/15 | – |
| **B(0.80, 8 s)×C** | 2 | **5** | 1 | 0 | 2 | 34/**15** | – (NULL) |
| B(0.80, 10/12 s)×C | 2 | 4 · 4 | 0 | 0 | 2 | 33/15 | – |
| **B(0.85, 8 s)×C** | 2 | **5** | 1 | 0 | 2 | 33/**15** | – (NULL) |
| B(0.85, 10/12 s)×C | 2 | 4 · 4 | 0 | 0 | 2 | 33/15 · 32/15 | – |
| B(0.90, 8/10/12 s)×C | 2 | 4 · 4 · 4 | 0 | 0 | 2 | 33/15 · 32/15 · 31/15 | – |

Zegar kryterium: segmentowy dla ×C, od pierwszej klatki dla pozostałych;
podwójny zegar w JSON wszędzie (uzgodnione doprecyzowanie). FP = 0/3
i ORB = 2/2 **we wszystkich 26 wariantach** (podłoga klatkowa robi swoje);
decyzja ZBLIŻ bezprzedmiotowa (nie ma zwycięzcy).

## §4. Odczyt mechanizmowy (aktyw dla katalogu)

Kryterium było dobrze postawione i rozstrzygnęło jednoznacznie: **naprawa
agregacji czasowej NIE wystarcza — wąskim gardłem jest JAKOŚĆ predykatu
klatkowego** (piki v_rad estymaty toru), czyli warstwa CECH, której ta noga
świadomie nie tykała (PRE §1: „bez zmiany cech" = granica nogi). Kierunki
poza tą nogą (katalog, do decyzji CC): wygładzenie v_rad dłuższym oknem /
medianą PRZED predykatem (zmiana cech = inna noga litery PRE §5), albo
poprawa samego estymatora toru (łączy się z pozycją MULTI-TARGET/TOŻSAMOŚĆ
TRACKA). Wartość dodana: pełna mapa Pareto 26 wariantów na 126 epizodach
(11 S2 + 115 NULL) w repo — przyszła noga cech startuje z gotowym benchem
selekcji.

## §5. Artefakty

`results/WABIK2/`: **RAPORT_WABIK2_S1.md** (ten plik) · `s1_tabela.json`
(pełna tabela: 26 wariantów × 11 epizodów S2 + NULL ever/final, podwójne
zegary) · `tools/wabik_sig2.py`. Zero bootów; budżet nogi 0/≤4 wydane.
**Push = Olga („wypchnięte" — CC weryfikuje kotwicę, tabelę przeliczeniem
wyrywkowym i literę selekcji).** Po weryfikacji CC: **ANEKS zamykający**
(ścieżka śmierci S1 — werdykt, KSIĘGA P-W2-1 na NIE, powrót pozycji do
katalogu z tabelą jako aktywem). **STOP-WABIK2-1.**
