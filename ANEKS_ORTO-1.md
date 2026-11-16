# ANEKS_ORTO-1 — zamknięcie reconu ORTO-S0: śmierć Ś3 dla mapy z edycji sprzed 13 lat; wynik wąski z winy projektu CC; kontrola (ta sama edycja) działa

LiquidPatrol · CC · 16.11.2026 · łańcuch ORTO, po STOP-ORTOR-DECYZJA
(db632bba na origin). Do ratyfikacji sygnałem **„ratyfikuję ORTO-1"**.
Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC (z repo, własnym kodem)

1. **Model kamery.** Rzut pozycji znaczników na kadr przy pozie GT
   wobec zapisanych detekcji, trzy loty NAD2, te same liczby detekcji
   co w raporcie (3802 / 3754 / 3726): p50 0.75 px, p95 1.1 px, max
   2.5 px. Różnica wobec 0.28 px wykonawcy to konwencja środka piksela.
2. **Tabela strojenia.** Zestawienie reguły wybranej, policzone od
   nowa z `r4_strojenie.json.gz`: wszystkie 18 wierszy raportu
   identyczne.
3. **Ocena częściowa**, której wykonawca nie zestawiał. Reguły
   zamrożone z c05, loty oceny, które zdążyły się policzyć (A i B:
   p02, p04, p07; C dodatkowo p09 i lot długi):
   - para, łata A: SIFT 6 przyjętych, max błąd 35.1 m; AKAZE nic nie
     przyjmuje; korelacja 6 przyjętych, max 2.70 m, przerwa 71 s;
   - para, łata B: SIFT 1 przyjęta, 25.5 m; pozostałe bez reguły;
   - para, łata C: korelacja 8 przyjętych, max 59.9 m;
   - kontrola, łaty A i B: cechy przyjmują 1149 z 1149 klatek, błąd
     p50 0.03–0.07 m, max 0.17–0.18 m, bez przerw.
4. **Dane.** Para 2012-04-28 → 2025-08-12 wybrana literą promptu
   spośród siedmiu edycji o pikselu ≤ 10 cm.

## §2. Werdykt

1. **Ś3 zachodzi literą.** Kryterium jest maksimum po lotach oceny,
   więc rozstrzygają je loty już policzone: na każdej łacie i dla
   każdego kandydata największy błąd przyjętej poprawki przekracza
   1.37 m albo przez cały lot nie ma żadnej przyjętej. Kolejne loty
   nie mogą obniżyć maksimum.
2. **Recon ORTO-S0 — CLOSED.** Bieg oceny przerwany decyzją Olgi
   16.11 („zamykam ORTO-S0 decyzją") przy 42 z 78 zadań; R6–R8
   niewykonane. 0 bootów.
3. Kierunek „cudza mapa z innej edycji" w tej postaci zamknięty przy
   biurku.

## §3. Co ten wynik mówi, a czego nie

**Mówi:** klasyczne dopasowanie kadru (SIFT, AKAZE, korelacja
gradientu) do ortofotomapy starszej o 13 lat, z inną porą roku, na
łatach zdominowanych przez drzewa nie działa. Błędy sięgają dziesiątek
metrów, a reguła odrzucania zostawia najwyżej 10 poprawek na sześć
lotów.

**Mówi też:** przy tej samej edycji po obu stronach tor działa —
0.2 m bez przerw, także na lotach, których strojenie nie widziało.

**Nie mówi nic o:**
- mapie sprzed roku–trzech z tej samej pory roku (edycje 2021-05-09,
  2022-05-18 i 2024-04-27 istnieją, piksel 5 cm);
- terenie o wyraźnej strukturze bez koron drzew;
- terenie jednolitym — łata C to lotnisko, którego dane publiczne są
  zgrubione do bloków rzędu metrów we wszystkich edycjach;
- metodach uczonych.

## §4. Błędy projektu CC

- **Reguła pary.** „Największy odstęp czasu" bez górnej granicy i bez
  warunku pory roku dała przypadek najtrudniejszy i nieoperacyjny.
- **Łaty na ślepo.** Zakaz podglądu przed wyborem dał dwie łaty
  z koron drzew i jedną ocenzurowaną. Wybór po obejrzeniu obrazu, ale
  przed jakimkolwiek dopasowaniem, nie obciążałby wyniku.
- **Brak budżetu obliczeń.** Dopasowanie do całej mapy przy 22
  procesach dało 10 s na klatkę; pierwszy bieg oceny przepadł przy
  restarcie komputera.

Wykonawca trzymał się litery; odchylenia 1–10 raportu przyjęte. Zapis
cząstkowy po restarcie był właściwą decyzją — dzięki niemu Ś3 da się
rozstrzygnąć.

## §5. Rozliczenie predykcji reconu

- P-ORTO-R1 (0.90) ✓ — edycje ≤ 10 cm z różnych lat istnieją.
- P-ORTO-R2 (0.75) ✓ warunkowo — kontrola: p50 0.03–0.07 m, max
  0.18 m, ale na 3 z 7 lotów oceny.
- P-ORTO-R3 (0.50) ✗ — łata A: 2.70 m.
- P-ORTO-R4 (0.25) ✗ literą — łata C: 59.9 m; w treści bez wartości,
  bo dane są zgrubione.
- P-ORTO-R5 (0.65) ✓ — przed odrzucaniem błędy do 370 m.
- P-ORTO-R6 (0.55) ✓ — przerwa 61.7 s.
- P-ORTO-R7 (0.80) ✓ rachunkiem z przypiętych masek (kamera misji
  ~bit 1, kamera przepływu ~bit 2, kamera w dół bez maski);
  niesprawdzona lotem.

5 z 7 przy sumie szans 4.40.

## §6. KSIĘGA (append-only przy commicie [CO-ORTO-1])

```
## ORTO — zamknięcie reconu (ANEKS_ORTO-1, 16.11.2026)
- Recon ORTO-S0 CLOSED, śmierć Ś3 literą: na parze edycji
  2012-04-28 → 2025-08-12 żaden kandydat na żadnej łacie nie mieści
  się w 1.37 m i przerwach 2.15 s. Bieg oceny przerwany decyzją Olgi
  przy 42/78 zadań; kryterium jest maksimum po lotach, więc
  rozstrzygają je loty policzone (A: 2.70 m i przerwa 71 s; B: 25.5 m;
  C: 59.9 m). 0 bootów.
- Kontrola (ta sama edycja): cechy p50 0.03–0.07 m, max 0.18 m, bez
  przerw, na lotach oceny A i B.
- Predykcje 5/7 przy sumie szans 4.40 (✗ R3, ✗ literą R4).
- ✗ projektowe CC: reguła pary bez górnej granicy odstępu i bez pory
  roku; łaty wybierane bez podglądu (dwie z koron drzew, jedna
  ocenzurowana); brak budżetu obliczeń.
- Lekcje: reguła doboru danych ma granicę z obu stron; wybór po
  obejrzeniu, ale przed pomiarem, nie jest podglądaniem wyniku; każdy
  bieg przy biurku ma limit czasu i zapis cząstkowy.
- CC własnym kodem z zapisów lotów: mapa z klatek sprzed cięcia
  pokrywa co najmniej połowę kadru w 99–100% klatek po cięciu
  (geometria NAD3) i w 97% (NAD2); EKF przed cięciem: pozycja p50
  0.21 m, max 0.42 m, kurs p50 2.9°, p95 4.8°, max 15.2°.
```

## §7. KIERUNKI_PO_PLANIE (append-only przy commicie [CO-ORTO-1])

```
## Dopisek stanu katalogu — 16.11.2026 (CO-ORTO-1, ANEKS_ORTO-1)
- **ORTO, recon — CLOSED przy biurku (Ś3).** Cudza mapa z edycji
  sprzed 13 lat i z innej pory roku: poza kontraktem na wszystkich
  łatach. Ta sama edycja po obu stronach: 0.2 m bez przerw.
- **Następna pozycja wątku: TEACH — mapa z własnego lotu.** Dron
  buduje mapę z klatek kamery w dół, dopóki ma GNSS, i po cięciu
  dopasowuje do niej bieżący kadr. Recon przy biurku otwiera
  przekazanie PROMPT_TEACH_S0.
- Pozycja nieotwarta: wiek cudzej mapy (drabina edycji 2021, 2022,
  2024). Otwarcie tylko decyzją Olgi.
```
