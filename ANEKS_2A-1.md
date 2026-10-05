# ANEKS_2A-1 — werdykt bramek A/B, naprawa yaw na granicy MAVSDK, bramkowanie REFRESH, powtórka etapu A

CC · 05.10.2026 · łańcuch 2A (po STOP-2A2, commit 0dd749a na origin). Samowykonalny: §6.
Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-2A2

Przyjęte po weryfikacji CC z repo: liczby bramek zgodne z raportem; **sędzia i agregator
nie konsumują yaw w żadnej linii (grep bench_judge + campaign_analyze: zero trafień —
potwierdzone wykonaniem)**, więc werdykty NET/K2/W/LIQ stoją bez jednej gwiazdki; miejsce
usterki potwierdzone w kodzie (bench_flight.py:398 — surowe radiany w stopniowe pole
VelocityNedYaw; wszystkie trzy kontrolery emitują atan2-radiany; komentarz „kosmetyka"
przy yaw w net_controller dokumentuje, czemu nikt tego nie widział przez pięć nóg — nos
był dekoracją, dopóki kamera nie uczyniła go nośnym). Diagnostyka habitatu 05.10 wzorowa
(3 diagi 0-lotne, mitygacja GZ_IP udowodniona: ekf2 0→1473 updates). Tryb cienia wykonał
dokładnie swoją robotę: złapał ukrytą usterkę harnessu za 2 booty, zanim dotknęła
jakiejkolwiek kampanii.

## §2. Werdykt bramek

**Bramka A: FAIL (i) z przyczyną ZEWNĘTRZNĄ wobec percepcji** — pokrycie 0.609/0.403
i 0.113/0.385 przy progu 0.90, 100% wypadnięć przez azymut, elewacja w zapasie (desk
potwierdzony w jedynej osi, w której przyrząd działał). (ii) dsw 0.9907/0.9951 PASS bez
retry — **pełny stack percepcji kosztuje zero RTF**; (iii) quat PASS z niezależnym dowodem
konwersji ramek (vs attitude PX4 p50 0.76–0.92°).

**Etap B — rozstrzygnięcie trójdzielne:**
- progi CZASOWE zmierzone uczciwie (nie zależą od celowania) i **PASS kryterialnie**:
  kadencja 14.71 Hz, latencja p95 0.044 s. **Śmierć kierunku (czasowa) NIE ZACHODZI.**
- próg BŁĘDU: pomiar **unieważniony jako charakteryzacja percepcji** — 60% ticków cel
  poza kadrem z powodu usterki harnessu; 50.9 m to pomiar śledzenia nieobecnego celu.
  Liczby zachowane jako diagnostyka. Bramka błędu przechodzi na powtórkę z progiem
  BEZ ZMIAN (≤3.0 m p95).
- **wyjątek ekonomiczny (>6 m ⇒ C-sonda): NIE AKTYWOWANY.** Trzy racje, wzór errat
  programu: (a) reguła zakładała sprawny przyrząd celowania — struktura PRE §3 czyni
  etap A warunkiem wstępnym B, a A padł z przyczyny zewnętrznej; (b) jedyne nośniki
  śmierci (czasowe) zmierzone uczciwie i PASS; (c) istnieje pozytywny dowód, że percepcja
  na widocznym celu działa: **1.06 m @ d≈10 m** (sanity z boxem na intruzie, mti=True) —
  dokładnie ta wielkość, przed której złudzeniem reguła miała chronić. Od powtórki wyjątek
  obowiązuje normalnie.

Do księgi błędów CC: **P-2A-1 ✗** — pierwsze chybienie w kierunku PRZESZACOWANIA
(seria pięciu szła w niedoszacowanie komponentu uczonego; to jest inna klasa: infrastruktura).
Rozliczenie formalne przy zamknięciu nogi.

## §3. Naprawy (ratyfikowane tym aneksem; lista zamknięta)

- **N1 — jednostki yaw na granicy MAVSDK:** w bench_flight.py:398 wartość yaw przechodzi
  przez konwersję rad→deg (math.degrees) w TYM JEDNYM miejscu; kontrolery dalej emitują
  radiany (konwencja wewnętrzna bez zmian); komentarz przy linii: jednostki + odsyłacz do
  tego aneksu. To jest TRZECIA edycja bench_flight w nodze — jawne rozszerzenie listy
  PRE_2A §2-D6 o jeden hunk; diff verbatim w raporcie, nowy sha do FREEZE_2A.
  Test jednostkowy granicy: cmd yaw=π ⇒ pole 180.0.
- **N2 — bramkowanie REFRESH w feed_vision:** odświeżenie tracku WYŁĄCZNIE boxem, który
  (a) spełnia koniunkcję admisyjną (struktura∧MTI) ALBO (b) mieści się w oknie bramkowania
  wokół predykcji tracku (promień okna = decyzja wykonawcza, wartość do FREEZE_2A);
  brak zgodnego boxa ⇒ ZOH z rosnącym age (lustro semantyki dropu FeedB), NIGDY refresh
  z top-1 tła. Nowy sha feed_vision do FREEZE_2A. Testy: syntetyczny scenariusz
  „cel znika, tło strzela" ⇒ track starzeje się i wygasa, zero przeciągnięcia.
- **N3 — GZ_IP=127.0.0.1:** zostaje w driverze etapu (mitygacja dowiedziona, odwracalna);
  run_boot.sh NIETYKANY w tej nodze; wpis do backlogu harnessowego (przy następnym
  uprawnionym dotknięciu run_boot — razem z notą o yaw).

## §4. Sanity naprawy yaw (nowe, miara N1 — nie bramka percepcji)

W bootach powtórki: mediana |yaw_drona − az(do tracku)| w fazie orbit (po ustaleniu)
≤ 15°. To mierzy, że nos realnie śledzi; progi bramki A (pokrycie ≥0.90) pozostają
właściwym kryterium.

## §5. Powtórka etapu A + etap B (progi bez JEDNEJ zmiany)

A1b: c08_s03 · A2b: c11_s01 — reżim identyczny z PROMPT_2A_S2 §0/§1 (shadow, FEED=B,
kind=2a, driver etapu z GZ_IP). Bramki A: pokrycie ≥0.90 orbit i approach, dsw ≥0.90
(wariant det-5Hz dalej dostępny raz), quat. Etap B od nowa na nowych shadow-logach:
≥8 Hz ∧ ≤0.25 s ∧ ≤3.0 m p95; wyjątek >6 m ⇒ C-sonda obowiązuje normalnie. Budżet po
powtórce: 4 booty lotne z ≤31 (diagi 0-lotne poza licznikiem, precedens tej sesji).

## §6. Wykonanie (jedna sesja)

1. Bramka wejścia: origin/master zawiera 0dd749a; ahead pusty; porcelain pełny; FROZEN
   wykonaniem (piny, certy, sha — w tym bench_flight 2972a48a PRZED N1).
2. ARCH-1: ten plik → korzeń VERBATIM, pierwszy commit.
3. N1 + N2 + testy (jednostkowy granicy, scenariusz REFRESH, pełny pytest regresji);
   FREEZE_2A update (bench_flight po N1, feed_vision po N2, promień okna bramkowania).
4. Booty A1b/A2b + sanity §4 + etap B. REFUSE/breach: reguły S2 bez zmian.
5. STOP-2A2b: commit (edycje z diffami verbatim, FREEZE_2A, booty, shadow-logi, 6 sanity-PNG,
   `results/2A/RAPORT_2A_S2b.md` — bramki A/B z liczbami i klasyfikacją progową, sanity yaw,
   porcelain). Push = Olga; „wypchnięte" wystarczy. Dalej: **ANEKS_2A-2** (go/no-go na
   etap C). STOP.
