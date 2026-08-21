# KIERUNKI_SOTA — LiquidPatrol: kierunki rozwoju ku stanowi sztuki

Data: 2026-08-22. Kontekst: DEMO-B domknięty (warstwa certyfikowana: bramkowanie autorytetu A1 +
kontenacja GPS-denied A3, kanał detekcji GT-fed; świat v3.1, box-on-silhouette). Poniżej kierunki
wyprowadzone z FAKTYCZNYCH znalezisk projektu — co jest udowodnione, co otwarte, i gdzie leży SOTA.

## Stan bazowy (co stoi)
- **Warstwa osłony** (default-deny, token per-admisja, EXPIRE/konsumpcja, REFUSE odwracalny) —
  certyfikowana, sędzia zamrożony `79b1e936`, próby A1/A3 VALID.
- **Kontenacja GPS-denied** (REFUSE POS_DEGRADED → zejście → touchdown w R_E) — proven.
- **Kontrakt wierności sim** — bramka habitatu H1 (lockstep, timejump=0) ∧ H2 (Δsim/Δwall≥0.95,
  frac<0.5=0) jako warunek, że tezy stoją w czasie symulacji.
- **Roszczenie (ANEKS_D6 §1b):** warstwa certyfikowana PRZY DANEJ detekcji; kanał = przesłanka, nie teza.

## K1 — Koperta percepcji live (najważniejszy dług; „live-MTI envelope")
Bloker całego programu: przejście od GT-fed (idealizowany detektor = przesłanka) do **detekcji live
w roszczeniu**. Zmierzone fakty: mechanizm MTI odtwarzalny (diff_max≫próg, ego-motion translacyjny
separuje cel od tła), ALE **central-admission** (struktura∧central∧mti k=3) nieosiągnięta niezawodnie
w oknie dwell; zagadka **cy≈0.68–0.72 inwariantna** względem wysokości i profilu (mount kamery /
asymetria boxu YOLO / konwencja projekcji — nierozstrzygnięte).
Poddkierunki (rosnący koszt):
1. **Pivot `mti_flight`** — port rdzenia (pełna pętla OBSERVE z ego-motion translacyjnym, kwadrat
   yaw=0) jako runner aktów; token/spec/sędzia/trace bez zmian. Mechanistycznie wskazany (orbita
   bankowała, translacja stabilizuje kadr).
2. **Rozstrzygnięcie `cy` inwariantnego** — kalibracja boresightu / lekki gimbal utrzymujący elewację
   celu na osi (zmienna lotu/hardware, nie percepcja); pomiar cy(elew) na siatce a priori.
3. **Margines detektora** — fine-tune YOLO-World pod małe/odległe cele UAV (obecnie conf ~0.1 przy 8 m),
   lub głowica detekcji świadoma skali; podniesienie separacji conf od szumu.
4. **Rezyduum derotacji przy zawisie** — MTI zostawia globalne rezyduum tła bez ego-motion; SOTA:
   uczony flow/derotacja (RAFT-lite) zamiast prostej różnicy klatek + homografia z attitude.

## K2 — Rozszerzenie roszczenia certyfikacji
Od „warstwa certyfikowana PRZY danej detekcji" do „warstwa certyfikowana Z SCHARAKTERYZOWANĄ detekcją":
związać kopertę FP/FN detektora (ε_FP=0 w locie już mierzone; ε_FN i zasięg-pokrycie do domknięcia)
jako JAWNĄ przesłankę o zmierzonych granicach, nie idealizację. To czyni roszczenie mocniejszym bez
udawania, że percepcja jest rozwiązana.

## K3 — Wierność sim-to-real
Bramka habitatu (RTF lockstep) to zalążek KONTRAKTU wierności. SOTA: (a) modele szumu realnych sensorów
(IMU/GPS/kamera) + domain randomization; (b) hardware-in-the-loop (PX4 na realnym FMU); (c) walidacja
że tezy warstwy (default-deny, containment) są niezmiennicze względem ramki zegara i szumu — rozszerzyć
H3-provenance o szum, nie tylko lockstep.

## K4 — Gwarancje formalne / runtime assurance
Sędzia zamrożony + werdykty z trace to zalążek runtime-assurance. SOTA: (a) monitor własności LTL/STL
na strumieniu trace (default-deny, per-admisja, R_E-containment) egzekwowany on-line; (b) dowód (Coq/
Lean lub kontrakty) że osłona jest bezpieczna-przez-konstrukcję dla policzalnych trybów awarii.

## K5 — Robustność wielotrybowa
GPS-denied (proven) → uogólnić: comms-denied (token nieosiągalny → default-deny utrzymany), awarie
sensorów (degradacja pozycji/attitude), wielo-awaria; ORAZ adwersarialne zachowania intruza (uniki,
roje) jako testy kontenacji i bramkowania.

## K6 — Higiena konwencji i prowieniencja (lekcja z U2R-2)
Znalezisko E/N: `intr_ned` w konwencji sterownika `[E,N,−U]` vs dron `[N,E,D]` — latentna niespójność
maskowana w bramie (dron≈origin). SOTA-inżynieria: JEDNA konwencja ramki (typowane wektory NED/ENU,
konwersje w jednym miejscu, testy własności projekcja↔odwrotność). Prowieniencja (generator światów +
hasze manifestu + sha sędziego) — utrzymać jako kręgosłup odtwarzalności każdej tezy.

## Priorytet
K1 (percepcja live) odblokowuje K2 (mocniejsze roszczenie). K3/K4 to ścieżka „certyfikacja poważna".
K5/K6 to hartowanie. Rekomendacja: **K1.1 (pivot mti_flight) + K1.2 (cy/boresight) najpierw** — to
jedyny dług blokujący przejście percepcji do roszczenia; reszta buduje na tym.
