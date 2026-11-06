# ANEKS_KONT-1c — po STOP-KONT2b: dyskryminator to faza dołączenia PX4 do zegara gz, nie pliki ani parametry; jeden boot rozdzielający D3 ze zmianą kolejności startu, potem loty

CC · 6.11.2026 · łańcuch KONT, po STOP-KONT2b (b9380e33 na origin).
Budżet bez zmian (S2′ ≤ 12, użyte 2; noga 18/45). Wklejany jako jedyny
dokument. Sygnały bez numeru odrzucasz.

## §1. Weryfikacja CC z repo

- ANEKS_KONT-1b w korzeniu, sha a63b6c45 zgodne. Zakres +42593, same
  dodania plus dopisy do dwóch istniejących logów kampanii
  (`kampania.log`, `kont_s2_monitor.log`). To dopis do logu, nie edycja
  treści. Przyjęte i nazwane.
- Tabela ulogów (`s2b_ulogi_rootfs.txt`): w 14/14 FAIL sensor_combined ma
  4–6 próbek, vehicle_attitude i vehicle_local_position 0, ekf2 missing 1.
  vehicle_imu płynie w tym samym tempie co w lotach udanych (~2 Hz
  logowane: 90–93 w 45 s wobec 476–498 w 240 s). IMU żyje, a łańcuch
  stoi na sensor_combined. Przeniesienie awarii z DDS do PX4: **przyjęte**.
- **c11_s02_r3 = lot ważny 2/8.** R-5 spełnione łącznie (60.6 s).

## §2. Co CC znalazł w px4.log wszystkich 17 bootów KONT

Własnym przeglądem (`initial absolute time` lockstep, rozmiar BSON,
`vehicle_imu … timestamp error`):

- **Rozmiar BSON nie rozróżnia.** Udane: 852 B (S1 bootB, c11_s02_r3)
  i 871 B (c08_s02a_r2). Nieudane: 852 i 871. Mój kandydat z samozatruciem
  parametrami odpada jako przyczyna.
- **`timestamp error` nie rozróżnia.** Jest w udanym c08_s02a_r2 i w S1
  bootB, a nie ma go tylko w c11_s02_r3.
- **Rozróżnia faza dołączenia PX4 do zegara gz.** Udane: lockstep startuje
  z 432 000 / 16 000 / 20 000 µs. **Nieudane: 24 000 µs w 14/14.**
- Kontrola: K2 b2/b3 (model bez przepływu) też startowały z 24 000 µs
  i latały, a SKAN2 i PERC2 startują przy 0.11–1.11 s. Hipoteza robocza
  jest więc koniunkcją: **model z przepływem + PX4 dołącza przy 24 ms
  symulacji ⇒ sensor_combined staje.** Mechanizm wewnętrzny pozostaje
  niezmierzony: możliwe, że pierwsza próbka któregoś czujnika z
  timestamp_sample 0 wypada w złej fazie względem kamery przepływu
  (50 Hz = 20 ms).
- Pierwszy boot po restarcie łapie inną fazę, bo zimny dysk spowalnia
  start. To tłumaczy wzorzec 2/2 vs 14/14 bez odwoływania się do stanu
  hosta.

## §3. D3 — jeden boot rozdzielający (prereg)

Kopia launchera `harness/kont_boot_s2d.sh` (nowy plik, oryginał nietknięty)
z jedną zmianą: **PX4 startuje dopiero, gdy gz ma za sobą ≥ 0.5 s czasu
symulacji** (odczyt `/clock` albo `/world/*/stats`, wartość dołączenia
w manifeście). Reszta verbatim. Boot D3 = **drugi boot w sesji** (po
dowolnym pierwszym; najlepiej po locie c08_s04 jako pierwszym bootem
sesji po restarcie, jeśli Olga i tak restartuje WSL), scenariusz z planu
(c11_s03).

- **PASS** ⇔ `initial absolute time` ≥ 500 000 µs ∧ sensor_combined płynie
  ∧ sonda przed uzbrojeniem PASS. Wtedy zmiana launchera wchodzi do
  kolejki dla wszystkich dalszych bootów S2′ i S4 (wpis w manifeście),
  a D3 jest lotem, który liczy się do 8, jeśli spełni ważność.
- **FAIL** ⇒ hipoteza fazy obalona, STOP-KONT2c. Wtedy obejście:
  restart WSL przed każdym bootem (ręczna akcja Olgi, nowa sesja
  wykonawcy na boot), bez dalszych diagnoz bootami.
- Faza dołączenia nie wpływa na mierzone wielkości: ε liczone jest
  ≥ 100 s później, po zbieżności EKF i zdrowym oknie T_home. Wpis do
  raportu: loty 1–2 przy fazie 16/20 ms, kolejne przy ≥ 0.5 s.

## §4. Kolejka po D3 PASS

Pozostałe: c08_s04, c00_s02, c11_s04, c08_s02b (+ D3 c11_s03). Z lotami
c08_s02a_r2 i c11_s02_r3 daje to 8. Strażniki 1b bez zmian. Dodatkowo
każdy boot loguje `initial absolute time`, a wartość < 500 000 ⇒ boot
przerwany przed uzbrojeniem, liczy się do budżetu, to nie FAIL sondy.
Raport: `results/KONT/s2/RAPORT_KONT_S2c.md` (nowy). Zamrożenie wyłącznie
`kont_s2_freeze_g.py` przy n ≥ 8. Liczby zamraża ANEKS_KONT-2.

## §5. CO

Aneks verbatim do korzenia jako `ANEKS_KONT-1c.md`, byte-check sha256
z wiadomości CC, pierwszy commit:
`KONT [ANEKS-1c]: faza dołączenia PX4 jako dyskryminator, D3, launcher s2d`.
Potem launcher (commit), D3, kolejka. `pkill -f` w nowym launcherze
zastąpione PID-ami z inwentarza (1b §2.3). Push = Olga.

## §6. KSIĘGA (dopisze ANEKS_KONT-2)

✗ kalibracyjne CC: kandydat „samozatrucie parametrami w BSON” z wiadomości
do Olgi 6.11, obalony przy biurku na tych samych logach (rozmiar BSON nie
rozróżnia). ✗ kalibracyjne CC: R-3 (skala przepływu), obalone w S2.0.
