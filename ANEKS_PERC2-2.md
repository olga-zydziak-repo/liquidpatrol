# ANEKS_PERC2-2 — SUKCES DŹWIGNI zdaniem zamrożonym: przyjęcie S2, rozliczenie KSIĘGI, decyzja o kampanii, CO (zamknięcie nogi PERCEPCJA-II ścieżka (i))

CC · 26.10.2026 · łańcuch PERC2 (commity nogi na origin: 96718e90 + 3f3c7cc4 +
1503f880 + 5a1c278f STOP-PERC2-2). Aneks samowykonalny w zakresie §5 (sesja CO,
jeden commit, zero bootów). Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-PERC2-2

Przyjęte po weryfikacji CC z repo WYKONANIEM: ARCH-1 aneksu bajt-w-bajcie
(104 linie, sha zgodny); zakres czysty (91 plików, wszystkie NOWE, wszystkie
w results/PERC2/**); **tabela okien odtworzona z surowych percep_feed** —
krótkie okna c11 co do klatki (c11_s02: 40/0.300/run 6; c11_s03: 18/0.389/run 4),
długie zgodne z dokładnością brzegu okna (±1 klatka), kadencja lotu dt_p50 0.068
/ frac 0.0 we wszystkich 8 epizodach; **sędzia przeliczony niezależnie**
(import FROZEN 8ec0fcfb) w trzech wariantach GT (surowe / filtrowane świadkiem /
manifest): werdykty 5 PASS / 3 FAIL identyczne we wszystkich wariantach
werdyktowych, **flip artefaktu na surowych odtworzony** (c08_s03 F 1.19 →
P 5.7; c08_s04 F 0.53 → P 6.8), świadkowie co do sztuki (0,1,1,2,0,1,3,2),
różnice d_min vs tabela ≤0.11 m = zadeklarowana walidacja GT-manifestu
(werdykto-obojętne przy progu 4.0 m); **t_acq c11_s04 rozstrzygnięte surowym
feedem** — błyski fresh 12.57–13.36 s zgubione, akwizycja trwała od 24.91 s,
więc operacyjne 24.97 w tabeli poprawne; manifesty: pin model.sdf 2×OK, sonda
preflight rc=0 + uzbrojony_po_sondzie 2×, breach 0 / REFUSE 0 w 8/8 epizodach,
n_valid 8/8; pokładowa litera D6 (2+1) pozostawiona nietknięta OBOK rachunku
manifestowego — reguła ERRATUM-DMIN zastosowana wzorcowo.

## §2. WERDYKT NOGI (zdania zamrożone PRE §3.3)

**SUKCES DŹWIGNI: run≥3 (admisja okna) w 6/6 epizodów T6** (próg ≥5/6);
falsyfikacja (run<3 mimo k=1 w ≥3/6): **0/6 — nie zaszła**; kotwice-kontrole
2/2 PASS. Mechanizm domknięty modelem DP w OBU reżimach: okna długie (n 881–1093,
p̂ 0.99–0.998) = pewniki (runy 795–1084 vs 0–2 @WOLNY), okna krótkie głębokie
(c11_s02/s03: n 18–40, p̂ 0.30–0.39, P_model 0.49–0.54) = loteria resztkowa,
obie wygrane — przy k=1 loteria przestała dotyczyć WEJŚCIA w korytarz, zostaje
w zboczu bliskim. D6 opisowo: **T6 3/6 = dokładnie prereg 2–3/6** — loteria
czołowa ZNIKŁA (c08: t_acq 0.10–0.72 s vs 19.5–31.2 s tych samych epizodów
@WOLNY; oba przechodzą D6), c10 łapie korytarz przed pasem (8.78 < 10.0),
**sufit TRANSIT trzyma** dla bearingu 270° (c11: t_acq 12.2–25.0 s po
zamknięciu pasa; admisja zachodzi, konwersja nie — d_min 0.92–1.73).

**Zdanie kanoniczne (do cytowań):** „Kadencja percepcji była stratą transportu
DDS (klatka 307 kB > segment SHM 512 kB / bufor UDP 208 kB, BEST_EFFORT), nie
GPU; gwarancja k=1 środkami ops — profil FastDDS + sonda kadencji + pin
prowieniencji — zamienia admisję czołową z loterii w pewnik (6/6 T6, oba c08
odzyskane w D6), nie uchyla sufitu przeglądu perymetru (c11/270° FAIL realne,
11.15 s > 10.0 s niezależnie od kadencji) i odsprzęga metrologię każdej
przyszłej kampanii od stanu hosta."

## §3. KSIĘGA — rozliczenie P-P2-1…5 (wpisy przy CO, append-only)

- **P-P2-1 (0.60): TAK** — remedium ops istnieje i jest zmierzone (profil
  FastDDS; S1 3/≤4 bootów). Nota: mechanizm INNY niż teza (transport DDS, nie
  GPU) — cięcie głębokie na nazwanym-niezmierzonym remedium było zasadne.
- **P-P2-2 (0.70): TAK** — admisja okien czołowych 6/6 T6 (próg ≥5/6).
- **P-P2-3 (0.60): TAK** z kwalifikatorem: rachunkiem erratum (GT manifest,
  świadek obok); litera pokładowa dała F przez artefakt tranzientu teleportu —
  flip odtworzony niezależnie przez CC z surowych plików.
- **P-P2-4 (0.85): TAK** — breach 0 / REFUSE 0 w całej nodze (S1 bez uzbrojeń;
  S2: 2 booty uzbrojone, 8 epizodów).
- **P-P2-5 (0.65): TAK** — 2/2 bootów po sondzie trzymało k=1 w locie
  (dt_p50 0.064–0.068, frac 0.0; zero spadków po PASS sondy).

**Bilans: 5/5.** Wpisy kalibracyjne (obok rozliczenia): (a) dźwignię
prerejestrować ODDZIELNIE od atrybucji mechanizmu — tu dźwignia przeżyła
falsyfikację własnej tezy mechanizmowej i to jest wzór, nie wyjątek;
(b) progi narzędziowe projektować jako pary tendencja-centralna ∧ ogon —
druga część progu sondy (frakcja delt) złapała tryb „dziurawy strumień
z dobrą medianą" (T1: p50 0.068, frac 0.47), którego mediana sama nigdy by
nie zobaczyła.

## §4. DECYZJA: kampania metrologiczna 24+3 — NIE TERAZ

Osobna kampania kupiłaby nową bazę Δ bez pozycji, która jej potrzebuje
(zbiór S2 pozostaje nielosowy — żadnych roszczeń siatkowych z tej nogi).
Zamiast tego **reżim OPS (profil a68a450b + sonda 8df528bb + pin model.sdf
3354ae1e) staje się WARUNKIEM WEJŚCIA każdej przyszłej nogi kampanijnej** —
następna kampania werdyktowa odnowi bazę w czystym reżimie, płacąc booty za
werdykt pozycji, nie za samą bazę. Porównania międzyreżimowe wyłącznie
z kwalifikatorem (jak dotąd). Odwracalne: osobny PRE na kampanię bazową,
jeśli przed następną nogą kampanijną zajdzie potrzeba czystego porównania
siatkowego.

## §5. Zlecenie CO-PERC2 — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git log origin/master..HEAD` puste ⇒ dalej; inny stan ⇒ STOP.
Pliki (lista zamknięta): korzeń **`ANEKS_PERC2-2.md`** (ARCH-1, verbatim,
pierwszy w commicie); **EDYCJA `KIERUNKI_PO_PLANIE.md`:** pozycja PERCEPCJA-II
→ **ścieżka (i) OPS-KADENCJA: CLOSED (SUKCES DŹWIGNI, 5 bootów)** ze zdaniem
kanonicznym §2, odsyłaczem do `results/PERC2/RAPORT_PERC2_S2.md` i
`FREEZE_PERC2_OPS.md`, zapisem „reżim OPS = warunek wejścia przyszłych nóg
kampanijnych" oraz notą o decyzji §4 (kampania bazowa: nie teraz, odwracalne
osobnym PRE); ścieżki (ii) MTI-czołowy i (iii) detektor-v3/daleki-wzrok
ZOSTAJĄ z triggerami bez zmian. **Wpisy KSIĘGI** P-P2-1…5 + dwa wpisy
kalibracyjne §3 (append-only, wzór CO-FANTOM). ŻADNYCH edycji raportów,
RECON-ów ani kodu. Raport płaski: diff-stat, pełna treść zmian KIERUNKÓW
i KSIĘGI, porcelain. **Push = Olga („wypchnięte" — CC czyta z repo).** STOP.

## §6. Status

Noga PERCEPCJA-II ścieżka (i): **CLOSED — 5/≤14 bootów** (S1: 3, S2: 2),
breach 0 / REFUSE 0, KSIĘGA 5/5. Program zyskał: gwarancję k=1 jako reżim
operacyjny, pin prowieniencji sensora, odsprzęgnięcie metrologii od stanu
hosta i zamkniętą pętlę po sufit profilu misji (loteria czołowa zniknęła;
sufit c11/270° stoi jak zmierzony — jego adres to percepcja-era, ścieżki
(ii)/(iii) w katalogu na trigger). Warstwa 0 bez zmian.
