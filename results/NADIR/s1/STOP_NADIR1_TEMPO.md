# STOP-NADIR1-TEMPO — S1 NADIR zatrzymany na bramce tempa w pierwszym boocie epizodowym (2/4 bootów)

Wykonawca · 9.11.2026 · łańcuch NADIR, PROMPT_NADIR_S1. Etap pasywny, nic nie wpływało na lot. Sygnały bez numeru
odrzucam.

## Raport płaski

- **Bramka tempa przerwała boot b2 przed uzbrojeniem:** dsim/dwall z settle 0.8536 < 0.93 (`b2_c08/kont_tempo.json`,
  okno 59.9 s, n = 722).
  - Porównanie: KONT S4 w trybie wydajnym miał 0.97–0.98 (np. `results/KONT/s4/nom_b3_r2/kont_tempo.json` 0.9807).
  - **Po literze PROMPT §3 to warunek śmierci S1 („tempo < 0.93”), więc STOP.**
- **Przyczyna niezmierzona.** Dwie konkurencyjne hipotezy:
  - (a) drugi render, czyli kamera nadir 640×480 przy 15 Hz plus detekcja;
  - (b) stanowisko: boot o 02:24, a o 02:29 maszyna się wyłączyła (`last -x`: shutdown 02:29, reboot 08:47).
    Poprzednie spowolnienie stanowiska (KONT 4e) dał tryb zasilania Windows.
  - Jeden pomiar nie rozdziela tych hipotez.
- **Boot b1 (statyczny, sam gz) — R1 PASS i pomiary wstępne:**
  - **R1 identyczność:** szum renderu K = 0 w 10 pozach. Klatki imagera na świecie ze znacznikami różnią się
    **wyłącznie w masce rzutu płyt**: 0 pikseli poza maską w 10/10 pozach.
  - Model-wariant `x500_nadir_flow` daje klatki imagera i przepływu bitowo jak `x500_mono_cam_flow` (10/10).
  - Kamera przepływu nie widzi znaczników (10/10, maska ~bit 2).
  - **R3 statycznie** (poza prawdziwa, błąd czysto detekcji): |p_fix − p| 0.02–0.37 m, 27 detekcji, boki 8.9–83 px.
  - **R6 wstępnie — kadłub w kadrze:** kamera w początku `base_link` (litera PRE §2.2) widzi nogi, silniki i czujnik
    przepływu x500. Maska kadłuba zajmuje 11.4% kadru i **16.9% stożka centralnego** (górne oszacowanie,
    `b1/maska_kadluba.json`).
    - W pozach statycznych 17 znaczników przewidzianych w stożku nie wykryto: 10 za kadłubem, 7 „inne” (krawędź nogi,
      skrzynki świata w widoku skośnym).
  - **7 z 37 węzłów siatki leży pod bryłami świata** (`manifest_znaczniki.json`, `kolizje_z_brylami`: id 1, 4, 7, 14,
    24, 27, 31 — 6 skrzynek `tex_*` i budynek `bldg_6`). Siatka jest FROZEN, nie przesuwałam jej.
- **R2–R5 w locie: brak danych.** Boot b2 nie poleciał.
- **Budżet S1: 2/4** (b1 statyczny, b2 przerwany bramką — przerwanie liczy się jak w KONT). Rezerwa: b3 + b4.
  Noga NADIR: 2/≤30.
- Breach 0, REFUSE 0 (brak lotów).

## Fakty bootu b2 (`b2_c08`, epizody 20 c08_s02 i 44 c08_s04, nominalne)

- Zegar przed bootem: 0 skoków (`zegar_przed_b2_c08.jsonl`); timesyncd zatrzymany; sieroty 0; /dev/shm sprzątnięte.
- PIN mono_cam OK (3354ae1e), profil FastDDS a68a450b, sonda percepcji PASS 14.71 Hz.
- `px4 initial absolute time` 7 628 000 µs (faza OK). Model nadir zainstalowany, sha w `nadir_model_sha.txt`.
- Driver `kont_s4_flight.py` (bez zmian): „BRAMKA TEMPA — boot przerwany przed uzbrojeniem”, rc 9.
- `nadir_obs` działał pasywnie: 1306 klatek, 0 zgubionych, 0 detekcji. Dron stał na ziemi: kamera ~0.2 m nad
  gruntem, znacznik pod home zasłonięty kadłubem.

## Budowa S1 (wyłącznie nowe pliki)

- `results/NADIR/tools/nadir_gen.py`: manifest (37 węzłów, DICT_4X4_50, ID = indeks, W 1.00 m), tekstury
  `worlds/nadir_markers/` (drawMarker 4.6.0 + strefa ciszy 1 komórka), świat `worlds/world_nadir_A3.sdf`
  (= world_kont_A3 + 37 modeli; assert bajtowy), model `results/NADIR/s1/zrodla/x500_nadir_flow/`, `pin_nadir.json`.
- **Decyzja wykonawcy, nazwana:** znaczniki mają `visibility_flags = 4`, a kamera przepływu w modelu-wariancie maskę
  ~bit 2. Przepływ widzi więc świat dokładnie jak w 2d, co zachowuje literę PRE §2.4 „ε_b bez zmian”. Kamera misji
  i nadir widzą znaczniki. Do akceptacji CC.
- `harness/nadir_obs.py`: rejestrator pasywny (gz-transport + ROS2 EKF, tylko log), `NADIR_FLIP=0`, OpenCV 4.6.0.
- `results/NADIR/tools/nadir_s1_boot.sh` / `nadir_s1_launch.sh`: kopie `kont_s4_boot.sh` / `kont_s4_launch.sh`
  z zamianami pilnowanymi asercją. `nadir_s1_run.py`: jeden boot w reżimie KONT.
- `nadir_frames.py` (b1), `nadir_maska.py`, `nadir_s1_analyze.py` (R2–R6, gotowe na loty).
- **Środowisko:** OpenCV z aruco już był w systemie (4.6.0, `/usr/lib/python3/dist-packages`), więc nic nie
  instalowałam. W `.b0deps` jest opencv-python 5.0.0 z nowym API — rejestrator uruchamiam bez `.b0deps`, żeby wersja
  była ta sama co w b1. Próba na sucho to złapała.
  - **Errata do RECON_NADIR §R4(ii):** zdanie „Nie ma OpenCV” było fałszywe (moja wada: zły wywołanie API 4.6
    wziąłam za brak modułu).
- Wady wykonawcy w tym etapie (żadna nie zużyła bootu):
  - runner sprawdzał wolność nazwy, a sam założył plik stdout z tą nazwą — pierwsze wywołanie b2 padło na asercji
    przed bootem; plik usunięty, restart;
  - pierwsza metoda maski kadłuba (piksele stałe w 10 pozach) dała 0.3% — cieniowanie nóg zależy od postawy;
    zastąpiona porównaniem dwóch póz o identycznej postawie.

## Do decyzji CC / Olgi

1. **Czy STOP-NADIR1-TEMPO to śmierć S1, czy stanowisko?**
   - Proponuję diagnostykę za 0 bootów lotnych: goły gz tego samego świata z rigiem `x500_nadir_flow` vs
     `x500_mono_cam_flow`, A/B naprzemiennie, RTF z `rtf_sampler` po 120 s (wzór B0 z KONT).
   - Wcześniej Olga sprawdza tryb zasilania Windows (wydajny) — maszyna przechodziła restart.
   - Jeśli A/B pokaże spadek tylko z nadirem: śmierć S1 po literze, chyba że CC dopuści obniżenie kosztu renderu
     (np. nadir 10 Hz albo 320×240) aneksem. Jeśli obie wersje są wolne: stanowisko, b3 po remedium.
2. **Kadłub w kadrze (16.9% stożka):** montaż w początku `base_link` to litera PRE. Mierzę dalej w locie (R6);
   ewentualna zmiana montażu (pod płozami) tylko aneksem.
3. **7 węzłów pod bryłami:** zostawione zgodnie z FROZEN; wpływ na pokrycie zmierzy R2/R6.

## Diff-stat i porcelain

(w wiadomości końcowej)

Sygnał: **STOP-NADIR1-TEMPO**. Push = Olga.
