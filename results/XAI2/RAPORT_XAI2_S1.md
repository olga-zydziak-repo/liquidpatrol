# RAPORT_XAI2_S1 — noga XAI-II, sesja S1 (0 bootów)

CC · 28.10.2026 · PROMPT_XAI2_S1 + PRE_XAI2 (0649deea).

## §0. Bramka

- PRE_XAI2 byte-check sha256 0649deea…0acb PASS, commit 1 nogi e8868fa2.
- democ_overlay_v4.py: drzewo czyste, plik zgodny z HEAD (porządek z §0.2 wykonany
  przed tą sesją, `git status` bez `M`).
- origin/master == 1798db1e; origin/master..HEAD = e8868fa2 (commit 1 tej nogi).
- FROZEN sha256: ncp.npz 0337d5ea, xai_replay ac9551ab, xai_thm_diff b4454cb9,
  xai_proofs e7a65b37, features 9adc1505. Wszystkie zgodne.

## §1. KROK 0: ważność narzędzi (śmierć S1 NIE zaszła)

| kontrola | wynik |
|---|---|
| (i) mapowanie | x0 rel_n std 6.10 · x1 rel_e std 6.03 · x2 rel_d std 0.503 (z npz; tabela w krok0.json): **PASS** |
| (ii) replay własnym krokiem z h₀=0 vs xai_replay | max \|Δy\| = **0.0** (≤1e-12) na 53 ep./74 708 tickach: **PASS** |
| (iii) klasyfikator | obrót 2π/50 ⇒ OKRESOWY p=50 ✓ · kontrakcja 0.5h+c ⇒ PUNKT_STALY ✓: **PASS** |

## §2. T3′(a) ZAPOMINANIE

1696/1696 par zbieżnych (100%). τ [s]: p50 2.044, p90 6.708, max 10.3.
max |Δy| po τ = 3.38e-6 m/s. λ₁ (QR, k=1, Δt między tickami inferencji):
53/53 epizodów ujemne, p50 −1.977 /s, min −2.434, max −1.710;
faza orbit −1.815 /s (Σdt 3641.7 s), approach −5.985 /s (Σdt 165.4 s).

## §3. T3′(b) AUTONOMIA

K = 200 orbit + 50 approach (ziarno 1, bez zwracania), M = 5000, 10 startów.

| pula | PUNKT_STALY | WIELOSTABILNY | OKRESOWY | INNY | ρ p50 / max |
|---|---|---|---|---|---|
| orbit (200) | 193 (96.5%) | 7 | 0 | 0 | 0.893 / 0.969 |
| approach (50) | 50 (100%) | 0 | 0 | 0 | 0.791 / 0.924 |

Wybory nazwane (PRE ich nie precyzuje): norma nawrotu L2; agregacja per
wejście: wszystkie starty stałe i rozrzut < 1e-6 ⇒ PUNKT_STALY, rozrzut
> 1e-3 ⇒ WIELOSTABILNY, ≥ 1 start okresowy ⇒ OKRESOWY; „h z logu" = stan
replayu PO wylosowanym ticku.

## §4. Werdykt T3′: **H-ECHO** (a 100% ≥ 95% ∧ b 96.5% ≥ 95%)

## §5. T4′

**Krok 0b (litera kierunku nauczyciela):** `bench/scenarios.py:70`
`orbit_dir = rng.choice(["CW", "CCW"])`; konsument
`r03/controllers/orbit_executor.py:93-96` (CCW: tan = (−out_e, out_n);
CW: tan = (out_e, −out_n); out = −r̂). Stąd CCW ⇒ tan = −t̂ ⇒ v_tan < 0,
a CW ⇒ v_tan > 0. Sieć nie ma tego wejścia (features.py: 8 cech).

**Różnicówka** (y surowe przed clip_v, rel odnormalizowane):
- T4a d ≥ 12: n = 1631, kontrprzykładów 0, min v_rad = 2.165 m/s.
- T4b d ≤ 4: n = 8 < 30 ⇒ **NIEROZSTRZYGALNE**. Opisowo wszystkie 8 mają
  v_rad > 0 (pełna lista: t4b_wszystkie.json):

| sid | t [s] | d [m] | v_rad [m/s] | od 1. inferencji [s] |
|---|---|---|---|---|
| c09_s02 | 188.148 | 1.988 | 1.859 | 0.000 |
| c09_s02 | 188.200 | 1.979 | 1.327 | 0.052 |
| c09_s03 | 189.476 | 0.571 | 0.809 | 0.000 |
| c09_s03 | 189.524 | 0.570 | 0.926 | 0.048 |
| c09_s03 | 189.576 | 0.944 | 0.569 | 0.100 |
| c09_s03 | 189.628 | 0.940 | 0.439 | 0.152 |
| c09_s03 | 189.680 | 2.147 | 1.821 | 0.204 |
| c09_s03 | 189.728 | 2.138 | 1.272 | 0.252 |

Wszystkie to pierwsze ≤ 0.25 s tracku (h z biegu od zera) przy skaczącym d.
Korpus nie zawiera normalnego lotu z d ≤ 4 m.

**Przedziałówka T4a:** ε-rury (ε_x 0.02 na 8 cechach znorm., ε_h 0.01 wokół
h_prev) **1631/1631 = 100%**. Próba globalna: d ∈ [12, 17.82], θ w 8 sektorach,
x₂..x₇ i h w pudełku p1–p99 z xai_s1_pudelko.json (28 wym.), bisekcja wszerz,
budżet 20 000 komórek wyczerpany ⇒ **0.0% objętości**.

**T4c (opisowo):** 53/53 epizodów z ≥ 10 tickami w paśmie 6–10 m.
Kierunek sieci (większość ticków) to **CW w 53/53**. Udział v_tan < 0 per
epizod wynosi od 0.0 do 0.41. Stały znak na wszystkich tickach pasma ma 6/53
(11.3%). Zgodność z orbit_dir scenariusza: 28/53 (52.8%). Tabela per epizod
jest w t4.json.

## §6. Mutanty (w pamięci, zero plików wag)

| mutant | T4a cex / n | T4b cex / n | T3′ |
|---|---|---|---|
| M6 odwrócenie (Wo,bo → −) | **1631 / 1631** (obala ✓) | 0 / 8 | — (dynamika h bez zmian) |
| M7 k=2 | — | — | MIESZANY (a 100%; orbita PS 26 / WS 173 / INNY 1) |
| M7 k=3 | — | — | MIESZANY (a 91.8%; orbita PS 11 / WS 99 / OKR 74 / INNY 16) |
| M7 k=5 | — | — | **H-GEN** (a 45.8%; orbita OKR 199 / INNY 1) |
| M1 znak | 0 / 1631 | 8 / 8 | — |
| M2 skala | 7 / 1631 | 8 / 8 | — |
| M3 zero | 0 / 1631 | 8 / 8 | — |
| M4 głowa | 0 / 1631 | 8 / 8 | — |
| M5 bramka | 0 / 1631 | 8 / 8 | — |

M1, M3, M4 i M5 nie łamią T4a: znak v_rad przy d ≥ 12 jest odporny na te
zaburzenia (S1 nogi XAI nie projektowała ich pod T4). Wymóg PRE dotyczył
tylko M6 i jest spełniony.

## §7. Statusy (jednym wierszem)

- **T3′: H-ECHO** — (a) 1696/1696 zbieżnych, τ p90 6.7 s, λ₁ < 0 w 53/53;
  (b) orbita 193/200 PS + 7 WS, ρ ≤ 0.969.
- **T4a: PROVED** na ε-rurach 1631/1631 (d ∈ [12, 17.3] m), próba globalna 0%.
- **T4b: NIEROZSTRZYGALNE** (n = 8; opisowo 8/8 v_rad > 0 w pierwszych 0.25 s tracku).
- **T4c: opisowo CW 53/53**, zgodność z nauczycielem 52.8%.

## §8. Odchylenia nazwane

- Narzędzia powstały w poprzedniej (przerwanej) sesji CC. W tej sesji
  przeczytałem je przed uruchomieniem i zmieniłem jedno miejsce:
  `global_box` przeszukuje wszerz (FIFO) zamiast w głąb (LIFO), bo przy
  LIFO budżet 20k wyczerpałby się w pierwszym sektorze.
- W korpusie pojawiają się powtórzone sid (FANTOM/DEMO_C), np. c00_s01 ×2.
  T4c liczy epizody, nie unikalne sid.

## §9. KSIĘGA (wejście do ANEKS_XAI2-1, rozliczenie po weryfikacji CC)

P-XA2-1 (0.60) H-ECHO → ✓ · P-XA2-2 (0.55) T4a 0 cex → ✓ ·
P-XA2-3 (0.60) T4b → n.r. (n = 8) · P-XA2-4 (0.50) ≥ 80% ε-rur → ✓ (100%).
