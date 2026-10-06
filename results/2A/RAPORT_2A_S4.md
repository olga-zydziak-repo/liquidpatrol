# RAPORT_2A_S4 — N3-C w locie + C-sonda bezpieczeństwa WYKONANA (C1r + C2): zawieranie trzyma pod kłamiącą percepcją

CC · 06.10.2026 · wykonanie ANEKS_2A-3 §5 · commity sesji: 583bc45 (ARCH-1) + d85c678 (N3-C) + ten (STOP-2A4).

## §0. TL;DR

**Sonda wykonana w całości: 2/2 booty VALID V2′ i WAŻNE instrumentowo (żywość §4 ALIVE ×2).
S-BEZP: breach R_E = 0 ×2, REFUSE = 0 ×2 (żadna gałąź), REFUSE(POS) brak.** N3-C działa
w locie (feed żywy: 306/592 klatek przetworzonych; w C1 było 0). Dwa jakościowo różne
przebiegi pod FEED=V:
- **C1r (c11_s01):** brama D2 nie wpuściła NICZEGO (0 ENTRY, koniunkcja central∧mti
  4/256 boxów, nigdy k=3 pod rząd) ⇒ dron ślepy w hold na home cały epizod. Zawieranie
  trywialne (r_max 0.09 m).
- **C2 (c08_s03):** pełny scenariusz „lying feed" — ENTRY na fantom tła w t_rel 2.4 s,
  track kłamał do **53.0 m** (146 ticków z celem POZA R_E=32), NCP gonił w approach
  z |cmd|≈3.0 m/s i wspiął się o ~10 m — a mimo to **r_est_max = 12.22 m (margines do
  R_E: 19.78 m), zero breach, zero REFUSE**. Mechanizm zawierania NIE-osłonowy:
  selektywna brama REFRESH (N2) głodzi track (age>1.0 s ⇒ konsument tnie na hover-hold),
  pogoń jest przerywana zanim się rozpędzi; θ_age 3.0 s zabija track fantoma (FEED_EXPIRE
  t_rel 42.2) i dron wraca/stoi. Osłona nie musiała ani razu strzelić.

## §1. Bramka, ARCH-1, N3-C

- Bramka §5.1 PASS: origin/master zawierał f8a0f9c i 08fb987 (push Olgi), ahead 0,
  porcelain pusty, FROZEN sha wykonaniem (feed_vision jeszcze 0a975121 przed N3-C).
- ARCH-1: `ANEKS_2A-3.md` verbatim w korzeniu, commit 583bc45.
- **N3-C (commit d85c678):** feed_vision sha `0a975121…` → `acc81df7…`; **feed_sha BEZ
  ZMIAN `d6a3367b…`** (params nietknięte — odnotowane w FREEZE_2A). Diff verbatim:
```diff
@@ -289,6 +289,13 @@ class FeedVisionLive(FeedVision):
         self._node.create_subscription(VehicleAttitude, "/fmu/out/vehicle_attitude",
                                        self._on_att, qos)
         self._node.create_subscription(Image, self.image_topic, self._on_image, qos_be())
+        # ANEKS_2A-3 N3-C: DEDYKOWANY egzekutor dla węzła feedu. rclpy.spin_once(node)
+        # używa egzekutora GLOBALNEGO, który w bench_flight już spinuje wątek EKF
+        # (bench_flight.py:248-251) ⇒ 'Executor is already spinning' i śmierć wątku _spin
+        # pierwszym wywołaniem (boot C1 sondy, RAPORT_2A_S3 §2b; repro probeC_repro_executor).
+        from rclpy.executors import SingleThreadedExecutor
+        self._ex = SingleThreadedExecutor()
+        self._ex.add_node(self._node)
         self._running = True
         self._th = threading.Thread(target=self._spin, daemon=True)
         self._th.start()
@@ -296,7 +303,7 @@ class FeedVisionLive(FeedVision):
     def _spin(self):
         import rclpy
         while self._running and rclpy.ok():
-            rclpy.spin_once(self._node, timeout_sec=0.05)
+            self._ex.spin_once(timeout_sec=0.05)
```
- Test `results/2A/tools/test_aneks3.py` PASS 1/1 (kolizja na PRAWDZIWEJ klasie:
  wątek-lustro bench na egzekutorze globalnym + FeedVisionLive z dummy-detektorem —
  wątek _spin żyje, callbacki pos/att/obraz dochodzą; kontrola negatywna = boot C1 +
  repro `collision`). Regresja lokalna feed_vision 15/15 (test_aneks1 + test_smoke_s1).

## §2. Booty sondy (driver v2, reżim ANEKS_2A-2 §3 bez zmian)

| | C1r | C2 |
|---|---|---|
| scenariusz / ep | c11_s01 / 11 (seed 1, CCW) | c08_s03 / 32 (seed 3, CW) |
| VALID V2′ | TAK (dsw 0.9588, stall 0.0) | TAK (dsw 0.9502, stall 0.0) |
| **żywość §4 (30 s)** | **ALIVE** (195 klatek, 0 fresh) | **ALIVE** (181 klatek, 72 fresh) |
| klatki / boxy / fresh (epizod) | 306 / 256 / 0 | 592 / 504 / 101 |
| ENTRY / FEED_EXPIRE | 0 / 0 | 2 (t_rel 2.4, 75.9) / 1 (42.2) |
| breach / REFUSE | 0 / 0 | 0 / 0 |
| r_est_max / margines do R_E | 0.09 / 31.91 m | **12.22 / 19.78 m** |
| t_entry (dband) | — (reguła 40 s) | 2.76 s (pełny epizod ~73 s) |
| d_min do intruza GT | 1.60 m (przeszedł obok ślepego) | 6.97 m |

Oś czasu jak w C1 (armed → bridge → offboard → make_feed in-process → epizod); mostek
żył (naprawa drivera §2a S3 potwierdzona: `ros2 topic list` pełny, bridge log czysty).
GZ_IP=127.0.0.1; host czysty (proc_gate PASS ×2, cooldown ≥300 s między bootami).

## §3. S-BEZP (kryterialne) — WERDYKT SONDY

**breach R_E = 0 w obu bootach (wymagane 0 — SPEŁNIONE). REFUSE = 0, więc rozkład per
gałąź pusty; REFUSE(POS) nie wystąpił.** Oczekiwany-możliwy REFUSE(GEOFENCE) na pogoni
za fantomem NIE wystąpił, bo pogoń nigdy nie doszła do pasma geofence'u — zatrzymywała
ją własna dynamika toru percepcyjnego (§4/C2). Zdanie pomiarowe: **system pozostał
bezpieczny, gdy percepcja aktywnie sterowała ku fantomom do 53 m (poza kopertą R_E=32)
— z zapasem 19.78 m i bez potrzeby interwencji osłony.**

## §4. S-MISJA (opisowe) + mechanizmy

**C1r — tryb „brama trzyma wszystko":** przy zawisie na home klatter naziemny daje boxy
głównie krawędziowe (181/256 poza edge-margin 0.10), MTI koincyduje rzadko (10/256),
koniunkcja central∧mti 4/256 i nigdy 3 pod rząd ⇒ 0 admisji, track nigdy valid, NCP hold
789/789 ticków. Spójne z S2-A2 (0/413) i nogą D §8a: bez ego-motion MTI nie łapie tła.
Conf tła p50 0.0044. Fantomy wymagają ruchu własnego — stąd asymetria C1r/C2.

**C2 — tryb „lying feed" (właściwy pomiar):** ENTRY t_rel 2.4 s → track fantoma, err vs
GT p50 9.86 / max 48.6 m; |fantom| od home p50 6.6 / p95 35.3 / **max 53.0 m** (fantom
max NED [25.7, −46.4, 3.5] @t_rel 30.1); 146 ticków z celem poza R_E. Dron: approach 258
+ orbit 379 ticków, wspiął się z −7.15 do −17.55 m, r_est rosło 8.4 → 10.9 → **12.22 m**
(okna 10-sekundowe), przy fantomie>R_E komendował |cmd_h| p50 2.99 (≈V_MAX). Potem
spadek do r≈3.2 i stabilizacja: **frakcja track_valid 1.00 → 0.22 → 0.00** (okna 30–50 s),
FEED_EXPIRE t_rel 42.2 (θ_age 3.0 s), próba re-ENTRY dopiero 75.9 (koniec epizodu).
**Mechanizm zawierania (nazwany):** brama REFRESH (N2) przepuszcza świeże rzadko
(101/504 boxów; gate mti 83 / window 18), track regularnie przekracza age 1.0 s ⇒
konsument (net_controller) tnie na hover-hold ⇒ pogoń jest POSZATKOWANA (hold 798/1435
ticków mimo locka przez pół epizodu); sufit θ_age dobija track zanim dron zajdzie
daleko. Selektywność bramy — ta sama, która w S2b położyła literę kadencji B(i) —
działa tu jako mimowolny ogranicznik pogoni za fantomem. To obserwacja opisowa
(1 boot), nie roszczenie kanonu.

## §5. Prowieniencja i odchylenia

- Manifesty: net_arm=ncp, weights_sha 0337d5ea…, feed_sha d6a3367b… ×2; feed_v.jsonl
  sha w manifestach (C1r 92187d65…, C2 cb748f47…); rozbiory `probeC_summary.json`
  per boot (narzędzie probeC_analyze z polem `feed_liveness_aneks3`).
- Nota numpy ławki 2.4.4 pod B0SP (jak S3, precedens finalize) — bez zmian.
- **Odchylenie opisowe (nie bramkowane):** kadencja przetwarzania klatek in-process
  6.7–7.2 Hz vs 14.7 Hz shadow-procesu z S2b — kontencja jednego wątku egzekutora feedu
  (pos ~100 Hz + att ~100 Hz + obraz 15 Hz, jeden callback na spin_once) + GIL z pętlą
  20 Hz. Dla sondy bez znaczenia (S-MISJA opisowe); dla ewentualnej przyszłej nogi
  percepcji — wpis do katalogu przy „detektor-v2".
- Driver: jedno `Killed` w logu C1r to kill -9 bridge'a przez teardown drivera (zamierzone).

## §6. Budżet i status

Booty lotne VALID: 4 (S2/S2b) + C1 + C1r + C2 = **7 z ≤31** (zgodnie z ANEKS_2A-3 §3).
Porcelain przy STOP: artefakty sondy + raport (commit STOP-2A4). Push = Olga.
Następne: **ANEKS_2A-4** — zamknięcie nogi (werdykt całości; kanon z trzema trybami
percepcji: zdrowa-w-kadrze [S2b: limituje dokładnością], kłamiąca [C2: zawieranie
trzyma, 19.78 m zapasu], martwa [C1: fail-silent→fail-safe]; KSIĘGA, CO-2A;
detektor-v2 do katalogu). STOP.
