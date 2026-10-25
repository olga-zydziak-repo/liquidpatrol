# ANEKS_PERC2-1 — przyjęcie S1 (remedium zmierzone, korekta tezy: transport DDS, nie GPU) + zlecenie S2 (test celowany T6 @k=1)

CC · 25.10.2026 · łańcuch PERC2 (PRE_PERC2 ratyfikowany, sha `24369ed9…1d9e21`;
commity nogi na origin: 96718e90 ARCH-1 + 3f3c7cc4 STOP-PERC2-1). Aneks
samowykonalny w zakresie §3 (sesja S2). Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-PERC2-1

Przyjęte po weryfikacji CC z repo WYKONANIEM: ARCH-1 bajt-w-bajcie (sha256
PRE w korzeniu = dokładnie dokument ratyfikowany; commit 1 osobny, tylko ten
plik); zakres S1 czysty (102 pliki, wszystkie NOWE, wszystkie w
results/PERC2/**; zero edycji czegokolwiek istniejącego); **macierz
przeliczona niezależnie z surowych percep_feed prób** — A2 0.132/0.607,
T1 0.068/0.4754, T2 0.132/0.695, T3 0.068/0.0017, T4 0.068, T5 0.068/0.0017:
zgodna z raportem co do trzeciego miejsca; render-vs-most odtworzony z
gzhz/roscount JSON-ów (poziom gz 606/40 s frac 0.0 RÓWNOLEGLE z próbą FAIL;
goły subskrybent 47–114 klatek bez profilu, 504 z profilem; kontrola busy17
wyklucza CPU callbacku); profil XML = wyłącznie pojemność transportu (SHM
16 MB, bufory UDP 4 MB, builtin off) — **zero elementów reliability/
durability/history**, semantyka QoS nietknięta; sha narzędzi 6/6 zgodne;
litera progu w perc2_sonda.py = litera PRE co do znaku; pin w 3/3 manifestach
= expected (pełny sha `3354ae1e8bcb…ee64c`, prefiks = recon); meta feedów
prób niesie FROZEN percep (det_v2 775ead15, feed_sha_v2 8015bd12); budżet
3/≤4 uczciwie z ABORTED. Geometryczność k_hist zweryfikowana przeze mnie na
danych RECON (p≈0.48: przewidywane 0.250/0.129/0.066/0.034 vs obserwowane
0.264/0.104/0.066/0.038 — odchyłki ≤2.5 pp, ogon trafiony).

## §2. Werdykt S1 i korekta tezy (odchylenie jawne — przyjęte wzorcowo)

**Śmierć S1 NIE zaszła; dźwignia PRE (k=1 środkami ops) POTWIERDZONA;
P-P2-1 = TAK** (rozliczenie KSIĘGI przy CO; cięcie głębokie na tej predykcji
było zasadne — remedium istnieje, ale mechanizm okazał się inny niż teza).

1. **Mechanizm (zmierzony):** klatki gubi TRANSPORT DDS — klatka mono8
   640×480 = 307 200 B > segment SHM FastDDS 512 KB (~1.6 klatki) i bufor UDP
   ~208 KB (<1 klatka) ⇒ losowa utrata BEST_EFFORT per subskrybent. Render
   sensora niewinny (gz zawsze 14.71 Hz, frac 0.0). **Teza PRE „wyborem k
   steruje stan GPU" SFALSYFIKOWANA jako mechanizm bezpośredni** (push_frame
   16.5–19.8 ms ≪ 68 ms, stany GPU identyczne przy FAIL i PASS); korelacja
   ×1.8 z recon pozostaje faktem — współobjaw stanu hosta, nie przyczyna.
   RECON_PERC2.md NIETKNIĘTY (raporty wstecz nietykalne; korekta żyje w
   RAPORT_PERC2_S1, tym aneksie i KSIĘDZE przy CO).
2. **Reinterpretacja „modów":** k_hist geometryczny ⇒ mod bootu = per-bootowa
   stopa dostarczenia p, nie czysta podharmoniczna (dt_p50 ląduje na 1/2/3
   tikach zależnie od p; kwantyzacja do siatki ticków pozostaje faktem).
   Wniosek metrologiczny: **żaden historyczny boot nie był gwarantowanie
   czysty** — „SZYBKI" znaczyło p>0.5, nie p≈1; reżim z profilem
   (frac 0.0000–0.0020) jest czystszy niż najlepszy boot historyczny.
   Porównywalność z kampaniami historycznymi wyłącznie z kwalifikatorem
   reżimu kadencji (bez zmian reguł; mod pozostaje telemetrią opisową).
3. **Litera zdań zamrożonych S2:** PRE §3.3 nazywa falsyfikację „TEZY
   GPU-KADENCJA" — zdanie operuje na zmierzonym k=1, więc działa bez zmian;
   etykietę czyta się od dziś jako „teza kadencja→admisja" (korekta w przód,
   litera PRE nietknięta).
4. Sonda kadencji zachowała się dokładnie tak, jak ją zaprojektowano:
   T1 (mediana 0.068 zdrowa, frac 0.4735) złapany DRUGĄ częścią progu ∧ —
   przypadek dziurawego strumienia z dobrą medianą, czyli dokładnie mod,
   który psuł okna admisji. Próg FROZEN bez zmian.

## §3. Zlecenie S2 — test celowany T6-geometrii @k=1 (aktywacja PRE §3; budżet 8+2 booty)

1. **Bramka:** `git fetch` → origin/master zawiera **3f3c7cc4 (STOP-PERC2-1)**;
   `origin/master..HEAD` puste ⇒ dalej, inaczej STOP; porcelain PEŁNY.
   FROZEN wykonaniem: komplet dotychczasowy (piny 5/5, certy 9/9, sędzia
   8ec0fcfb, bench 05137098, ncp 0337d5ea, FREEZE_DET) **+ FREEZE_PERC2_OPS:
   sonda 8df528bb · profil a68a450b · pin model.sdf pełny sha**.
2. **Każdy boot S2:** checklist hosta (FREEZE §checklist) → driver-kopia
   liczy pin model.sdf + world_hash PRZED stackiem (rozjazd = STOP) →
   `PERC2_FASTDDS_PROFILE` dla mostu obrazu i percep (XRCE/PX4 domyślne) →
   **sonda kadencji przed uzbrojeniem** (procedura FROZEN: FAIL ⇒ remedium ⇒
   powtórka ⇒ drugi FAIL = boot się nie uzbraja); wynik sondy w manifeście
   (`sondy[]`).
3. **Konfiguracja epizodów (PRE §3.2 verbatim):** CONTROLLER=net_fantom
   (e435ed7e), FEED=V2; scenariusze **T6 = {c08_s03, c08_s04, c10_s02,
   c11_s02, c11_s03, c11_s04}** (r1_anatomia epizody 0–5) **+ kotwice
   {c08_s01, c08_s02}** (oczekiwane PASS @k=1). Zbiór nielosowy: ŻADNEJ
   interpretacji progowej siatki, zero Δ. Układ epizodów per boot wg wzoru
   driver-kopii; budżet ≤10 bootów łącznie z powtórkami środowiskowymi.
4. **Loty są UZBROJONE — twarde STOPy verbatim:** breach ⇒ STOP;
   REFUSE(POS) ⇒ STOP; budżet ⇒ STOP. Przerwania planowane wyłącznie na
   granicach bootów. Osłona + piny nietykalne; zero dotyku percepcji,
   progów, sędziego.
5. **Telemetria i rachunek:** per epizod okna czołowe/radialne (p̂ per-klatkowe,
   max run central∧MTI, admisje, q_*, t_entry), mod + sonda per boot, D6
   OPISOWO (oczekiwane 2–3/6 T6; sufit TRANSIT obowiązuje — cytowanie
   wyłącznie z kwalifikatorem); **świadek-filtr |ned−cmd|_xy>1 m OBOK każdego
   rachunku sędziowanego**.
6. **Zdania zamrożone werdyktu (PRE §3.3, verbatim):** SUKCES DŹWIGNI =
   run≥3 (admisja okna) w ≥5/6 epizodów T6; FALSYFIKACJA = run<3 mimo k=1
   w ≥3/6 ⇒ STOP-ANEKS (mechanizm loterii nie był kadencyjny — wracamy do
   anatomii). Pomiędzy: strefa opisowa z dekompozycją per okno.
7. **STOP-PERC2-2:** commit (RAPORT_PERC2_S2: tabela okien per epizod
   p̂/run/admisja vs przewidywania modelu DP, werdykty D6 opisowo ze
   świadkiem, mody/sondy bootów, diff-stat, porcelain). **Push = Olga
   („wypchnięte" — CC czyta z repo).** Po weryfikacji CC: ANEKS_PERC2-2
   (werdykt, KSIĘGA P-P2-1…5, decyzja o kampanii metrologicznej — osobna,
   nieprekomitowana — i CO). STOP.

## §4. Status nogi

Budżet: 3/≤14 bootów wydane; S2 ≤10 ⇒ najwyżej 13/14. Predykcje P-P2-2
(admisja ≥5/6, 0.70), P-P2-3 (oba c08 D6, 0.60), P-P2-4 (breach/REFUSE 0,
0.85), P-P2-5 (sonda jako predyktor, 0.65) — żywe, rozliczenie przy CO.
Nietykalne bez zmian. Ścieżki (ii)/(iii) w katalogu, nieotwierane.
