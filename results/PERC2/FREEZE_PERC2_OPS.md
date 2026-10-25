# FREEZE_PERC2_OPS — zamrożenie przyrządu ops nogi PERCEPCJA-II (init S1, STOP-PERC2-1)

CC-wykonawca · 25.10.2026 · PRE_PERC2 §2 (ratyfikowany; sha256 PRE
`24369ed95017f5256ac02947f521a9900cb289919996976590c5f5485e1d9e21`).
Zmiana któregokolwiek sha/progu poniżej po commicie S1 = nowa decyzja (ANEKS),
nie poprawka. Liga wyłącznie OPS: percepcja (det_v2 775ead15, percep_proc
38a3a765, progi MTI/admisji), sędzia, bench, world_hash.sh — NIETKNIĘTE.

## Sonda kadencji (bramka narzędziowa preflight)

| plik | sha256 (16) |
|---|---|
| `results/PERC2/tools/perc2_sonda.py` | `8df528bb2ec477c3` |

**PRÓG FROZEN (PRE_PERC2 §2.2, jednostki JAWNIE per-klatkowe):**
PASS ⇔ **dt_p50 ≤ 0.070 s/klatkę ∧ frakcja delt > 0.10 s/klatkę ≤ 5 %**
(okno ≥30 s; delta = różnica stempli sensora `t_frame` kolejnych klatek
percep_feed). Procedura bramki: FAIL ⇒ remedium ⇒ powtórka ⇒ **drugi FAIL =
boot się nie uzbraja**. Wynik sondy (liczby + werdykt) wchodzi do manifestu
bootu jako pole 1. klasy (`sondy[]`). Bramka jest NARZĘDZIOWA (przed
uzbrojeniem) — nie zmienia sędziego ani reguł ważności kampanii.

## PIN prowieniencji sensora (naprawa luki z RECON_PERC2 §R4)

| plik | sha256 (PEŁNY) |
|---|---|
| `PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf` | `3354ae1e8bcb99cec143317fce607e460b13a451bc59f1da98e50e5ddd0ee64c` |

Procedura: driver-kopie od tej nogi liczą sha256 model.sdf przy KAŻDYM boocie
(obok world_hash) PRZED startem stacka; **rozjazd = STOP bootu** (perc2_s1_boot.sh
— wzór dla driverów S2+). Zero edycji `harness/world_hash.sh` (FROZEN).

## REMEDIUM NAZWANE I ZMIERZONE (k=1 stabilnie; macierz w RAPORT_PERC2_S1)

**Mechanizm strat (zmierzony, nie z tezy):** klatka mono8 640×480 = 307 200 B;
transport FastDDS domyślny: segment SHM 512 KB (~1.6 klatki) / bufor UDP
~208 KB (<1 klatka) ⇒ losowa utrata wiadomości BEST_EFFORT per subskrybent
(rozkład delt geometryczny). Render sensora NIEWINNY (poziom gz zawsze
14.71 Hz, frac>0.10 = 0.0). GPU NIE jest przełykiem (push_frame 16–20 ms ≪ 68 ms
we wszystkich próbach S1).

**Remedium (strona: WSL, zero komend Windows, zero admina):** profil transportu
FastDDS dla MOSTU OBRAZU i PROCESU PERCEP (wyłącznie te procesy; agent XRCE/PX4
na transportach domyślnych):

| plik | sha256 (16) | treść |
|---|---|---|
| `results/PERC2/tools/perc2_fastdds_profile.xml` | `a68a450b91c2ab51` | SHM segment **16 MB** + UDPv4 bufory **4 MB**, `useBuiltinTransports=false` |

Podpięcie: env **`PERC2_FASTDDS_PROFILE=<ścieżka xml>`** → driver eksportuje
`FASTRTPS_DEFAULT_PROFILES_FILE` PO starcie stacka, PRZED startem mostu
(perc2_s1_boot.sh) i w próbach percep (perc2_trial.sh). Pomiar skuteczności:
dt_p50 = p90 = 0.068 s, frac>0.10 = 0.0000–0.0020, stabilnie 40/90/35 s
(T3/T4/T5-live), także goły subskrybent 14.71 Hz / frac 0.0.

## Narzędzia pomocnicze S1 (diagnostyka — nie bramkują)

| plik | sha256 (16) | rola |
|---|---|---|
| `results/PERC2/tools/perc2_gzhz.py` | `443e32e66bd4f285` | kadencja na poziomie gz (render-vs-most) |
| `results/PERC2/tools/perc2_roscount.py` | `f43f944f56cddb38` | goły subskrybent ROS (strata DDS bez percep) |
| `results/PERC2/tools/perc2_trial.sh` | `49554c8818998e50` | próba macierzy (percep+gz+GPU+sonda) |
| `results/PERC2/tools/perc2_s1_boot.sh` | `9ca49040a3f16b29` | driver bootu diagnostycznego (higiena+pin+stack+most) |

## Checklist hosta przed kampanią (S2+)

1. Zasilanie AC (Win32_Battery BatteryStatus=2), brak obcych procesów GPU
   (`/mnt/c/Windows/System32/nvidia-smi.exe` — sekcja Processes; akceptowalny
   wyłącznie explorer.exe).
2. `PERC2_FASTDDS_PROFILE` wskazuje profil o sha `a68a450b…` (driver weryfikuje
   plik istnieje; profil trafia WYŁĄCZNIE do mostu obrazu i percep).
3. PIN model.sdf + world_hash (driver, automatycznie; rozjazd = STOP).
4. Sonda kadencji PASS przed uzbrojeniem (próg FROZEN j.w.; dwa FAIL-e = boot
   się nie uzbraja).
5. ESKALACJA (NIEUŻYWANA w S1; wymaga admina Windows — dokładne komendy,
   wykonuje Olga w PowerShell „Uruchom jako administrator"):
   `nvidia-smi -pl 70` (powrót do default power-limit; dziś 55/70/115 W) ·
   `nvidia-smi -lgc 1500,3090` / reset `nvidia-smi -rgc`. Bezprzedmiotowe wobec
   zmierzonego mechanizmu transportowego — zostają jako diagnostyka stanu GPU.
