# ANEKS_SKAN2-0 — warunek wejścia zegara po STOP-SKAN2-ZEGAR: skoki CLOCK_REALTIME do 1.2 s dopuszczone, bo nic w torze lotu nie czyta zegara ściennego; V2′ bez zmian

CC · 1.11.2026 · łańcuch SKAN2, po STOP-SKAN2-ZEGAR (budżet 0/8, commity
585f4d14 i 522c544c lokalnie). Zastępuje wyłącznie §0.4 PROMPT_SKAN2_S1.
PRE_SKAN2 (7305f4d7…8700f) bez zmian; kryteria, werdykty i budżet bez zmian.

## §1. Fakty

- Próbnik 60 s na świeżej sesji WSL (start 23:17:47, po `wsl --shutdown`):
  2 skoki realtime względem monotonic, +1.010 s i +1.019 s, odstęp 33.3 s;
  między skokami zegary idą równo. Dowód: `results/SKAN2/s1/zegar_pusty_host.jsonl`.
- CC z repo, `rtf_stream.jsonl` (przyrost wall − przyrost sim > 0.3 s między
  sąsiednimi próbkami): **PERC2 S2 z 25.10 (bA_c08, bB_c1011) — zero skoków
  okresowych**, tylko po dwa zdarzenia 0.4–0.6 s przy sim ≈ 110 s w obu
  bootach. WK wk0_b1 i WK2 g0_b1 (później): 17 zdarzeń, 2.2–2.8 s co ~32 s.
  Zjawisko pojawiło się po 25.10, ma zmienną amplitudę (2.2–3.3 s w WK-IV,
  dziś 1.0 s), a `wsl --shutdown` go nie usuwa. Przyczyna po stronie Windows
  nie jest zmierzona i ten aneks jej nie ustala.

## §2. Co w locie czyta CLOCK_REALTIME (plik:linia, FETCH_HEAD 4a319742)

- Pętla benchu: zegar symulacji (`bench/bench_flight.py:110`) i monotonic
  (`:103`, `:114`, `:225`).
- Percepcja: czas klatki = sim_t (`harness/feed_vision.py:118-154`), pomiary
  wewnętrzne na monotonic (`harness/percep_proc.py:133-159`).
- Kontrolery (`r03/controllers/*`, w tym net_skan2): wyłącznie `now_s` pętli.
- **Zegar ścienny czyta tylko próbnik RTF** (`rtf_stream.wall`), a z niego
  ważność V2′ (`bench/bench_judge.py:50-72`, `bench/campaign_analyze.py:30-32`).

Skok realtime nie zmienia więc niczego, co leci, liczy tor albo steruje
nosem. Zmienia tylko pomiar ważności. Jeden skok 1.0 s to jedna próbka deep
o długości ~1.0 s wall: limit `longest_stall_s` 1.5 s jest zachowany, a dsim/dwall
epizodu przy ~3 skokach na ~110 s wynosi ≈ 0.97 przy progu 0.90.

## §3. Nowy warunek wejścia (zastępuje §0.4 PROMPT_SKAN2_S1)

1. Przed bootem 1 i przed bootem 2: próbnik dwuzegarowy 60 s na pustym hoście.
   **Wejście ⇔ każdy skok ≤ 1.2 s ∧ najwyżej 3 skoki w 60 s.** Margines 0.3 s
   do limitu stalla V2′. Skok > 1.2 s albo więcej niż 3 skoki ⇒
   STOP-SKAN2-ZEGAR (to nie jest boot, budżetu nie rusza).
2. W locie V2′ zostaje literą: wall z rtf_stream, sędzia 8ec0fcfb, parametry
   D9. `zegar2.jsonl` biegnie z bootem. W raporcie każde zdarzenie deep, które
   pokrywa się w czasie ze skokiem w `zegar2.jsonl`, dostaje opisowo etykietę
   „artefakt zegara”. Etykieta niczego nie unieważnia ani nie ratuje.
3. Epizod nieważny V2′ ⇒ jedno dolecenie, liczone do budżetu (jak w prompcie).
   Drugi epizod nieważny V2′ przez skok > 1.5 s ⇒ STOP-SKAN2-ZEGAR.
4. Porównywalność z linią bazową: PERC2 S2 leciał na czystym zegarze. Skoro
   nic w torze lotu nie czyta realtime (§2), porównanie A/B zostaje w mocy.
   Raport podaje reżim zegara obu kampanii jednym zdaniem.

## §4. KSIĘGA (dopisek przy CO-SKAN2 na końcu łańcucha)

✗ kalibracyjne CC: §0.4 PROMPT_SKAN2_S1 zakładał, że `wsl --shutdown` usuwa
skoki zegara (na podstawie remedium z ANEKS_WK4-0). 1.11 to założenie okazało
się fałszywe. Bramka wejścia była zbyt ostra wobec tego, co faktycznie czyta
zegar ścienny; zabrakło sprawdzenia §2 przed jej napisaniem.

## §5. Wykonanie

1. Zapisz ten aneks verbatim do korzenia jako `ANEKS_SKAN2-0.md`; byte-check
   sha256 z wiadomości CC (ARCH-1). Commit razem z dowodem
   `results/SKAN2/s1/zegar_pusty_host.jsonl`:
   `SKAN2 [ANEKS-0]: warunek wejścia zegara (ANEKS_SKAN2-0), dowód próbnika`.
2. Narzędzia S1 i `kontrola_perc2.json` zostają nieśledzone do commita 3,
   jak w prompcie.
3. Próbnik 60 s według §3.1, potem boot 1 według §3 PROMPT_SKAN2_S1. Reszta
   promptu bez zmian.
