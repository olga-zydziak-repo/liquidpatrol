# RAPORT_LIQ — zamknięcie nogi LIQ: kontrola architektury (liquid vs rekurencja vs okno)

LiquidPatrol · CC · 03.10.2026 · CO-LIQ per ANEKS_LIQ-2 §6 (po STOP-LIQ3, commit 6ea3013
na origin). Raport końcowy nogi: werdykt drabiny, liczby kompletu 48 par, bramka offline,
sonda STOCK, kanon roszczeń, predykcje, odchylenia. Noga: **CLOSED — W1′**. Loty zakończone
(27/31 bootów); ten commit jest doc-only, zero bootów. Raporty sesyjne (liczby źródłowe):
RAPORT_LIQ_S1 (trening/bramka offline/FREEZE_LIQ), RAPORT_LIQ_S2 (smoke + rundy 1–6),
RAPORT_LIQ_S3 (rundy 7–12 + sonda). Prerejestracja: PRE_LIQ (29.09, przed pierwszą epoką
i pierwszym bootem) + ANEKS_LIQ-1 (errata progu sondy i definicja W1′ — PRZED pomiarami,
których dotyczą).

## §1. WERDYKT NOGI: W1′ (drabina ANEKS_LIQ-2 §2; progi zamrożone w PRE_LIQ §4 i ANEKS_LIQ-1 §4, przed treningiem kontroli)

- **W0 — przyrząd trzyma:** NCP świeże 43/48 ≥ 40/48; dryf względem kanonu NET (45/48)
  w granicach szumu 48-epizodowej próby.
- **W2 — ŚMIERĆ NIE ZASZŁA:** Δ(GRU) = 43−27 = **+16** przy progu śmierci ≤ +2.
- **W3 — nieewaluowalne w locie** (kontrola okna odpadła offline); kierunek offline
  przeciwny tezie okna (0–1/24).
- **W1 pełne — niewykonalne** w tej nodze (wymagało obu kontroli w locie).

**⇒ WERDYKT: W1′**, zdaniem zamrożonym w ANEKS_LIQ-1 §4 (verbatim):

> „NCP-20 przewyższył kontrolę rekurencji o tym samym budżecie (Δ≥6/48 par); kontrola okna
> odpadła offline — przewaga nad GRU wykazana, pełna izolacja mechanizmu liquid wymagałaby
> latającej kontroli okna."

Wynik nie jest brzegowy: próg W1′ wynosił +6, zmierzono +16; kierunkowość par niezgodnych
17:1 (GRU wygrał parę wyłącznie na c11_s02). W1′ NIE uprawnia do zdań pełnego W1
(ANEKS_LIQ-1 §4).

## §2. Liczby kompletu — 48 sparowanych par (S2 rundy 1–6 + S3 rundy 7–12; pierwsza ważna, unresolved=0)

**Agregat per ramię** (`aggregate_campaign`, sędzia bench_judge 8ec0fcfb przez
campaign_analyze, D9=V2′):

| ramię | success/resolved | p_exec | Wilson 95% | z_max zakres [m] |
|---|---|---|---|---|
| NCP (CfC, 1903 par., wagi 0337d5ea) | **43/48** | 0.8958 | [0.7783, 0.9547] | 12.45–13.77 |
| GRU h=21 (1956 par., wagi 5ec02755) | **27/48** | 0.5625 | [0.4227, 0.6930] | 13.29–16.79 |

Wspólne ważne pary: 48/48 (24 booty kryterialne, 12/12 + 12/12 VALID za pierwszym
podejściem, 0 powtórek, timejump=0 wszędzie). REFUSE: 0 w 96 epizodach kampanii
(w tym zero POS/GEOFENCE). Breach R_E: 0.

**Macierz par (komórka × ziarno; wpis = NCP/GRU, P=PASS D6, F=FAIL):**

| komórka | s01 | s02 | s03 | s04 |
|---|---|---|---|---|
| c00 | P/P | P/P | P/P | P/P |
| c01 | P/P | P/P | P/F | P/F |
| c02 | P/P | P/P | P/P | P/P |
| c03 | P/F | P/F | P/F | P/F |
| c04 | P/F | P/P | P/F | P/P |
| c05 | P/P | P/F | P/P | P/P |
| c06 | P/P | P/P | P/F | P/F |
| c07 | P/P | **F/F** | P/P | P/P |
| c08 | P/F | P/F | P/F | P/F |
| c09 | P/P | **F/F** | **F/F** | P/P |
| c10 | P/F | P/P | P/F | **F/F** |
| c11 | P/P | **F**/P | P/P | P/P |

**Kierunkowość par niezgodnych: 17:1** (17 par NCP-PASS∧GRU-FAIL; 1 para odwrotna —
c11_s02). 4 scenariusze oblane WSPÓLNIE (c07_s02, c09_s02, c09_s03, c10_s04) — trudność
scenariusza, nie ramienia. 26 par obustronnie PASS.

**Gałęzie FAIL (pierwsza ważna):**
- **GRU, 21 FAIL:** 19/21 niesie gałąź **c_sweep** (17 czysto: c03_s01, c04_s01, c08_s01,
  c10_s01, c03_s02, c05_s02, c08_s02, c01_s03, c03_s03, c04_s03, c06_s03, c08_s03,
  c10_s03, c01_s04, c03_s04, c08_s04, c10_s04; 2 z d_dmin: c09_s03, c06_s04) + 2× czyste
  d_dmin (c07_s02, c09_s02). Kontrola rekurencji systematycznie traci pokrycie orbity;
  do tego pełza wyżej (z_max do 16.79 m vs NCP ≤ 13.77 w kampanii) — bez naruszeń koperty:
  degradacja misji, nie bezpieczeństwa.
- **NCP, 5 FAIL:** 4× d_dmin (c07_s02, c09_s02, c09_s03, c10_s04) + 1× b_frac+d_dmin
  (c11_s02). Słaby scenariusz NCP: c11_s02 (FAIL na ławce, FAIL(b_frac) w sondzie) —
  wpis opisowy, spójny z epizodem sejwu nogi W (ta sama konfiguracja geometrii; →§8).

Smoke lotny GRU (c11_s01, niekryterialny, poza Δ): PASS 3/3 — RAPORT_LIQ_S2 §3.

## §3. Bramka offline G13′ i kolaps MLP-k20 (odsyłacz: RAPORT_LIQ_S1 §3)

Próg: PER ROLLOUT ≥ 20/24 (analog-D6, VERBATIM z ANEKS_NET-1 §2, echo przed treningiem).
Tor treningu NCP zamrożony listą (PRE_LIQ §2); hiperparametry mapowane literalnie
(nota →§7). Wyniki (seed 1, lata wyłącznie PASS):

| ramię | parametry | best val-MSE | rollouty /24 | werdykt |
|---|---|---|---|---|
| NCP kanoniczny | 1903 | — (bez retreningu) | 24/24 | PASS (punkt odniesienia) |
| GRU h=21 | 1956 | 0.04901 | 24/24 | PASS ⇒ latał |
| MLP k=20 h=11 | 1939 | **0.01794** | **1/24** | FAIL ⇒ nie latał |

**Kolaps okna k=20 stabilny między ziarnami init** (dyspersja s1/s2/s3: MLP-k20 1/24,
0/24, 1/24; GRU 24/23/24; NCP 24/24/24 — RAPORT_LIQ_S1 §3) — przy NAJLEPSZYM val-MSE
z trójki (0.0179 vs 0.049): rozjazd model-punktowy↔rollout widoczny już offline (przy k=5
ujawnił go dopiero lot, 8/48 — noga NET). Zdanie kanonu MLP-k20 (PRE_LIQ §2, verbatim):
„pod zamrożonym torem treningu NCP kontrola MLP-k20 nie osiągnęła progu offline pozycji 3;
porównanie lotne niewykonane".

## §4. Sonda STOCK — NIEROZSTRZYGAJĄCE; kwalifikator habitatowy ZOSTAJE

Progi (ANEKS_LIQ-1 §3, zamrożone PRZED pomiarem; errata progu →§7): pełzanie NIEOBECNE ⇔
z_max ≤ 14.0 m w 2/2; POTWIERDZONE ⇔ z_max ≥ 15.0 m w ≥1/2; 14.0–15.0 ⇒ nierozstrzygające.

Wynik (2/2 booty VALID za 1. podejściem, model stock x500_base, świat world_wind_s0 =
FREEZE_W 921bdda7 byte-identyczny, CONTROLLER=net 0337d5ea, dowód stock
`GZ_SIM_RESOURCE_PATH=<puste>` w obu manifestach — RAPORT_LIQ_S3 §3):

| ziarno | sonda STOCK | W L0 enable_wind (ten sam świat) | Δ habitatu |
|---|---|---|---|
| s01 | **13.10** | 18.45 | **+5.35** |
| s02 | **14.26** | 14.43 | +0.17 (znika) |

s01 13.10 ≤ 14.0 ✓, ale s02 14.26 w przerwie 14.0–15.0; żaden boot ≥ 15.0 ⇒
**NIEROZSTRZYGAJĄCE**. **Kwalifikator habitatowy ZOSTAJE** — zdanie o pełzaniu NCP nadal
wolno wypowiadać wyłącznie jako „w habitacie wiatrowym (model enable_wind)". Nota opisowa
do kanonu: rozszczepienie per ziarno — na s01 habitat enable_wind dokłada +5.35 m, na s02
różnica znika; modulacja habitatu jest silnie zależna od ziarna. **Nota-z-triggerem
z ANEKS_W-2 §3 ZAMKNIĘTA** wynikiem „nierozstrzygnięte przy 2 bootach"; ewentualne
poszerzenie sondy to osobna pozycja katalogu, nie kontynuacja tej nogi.

## §5. KANON OBOWIĄZUJĄCY — ANEKS_LIQ-2 (§4 verbatim)

**WOLNO** (każde zdanie niesie: SITL, ławka 48 sparowanych scenariuszy, feed emulowany,
budżet ~1.9k parametrów, zamrożony tor treningu NCP):
- „NCP-20 (CfC, 1903 parametry) przewyższył param-matched kontrolę GRU (1956): 43/48 vs
  27/48 na 48 wspólnych ważnych parach (Wilson 95%: [0.778, 0.955] vs [0.423, 0.693]);
  architektury, tor treningu, progi i kryterium śmierci zamrożone przed treningiem kontroli."
- „FAIL-e kontroli GRU są zdominowane jedną gałęzią (pokrycie orbity, 19/21); GRU wykazuje
  też silniejsze pełzanie wysokości (do 16.8 m vs ≤13.8 u NCP), bez naruszeń koperty —
  degradacja misji, nie bezpieczeństwa (0 REFUSE, 0 breach w 96 epizodach kampanii)."
- „Param-matched kontrola okna (MLP k=20, 1939 par.) nie osiągnęła progu offline
  (0–1/24 rolloutów na trzech ziarnach init) przy NAJLEPSZYM val-MSE z trzech architektur —
  rozjazd model-punktowy↔rollout widoczny już offline."
- „Pierwszy kontrolowany wynik liquid-dodatni programu; odwraca null LiquidWatch
  (CfC vs GRU) w pętli lotu, z prerejestracją i parowaniem."
- Zdanie W1′ verbatim (§2).
- Pełzanie NCP: wyłącznie z kwalifikatorem habitatowym (§3), z notą o rozszczepieniu
  per ziarno.

**NIE WOLNO:**
- „liquid > MLP w ogólności" (trwale; k=20/h=11 i k=5/h=32 to dwa punkty przestrzeni);
- „liquid lepszy w zadaniach sterowania" ani jakiejkolwiek generalizacji poza tę ławkę,
  budżet i tor; stóp niezawodności z 48 epizodów; języka istotności;
- przypisywać przewagi „płynnej dynamice" jako wyizolowanemu mechanizmowi — izolacja
  niepełna (okno nie latało); wolno: „przewaga nad rekurencją GRU przy tym budżecie";
- „GRU niebezpieczny" — breach 0; symetrycznie: z porażki treningowej MLP-k20 nie wolno
  robić dowodu mechanizmu liquid;
- wnioskować z sondy w którąkolwiek stronę (wynik nierozstrzygający).

(Uwaga nawigacyjna: odsyłacze „§2"/„§3" wewnątrz kanonu wskazują sekcje ANEKS_LIQ-2 —
tu odpowiednio §1–§2 i §4.)

## §6. Rozliczenie predykcji (ANEKS_LIQ-2 §5; ledger → results/KSIEGA_PREDYKCJI.md, sekcja NOGA LIQ)

**P-LIQ-1 ✓** (GRU offline PASS). **P-LIQ-2 ✗** (MLP-k20 offline PASS, p≈0.7 — padł).
**P-LIQ-3 ✗ — predykcja modalna CC pada** (W2∪W3 p≈0.6; zaszedł wariant klasy W1,
któremu dawałem 0.2). **P-LIQ-4 ✗** (sonda NIEOBECNE p≈0.65 — wyszło nierozstrzygające;
s02 nad progiem). **P-LIQ-5 ✓** (NCP ≥ 43/48 — dokładnie na progu). **Suma nogi: 2✓/3✗.**
Kalibracja CC, wpis do księgi błędów: wszystkie trzy ✗ mają TEN SAM kierunek —
niedoszacowanie wyników komponentu uczonego/liquid; łącznie z nogą W (P-W-1, P-W-2) to
pięć chybień w jedną stronę przy zerze w drugą. Reguła 9 (predykcje CC nie są priorami)
potwierdzona i zaostrzona: w ocenach jakościowych stosuję korektę na udokumentowany
kierunek błędu.

## §7. Odchylenia nogi (kompletny rejestr)

1. **Errata progu sondy 13.0→14.0 (ANEKS_LIQ-1 §3, PRZED pomiarem; wpis do księgi błędów
   CC, klasa SEKWENCJI KALIBRACJI):** próg ABSENT ≤13.0 ustawiony w PRE_LIQ §5 na ślepo,
   zanim istniał punkt odniesienia zamówiony w tym samym dokumencie. Dane biurkowe
   (RAPORT_LIQ_S1 §5): historyczny stock w c11 (F2, świat A3) 12.86–13.27 m siedzi
   okrakiem na 13.0; separacja czysta stock 12.86–13.27 vs enable_wind L0 14.43–18.45 —
   próg położony w przerwę: ABSENT ≤14.0 / POTWIERDZONE ≥15.0 (bez zmian). Korekta
   legalna: sonda jeszcze nie poleciała, wyłącznie dane historyczne.
2. **Mapowanie hiperparametrów MLP-k20 (nota z RAPORT_LIQ_S1 §1):** literalne mapowanie
   promptu („to samo" = komplet gałęzi ncp; batch jako jedyny FORMAT toru okiennego) dało
   MLP-k20 lr 0.003 / cap 1000 (≠ historyczne mlp 0.001/80) — część ZAMROŻONEGO przyrządu,
   echo przed treningiem. Retrening z innym lr po obejrzeniu wyniku = strojenie po fakcie,
   zakazany w tej nodze (osobna noga, gdyby kiedyś trzeba).
3. **Nota r11_ncp (RAPORT_LIQ_S3 §2):** 1 linia `terminate called without an active
   exception` w act.log PO ostatnim episode_end+reset_done, przed czystym `[bench] done` —
   szum teardownu warstwy C++/MAVSDK, wzorzec precedensowany w F2 (f2_mlp_b5, f2_mlp_b6);
   zero wyjątków kontrolera/guardu (Python), finalize 4/4.
4. **Lock W transientny (sonda, RAPORT_LIQ_S3 §3):** launcher sondy (klon w_launcher)
   zakłada `results/W/.executor_lock`, zdejmowany trapem EXIT, niecommitowany — lista
   zamknięta plików dotyczy plików commitowanych; przyjęte w ANEKS_LIQ-2 §1.

## §8. Odsyłacze krzyżowe

- **RAPORT_NET §11 (results/NET/FLY/RAPORT_NET.md) — relacja kanonów NET↔LIQ:** kanon NET
  („NCP-20 dorównuje nauczycielowi w locie", 45/48, NCP vs tiny-MLP k=5 NIE-param-matched)
  pozostaje w mocy i NIE jest zastępowany; kanon LIQ (§5) DOKŁADA pierwsze param-matched
  porównanie architektur. NCP świeże 43/48 vs historyczne 45/48 = punkt kontroli dryfu
  ławki, w granicach szumu (W0). Zdanie o MLP z nogi NET (k=5, 2467 par., +29.6% budżetu,
  8/48) nadal nie rozstrzyga architektur — od teraz rozstrzyga ławka LIQ.
- **RAPORT_W §2 (results/W/RAPORT_W.md) — c11_s02:** scenariusz sejwu nogi W
  (REFUSE(GEOFENCE) prawdziwy, L3/net_s02) to ta sama konfiguracja geometrii, w której NCP
  obrywa na ławce (FAIL b_frac+d_dmin) i w sondzie (FAIL b_frac) — spójny, opisowy wpis
  o trudnej komórce; bez języka przyczynowego.
- **RAPORT_W §5 (kanon W) — kwalifikator pełzania:** status po sondzie: ZOSTAJE (§4);
  nota-z-triggerem ANEKS_W-2 §3 zamknięta wynikiem nierozstrzygającym przy 2 bootach.

**Noga LIQ: CLOSED — W1′.** Budżet 27/31 bootów, 0 powtórek, 0 INVALID, 0 REFUSE,
0 breach; kod repo nietknięty poza ratyfikowaną dopiską rejestru (S1). Push = Olga.
Program wraca do trybu katalogu (ANEKS_LIQ-2 §7): warstwa 0 → 2a.
