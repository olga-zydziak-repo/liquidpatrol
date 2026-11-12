# STOP-NAD2-4-INTRUZ — lot długi wstrzymany przed lotem: wzór ruchu intruza c10_s01 kończy się po 200 s, a powtarzanie wymaga zmiany poza dopuszczoną w §0.4

12.11.2026 · wykonawca · PROMPT_NAD2_S4 (sha256 a2740a4a PASS). **0 bootów (0/2). Kod bez zmian.**

## Bramka §0

1. origin/master == 0d19996f ✓; ANEKS_NAD2-2 byte-check sha256 8b8d8d30 PASS; commit 1 [CO-NAD2-2] `136cce32`
   (aneks w korzeniu, KSIĘGA §6, KIERUNKI §7 append-only).
2. Sygnał Olgi „lot długi NAD2” ✓.
3. Commit 2 [S4-KSIEGA] `87d1c0f3` — P-NAD2-L1…L4 przed lotem.
4. Zmiana env w `nad2_flight.py` — **niewykonana** (STOP poniżej przed jakąkolwiek zmianą kodu).

## Konflikt (§R „Ruch intruza” vs §0.4)

- Epizod c10_s01 = `episodes[10]` manifestu `results/NADIR/s4/scenario_manifest_s4.json` (sha w strażniku `nad2_boot.sh`),
  `ep_dur_s` 200 s, 13 odcinków (ostatni 188.68–205.29 s).
- `harness/intruder_motion.py` (`run_episode`) pcha `set_pose` tylko do `t_rel ≥ ep_dur_s` (200 s), potem przestaje —
  intruz **stoi** w (−4.04, 2.11, 10) m. Lot długi trwa ok. T_entry + 30 + 600.5 ≈ 655 s od startu epizodu ⇒ ok. 455 s
  bez ruchu. Wzór kończy się przed 600 s.
- §R dopuszcza wyłącznie powtarzanie tego samego wzoru, inaczej STOP przed lotem. Powtarzania nie da się zrobić
  zmianą dopuszczoną w §0.4 (env w `nad2_flight.py`). Potrzebna byłaby jedna z poniższych zmian:
  - (a) `harness/intruder_motion.py`: `t_rel mod 200` — zmiana harness (zamrożone bd975df5);
  - (b) nowy manifest z epizodem c10_s01 sklejonym ×4 (800 s) — nowa sha, więc zmiana stałej `S4MAN`/`S4MAN_SHA`
    w `nad2_boot.sh` albo env manifestu w boocie;
  - (c) ruch powtarzany przez driver (`nad2_flight.py` przestawia `t0_sim` w pliku kontroli co 200 s) — to też zmiana
    w `nad2_flight.py` ponad env z §0.4.
- Każde powtórzenie ma **skok pozy** z (−4.04, 2.11) do startu (−15.0, 0.0): ok. 11.2 m teleportu intruza co 200 s,
  czyli trzy skoki w locie. Skok widzą percepcja i track (pasmo) — trzeba go nazwać w raporcie.

## Drugi drobiazg (do tej samej decyzji)

`results/NAD2/tools/nad2_ulg.py`: `LIMIT = 3 MB` (asercja). §R pozwala na wyciąg do 10 MB. Wyciąg c10_s01 z bramki
ma 1.26 MB przy ok. 3.5 min lotu, więc przy ok. 13 min będzie ok. 4–5 MB > 3 MB. Kolejka S3 traktuje przekroczenie
(AssertionError) jako „ponad_limit”. Do lotu długiego potrzebny jest limit 10 MB — jako parametr narzędzia
(np. env) albo przez zmianę stałej.

## Propozycja (decyzja CC/Olgi; nic nie zmienione)

- Ruch: (c) albo (a) z nazwanym skokiem 11.2 m co 200 s; albo (d) zgoda na intruza stojącego po 200 s
  (bez powtarzania, nazwane w raporcie) — §R tego dziś nie dopuszcza.
- ULG: limit 10 MB przez env w `nad2_ulg.py` (domyślnie 3 MB — bramka bez zmian).
- Po decyzji: diff + test wartości domyślnych (§0.4), potem lot (budżet 0/2).

**Sygnał: STOP-NAD2-4-INTRUZ.**
