# ANEKS_WK3-1 — przyjęcie S1, werdykt nogi WK-III (V-A3), KSIĘGA P-WK3-1…4, CO (samowykonalny)

CC · 30.10.2026 · po STOP-WK3-1 (ARCH-1 `8bc3d19f` + `d1f8f15a`), zweryfikowanym
z repo wykonaniem. §5 = zlecenie CO. Sygnały bez numeru wykonawca odrzuca.

## §1. Weryfikacja CC (niezależna)

1. **ARCH-1 PASS:** `PRE_WK3.md` bajt w bajt (3758b86f…). Commit `d1f8f15a`:
   wyłącznie nowe pliki; driver `wk3_boot.sh` = kopia `wk2_boot.sh` z różnicą
   tylko w liście światów, katalogu i komunikatach; w logu każdego z 4 bootów
   PIN OK ×2 i sha świata zgodny z profilem (P1 fe96b096, P2 e47ef380).
2. **Rejudge sędzią bazowym 8ec0fcfb, 16 epizodów:** P1 **8/8** ze świadkiem
   (pełny 6/8 — c06 i c07 padają na b_frac wyłącznie przez pierwsze próbki GT
   sprzed teleportu; frac ze świadkiem 1.00, d_min 6.75 / 7.89 — klasa
   ERRATUM-DMIN, świadek rozstrzyga), P2 **7/8** w obu wariantach. V2′ 16/16.
   Mediana sweep/stock 0.897 (P1) i 0.885 (P2) — nie gorzej niż przy stałym
   wietrze w WK-II (0.83–0.90). d_min ≥ 6.35 m we wszystkich 16.
3. **Opór per boot, własny bilans z literą wiatru odjętą od prędkości:**
   0.495 / 0.495 / 0.498 / 0.496 — habitat bez zmian (kalibracja 0.494).
4. **Porażka P2 c01 z logów:** jedyny powód a_entry — wejście w pas po
   26.2 s (limit 25 s), potem pełna orbita (sweep 838°, frac 1.00, d_min 7.14).
   Track startowy wygasł po 2.95 s, ponowna akwizycja po ~20 s przy przechyle
   ≤ 9.5°. Ta sama klasa co G1.5 c03 w WK-II: akwizycja, nie tor.
5. **Przechył — korekta rachunku CC po drodze:** z surowego feedu wyszło mi
   31.8–38.2° maksimum per boot; po ograniczeniu do okien epizodów maksima
   wynoszą 16.3–26.3°, zgodnie z raportem. Szczyty 31–38° leżą MIĘDZY
   epizodami (szybki powrót do home po reset). Ryzyko z reconu (34.6°
   u nauczyciela wobec pół-pola kamery 40.4°) w lotach sieci nie zaszło:
   sieć w orbicie przechyla drona mniej niż nauczyciel w kalibracji.
6. **Kadr:** liczby per epizod zgodne; w żadnej porażce wypadnięcie dołem nie
   poprzedza utraty; 85% wypadnięć to bok w fazie skanu/obrotu na cel.

## §2. Werdykt (zdania zamrożone)

**Noga WK-III CLOSED werdyktem V-A3, 4/≤8 bootów; śmierć nie zaszła;
breach 0 / REFUSE 0 / sejwy 0.**

> **V-A3.** NCP-20 (20 neuronów, uczona w świecie bez oporu i bez wiatru)
> prowadzi pełną misję na własnej kamerze pod wiatrem zmiennym w czasie,
> w habitacie z realnym oporem (k ≈ 0.49 /s), komórki v ≤ 0.5: profil
> łagodny (średnia 2 m/s, porywy 1.2–2.8 m/s, okres 8 s) **D6 8/8**; profil
> ostry (0.4–3.6 m/s, okres 4 s, kierunek ±30° z okresem 11 s) **D6 7/8**,
> breach 0, sejwy osłony 0. Jedyna porażka to spóźniona akwizycja celu
> (wejście w pas po 26.2 s przy limicie 25 s), po której orbita była pełna.
> Tempo orbity 0.89 stocku, przechył w epizodach ≤ 26.3°, cel nigdy nie
> wypadł z kadru dołem przed porażką. Sinus deterministyczny — to „wiatr
> zmienny o znanym profilu", nie turbulencja.

**Dla tezy „mała sieć umie latać":** po WK-II wolno było mówić „przy stałym
wietrze do 3 m/s"; od dziś: **„pod wiatrem zmiennym w czasie z porywami do
3.6 m/s i obrotem kierunku, w habitacie z realnym oporem"**. Kanon W
zostaje: nie „odporna na wiatr" (brak turbulencji stochastycznej, brak
realnego sprzętu), nic o porywach ponad 3.6 m/s.

**Mechanizm, który się powtarza (3 nogi):** w WK-II (G1.5) i WK-III (P2)
wszystkie 3 porażki sieci na kamerze pod wiatrem to akwizycja/track w pierwszych
sekundach (startowy track wygasa po ~3 s, ponowne złapanie trwa 15–20 s),
nigdy tor orbity po akwizycji. Sieć lata; percepcja czasem spóźnia start.
To wzmacnia istniejącą pozycję PERCEPCJA-II (ii), nie tworzy nowej.

## §3. KSIĘGA — rozliczenie P-WK3-1…4 (3 ✓ / 0 ✗ / 1 n.r.)

- **P-WK3-1 (0.70) ✓** — P1 8/8.
- **P-WK3-2 (0.45) ✓** — P2 7/8.
- **P-WK3-3 (0.60) n.r. (adjudykacja CC)** — litera trafiona (P2: 5/8
  epizodów z celem poza kadrem ≥ 5%), ale ten sam miernik przy stałym wietrze
  WK-II daje 4–5/8, a 85% wypadnięć to bok w fazie skanu, niezależny od
  porywów. Predykcja miała mierzyć mechanizm przechyłu, a miernik go nie
  wyodrębnia — nie zaliczam trafienia na źle postawionym mierniku. **Lekcja
  kalibracyjna:** predykcja o mechanizmie musi mieć miernik z bazą kontrolną
  wpisaną w PRE (tu: „dół ≥ x% ponad poziom przy stałym wietrze"), inaczej
  trafia w szum.
- **P-WK3-4 (0.90) ✓** — breach 0.

Druga lekcja (z §1.5, błąd CC w weryfikacji, złapany przed werdyktem):
statystyki przechyłu i kadru liczyć wyłącznie w oknach epizodów — między
epizodami dron wykonuje manewry nienależące do misji.

## §4. Katalog

Bez nowych pozycji. Dopisek do PERCEPCJA-II (ii) MTI-czołowy: trzeci
przypadek spóźnionej akwizycji pod wiatrem (P2 c01) obok G1.5 c03/c06;
łącznie 3/32 epizodów kamerowych pod wiatrem. Wątek wiatr+kamera (WK, WK-II,
WK-III) zamknięty w całości: 13 bootów, breach 0.

## §5. CO — zlecenie (lista zamknięta edycji)

1. Bramka: `git fetch` → origin/master == **d1f8f15a**; `origin/master..HEAD`
   puste; porcelain czysty poza nazwanymi ??.
2. Commit CO-WK3 (jeden): (a) `ANEKS_WK3-1.md` verbatim do korzenia (ARCH-1:
   byte-check sha256 z wiadomości CC — rozjazd ⇒ STOP); (b)
   `KIERUNKI_PO_PLANIE.md` dopisek 30.10 append-only: WK-III CLOSED (V-A3)
   ze zdaniami z §2, odsyłacze (RAPORT_WK3_S1, RECON_WK3), dopisek do
   PERCEPCJA-II (ii) z §4; (c) `results/KSIEGA_PREDYKCJI.md` sekcja NOGA WK-III
   append-only, treść §3.
3. ZERO edycji raportów, reconu, FREEZE, PRE i kodu.
4. Push = Olga („wypchnięte" — CC zamyka nogę z repo). STOP.

## §6. Status

Katalog 8 pozycji, bez zmian. Breach 0 / REFUSE 0 programowo. Raport programu
dostaje aktualizację punktu „lata na kamerze w wietrze" o wiatr zmienny.
Program wraca do trybu katalogu; najbliższe tanie ruchy to warstwa 0
(rozmowa z pilotem, wersja EN raportu, opcjonalny akt 6 dema z bootów P2 —
montaż, 0 lotów).
