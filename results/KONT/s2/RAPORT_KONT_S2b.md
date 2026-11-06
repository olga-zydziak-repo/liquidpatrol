# RAPORT_KONT_S2b — STOP-KONT2b: D1 PASS, D2 FAIL; kandydat 1 obalony; awaria leży w PX4, nie w DDS

**Werdykt prereg (ANEKS_KONT-1b §3): FAIL D2 ⇒ kandydat 1 (zalegające segmenty FastDDS SHM) obalony, STOP-KONT2b.** Bez trzeciej próby, bez łatania. Czekam na dokument CC.

**Znalezisko przy biurku, 0 bootów (§2):** w każdym z 14 bootów FAIL EKF2 w ogóle nie publikuje. `sensor_combined` urywa się po 4–6 próbkach, `vehicle_attitude` i `vehicle_local_position` mają 0 próbek, a PX4 zgłasza `Preflight Fail: ekf2 missing data`. Percepcja nie dostawała stanu własnego, bo PX4 go nie wytwarzał. Mechanizm samego urwania `sensor_combined`: [MECHANIZM NIEZMIERZONY].

**Werdykt S2 według PRE §4: BRAK.** Loty ważne 2/8, T*, R_nom, ε_b i Δ_D5 nie istnieją. Zamrożenia nie było.

## 1. Booty S2′

| boot | nazwa | rola | /dev/shm przed | uzbrojony | n_img_cb | n_frames | wynik |
|---|---|---|---|---|---|---|---|
| 1/12 (15) | `c11_s02_r3` (ep. 23) | D1, bez sprzątania | 0 plików `fastrtps` | tak, sonda PASS 15.62 Hz | 3862 | 3862 | **lot ważny, 2/8** |
| 2/12 (16) | `c02_s01_r3` (ep. 2) | D2, po sprzątaniu | 14 → 0, nic ich nie trzymało | nie, sonda ZA_MALO_DANYCH | 566 | **0** | **FAIL** |

Lot ważny `c11_s02_r3`, liczby niezamrożone:

| ε(0⁺) p95 nominału | ε 10 s | ε 20 s | ε 30 s | ε 60 s | ε 70 s | ε max | Δ max | r_GT max | xy_valid | przeskoki |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.016 m | 2.01 m | 0.83 m | 0.83 m | 1.03 m | 1.57 m | 2.16 m | 0.95 m | 25.13 m | całe okno 72 s | 0 |

Ten sam lot: V2′ 0.952, track przed odcięciem 1.000 (mediana błędu 0.32 m), opóźnienie flagi 0.016 s, nav 14 do przyziemienia, z_off −0.06 m, kadencja w locie 15.62 Hz, zejście z końca okna, breach 0, REFUSE 0, nominał w powietrzu 60.6 s. Tym lotem R-5 (≥ 60 s nominału) jest spełniony.

Drugi lot wzmacnia obraz z §5 aneksu (ε ~1–2 m, nie 7 m), ale n = 2 to nadal opis, nie wynik.

## 2. Co się psuje

**Zmierzone,** ze wszystkich ulogów z 6.11 w rootfs PX4 (`s2b_ulogi_rootfs.txt`, nazwy w UTC):

| grupa | ulogów | sensor_combined | vehicle_attitude | vehicle_local_position | estimator_status | vehicle_imu | `ekf2 missing data` |
|---|---|---|---|---|---|---|---|
| boot uzbrojony (S1 `bootB`, `c08_s02a_r2`, `c11_s02_r3`) | 3 | 59481–62209 | 59132–61996 | 29740–31083 | 23795–24869 | 476–498 | 0 |
| FAIL | 14 | **4–6** | **0** | **0** | **0** | 90–93 | 1 w każdym |

Rootfs trzyma ulogi wszystkich 14 bootów FAIL, więc **obraz i komunikat występują w 14/14 FAIL**, a w 0/3 uzbrojonych. Komunikatu nie ma też w `px4.log` lotów porównawczych (WK3 p1_b1, p1_b2, p2_b1; SKAN2 bB_c1011, bA_c08; KONT S1 bootB).

Wnioski z tych liczb:

- `vehicle_imu` żyje przez cały boot (~2 Hz w ulogu), a `sensor_combined` staje po ~0.05 s od startu. Przerwa leży między `vehicle_imu` a wyjściem `sensor_combined` lub w logowaniu tego tematu, a EKF2 milczy.
- Wątek DDS z raportu S2 §2 był objawem. Writery XRCE powstawały, ale nie miały czego nadawać. Most i obraz działały, stąd n_img_cb ~570 przy n_frames 0 (`feed_vision.py:156`).
- `ekf_watchdog`: D2 ma `bias_max=None`, D1 `0.00017`, zgodnie z brakiem estymatora.

**Sprawdzone i bez związku:**

- **Sprzątanie SHM:** D2 padł na pustym stanie, z tym samym n_frames 0, n_img_cb 566 i sim_last 40.75 s.
- **Sieroty:** przed D1 i D2 żadnej.
- **`EKF2_GPS_CTRL` w bson:** wariant RESET ma i PASS (`c08_s02a_r2`), i FAIL (`c11_s02`, `c02_s01_r3`). Wariant „nieobecny” ma i PASS (`c11_s02_r3`), i FAIL (12 bootów). Parametry EKF2 w ulogach D1 i D2 są równe na sprawdzonym podzbiorze: GPS_CTRL 7, EN 1, HGT_REF 0, OF_CTRL 1, RNG_CTRL 1, SENS_IMU_MODE 1.
- **Kolejność agent / most w DDS:** D1 i D2 mają te same odstępy od startu agenta w granicach 0.3 s (sesja 9.07/9.11 s, most 13.31/13.05 s, pierwszy reader 15.13/15.22 s). Chwili startu percepcji nie logujemy, ale przy tym znalezisku nie ma ona znaczenia, bo EKF2 milczy niezależnie od niej.

**Niezmierzone [MECHANIZM NIEZMIERZONY]:** dlaczego `sensor_combined` staje. Fakty do ręki CC, bez wniosków:

- **Wzorzec sesji:** pierwszy boot po restarcie WSL PASS 2/2 w S2+S2′, każdy następny FAIL 14/14.
- **Inne nogi:** WK3 p1_b1/p1_b2 oraz SKAN2 bB_c1011/bA_c08 latały boot po boocie w jednej sesji (ten sam start systemd w `proc_inventory_pre.txt`) na modelu `x500_mono_cam`. Sam „drugi boot w sesji” nie wystarcza do awarii. KONT ma `x500_mono_cam_flow`, AUTOSTART 4010 i `world_kont_A3`.
- **Kolejność w `px4.log`:** w FAIL `lockstep_scheduler` startuje z 24000 us, a `ERROR [vehicle_imu] … timestamp error` jest przed synchronizacją. Sama para nie rozdziela grup: `c08_s02a_r2` (PASS) ma imuERR 2 przy 16000 us, WK3 p1_b2 (PASS) ma 24000 us przy imuERR 0.
- **Co przeżywa między bootami po sprzątaniu:** page cache, stan GPU, `lttng-ust-wait-8-1000`, rootfs PX4 (bson, dataman, logi). Żadnego z nich nie badałam.

**Kandydat 2 (wyścig startu)** w wersji z aneksu, czyli faza mostu i percepcji względem agenta, nie ma poparcia w tych danych. Wyścig wewnątrz startu PX4 (gz ↔ sensory ↔ EKF2) pasuje do obrazu, ale nie jest zmierzony.

Obserwacja poboczna, bez mapowania portów na procesy: `/dev/shm` po D1 ma porty 7001/7411/7413/7415, po D2 7000/7411/7413, jak po S2. Różnica nie wynika z zalegających plików, bo D2 startował od zera. W świetle §2 nie traktuję jej jako przyczyny.

## 3. Strażniki i kolejka

- **Zadziałały:** STOP po pierwszym FAIL diagnostycznym (§3 aneksu), budżet zjedzony 2/12 zamiast kolejnych 11. Alarm w `kampania.log` dotarł na bieżąco.
- **Sieroty po STOP:** `rtf_sampler` (4432) i `infra2_ekf_watchdog` (4433) z bootu D2, TERM po PID, obie zniknęły. Ścieżka „pod podłogą” dalej je zostawia, strażnik kolejki je łapie.
- **`kont_s2_freeze_g.py`:** przy n = 1 odmowa, kod 2, brak `s2_freeze.json`. Po lotach nieuruchamiany, n = 2.

## 4. Wady i odstępstwa po mojej stronie

- **`sonda=None` w `kampania.log`:** `sonda_stan` czyta klucz `verdict`, a pole nazywa się `werdykt`. Tylko wiersz logu; decyzje idą po `uzbrojony`. Nie poprawiałam w trakcie, skrypt zostaje jak w commicie `61982d47`.
- **Litera §2.3 „nigdy `-f` po wzorcu”:** spełniona w kolejce, ale `kont_s2_boot.sh` i `harness/kont_boot_s2.sh` dalej mają `pkill -9 -f`. Zostawione celowo, bo zmiana sprzątania przed D1/D2 mieszałaby diagnozę.
- **`wsl --shutdown` przed D1:** nie mam dowodu, że wykonano właśnie to polecenie. Sprawdziłam skutek: host wstał o 11:47, `/dev/shm` bez `fastrtps`.
- **`PROMPT_KONT_S2` nie ma w repo ani w `~`.** §S2.2–§S2.3 stosowałam przez PRE §4, `kont_s2_analyze.py` i układ RAPORT_KONT_S2.
- **Praca ponad literę aneksu:** odczyt ulogów i porównania z §2. Wyłącznie odczyt, 0 bootów, zero zmian w PX4.
- **Decyzje własne:** PASS D1/D2 = uzbrojenie po sondzie, nie ważność lotu; kody 4/5/6 skryptu bootu = STOP bez liczenia bootu; nazwy = pierwszy wolny katalog (REPO-2); numery bootów dalej od 15.

## 5. Rozliczenie predykcji

P-KONT-3 i P-KONT-4: nierozstrzygnięte, brak T* i R_nom. R-5: spełniony, 60.6 s, 0 przeskoków.

## 6. Budżet, zegar, stan

- **S2′: 2/12. Noga: 18/45** (S1 2 + S2 14 + S2′ 2). Rezerwa S2′ 10 bootów.
- **Zegar:** próbniki D1 i D2 0 skoków; timesyncd stop na czas kampanii, po niej `active`.
- **Twarde STOPy:** breach 0, REFUSE(POS) poza scenariuszem 0, przeskoki 0.
- **`/dev/shm`:** stan po D2 w `shm_po_STOP_KONT2b.txt`, nieczyszczony.
- **Nie dotknięto:** certów, kodu osłony, PX4, parametrów EKF2, RAPORT_KONT_S2, oryginałów kolejki i zamrożenia. Push = Olga.

## 7. Do rozstrzygnięcia przez CC

1. **Przyjęcie zmiany miejsca awarii:** z DDS na PX4, czyli `sensor_combined` / EKF2 przy starcie.
2. **Następna diagnostyka.** Propozycja, sama jej nie zaczynam: najpierw przy biurku kod `sensors` i `lockstep` PX4 wobec kolejności startu, różnica startu KONT vs WK3/SKAN2 (model flow, AUTOSTART 4010, świat). Dopiero potem ewentualny boot z bramką „`vehicle_local_position` płynie” zaraz po starcie stosu, która przerywa boot jeszcze przed sondą.
3. **Czy kolejne loty mogą iść przez restart WSL przed każdym bootem.** Zaobserwowane 2/2, ale bez mechanizmu i z ręczną akcją Olgi, więc to obejście, nie naprawa. 6 lotów ważnych brakuje, budżet S2′ to pozwala.
4. **Lot `c11_s02_r3` jako ważny 2/8.** Rekomendacja: tak, spełnia wszystkie warunki.

**Liczby tego raportu nie są zamrożone** — zamraża je ANEKS_KONT-2 od CC po przeliczeniu z repo.

STOP.
