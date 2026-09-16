NOTA — bieg INFRA-2 z 2026-08-25 (wydzielony z K1/E/p0_0) [ANEKS_REPO-1a §3]
============================================================================

CO TO ZA BIEG
-------------
Sekwencyjny bieg 3 bootów walidacyjnych ramienia E (arm=E, point=0.0, kind=empty), world=default,
model x500_mono_cam_0 (SYS_AUTOSTART=4010), uruchamiany przez wrapper empty-flight. Wszystkie trzy
booty ZAKOŃCZONE ARM-FAIL (rc=2, habitat INVALID) — maszyna nie uzbroiła się w oknie preflight.

DATA (z mtime plików, co do sekundy)
------------------------------------
boot1: 2026-08-25 16:42:14 → 16:46:24
boot2: 2026-08-25 16:51:56 → 16:56:05
boot3: 2026-08-25 17:01:40 → 17:05:49

SYGNATURY px4.log (verbatim, Preflight Fail)
--------------------------------------------
boot1: "Preflight Fail: ekf2 missing data"; "Preflight Fail: No connection to the ground control station"
boot3: "Preflight Fail: No valid data from Baro 0"; "Preflight Fail: ekf2 missing data"
boot2: "Preflight Fail: horizontal velocity unstable" (×20); "Preflight Fail: High Gyro Bias" (×17);
       "Preflight Fail: High Accelerometer Bias" (×6); "Preflight Fail: heading estimate not stable" (×2);
       "Preflight Fail: ekf2 missing data" (×1); "No connection to the ground control station" (×23)
act.log każdego: pętla "[E] arm niegotowe (preflight) retry #0..#N".

sha_harness / loadavg1 (z manifest.json / finalize.log)
-------------------------------------------------------
boot1: sha_harness c41276ffe0a7bd74a97bb35bef38bb2bc2992aa17cfba512ea447df51f8521b7 ; loadavg1 6.06
boot2: sha_harness c41276ffe0a7bd74a97bb35bef38bb2bc2992aa17cfba512ea447df51f8521b7 ; loadavg1 0.96
boot3: sha_harness c41276ffe0a7bd74a97bb35bef38bb2bc2992aa17cfba512ea447df51f8521b7 ; loadavg1 4.90

DLACZEGO LEŻY OSOBNO
--------------------
Ten bieg zapisał się do katalogów results/K1/E/p0_0/boot{1,2,3}, z których boot1 i boot3 były już
zajęte przez artefakty COMMITOWANE 2026-08-24 (INFRA-1: commit 8d780f2 „W3-shakeout PASS" dla boot1,
dfb3459 „N3-shakeout FAIL" dla boot3). Nadpisał je w DRZEWIE ROBOCZYM; nigdy nie został ani
zacommitowany, ani zrewertowany — leżał brudny ~3 tygodnie.

Najostrzejsza różnica (D2 ANEKS_REPO-1): HEAD boot3 = rc=0 + hover_window [102.532, 162.592]
(UDANY zawis 60 s) — dysk boot3 = rc=2 + [None, None] (arm-fail). boot1 różni się dodatkowo
sha_harness (HEAD 55b26742… vs ten bieg c41276ff…) — to INNA wersja harnessu, czyli inny bieg,
nie powtórka. boot2 w HEAD nie istniał (nowy katalog).

STATUS
------
Bieg NIESĘDZIOWANY, NIGDY NIE RAPORTOWANY (żaden raport nie cytuje tych katalogów po nazwie — D5).
Ramię E = booty uzbrajania/habitatu, nie loty sędziowane → werdykty K1/INFRA od niego nie zależą.
Zachowany jako artefakt środowiskowy zgodnie z ANEKS_K1-14 M1 („env-faile COMMITOWAĆ jako dowód,
kind: env-fail, run_valid=None"). Udany boot3 (rc=0) pozostaje nienaruszony w HEAD po przywróceniu
K1/E/p0_0.

Errata atrybucji: ANEKS_REPO-1 §1 błędnie przypisał ten stan sondzie nogi W (2026-09-15/16). To
NIEPRAWDA — sonda W pisała wyłącznie do results/W_RECON/boot${N} (world_wind_s6), a ten bieg to
INFRA-2 z 25.08 (world=default). Sprostowane w ANEKS_REPO-1a §1.
