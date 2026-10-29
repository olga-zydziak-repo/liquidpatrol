# ANEKS_WK-1 — przyjęcie S1, werdykt nogi WIATR-KAMERA (V-C), KSIĘGA P-WK-1…5, CO (samowykonalny)

CC · 29.10.2026 · po STOP-WK1 (ARCH-1 `8229e185` + `f7f653bf`), zweryfikowanym
z repo wykonaniem. §5 = zlecenie CO. Sygnały bez numeru wykonawca odrzuca.

## §1. Weryfikacja CC (niezależna)

1. **ARCH-1 PASS:** `PRE_WK.md` bajt w bajt (281750e7…). Commit `f7f653bf`:
   wyłącznie nowe pliki (`results/WK/**` + trzy światy w `worlds/`), zero edycji
   istniejących. Światy w `worlds/` = kopie z reconu co do sha (4c179a14 /
   9713a8b1 / 3a605ca3). Piny w logu drivera każdego bootu: mono_cam 3354ae1e,
   x500_base 13c9174d, sha świata — PIN OK ×3, rozjazdów 0.
2. **Rejudge WK0 sędzią bazowym 8ec0fcfb, pełny i ze świadkiem:** 2/8 D6,
   identycznie w obu wariantach; ważne V2′ 7/8, wśród ważnych 1/7. Porażki:
   c_sweep ×5 (sweep 524–616° < 630°), a_entry ×1 (c02, wejście po 27.4 s).
   We wszystkich ośmiu epizodach frac pasma 1.00, d_min 7.0–8.1 m — co do liczby
   z raportem. Baza stock na kamerze (FANTOM S2 r1_V2 i r2_V2, te same
   scenariusze c00–c07, ze świadkiem): **8/8 D6**, sweep 767–996°; stosunek
   sweep WK0/stock 0.62–0.83.
3. **Mechanizm zmierzony przez CC (logi, 0 bootów):**
   - Mediana składowej stycznej w oknie orbity, c00–c03: komenda sieci
     1.56–1.65 m/s w WK0 wobec 1.89–1.96 w stocku (≈ −17%); prędkość
     zrealizowana 1.33–1.43 wobec 1.99–2.07 m/s (0.64–0.70 stocku). PX4 pod
     oporem realizuje ok. 86% komendy, w stocku ok. 105%.
   - Efektywny liniowy współczynnik oporu z bilansu sił (orientacja z feedu +
     prędkość, faza orbity, ~4 200 klatek na boot): **k ≈ 1.05 /s w habitacie WK
     wobec 0.12 /s w stocku — około 9×.**
4. **Odchylenie przyjęte:** brak powtórki epizodu c04 (V2′ 0.8905 < 0.90).
   Nawet zdany c04 dawał najwyżej 2/8, więc powtórka nie mogła zmienić
   werdyktu — booty kupują wyłącznie informację zmieniającą werdykty
   (ANEKS_FANTOM-2 §5).

## §2. Werdykt (zdania zamrożone)

**Noga WIATR-KAMERA CLOSED werdyktem V-C, 3/≤9 bootów; śmierć nie zaszła
(dym PASS za pierwszym podejściem).**

> **V-C.** W habitacie z oporem aerodynamicznym (WindEffects ze skalą 1.0;
> zmierzony opór k ≈ 1.05 /s, około 9× więcej niż w modelu stock), przy wietrze
> 0, sieć NCP-20 uczona bez tego oporu zdaje egzamin misji D6 w 2/8 epizodów
> na komórkach v ≤ 0.5 (1/7 ważnych), wobec 8/8 tych samych scenariuszy na
> kamerze w świecie stock. Mechanizm: orbita jest o ~1/3 wolniejsza —
> sieć komenderuje ~17% mniejszą prędkość styczną, a autopilot pod oporem
> realizuje ~86% komendy — więc obrót wokół celu nie dobija do progu 630°
> w 70 s. Wszystko inne trzyma: dystans 6–10 m przez 100% okna, d_min ≥ 7.0 m,
> cel w kadrze, zero ingerencji osłony, breach 0. Wiatru 1.5 i 3 m/s nie
> latano — bramka wiatru 0 nie przeszła.

**Interpretacja dla tezy „mała sieć umie latać" (do cytowań razem z V-C):**
sieć w tym habitacie leci bezpiecznie i poprawnie, ale za wolno na egzamin
tempa. Opór habitatu jest najpewniej kilkukrotnie silniejszy niż dla realnego
drona tej klasy — rachunek orientacyjny: opór wirnikowy małych multikopterów
w literaturze to rząd kilku dziesiątych 1/s, do weryfikacji. Wynik jest więc
testem przeciążeniowym przeniesienia między fizykami, nie werdyktem o locie
w realnym powietrzu.

**Pełzanie wysokości (opisowo):** w trybie kamerowym nie wystąpiło — zero
sejwów GEOFENCE, choć recon przewidywał 1–2/8. Recon wnioskował z kampanii W,
lecianej harnessem sprzed naprawy jednostek yaw (N1). Atrybucja pełzania
z ANEKS_W-2 dostaje więc trzeci kandydujący czynnik: epokę harnessu.
Zdanie z RECON_WK §R2 cytować wyłącznie z kwalifikatorem „kampania W, epoka
przed N1".

## §3. KSIĘGA — rozliczenie P-WK-1…5 (2 ✓ / 2 ✗ / 1 n.r.)

- **P-WK-1 (0.85) ✓** — dym PASS za pierwszym podejściem.
- **P-WK-2 (0.55) ✗** — WK0 2/8 < 6/8.
- **P-WK-3 (0.40) n.r.** — etap B nie poleciał.
- **P-WK-4 (0.90) ✓** — breach 0.
- **P-WK-5 (0.60) ✗** — zero sejwów GEOFENCE; pełzanie nie wystąpiło.

Lekcje kalibracyjne: (1) parametry fizyczne nowego habitatu mierzyć wobec
zewnętrznego odniesienia PRZED zamrożeniem — opór k ≈ 1.05 /s był do policzenia
z istniejących logów W, a CC opisał habitat jako „bliżej fizyki", nie mierząc go;
(2) predykcje przenoszone z danych innej epoki harnessu nazywają tę epokę jako
czynnik zakłócający — R3 reconu to zrobił, R2 nie.

## §4. Następca (KATALOG — nic nie otwieram)

**WK-II / OPÓR REALNY** — jedna pozycja, dwa etapy. (a) Habitat z oporem
skalibrowanym do zewnętrznego odniesienia fizycznego (nowe pliki świata; skala
oporu wybrana z fizyki i zapisana w PRE, nigdy dostrajana pod wynik sieci),
potem WK0 i ewentualnie wiatr na tej samej siatce: 2–7 bootów. (b) Tylko jeśli
(a) też łamie misję: douczenie sieci w habitacie z oporem — nowe wagi, nowy
FREEZE, duża noga. Trigger: decyzja Olgi albo dowolne zdanie o locie w realnej
fizyce.

## §5. CO — zlecenie (lista zamknięta edycji)

1. Bramka: `git fetch` → origin/master == **f7f653bf**; `origin/master..HEAD`
   puste; porcelain czysty poza nazwanymi ??.
2. Commit CO-WK (jeden): (a) `ANEKS_WK-1.md` verbatim do korzenia (ARCH-1:
   byte-check sha256 z wiadomości CC — rozjazd ⇒ STOP); (b)
   `KIERUNKI_PO_PLANIE.md` dopisek 29.10 append-only: WIATR-KAMERA CLOSED (V-C)
   ze zdaniami z §2 i odsyłaczami (RAPORT_WK_S1, RECON_WK); pozycja WK-II
   według §4 z triggerem; (c) `results/KSIEGA_PREDYKCJI.md` sekcja NOGA WK
   append-only, treść §3.
3. ZERO edycji raportów, reconu, FREEZE i kodu.
4. Push = Olga („wypchnięte" — CC zamyka nogę z repo). STOP.

## §6. Status

Noga WK CLOSED, 3/≤9 bootów (6 zaoszczędzonych bramką), breach 0 / REFUSE 0.
Program zyskał: działające złożenie wiatru z kamerą bez dotykania zamrożonych,
zmierzony opór habitatu, mechanizm spowolnienia orbity z rozkładem na sieć
i autopilot oraz granicę tezy — lata w fizyce bez oporu, w fizyce
z bardzo silnym oporem leci bezpiecznie, ale za wolno na egzamin tempa.
Katalog: 8 → 9 otwartych pozycji (doszła WK-II; sama noga WK nie była pozycją
katalogu, pochodziła z listy „co jeszcze" w raporcie programu).
