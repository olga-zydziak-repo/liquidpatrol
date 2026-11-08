# ANEKS_KOTW-1 — kotwica centralna CLOSED-BY-RECON (piła nie domyka się o 0.30 m przy idealnej poprawce); jedyna reformulacja: kotwice na obwodzie strefy (PROMPT_KOTW_R2, przy biurku)

CC · 8.11.2026 · łańcuch KOTW, po STOP-KOTWR (662293ae na origin).
Wklejany RAZEM z PROMPT_KOTW_R2. Sygnały bez numeru odrzucasz.

## §1. Weryfikacja CC z repo

- Zakres czysty: 11 plików, +15959, 0 bootów. Narzędzia R1 i R5
  uruchomione u CC: `r1_widocznosc.json` i `r5_pila.json` **identyczne
  bajtowo**. Arytmetyka decydująca z zamrożonej krzywej 2d: ε_b(37) =
  4.567, +Δ_D5 1.524 = 6.091 > 5.79 — przekroczenie 0.30 m przy
  ε_fix = 0, zgodnie z raportem. Niezależna rekonstrukcja CC najgorszej
  przerwy (c05_s01, FANTOM r2_V2, własny kod z GT i quaternionów):
  38.6 s wobec 37.1 s — różnica stożka metody, ta sama geometria.
- Werdykt preregu R6 zachodzi (R5 pusty: 0/27 kombinacji):
  **kotwica w środku strefy CLOSED-BY-RECON.** Mechanizm: na orbicie
  dron patrzy na intruza, na zewnątrz — środek strefy jest za kamerą
  przez pół okrążenia; w fazie startu kamera pozioma nad kotwicą jej
  nie widzi. To geometria pozycji kotwicy, nie dokładność poprawki:
  umiejscowienie kotwicy w (0,0) było wyborem CC w prompcie — ✗
  projektowe CC do KSIĘGI.
- Przyjęte bez lotów: R3 wariant B (poprawka po stronie osłony; EV
  w PX4 1.16.2 z timeoutem 1 s dyskwalifikuje wariant A przy oknach
  co ~20 s — cytat przyjęty), R4 (fałszywej admisji na kotwicy litera
  nie wyklucza: MTI bez kompensacji paralaksy, brama bez minimum ruchu,
  odświeżenie tracku bez bramki pozycji — feed_vision.py:202;
  rozstrzygnie sonda S1, jeśli noga dożyje).
- Zastrzeżenia wykonawcy zapisane: próg 10 px niezmierzony (założenie
  do sondy), bias yaw ~−3° możliwy artefakt dopasowania czasu
  (rozdzielić w R2), pochylenie 0.5°/wysokość 0.2 m przyjęte bez
  pomiaru (nazwane założenia).

## §2. Reformulacja — zasada i granica

Jak przy SKAN2: werdykt litery stoi i jest zapisany; reformulacja
bierze się z mechanizmu zmierzonego w tym samym reconie (dron patrzy
na zewnątrz ⇒ kotwice powinny stać na obwodzie, nie w środku).
**To jest jedyna reformulacja nogi KOTW:** jeśli obwód nie domknie
piły przy biurku, KOTW zamyka się w całości i trzeciego podejścia nie
ma. Perymetr w obronie perymetru ma ogrodzenie z konstrukcji zadania,
więc maszt na obwodzie nie zmienia misji ani kanonu — wchodzi jako
wariant świata klasy dekalu (addytywny, poza FROZEN), dopiero w S1.

## §3. KSIĘGA (append-only przy commicie §CO)

```
## KOTW recon 1 (ANEKS_KOTW-1, 8.11.2026): kotwica centralna
CLOSED-BY-RECON (0 bootów)
- Piła nie domyka się przy żadnej z 27 kombinacji; najgorsza przerwa
  orbity 37.1 s (CC: 38.6 s niezależnie) ⇒ ε_b(37) 4.567 + Δ 1.524 =
  6.091 > 5.79 przy idealnej poprawce. Mechanizm: orbita patrzy na
  zewnątrz, start ma kamerę poziomą nad kotwicą.
- ✗ projektowe CC: pozycja kotwicy (0,0) wpisana w prompt bez rachunku
  geometrii spojrzenia; recon sfalsyfikował ją za 0 bootów (ósme
  zamknięcie kierunku przy biurku w programie).
- Znaleziska przechodnie: EV-aiding PX4 1.16.2 (timeout 1 s)
  niezdatny do poprawek co ~20 s ⇒ wariant B (osłona) jedyny;
  fałszywa admisja na obiekcie statycznym nie jest wykluczona literą
  percepcji (paralaksa w MTI, brak bramki pozycji w odświeżeniu
  tracku) — ryzyko nazwane dla każdej przyszłej kotwicy.
```

## §CO

Bramka: origin/master == **662293ae**. Commit 1: korzeń
`ANEKS_KOTW-1.md` verbatim (byte-check sha256 z wiadomości CC) +
KSIĘGA §3 append-only. Potem recon PROMPT_KOTW_R2 w tej samej sesji
(0 bootów). Push = Olga.
