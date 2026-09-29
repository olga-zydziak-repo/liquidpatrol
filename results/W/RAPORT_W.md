RAPORT_W — noga W (wiatr, poz. 2b): raport końcowy
===================================================
CC · 29.09.2026 · autoryzacja: ANEKS_W-2 (CO-W). Łańcuch: PRE_W (ANEKS_W-0) → S1 build+W-A
(ANEKS_W-1) → S2: crash route (39bf7b7) → ANEKS_W-1b → R-NC + kampania W-B 16/18 → STOP-W2
(15a4f2a) → ANEKS_W-2. Surowe dane: `results/W/RAPORT_W_S2.md` + `results/W/camp/**` +
`results/W/probe/**` (W-A). Noga W: **CLOSED — PASS + znalezisko** (z chwilą pushu CO-W).


§1. WERDYKT NOGI (ANEKS_W-2 §2, verbatim)
-----------------------------------------
**PASS ramienia dostępności na zmierzonej siatce ∧ ZNALEZISKO PIERWSZEJ WAGI.**

- **(−) dostępność — czysta:** 0 fałszywych REFUSE jakiegokolwiek rodzaju, 0 REFUSE(POS),
  0 breach R_E, dead_reckoning=False 17/17, eph ~0.151 (nominał) na wszystkich poziomach.
  Rdzeń pytania nogi („czy osłona fałszywie odmawia pod szumem świata") ma odpowiedź: NIE,
  w zmierzonym zakresie (wektor stały ≤3 m/s, c11). Komplet siatki wg zamrożonej reguły
  ≥2/3 ważnych ziaren per komórkę JEST spełniony: L3×route 2 ważne (s01,s02), L3×net 2 ważne
  (s01, s02 — epizod REFUSE jest WAŻNY habitatowo, jego wynikiem jest odmowa). s03 nielatane
  wskutek obowiązkowego STOP — zapisane, nie dolatywane (dolatywanie po znalezisku = selekcja).
- **ZNALEZISKO (nie FAIL):** pierwsza w historii programu **aktywna interwencja osłony wobec
  kontrolera uczonego w locie nominalnym** — REFUSE(GEOFENCE) gałęzią pionową NA CELU
  (|tgt_z| > V_E=20 przy pozycji EKF 19.787 — prewencja na komendzie, zanim pozycja przekroczyła
  obwiednię), przy estymatorze zdrowym (|EKF−GT| pion med 0.024 m, dr=False) ⇒ PRAWDZIWY wg
  zamrożonego kryterium. Domknięcie łuku programu: predykat, którego równoważność z modelem
  certu dowiodła noga FV (P8), wykonał pierwszy realny sejw. Zdanie zakazane w RAPORT_NET §11
  („osłona zawierała złą sieć" — ledger pusty 0/132) POZOSTAJE zakazane dla danych NET;
  noga W dostarcza pierwszy zmierzony przypadek aktywnego zawierania — cytuje się go z W.
- ŚMIERĆ nie zaszła (R-NC rozstrzygnęła no-climb jako artefakt modułu infra1); FAIL
  dostępności nie zaszedł.


§2. Zdarzenie STOP — liczby, klasyfikacja, mechanizm
-----------------------------------------------------
**Epizod:** L3/net_s02 (c11_s02, seed 2, world_wind_s3 = wektor stały 3 m/s ENU +x,
CONTROLLER=net/NCP-20 frozen, W_ARM_ALWAYS=1, bez denialu). Boot VALID na V2′ (dsw 0.930).

**Zdarzenie:** `refuse, reason=GEOFENCE, r_est=19.98, sim=179.556` — t_rel 68.5 s epizodu
(T_orb=70); po REFUSE protokołowy hover, episode_end, reset. Breach R_E: NIE (r_max 20.53,
margines 11.47 m).

**Tor tripu:** bariera R-G (r01/shield.py:101-112), gałąź pionowa NA CELU: w ticku tripu
EKF |z| = 19.787 < V_E = 20.0, zadziałało `|target_z| > V_E` na komendzie NCP — prewencja
zanim pozycja przekroczyła obwiednię.

**Klasyfikacja (kryterium zamrożone PRE_W §5):** okno 1 s przed tripem (20 ticków, metoda
w_judge): |EKF−GT| poziom mediana 0.099 m (max 0.108), pion mediana 0.024 m (max 0.026),
eph 0.151, dead_reckoning=False cały lot. Estymator zdrowy, stan realny ⇒ **REFUSE PRAWDZIWY**.
To nie jest tor POS (w_judge n_refuse(POS)=0 w całej kampanii).

**Mechanizm:** pełzanie wysokości ramienia NCP — profil z(t_rel) 8.2 → 11.4 → 14.6 → 17.1 →
18.8 → 19.78 m; uporczywa komenda wznoszenia (cmd_vz NED mediana −0.118 m/s przez ostatnie
30 s). Kontekst z siatki: egzekutor trzyma pion wszędzie (z_max 11.77–12.40 na wszystkich
poziomach), net pełza już przy WIETRZE ZERO (z_max 18.45 m, L0/net_s01; zakres net
12.40–19.77) — skłonność jest własnością ramienia net, poziom/ziarno modulują amplitudę.

**KWALIFIKATOR HABITATOWY (ANEKS_W-2 §3, obowiązuje):** habitat kampanii W różni się od
habitatu nogi sieci kopią modelu z `enable_wind` (opór aerodynamiczny działa także przy
wektorze 0) ⇒ „net pełza" wolno twierdzić wyłącznie z kwalifikatorem „w habitacie wiatrowym".
**NOTA Z TRIGGEREM:** przed jakimkolwiek zewnętrznym użyciem zdania o pełzaniu poza tym
habitatem — tania sonda atrybucyjna (1–2 booty net L0 na modelu stock). Nieotwarta.


§3. Siatka i krzywe
--------------------
Pełna tabela per epizod (17 bootów lotnych, wszystkie kolumny sędziowskie):
**RAPORT_W_S2 §2** (ten katalog). Skrót:
- Ważność: 17/17 VALID na V2′ (dsw 0.908–0.960, longest_stall 0.0, timejump 0); zero
  env-fail, zero ponowień, zero kolizji wyłączności.
- Tor POS: dr=False 17/17, eph ~0.151 nominał, 0 REFUSE(POS), 0 fałszywych odmów.
- Koperta: breach 0/17, r_max ≤ 25.51 (margines ≥ 6.49 do R_E=32), EPS_CAP użycie ≤ 2.76/9.25,
  vmax GT ≤ 3.73 < V_ENV=6.0 (flaga 0/17).
- Pary orbit↔net per (poziom, ziarno), opisowo: net wyżej w frac[6,10] w 7/8 par
  (mediana 0.850 vs 0.786); r_max i d_min zbieżne per ziarno (d_min 1.2–1.9 m dla s01 na
  1.5/3.0 w OBU ramionach — geometria ziarna, nie ramię); t_entry stabilne ~14–17 s wszędzie.
- Przechył (w_tilt, okno=cały ulog, porównawczo): mediany per poziom L0 2.14–3.85° ·
  L1p5 8.08–9.90° · L3 9.69–12.79°; p95 odpowiednio 12.6–17.3° / 18.7–21.9° / 25.7–29.0°.
  Monotoniczny podpis wiatru, parytet ramion.


§4. R-NC i doprecyzowanie H2
-----------------------------
Boot-0 diag @3.0 (c11_s01, orbit, `camp/diag_boot0_r`): wznoszenie z ziemi TAK (z_max GT
12.05 m), wejście w pasmo wg bench_judge t_entry 17.34 s, habitat V2′ VALID ⇒ **gałąź (a)**,
siatka pełna {0,1.5,3.0}. Doprecyzowanie H2: „no-climb @≥3.0" z W-A jest **artefaktem modułu
startu infra1** (natywny takeoff), nie własnością platformy pod wiatrem — start offboard
pętli ławki wznosi się przy 3 m/s. Próg dostępności startu = własność modułu startu.


§5. KANON OBOWIĄZUJĄCY — ANEKS_W-2 (verbatim §5)
------------------------------------------------
**WOLNO** (każde zdanie niesie: SITL, wektor stały, komórka c11, feed emulowany):
- „0 fałszywych odmów jakiegokolwiek rodzaju i 0 REFUSE(POS) w 17 uzbrojonych bootach pod
  stałym wiatrem do 3 m/s; dead_reckoning=False w każdym; kryterium fałszywości (ε_false=2.0 m,
  okno 1 s) zamrożone przed kampanią; baza bezwietrzna programu rośnie do 0 fałszywych odmów
  w 24+17 uzbrojonych epizodach".
- „Zmierzony próg dostępności STARTU jest własnością modułu startu, nie platformy: natywny
  takeoff (infra1) nie wznosi drona od 3 m/s, start offboard pętli ławki wznosi się przy
  3 m/s (boot-0, z_max 12.05)".
- „Osłona wykonała prewencyjną, aktywną interwencję wobec kontrolera uczonego w locie
  nominalnym: REFUSE(GEOFENCE) na KOMENDZIE (|tgt_z|>V_E) przy pozycji 19.79 m < V_E=20
  i zdrowym estymatorze (0.024 m błędu pionu); pełzanie wysokości sieci obecne już przy
  wietrze 0 w habitacie wiatrowym; n=1 wpis — istnienie i mechanizm, nie stopa".
- Sygnatura wiatru na platformie: przechył w zawisie/orbicie monotoniczny z poziomem
  (mediany ~3°/~9°/~10–13°); krzywe degradacji parowane per (poziom, ziarno); net wyżej
  w frac[6,10] w 7/8 par — opisowo, zakaz języka istotności.

**NIE WOLNO:**
- „odporny na wiatr"; czegokolwiek o turbulencji/podmuchach/uskoku z pomiaru wektora stałego;
  stóp niezawodności; ekstrapolacji poza SITL, poziomy {0, 1.5, 3} i komórkę c11.
- „sieć niebezpieczna" — net nie naruszył koperty (breach 0); to degradacja MISJI zawarta
  prewencyjnie przez osłonę. Symetrycznie: z n=1 nie wolno robić „osłona zawiera złe sieci"
  jako stopy.
- przypisywać pełzania wysokości wiatrowi (obecne przy L0) ani sieciom w ogólności
  (kwalifikator habitatowy obowiązuje do rozstrzygnięcia notą z triggerem).


§6. Rozliczenie predykcji (ANEKS_W-2 §4)
-----------------------------------------
P-W-1 ✗ (0 REFUSE, p≈0.75 — chybienie przyniosło główny wynik nogi) · P-W-2 ✗ (4.5 armuje,
W-A) · P-W-5 ✓ (przechył monotoniczny, parytet ramion) · P-W-3 poza sumą (hover @3.0 nie
zaistniał — no-climb infra1) · P-W-4 poza sumą (siatka L3 przerwana obowiązkowym STOP; 2 pary
to za mało na zdanie o ≤2 różnicach netto). **Suma nogi: 1✓/2✗ (+2 poza sumą).** Kalibracja
CC: obie ✗ to przewidywania o zachowaniu środowiska/systemu pod wiatrem (reguła 9).


§7. Odchylenia nogi (kompletny rejestr)
----------------------------------------
1. **Errata route→orbit (ANEKS_W-1b):** ratyfikowany parametr `CONTROLLER=route` (RECON_W
   §R5(ii) → PRE_W §2 → ANEKS_W-1 §3) był nazwą z niewłaściwej przestrzeni nazw; zamrożony
   przyrząd ODMÓWIŁ wykonania (crash deterministyczny przed armem, zero skażonych danych);
   wykonawca zatrzymał się bez cichej podmiany (S2-B). Czyta się `CONTROLLER=orbit`.
2. **Crash 20.09 poza budżetem** (ANEKS_W-1b §3, precedens ANEKS_K1-5 B1): kategoria „crash
   przyrządu", ślad w `camp/diag_boot0/` + commit 39bf7b7; licznik R-NC nieskonsumowany;
   drugi crash nie wystąpił (łapacz nieaktywowany).
3. **rc=134 bootu STOP (L3/net_s02):** „terminate called without an active exception" PO
   `[bench] done` — artefakt teardownu C++ po kompletnym locie; finalize przebiegł, manifest
   1. klasy; boot ważny (przyjęte ANEKS_W-2 §1).
4. **`.last_boot_end`:** w S2 wykonano `git rm --cached results/.last_boot_end` (dokończenie
   ratyfikowanego ANEKS_REPO-1a §4; przyjęte ANEKS_W-2 §6); przy CO-W analogicznie
   `results/INFRA3/.last_boot_end` i `results/K1/.last_boot_end`.


§8. Odsyłacz krzyżowy — zdanie o zawieraniu
--------------------------------------------
RAPORT_NET §11: „osłona zawierała złą sieć" pozostaje ZAKAZANE dla danych NET (ledger pusty
0/132 — brak zdarzeń do cytowania). Pierwszy zmierzony przypadek aktywnego zawierania
kontrolera uczonego przez osłonę pochodzi z nogi W (niniejszy raport §2) i wyłącznie stąd
wolno go cytować, w brzmieniu kanonu §5 (n=1: istnienie i mechanizm, nie stopa).
