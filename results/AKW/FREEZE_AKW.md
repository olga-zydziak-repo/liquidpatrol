# FREEZE_AKW — zamrożenie przyrządu nogi AKW (init przy S1, PRE_AKW §2 / PROMPT_AKW_S1 §1)

Wykonawca · 09.10.2026 · po ratyfikacji PRE_AKW (Olga, 09.10.2026) i PROMPT_AKW_S1;
ARCH-1 = commit b1f77856 (PRE_AKW.md VERBATIM, pierwszy commit sesji).

## Parametry profilu skanu (FROZEN — zmiana wartości = ANEKS, nie env)

| parametr | wartość |
|---|---|
| ω skanu | **30.0 °/s**, ciągły, jednokierunkowy CCW (konwencja kodu: yaw atan2 ROSNĄCY, jak orbit_executor CCW) |
| ψ_last (doprecyzowanie wiążące PROMPT §1) | ostatnio WYEMITOWANY yaw z każdego ticku (track: atan2 delegata; skan: własna rampa) |
| dwell po wejściu w hold | **2.0 s** trzymania ψ_last, potem rampa ψ(t)=ψ_last+ω·t_skanu |
| rampa | liczona wewnętrznie UNWRAPPED; **emisja wrapowana do (−π, π]** (granica MAVSDK w benchu bez zmian) |
| reset() | zeruje stan skanu i **ψ_last = 0.0** (pierwszy hold epizodu ⇒ dwell na 0.0, rampa od 0) |
| zegar profilu | now_s pętli (ten sam co w step delegata) |
| env `AKW_SCAN_DPS`/`AKW_DWELL_S` | WYŁĄCZNIE odczyt diagnostyczny; loty NA WARTOŚCIACH Z KODU — driver bramkowy ODMAWIA przy ustawionych |

## Sha zamrożone (sha256)

| plik | sha256 |
|---|---|
| `r03/controllers/akw_scan.py` (wrapper, NOWY) | `2237cc7ca10fc696ae4e07214716f0be16c76847422108ab82ba8fcf57cd06dd` |
| `r03/controllers/__init__.py` (PO wpisie net_akw — 2 linie additive) | `4f58d204630b9cf8db3bfb9a98b480c7c24552c8c7632eee9373c18b7cbd656a` |
| `results/AKW/tools/akwS1_boot.sh` (driver, kopia detS4_boot; jedyna zmiana funkcjonalna: CONTROLLER=net_akw; dodatki niefunkcjonalne jawne: KIND=akw [etykieta finalize], guard ODMOWY przy env AKW_*, blok `akw` w manifeście, ścieżki results/AKW/camp) | `fcff9b30caed4345bc3bf032eddfd658028cc5c3e36c499390ffe7b629a711f3` |
| `results/AKW/tools/akw_analyze.py` (analiza, kopia detS4_analyze + blok akw/smoke_gates/yaw_sanity_ulog) | `e9b3bdfbfb44965671beb35ceb6502f0e7edfddd56231ee7d41d3fa86ff5377b` |
| `results/AKW/tools/test_pre_akw.py` (testy przedlotowe §2) | `6ee42fd59aa8c50cd05fa0e57b711f1e31d24edeb27775d933101210d3e5fa87` |

## Dziedziczone VERBATIM (bajty bez zmian — edycja = STOP)

FREEZE_DET w całości (results/DET/FREEZE_DET.md) · piny 5/5 (k1_shield_pins: shield
1c584964 · config 4c440e42 · gate_run 5647ae20 · base 7fc45cf2 · safe_descend e3c1040b)
· certy 9/9 · bench_flight `05137098` · bench_judge `8ec0fcfb` · feed_vision `acc81df7`
· det_v2.pt `775ead15` · det_v2.py `e801f7d5` · percep_proc `38a3a765` ·
feed_vision_proc `79633489` · feed_registry `ee1481f9` · ncp `0337d5ea` ·
net_controller `e8c1b658` (wrapper go IMPORTUJE, nie edytuje) · feed_sha_v2 `8015bd12`
(meta percep_feed, do manifestów V2).

Weryfikacja przy S1 (wykonaniem): piny 5/5 PASS, certy 9/9 PASS, sha 9/9 zgodne.
Testy przedlotowe: **12/12 PASS** (pass-through bajtowy: 5714 tików ramienia B +
3754 tików demo V2 + 411 ważnych tracków V2 wprost z percep_feed r1_V2; profil
[dwell/rampa 30°/s/wrap ±π/wznowienie od ψ_last/reakwizycja/reset]; rejestr +
regresja "net"). Istniejące pytest: **210 passed, 0 failed** (pełna lista suit
w RAPORT_AKW_S1; r01/brake_test.py i r02/test_deadman.py = skrypty zależne od rclpy,
nie kolekcjonują się gołym pythonem — stan habitatu sprzed nogi, bez zmian).
