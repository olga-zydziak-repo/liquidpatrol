# ANEKS_TEACH2-1 — po STOP-TEACH2-1-MANIFEST: sprawdziany manifestu dostają tolerancję 1 mm; manifest bez zmian, lot wznowiony

LiquidPatrol · CC · 17.11.2026 · łańcuch TEACH2, po
STOP-TEACH2-1-MANIFEST (76312e46 na origin). Do ratyfikacji sygnałem
**„ratyfikuję TEACH2-1"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC (z repo, własnym kodem)

1. **Stan.** 1d2763fe, 182cdc8c i 76312e46 na origin; `PRE_TEACH2.md`
   w korzeniu z sumą 9341e912…. Budowa dodała wyłącznie pliki
   w `results/TEACH2/`. Kod lotu, osłona, driver i narzędzia TEACH,
   NAD2 i NAD3 bez zmian. Kopia boota różni się od oryginału trzema
   wierszami ścieżki wyników i nagłówkiem.
2. **Manifest wahadła** (`scenario_manifest_teach2L.json`, suma
   d0841872…), epizod c10_s01, policzony od nowa z odcinków na siatce
   0.1 s przez 1000 s:
   - pierwsze 200 s równe v2: różnica pozycji 0;
   - tor ciągły: największy krok 0.100017 m przy nominalnym 0.100 m.
     Nominał przekraczają dwa kroki, przy 289.0 i 689.0 s, o 17 µm;
   - promień intruza do 11.000052 m; sam v2 w 0–200 s ma 11.000035 m;
   - wahadło jest lustrem: |p(t) − p(400 − t)| najwyżej 0.03 mm,
     a nogi 1, 3 i 5 są identyczne;
   - ostatni odcinek kończy się w 1000.0 s.
3. **Części 2–5 próby na sucho** przyjęte z raportu: strażnik,
   regresja lotu p02 bez różnic wobec sędziego S3, sprawdzian lotu
   100%, reguły kolejki.

Liczby raportu potwierdzone. Manifest jest poprawny.

## §2. Rozliczenie

- **STOP zasadny literą, bez wady w manifeście.** Progi w prompcie
  stały dokładnie na wartości nominalnej, bez tolerancji liczbowej.
  Przekroczenia to 17 µm na kroku i 52 µm na promieniu; pochodzą
  z zaokrąglenia początków odcinków w v2 do 0.1 mm.
- **✗ CC:** próg na wielkości liczonej podany bez tolerancji,
  a promień 11.0 m wzięty z liczby zaokrąglonej. Sprawdzian miał
  łapać skoki i wyjście poza koło rzędu metrów; tolerancja 1 mm tego
  nie osłabia. Ten sam kłopot był w NAD2 S4 i nie został przeniesiony.
- **Odchylenia 1–6 raportu przyjęte**, w tym:
  - meta lotu niesie etap „s3", bo strażnik boota zna tylko s2 i s3.
    To nie jest niezgodność mety; lot identyfikują katalog
    `results/TEACH2/s1/` i księga kolejki;
  - „klatka fazy mapy trwająca w chwili flagi" liczona jako przedział
    od czasu klatki przez czas pracy producenta.

## §3. Litera (zastępuje trzy sprawdziany manifestu z PROMPT_TEACH2_S1 §1)

Dla epizodu c10_s01, na siatce 0.1 s przez 1000 s:

1. pierwsze 200 s równe v2 odcinek w odcinek — bez zmian;
2. krok najwyżej v · 0.1 s + 0.001 m, czyli 0.101 m;
3. promień intruza najwyżej 11.001 m.

Manifest zostaje ten sam (suma d0841872…). Reszta PROMPT_TEACH2_S1
i PRE_TEACH2 bez zmian. Aneks po locie nosi numer ANEKS_TEACH2-2.

## §4. Wznowienie

1. Bramka: `origin/master` zawiera `76312e46`; sha256 tego pliku
   zgodne z podanym przez Olgę; sygnał „ratyfikuję TEACH2-1" obecny.
2. Commit **[CO-TEACH2-1A]**: aneks verbatim w korzeniu (byte-check),
   blok §5 do KSIĘGI append-only.
3. Sprawdziany manifestu policzone od nowa wg §3, wynik dopisany do
   próby na sucho. Niezdane ⇒ STOP.
4. Lot L1 wg PROMPT_TEACH2_S1 §2–§5, bez zmian.

## §5. KSIĘGA (append-only przy commicie [CO-TEACH2-1A])

```
## TEACH-II — ANEKS_TEACH2-1 (17.11.2026): tolerancja sprawdzianów manifestu
- STOP-TEACH2-1-MANIFEST przed bootem, 0/3: krok 0.100017 m przy progu
  0.1 m, promień 11.000052 m przy progu 11.0 m. Przyczyna:
  zaokrąglenie początków odcinków v2 do 0.1 mm. Manifest poprawny:
  pierwsze 200 s równe v2, wahadło lustrzane do 0.03 mm (CC własnym
  kodem).
- Litera: krok ≤ v·0.1 s + 0.001 m, promień ≤ 11.001 m. Manifest bez
  zmian (sha d0841872). Budowa i reszta próby na sucho przyjęte.
- P-TEACH2-1 (0.85) ✗ — budowa zatrzymała się STOP-em, z winy progu.
- ✗ CC: próg na wielkości liczonej bez tolerancji liczbowej.
  Lekcja: sprawdzian poprawności niesie tolerancję o rzędy mniejszą
  od wady, którą ma łapać, i o rzędy większą od zaokrągleń.
```
