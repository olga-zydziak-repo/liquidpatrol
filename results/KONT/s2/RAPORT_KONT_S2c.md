# RAPORT_KONT_S2c — STOP-KONT2c, etykieta: TEST NIEWYKONANY; hipoteza fazy niesprawdzona, błąd mojego launchera

**D3 nie sprawdził hipotezy fazy ani w jedną, ani w drugą stronę.** Skrypt `harness/kont_run_stack_s2d.sh` padł, zanim wystartowały gz i PX4. Wg doprecyzowania CC przekazanego przez Olgę (bez numeru dokumentu; do potwierdzenia w ANEKS_KONT-2): FAIL D3 przy initial absolute time < 500 000 µs = „test niewykonany”, STOP-KONT2c z tą etykietą, **bez przejścia na restart WSL**. Czekam na dokument CC.

**Werdykt S2 według PRE §4: BRAK.** Loty ważne dalej 2/8. Zamrożenia nie było.

## 1. Co się stało

| boot | nazwa | initial absolute time | sensor_combined | sonda | wynik |
|---|---|---|---|---|---|
| 3/12 wg kolejki (nr 17) | `c11_s03_r3` (D3) | brak, `px4.log` nie powstał | brak | nieuruchomiona | STOP-KONT2c: test niewykonany |

Przyczyna, odtworzona bez bootu (0 procesów): `stack.log` kończy się na `./gz_env.sh: line 20: GZ_SIM_SYSTEM_PLUGIN_PATH: unbound variable`. Kopia stosu dziedziczy `set -uo pipefail` z `run_stack.sh`, a moja dopisana linia `. ./gz_env.sh` czyta w tym pliku niezdefiniowane zmienne. Stos zakończył się przed startem gz, bramką czasu i PX4. Launcher szedł dalej: agent wstał, a `model_in_state=0`.

## 2. Moja wada

- **Próba na sucho była nieprzenośna.** Sprawdzałam `gz_env.sh`, gz i `kont_gz_czas.py` z własnej powłoki bez `set -u`, a nie sam skrypt stosu. `bash -n` tego nie wyłapie. Zgłaszając launcher, napisałam, że pełna ścieżka s2d nie jest sprawdzona, ale taki błąd dało się wykryć bez bootu.
- **`px4.log` brak = komunikat mylący:** kolejka i `kont_s2d_boot.sh` piszą „FAZA < 500000”, choć wartości nie było, a ALARM „FAIL D3” nie niesie etykiety. Właściwą etykietą jest nagłówek tego raportu.
- **Bramka fazy czekała 5.5 min na stos, którego nie było** (12:29:25 → 12:35:03: pętla topiku i pętla fazy). Pętle reagują na śmierć launchera, a nie stosu, który padł pod nim.

## 3. Proponowana poprawka (niezaaplikowana, czeka na CC)

W `harness/kont_run_stack_s2d.sh`:

```bash
set +u; . ./gz_env.sh; set -u
```

Sprawdzone w powłoce z `set -uo pipefail`, bez `GZ_SIM_*` w środowisku: bez poprawki pada, z poprawką przechodzi i daje poprawne `PX4_GZ_WORLDS`. Tak samo `px4-rc.gzsim` czyta ten plik w `/bin/sh` bez `-u`.

Propozycja dodatkowa: przed D3 uruchomić `kont_run_stack_s2d.sh` do końca z atrapą PX4 w scratchpadzie, żeby sprawdzić resztę skryptu (gz, bramka, `px4_join.json`) bez PX4. To nie jest boot, ale proszę o zgodę, bo dotyka stanowiska.

## 4. Do rozstrzygnięcia przez CC

1. **Czy ten boot liczy się do budżetu.** Kolejka zapisała 3/12 (noga 19/45), a 1c §4 liczy przerwanie fazy do budżetu. **Rekomendacja: nie liczyć** (S2′ 2/12, noga 18/45). Stos nie wstał, a precedens to `c08_s02a` z RAPORT_KONT_S2 §6 (stos nie wstał, nie boot). To decyzja o budżecie, więc nie podejmuję jej sama.
2. **Czy poprawka z §3 i powtórka D3 w tej sesji.** Warunek „drugi boot w sesji” jest spełniony: D1 i D2 poleciały, a /dev/shm ma pozostałości.
3. **Nazwa D3:** `c11_s03_r3` zajęte (REPO-2), powtórka poleci jako `c11_s03_r4`. Kolejka wymaga też zdjęcia `kampania_d.json`, którego strażnik odmawia nadpisania, albo kopii skryptu.

## 5. Stan

- **Zegar:** próbnik 0 skoków; timesyncd po kolejce `active` (`zegar_stan_po_d.txt`).
- **Twarde STOPy:** breach 0, REFUSE 0, przeskoki 0. Lot się nie odbył.
- **Nie dotknięto:** certów, kodu osłony, PX4, parametrów EKF2, oryginałów launchera i kolejki. Push = Olga.

**Liczby nie są zamrożone** — zamraża je ANEKS_KONT-2 od CC po przeliczeniu z repo.

STOP.
