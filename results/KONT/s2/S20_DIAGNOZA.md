# S2.0 — diagnoza skali przepływu (0 bootów, ulog bootB)

**Wynik:** skala niejednorodna w sensie R-3, czyli dryf nie jest błędem skali: prędkość EKF po odcięciu ma s = 1.013 (rzut na v_GT) i 1.027 (stosunek średnich), a ε(72 s) ≈ 7.1 m odpowiada wolnozmiennemu błędowi prędkości ok. 0.10 m/s; źródło nieustalone, naprawialnego w kopii modelu ani parametrze nie wskazano ⇒ **brak STOP-KONT2a, S2 leci na obecnej konfiguracji, mechanizm otwarty.**

Narzędzia: `tools/kont_s20_{scale,model,rate,robust}.py`, wyniki: `s20_scale.json`, `s20_model.json`, `s20_rate.json`, `s20_robust.json`.

| Pytanie | Pomiar | Odczyt |
|---|---|---|
| Skąd 1.136? | droga EKF z pozycji 169.8 m, z całki prędkości 153.7 m, GT 149.6 m; próbkowana 1 Hz 159.4 / 147.6 m | w dużej części **drgania pozycji**, nie prędkość: z całki 1.027 |
| Model wektorowy e(t) | sama skala: rms 3.06 m (s−1 = −0.054, zły znak); stały bias v w NED: rms 1.20 m (−0.073; −0.001 m/s); skala + bias: rms 1.15 m (s−1 = +0.032); bez modelu 3.28 m | skala nie tłumaczy, bias tak |
| Bilans | średni błąd v EKF−GT po odcięciu (−0.095; −0.027) m/s × 72 s = 7.1 m; ε(72) = 7.09 m | zamyka się; w nominale (0.007; −0.005) |
| Prędkość z przepływu w ciele, filtr | oś y (poprzeczna, tu v_GT ≈ −1.9 m/s): stosunek ≈ 1.0, mediana błędu −0.05; oś x: mediana błędu +0.23 m/s | błąd skali na osi, która niesie ruch: brak; bias na osi x |
| Dystans do przeliczenia | użyty 14.04 m, dalmierz 14.05, dist_bottom 13.96, GT 13.80 (nominał 13.97 / 13.97 / 13.90 / 13.76) | **przesunięcie 1.8 m nie wchodzi w skalę**; h_EKF 12.0 nie jest używane; różnica wobec GT 1.7 % przy tym samym znaku w nominale |
| Parametry kamery | blok flow/lidar kopii = x500_flow (diff pusty), optical_flow 2ddd3d57 bez zmian: hfov 0.733, 100×100, 50 Hz | źródła w kopii modelu brak |
| Kurs | błąd EKF−GT p50 −0.75°, zakres −2.0…+2.3° | mały |

**Otwarte, opisowo, [MECHANIZM NIEZMIERZONY]:**
- Surowa prędkość z przepływu ma duży szum: |błąd| > 2 m/s w 44 % próbek osi x i 19 % osi y, a anizotropia osi (p05–p95 ±6 m/s vs ±2.8 m/s) nie ma wyjaśnienia. Regresje po składowych surowych mają r² 0.25–0.48, a oś y przy orbicie jest bliska stałej, więc s i b z osobna są tam nieidentyfikowalne; `s20_scale.json` czytać z tym zastrzeżeniem.
- Bias osi x: mediana 0.004 w nominale i 0.164 po odcięciu w tym samym przyrządzie, więc odcięcie GNSS albo faza orbity. Zależności od tempa kursu w przedziałach nie widać w sposób jednoznaczny (`s20_robust.json`).
- `s20_rate.json` (residuum kątowe względem vehicle_angular_velocity_groundtruth) jest niekonkluzywne: ta sama szumowość, a średnie ω_z tego tematu nie zgadza się z tempem kursu z kwaternionu (0.22 rad/s). Nie opieram na nim wniosków.
- Szachownica jako źródło szumu KLT: niesprawdzalne z ulogu, klatek przepływu w locie brak.
- Granica: jeden lot, FeedB (R-4).
