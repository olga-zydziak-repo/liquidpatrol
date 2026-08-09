# B1-bis instrument — ZNALEZISKO: definicja ε_pos + jakość kanału GT (przed siatką lotów)

Data: 2026-08-09. Instrument: `gt_judge.py` (unit-test R-2 **PASS**, `unit_test.log`).
Weryfikacja liczb ANEKS-2 (prompt: „1.49 weryfikujesz cytatami do artefaktów B1").

## 1. Reprodukcja ANEKS-2 (dokładna)

Instrument zwalidowany (unit-test PASS, oba układy osi) uruchomiony na `b1_flight1/2.jsonl`:

| lot | ABS \|e\| max (bez bazy) | REL \|e−e0\| max (baza odjęta) | healthy std (N,E) | e0 offset |
|---|---|---|---|---|
| 1 | **1.490** | 1.152 | (0.226, 0.021) | (−0.389, −0.071) |
| 2 | **0.855** (ANEKS-2: 0.91) | 0.540 | (0.192, 0.025) | (−0.313, −0.042) |

**ANEKS-2 `max_drift` = ABSOLUTNE `|pos_EKF − pos_GT|` (bez odjęcia bazy)** — reprodukuje 1.490 co do
cyfry (lot 1). Lot 2: 0.855 (ANEKS-2 podało 0.91 — drobna różnica z GT-matching/okna, nieistotna dla tezy).

## 2. Dwa problemy przyrządowe (R-2)

**(P-A) Offset ramki home↔gz-world (~0.39–0.49 m), NIE błąd EKF.** Przy zdrowym GPS EKF śledzi truth do
cm, więc stały składnik `e0` w oknie zdrowym to różnica origin (EKF-local=home vs gz-world), a nie błąd
estymatora. ABS `|e|` (1.49) **wlicza ten offset jako błąd** — nadmiarowo. Fizyczne ε_pos (błąd estymaty
w ramce home) = REL `|e−e0|` ≈ 1.15 (lot 1).

**(P-B) Szum GT skorelowany z ruchem (~0.2 m, oś Północ).** healthy std Północ ~0.22 m vs Wschód ~0.02 m.
Patrol porusza się w OSI PÓŁNOC (±1.5 m/s). Asymetria N≫E ⇒ artefakt **latencji stempla GT**: `gz model -p`
to subprocess ~2 Hz, `mono` stemplowany przy POWROCIE komendy (lag), nie w chwili próbki. Interpolacja
liniowa NIE usuwa (stempel sam jest spóźniony). Kontaminuje też bazę e0 (mierzona pod ruchem).

## 3. Skutek dla D10 (cap) i D13c (bramka)

- ε_cap = 1.5 × max(max_drift). Definicja max_drift zmienia liczbę:
  - ABS (styl ANEKS-2): 1.5×1.49 = 2.235 → **9/4 = 2.25** (wartość robocza z promptu).
  - REL (fizyczne ε_pos): 1.5×1.15 = 1.725 → **7/4 = 1.75**.
- Kanał GT (gz model -p) ma **podłogę szumu ~0.2 m pod ruchem** → pomiar dryfu w locie „prostym v_max"
  i „narożnik" zawyżony o szum. Loty **w ZAWISIE** (v≈0) nie mają tego szumu → czysta kotwica ε_pos.

## 4. Kierunki (rozstrzygnięcie potrzebne PRZED siatką 6+ lotów)

Definicja `ε_pos_rzecz` w §0/D13c brzmi literalnie `|pos_EKF − pos_GT|` (ABSOLUTNE) — ale to równa się
błędowi estymaty TYLKO gdy home ≈ gz-world (założenie autorów; TU obalone offsetem ~0.44 m).

- **(A) ε_pos = REL (baza odjęta) — fizycznie poprawne, cap z reguły D10:** poprawiony kanał GT
  (streaming pozy gz z sim-time) + kotwica ZAWIS na czysty pomiar; cap 1.5×max(REL). Ryzyko: zmienia
  ratyfikowaną liczbę roboczą (9/4→~7/4 z B1; B1-bis może podnieść).
- **(B) ε_pos = ABS (styl ANEKS-2) — konserwatywne, ciągłe z 1.49:** wlicza offset ramki (nadmiarowo,
  ale bezpiecznie: większy cap = mniejsza trasa = więcej marginesu). Samo-spójne char↔bramka.
- **(C) STOP jako SR-instrument:** re-pomiar/decyzja Olgi o kanale GT i definicji przed jakimkolwiek freeze.

**Rekomendacja:** (A) — fizycznie poprawne ε_pos, z poprawionym kanałem GT i kotwicą zawisu; offset ramki
to NIE błąd estymatora i nie powinien wchodzić do capa. Konserwatyzm zapewnia mnożnik 1.5 nad zmierzonym
(zaszumionym) maksimum, nie sztuczny offset geometryczny.

---

## 5. KOREKTA po ratyfikacji Olgi (T_home z okna ≥20 s) — „offset 0.44 m" był artefaktem skew

Po wdrożeniu zaostrzeń (T_home z ≥20 s zdrowego GPS, estymator skew, bramka p95) instrument uruchomiony
ponownie na starych lotach B1:

| lot | T_home (≥20 s) | healthy_p95 | healthy_valid (≤0.10) | skew_hat | resid@0 | max_drift |
|---|---|---|---|---|---|---|
| 1 | (−0.011, −0.045) ≈ **0** | 0.433 | **False** | **0.32 s** | 0.227 | 1.493 |
| 2 | (0.018, −0.032) ≈ **0** | 0.375 | **False** | **0.28 s** | 0.194 | 0.872 |

**Wnioski (poprawiają §2 P-A):**
1. **T_home ≈ 0** przez okno ≥20 s ⇒ **home ≈ gz-world-origin; NIE ma realnego offsetu ramki ~0.44 m.**
   Wcześniejsze „0.44 m" to był **artefakt skew na krótkim (3 s) oknie jednej nogi patrolu** — skew·v ma
   znak prędkości, więc na jednej nodze daje bias ~0.45 m, a po pełnych cyklach ±v uśrednia się do ~0.
   Zaostrzenie Olgi (T_home ≥20 s) DOKŁADNIE to naprawia. (P-A zdezaktualizowane; realny problem = skew.)
2. **Oba stare loty B1 NIEWAŻNE** wg bramki W5 (p95 0.43/0.37 ≫ 0.10) — kanał `gz model -p` odrzucony;
   skew 0.28–0.32 s wykryty automatycznie. **Nie wchodzą do `max` capa (D10).**
3. `max_drift=1.49` (lot 1) = **prawdziwy dryf + szum skew (~0.3–0.45 m)** — zawyżony. Czysty dryf
   wymaga kanału streaming (skew~0, p95<0.10) → siatka B1-bis. Ani 1.49 (ABS/stary) ani 1.15
   (REL/3 s-baseline) nie są czyste; obie skażone skewem starego kanału.

**Konsekwencja:** liczba capa czeka WYŁĄCZNIE na czyste loty B1-bis (streaming). Reguła D10/D11 stoi.
