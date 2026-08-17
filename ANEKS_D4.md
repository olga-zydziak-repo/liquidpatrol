# ANEKS_D4 — DEMO-B B5 wznowienie: ratyfikacja rdzenia mti_flight (PROMPT_D_BUILD_5R2)

Data: 2026-08-17. Aneks do `ANEKS_D1/D2/D3`. Wklejenie PROMPT_D_BUILD_5R2 przez Olgę = ratyfikacja
tego aneksu. **PROMPT_D_BUILD_5R nie był wykonywany i zostaje ZASTĄPIONY przez 5R2** (odnotowane).

## Decyzje ratyfikowane

- **(a) Manifest-po-arm ZATWIERDZONY** jako obowiązująca semantyka §0: `gate_run_r02._emit_act_manifest`
  wołany PO `bring_up`/arm (pole `armed_before_manifest`). **Envfail1–6 = NIE-próby** (dron nigdy nie
  uzbrojony); **licznik prób wszystkich aktów = 0**.
- **(b) Ścieżka wznowienia = opcja 2:** rdzeń lotu LIVE przeniesiony na **topologię `mti_flight`** —
  tę, w której arm i percepcja live DOWIEDZIONE w REGATE. Powrót do topologii scharakteryzowanej,
  nie nowa konstrukcja. **Różnica zmierzona:** `exec_lib.Mav`/`bring_up` = ten sam warunek health
  (`is_global_position_ok ∧ is_home_position_ok`) ale timeout **30 s** i BEZ arm-retry; `mti_flight` =
  timeout **90 s** + pętla arm-retry (60×), arm PRZED załadowaniem YOLO (redukcja kontencji EKF).
- **(c) Higiena środowiska** przed każdą serią bootów: kill stale gz/px4/ros2/detector + zrzut `ps`.
- **(d) Próby bez kontencji fabryki**, `contention: none` w manifeście + nota uczciwości: okno ENTRY
  [23, 33.87] z REGATE (POD kontencją) = granica KONSERWATYWNA.
- **(e) FILM_CAPTURE aktywne PRZED emisją manifestu** (pełne pokrycie aktu klatkami).
- **(f) Zmiany kamery/światów/spec/sędziego/percepcji — POZA zakresem** (ścieżka STOP → dowód →
  adnotacja → ratyfikacja → nowe hashe).
- **(g) Kryterium stabilności i śmierci PREREJESTROWANE** (T1): seria = **3 kolejne czyste booty LIVE**
  (łącze MAVSDK → health → arm → takeoff → ≥10 s hover → czysty shutdown); log czasu-do-health per boot.
  3/3 ⇒ odblokowane §1. **Śmierć: 3 serie bez 3/3 ⇒ STOP.** **Fallback (falsyfikacja topologii):
  jeśli rdzeń mti_flight nie ustanowi łącza MAVSDK w ≤2 bootach PIERWSZEJ serii ⇒ STOP natychmiast**
  (hipoteza „to topologia" obalona → opcja 1 osobnym promptem; ścieżek nie mieszać, SR-H3).

## Kontrakty NIEZMIENIONE (T0)

Schemat trace v2; manifest (pola + emisja PO arm); **sędzia `79b1e936…` z niezmienionym wejściem**;
token path B1 (assert A4 `token_gated=True`, `admission_seq`, beaty operatora A5); choreografia ze spec
(teleport f(sim_t)); **światy zamrożone** (hashe A1 `d7e3db24`/A2 `dd0c85e2`/A3 `486a0cea` bez zmian).
