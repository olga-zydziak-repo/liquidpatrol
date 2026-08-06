# RECON P2 (ETAP R) — rdzeń estymatora stanu celu pod nieregularną obserwacją — 2026-08-06

Tor P2: offline pomiar rdzenia estymatora na publicznym datasecie (katalog `p2/`). Jeden rdzeń → dwa tory: figura na publicznym wideo + komponent kanału celu w R0.2. Recon = odczyt + pomiar nieinwazyjny.

## R1 — dataset (rodzina Anti-UAV)

Estymator uczy się na **sekwencjach boxów** (cx,cy,w,h,age), NIE na obrazach → potrzebne są **anotacje** (małe JSON/txt), nie klatki. Figura (tor 1) potrzebuje wideo → licencja istotna.

| Kryterium | **Wariant B — oryginał Anti-UAV** (ZhaoJ9014) | **Wariant A — Anti-UAV410** (HwangBo94) |
|---|---|---|
| Modalność | RGB + IR (pary) | IR (thermal) |
| Sekwencje / split | **318** (train 160 / val 67 / test 91) | 410 (test/train/val, rozmiary niepodane w README) |
| fps | **25** | niepodane w README (rodzina Anti-UAV = 25 fps) |
| Boxy / gęstość | 585,900 boxów ≈ **~1.0 box/klatkę** (per-klatka) | >438K boxów (per-klatka) |
| Śr. długość | span >23000 s → **avg 72.3 s** (~1808 kl) | niepodana w README |
| Flaga istnienia | **`exist` 1/0 + `get_rect`=[x1,y1,x2,y2]** (jasno udokumentowana; v_t=0 = absent) | atrybuty per-klatka (w tym `Out-of-View`) w `IR_label.json`, ale **„not complete"** |
| Atrybuty | exist + OV + inne | 10 atrybutów (Thermal Crossover, Out-of-View, Scale/Fast/Occlusion/Clutter/Tiny…Normal Size) — **niekompletne** |
| **Licencja** | **MIT** (figura w publikacji ✓) | **nieustalona** w README (toolkit os.; warunki datasetu do weryfikacji) |
| Dostępność | repo + link do danych (challenge CVPR) | Google Drive + Baidu (kod `a410`) |

**REKOMENDACJA: wariant B (oryginał Anti-UAV).** Kryterium „jakość flag (naturalne dziury) + gęstość boxów": B ma **jasno udokumentowaną flagę `exist` 1/0** (czyste naturalne dziury), gęstość per-klatka, dłuższe sekwencje, **znane 25 fps**, oraz **licencję MIT decydującą dla figury (tor 1)**. Wariant A ma więcej sekwencji i IR-only, ale **niekompletne atrybuty** (ryzyko jakości flagi out-of-view) i **nieustaloną licencję** → **fallback** (użyć, jeśli potrzeba więcej sekwencji / IR-only, po weryfikacji kompletności flag i licencji w budowie).

**CAVEAT do weryfikacji w budowie (krok 0):** baza Anti-UAV 2021 miała anotację **coarse co 25 klatek** dla większości + 30 par fine (per-klatka). Liczba 585,900 boxów ≈ liczbie klatek sugeruje per-klatkę w wersji **challenge (CVPR)** — **użyć anotacji challenge (per-klatka)**, nie coarse bazy. Potwierdzić gęstość wybranego splitu z etykiet.

## R2 — statystyki pod protokół

- **fps = 25** (B). Przeliczniki horyzontów {0.5, 1, 2} s → **{13, 25, 50} klatek** (0.5 s = 12.5 → 13, round-up; 1 s = 25; 2 s = 50).
- Gęstość ≈ 1.0 box/klatkę (per-klatka) — czysty gęsty sygnał GT do maskowania (protokół wyroczni).
- Śr. długość **72.3 s** (~1808 kl); przy tej średniej **zdecydowana większość sekwencji ≥ 30 s** (750 kl).
- **DO POLICZENIA Z ETYKIET (krok 0 budowy — etykiety NIE są w repo git, przychodzą z pobraniem):** dokładny rozkład długości, **licznik sekwencji ≥ 30 s**, oraz **rate naturalnych dziur** (frakcja klatek exist=0, rozkład długości dziur — „duch G2"). Recon dostarcza przeliczniki i estymaty; dokładne per-sekwencja liczby wymagają anotacji.

## R3 — budżet obliczeń

- GPU: RTX 5070 Ti Laptop, 12 GB, sterownik 577.13. **torch NIE zainstalowany** (tylko numpy) → zależność budowy.
- Rdzeń ~30k parametrów, wejście 5-dim, model sekwencyjny (GRU/CfC/Mamba/latent-ODE). Dane: train 160 seq × ~1808 kl ≈ **289k timestepów/epokę**.
- Szacunek (analityczny, konserwatywny 50k timestep/s dla małego modelu na GPU): **~5.8 s/epokę**; 150 epok ≈ **~15 min/run** (realnie prawdopodobnie 3–8 min — model mikro). Precyzyjny benchmark = szybki krok budowy po instalacji torch.
- Ramiona analityczne (ZOH-age, Kalman CV, IMM) — **bez treningu**. Ramiona uczone: ~4–5 (GRU+Δt, CfC, Mamba-no-time, Mamba+Δt, opc. latent-ODE).
- **Zwymiarowanie seedów (wejście do PRE):** przy ~15 min/run worst-case, budżet ~2 sesji ⇒ **≤ ~30–40 runów treningu**. Stąd propozycja: 5 ramion uczonych × ~5 seedów treningu = 25 runów (≈ 2–6 h); seedy masek i siatka (p,L) w ewaluacji (tanie, bez re-treningu rdzenia).

## Źródła
- Anti-UAV410: https://github.com/HwangBo94/Anti-UAV410 · TPAMI 2023 (10.1109/TPAMI.2023.3335338)
- Anti-UAV (oryginał, MIT): https://github.com/ZhaoJ9014/Anti-UAV · arXiv 2101.08466
- Anti-UAV600 (CC BY-NC-SA): arXiv 2306.15767
- Anti-UAV-RGBT specs: https://www.emergentmind.com/topics/anti-uav-rgbt-dataset
