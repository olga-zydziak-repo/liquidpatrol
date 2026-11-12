#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_en_71.py — KOPIA democ_en.py (nietknięty) dla montażu v7.1 EN (PROMPT_DEMOC_V71). Zmiany (hunki):
  (§3) przyrząd kolizji democ_kolizje w każdym kroku, tabela paneli per krok, łączenie etapów brain-clip, agregacja do zegara
       filmu i sprawdzenie przedziałów §1 (tryb v7 = oryginalne narzędzia, wyjście kolizje_v7.json);
  (§2/§4) tryb v71 woła kopie narzędzi *_71.py; (§5) plansza: ~240 simulation runs; wyjścia clips_en71/, DEMO_C_v71_*.
--- nagłówek kopii ---
results/DEMO_C/tools/democ_en.py — angielska wersja demo v7 (decyzja Olgi 12.11.2026: „Demo musi być po angielsku” + bez
oznaczeń wewnętrznych typu „epizod c10_s01”, które widzowi nic nie mówią). NOWY plik; v1–v7 NIETKNIĘTE.

Mechanizm: każdy krok to osobny proces, który przed importem narzędzia podmienia funkcje rysujące tekst —
PIL ImageDraw.text / textlength i cv2.putText — na wersje tłumaczące napis słownikiem PL→EN (dokładne dopasowanie, potem reguły
regex dla napisów z liczbami). Tryb ścisły: napis z polskimi znakami albo słowami, którego słownik nie zna, przerywa render
(AssertionError). Potem wołany jest main() narzędzia z tymi samymi argumentami co przy v2–v7 (odtworzone z transkryptów
sesji), wyjście do clips_en/. Te same klatki, segmenty tempa i dane; zmienia się wyłącznie tekst. Karty i plansza v7 renderowane
wprost po angielsku (funkcje karta/plansza7 z democ_overlay_v7 z angielskim tekstem).
Teksty EN: napisy aktów z DEMO_C_v6_en.srt / v7_en.srt, uproszczone tam, gdzie srt niósł żargon (det_v2, EKF2_GPS_CTRL, D5,
REFUSE(POS), t_acq sędziego); HUD i etykiety tłumaczone tu. Pełna lista: słownik niżej.

Użycie: democ_en.py all            (wszystkie kroki po kolei, potem montaż)
        democ_en.py step <nazwa>   (jeden krok)
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(DC, "..", ".."))
UKLAD = os.environ.get("UKLAD", "v71")                                   # (§3) v7 = oryginały, v71 = kopie *_71
OUT = os.path.join(DC, "clips_en71", UKLAD)

TR = {
    # akty 1–3 (democ_overlay_v2 / v31 CAPTIONS)
    "AKT 1 — DRON WIDZI: cel nadlatuje czołowo; detektor det_v2 na żywej kamerze":
        "ACT 1 — THE DRONE SEES: the target flies in head-on; the detector runs on the live camera",
    "Zielona ramka = detekcja; TRACK = admisja toru percepcji (14,7 kl/s)":
        "Green box = detection; TRACK = the target is locked (14.7 frames/s)",
    "Sieć płynna (20 neuronów) prowadzi podejście i orbitę 6–10 m":
        "The liquid network (20 neurons) flies the approach and a 6–10 m orbit",
    "AKT 2 — DRON SZUKA: cel startuje ZA plecami (azymut 180°) — kamera pusta":
        "ACT 2 — THE DRONE SEARCHES: the target starts BEHIND it (180°) — the camera sees nothing",
    "Skan skokowy całym kadłubem: krok 40°, przegląd perymetru":
        "Step scan with the whole airframe: 40° steps, sweeping the perimeter",
    "Znalezienie → pościg → orbita; wszystko z jednej kamery mono 640×480":
        "Find → pursue → orbit; all from a single 640×480 mono camera",
    "AKT 3 — DRON PRZEŻYWA: orbita nominalna (widok z kamery pokładowej)":
        "ACT 3 — THE DRONE SURVIVES: normal orbit (view from the onboard camera)",
    "Wstrzykujemy awarię GPS (EKF2_GPS_CTRL=0) — pozycja zaczyna dryfować":
        "We inject a GPS failure — the position estimate starts to drift",
    "Osłona: REFUSE(POS) w ~0,1 s → bezpieczne zejście D5 do przyziemienia":
        "The shield refuses within ~0.1 s → safe descent to touchdown",
    # akt 4 (v31)
    "AKT 4 — DRON ROZPOZNAJE PRZYNĘTĘ: obiekt krąży, nigdy nie atakuje":
        "ACT 4 — THE DRONE RECOGNISES A DECOY: the object circles but never attacks",
    "Sygnatura ruchu: szybki, nie zbliża się, nie schodzi pod 5 m":
        "Motion signature: fast, not closing in, never below 5 m",
    "Etykieta WABIK po spełnieniu reguły — czas liczony jawnie":
        "DECOY label once the rule holds — the clock is shown openly",
    "AKT 4b — FLAGA SIĘ COFA: cel zaczyna jak wabik (kręci, nie zbliża się)":
        "ACT 4b — THE FLAG IS REVOKED: the target starts out like a decoy (circling, not closing in)",
    "Klasyfikator daje flagę wstępną… ale cel ZMIENIA zachowanie":
        "The classifier raises a tentative flag… but the target CHANGES its behaviour",
    "Zejście <5 m ⇒ system COFA etykietę i ściga — orbita domyka":
        "It comes within 5 m ⇒ the system REVOKES the label and pursues — the orbit closes in",
    # HUD v2/v31/v6
    "FAZA": "PHASE", "STAN": "STATE", "PRZECHYŁ": "TILT",
    "SCAN (szukam)": "SCAN (searching)",
    "DYSTANS DO CELU (GT)": "DISTANCE TO TARGET (true)",
    "DYSTANS (GT)": "DISTANCE",
    "DETEKTOR det_v2 (mono 640×480 ×2)": "DETECTOR (onboard camera 640×480)",
    "brak detekcji": "no detection",
    "panel taktyczny ↑ · kamera pokładowa →": "top-down map ↑ · onboard camera →",
    "SHIELD: REFUSE(POS) → D5": "SHIELD → safe descent",
    "TOUCHDOWN — bez naruszeń": "TOUCHDOWN — no violations",
    "WYSOKOŚĆ (GT)": "ALTITUDE (true)",
    "panel: ● dron (GT) · ∘ estymata nawigacji —": "map: ● drone (true) · ∘ navigation estimate —",
    "po denialu estymata ODPŁYWA od prawdy": "after GPS loss the estimate DRIFTS from the truth",
    "percepcja EMULOWANA w tym akcie": "perception EMULATED in this act",
    "(obraz pokładowy = podgląd, nie karmi sterowania)": "(onboard image = preview only, not used for control)",
    "ADMISJA INTRUZA — krok po kroku (liczby z feedu lotu)": "TARGET ADMISSION — step by step (numbers from this flight)",
    "3 zgodne klatki: centralność + ruch (brama admisji k=3)": "3 consistent frames: centred + moving (admission gate)",
    "JAK ROZPOZNAJE (reguła):": "HOW IT KNOWS (rule):",
    "— warunki z zapisu lotu": "— from the flight log",
    "w ruchu": "moving", "nie zbliża się": "not closing in", "nie był <5 m": "never within 5 m",
    "ODWOŁANA — cel atakuje": "REVOKED — target attacks",
    "klasyfikator diagnostyczny — etykieta wyliczona": "diagnostic classifier — label computed",
    "z zapisu lotu, nie steruje dronem": "from the flight log, does not steer the drone",
    # panel (cv2.putText — wyłącznie ASCII)
    "intruz": "intruder", "dron": "drone", "wabik": "decoy", "cel": "target",
    "panel taktyczny (GT) · siatka 5 m": "top-down map (true positions), 5 m grid",
    "panel taktyczny (GT) / siatka 5 m": "top-down map (true positions), 5 m grid",
    "REFUSE(POS)": "SHIELD REFUSE", "ENTRY": "TARGET LOCK",
    # akt 5 (v5)
    "AKT 5 — W GŁOWIE SIECI: ta sama misja co akt 2; stan 20 neuronów odtworzony replayem":
        "ACT 5 — INSIDE THE NETWORK: same mission as act 2; the state of the 20 neurons replayed from the log",
    "Skan: stan STOI. Akwizycja: stan SKACZE. Orbita: stan krąży po PIERŚCIENIU":
        "Scan: the state STAYS STILL. Acquisition: it JUMPS. Orbit: it circles a RING",
    "Pierścień stanu i strzałka «kierunek na cel» krążą RAZEM — tak sieć pamięta, gdzie jest cel":
        "The state ring and the «direction to target» arrow circle TOGETHER — this is how the network remembers the target",
    "Wykres: neuron n0 nakłada się na sin(kierunku na cel) — czytamy, CO sieć koduje (opisowe)":
        "Chart: neuron n0 follows sin(direction to target) — we read WHAT the network encodes (descriptive)",
    "W GŁOWIE SIECI — ta sieć PROWADZI lot": "INSIDE THE NETWORK (it flies)",
    "panel = replay zapisu (nie steruje)": "replay of the log (steers nothing)",
    "AKT 5 — W GŁOWIE SIECI": "ACT 5 — IN THE NETWORK",
    "KROK PO KROKU (liczby z tego lotu):": "STEP BY STEP (numbers from this flight):",
    "1. skan: sieć nie widzi celu — punkt stanu STOI": "1. scan: the network does not see the target — the state STAYS STILL",
    "3. orbita: stan krąży po PIERŚCIENIU — rytm = okrążenia celu": "3. orbit: the state circles a RING — rhythm = laps around the target",
    "faza:": "now:", "scan": "scan", "approach": "approach", "orbita": "orbit",
    "kierunek": "direction", "na cel": "to target",
    "stabilny cykl = decyzja «krążę»": "stable cycle = decision «orbit»",
    "sin(kierunku na cel) z lotu": "sin(direction to target)",
    "ŻYWA SIEĆ: 8 wejść → 20 neuronów → komenda [vn ve vd] (replay)":
        "LIVE NETWORK: 8 inputs → 20 neurons → command [vn ve vd] (replay)",
    "dowiedzione: |komenda| < 3 m/s (T1) · stan ograniczony |h|<1 (T2) — status PROVED, różnicówka 0/74 708 ticków":
        "proved: |command| < 3 m/s (T1) · bounded state |h|<1 (T2) — status PROVED, differential test 0/74 708 ticks",
    "sieć NCP-20 PROWADZIŁA ten lot; panel aktywacji odtworzony deterministycznie z zapisu (replay) — sam niczym nie steruje":
        "the 20-neuron network FLEW this mission; the activation panel is replayed deterministically from the log — it steers nothing",
    # akt 6 (v6)
    "świat z oporem aerodynamicznym skalibrowanym do fizyki (k ≈ 0.49 /s); wiatr zmienny o znanym profilu, nie turbulencja":
        "simulated air drag calibrated to physics (k ≈ 0.49 /s); varying wind with a known profile, not turbulence",
    "wiatr: profil z litery świata — 0.4–3.6 m/s, kierunek ±30°": "wind: profile from the world definition — 0.4–3.6 m/s, direction ±30°",
    "pod wiatrem: łagodne 8/8, ostre 7/8 — jedyna porażka to spóźnione rozpoznanie celu":
        "Under wind: mild profile 8/8, sharp 7/8 — the only failure was late target recognition",
    "AKT 6 — WIATR: ta sama sieć, uczona bez wiatru i bez oporu": "ACT 6 — WIND: the same network, trained with no wind and no drag",
    "porywy do 3.6 m/s, kierunek wędruje o ±30°": "Gusts up to 3.6 m/s, the direction swings by ±30°",
    "orbita trzyma: dystans 6–10 m przez całe okno": "The orbit holds: 6–10 m distance through the whole window",
    "strzałka = dokąd wieje": "arrow = where it blows",
    "przechył z zapisu lotu": "tilt from the flight log",
    "teraz": "now",
    # akt 7 (v7)
    "GPS działa — sieć krąży wokół intruza": "GPS working — the network orbits the intruder",
    "GPS ODCIĘTY (celowo, test)": "GPS CUT (deliberately, a test)",
    "pozycję daje kamera w dół: znaczniki naziemne co 10 m": "position now comes from a downward camera: ground markers every 10 m",
    "ta sama sieć: 20 neuronów, 1903 parametry — prowadzi lot dalej": "the same network: 20 neurons, 1903 parameters — keeps flying the mission",
    "osłona z dowodem pilnuje strefy": "a shield with a proof guards the zone",
    "symulacja PX4/Gazebo · pozycja bez GNSS: przepływ optyczny + kamera w dół nad znacznikami":
        "PX4/Gazebo simulation · position without GNSS: optical flow + downward camera over markers",
    "planowe zejście po 110 s": "planned descent after 110 s",
    "zapis lotu z 12.11.2026 — odtworzenie z logów, nie obraz z kamery · TEMPO ×30":
        "flight log of 12.11.2026 — replayed from logs, not camera footage · SPEED ×30",
    "600 s bez GPS: intruz śledzony 100% czasu · 0 odmów osłony · błąd pozycji bez trendu (p95 0.2 m) · surowy estymator odjechał do 20.6 m":
        "600 s without GPS: intruder tracked 100% of the time · 0 shield refusals · position error with no trend (p95 0.2 m) · raw estimator drifted up to 20.6 m",
    "● prawda (GT)": "● truth (simulator)", "◯ pozycja poprawiona": "◯ corrected position",
    "∘ surowy estymator": "∘ raw estimator", "● intruz": "● intruder",
    "□ znaczniki (37, co 10 m)": "□ markers every 10 m",
    "kamera w dół (nadir) · obrysy z zapisu": "downward camera",
    "para": "marker pair", "jeden znacznik": "single marker", "bez poprawki": "no fix",
    "zielony = przyjęty literą · czerwony = odrzucony": "green = accepted · red = rejected",
    "ODCIĘTY": "CUT", "BEZ GPS": "WITHOUT GPS", "wiek poprawki τ": "age of last fix",
    "odmowy osłony (misja)": "shield refusals (mission)", "odmowy osłony": "shield refusals",
    "błąd pozycji poprawionej": "corrected position error",
    "surowy estymator ↔ prawda": "raw estimator ↔ truth", "surowy estymator od prawdy": "raw estimator vs truth",
    "błędy wobec prawdy symulatora (GT), kanon czasu analizatora": "errors measured against simulator ground truth",
    "błędy wobec prawdy symulatora (GT)": "errors measured against simulator ground truth",
    "zużycie granicy dowodu (e/U)": "share of the proof's error bound used",
    "AKT 7 — 10 minut bez GPS": "ACT 7 — 10 minutes without GPS",
}
RULES = [
    (r"^AKT (\w+)$", r"ACT \1"),
    (r"^TEMPO ×(.+)$", r"SPEED ×\1"),
    (r"^epizod \S+ \(ujęcie aktu 2\) · zegar\s*(\S+) s$", r"same flight as act 2 · mission clock \1 s"),
    (r"^epizod \S+ · świat \S+ · zegar\s*(\S+) s$", r"mission clock \1 s"),
    (r"^epizod \S+ · zegar\s*(\S+) s$", r"mission clock \1 s"),
    (r"^conf (.+)$", r"confidence \1"),
    (r"^detektor conf (.+)$", r"detector confidence \1"),
    (r"^ramka detektora na celu — conf (.+)$", r"detector box on the target — confidence \1"),
    (r"^ADMISJA → TRACK  \(t_acq sędziego (.+) s\)$", r"ADMITTED → TRACK  (target acquired after \1 s)"),
    (r"^sieć płynna prowadzi — APPROACH (.+) s → ORBITA (.+) s$", r"the liquid network flies — APPROACH \1 s → ORBIT \2 s"),
    (r"^v_rad (.+)$", r"radial speed \1"),
    (r"^licznik: (.+) / (.+) s  →$", r"counter: \1 / \2 s  →"),
    (r"^WABIK  \(\+(.+) s\)$", r"DECOY  (+\1 s)"),
    (r"^2\. akwizycja \((.+) s\): stan SKACZE — sieć złapała cel$", r"2. acquisition (\1 s): the state JUMPS — the network has locked on"),
    (r"^4\. neuron n0 ≈ sin\(kierunku na cel\): \|r\|=(.+) na tym ujęciu$", r"4. neuron n0 ≈ sin(direction to target): |r|=\1 on this flight"),
    (r"^PRZESTRZEŃ STANU h\(t\)∈R²⁰ → PCA · 2 osie = (.+)% wariancji \(pomiar atlasu\)$",
     r"STATE SPACE h(t)∈R²⁰ → PCA · 2 axes = \1% of variance (atlas measurement)"),
    (r"^\|r\| = (.+) \(to ujęcie; atlas 0\.95\) — opisowe$", r"|r| = \1 (this flight; atlas 0.95) — descriptive"),
    (r"^kotwica tego ujęcia: p95 \|Δv_replay − Δv_log\| = (.+)·10⁻³ m/s \(max (.+)·10⁻³\)$",
     r"replay vs flight log: p95 |Δv| = \1·10⁻³ m/s (max \2·10⁻³)"),
    (r"^wiatr (.+) m/s$", r"wind \1 m/s"),
    (r"^kierunek (.+)°$", r"direction \1°"),
    (r"^maks\. w epizodzie dotąd (.+)°$", r"max so far \1°"),
    (r"^PORYW \|w\| — ostatnie (.+) s \(litera świata\)$", r"GUST |w| — last \1 s (world definition)"),
    (r"^maks\. dotąd (.+)%$", r"max so far \1%"),
    (r"^○ strefa R_E = (.+) m$", r"○ zone \1 m"),
    (r"^strefa oslony R_E = (.+) m$", r"protected zone \1 m"),
]
POLSKIE = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]|\b(epizod|zegar|sieć|kamera|strefa|osłon|panel taktyczny|brak|nie|się|przez|oraz|"
                     r"jest|dla|bez|AKT|FAZA|STAN|licznik|wabik|dron|intruz|cel|świat|zapis|lotu|estymat|odmow)\b")
SEEN = {}


def tr(s):
    if not isinstance(s, str) or not s.strip():
        return s
    if s in TR:
        out = TR[s]
    else:
        out = s
        for pat, rep in RULES:
            if re.match(pat, s):
                out = re.sub(pat, rep, s)
                break
        else:
            m = re.match(r"^(\d)\. (.+)$", s)                    # krok numerowany: „N. <tekst>” — tekst ze słownika/reguł
            if m:
                out = f"{m.group(1)}. {tr(m.group(2))}"
    assert not POLSKIE.search(out), f"NIEPRZETŁUMACZONE: {s!r}"
    SEEN[s] = out
    return out


def install():
    import cv2
    from PIL import ImageDraw
    _text, _len = ImageDraw.ImageDraw.text, ImageDraw.ImageDraw.textlength
    ImageDraw.ImageDraw.text = lambda self, xy, text, *a, **k: _text(self, xy, tr(text), *a, **k)
    ImageDraw.ImageDraw.textlength = lambda self, text, *a, **k: _len(self, tr(text), *a, **k)
    _pt = cv2.putText

    def put_text(img, text, *a, **k):
        t = tr(text)
        assert t.isascii(), f"cv2.putText nie-ASCII: {t!r}"
        return _pt(img, t, *a, **k)
    cv2.putText = put_text
    _gts = cv2.getTextSize
    cv2.getTextSize = lambda text, *a, **k: _gts(tr(text), *a, **k)     # (§2.3) etykiety mapy mierzone po tłumaczeniu


def P(*a):
    return os.path.join(DC, *a)


def O(nm):
    return os.path.join(OUT, nm)


KOPIE = {"democ_overlay_v2", "democ_overlay_v31", "democ_overlay_v5", "democ_overlay_v6", "democ_overlay_v7"}


def M(nm):                                                             # (§2/§4) v71: kopie narzędzi
    return nm + "_71" if UKLAD == "v71" and nm in KOPIE else nm


SEG1 = "0:0.2:1,0.2:3.2:0.5,3.2:32:1"
SEG4A = "0:12:1,12:34:3,34:44:1"
SEG4B = "0:4:1,4:18:2,18:26:1,26:30:2,30:38:1,38:52:3"
# (moduł, argv) — argumenty jak przy v2–v7 (transkrypty sesji), wyjścia w clips_en71/<układ>/  # (§2, §6)
STEPS = {
    "akt2_v2": (M("democ_overlay_v2"), [P("booty/d2_akty12"), "c10_s02", "2", "0", "34", O("akt2_v2.mp4")]),  # (§2, §4, §6)
    "akt3_v2": (M("democ_overlay_v2"), [P("booty/d3_akt3"), "c03_s01", "3", "22.7", "46.5", O("akt3_v2.mp4")]),  # (§2, §4, §6)
    "akt1_v31": (M("democ_overlay_v31"), ["akt1", P("booty/d1_proba"), "c08_s03", O("akt1_v31.mp4"), SEG1]),  # (§2, §4, §6)
    "akt4a_v31": (M("democ_overlay_v31"), ["4a", P("s3_wabik/akt4a_loiter"), "w00a_s01", O("akt4a_v31.mp4"), SEG4A,  # (§2, §4, §6)
                                        P("s3_wabik/akt4a_sig.json"), P("s3_wabik/akt4a_sig.jsonl")]),
    "akt4b_v31": (M("democ_overlay_v31"), ["4b", P("s3_wabik/akt4b_orbita"), "m01_s01", O("akt4b_v31.mp4"), SEG4B,  # (§2, §4, §6)
                                        P("s3_wabik/akt4b_sig.json"), P("s3_wabik/akt4b_sig.jsonl")]),
    "akt1_v5": (M("democ_overlay_v5"), ["brain-clip", O("akt1_v31.mp4"), O("akt1_v5.mp4"), P("booty/d1_proba"), "c08_s03", SEG1]),  # (§2, §4, §6)
    "akt2_v5": (M("democ_overlay_v5"), ["brain-clip", O("akt2_v2.mp4"), O("akt2_v5.mp4"), P("booty/d2_akty12"), "c10_s02", "0:34:1"]),  # (§2, §4, §6)
    "akt4a_v5": (M("democ_overlay_v5"), ["brain-clip", O("akt4a_v31.mp4"), O("akt4a_v5.mp4"), P("s3_wabik/akt4a_loiter"), "w00a_s01", SEG4A]),  # (§2, §4, §6)
    "akt4b_v5": (M("democ_overlay_v5"), ["brain-clip", O("akt4b_v31.mp4"), O("akt4b_v5.mp4"), P("s3_wabik/akt4b_orbita"), "m01_s01", SEG4B]),  # (§2, §4, §6)
    "akt5_v5": (M("democ_overlay_v5"), ["akt5", P("booty/d2_akty12"), "c10_s02", O("akt2_v2.mp4"), P("xai_pca_base.json"),  # (§2, §4, §6)
                                     O("akt5_v5.mp4"), "0:7.5:1,7.5:11.5:0.5,11.5:34:1"]),
    "akt6_v6": (M("democ_overlay_v6"), ["akt6", P("s6_wiatr/take2_c04"), "c04_s01", O("akt6_v6.mp4"), "0:8:1,8.1:64:2,64.1:72:1"]),  # (§2, §4, §6)
    "akt7_A": (M("democ_overlay_v7"), ["aktA", P("s7_gps/take1_c10_s01"), O("akt7_A.mp4")]),
    "akt7_B": (M("democ_overlay_v7"), ["aktB", O("akt7_B.mp4")]),
}
ORDER = ["akt2_v2", "akt3_v2", "akt1_v31", "akt4a_v31", "akt4b_v31", "akt1_v5", "akt2_v5", "akt4a_v5", "akt4b_v5", "akt5_v5",
         "akt6_v6", "akt7_A", "akt7_B", "karty", "cut"]
MONTAZ = ["akt1_v5", "akt2_v5", "akt3_v2", "akt4a_v5", "akt4b_v5", "akt5_v5", "akt6_v6",
          "karta_wejscia_v7", "akt7_A", "akt7_B", "karta_zakresu_v7", "plansza_v7"]
AKT7 = MONTAZ[7:]

PLANSZA_EN = ["LiquidPatrol — PX4/Gazebo simulation (SITL).",
              ("Zero zone breaches and zero false refusals in ~240 simulation runs." if UKLAD == "v71" else
               "Zero zone breaches and zero false refusals in ~140 simulation runs."),   # (§5)
              "Controller: a 20-neuron liquid network — 48/48 vs GRU 29/48",
              "on the same test grid.",
              "Decoys: recognised by behaviour — zero false alarms on attacking targets;",
              "a slow target that only circles remains indistinguishable.",
              "Controller: 20 neurons — proved boundedness theorems (T1/T2),",
              "activations auditable by replay.",
              "Time-varying wind up to 3.6 m/s on camera: 15/16 missions.",
              "Without GPS over a marker field: 12/12 flights of 110 s under proof; 10 minutes in one flight.",
              "Home hardware, evenings and weekends."]


def karty_en():
    import cv2
    sys.path.insert(0, HERE)
    V = __import__(M("democ_overlay_v7"))  # (§2, §5)
    V.PLANSZA7 = PLANSZA_EN
    for nm, rys, sek in (("karta_wejscia_v7", lambda: V.karta(V.CARD_IN_EN)[0], 4),          # (§3) rysuj i zapisuj po kolei
                         ("karta_zakresu_v7", lambda: V.karta(V.CARD_SCOPE_EN)[0], 6), ("plansza_v7", V.plansza7, 9)):
        img = rys()
        cv2.imwrite(O(nm + ".png"), img)
        vw = cv2.VideoWriter(O(nm + ".mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
        for _ in range(sek * 10):
            vw.write(img)
        vw.release()
    print("[karty_en] OK")


def cut_en():
    import cv2
    def cat(names, out):
        vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
        n, lens = 0, {}
        for nm in names:
            c = cv2.VideoCapture(O(nm + ".mp4")); k = 0  # (§6)
            while True:
                ok, fr = c.read()
                if not ok:
                    break
                assert fr.shape == (1080, 1920, 3), (nm, fr.shape)
                vw.write(fr); k += 1
            c.release(); lens[nm] = k / 10.0; n += k
        vw.release()
        return n / 10.0, lens
    t7, l7 = cat(MONTAZ, P("DEMO_C_v71_EN.mp4" if UKLAD == "v71" else "clips_en71/v7/DEMO_C_v7_EN_kontrola.mp4"))  # (§6)
    tg, lg = cat(AKT7, P("DEMO_C_v71_GPS_EN.mp4" if UKLAD == "v71" else "clips_en71/v7/DEMO_C_v7_GPS_EN_kontrola.mp4"))  # (§6)
    print(f"[cut_en] v7 EN {t7:.1f} s {l7}; klip GPS EN {tg:.1f} s")
    assert t7 <= 310.0 and tg <= 75.0


PANELE_KROKU = {"akt2_v2": ["std"], "akt3_v2": ["std"], "akt1_v31": ["std"], "akt4a_v31": ["std"], "akt4b_v31": ["std"],
                "akt1_v5": ["std", "brain"], "akt2_v5": ["std", "brain"], "akt4a_v5": ["std", "brain"], "akt4b_v5": ["std", "brain"],
                "akt5_v5": ["akt5"], "akt6_v6": ["std", "brain"], "akt7_A": ["std", "nadir", "brain"], "akt7_B": ["aktB"],
                "karty": ["karta"]}
BAZA = {"akt1_v5": "akt1_v31", "akt2_v5": "akt2_v2", "akt4a_v5": "akt4a_v31", "akt4b_v5": "akt4b_v31"}


def instrument(name):                                                     # (§3)
    os.environ["KOLIZJE_OUT"] = O(f"kolizje_{name}.json")
    os.environ["KOLIZJE_BAZA"] = O(f"kolizje_{BAZA[name]}.json") if name in BAZA else ""
    sys.path.insert(0, HERE)
    import democ_kolizje
    democ_kolizje.install(tr, PANELE_KROKU[name])


def step(name):
    if name == "karty":
        install(); instrument(name); karty_en(); return  # (§3)
    if name == "cut":
        cut_en(); return
    mod, argv = STEPS[name]
    install()
    instrument(name)  # (§3)
    sys.path.insert(0, HERE)
    m = __import__(mod)
    sys.argv = [mod + ".py"] + argv
    m.main()
    import json
    json.dump(SEEN, open(O(f"teksty_{name}.json"), "w"), ensure_ascii=False, indent=0)


FILM = [("akt1_v5", None), ("akt2_v5", None), ("akt3_v2", None), ("akt4a_v5", None), ("akt4b_v5", None), ("akt5_v5", None),
        ("akt6_v6", None), ("karty", (0, 40)), ("akt7_A", None), ("akt7_B", None), ("karty", (40, 100)), ("karty", (100, 190))]
FAZY = ("PHASE", "DISTANCE", "ORBIT", "TRACK", "SCAN")
# (§3) przedziały §1 w zegarze filmu v7 (±2 s): klasa → [(od, do, napisy A, napisy B)]
SPR = {"K1": [(120, 122, ("DECOY",), FAZY), (138, 146, ("DECOY",), FAZY), (148, 156, ("REVOKED",), FAZY)],
       "K2": [(124, 124, ("TRACK → APPROACH",), ("DISTANCE",))],
       "K3": [(48, 56, ("TARGET LOCK", "intruder", "home"), ("TARGET LOCK", "intruder", "home")),
              (84, 94, ("SHIELD REFUSE", "drone", "TOUCHDOWN"), ("SHIELD REFUSE", "drone", "TOUCHDOWN")),
              (96, 104, ("drone",), ("home",)), (124, 124, ("drone",), ("home",))],
       "K5": [(160, 194, ("vn", "ve", "vd"), ("+", "-"))]}


def agreguj():
    import json
    wynik, t_film = [], 0.0
    for nm, rng in FILM:
        kl = json.load(open(O(f"kolizje_{nm}.json")))["klatki"]
        if rng:
            kl = kl[rng[0]:rng[1]]
        for k, f in enumerate(kl):
            for c in f["kolizje"]:
                wynik.append({"klip": nm, "klatka_klipu": k, "t_klipu": round(k / 10.0, 1), "t_filmu": round(t_film + k / 10.0, 1), **c})
        t_film += len(kl) / 10.0
    out = {"uklad": UKLAD, "dlugosc_filmu_s": round(t_film, 1), "n_kolizji": len(wynik),
           "typy": {t: sum(1 for w in wynik if w["typ"] == t) for t in sorted({w["typ"] for w in wynik})},
           "per_klip": {nm: sum(1 for w in wynik if w["klip"] == nm) for nm, _ in FILM}, "kolizje": wynik}
    if UKLAD == "v7":
        def ok(txt, wz):
            return txt is not None and any(txt == w or txt.startswith(w) for w in wz)
        spr = {}
        for kl, lst in SPR.items():
            spr[kl] = []
            for (a, b, A, B) in lst:
                hit = [w for w in wynik if w["typ"] == "napis-napis" and a - 2 <= w["t_filmu"] <= b + 2 and
                       ((ok(w["a"], A) and ok(w.get("b"), B)) or (ok(w.get("b"), A) and ok(w["a"], B)))]
                spr[kl].append({"przedzial": [a, b], "klatki_kolizji": len(hit), "przyklad": hit[0] if hit else None})
        out["sprawdzenie_s1"] = spr
        out["s1_PASS"] = all(x["klatki_kolizji"] > 0 for v in spr.values() for x in v)
    json.dump(out, open(P(f"kolizje_{UKLAD}.json"), "w"), ensure_ascii=False, indent=1)
    print(f"[kolizje] {UKLAD}: {out['n_kolizji']} kolizji {out['typy']} per klip {out['per_klip']}"
          + (f"; §1 PASS={out['s1_PASS']}" if UKLAD == "v7" else ""))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "agreguj":  # (§3)
        o = agreguj()  # (§3)
        assert UKLAD == "v7" or o["n_kolizji"] == 0, "v7.1: kolizje niezerowe — render przerwany"  # (§3)
        return
    if sys.argv[1] == "step":
        step(sys.argv[2])
    elif sys.argv[1] == "all":
        for nm in (sys.argv[2:] or ORDER):
            r = subprocess.run([sys.executable, __file__, "step", nm], cwd=DC)
            assert r.returncode == 0, f"krok {nm} rc={r.returncode}"
            print(f"[democ_en] {nm} OK", flush=True)


if __name__ == "__main__":
    main()
