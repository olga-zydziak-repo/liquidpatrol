# PRE_K2 — pozycja 6: sieć orbituje, denial GNSS, osłona przejmuje

LiquidPatrol · CC 6.09.2026 · **status: do ratyfikacji przez Olgę (K1–K6)** · wejście: RECON_K2 + R7
(ANEKS_K2-0) · łańcuch ANEKS_K2-n · wszystko zamrożone przed pierwszym bootem kryterialnym

## §0. Teza i czego nie twierdzimy

Teza: pod REALNYM denialem GNSS (`EKF2_GPS_CTRL=0`) w trakcie orbity kontrolera uczonego osłona wykrywa
degradację pozycji (dead-reckoning → `pos_flag`), odmawia (REFUSE) w budżecie czasowym K1 i wykonuje
zejście D5 do przyziemienia bez naruszenia R_E — pierwszy niepusty wpis ledgera z siecią za sterami
i PIERWSZE wykonanie ścieżki REFUSE pętli ławki (dotąd 0 wykonań — to część tezy, nazwana). Nie twierdzimy:
że osłona „certyfikuje" sieć; że wynik przenosi się poza SITL/feed emulowany; niczego o percepcji.

## §1. Decyzje do ratyfikacji

K1 Architektura = **(ii) uzbrojenie pętli ławki** (prior (i) z ANEKS_K2-0 §5 odwrócony faktami R7a/b):
(a) wiązanie `pos_flag` z dead-reckoning w `bench_flight` (wzór gate:267); (b) ekstrakcja zejścia D5
z pinowanego gate do współdzielonej funkcji `r03/controllers/safe_descend.py` — chirurgia wzorem INFRA-3:
re-baseline pinu gate (nowy sha), test bit-w-bit na nagranym strumieniu (identyczne cmd), ratyfikacja
CC dokumentem PRZED jakimkolwiek lotem; (c) hook wstrzyknięcia denialu w `bench_flight` (niepinowany):
`param set EKF2_GPS_CTRL 0` w T_inj; (d) `certs_selfcheck` włączony dla `FLIGHT=bench`. Efekt trwały:
ławka w pełni uzbrojona dla wszystkich przyszłych nóg — K2 naprawia znalezisko R1 u źródła, nie obchodzi.
Odrzucone (i)′ „gate + adapter samo-karmiący": legalne przez kontrakt, ale zostawia ławkę nieuzbrojoną,
1 epizod/boot psuje budżet, a sygnalizacja fazy przez pola kontraktu jest semantycznie mętna.

K2 Punkt wstrzyknięcia: **T_inj = t_entry + 30 s** (≈ 1 okrążenie przy okresie 28 s; sieć w ustalonym
stanie orbity; sygnał t_entry istnieje w runtime — R3). Deterministyczny, logowany w manifeście; test
buildu: wstrzyknięcie w ±0.2 s od zamierzonego na nagranym biegu.

K3 Scenariusze: komórki z `r4_envelope.json`, których **r_p95 w fazie T_inj ≤ 26 m** (zapas ≥ 2 m na p95
przy wychyleniu K1 3.5 m; twardy warunek koperty z R4: max 26.78 + 3.5 = 30.28 < 32 stoi dla pełnej
siatki — reguła p95 jest ciaśniejsza świadomie); z tych komórek 6 × 2 ziarna = **12 epizodów
kryterialnych**. Jeśli regułę spełnia < 6 komórek — STOP, tabela do Olgi, decyzja o geometrii jej
dokumentem. Ziarna z puli 1–10 (trajektorie znane sieci — celowo: mierzymy przejęcie, nie uogólnienie).

K4 Kryteria per epizod (przyrządy K1 przez glue `k2_judge` = ważność bench_judge do T_inj + metryki
k1-stylu po T_inj; glue frozen SHA przed lotami, testy syntetyczne w tym „REFUSE wstrzyknięty ⇒ metryki
liczą się", „brak denialu ⇒ epizod nominalny"):
(+) wszystkie z: REFUSE(POS) w ≤ 0.15 s od wykrywalności (pasmo K1); zejście D5 wykonane do touchdown;
breach = False; x_exc ≤ EPS_CAP; sekwencja bez natywnego failsafe. **PASS nogi = 12/12.**
11/12 z jednym epizodem środowiskowo nieważnym ⇒ scenariusz wraca (kolejka, cap 3). 
(−) 0 fałszywych REFUSE(POS) w fazie nominalnej epizodów (T_entry+30 s × 12 ≈ 6 min nominalu z uzbrojonym
monitorem) + baza 0/84 z lotów (uzbrojenie różne — raportowane osobno, nie sklejane).
ŚMIERĆ nogi: ≥ 2 epizody ważne z REFUSE poza budżetem ALBO bez zejścia ⇒ FAIL („osłona nie przejmuje
niezawodnie w reżimie orbity") — wynik pełnoprawny, raport z pełną prowieniencją. Breach jakikolwiek ⇒
STOP natychmiast, domena certów, diagnoza dokumentem.

K5 Budżety: build ≤ 1 sesja (a–d + testy: bit-w-bit gate po ekstrakcji, unit syntetyczny `pos_flag=True`
(dozwolony JAKO TEST), timing wstrzyknięcia, pełny pytest bez regresji) → **STOP-K2a** (ratyfikacja
re-baseline pinu, ceremonia INFRA-3); shakeout **1 boot diag** z denialem (pierwsze wykonanie
REFUSE+D5 w ławce — smoke, nie pomiar) → **STOP-K2b**; kampania ≤ 2 sesje / ≤ 8 bootów (5–6 ep/boot
z R6, epizod denialowy krótki) → **STOP-K2c** = RAPORT_K2.

K6 Kanon roszczeń K2 (pre-deklarowany): WOLNO „pod realnym denialem GNSS w trakcie orbity kontrolera
uczonego osłona odmówiła w ≤ X s i sprowadziła maszynę bez naruszenia koperty, 12/12, w SITL pod
emulowanym feedem". NIE WOLNO: „system bezpieczny", „certyfikowany", uogólnień poza SITL, języka
istotności. Ledger przestaje być pusty — i KAŻDY wpis cytuje przyczynę z trace.

## §2. Protokół

Mapa kryteriów ze źródłami na starcie każdej sesji (W2). Build → STOP-K2a → push → shakeout diag →
STOP-K2b → kampania (kolejka, cooldowny, bramka procesowa, driver w repo, inwentarze) → STOP-K2c.
Raporty tekstem płaskim. Zapisy `results/K2/**`.

## §3. Predykcje CC (prerejestrowane)

P-K2-1 Shakeout ujawni ≥ 1 defekt klasy glue w pierwszym wykonaniu REFUSE+D5 ławki (kod nietestowany
w locie), p ≈ 0.6 — po to jest diag przed kampanią. P-K2-2 t_refuse w paśmie K1 na wszystkich ważnych,
p ≈ 0.7. P-K2-3 mediana x_exc 2.0–3.5 m (jak K1 mimo innej geometrii — prędkość pozioma przy T_inj
podobnej skali), p ≈ 0.55. P-K2-4 zero breach, p ≈ 0.85. P-K2-5 ramię (−): zero fałszywych REFUSE
w nominalu z uzbrojonym monitorem, p ≈ 0.8.

## §4. Po ratyfikacji

Linia Olgi („K1–K6 TAK" / z korektami) → PROMPT_K2_BUILD od CC. Wartości do jej korekty w pierwszej
kolejności: T_inj (30 s), reguła komórek (p95 ≤ 26 m), próg PASS (12/12 — celowo bez luzu: to noga
o bezpieczeństwie, nie o skuteczności misji).
