# RAPORT_AKW — noga AKW (akwizycja: skan yaw przedakwizycyjny) — CLOSED

Wykonawca · 11.10.2026 · CO-AKW per ANEKS_AKW-3 §7. Noga otwarta decyzją Olgi
z katalogu (ANEKS_DET-4 §8), PRE_AKW ratyfikowane 09.10, zamknięta ANEKS_AKW-3.
Bilans: **29/≤32 bootów, 3 sesje lotne + 2 deski, 3 dni; breach 0 / REFUSE 0
w 25 uzbrojonych bootach nogi.**

## §1. WERDYKT NOGI (ANEKS_AKW-3 §3, verbatim)

1. **Mechanizm admisji pod rotacją zlokalizowany:** zmienna sprawcza ω·dt [°/klatkę],
   ogniwo = persystencja MTI nad celem transitującym kadr (fail_mti 70–95%; śledzenie
   toleruje ≥4.5°/kl); profil krokowy 40°/1.2 s omija go KONSTRUKCYJNIE — admisja
   98.4% (szybki mod) i 96–99% (wolny), vs 0/235 ciągłego @3.96°/kl.
2. **Skan krokowy domyka lukę geometryczną akwizycji** (dekompozycje §3) — pierwszy
   raz w programie D6 przechodzi na wszystkich bearingach; dron realnie znajduje cel,
   którego nie widział na starcie, w 9–16 s.
3. **Kampania powtórkowa 48/48 par wykonana i rozstrzygnięta progiem zamrożonym:
   ŚMIERĆ-AKW** — następne ogniwo nazwane co do mechanizmu i co do danych (dynamika
   celu szybkiego; re-akwizycja kierunkowo ślepa). Bezpieczeństwo: **breach 0 /
   REFUSE 0 w 25 uzbrojonych bootach nogi**; prawda programu (0/0 we wszystkim, co
   kiedykolwiek poleciało uzbrojone) utrzymana.

**Noga AKW: CLOSED — „luka geometryczna domknięta zachowaniem; skan nie wystarcza na
cel szybki; następne ogniwo: re-akwizycja kierunkowa".**

## §2. Łańcuch S0→S3 (liczby + odsyłacze)

- **S0 RECON** (`results/AKW_RECON/RECON_AKW.md`, commit 21102888): tor yaw nazwany
  (hover-hold emituje yaw=0.0 — mechanizm 29 ślepych DET; wpięcie = wrapper
  SetpointSource, SR-9 dopisaniem klasy); PX4 z drzewa (MC_YAWRATE_MAX 200,
  MC_YAW_P 2.8, lag ω/P); R3 zmierzone na replayach+kampanii: pasmo |yaw_rate|
  10–25°/s „czyste" (99.9/99.8% on-target) — jak się okazało w S1, mierzyło
  MIESZANKĘ KADENCJI (0.7–1.7°/klatkę), a nie rotację per se; ograniczenie nazwane
  w recon (transit przez kadr niemierzony; R5.8 intruz ruchomy × skan).
- **PRE_AKW** (ratyfikowane 09.10; ARCH-1 b1f77856): wrapper `net_akw`, profil
  ciągły ω=30°/s CCW, dwell 2.0 s, ψ_last; smoke A/B/C; kampania 12×{B, V2+skan},
  progi Δ_new z PRE_2A §4 verbatim; predykcje P-AKW-1..5.
- **S1 build+smoke** (`results/AKW/RAPORT_AKW_S1.md`, commity 50f83cf5+cc212d2a):
  testy przedlotowe 12/12 (pass-through bajtowy 5714+3754 tików + 411 tracków);
  smoke **A FAIL** (2/3 → powtórka 0/3) ⇒ STOP-ANEKS. **Mechanizm rozstrzygnięty
  liczbami:** boot 2 (14.71 Hz, 2.04°/kl): admisja 94.7%, akwizycje ze skanu
  działają; boot 3 (7.58 Hz, 3.96°/kl): **0/235** mimo profilu fizycznie wzorcowego
  (ulog 29.9°/s) — zmienna sprawcza = obrót MIĘDZYKLATKOWY ω·dt, nie ω. Błąd
  jednostki CC do księgi (ANEKS_AKW-1 §3): zamrożono niewłaściwą zmienną sprawczą.
- **S2 desk+profil II+re-smoke** (`results/AKW/RAPORT_AKW_S2.md`, commity
  80484a5c+157f1a3d): desk S2a (przyrząd `akw_s2a_cliff.py`, walidacja co do sztuki
  na liczbach S1; decymacja ×2 replayów przez frozen det_replay; ODMOWA decymacji
  rekordów bez klatek) — **ω·dt korpusu ≠ ruch pikselowy celu**: śledzenie przeżywa
  ≥4.5°/kl, w akwizycji pada MTI-persystencja (70–95%); κ₉₀ kandydaci 0.0/0.0/2.1
  ⇒ ω_safe ≤13.53 <14 ⇒ **ścieżka II step-and-stare** (reguła prereg zastosowana
  mechanicznie): krok 40° @60°/s → stare 1.2 s (ω·dt=0), 9 kroków = 16.8 s,
  t_A=23 s; wrapper 2237cc7c→**b94cdeae** (FROZEN, ratyfikacja ANEKS_AKW-2 §2);
  re-smoke **A′ PASS 3/3** (8.97/11.62/15.78 ≤23; D6 3/3 ślepych pierwszy raz),
  C PASS, admisja ślepych 98.4%.
- **S3 kampania** (`results/AKW/RAPORT_AKW_S3.md`, commity c9149e93+cfee6722):
  12 rund × {B, V2+skan}, oba ramiona net_akw, 25 bootów (1 powtórka), launches
  26/≤27; **Δ_new=12**; bezpiecznik modu bez tripa — ryzyko wolnego modu zamknięte
  pomiarem (10 bootów, 96.1–99.0%).

## §3. Kampania S3 — werdykt i dekompozycje (ANEKS_AKW-3 §2, obowiązkowe przy cytowaniu)

**Δ_new = 12 ≥ 10 ⇒ ŚMIERĆ-AKW: „skan nie wystarcza — akwizycja nie była jedynym
ogniwem."** (pass(B)=46, pass(V2+skan)=34, n_common=48; 46 sceno-świeże: Δ=10).
Próg zamrożony przed pierwszym lotem nogi; liczby się z nim nie targują.

- **Luka GEOMETRYCZNA akwizycji jest DOMKNIĘTA:** Δ po bearingach 3/3/3/3 (wzorzec
  DET: cały deficyt w bearing≠0); **24 z 35 ślepych porażek DET przechodzi**; koszt
  akwizycji deterministyczny (p50 1/4/6 kroków dla 90/180/270° = 5.0/9.5/12.9 s).
- **Rezyduum siedzi w CELU SZYBKIM:** v=1.0 niesie 9 z 12 Δ (v=0: 1; v=0.5: 2).
  ENTRY zachodzi niemal wszędzie (klasy F1_cel, **F3=0 w całej kampanii**) — pada
  budżet D6 PO akwizycji, nie percepcja.
- **Mechanizm regresji (c08_s02/s03/s04, bearing 0 + v=1.0):** po utracie szybkiego
  celu skan rusza od ψ_last — kierunkowo ŚLEPY (7–13 kroków reakwizycji), choć
  kontrakt feedu od zawsze niesie trk_vel_ned, którego re-akwizycja nie czyta.
  Saldo per-para vs DET: **+24/−3**.
- **ΔΔ = 34 − 12 = 22** — największa pojedyncza poprawa programu; ZAWSZE
  z kwalifikatorem dwóch kampanii (ten sam habitat/siatka; świeże B 46/48 vs 47/48
  jako kontrola dryfu — obie nowe porażki B to v=1.0 i padły też w V2).
- **Ryzyko wolnego modu ZAMKNIĘTE POMIAREM** (10 bootów, 96.1–99.0%, nigdy zero) —
  prereg-bezpiecznik zarobił na siebie bez odpalenia.

Tabela 48 par, telemetria per epizod (t_entry, fizyczne kroki do fresh/ENTRY,
mod per boot, klasy ENTRY), liczniki REFUSE per gałąź: `results/AKW/RAPORT_AKW_S3.md`
§4–§5 + `camp/akw_pairs.json` + `camp/akwS3_telemetry.json`. Telemetria jakości:
err_fresh V2 0.287/0.516 LEPIEJ niż wyrocznia B 0.674/1.279 (spójne z DET — po
akwizycji percepcja nie jest ogniwem słabym).

## §4. Mechanizmy (dwa, oba z liczbami)

1. **ω·dt + MTI-persystencja (klif akwizycji S1→S2):** admisja bramy struktura∧MTI
   zależy od obrotu międzyklatkowego ω·dt, nie prędkości ω; przy skanie ciągłym cel
   TRANSITUJE kadr z prędkością ≈ω·dt i persystencja MTI (3-z-4, move_thr 0.10) nie
   składa się nad nim (fail_mti 70–95%; central 4–24%; k=3 nigdy) — podczas gdy
   w śledzeniu box jest pikselowo stacjonarny i admisja przeżywa ≥4.5°/kl. Rozcięcie
   zmierzone deskiem S2a (decymacja ×2 przez frozen det_replay + punkty lotne 2.04
   i 3.96°/kl). Step-and-stare przenosi akwizycję do reżimu ω·dt=0 (dowiedzionego
   całym programem) i działa w OBU modach kadencji.
2. **Regresje c08 + trk_vel_ned (droga dalej):** skan startuje od ψ_last i jest
   kierunkowo ślepy — po utracie szybkiego celu potrafi odkręcić nos od niego
   (reakwizycja 7–13 kroków, fresh 15.5–27.7 s ⇒ D6 pada). Kontrakt feedu niesie
   trk_vel_ned (linreg 1 s) — ekstrapolacja kierunku przed wznowieniem pełnego
   skanu jest jednym zachowaniem w TYM SAMYM wrapperze (→ §8 RE-AKW).

## §5. KANON OBOWIĄZUJĄCY — ANEKS_AKW-3 (§4 verbatim)

**WOLNO** (kwalifikatory DET w całości + „akwizycja skanem krokowym 40°/1.2 s"):
- zdania 1–3 z §3 [ANEKS_AKW-3; tu §1] verbatim, z liczbami;
- „dron lata na kamerze w 34/48 scenariuszy pełnej geometrii (wyrocznia 46/48);
  rezydualne ogniwo = cel szybki, nie percepcja" — zdanie ZAWSZE z kwalifikatorem
  dynamiki celu;
- „ΔΔ=22 (34→12)" wyłącznie z kwalifikatorem dwóch kampanii i z jawnym Δ_new=12;
- „ryzyko wolnego modu zamknięte pomiarem (10 bootów, 96–99%, nigdy zero)";
- mechanizm c08 z trk_vel_ned jako nazwana droga dalej.

**NIE WOLNO:**
- „skan wystarcza" / „akwizycja rozwiązana" jako całość — ŚMIERĆ-AKW obowiązuje;
- „dron lata na kamerze" bez kwalifikatora dynamiki celu;
- przypisywać rezyduum detektorowi/percepcji (ENTRY F1 wszędzie, F3=0) ani osłonie
  (nie interweniowała: REFUSE 0);
- cytować ΔΔ bez Δ_new; porównań międzykampanijnych bez kwalifikatora;
- ekstrapolacji na realne sensory/warunki (PRE_2A §4 verbatim).

## §6. Predykcje (rozliczenie ANEKS_AKW-3 §5)

**P-AKW-1 ✗** (0.50; smoke padł na pierwszym profilu) · **P-AKW-2 ✓** (0.70; FP tła 0
w całej nodze, F3=0 w kampanii) · **P-AKW-3 ✗** (0.60; Δ_new=12 zamiast ≤4) ·
**P-AKW-4 ✓** (0.80; pass(B) dokładnie 46/48) · **P-AKW-5 ✓** (0.85; REFUSE 0).
**Suma: 3✓/2✗.** Kalibracja: trzeci kolejny przestrzał wyniku systemowego
(2A → DET-5 → AKW-3), w interakcji nazwanej-a-niezmierzonej (R5.8); doprecyzowanie
reguły w KSIĘDZE (korekta w dół ≈0.4–0.5 dla takich predykcji, dopóki interakcja
nie ma pomiaru choćby sondą).

## §7. Rejestr odchyleń nogi (ANEKS_AKW-3 §6 verbatim)

Błąd jednostki CC — zamrożono ω zamiast ω·dt (ANEKS_AKW-1 §3, klasa nowa); edycja
ratyfikowanego dokumentu przy ARCH-1 S1 (naprawiona amendem przed pushem); launch
przed promptem (reguła wzmocniona); ODMOWA decymacji rekordów bez klatek (dobra
praktyka, nazwana fałszerstwem wprost); rozbicie locked/unlocked wymuszone danymi;
pola nominalne analyzera (prawda = yaw_ulog); pad hosta r7 (narzędziowy); powtórka
r12_B (zapas 1/3); pole scan_dps_frozen historyczne od S2.

## §8. Roadmapa — RE-AKW (re-akwizycja kierunkowa), pozycja katalogu

**Trigger:** przed roszczeniem pełnej geometrii z celem szybkim. **Zakres:** dwell +
obrót w kierunku ekstrapolowanym z trk_vel_ned (dane już w kontrakcie feedu) przed
wznowieniem pełnego skanu — jedno zachowanie w TYM SAMYM wrapperze (akw_scan.py),
zero nowych komponentów uczonych, zero zmian osłony/sieci. **Aktywa gotowe:**
3 regresje c08 + 14 porażek V2 jako zbiór odniesienia (per-para w akw_pairs.json),
dwie kampanie-wzorce (DET S4 + AKW S3) do trzeciego pomiaru parowanego, profil II
FROZEN b94cdeae, cała ewaluacja (driver/parowanie/analyzer/bezpiecznik modu).
Najkrótsza ścieżka od 34/48 do pytania „ile naprawdę zostało". Wybór nogi należy
do trybu katalogu.
