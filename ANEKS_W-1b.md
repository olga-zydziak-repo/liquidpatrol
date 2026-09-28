# ANEKS_W-1b — errata parametru ramienia skryptowego (route → orbit) + rozstrzygnięcia budżetowe

CC · 28.09.2026 · łańcuch W (sub-numer po ANEKS_W-1a; ANEKS_W-2 pozostaje zarezerwowany na
werdykt nogi). Wklejany do CZEKAJĄCEJ, wznowionej sesji S2 — sesja kontynuuje od §5.

## §1. Errata i właścicielstwo błędu

Crash boot-0 to skutek MOJEGO ratyfikowanego parametru, nie zamrożonego kodu. `CONTROLLER=route`
(RouteFollower) jest kontrolerem PĘTLI GATE — wykonawcą trasy patrolowej z INFRA-3, o sygnaturze
fabryki i semantyce misji (kwadrat, zero pojęcia intruza/tracka) niekompatybilnych z pętlą ławki
i scenariuszem c11 (podejście + orbita). Ramię skryptowe ławki to od zawsze **egzekutor orbity**
— nauczyciel i kotwica programu. Klasa błędu CC: **nazwa z niewłaściwej przestrzeni nazw**
(rodzina „zgadywanie nazw z pamięci" z listy kalibracyjnej; w tej nodze trzecia instancja rodziny
źródłowania nazw po c11-bez-źródła w prompcie S0 i atrybucji REPO). Uczciwie o łańcuchu: etykieta
„route/CONTROLLER=route" urodziła się w RECON_W §R5(ii), przeszła recon → PRE_W §2 → ratyfikację
→ ANEKS_W-1 §3 i została złapana dopiero przez zamrożony przyrząd, który ODMÓWIŁ wykonania —
to jest poprawne działanie systemu: crash deterministyczny przed uzbrojeniem, zero skażonych
danych lotu, zero cichej podmiany po stronie wykonawcy (S2-B dotrzymane wzorcowo). Semantyka
ratyfikowana („egzekutor skryptowy jako kotwica, parowanie jak w nodze sieci") była jednoznaczna
i wykonalna — błędna była wyłącznie nazwa. Wpis do księgi błędów CC.

## §2. Rozstrzygnięcie 1 — parametr (pytanie 1: TAK)

Wszędzie, gdzie PRE_W (§2, §3, §12/W4) i ANEKS_W-1 (§3) mówią „route-executor" /
`CONTROLLER=route`, czyta się: **`CONTROLLER=orbit`** — OrbitExecutor `840514361e` +
`executor_params.json` `12c14adb` (zamrożony nauczyciel ławki; 35+ epizodów historycznych
w K2/NET; parowanie nauczyciel↔NCP z precedensem 47/48 par). Tożsamość jak zawsze przez
`controller_sha` w manifeście per boot. **Zero zmian w kryteriach, siatce, poziomach, ziarnach,
bramkach i budżetach** — zmienia się wyłącznie wartość jednego parametru na tę, którą semantyka
zawsze oznaczała.

## §3. Rozstrzygnięcie 2 — budżet (pytanie 2: NIE liczy się)

Crash przyrządu PRZED uzbrojeniem ≠ boot lotny. Precedens ANEKS_K1-5 B1: budżet liczy booty,
które POLECIAŁY; zdarzenia bez lotu żyją poza budżetem, ale są raportowane. Crash boot-0 wchodzi
do RAPORT_W jako osobna kategoria „crash przyrządu" z traceem. Łapacz przeciw nadużyciu tej
furtki: KOLEJNY deterministyczny crash przyrządu w tej sesji ⇒ twardy STOP i pytanie do CC —
żadnej pętli retry na crashach.

## §4. Rozstrzygnięcie 3 — licznik R-NC (pytanie 3: NIE konsumuje)

Licznik ≤2 podejść R-NC mierzy ZJAWISKO (uzbrojenie/wznoszenie pod wiatrem), a TypeError fabryki
przed arm nie niesie o nim żadnej informacji. Licznik startuje od zera z poprawionym parametrem.
Retry boot-0 do świeżego katalogu `results/W/camp/diag_boot0_r` (guard REPO-2 — stary katalog
z artefaktami crashu zostaje nietknięty jako ślad).

## §5. Przyjęcia i wykonanie

FREEZE_W 11/11 po 9 dniach = przyrząd nietknięty — przyjęte. Uzupełnienie W-A przyjęte
i zamyka dwie wątpliwości: eph_max ≈ 0.152–0.154 na wszystkich bootach (nominał; wcześniejsze
„0–4.5" było artefaktem transportu, sprawa zamknięta) oraz Δsim/Δwall 0.935–0.988 — wszystkie
≥ 0.90, czyli pod regułą ważności KAMPANII (V2′) te habitaty by przeszły; INVALID 5/5 dotyczyło
progu 0.95 przyrządu W-A i pozostaje niebramkujące. Commit 39bf7b7 (raport crashu + ślad)
przyjęty — booty VOID zachowują artefakty; push = Olga, PRZED kontynuacją (żeby ewentualne
kolejne wznowienie nie zderzyło się z bramką).

Sesja kontynuuje od R-NC boot-0 z `CONTROLLER=orbit`; cała reszta PROMPT_W_S2 (kolejność,
przeplot, ważność, ponowienia, STOP-y, raport STOP-W2) bez zmian. ARCH-1: `ANEKS_W-1b.md`
do korzenia repo pierwszym commitem po wznowieniu.
