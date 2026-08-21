# PREREG — ANEKS_D8 §6 bieg korekcyjny (bieg3) — commit PRZED biegiem (§6a)

**Dźwignia:** §5b centrowanie pionowe (wysokość dwell drona = stała runnera `PROBE_ALT`).

**Wartość commitowana:** `PROBE_ALT = 10.75` m.

**Wyprowadzenie (interpolacja 2-punktowa, cy = centralność pionowa boxu, pre-lock w kopercie):**
- proba_1 @ alt 10.0 → cy ≈ 0.28
- bieg2   @ alt 11.5 → cy ≈ 0.72 (mediana 8 klatek pre-lock)
- nachylenie = (0.72 − 0.28) / (11.5 − 10.0) = 0.2933 /m (monotoniczne)
- cel cy = 0.50 → alt = 10.0 + (0.50 − 0.28)/0.2933 = **10.75 m**

**Reszta konfiguracji:** bajt-w-bajt jak bieg2 (ρ=1.0, v=2.5, yaw-na-cel, intruz ring [7.86,0,11.5]
świat-stały, osc ±1.5, det_hz 2.0, teleport 16.7 Hz, DEMO_MTI=1, FILM=0). Spec/progi/tracker/
sędzia `79b1e936` NIETKNIĘTE (SR-N1).

**Bramka §5c (BEZ ZMIAN):** PASS ⟺ ENTRY in-window ∧ mti_ok k=3 ∧ central-ok |cy−0.5|≤0.12
w ≥80% klatek pre-lock w kopercie. Raport marginesu cy med/p90. (Okno pre-lock ~8 klatek —
statystycznie kruche, próg świadomie NIERUSZANY po danych, §6b.)

**Terminalność (§6c):** trzecia i OSTATNIA iteracja dźwigni. PASS ⇒ T2. FAIL ⇒ zero dalszych
biegów; wybór Olgi §5c (i) GT-fed A1+A3 albo (ii) pivot mti_flight.
