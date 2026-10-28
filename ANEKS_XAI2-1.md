# ANEKS_XAI2-1 — przyjęcie S1, werdykt nogi XAI-II, KSIĘGA P-XA2-1…4, CO (samowykonalny)

CC · 28.10.2026 · po STOP-XAI2-1 (ARCH-1 `e8868fa2` + `0e50a7e5`),
zweryfikowanym z repo wykonaniem. §5 = zlecenie CO. Sygnały bez numeru
wykonawca odrzuca.

## §1. Weryfikacja CC (niezależna)

1. **ARCH-1 PASS:** `PRE_XAI2.md` w korzeniu bajt w bajt (0649deea…0acb).
   Zakres `0e50a7e5`: 12 plików, wszystkie nowe, wyłącznie `results/XAI2/**`.
2. **Mapowanie cech sprawdzone literą, nie deklaracją:** x₀..x₂
   odnormalizowane statystykami z npz pokrywają się z surowym
   trk_pos_ned − own_pos_ned z demo.jsonl do 1.8·10⁻¹⁵ na całym korpusie
   (lekcja (3) z ERRATUM_XAI-1 zastosowana).
3. **Przeliczone własnym forwardem i własnymi ziarnami (53 loty):**
   - T3′(a): 424/424 par zbieżnych (8 losowych h₀ na lot), τ p50 1.99 /
     p90 6.47 / max 10.20 s — zgodne z 2.04 / 6.71 / 10.3 s raportu. λ₁ nie
     przeliczałem; zbieżność globalna, której λ₁ jest lokalną wersją, tak.
   - T3′(b): własna próbka 40 wejść z orbity → 39 punktów stałych + 1
     wielostabilny (97.5%), 10/10 z podejścia; ρ max 0.966 — zgodne z 96.5%
     i ρ max 0.969 raportu.
   - T4a: n = 1631, 0 kontrprzykładów, min v_rad 2.165 m/s — co do liczby.
     Przedziałówka własną implementacją (licznik v_rad·d, przecięcie dwóch
     poprawnych rozkładów kroku): 1467/1467 rur z lotów LIQ certyfikowanych.
     Pierwsze podejście z dzieleniem przez d dało 30/40 — to luz metody, nie
     twierdzenia; sformułowanie wykonawcy (licznik) jest ciaśniejsze i poprawne.
   - T4b: n = 8, 8/8 z v_rad > 0 — te same ticki i wartości.
   - T4c: dominujący znak v_tan ten sam w 53/53, ściśle stały w 6/53, udział
     ticków przeciwnych do 0.41 — co do liczby.
4. **Konwencja kierunku (sprawdzone wprost z pozycji w locie):** v_tan > 0,
   które kod nauczyciela i FREEZE_XAI2 nazywają „CW", na mapie z północą
   u góry jest ruchem PRZECIWNYM do wskazówek zegara (kąt drona wokół celu
   rośnie w 8/8 sprawdzonych lotach). „CW" to etykieta konwencji kodu, w której
   (n, e) czyta się jak (x, y). W opisach dla ludzi: „zawsze w tę samą stronę"
   albo „przeciwnie do wskazówek zegara, widok z góry".

## §2. Werdykt (zdania zamrożone)

**Noga XAI-II CLOSED za 0 bootów; śmierć S1 nie zaszła (krok 0 PASS 3/3).**

> **T3′ = H-ECHO.** Sieć zapomina swój stan początkowy: 1696/1696 losowych
> startów (32 na każdy z 53 lotów) zbiega do trajektorii referencyjnej,
> w medianie po 2 s, najpóźniej po 10.3 s, a różnica komendy po zbieżności nie
> przekracza 3.4·10⁻⁶ m/s; warunkowy wykładnik Lapunowa jest ujemny w 53/53
> lotach (orbita −1.8/s). Przy wejściu zamrożonym z pasma orbity stan zbiega do
> punktu stałego w 193/200 przypadków (7 wielostabilnych, 0 okresowych,
> ρ ≤ 0.969). Pierścień w przestrzeni stanu jest więc odbiciem obracającego się
> wejścia, a nie własnym rytmem sieci. Warunkowo na zalogowanych wejściach;
> zamrożone wejście to sonda matematyczna.

> **T4a PROVED na ε-rurach.** Z daleka sieć zawsze kieruje w stronę celu: na
> wszystkich 1631 tickach z d ∈ [12, 17.3] m składowa radialna komendy jest
> dodatnia (min 2.17 m/s), a znak jest certyfikowany przedziałowo w otoczeniu
> każdego z nich (ε_x 0.02, ε_h 0.01; 100%). Próba globalna na całym pudełku
> dziedziny: 0% — twierdzenie jest lokalne wokół zaobserwowanych stanów, nie
> dla dowolnego wejścia.

> **T4b NIEROZSTRZYGALNE (n = 8), z dowodem przeciwnym w małej próbce.**
> Normalny lot nie wchodzi w d ≤ 4 m; jedyne 8 ticków to narodziny tracku
> (pierwsze ≤ 0.25 s, stan od zera, d skacze 0.57 → 2.15 m) i we wszystkich
> 8 sieć kieruje w stronę celu. Zachowanie z bliska w ustalonym locie jest
> nieznane. Cytować wyłącznie razem z „8/8 obserwacji przeczy" — to zaostrza
> pkt 3 zasady cytowania FREEZE_XAI2.

> **T4c (opisowo).** Sieć krąży zawsze w tę samą stronę (dominujący znak
> w 53/53 lotach, ściśle stały w 6/53), choć nauczyciel losował kierunek
> orbity z ziarna (zgodność 28/53, czyli przypadkowa). Sieć nie ma wejścia
> o kierunku — z dwóch trybów nauczyciela nauczyła się jednego.

Wobec ERRATUM_XAI-1: wycofane „generator, nie echo" okazało się odwrotne do
prawdy. Pomiar wielokrokowy dał echo przy ‖J‖₂ ≥ 1 w każdym kroku — dokładnie
przypadek macierzy nienormalnych opisany w erracie. Errata była konieczna, nie
kosmetyczna.

**Zdanie programowe XAI po obu nogach (do cytowań, z zasadą cytowania
FREEZE_XAI2):** „NCP-20: dwa twierdzenia architektoniczne (T1: komenda
< 3 m/s, T2: |h| < 1) dowiedzione dla każdego wejścia; sieć-echo — na
zalogowanych lotach zachowanie nie zależy od stanu początkowego (1696/1696
startów zbieżnych w ≤ 10.3 s); z daleka zawsze kieruje w stronę celu
(certyfikowane wokół 1631 ticków)."

## §3. KSIĘGA — rozliczenie P-XA2-1…4 (3 ✓ / 0 ✗ / 1 n.r.)

- **P-XA2-1 (0.60) ✓** — H-ECHO.
- **P-XA2-2 (0.55) ✓** — T4a 0/1631.
- **P-XA2-3 (0.60) n.r.** — n = 8 < 30 (klauzula predykcji). Bez klauzuli
  byłoby ✗: wszystkie 8 obserwacji przeczą.
- **P-XA2-4 (0.50) ✓** — T4a certyfikowane na 100% ε-rur (jedyne T4 po
  różnicówce).

Lekcje kalibracyjne: (1) próg minimalnego n chroni przed potwierdzeniem na
małej próbce, nie przed falsyfikacją — w przyszłych PRE kontrprzykład
falsyfikuje niezależnie od n, a próg n dotyczy tylko statusu PROVED;
(2) pokrycie dziedziny (ile ticków w ogóle w niej leży) mierzyć przed
zamrożeniem progu — to nie jest podglądanie wyniku, a d ≤ 4 m dało się
wykluczyć przed PRE; (3) etykiety kierunków z kodu sprawdzać geometrią, zanim
trafią do opisu dla ludzi.

## §4. Pytanie nazwane (nie pozycja katalogu)

T4c łączy się z głównym wynikiem programu: NCP 48/48 wobec GRU 29/48,
a wszystkie 19 porażek GRU na liście przewagi to niedokręcona orbita. Pytanie:
czy GRU przegrywa, bo przy niejednoznacznym nauczycielu uśrednia dwa kierunki
krążenia zamiast wybrać jeden, co dawałoby słabszą składową styczną? Test przy
biurku: znak i moduł v_tan GRU w paśmie 6–10 m na jego własnych lotach
z kampanii LIQ (replay ramienia GRU) oraz na wejściach NCP. Jedna krótka sesja,
0 bootów. Katalog nie rośnie; otwarcie wyłącznie decyzją Olgi, z PRE jak każda
noga.

## §5. CO — zlecenie (lista zamknięta edycji)

1. Bramka: `git fetch` → origin/master == **0e50a7e5**; `origin/master..HEAD`
   puste; porcelain czysty poza nazwanymi ??.
2. Commit CO-XAI2 (jeden): (a) `ANEKS_XAI2-1.md` verbatim do korzenia (ARCH-1:
   byte-check sha256 z wiadomości CC — rozjazd ⇒ STOP); (b)
   `KIERUNKI_PO_PLANIE.md` dopisek 28.10 append-only: XAI-II CLOSED ze zdaniami
   z §2 i odsyłaczami (RAPORT_XAI2_S1, FREEZE_XAI2); XAI-FLOQUET i XAI-ZNAK →
   CLOSED; nakładka demo „co myśli sieć" → CLOSED (zrobiona w DEMOC v4/v5,
   STOP-DEMOC-4/5); GT-CZYSTOŚĆ → backlog §8 (filtr-świadek wystarcza);
   pytanie z §4 zapisane jako pytanie, nie pozycja; (c)
   `results/KSIEGA_PREDYKCJI.md` sekcja NOGA XAI-II append-only, treść §3.
3. ZERO edycji raportów, FREEZE, kodu i demo.
4. Push = Olga („wypchnięte" — CC zamyka nogę z repo). STOP.

## §6. Status

Wątek XAI zamknięty w całości: dwie nogi, 0 bootów, zero otwartych pozycji
XAI w katalogu. Katalog: 11 → 8 otwartych pozycji (XAI-FLOQUET, XAI-ZNAK
i GT-CZYSTOŚĆ zdjęte; nakładka demo domknięta formalnie). Breach 0 /
REFUSE 0 bez zmian — nic nie latało. Następna noga według kolejności
z 28.10: TOR-CECHY ∪ MULTI-TARGET, decyzja Olgi. Opcjonalnie,
nieprekomitowane: nakładka demo „32 starty zlewają się w jedną trajektorię".
