# RAPORT_P2 — rdzeń estymatora stanu celu pod nieregularną obserwacją (offline)

Data: 2026-08-06. Poprzedniki: `PRE_P2.md` (ratyfikowany + aneksy A1–A4), `p2/recon_P2.md`, commit zamrażający `bdd4f1f` (krok 0, A2). Bieg bramki: `p2/frozen/gate_results.json` (wall 113 min).

## WERDYKT TEZY §7: **NEGATYWNY / NULL** (pełnoprawny wynik)

Żadne ramię uczone **nie przeszło preconditionu** (bicie ZOH-age na filtracji) → wszystkie **FAIL_EARLY** (5/5 seedów). Teza „najlepsze uczone bije Kalman/IMM na predykcji o > pooled_std" **nie mogła zostać potwierdzona** — brak kwalifikujących ramion uczonych. Niezależnie: **strojony Kalman/IMM (mocny baseline A3) przegrywają z ZOH-age** na predykcji w dziury. **Offline proxy nie wykazuje zysku z rdzeni uczonych; najsilniejszym estymatorem jest ZOH-age.** Arbitrem pozostaje bramka w pętli (lekcja 3d).

---

## 1. Co postawione (krok 0, zamrożone `bdd4f1f`)

- **Dane:** Anti-UAV300 (oryginał, licencja MIT), **modalność IR** (A1). Pobrane samodzielnie (opcja 2, paczka 6.04 GB z Google Drive; wypakowano tylko `infrared.json` — 14 MB, 318 seq; wideo usunięte). Prowieniencja: sha256 każdego pliku + zip + URL (`p2/frozen/{provenance,deleted_videos}.json`).
- **Split predefiniowany po sekwencjach:** train 160 / val 67 / **test 91 (zamrożony)**. fps 25. Box `[x,y,w,h]` znorm. do IR 640×512. T_min=30 s (84 test kwalifikujących).
- **Protokół wyroczni:** gęste GT → szum σ (frakcja boxa) → maski Gilbert-Elliott (Bernoulli p + burst L) + naturalne dziury exist=0 („duch G2"). Punkt operacyjny σ=0.05, p=0.5, L=25. Seedy masek {0..4}, treningu {0..4}.

## 2. Metryki i ramiona

- **Filtracja RMSE** (chwile obserwacji, cx,cy) + **predykcja ADE/FDE** w dziury (horyzonty {13,25,50} kl = {0.5,1,2} s).
- Analityczne: ZOH-age (kotwica), **Kalman-CV**, **IMM** — A3 mocny baseline: R=σ² + Q strojone na train (wybrane q_vel=1e-9).
- Uczone (parytet ±2%, patrz §5): GRU+Δt, CfC, Mamba time-blind, Mamba+Δt, latent-ODE. Trening identyczny (batch/okna BPTT, 40 epok, jawny selektor epoki = min val FDE@25, F-3b-3).

## 3. Wyniki (test 91 seq × 5 seedów masek = 420 jednostek)

**Predykcja w dziury — ADE (mean ± std):**
| Ramię | ADE | Uwaga |
|---|---|---|
| **ZOH-age** | **0.1073 ± 0.0450** | najlepszy |
| Kalman-CV (strojony A3) | 0.1356 ± 0.0829 | gorszy od ZOH |
| IMM (strojony A3) | 0.1563 ± 0.0922 | gorszy od ZOH |

**Precondition (filtracja RMSE vs ZOH=0.0051):** wszystkie uczone FAIL_EARLY (5/5 seedów):
| Ramię | filtracja RMSE (per seed) | krotność ZOH |
|---|---|---|
| GRU+Δt | 0.038–0.044 | ~8× gorzej |
| CfC | 0.047–0.054 | ~10× |
| Mamba time-blind | 0.11–0.24 | ~20–40× |
| Mamba+Δt | 0.12–0.24 | ~20–40× |
| latent-ODE | 6.9–12.7 | **rozbieżny (bug integracji)** |

## 4. Interpretacja (uczciwie)

- **ZOH-age = podłoga szumu.** Przy obserwacji ZOH zwraca detekcję; jego filtracja RMSE = poziom szumu (σ·w ≈ 0.005). Bicie tego wymaga **odszumienia pojedynczej obserwacji**, co dla ruchomego celu jest strukturalnie ~niemożliwe (uśrednianie w czasie szkodzi przy ruchu). **Precondition „bij ZOH na filtracji" jest przy tym σ bardzo ostry** — konsekwencja zamrożonego protokołu.
- **Wynik training-NIEZALEŻNY i mocny:** strojony Kalman/IMM (nie słomiane — A3) **przegrywają z ZOH** na predykcji. Interpretacja: **dynamika boxa UAV w obrazie jest mała i erratyczna** (dron zawisa/manewruje w małej skali pikselowej) → „trzymaj ostatnią pozycję" (ZOH) bije ekstrapolację stałej prędkości (CV). To niezależne od jakości treningu.
- Offline proxy: **rdzenie uczone nie dają zysku** na tym zadaniu/danych.

## 5. Komplet ramion uczonych (parytet ±2%, budżet 30k) — ledger #2

| Ramię | Parametry | W paśmie 29400..30600 |
|---|---:|:---:|
| GRU+Δt | **30002** | ✓ |
| CfC | **30292** | ✓ |
| Mamba time-blind | **29732** | ✓ |
| Mamba+Δt | **29732** | ✓ (ten sam rdzeń S6 co time-blind, A4) |
| latent-ODE | **30350** | ✓ |

## 6. Zagrożenia dla wnioskowania (threats to validity — jawnie)

1. **latent-ODE numerycznie rozbieżny** (RMSE 7–12): niestabilna integracja Eulera (age-skalowany krok + addytywna aktualizacja obserwacją → nieograniczone z). To **błąd implementacji**, nie rzetelna ocena latent-ODE — wynik dla tego ramienia nie jest miarodajny (pozostałe 4 są).
2. **Ostrość preconditionu:** przy σ=0.05 ZOH jest ~optymalny na filtracji; precondition może być zbyt ostry (mierzy „odszumianie", którego przy jednej obserwacji nie ma). Kryterium było jednak ZAMROŻONE (A2) — nie zmieniam po fakcie.
3. **40 epok** mogło nie wystarczyć rdzeniom do nauki bliskiej-identyczności + predykcji; jednak trend (8–40× gorzej) i wynik analityczny (Kalman/IMM < ZOH) wskazują, że problem nie jest wyłącznie liczbą epok.
4. **Test zamrożony + kryteria locked (A2):** brak re-strojenia pod pozytyw — zgodnie z regułą.

## 7. Lekcja 3d (jawnie)

Werdykt offline **wybiera kandydata** rdzenia do R0.2 — tu: **brak zysku z rdzeni uczonych; kandydatem offline jest ZOH-age** (najprostszy). **Nie przesądza to pętli** — możliwa **inwersja proxy↔pętla** (rdzeń słaby na proxy predykcji-w-dziury może być użyteczny w pętli sterowania i odwrotnie; `RAPORT_3D`). **Figura na publicznym wideo raportuje TYLKO to, co zmierzono offline** (ZOH bije uczone i Kalman/IMM na predykcji-w-dziury Anti-UAV IR), NIE twierdzi o wydajności w pętli. Arbitrem finalnym jest bramka w pętli zamkniętej.

## 8. Rozbieżności (rejestr)

1. **recon↔dane (ledger #1):** recon R2 oszacował **avg 72.3 s** długości sekwencji (z „Total annotation span >23000 s / 318" — strona `emergentmind.com/topics/anti-uav-rgbt-dataset`). **Zmierzone dane Anti-UAV300:** sekwencje **≤1000 kl = ≤40 s** (test mean ~37.5 s, median 40 s). Pierwotna liczba (23000 s span) **przeszacowała** — prawdopodobnie agregat innej/większej wersji rodziny Anti-UAV lub inne liczenie. Horyzonty {13,25,50} kl i próg T_min=30 s pozostają poprawne (84 test kwalifikujących); rozbieżność bez wpływu na protokół.
2. **Dane: opcja 2 (pobranie)** zamiast opcji 1 (zrzut) — zrzut niewykonany; pobrano samodzielnie z gwardią miejsca (stall Drive na 990M → jedno wznowienie `--continue`).
3. **latent-ODE** — patrz §6 (bug numeryczny, wynik niemiarodajny dla tego ramienia).
4. **Duch G2 (walidacja pozytywna):** naturalne dziury (mediana 13, średnia 25.6 kl) **pokrywają siatkę L {13,25,50}** — syntetyczne maski realistyczne.

## 9. Konkluzja

**Wynik NEGATYWNY/NULL — i jest to wynik.** Na Anti-UAV IR, pod protokołem wyroczni (σ=0.05, maski p=0.5/L=25), **żaden rdzeń uczony (~30k) nie bije trywialnego ZOH-age na filtracji**, a **mocne, strojone filtry Kalman/IMM przegrywają z ZOH na predykcji w dziury** — dynamika boxa UAV faworyzuje „trzymaj". Offline proxy nie rekomenduje rdzenia uczonego. Zgodnie z lekcją 3d: to wybór kandydata, nie werdykt pętli; figura twierdzi tylko to, co mierzy. Push robi Olga. **STOP.**
