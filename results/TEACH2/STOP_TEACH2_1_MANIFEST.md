# STOP-TEACH2-1-MANIFEST — próba na sucho: sprawdziany manifestu wahadła niezdane dosłownie, 0 bootów

LiquidPatrol · wykonawca · 17.11.2026 · PROMPT_TEACH2_S1 (sha256 f7f23592),
PRE_TEACH2 (sha256 9341e912, „ratyfikuję PRE_TEACH2”). Commity:
- [CO-TEACH2-1] `1d2763fe`;
- [L-BUDOWA] `182cdc8c`.

**STOP przed bootem, zgodnie z §1: „Niepowodzenie próby ⇒ STOP bez
bootu”. Decyzja Olgi: STOP do CC. Booty 0/3.**

Nie przeszły dwa z trzech sprawdzianów manifestu wahadła (epizod
c10_s01). Przekroczenia są rzędu dziesiątek mikrometrów. Części 2–5
próby są zielone.

## §0 bramka

Bramka przeszła:
- origin = 7c466e53;
- sumy PRE i promptu zgodne;
- `teach_certs_selfcheck` 24/24;
- sumy zgodne ze STOP-TEACH-3: tabela 7a56ba1b, `tor.json`, świat S
  (38f1f4ac), tekstura S (13ac9a79), model (656ccc9b; zainstalowany =
  źródło), `nadir_obs.py` db96a4a7, `teach_map.py` 4eefedda;
- kod lotu, osłona i narzędzia TEACH bez zmian od 5ad2555e;
- `systemd-timesyncd` nieaktywny.

## Część 1 — manifest wahadła

Generator: `results/TEACH2/tools/teach2_manifest.py`. Importuje
`wahadlo` z `nad2_s4_manifest.py`, który pozostał nietknięty, i ustawia
`EP_DUR_S_L` = 1000 s w swoim procesie. Wyjście:
`results/TEACH2/scenario_manifest_teach2L.json`, sha256 d0841872…858c,
120 epizodów, episode_id = indeks.

| sprawdzian (c10_s01) | wynik | próg | stan |
|---|---|---|---|
| pierwsze 200 s równe v2 odcinek w odcinek | 16 odcinków równych, różnica pozycji 0.0 m | równe | ✓ |
| tor ciągły, krok na 0.1 s | **0.100017 m** (t = 289.0 i 689.0 s) | ≤ 0.1 m | ✗ |
| promień intruza | **11.000052 m** (t = 289.1 s) | ≤ 11.0 m | ✗ |
| ostatni odcinek do | 1000.0 s | ≥ 1000 s | ✓ |

**Skąd przekroczenia** (`position_at` co 0.1 s):
- **Krok.** Prędkość c10 to 1.0 m/s, więc idealny krok wynosi dokładnie
  0.1 m. Nogi wstecz startują w punkcie końca odcinka liczonym bez
  zaokrągleń (opis generatora NAD2), a v2 zapisuje x0/y0 odcinków
  z dokładnością 1e-4 m. Na nawrocie przy 110.9 s v2 (w nogach wstecz
  289 s i 689 s) daje to skok 17 µm.
- **Promień.** Sam v2 w 0–200 s ma 11.000035 m (t = 110.9 s, jeden
  punkt próbki). W wahadle wynosi 11.000052 m w tym samym punkcie
  nawrotu. CC podał 11.0 m po zaokrągleniu, a R2 reconu podał 11.000 m
  z dokładnością do trzech miejsc.
- W NAD2 S4 analogiczny test miał tolerancję v·0.1 + 1e-6. Pozycja 1
  tamtego generatora odpadła na 0.1000206 m.

## Części 2–5 — PASS

- **(2) plan i strażnik:**
  - `teach2_run --sucho`: env (tryb 1/1/0, `TEACH_ETAP` s3, łata S,
    cień 0, `NAD3_MANIFEST` z sumą, `NAD2_T_CONT_S` 600.5,
    `NAD2_WALL_MAX_CUT_S` 1000), argumenty `10 200`,
    `NAD2_ULG_LIMIT_MB` 10, niezmiennik manifestu prawdziwy;
  - kopia boota `teach2_boot.sh`: `bash -n` OK, różnica wobec
    `teach_boot.sh` wyłącznie w 3 wierszach ścieżki wyników (plus
    nagłówek);
  - strażnik: bez profilu FastDDS rc 5; z profilem i złą sumą
    manifestu rc 5 „manifest S4 sha”, stos nie ruszył.
- **(3) regresja `s3/p02_S_c10_a`** przez `teach2_lot` z T_CONT 110:
  0 różnic wobec `sedzia_s3.json` na wszystkich porównywanych polach
  (ważność, litera, B1–B4, D1, e′, τ, okno misji, r_max, błąd poprawki,
  przerwy, oś czasu, georef, czasy, kurs KF). Max e′/U′ z ticków sędzi
  wynosi 0.2104, tyle co analizator. Plik poprawek ma 596 wierszy,
  georeferencja 555 wiązań.
- **(4) sprawdzian lotu** `teach_s3_spr` bez zmian: 100% (3248 ticków
  osłony, 596 poprawek, georef 5e-7°).
- **(5) reguły §4:**
  - funkcje 8/8;
  - decyzje 6/6, w tym czwarty boot ⇒ STOP-TEACH2-1-BUDZET;
  - pełny sędzia na kopii p02 z wstrzykniętą odmową:
    - τ* 1.54 s po fladze z klatką fazy mapy 0.8 s trwającą w chwili
      flagi ⇒ powtórka;
    - to samo bez wolnej klatki ⇒ L-B;
    - odmowa 100 s po cięciu ⇒ L-B, kontynuacja do odmowy 100.02 s.

## Do rozstrzygnięcia przez CC

Czy sprawdziany manifestu mają tolerancję na zaokrąglenie v2 (np.
1e-4 m na kroku i promieniu)? Jeśli nie, generator wymaga innej
konstrukcji nóg wstecz. To byłaby zmiana narzędzia, nie kodu lotu.
Manifest dziś odtwarza v2 bit w bit w pierwszych 200 s.

## Odchylenia od promptu (każde osobno)

1. **Kopia boota** `results/TEACH2/tools/teach2_boot.sh`: `teach_boot.sh`
   nie przyjmuje katalogu wyników parametrem. Strażnik `TEACH_ETAP`
   ∈ {s2, s3} pozostał bez zmian, więc kolejka podaje `s3` i meta lotu
   będzie miała „etap” = s3.
2. **D-L** liczona przez nadpisanie stałej `T_CONT` modułu
   `teach_analyze` w procesie sędziego (600 s; w regresji 110 s). Plik
   analizatora jest nietknięty.
3. **„Klatka fazy mapy trwająca w chwili flagi”** to przedział w czasie
   sim [sim wiersza, + czas producenta]. Wiersz nf nie niesie chwili
   startu przetwarzania, więc to przybliżenie przy tempie ~0.95.
4. **Pamięć producenta** mierzy nowy próbnik w kolejce (VmRSS/VmHWM
   procesu `harness/nadir_obs.py` co 1 s, CLOCK_MONOTONIC). Harness
   jej nie zapisuje.
5. **Odmowa „w 300. sekundzie”** sprawdzona jako odmowa 100 s po
   cięciu, bo lot bramki ma 110 s kontynuacji. W scenariuszach (5)
   sprawdzian lotu został podmieniony na zgodny, bo dane zmieniono
   celowo.
6. **Klatki zgubione w fazie mapy i w lokalizacji** liczone z luk ciągu
   5 Hz wierszy nf. Całość pochodzi z `summary n_drop`.

`systemd-timesyncd` jest nadal zatrzymany. Po sesji:
`sudo systemctl start systemd-timesyncd`.
