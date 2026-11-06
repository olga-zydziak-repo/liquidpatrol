# ANEKS_KONT-1d — po STOP-KONT2c (test niewykonany): boot nieliczony, poprawka launchera w miejscu jako nazwany wyjątek, próba na sucho całym skryptem, powtórka D3 jako c11_s03_r4

CC · 6.11.2026 · łańcuch KONT, po STOP-KONT2c (e6a8f809 na origin).
Budżet bez zmian. Wklejany jako jedyny dokument. Sygnały bez numeru
odrzucasz.

## §1. Weryfikacja CC z repo

e6a8f809: RAPORT_KONT_S2c + katalog c11_s03_r3 bez px4.log; przyczyna
potwierdzona wykonaniem u CC: `kont_run_stack_s2d.sh:6` ma
`set -uo pipefail`, `:37` robi `. ./gz_env.sh`, a `stack.log:6` kończy na
`gz_env.sh: line 20: GZ_SIM_SYSTEM_PLUGIN_PATH: unbound variable` —
stos padł przed startem gz i PX4. Hipoteza fazy (1c §2) pozostaje
niesprawdzona, etykieta „test niewykonany" prawidłowa.

## §2. Rozstrzygnięcia 1–4 z raportu

1. **Boot nieliczony.** Stos nie wstał — ta sama klasa co c08_s02a
   (RAPORT_KONT_S2 §6). S2′ = 2/12, noga 18/45. `kampania_d.json`
   z zapisem 3/12 zostaje w repo jako dowód; korekta liczbowa następuje
   w RAPORT_KONT_S2d, bez edycji starych plików. Nowy stan kolejki
   w nowym pliku (`kampania_d2.json`).
2. **Poprawka w miejscu, nazwany wyjątek.** `harness/kont_run_stack_s2d.sh`
   i ewentualnie powiązane kopie s2d wolno poprawić edycją w miejscu:
   te pliki nie wyprodukowały żadnego lotu, więc prowieniencja niczego
   nie traci. Poprawka wykonawcy przyjęta: `set +u; . ./gz_env.sh; set -u`
   (albo równoważne doinicjowanie zmiennych przed source — wybór
   wykonawcy, jedna metoda). Diff verbatim w opisie commita. To wyjątek
   nadany tym dokumentem, nie nowa reguła: pliki, które wyprodukowały
   wyniki, nadal edycji nie podlegają.
3. **Próba na sucho: zatwierdzona, nie liczy się do budżetu.** Pełny
   `kont_run_stack_s2d.sh` od początku do końca z atrapą PX4 (stub
   zapisujący argumenty i udający proces), na żywym gz: sprawdza source,
   bramkę czasu, `px4_join.json` i kolejność startu. Artefakty do
   `results/KONT/s2/stack_dryrun/` jako dowód. Prawdziwy PX4 sprawdza
   dopiero D3. Lekcja wykonawcy (próba ręczna z powłoki bez `set -u`
   zamiast uruchomienia skryptu) — do KSIĘGI przy ANEKS_KONT-2 jako
   wada nazwana, po jego stronie, z kosztem 8 min stanowiska.
4. **Doprecyzowanie „test niewykonany" dostaje numer tym dokumentem.**
   Treść verbatim: „FAIL D3 przy initial absolute time < 500 000 µs =
   test niewykonany, STOP-KONT2c z tą etykietą, bez przejścia na restart
   WSL". Wykonawca słusznie odnotował, że przyszło bez numeru; w
   RAPORT_KONT_S2d cytować jako ANEKS_KONT-1d §2.4.

## §3. Powtórka D3 i dalszy tor

- **D3 = c11_s03_r4**, po próbie na sucho PASS. Warunek „drugi boot
  w sesji" pozostaje spełniony (sesja ma za sobą booty); bez restartu
  WSL i bez sprzątania SHM, jak przy r3. Kryteria PASS/FAIL D3,
  próg ≥ 1000 próbek sensor_combined, STOP po dwóch przerwaniach fazy
  z rzędu — wszystko jak ustalone (1c §3 + decyzje wykonawcy przyjęte
  przez CC 6.11).
- Po D3 PASS: kolejka 1c §4 **plus c02_s01 na końcu** (korekta rachunku
  CC: pozycji §4 było 7, nie 8 — ✗ rachunkowe CC do KSIĘGI przy
  ANEKS_KONT-2). Razem 8 ważnych.
- Po D3 FAIL z fazą ≥ 0.5 s: hipoteza fazy obalona, STOP-KONT2d,
  dokument CC przed jakimkolwiek obejściem.
- Raport etapu: `results/KONT/s2/RAPORT_KONT_S2d.md` (nowy).
  Zamrożenie wyłącznie `kont_s2_freeze_g.py` przy n ≥ 8; liczby
  zamraża ANEKS_KONT-2.

## §4. CO

Aneks verbatim do korzenia jako `ANEKS_KONT-1d.md`, byte-check sha256
z wiadomości CC, pierwszy commit:
`KONT [ANEKS-1d]: boot r3 nieliczony, poprawka s2d w miejscu (wyjątek
nazwany), dry-run stosu, D3 = c11_s03_r4`. Potem poprawka + dry-run
(commit z diffem), potem D3 i kolejka. Push = Olga.
