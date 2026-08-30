# RAPORT_INFRA3 — rozcięcie kontroler/osłona + wrapper bootu

LiquidPatrol · pozycja 1a planu · baza `3065b8b` · wykonawca Claude Code · push=Olga.
Liczby z etykietą przyrządu (nav=EKF/mav=MAVSDK/sim=Gazebo/wall=zegar) i ścieżką pliku.

Commity: A1 `31fe970` · A1b `9b6c006` · A2.0 `f134a2a` (pushnięte) · A2 artefakty (ten commit) · B (dalej).

---

## §1. D0 — inwentarz (pełny w `results/INFRA3/D0_inventory.md`)

sha256 pinów zgodne na wejściu: shield `1c584964`, config `4c440e42`, gate `72619513` (przed A1),
k1_judge `4e0dc0af`, act_judge `79b1e936`. Bloki setpointów w `gate_run_r03.py`: init trasy (200),
init stanu (206–207), wp/dx/dy/dist/inkrement/tgt (225–230), v_ned (291).

**Macierz ścieżka × mechanizm (proza):**
- `k1/run_k1_boot.sh` (K1 S/N/E): watchdog EKF2, higiena CAL_MAG, higiena GPS, bramka obciążenia I2a,
  próbnik RTF, headless, kopia ulogu, certs_selfcheck(S), finalize, settle 90 s, b4_state. **Bez** hasha
  świata (stock `default`), **bez** spawnu intruza.
- `acts/run_act.sh` (A1/A2 DEMO-B): hash świata, spawn intruza, bridge kamery, headless, settle 150 s.
  **Bez** watchdoga/higieny mag/higieny GPS/bramki I2a/RTF/ulogu/certs/b4.
- `acts/run_A3.sh` (A3 GPS-denied): hash świata, RTF, bridge kamery, headless, settle 90 s, finalize.
  **Bez** watchdoga/higieny/I2a/spawnu/ulogu/certs/b4.

Predykcja CC potwierdzona: `acts/*` bez watchdoga/mag/I2a; `run_k1_boot.sh` bez hasha/spawnu. Luka domykana wrapperem §B.

---

## §2. A — rozcięcie kontroler/osłona

### Diff-summary gate'a (pełny verbatim: ANEKS_SHA §W12)
`r03/gate_run_r03.py` dotknięty WYŁĄCZNIE: (i) import pakietu kontrolerów; (ii) konstrukcja `ctrl`
(env `CONTROLLER` default `route`, `reset()`); (iii) wiersz `meta` +`controller`/+`controller_sha`;
(iv) blok wp/dx/dy/dist/seg_i/tgt → `ctrl.step(...)` z odczytem `seg_i`/`dist`/`wps` (triggery S4/K1);
(v) wiersz ALLOW `set_velocity_ned` z `cmd["v_ned"]`. Gałąź `is_pos`/zejście D5, `shield.step`,
denial/recovery, timeouty, `outcome`/restore — NIETKNIĘTE (SR-3, potwierdzone diffem). Pin `72619513…`→`c3ccabe0…`.
`k1_finalize.py` +2 linie (przepisanie `controller`/`controller_sha` meta→manifest, SR-2 dozwolone).

### Wynik testu równoważności A1.3 (verbatim, `tests_controller_split.py`)
```
korpus S/K1 z wierszami tick: 11 lotów
Łącznie ticków porównanych bit-w-bit: 4221  → WSZYSTKIE IDENTYCZNE (tgt, v_ned, seg_i, dist)
test syntetyczny przejścia narożnika (dist 1.01→0.99): OK
test descending=True ∧ dist<1.0 ⇒ brak inkrementu seg_i (obie impl.): OK
R0.3a v1 (bez tick): pominięte zgodnie z A1.3(ii)
pytest: 5 passed
```

### Regresja glue A1.4
`judge.json` BAJT-IDENTYCZNY (kopia `results/K1/S/p0_65/boot3`, stary gate przywrócony w drzewie → pin
się zgadza → sędzia liczy). Manifest porównywany z wyłączeniem pól pomiarowych chwili uruchomienia
(`session`: mem_free/loadavg — snapshot środowiska, D5 ANEKS_INFRA3-1); realna różnica = tylko nowe pola
`controller`/`controller_sha`. Przepisanie meta→manifest zweryfikowane na trace z wstrzykniętym meta.

### Dwa loty równoważności (A2.1, `tools/run_k1_boot_infra3.sh`, `CONTROLLER=route`, KIND=crit)
Wrapper = kopia `run_k1_boot.sh`, diff 3 linie (OUTDIR + marker read + marker write → `results/INFRA3/`;
nota §6). Referencja: `results/K1/S/p0_65/boot3` (x_exc 3.470, r_max 15.448, t_refuse 0.10, t_td 3.680,
seq LOITER→PRECLAND→OFFBOARD→DESCEND→OFFBOARD). Sędzia `4e0dc0af`. B4 pre-series: brak procesu >50% CPU.

| metryka (etykieta) | ref boot3 | **boot1** | **boot2** | próg | ok |
|---|---|---|---|---|---|
| run_valid ∧ habitat | VALID | **VALID** | **VALID** | ważny | ✅ |
| pairing dr [m] (nav) | — | 0.789 | 0.312 | ≤1.0 | ✅ |
| pairing dv [m/s] (nav) | — | 0.008 | 0.024 | ≤0.3 | ✅ |
| pairing dhead [°] (nav) | — | 6.215 | 2.885 | ≤10 | ✅ |
| pairing dz [m] (sim GT) | — | 0.481 | 0.426 | ≤0.5 | ✅ |
| breach | False | **False** | **False** | False | ✅ |
| nav_state_seq (ulog) | 5-stan | identyczna | identyczna | ==, bez AUTO_LAND | ✅ |
| t_refuse_rel_s (nav) | 0.10 | **0.10** | **0.08** | [0.05,0.15] | ✅ |
| x_exc [m] (sim GT) | 3.470 | **3.112** (\|Δ\|0.358) | **2.914** (\|Δ\|0.556) | \|Δ\|≤0.905 | ✅ |
| t_td_s (ulog) | 3.680 | **3.4** (\|Δ\|0.28) | **4.06** (\|Δ\|0.38) | \|Δ\|≤0.5 | ✅ |
| controller / _sha (meta+manifest) | — | route / `e0fcc7d2…` | route / `e0fcc7d2…` | route | ✅ |

Cytaty: `results/INFRA3/A2/S/p0_65/boot1/{judge.json,manifest.json}`, `.../boot2/{judge.json,manifest.json}`.
`controller_sha` = sha256 `r03/controllers/route_follower.py` = `e0fcc7d2…` (w meta i manifeście obu lotów).

### Werdykt A2: **PASS** (2/2 loty ważne i porównywalne spełniają WSZYSTKIE punkty A2.3).
Refaktor kontroler/osłona jest równoważny; osłona zachowuje się identycznie z natywnym blokiem setpointów.
Predykcja P2 trafiona (2 loty porównywalne w 2 bootach, t_refuse w oknie, |x_exc−3.470|≤0.905 w obu).

---

## §3. B — jeden wrapper bootu programu

[OCZEKUJE — seria B rusza po ratyfikacji STOP-2 i pushu Olgi. §B1 (harness/run_boot.sh + test) + §B2 (6 bootów).]

---

## §4. Re-baseline pinu (A2.0, commit `f134a2a`)

`k1/k1_shield_pins.py`: `r03/gate_run_r03.py` `72619513c682e76892c531ec3dae2d918da08da92017605dcba50103977cf58a`
→ `c3ccabe04b9cae8ea57cfa899b8e363451fe9a6b4dbaffc8b1b0910ad192b729` (D1). `+r03/controllers/base.py`
`7fc45cf2216d4a9eae86fa9ee714d70354fafbc64721f76bff7c0575bb9fb8f9` jako 4. pin (D2: kontrakt kontroler↔osłona).
`shield.py`/`config.py` sha256 BEZ ZMIAN. Odsyłacz: ANEKS_SHA §W12. Weryfikacja: self-check SHIELD FROZEN=True (4/4),
`tools/test_k1_shield.py` 5/5.

---

## §5. Wpięcie kontrolera dla ławki (5 zdań)

1. Napisz klasę dziedziczącą `SetpointSource` (interfejs `r03/controllers/base.py`) implementującą
   `reset()` i `step(tick, pos_ned, vel_ned, now_s, descending)`.
2. `step` zwraca dict z kluczami `tgt_ned`/`v_ned`/`yaw`/`seg_i`/`dist`/`wps`/`extra` — nazwy obowiązujące,
   bo pętla i triggery K1/S4 czytają dokładnie te klucze.
3. Zarejestruj klasę w `r03/controllers/__init__.py` (`_REGISTRY`) pod nazwą kanału i wskaż ją env
   `CONTROLLER=<nazwa>` przy uruchomieniu (default `route`).
4. Osłona (`r01.shield.PatrolShield`) widzi WYŁĄCZNIE `cmd["tgt_ned"]` (jako `tgt` do `shield.step`) i
   `cmd["v_ned"]` (gałąź ALLOW) — nie widzi wnętrza kontrolera; decyzja osłony pozostaje niezależna.
5. Do manifestu trafia `controller` (nazwa) i `controller_sha` (sha256 pliku modułu kontrolera) — tożsamość
   wtyczki jest audytowalna per boot, bez ruszania żadnego pinu (`base.py` pinowany, wtyczki nie).

---

## §6. Odchylenia i noty

- **N1 (KIND=eq→crit):** PROMPT_INFRA3 §A2.2 podał `KIND=eq`, ale zamrożony `k1_finalize` przyjmuje tylko
  `{crit,info}` (SR-2 zabrania poszerzenia). ADJUDYKACJA CC INFRA3-A2.2 (30.08): loty A2 lecą `crit`
  (referencja boot3 też crit; izolacja od K1 katalogiem `results/INFRA3/`, nie etykietą kind). Zastosowano crit.
- **N2 (wrapper diff = 3 linie, nie 2):** marker `.last_boot_end` występuje w `run_k1_boot.sh` DWUKROTNIE
  (odczyt cooldownu, zapis końca) — dla spójnego łańcucha cooldownu serii INFRA3 oba muszą wskazywać
  `results/INFRA3/.last_boot_end`; z OUTDIR daje to 3 zmienione linie. Predykcja „2 linie" rozminęła się o 1;
  obie zmiany mieszczą się w dwóch pojęciach (ścieżka wyjścia + marker). Zero innych różnic (SR-7: brak `results/K1`).
- **N3 (dz blisko progu, P4):** pairing `dz` = 0.481 (boot1) / 0.426 (boot2) przy tol 0.5 — rozrzut z_gt
  wstrzyknięcia (lekcja 0.50) jest realnym ryzykiem porównywalności, w obu lotach zmieścił się.
- **Błąd w logice setpointów:** brak (A1.1 „nota, nie fix") — nie znaleziono.
- **CONTROLLER=route:** przekazane env przy wywołaniu wrappera (wrapper bajt-czysty poza 3 liniami ścieżek);
  gate i tak konstruuje kontroler z default `route`, więc `controller_sha` pojawia się niezależnie.
