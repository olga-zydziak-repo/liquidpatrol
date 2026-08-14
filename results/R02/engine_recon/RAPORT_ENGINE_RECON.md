# RAPORT_ENGINE_RECON — dlaczego powietrzny sensor „nie renderował" intruza

Data: 2026-08-11. Reżim: diagnostyka (NIE budowa — SR-E1). Habitat: Gazebo Sim **8.14.0** / ogre2 /
WSL2 **mesa-D3D12**. Headless WYMUSZONY i weryfikowany per bieg (SR-E4). Artefakty:
`results/R02/engine_recon/<dyskryminator>/<run>/` (frame.npy, frame.png 1:1, result.json, world_as_run.sdf,
topics.txt, gz.log). Guard RAPORTUJE, nie orzeka.

## AKTUALIZACJA (E1/E2, PROMPT_R02C_CONFIRM, 2026-08-11) — konfundacja static-vs-flight DOMKNIĘTA

D0.5 był podwójnie konfundowany (GUI on→off ORAZ lot→statyka). E1 domyka to jednozmiennie.

**E1 — KONFIRMATOR jednozmienny (lot + headless, tylko GUI off vs §6):** dron W LOCIE (zawis ~8.5 m,
pitch 0.2°/roll 0.1°), intruz dead-ahead z realnej pozy gz → **RENDER_PASS** (dark_px 32; kontrola centrowana
`flight_headless_centered` dark_px 54; potwierdzenie WZROKOWE `frame.png`: mesh x500 w centrum + własne ramię).
Headless zweryfikowany (GUI_PROCS=brak, gz `-s`). **Hipoteza silnikowa OBALONA JEDNOZMIENNIE — §6 FAIL to GUI,
nie lot, nie silnik.** Artefakty: `E1_confirm/{flight_headless,flight_headless_clean,flight_headless_centered}/`.

**E2 — test mechanizmu pod obciążeniem CPU (`yes` oversubskrypcja, lot+headless):**
| N yes | RTF baseline→stress | time jumps | dron | render |
|---|---|---|---|---|
| 32 | 0.985→**0.9996** | **0** | trzyma (z=8.25) | **PASS** dark_px 43 (wzrokowo mesh+ramię) |
| 48 | ~1.0 | 0 | — | głodzi EKF → arm denied (poza lotem) |
| 96 | 0.990→**0.9999** | **0** | **traci wysokość** (z→0.39, EKF głodzony) | placement artefakt |

**HIPOTEZA UNIFIKUJĄCA (kontencja→time-jump→nieaktualna poza renderu→znikanie) — OBALONA dla kontencji CPU.**
Kontencja CPU (do 96×, load>100) **NIE zrzuca RTF gz poniżej 1.0 i NIE tworzy time-jumpów** — render sensora
utrzymuje real-time i renderuje poprawnie pod obciążeniem (E2@32 PASS wzrokowo). To, co kontencja CPU łamie, to
**EKF PX4** (arm denied @48, utrata wysokości @96) — TEN SAM objaw co R0.3a, ale strona LOTU/estymatora, NIE render.
→ **PASS mimo kontencji ⇒ przyczyna oryginalnego FAIL NIE jest domknięta mechanizmem CPU-lockstep.** GUI jest
USTALONĄ ZMIENNĄ RÓŻNICUJĄCĄ (E1 jednozmiennie), ale wewnętrzny mechanizm (prawdopodobnie kontencja renderu
GPU — GUI konkuruje o GPU z renderem sensora) **NIE jest zademonstrowany**. Nie zaokrąglam „GUI winne" do mechanizmu.

**OTWARTA POZYCJA:** mechanizm renderowego FAIL pozostaje niedomknięty (kontencja GPU-side, nieodtwarzalna
headless — GUI nie wstaje bez DISPLAY; CPU-stress jej nie replikuje). **Nota dla dema (zaostrzona):** monitor RTF
+ `time jump` jest KONIECZNY, ale NIE WYSTARCZAJĄCY — kontencja CPU głodzi EKF przy RTF=1.0 i 0 time-jumpów;
warunek ważności biegu percepcyjnego musi obejmować też zdrowie EKF (gyro-bias/velocity-stable), nie tylko RTF.

## WYNIK PIERWOTNY: D0.5 → PASS ⇒ **STOP (SR-E3)**. (E1 potwierdza jednozmiennie.)

D0/D1/D2/D3/D4 **NIEWYKONANE** (SR-E3; klasa przyczyny ustalona: NIE silnik).

### D0.5 — headless re-run pary naziemna/powietrzna (ten sam cel, ten sam intruz)

Instrument: świat SDF z JEDNĄ kamerą (izolacja), intruz **dead-ahead** (centrum kadru → projekcja odporna
na znaki konwencji), `dark_px` w oknie centralnym (mesh ciemny < 160 na tle nieba/gruntu ~200). Intruz =
mesh `x500_base/NXP-HGD-CF.dae` (jak §3f/C1), ~0.6 m, dystans 7 m. gz **server-only** (`gz sim -s`) = headless
z definicji (weryfikacja: zero procesów GUI). Kopie as-run zapisane (prowieniencja §6).

| bieg | kamera | wysokość | HEADLESS | GUI proc | verdict | dark_px | center_min |
|---|---|---|---|---|---|---|---|
| `ground_low_control` | standalone (unattached) | z=0.5 m | 1 (zweryf.) | brak | **RENDER_PASS_visible** | 42 | 49 |
| `aerial_high_drone` | x500_mono_cam (attached-high) | z=9.0 m | 1 (zweryf.) | brak | **RENDER_PASS_visible** | 34 | 39 |
| `aerial_high_drone_GUIon` | x500_mono_cam (attached-high) | z=9.0 m | 0 (próba GUI) | **nie wstał**¹ | RENDER_PASS_visible | 34 | 39 |

**Powietrzny sensor NA WYSOKOŚCI 9 m RENDERUJE intruza 0.6 m @ 7 m — headless.** Potwierdzenie WZROKOWE:
`aerial_high_drone/frame.png` pokazuje wyraźny ciemny mesh x500 w centrum, na tle horyzontu (nie artefakt).
Kamera naziemna renderuje tak samo (kontrola, jak §3f). **Prerejestrowana predykcja była FAIL — WYNIK PASS
jest falsyfikacją**, dokładnie po to test był zaprojektowany.

¹ `aerial_high_drone_GUIon`: próba włączenia GUI (`gz sim -r`) z powłoki bash — **proces GUI nie wystartował**
(brak DISPLAY; w R0.3a GUI wstawał, bo PX4 uruchamiał go przez WSLg). Bieg efektywnie headless → nieporównywalny
jako kontrola GUI (oznaczony `GUI_DIAGNOSTIC`). Kontencji GUI **nie udało się odtworzyć** w tej sesji.

## Interpretacja — hipoteza mechanizmu (frustum-culling) OBALONA

Prompt stawiał kandydata: „dywergencja frustum-cullingu od pozy renderu" — mały obcy model @ 7–13 m wypada,
`ground_plane` i śmigła przechodzą. **Gdyby to była prawda, statyczny headless na tej samej pozie 9 m też by
zawiódł. Nie zawiódł.** Silnik renderuje TĘ geometrię z TEJ pozy. Hipoteza silnikowa (culling / LOD /
scene-management dla podniesionego sensora) — **FALSYFIKOWANA**.

Oryginalny FAIL z §3f/§6 (`dark_px=0`, kamera powietrzna) zachodził w warunkach **lot + GUI-on** (`gz sim -g`
>180% CPU — ten sam konfundator, który w R0.3a głodził lockstep → time-jump → reset EKF → arming denied).
Usunięcie GUI (headless) przywraca render. **Symptom to artefakt KONTENCJI / threat-to-validity (komponent
wizualizacji głodzi potok renderu sensora), NIE defekt silnika.** To ta sama klasa co znalezisko GUI z R0.3a
(§VI/3 RAPORT_R03A) — teraz widać, że GUI kaził DWA substraty: warstwę-0 (arming/EKF) ORAZ render kamery.

### Granica dowodu (uczciwie) — konfundacja static-vs-flight

Bieg powietrzny wykonałem **statycznie** (x500_mono_cam zapozowany na 9 m), nie w locie. To usuwa względem
oryginału DWA warunki: (GUI→off) ORAZ (lot→statyka). Czysto jedno-zmienna wersja D0.5 to **lot powietrzny +
headless** (flip tylko GUI). Nie wykonana, bo: (a) SR-E3 — pierwszy PASS = STOP; (b) render z tej pozy jest
i tak decydujący dla pytania „czy to bug silnika" (nie jest). Rezydualne pytanie „GUI-kontencja vs
lot-lockstep-kontencja" NIE zmienia rutowania — obie prowadzą do habitatu/uprzęży, nie upstream.

## Zawężona klasa przyczyny

**KONTENCJA substratu renderu (GUI i/lub lockstep lotu), NIE bug renderera gz.** Silnik ogre2/mesa-D3D12 na
WSL2 renderuje mały mesh z podniesionego sensora headless poprawnie (gz 8.14.0, zweryfikowane wzrokowo).

## Rekomendacja rutowania (z kosztem)

| opcja | werdykt | koszt |
|---|---|---|
| **Fix habitatu/uprzęży = headless** | **REKOMENDOWANE — już zrobione** | ≈0. `run_stack.sh` honoruje `HEADLESS` (`4845a92`). Percepcja jedzie headless. |
| Zgłoszenie upstream (gz) | **NIE uzasadnione** | — nie ma przenośnego bugu cullingu do zgłoszenia; silnik renderuje poprawnie. D2 (llvmpipe) NIEpotrzebny — przesłanka „silnik nie renderuje" jest fałszywa. |
| Obejście sensorem (D4 rgbd) | **NIE potrzebne** | — |

**Pakietu issue-ready NIE przygotowuję** — nic do wysłania upstream (silnik sprawny). Zgodnie z promptem i tak
nic nie idzie upstream bez decyzji Olgi; tutaj rekomendacja jest: **nie zgłaszać**.

## Konfirmatory zalecane (przeprojektowane po zmianie rutowania — do decyzji Olgi)

1. **Lot powietrzny + headless, przechwyt renderu** (predykcja: PASS) — czysto jedno-zmienny flip względem
   oryginału (GUI→off, lot zachowany). Domyka konfundację static-vs-flight. Koszt: średni (stack headless +
   hover na 9 m + capture; reużywa r02 IMG_TOPIC/scene_sanity).
2. **Prawdziwy GUI-on z DISPLAY (WSLg), statyczny** (predykcja: FAIL) — bezpośrednio odtwarza kontencję GUI i
   domyka atrybucję. Koszt: niski, ale wymaga uruchomienia GUI z dostępnym display (jak px4-rc.gzsim).

## Prowieniencja / artefakty

- `D0.5/{ground_low_control, aerial_high_drone, aerial_high_drone_GUIon}/` — frame.npy + frame.png 1:1 +
  result.json (poza kamery, poza intruza, gz 8.14.0, backend mesa-d3d12, HEADLESS, `model_in_state`
  enumeracja: `[ground_plane, intruder, <cam>]`) + world_as_run.sdf (kopia as-run) + topics.txt + gz.log.
- Narzędzia: `gen_world.py` (generator świata), `grab.py` (gz-transport capture + dark_px + enumeracja),
  `run_recon.sh` (boot headless-weryfikowany + teardown). BEZ ROS-bridge (gz transport bezpośrednio).
- Środowisko po sesji: czyste (brak procesów gz/px4), 0 biegów w `/tmp` (SR-E4).

**STOP (SR-E3, pierwszy PASS). Push = Olga.**
