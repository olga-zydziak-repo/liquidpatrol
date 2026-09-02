# ANEKS_BENCH-1a — uzupełnienie po C1 (RAPORT_BENCH_BUILD przeczytany przez CC)

LiquidPatrol · ławka · CC 1.09.2026 · obowiązuje łącznie z ANEKS_BENCH-1; numeracja łańcucha bez zmian
(następna skuteczna linia = „ANEKS_BENCH-1 skuteczny", obejmuje -1 i -1a razem)

## §1. C1 przyjęte — ustalenia

U1 Mechanizm c11 (i t_entry 0.0 w c00/c10): dziedziczenie pozycji intruza między epizodami + nieprzerywalny
mover goniący pozę startową w trakcie epizodu. Jedna przyczyna, trzy symptomy (near-miss 0.26 m, d_min_orb
3.23/3.76, wejścia „0.0 s"). v1.1+v1.2 usuwa przyczynę; egzekutor bajt-w-bajt. N2(b) OBALONE z zastrzeżeniem
n=1/konfigurację — d_min jest kryterium D6, nawrót w kampanii będzie jawnym FAIL(d).
U2 Saturacja: tylko w kontrolerach (P-BB1 ✓); gate nie obcina; `vmax_check` = pomiar. Test kontraktu 10⁴
pozostaje jedynym strażnikiem — dla nogi sieci to będzie warunek wejścia, zapisane w §8 PRE.
U3 N3 (rozjazd licznika feed vs sędzia GT): sędzia rozstrzygający, licznik bench_flight = log. Przyjęte.
U4 N6: błąd CC w PROMPT §5 (test stall 2 s sprzeczny z D9 1.5 s); wykonawca zastosował „aneks wygrywa".
Zapisane jako błąd CC z działającym łapaczem.

## §2. Rozstrzygnięcia na punkcie STOP-1 (wyznaczonym w D9 do wyboru reguły)

R1 Reguła ważności kampanii = **V2′**: najdłuższy deep-stall (rtf < 0.5) ≤ 1.5 s wall ∧ Δsim/Δwall ≥ 0.90
na epizodzie; LICZBA zdarzeń deep raportowana per epizod, NIEBRAMKUJĄCA. Uzasadnienie: cap „≤3" przeniesiony
z §7 jako liczba absolutna gryzł jednopróbkowe blipy (4 × 0.05 s na 72 s ⇒ Δ 0.997), które są szumem próbnika,
nie chorobą mostu; przed patologią wielu stalli chroni Δ. JAWNIE: V2 odrzucała c00 shakeout, V2′ odrzuca 0/4 —
efekt zmiany ujawniony. Strażnik: kampania raportuje sukces D6 vs liczba stalli (0 vs ≥1); korelacja ujemna ⇒
rewizja V2′ dokumentem, nie cicho. Zamrożone od tego aneksu; sędzia dostaje V2′ w B5 (zmiana w bench_judge?
NIE — sędzia liczy V1/V2/V3 i tak; bramkowanie robi agregacja kampanii wg V2′; bench_judge NIETKNIĘTY, sha stoi).
R2 Manifest pierwszej klasy: przed kampanią commit **B5** = `bench/bench_finalize.py` — manifest per boot
ławki (lista epizodów z attempt/scenario_id/ważnością V2′, controller_sha, feed_sha, executor_params_sha,
ulog_sha, world_hash, wynik bramki procesowej, n wierszy demo), wołany z gałęzi `bench)` wrappera zamiast
crashującego `k1_finalize` (zmiana wyłącznie w linii dispatch `bench)` — diff verbatim do raportu); test bez
SITL (manifest bez null, stub tylko przy crashu). Zestaw zamrożony §3 NIETKNIĘTY.

## §3. Księga predykcji (build+shakeout)

P-BB1 ✓ · P-BB2 ✓ · P-BB3 ✓ · P-BB4 ✓ · P-BB5 ✗ (problemem start intruza, nie bramka resetu) ·
„1 linia wrappera" ✗ (2 linie; drugi raz zaniżony glue — poprawka kalibracyjna CC: przewidywania
o rozmiarze glue podawać jako przedział, nie liczbę). Suma ławki: 4 ✓ / 2 ✗.

## §4. Warunki skuteczności — stan po C1

C1 ✓ (ten aneks). C2 diff `b34.txt` — NADAL WYMAGANE. C3 sha zestawu zamrożonego — NADAL WYMAGANE.
C4 zredukowane: pozostaje tylko potwierdzenie mapowania INVALID_START → „env-nieważny, scenariusz na koniec
kolejki, attempt++" (część o V2 załatwiona: c00, n_deep 4 — z raportu C1).
NOWE C5: commit B5 (R2) z testem — może iść od razu, nie czeka na skuteczność (nie dotyka zamrożonego).
Linia „ANEKS_BENCH-1 skuteczny" pada po C2+C3+C4; kampania startuje po niej i po C5, przy pytest pełnym
na czystej maszynie i bramce procesowej CLEAN.
