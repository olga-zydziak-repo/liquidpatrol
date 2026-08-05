# 3× NIEZALEŻNY boot stacku (zaostrzenie §3.1, przyjęte 2026-08-05) + A4-RTF per bieg — 2026-08-05

Zaostrzenie: §3.1 bramki („3× bez pada") wykonane jako **trzy osobne uruchomienia całego stacku** (świeży launch → hello-mission → teardown), NIE 3 misje na jednej instancji SITL (te były w sesji 1, `hello_mission_runs.md`). Każdy boot łączy §3.1 (3× bez pada) z §3.2 (render GPU podczas misji) i A4 (misja domknięta + brak przerwy telemetrii >1 s).

Stack per boot: PX4 SITL v1.16.2 (`gz_x500`) + gz Harmonic 8.14.0 (serwer `-r -s` + GUI `gz sim -g`, **D3D12**) + MicroXRCE-DDS-Agent v2.4.3. Orkiestracja: `run_boots.sh` (N=3, MODEL=gz_x500). Misja: `run_hello_mission.py` (arm → 4 wp → RTL/land → disarm, monitor przerw pozycji A4).

## Wynik: **3/3 PASS** — każdy boot niezależny, render GPU D3D12, misja domknięta, 0 padów

| Boot | gz świat | Renderer (podczas lotu) | RTF (start) | Misja | A4 max przerwa poz. | Pad spontaniczny | Wynik |
|-----:|:--------:|:------------------------|:-----------:|:-----:|:-------------------:|:----------------:|:-----:|
| #1 | up | D3D12 (NVIDIA RTX 5070 Ti) | 0.99990 | 4/4→RTL→disarm | 0.02 s (≤1 s ✓) | brak (CaptureCrash/oops=0) | **PASS** |
| #2 | up | D3D12 (NVIDIA RTX 5070 Ti) | 1.00004 | 4/4→RTL→disarm | 0.02 s (≤1 s ✓) | brak (CaptureCrash/oops=0) | **PASS** |
| #3 | up | D3D12 (NVIDIA RTX 5070 Ti) | 1.04280* | 4/4→RTL→disarm | 0.03 s (≤1 s ✓) | brak (CaptureCrash/oops=0) | **PASS** |

\* RTF #3 = pojedyncza próbka tuż po starcie świata (chwilowy pik inicjalizacji >1.0); soak (A2, 29 próbek) potwierdza ustabilizowany RTF ~0.9998. RTF niebramkujący (A4).

## Dyscyplina padów (A5)
- **§3.1 render GPU podczas każdego biegu** (nie headless) — 3× potwierdzony renderer `D3D12`, nie llvmpipe.
- **Pad spontaniczny (podczas biegu):** 0/3 — żadnego nowego `CaptureCrash`/oops w dmesg w oknie żadnej misji.
- **Teardown (intencjonalny kill po każdym boocie):** generuje znany benign artefakt (exit-144 subshell / `dxg -2`/`-512`), NIE liczony do A5 (patrz `teardown_dmesg_note.md`, zaostrzona A5 w PRE §4). Weryfikacja: CaptureCrash=0 przez wszystkie 3 cykle.
- **Werdykt A5:** 0 padów o sygnaturze pada. Zejście po drabinie NIE aktywowane. Bramka w trybie **GPU**.

## Artefakty
- `results/R0/independent_boots_raw.log` — surowy log 3 bootów (kopia `/tmp/r0_boots/boots_result.log`).
- Orkiestracja w repo: `run_boots.sh`.
