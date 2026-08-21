# RAPORT_U1R — HUD post-produkcyjny na materiale v1.0 (ANEKS_U1R §2)

Data: 2026-08-22. Zakres (PROMPT_D_U1R §1): WYŁĄCZNIE post-produkcja na ISTNIEJĄCYCH klatkach
osądzonych prób **A1 proba_1** i **A3 proba_1** (v1.0). Zero nowych biegów/pomiarów/zmian świata/spec/
sędziego. Skrypt: `acts/hud_render.py`. Wyjście: `results/demo/DEMO_B_A1_A3_HUD.mp4` (+`_h264.mp4`) OBOK
oryginału (v1.0 nietknięty), manifest `..._manifest.json` (sha klatek wejściowych + sha skryptu HUD).

## Wzór projekcji (§5)
Kamera filmowa STATYCZNA (film_cam, pozy ze świata v1.0 — FREEZE ANEKS_D2):
- A1: C=(10,−14,8), pitch=0.1783, yaw=1.9799 · A3: C=(14,−18,7), pitch=−0.1649, yaw=1.6263 · roll=0.
- hfov=1.20 rad, 1280×720 → fx=(W/2)/tan(hfov/2)=935.7, fy=fx, cx=640, cy=360.

Konwersja NED→ENU:  `[E,N,U] = [ned_E, ned_N, −ned_D]`.
Rzut (pinhole, oś kamery = +X linku, +Y=lewo, +Z=góra):
```
R = Rz(yaw)·Ry(pitch)              (roll=0)
P_cam = Rᵀ · (P_enu − C)  = (X, Y, Z)          [X>0 = przed kamerą]
u = cx − fx · (Y/X)
v = cy − fy · (Z/X)
```
Pozycja intruza = `intr_ned` z trace v2 (GT-fed) → ENU → (u,v). Range = ‖pos − intr_ned‖ (dron↔cel, 3D).

## Sanity dla materiału v1.0 (ANEKS_U1R §2c — zastępuje marker-on-silhouette)
1. **Reprojekcja drona ≤10 px:** kalibracja frame→time metodą detekcji drona (najciemniejszy piksel
   pasma nieba v∈[40,195]) ↔ rzut drona z trace, least-squares → **t0=5.0, dt=1.85, błąd 8 px** na 20
   klatkach (≤10 ✓). To „nie na oko" — walidacja geometryczna, niezależna od intruza.
2. **Spot-check OBSERVE (cień pod markerem):** `results/demo/hud_control/control_A1_observe_shadow.png`
   — marker datum toru (ring, (671,43)) połączony leader-line PIONOWO w dół z **cieniem intruza na gruncie**
   (643,477): fizyczne potwierdzenie, że certyfikowany tor pokrywa się z rzeczywistą pozycją modelu w OBSERVE.

## Rozjazd model↔tor (§2d — wielkość per faza; z trace + filmu, bez spekulacji o przyczynie)
Diagnoza (§2a przyjęta): rozjazd = **scenografia** (dekoracyjny model intruza) vs **certyfikowany tor GT**
na który działała osłona. NIE błąd dowodowy (projekcja zwalidowana).
| faza | tor GT (trace) | model (film) | rozjazd (zmierzony) |
|------|----------------|--------------|---------------------|
| OBSERVE (t≈31) | ring (7.9, osc, 11.5) | ~ring (cień pod markerem) | **~2.2 m poziomo** (w tym offset cienia po kierunku światła) — model ≈ tor |
| PATROL (t≈19) | park (7.0, 0, 3.0) | ~spawn/ring (~11.5 m alt) | **~8.5 m** (zdominowany różnicą wysokości; model nie schodzi do park) |
Wielkości zmierzone: reprojekcja markera (tor) vs rewers-projekcja cienia/sylwetki (model). Bez wnioskowania
o przyczynie ponad zmierzone (§2d). Marker-on-silhouette przeniesione do ewentualnego U2R (§2e).

## Elementy HUD (per klatka, wyłącznie z trace)
- **§2b datum toru GT** (nie box detekcji): diament + leader line + „GT track · X.X m", styl instrumentowy,
  kolor cyan-teal (odrębny od plansz). Legenda intro raz/akt: „◆ certified GT track — the shield's input;
  airframe model is decorative".
- **§2b pasek MODE**: PATROL / OBSERVE / REFUSE·NO_AUTH / REFUSE·POS_DEGRADED / LAND — ze stanu bramy w trace.
- **§2c status tokenu**: TOKEN ISSUED / CONSUMED przy zdarzeniach trace.
- **§2d plansze §1c + napisy EN**: bez zmian (współdzielone z montażem).
- Stopka prowieniencji: „ACT · film_cam (v1.0) · HUD from trace.jsonl".

## Prowieniencja / wyjście (§2f, [4])
`DEMO_B_A1_A3_HUD.mp4` (191 kl. @8fps) + `_h264.mp4` (23.9 s, przeglądarkowo-grywalny). Manifest:
script_sha256, pozy kamer, hfov, per-akt {run_dir, n_frames, frames_sha16, time_calibration}.
A1: 29 kl. drone-fit 8 px · A3: 14 kl. (brak intruza → tylko MODE/§1c). Sędzia 79b1e936 / spec / świat / v1.0 NIETKNIĘTE.

---

## ERRATUM (2026-08-22, po znalezisku E/N z U2R-2) — nota zamykająca U2R Z1
Znalezisko U2R-2: `intr_ned` ma konwencję **[E, N, −U]** (sterownik `intruder_driver.set_pose`:
`gz_x = intr_ned[0] = East`), a `hud_render._enu` zamieniało E↔N. To unieważnia część interpretacji U1R.

**STOI (poprawne):**
- **Reprojekcja drona 8 px** — używała `_enu(mav.pos)` z `mav.pos = [N,E,D]` (prawdziwy NED), konwencja
  drona poprawna. Kalibracja frame→time i walidacja geometrii kamery filmowej — WAŻNE.
- Wniosek jakościowy, że kamera filmowa v1.0 daje małą/bladą sylwetkę intruza — WAŻNY (osobny od E/N).

**SUPERSEDED (zastąpione):**
- **§2d rozjazd model↔tor (OBSERVE ~2.2 m, PATROL ~8.5 m)** — ZASTĄPIONE. Przestrzeń pomiaru była
  „światowa" (ENU), ALE „tor" liczono `_enu(intr_ned)` z BŁĘDNĄ zamianą E/N → pozycja toru była
  przekręcona (~250 px w pikselu / oś zamieniona w świecie). Liczby te NIE są czystym rozjazdem model↔tor.
  Rzeczywisty rozjazd (slaving, single-source) = sub-0.5 m — potwierdzony w U2R-2 (box NA sylwetce).
- **§2c spot-check „cień pod markerem"** — ZASTĄPIONE: marker był w przekręconej pozycji (u zamienione),
  więc „cień pionowo pod markerem" potwierdzał złą lokalizację; nie jest dowodem geometrycznym.
- **Atrybucja rozjazdu ~250 px do „bladości/divergence"** — BŁĘDNA; właściwa przyczyna = BUG konwencji E/N.

**Materiał v1.0-HUD (`DEMO_B_A1_A3_HUD.mp4` + artefakt HUD) — SUPERSEDED** przez v3.1
(`DEMO_B_A1_A3_v3_1.mp4`, box-on-silhouette z naprawioną konwencją). Zostaje w repo jako historyczny.
