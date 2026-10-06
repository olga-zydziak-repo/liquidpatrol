# FREEZE_DET — zamrożenie przyrządu nogi DET (init S1, przed STOP-DET1)

CC-wykonawca · 06.10.2026 · PRE_DET §1/§4/§9. Zmiana któregokolwiek sha poniżej po
commicie S1 = nowa decyzja do ratyfikacji (ANEKS), nie poprawka. Wagi bazowe pobrane
PRZED jakimkolwiek treningiem (PRE_DET §4, ratyfikowana zmiana inwentarza wag);
trening zacznie się dopiero w S2 po ANEKS_DET-1.

## sha256 wag

| plik | sha256 | nota |
|---|---|---|
| `.b0deps/weights/yolov8n.pt` (baza fine-tune, ścieżka główna) | `f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36` | pobrane 06.10, assets v8.4.0, 6 549 796 B |
| `.b0deps/weights/yolov8s.pt` (baza eskalacji — RAZ, PRE §4) | `1f47a78bf100391c2a140b7ac73a1caae18c32779be7d310658112f7ac9aa78a` | pobrane 06.10, assets v8.4.0, 22 588 772 B |
| `.b0deps/weights/yolov8s-worldv2.pt` (detektor 2A — tylko shadow dolotu i T4) | `9b2c17ab6124a913e9b3a5c170617920d91b0f01111a8479da69f00e2cf27792` | FREEZE_2A verbatim |
| `net/frozen/det_v2.pt` **(FINALNY, S2)** | `775ead150b9937453168538cb97c55f69166e27ddc2d93f71b3710e0e49832ce` | = best.pt v8n seed1 (epoka 69/99, EarlyStop p30, 0.733 h, 0 fallbacków OOM); eskalacja v8s NIE zaszła (VAL p95 0.725/0.778 ≪ 3.0); TEST raz: **T2 pooled p95 1.365 m PASS**, T1 100.0/99.8 % |

## sha256 narzędzi

| plik | sha256 |
|---|---|
| `results/DET_RECON/tools/det_labels.py` (etykiety — FROZEN od PRE §1) | `8f7430cd5cd7a0ad851d851ebc810125762b4bb034026f185c06285b83db6693` |
| `results/DET/tools/det_replay.py` (przyrząd bramki T) | `de0feb37c2b99cb5d34d90007dd42cd003b67b0091995cd1b6f795805442a1c8` |
| `results/DET/tools/make_dataset.py` | `e958cc480684a44c2ec4e5e46b6c8928bdd13b2c457718051aece8386e5f2f7f` |
| `results/DET/tools/detS1_boot.sh` (driver zrzutu; jedyna zmiana vs stageA: --frames-hz 1000) | `a7313b3c4bc0849e39b87daa42ccbea078e5ec8d9d49b88ba8d6344fdcdb6542` |

## Walidacja przyrządu replay (T4, PRE §5 — wykonana w S1 PRZED dolotem)

Replay S2b-A2b z YOLO-World (9b2c17ab): **err p95 = 31.489 m ∈ [20.45, 81.8]
(= [0.5×, 2×] × 40.9 lotne) ⇒ PASS**; frakcja top-1-na-celu 10.4% — zgodność jakościowa
z lotem (~3–12%, S2b/recon); admisja strukturalnie obecna (ENTRY 2, FEED_EXPIRE 2,
fresh wyłącznie gate=mti). Zastrzeżenie jawne: klatki A2b zapisane w S2b z decymacją
2 Hz (dt 0.528 s) — replay waliduje się na nich, korpus dolotu jest 15 Hz.
Artefakt: `results/DET/t4_replay_A2b_world.json`.

## Runtime FEED=V2 (S3, ANEKS_DET-2)

**feed_sha_v2 = `8015bd12d7e8852bdc2e773d8b32c335a21752ea6209c6f245364809e4ed4a9c`**
(= sha256(params rdzenia FeedVision acc81df7 z podmianą detector→det_v2(yolov8n-ft),
weights_sha→775ead15…); JEDEN punkt prawdy: `harness/det_v2.feed_sha_v2()` — używany
przez proces percepcji i klienta).

| plik | sha256 (16) | rola |
|---|---|---|
| `harness/det_v2.py` | e801f7d592a023ed | wrapper det_v2 (guard SR-2, bez progu conf) + feed_sha_v2() |
| `harness/percep_proc.py` | 38a3a7656c53d857 | proces percepcji: rdzeń FeedVision READ-ONLY + DetV2, dedykowany egzekutor (N3-C), UDS |
| `harness/feed_vision_proc.py` | 79633489708d287d | klient FEED=V2 (zero rclpy, kontrakt R1 verbatim, log E2E) |
| `harness/feed_registry.py` PO wpisie V2 (additive) | ee1481f99729319d | rejestr B/V/V2 (bazowy 2629bc40 z FREEZE_2A) |
| `results/DET/tools/detS3_smoke.sh` | a3071542b2f2e6b8 | driver smoke (percep+bridge po armed, teardown SIGTERM) |
| `results/DET/tools/detS3_analyze.py` | 2d921776f84a2c6c | sędzia smoke (bramki runtime, żywość, S-BEZP) |
| `results/DET/tools/test_aneks_det2.py` | 3c185deea79ac772 | testy przed lotem (4: kontrakt/UDS/kolizja/cykl życia) |

## Przepis treningu (echo PRE §4, FROZEN)

ultralytics 8.4.115 (pin .b0deps) · torch 2.11.0+cu128 · `model=yolov8n.pt
data=dataset.yaml(nc=1) epochs=100 imgsz=640 batch=16 seed=1 deterministic=True
device=0 workers=4 patience=30 cache=False`; reszta = domyślne 8.4.115; fallback OOM
batch 16→8 zliczony; jeden run/architekturę; eskalacja v8s RAZ tylko po fail progu
błędu na VAL. Split FROZEN (PRE §3): TEST c06+c09 · VAL c02+c04 · TRAIN reszta.
