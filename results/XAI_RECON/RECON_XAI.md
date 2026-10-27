# RECON_XAI — recon pozycji XAI-SIECI: kotwica deterministyczna, atlas aktywacji NCP-20, kontrast GRU — STOP-XAIR

CC-wykonawca · 27.10.2026 · wykonanie PROMPT_XAI_S0. **Sesja w całości
rozpoznawcza: 0 bootów, 0 SITL, 0 treningu, zero edycji istniejących plików;
nowe pliki wyłącznie `results/XAI_RECON/**`.** Punkt odroczenia §R1 NIE zaszedł
— kotwica deterministyczna PASS, atlas wykonany na pełnej siatce LIQ 48×2
+ próbka OPS.

## §0. Bramka — PASS

`git fetch`: origin/master == HEAD == `44b271d3` (STOP-DEMOC-31, po v3.1),
`origin/master..HEAD` puste. Porcelain czysty poza nazwanymi `??` (wideo/jpg
DEMO_C — celowe). FROZEN wykonaniem (sha zmierzone na plikach):

| przyrząd | plik | sha (16) | zgodność |
|---|---|---|---|
| wagi NCP | `net/frozen/ncp.npz` | 0337d5ea | = FREEZE_NET (net_controller.py:31) ✓ |
| wagi GRU | `net/frozen/gru.npz` | **5ec02755 55b8fc0b…** | = FREEZE_LIQ literą: `5ec027555b8fc0bf12007a3dea0fdb5629fc46cdbbd859150b6963c4cdaac383` (1956 par., arm `gru`) ✓ |
| kod ramienia GRU | `r03/controllers/liq_controller.py` | 6d72437f | = FREEZE_LIQ „controller_sha 6d72437f7dd16d83…" ✓ |
| net_controller | `r03/controllers/net_controller.py` | e8c1b658 | ✓ |
| fantom_scan | `r03/controllers/fantom_scan.py` | e435ed7e | ✓ |
| rejestr | `r03/controllers/__init__.py` | 87203d29 | ✓ |
| bench | `bench/bench_flight.py` | 05137098 | ✓ |
| sędzia | `bench/bench_judge.py` | 8ec0fcfb | ✓ |
| cechy | `bench/features.py` | 9adc1505 | = FREEZE_LIQ ✓ |

Wszystko czytane importem/kopiami — zero dotyku.

## §R1. KOTWICA DETERMINISTYCZNA — **PASS**

**Wejście sieci w locie (litera, plik:linia):** 8 cech
`[rel_x,rel_y,rel_z,own_vn,own_ve,own_vd,track_age_s,track_valid]`
(`bench/features.py:30-33`; rel = trk−own), preprocessing `clip_age`
(cap age→1.0 s, `net/dataset.py:104-110`), standaryzacja `(x−mean)/std`
z metadanych npz wag (`net_controller.py:64-65,87-88`; identycznie GRU
`liq_controller.py:62-63,85-86`). Stan własny: NCP h(20) / GRU h(21),
**reset per epizod** — świeży kontroler na epizod (`bench_flight.py:310-312`).
Utrata tracka (`!valid ∨ age>1.0 s`) ⇒ cmd `[0,0,0]`, **sieć nie stepuje —
stan zamrożony** (`net_controller.py:106-111`). Wyjście: `clip_v(y, V_MAX=3.0)`
(`net_controller.py:97`, `r01/config.py:24`). Wrapper `net_fantom`
(FANTOM/PERC2/DEMO_C): kwarantanna K1 podmienia delegatowi fd na blank do
wyjścia A/B/C (`fantom_scan.py:93-140`, progi FROZEN T_q=3.0/D_JUMP=5.0);
`AkwScan` zmienia wyłącznie yaw w hold (`akw_scan.py:91-109`) — `cmd_v`
nietknięte.

**Komplet wejść JEST zalogowany:** `demo.jsonl` loguje per tick DOKŁADNIE
obiekty skonsumowane przez kontroler + jego wyjście — `bench_flight.py:360-361`
(ctrl.set_feed(fs); ctrl.step(tick, own, vel, …)) vs `:406`
(make_row(…, own, vel, fs, cmd["v_ned"], …)); pola litery:
`demo_logger.py:31-40` (own_pos_ned, own_vel_ned, trk_pos_ned, track_age_s,
track_valid, cmd_v_ned). **Jedyna strata informacji = zaokrąglenie zapisu do
3 miejsc** (`demo_logger.py:_r3`) ⇒ kwant 5·10⁻⁴.

**Replayer:** `tools/xai_replay.py` — modele importem (NCP20 `step_np`
`net/models.py:127-138`, GRU21 `net/models_liq.py:51-62`), wagi FROZEN, pełna
replika litery kontrolera + maszyny stanów kwarantanny. **Pomiar: 21 epizodów
z 3 kampanii** (LIQ r1/r5_ncp + r1/r5_gru = 16 ep.; FANTOM r1_V2 = 4 ep.
net_fantom na percepcji V2; DEMO_C d1_proba c08_s03 = 1 ep. percepcja żywa),
|wyjście_replay − cmd_v_ned| per tick (max po 3 składowych), wyniki
`xai_anchor.json`:

| metryka | wartość |
|---|---|
| p50 (mediana epizodów) | ~6·10⁻⁴ m/s |
| p95 (mediana / max po epizodach) | 1.22·10⁻³ / **1.32·10⁻³** m/s |
| max globalne | **2.45·10⁻³** m/s (8·10⁻⁴ V_MAX) |
| rozjazd na tickach hold (granica hold/inferencja, w tym kwarantanna) | **0 — co do bitu, 21/21 epizodów** |
| akumulacja w czasie | brak: p95 połówek epizodu 1.244 vs 1.212·10⁻³ (NCP) / 1.068 vs 1.058·10⁻³ (GRU); corr(|Δ|, tick) = 0.074 / 0.006 |

**Próg PASS nazwany z pomiaru:** rozjazd = szum zaokrąglenia zapisu
(kwant 5·10⁻⁴: wejścia i wyjście logowane po 3 miejscach) ⇒ kryterium
p95 ≤ 2·10⁻³ (4 kwanty) ∧ max ≤ 5·10⁻³ ∧ zgodność granicy hold/infer co do
ticku. Zmierzone: p95_max 1.32·10⁻³, max 2.45·10⁻³, granica 0 rozjazdów —
**PASS z zapasem; brak dryfu stanu. Replay z samych logów jest wiarygodnym
substratem atlasu — instrumentacja (shadow-logger, ~2 booty) NIEPOTRZEBNA.**

## §R2. ATLAS AKTYWACJI NCP-20 (`xai_atlas_ncp.json`, PNG w `png/`)

Korpus: **pełna siatka LIQ 48 epizodów ramienia NCP** — indeks epizodów
sędziowanych PO erratum z `results/POSCIG_RECON/erratum_sweep.json`
(cases `LIQ:*`, `judge_filtered`; NCP 48/48 PASS — zgodne z kanonem) +
**próbka OPS** 5 ep. (FANTOM r1_V2 + DEMO_C d1_proba; `xai_proba_ops.json`).
67.6k ticków inferencji NCP / 67.6k GRU. Narzędzie `tools/xai_atlas.py`,
lista pomiarów zamknięta w nagłówku, seedy stałe (0). Fazy z pola `phase`
demo (hold/approach/orbit; hold wykluczony — stan zamrożony, sieć nie widzi
wejść).

**(a) Separowalność faz approach/orbit — werdykt: CZĘŚCIOWA.**
Fisher J = **17.16** (wysoka separacja wzdłuż kierunku dyskryminacyjnego;
GRU 7.17), ale klastry niezwarte: najbliższy centroid (split epizodami
parz./nieparz.) recall approach/orbit 0.754/0.708, balanced acc **0.731**;
silhouette (podpróbka zbalansowana 2×2000) **0.057**. Uczciwość: etykieta
fazy pochodzi z progu d≤10 m (`ENTER_HI`, net_controller.py:36), a d jest
funkcją wejść — separowalność wzdłuż kierunku jest częściowo oczekiwana;
wynik mówi: faza NIE jest osobnym atraktorem, tylko rejonem na wspólnej
rozmaitości.

**(b) Wymiar efektywny — werdykt: CZYTELNY (najmocniejszy wynik atlasu).**
PCA puli 48 epizodów: **3 składowe na 90% wariancji, 5 na 95%**
(top5: 0.500/0.378/0.037/0.035/0.020). PC1+PC2 = **88% wariancji, a stan
leży na PIERŚCIENIU** (`png/ncp_pca_fazy.png`) — cykl graniczny orbity;
approach wchodzi do wnętrza pierścienia. 20 neuronów o dynamice ~3-wymiarowej:
polityka jest niskowymiarowa i audytowalna. Próbka OPS (percepcja żywa,
skan/kwarantanna): n_90 = **2** — struktura trzyma się poza ławką
(separowalność na OPS słabsza: bal.acc 0.62 przy 249 tickach approach —
mało danych, nie werdykt).

**(c) Role neuronów — werdykt: CZYTELNE/CZĘŚCIOWE, zero splątanych.**
|Pearson| h_i × {cechy, d, cos/sin bearingu, wyjścia}: **11/20 neuronów
czytelnych** (max|r| ≥ 0.8), 9/20 częściowych (0.5–0.8), **0 splątanych**
(<0.5). Dominują neurony BEARINGU (sin/cos kąta do celu: n0 |r|=0.95 sin,
n5 0.89 cos, n2 0.87 sin…) + neurony prędkości własnej (n7 own_vn 0.89) —
spójne z pierścieniem z (b). Zastrzeżenie: korelacja ≠ przyczynowość (opisowe).
Cecha `valid` ≡ 1 na tickach inferencji (zdegenerowana, wykluczona z korelat).

**(d) Stałe czasowe per neuron (bramka czasu CfC gate, models.py:133) —
werdykt: CZĘŚCIOWY, z wyraźnym sygnałem granicznym.** Średnie bramki w wąskim
pasmie: approach [0.37, 0.64], orbita **[0.45, 0.55]** (pasmo ZWĘŻA SIĘ
w ustalonej orbicie — jednorodna retencja); max różnica fazowa per neuron
0.148. **Skok na granicy approach→orbit (42 przejścia, okna ±1 s vs baseline
losowych okien wewnątrz fazy): 9/20 neuronów z ratio > 2** (max 3.19, mediana
ratio 1.87) — bramki czasu części neuronów przełączają się na granicy fazy.
NIUANS UCZCIWOŚCI vs litera promptu („GRU nie ma τ z konstrukcji"): GRU MA
zależną od wejść bramkę retencji z (models_liq.py:54) — zmierzyliśmy ją jako
obserwablę analogiczną (§R3); różnica jest w MECHANIZMIE (CfC: wypukła
interpolacja dwóch świeżych głów tanh per tick ⇒ |h|<1 architektonicznie
i brak czystego integratora; GRU: z→1 pozwala trzymać stan bez dopływu) —
i w zmierzonym PROFILU (NCP: wąskie pasmo ~0.5; GRU: rozrzut 0.04–0.86).

**(e) Saliency chwilowe (Jacobian ∂y/∂x różnicą centralną eps=1e-4 przy
ZAMROŻONYM h; ścieżka rekurencyjna wykluczona — ograniczenie nazwane) —
werdykt: CZYTELNE.** Struktura quasi-diagonalna prawa pościgu: vn←rel_x
(|J| 2.28 approach → 3.64 orbita), ve←rel_y analogicznie; tłumienie od
prędkości własnej (vn←own_vn ~1); **kanał pionowy martwy** (|J| vd ≤ 0.20 —
sieć nie steruje wysokością, spójne z zadaniem). Wzmocnienia ROSNĄ w orbicie
(ciaśniejsza pętla przy d≤10). `png/saliency_ncp_gru.png`.

## §R3. KONTRAST Z GRU (`xai_atlas_gru.json`, `xai_kontrast.json`) — analiza OPISOWA (mechanizm-kandydat, nie dowód przyczynowy)

**(a) Te same obserwable na 48 lotach GRU:** wymiar n_90 = **4** (top2 69%
vs 88% NCP — stan BARDZIEJ rozproszony); pierścień też istnieje (grubszy,
`png/gru_pca_fazy.png`); role: **8/21 czytelnych** (vs 11/20), 13/21
częściowych, 0 splątanych; separowalność faz: Fisher J **7.17** (×2.4 niższy
niż NCP) przy podobnej balanced acc 0.76 i silhouette 0.08; saliency ta sama
struktura pościgowa (vn←rel_x 3.21), ale kanał pionowy mniej martwy
(vd do 0.45). Bramka z: rozrzut per neuron 0.04–0.86, różnice fazowe do
0.415, skok graniczny 5/21 neuronów ratio>2 (jeden 9.47), mediana ratio 1.42.
**Podsumowanie kontrastu struktury: NCP czytelniejszy w (b) wymiarze,
(c) rolach i (a-Fisher); GRU nie jest „nieczytelny" — jest mniej
skompresowany.**

**(b) 19 epizodów przewagi (NCP PASS ∧ GRU FAIL po erratum; lista
w `xai_kontrast.json.adv_sids`, zgodna z kanonem 48−29=19):** wszystkie
19 porażek GRU = **`c_sweep`** (niedomknięte pokrycie kątowe orbity —
sędzia 8ec0fcfb). CROSS-REPLAY open-loop (model GRU na WEJŚCIACH zalogowanych
lotów NCP — te same wejścia, zero sprzężenia): mediana |v_NCP−v_GRU| p50
**0.287 m/s na epizodach przewagi vs 0.285 na 29 kontrolnych (oba PASS)** —
chwilowy rozjazd komend NIE odróżnia epizodów przewagi. Rozjazd rośnie
w approach (0.38–0.42) i epizodycznie strzela do 3–4.4 m/s przy wyjściach
d ku granicy pasma (`png/kontrast_c08_s01.png`). **Mechanizm-kandydat
(opisowy): przewaga NCP nie bierze się z innej chwilowej mapy wejście→wyjście
(te są zbliżone), lecz z akumulacji małych różnic w pętli zamkniętej —
GRU gubi domknięcie orbity (c_sweep 19/19), nie zbliżenie ani breach.**
Dowód przyczynowy wymagałby kontrfaktycznych lotów — poza reconem.

## §R4. Artefakty (inwentarz widoków; zero montażu wideo)

`png/`: `ncp_raster_c03_s01.png` + `gru_raster_c03_s01.png` (paski h i bramek
w czasie + pas faz; widoczna okresowość orbity), `ncp_pca_fazy.png` /
`gru_pca_fazy.png` (pierścień stanu kolorowany fazą), `tau_bramki_fazy.png`
(mapa bramek per neuron×faza, NCP vs GRU), `saliency_ncp_gru.png` (mapy |J|
per faza), `kontrast_c08_s01.png` (rozjazd cross-replay w czasie vs dystans).
JSON-y: `xai_anchor.json`, `xai_atlas_ncp.json`, `xai_atlas_gru.json`,
`xai_proba_ops.json`, `xai_kontrast.json`. Do przyszłego demo nadają się
wprost: pasek aktywacji + bramek zsynchronizowany zegarem epizodu (ten sam
tor posthoc co panele DEMO_C v3/v3.1).

## §R5. Granice uczciwości + prior art

- **Wyjaśnialność ≠ weryfikacja.** Atlas opisuje korelacje i geometrię stanu;
  nie dowodzi własności. Saliency chwilowe pomija ścieżkę rekurencyjną
  (gradient przez h) i jest lokalne wokół punktu pracy; role neuronów =
  korelacje (confounding przez wspólną geometrię orbity — bearing koreluje
  z większością sygnałów). Etykiety faz pochodzą z progu d≤10 (reguła
  kontrolera), nie z niezależnej anotacji.
- **„Pełna wyjaśnialność" nie jest werdyktem tego reconu.** Werdykty per
  obserwabla: (a) częściowa, (b) czytelna, (c) czytelna/częściowa,
  (d) częściowa, (e) czytelna.
- **Prior art (nazwiska/tytuły Z ZASTRZEŻENIEM weryfikacji bibliograficznej
  przed cytowaniem na zewnątrz):** linia NCP/liquid sprzedaje się jako
  „auditable autonomy" — M. Lechner, R. Hasani i in., *Neural circuit
  policies enabling auditable autonomy* (Nature Machine Intelligence, 2020);
  R. Hasani i in., *Liquid Time-constant Networks* (AAAI 2021) oraz
  *Closed-form continuous-time neural networks* (Nature MI, 2022) — nasza
  komórka to CfC (models.py:11-13). **Warstwa nowości programu = KOMPOZYCJA:
  audyt aktywacji polityki klasy werdyktowej na pełnym korpusie kampanii
  sędziowanych (48×2 po erratum, kotwica deterministyczna do logów lotu)
  + kontrast z pokonaną bazą na tych samych wejściach** — nie sama idea
  „liquid = auditable".

## §R6. Wycena ścieżek + rekomendacja

- **(i) Atlas offline:** w zasadzie SKONSUMOWANY tym reconem (0 bootów).
  Ewentualna noga porządkująca (PRE z zamkniętą listą twierdzeń, pełne
  korpusy FANTOM/PERC2/DEMO_C, stabilność obserwabli między kampaniami):
  deskowa, **0 bootów**, 1 sesja.
- **(ii) Zasilenie 1b(ii) weryfikacji formalnej — kandydaci na własności
  Z POMIARÓW (rekomendowane):**
  1. **ograniczoność wyjść** — architektoniczna (tanh×V_MAX models.py:135-136
     + clip_v druga szelka): dowód statyczny, natychmiastowy;
  2. **ograniczoność stanu NCP** — lemat architektoniczny: h′ = gate·g +
     (1−gate)·hh to wypukła kombinacja dwóch tanh ⇒ |h′|∞ < 1 zawsze
     (models.py:130-134); analogiczny indukcyjny dla GRU;
  3. **pasmo bramek** — zmierzone [0.37,0.64]/[0.45,0.55]: kandydat na
     założenie przedziałowe do dowodów typu Lipschitz/kontraktywność na
     rozmaitości roboczej;
  4. **znak/monotonia prawa pościgu** — saliency vn←rel_x, ve←rel_y stałego
     znaku w obu fazach: kandydat na własność kierunkową dowodliwą
     przedziałowo (interwałowa propagacja przez 1 krok CfC);
  warsztat FV istnieje (noga FV: O1/O2 PROVED). Deskowe, **0 bootów**.
- **(iii) Nakładka demo „co myśli sieć":** tor gotowy (replay posthoc jak
  panele DEMO_C v3.1 + paski z R4); **era montażu, ~1 sesja, 0 bootów —
  wycenione, NIE otwierane.**

**Sufit ewentualnej nogi XAI: 0 bootów (całość deskowa; kotwica PASS znosi
potrzebę instrumentacji).** **Rekomendacja: PRE_XAI dla ścieżki (ii)+(i)
łącznie** — jedna noga deskowa: zamknięta lista twierdzeń FV zasilonych
atlasem (4 kandydatury wyżej) + porządek atlasu na pełnych korpusach; (iii)
czeka na erę montażu. Uzasadnienie: (ii) zamienia najmocniejsze wyniki atlasu
(niskowymiarowość, pasmo bramek, ograniczoność architektoniczną) w twierdzenia
klasy dowodowej — najbliżej „audytowalnej autonomii" jako WYNIKU, nie
przymiotnika.

## Narzędzia i artefakty (sha256, 16)

| plik | sha | rola |
|---|---|---|
| `tools/xai_replay.py` | ac9551abf92dd1e2 | replayer + kotwica R1 (modele/cechy importem z FROZEN) |
| `tools/xai_atlas.py` | d0af3f2458f6cdb6 | atlas R2 + kontrast R3 + PNG R4 (lista pomiarów zamknięta) |

**STOP-XAIR.** Commit: RECON + tools + JSON-y + PNG. **Push = Olga
(„wypchnięte" — CC czyta z repo).** Potem CC: **PRE_XAI ścieżki (ii)+(i)**
(rekomendacja §R6). Zero edycji czegokolwiek istniejącego.
