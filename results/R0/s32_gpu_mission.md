# §3.2 — misja z renderem GPU (NIE headless) — 2026-08-05

Stack: PX4 v1.16.2 + gz Harmonic (serwer `-s`) + klient GUI `gz sim -g` pod `env_gpu` (D3D12).

## Wynik: **PASS**
- Misja: 4/4 waypointy → RTL → DISARMED, 42.9 s, gap 0.02 s (PASS).
- Renderer PODCZAS lotu: `GL_RENDERER = D3D12 (NVIDIA RTX 5070 Ti)`, GL 4.6 (**nie llvmpipe**).
- Proces gz GUI (`/ruby`) typu **G** na GPU (`nvidia-smi`).
- **A4 RTF podczas lotu: ~0.97–1.02 (real-time, śr. ~0.99)** — raportowany, nie bramka.
- GPU util 21–24%, ~241 MiB przez cały lot.
- Sim zdrowy po locie: renderer D3D12, gz GUI + px4 żyją.

## Pomiar RTF/GPU (12 próbek w locie)
```
t1  RTF=1.00013  GPU=24 %, 241 MiB
t2  RTF=1.00078  GPU=24 %, 241 MiB
t3  RTF=0.99989  GPU=23 %, 241 MiB
t4  RTF=0.96771  GPU=21 %, 241 MiB
t5  RTF=0.99288  GPU=21 %, 241 MiB
t6  RTF=0.99567  GPU=22 %, 241 MiB
t7  RTF=0.98660  GPU=24 %, 241 MiB
t8  RTF=0.98734  GPU=21 %, 241 MiB
t9  RTF=0.99726  GPU=23 %, 241 MiB
t10 RTF=0.96860  GPU=24 %, 241 MiB
t11 RTF=0.98903  GPU=24 %, 241 MiB
t12 RTF=1.02230  GPU=24 %, 241 MiB
```

## KLUCZOWE dla dyscypliny A5: `dxg query_adapter_info -22` = szum `nvidia-smi`, NIE pad
Podczas biegu w dmesg pojawiły się `misc dxg: dxgkio_query_adapter_info: Ioctl failed: -22` — sygnatura pozornie zgodna z A5.

**Test korelacji (rygorystyczny):** przed serią `nvidia-smi` ostatni wpis dmesg = `[38567.93]`; po wykonaniu 3× `nvidia-smi` pojawiły się **nowe** `query_adapter_info -22` (`[38671.67]`, `[38671.95]`, `[38672.25]`) — jednoznaczna korelacja z zapytaniami `nvidia-smi` o adapter. Sim przez cały czas zdrowy (D3D12, GUI+px4 żyją, misja PASS).

**Wniosek:** `dxgkio_query_adapter_info: -22` jest generowany przez narzędzia odpytujące adapter (`nvidia-smi`) i jest **benign** — NIE jest padem GPU. Prawdziwy pad zabija proces (`CaptureCrash`/SIGABRT/zatrzymanie renderu), czego tu nie ma. To **zaostrzenie precyzji** sygnatury A5 (eliminuje fałszywe trafienia), wpięte do PRE §4/A5.

**Implikacja dla A2 (soak):** kryterium pada = **śmierć procesu / `CaptureCrash` / zatrzymanie renderu**, a nie bare `query_adapter_info -22`. `nvidia-smi` odpytywać rzadko, by nie zaśmiecać dmesg.
