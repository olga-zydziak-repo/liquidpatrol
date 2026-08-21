# PREREG — ANEKS_D8 §7 bieg rozstrzygający (bieg4, WEAVE) — commit PRZED biegiem

**Dźwignia INNEJ KLASY (§7):** usunięcie mechanizmu przechyłu (nie strojenie w jego obrębie).
Weave translacyjny PROSTOPADŁY do linii celu zamiast orbity.

**Parametry (a priori, commitowane przed biegiem):**
- `PROBE_MODE = weave`
- `PROBE_WEAVE_A = 1.2` m (amplituda nogi ±1.2, §7b)
- `PROBE_ORBIT_V = 2.5` m/s (prędkość nogi, zachowana z REGATE)
- okres pełnego cyklu = 4·A/v = 4·1.2/2.5 = **1.92 s** (constant-speed trójkąt, ostre nawroty)
- oś weave ⊥ LOS, zamrożona przy 1. bearing (proste nogi, brak dryfu osi)
- yaw = bearing na cel (centrowanie azymutu cx)

**ALT a priori z GEOMETRII ELEWACJI (§7b — NIE z cy(alt) biegów 2-3, skażonych przechyłem):**
- Kamera mono_cam: `horizontal_fov=1.74 rad`, forward = body **+X**, level-forward boresight
  (PRE_MTI.md:50, PRE_R02C.md:17) → oś optyczna POZIOMA.
- Cel na osi optycznej ⟺ elewacja θ = atan((z_intr − z_drone)/R_h) = 0 ⟺ **z_drone = z_intr**.
- Intruz ring alt = 11.5 m ENU (spec A1, NIETKNIĘTY). ⟹ **PROBE_ALT = 11.5 m**.
- θ=0 ⇒ cy = 0.5 NIEZALEŻNIE od FOV (rectilinear: cy = 0.5 − 0.5·tanθ/tan(hfov_v/2)).

**Zasięg:** ~stały z prostopadłości (dron E∈[−1.2,1.2] N=0, intruz N≈7.86 E∈[−1.5,1.5] →
range 7.86–8.31 m ∈ [7,9]).

**Reszta:** byte-jak-bieg2/3 (det_hz 2.0, teleport 16.7 Hz, DEMO_MTI=1, FILM=0). Percepcja/progi/
spec intruza/sędzia `79b1e936` NIETKNIĘTE (SR-N1).

**SYGNATURA FALSYFIKOWALNA (§7c, a priori, NIEZALEŻNA od bramki):** wariancja cy pre-lock ZAPADA SIĘ
pod weave (`cy_std < 0.10` vs orbita `cy_std ~0.19`); plateau w nogach, spike'i tylko na nawrotach.
Brak zapadu ⇒ dominanta przechyłu OBALONA (raportować bez względu na §5c).

**BRAMKA §5c (BEZ ZMIAN, §7d):** PASS ⟺ ENTRY in-window ∧ mti_ok k=3 ∧ central-ok |cy−0.5|≤0.12
w ≥80% klatek pre-lock w kopercie.

**ROUTING TERMINALNY (§7e/§7f):** OSTATNI bieg percepcyjny DEMO-B. PASS ⇒ pivot ZBĘDNY → T2
(weave+yaw+ALT stałe runnera) → T2b → próby → RAPORT §FINAL → B6. FAIL ⇒ AUTOMATYCZNIE GT-fed
A1+A3 (§2b), pivot ZDJĘTY (proste nogi = profil mti_flight; ich porażka falsyfikuje przesłankę pivotu).
