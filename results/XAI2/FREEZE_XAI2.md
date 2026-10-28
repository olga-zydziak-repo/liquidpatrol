# FREEZE_XAI2 — wyniki nogi XAI-II (S1), zamrożone

CC · 28.10.2026 · PRE_XAI2 (sha256 0649deea, commit e8868fa2) · 0 bootów.
Sieć ncp 0337d5ea; korpus 53 ep. / 74 708 ticków inferencji (xai_replay ac9551ab).

## Werdykt T3′ (prereg PRE §2): **H-ECHO**

- (a) ZAPOMINANIE: **1696/1696 par zbieżnych (100%)** (N = 32 × 53, ziarno 0,
  próg 10⁻⁶ na końcu epizodu); τ p50 2.04 s / p90 6.71 s / max 10.3 s czasu
  symulacji; max |Δy| po τ 3.4·10⁻⁶ m/s. λ₁ (QR) per epizod: 53/53 ujemne,
  p50 −1.98 /s, zakres [−2.43, −1.71]; per faza: orbit −1.82 /s
  (3642 s), approach −5.99 /s (165 s).
- (b) AUTONOMIA: orbita **193/200 PUNKT STAŁY (96.5%)** + 7 WIELOSTABILNY,
  0 OKRESOWY, 0 INNY; podejście 50/50 PUNKT STAŁY; promień spektralny
  ∂f/∂h w punktach stałych: orbita p50 0.893 / max 0.969, podejście
  p50 0.791 / max 0.924 (wszystkie < 1).
- Margines progu (b): 3 wejścia (190/200 = 95%).

## Statusy T4′

| twierdzenie | dziedzina | n | różnicówka | ε-rury | próba globalna | status |
|---|---|---|---|---|---|---|
| T4a d ≥ 12 m ⇒ v_rad > 0 | d ∈ [12, 17.32] m na korpusie | 1631 | 0 kontrprzykładów (min v_rad 2.16 m/s) | 1631/1631 = 100% | 0.0% objętości (20k komórek) | **PROVED** (na ε-rurach) |
| T4b d ≤ 4 m ⇒ v_rad < 0 | d ∈ [0.57, 4] m na korpusie | **8** | 8/8 z v_rad > 0 (opisowo) | — | — | **NIEROZSTRZYGALNE** (n < 30) |
| T4c kierunek orbity | pasmo 6–10 m | 53 ep. | — | — | — | OPISOWE (niżej) |

T4b: wszystkie 8 ticków w dziedzinie to pierwsze 0.25 s inferencji dwóch
epizodów (c09_s02, c09_s03) ze skaczącym d (0.57 → 0.94 → 2.15 m) przy h
z biegu od zera; w normalnym locie sieć nie wchodzi w d ≤ 4 m.

T4c (opisowo): sieć krąży **CW w 53/53 epizodach** (większość ticków
w paśmie ma v_tan > 0); stały znak na wszystkich tickach pasma w 6/53 (11.3%);
zgodność z orbit_dir nauczyciela 28/53 (52.8%), czyli na poziomie rzutu
monetą. Sieć nie ma wejścia kierunku i nie wybiera go per epizod: zawsze
krąży w jedną stronę (CW).

## Czułość

- M6_odwrócenie: T4a 1631/1631 kontrprzykładów ⇒ **obala przechodzące T4a ✓**.
- M7_rekurencja: k=2 MIESZANY (a 100%, orbita 173 WIELOSTABILNY),
  k=3 MIESZANY (a 91.8%, orbita 74 OKRESOWY), k=5 **H-GEN** (a 45.8%,
  orbita 199/200 OKRESOWY) ⇒ maszyneria werdyktu umie wydać H-GEN.

## Narzędzia (sha256, prefiks 8)

xai2_common.py 38c5366f · xai2_t3.py 8f723d16 · xai2_t4.py b628fc06.
Wyniki: krok0.json 4b4c3231 · t3.json ab848e30 · t4.json ef8dfd0d ·
t4b_wszystkie.json e32c06d7 · mutanty.json 3204aeec.

## Zasada cytowania

1. T3′ zawsze z werdyktem i liczbami (a)/(b): „H-ECHO: 100% par zbieżnych
   (τ p90 6.7 s), 96.5% orbitalnych wejść z jedynym punktem stałym
   (ρ ≤ 0.969)". Zawsze z warunkiem: (a) na zalogowanych wejściach,
   (b) zamrożone wejście = sonda matematyczna.
2. T4a zawsze z dziedziną i %: „PROVED na ε-rurach (ε_x 0.02, ε_h 0.01)
   wokół 1631 ticków korpusu z d ∈ [12, 17.3] m; próba globalna 0%
   objętości". Nie cytować jako twierdzenia globalnego.
3. T4b: NIEROZSTRZYGALNE na korpusie (n = 8). Nie cytować znaku.
4. Zero roszczeń D6 i misji.
5. Pierścień = ECHO WEJŚCIA (stan zapomina h₀, a przy zamrożonym wejściu
   zbiega do punktu). Werdykt H-ECHO, więc FREEZE nie zapisuje nazwanego
   pytania H-GEN/MIESZANY. Obserwacja CW-only to opis, nie pozycja katalogu.
