# STOP-NAD3-2-MANIFEST — manifest NAD3 łamie niezmiennik „indeks listy = episode_id”, na którym stoi ruch intruza; po N1 epizody c05 i c10 poleciały z niewłaściwym intruzem; kolejka zatrzymana przed N2

15.11.2026 · wykonawca · PROMPT_NAD3_S2 (sha256 5aeba32f, „sha ok” Olgi). **Booty: 1 z 4** (S2), noga NADIR-III 1 z ≤ 22.

**Werdykt.** STOP z wadą przyrządu, nie śmierć. Bezpieczeństwo nie było naruszone: N1 przeszedł B1–B5 we wszystkich czterech epizodach. Bramka geometrii przeszła formalnie (r_max ≤ 19.5 m w 4/4), ale dla c05 i c10 pomiar jest nieważny jako pomiar geometrii NAD3:
- ruch intruza `harness/intruder_motion.py:169` bierze `manifest["episodes"][episode_id]`;
- manifest NAD3 z S1 ma 6 epizodów (indeksy 0–5) z oryginalnymi `episode_id` 0, 1, 2, 3, 5, 10;
- epizod c05 (id 5) dostał tor c10 (indeks 5);
- przy c10 (id 10) proces ruchu intruza padł na `IndexError`, więc intruz stał na pozycji startowej przez cały epizod.

N2, B3 i B4 dziedziczą tę wadę: B3 i B4 to cięcie c05, czyli z torem c10. Kolejkę zatrzymałem SIGINT w przerwie między próbami bramki zdrowia N2, zanim boot ruszył. timesyncd jest wznowiony, procesów symulatora brak. **Wada jest moja** — manifest z S1 („episode_id jak w kanonie”), a próba na sucho sprawdzała mapowanie po stronie drivera, nie procesu intruza.

## Bramka §1 i budowa przed bootem

- origin ⊇ `69128dba`, sha promptu 5aeba32f („sha ok”), `nad3_certs_selfcheck` 20/20, sumy tabel P1–P3 i manifestu = strażnik boota.
- **Próba drivera na sucho PASS** (`nad3_s2_dryrun.py` ⇒ `s2/dryrun/dryrun_s2.json`, commit `e90346f0` [S2-BUDOWA]):
  - `main()` z atrapami KONT dochodzi do uzbrojenia z meta nad3 (P1, sha 806f5e90);
  - odmowy mają kody 8 (bez `NADIR_OSLONA`), 8 (litera NADIR1), 41, 42, 44, 45;
  - kod 43 nieosiągalny z env drivera — test jednostkowy z S1;
  - blok litery i degradacji wycięty dosłownie z drivera: 10/10 przypadków;
  - strażnik boota daje kod 5 na 8 złych kombinacji, JSON `NAD3_DEGRAD` z boota jest poprawny;
  - kolejka na sucho: plan [N1, N2, B3, B4];
  - epizod syntetyczny B4 i B3 PASS z negatywami wykrytymi.
- **Czego próba nie objęła:** procesu `harness.intruder_motion`. Atrapy zatrzymują driver przy uzbrojeniu, a epizod syntetyczny odtwarza zapisany lot NAD2 bez ruchu intruza.
- **Mapowanie w próbie** sprawdzało tylko stronę drivera: driver wybiera `manifest["episodes"][i]` po indeksie z `BENCH_EPISODE_IDS` (`nad3_flight.py:304-305`), więc kolejka podawała c05 = 4 i c10 = 5. Proces intruza dostaje od drivera `episode_id` z pola epizodu (5, 10) i indeksuje nim listę.

## N1 — `results/NAD3/s2/n1_nominal`

- Boot 1. Bramka zdrowia A: GO, tempo 0.903. Tempo lotu 0.9396, rc 0, breach brak.
- Litera NAD2 = osłona. `nad3_degradacja`: bez degradacji, zgodna. Tabela P1 w meta (sha 806f5e90).
- Analizator: ważny, bezpieczeństwo OK.

| epizod | okno misji [s] | r_max GT [m] | intruz (log) max [m] | intruz zadany max: okno nominału / okno cięcia [m] | track | pasmo | B1–B5 | ważny geometrycznie |
|---|---|---|---|---|---|---|---|---|
| c00_s01 | 74.02 | **18.326** | 10.0 (stoi) | 10.0 / 10.0 (okno cięcia 0–144.5 s) | 0.891 | 0.931 | 5 × OK | **tak** |
| c01_s01 | 81.70 | **18.143** | 10.0 (stoi) | 10.0 / 10.0 (0–152.2 s) | 0.896 | 0.987 | 5 × OK | **tak** |
| c05_s01 | 74.68 | 18.831 | 10.994 — **tor c10** (log z etykietą c10_s01) | (10.0 / 10.0 — tor c05 nielatany) | 0.943 | 0.946 | 5 × OK | **nie** |
| c10_s01 | 72.89 | 12.175 | brak logu — intruz stał na (−10, 0) po `IndexError` | (10.9996 / 11.0 — tor c10 nielatany w tym epizodzie) | 0.966 | 0.941 | 5 × OK | **nie** |

- Ważne epizody c00 i c01: dron sięga 8.1–8.3 m dalej niż stojący intruz na 10 m, czyli r_max 18.1–18.3 m przy bramce 19.5 m.
- c05 z torem c10 (intruz do 11 m w ruchu 1 m/s) dał r_max 18.83 m. To jedyna obserwacja ruchomego intruza w NAD3 — opisowo, nie do bramki.
- `act.log` N1: `intruder_start_gate` ustawił poprawne pozycje startowe wszystkich czterech epizodów — c05 (0, 10), c10 (−10, 0) — z manifestu po indeksie drivera. Ruch po starcie szedł z procesu intruza po `episode_id`.
- Traceback: `harness/intruder_motion.py:169` (`ep = manifest["episodes"][this_id]`) przy `episode_id` 10.

## N2 — niezaczęty

- Bramka zdrowia `n2_nominal_g1` (A): NO-GO, tempo 0.866.
- Do zamknięcia według przyrządu: Chrome i dwm na iGPU (17%), python 2.9% CPU, ChatGPT.
- Kolejka przerwana w przerwie 180 s przed próbą C. Booty zużyte: 1. Wpis `kampania_s2.json`: stop None, pozostało [N2, B3, B4] (przerwanie ręczne).

## Do decyzji CC (aneks) — drogi naprawy, bez wyboru

1. **(A) Manifest NAD3 jako pełna lista 120 epizodów** tym samym generatorem z parametrami NAD3 (10.0 / 11.0 / 8.5, trajektorie 200 s, `orbit_dir` z wersji 110 s), więc indeks = `episode_id` jak w kanonie i w manifeście bramki NAD2.
   - Kod bez zmian. Kolejka podaje id wprost (N1 0,1,5,10; N2 2,3,5,10; cięcie 5).
   - Manifest dostaje nową sumę (zmiana strażnika boota i testu S1), a testy na sucho obejmują cały manifest albo 6 używanych komórek.
2. **(B) Podzbiór 6 epizodów z `episode_id` przenumerowanym na indeks** (0–5). Kod bez zmian, ale `episode_id` w trace odbiega od kanonu (c05 = 4, c10 = 5).
3. **(C) Ruch intruza wyszukuje epizod po `episode_id`.** To zmiana pliku `harness/intruder_motion.py` (nie na liście nietkniętych PRE §5.5, ale to kod toru lotu) i wymaga regresji intruza. Manifest bez zmian.

Niezależnie od wyboru:
- **N1 c00 i c01 pozostają ważnymi pomiarami geometrii** (ten sam manifest dla komórek stojących, tor i start poprawne).
- c05 i c10 wymagają lotu.
- Danych S2 nie użyto do zmiany tabel.
- Pod (A) tor c05 i c10 w nowym manifeście jest identyczny z dzisiejszym: `nad3_manifest.py` już dziś generuje pełną listę 120 i z niej wybiera 6 komórek, więc pod (A) zmienia się tylko filtr i suma.

## Obserwacje do aneksu

- **Kod 9 drivera jest podwójny:** bramka tempa (odziedziczona z KONT, `nad3_flight.py:324`) i niezgodność degradacji (NAD3, `:603`, mój wybór w S1). Kolejka rozróżnia je przez `kont_tempo.json` i zdarzenie `nad3_degradacja`. Kodu lotu nie zmieniałem (§4).
- **Stanowisko:** pierwsza próba N2 dała NO-GO przez obciążenie iGPU przeglądarką. Przed wznowieniem warto zamknąć Chrome i aplikacje okienkowe.

## Licznik bootów

| etap | zużyte | budżet |
|---|---|---|
| S2 | 1 (N1) | 4 |
| noga NADIR-III | 1 | ≤ 22 |

Nieważnych stanowiskowo: 0 (N2 nie bootował — NO-GO bramki przed bootem nie jest bootem).

**Sygnał: STOP-NAD3-2-MANIFEST.** Push robi Olga. Kolejka nie ruszy bez aneksu CC ze wskazaną drogą naprawy manifestu albo ruchu intruza.
