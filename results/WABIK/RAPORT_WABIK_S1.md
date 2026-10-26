# RAPORT_WABIK_S1 — sesja S1 nogi WABIK: wabik w świecie, klasyfikator FROZEN, smoke z kotwicą — STOP-WABIK1

CC-wykonawca · 26.10.2026 · wykonanie PROMPT_WABIK_S1 (PRE_WABIK ratyfikowany,
byte-check PASS `f2cbf63b…cf3c79`, commit 1 = `bf776d20`). **Budżet S1: 2/≤3
bootów (s1_smoke, s1_rozdzielony — drugi boot z zapasu, powód niżej); oba
uzbrojone: breach 0 / REFUSE 0.** Zero dotyku zamrożonych (spawn runtime;
intruder_motion/manifest/sędzia/percepcja nietknięte); nowe pliki wyłącznie
korzeń (PRE) + `results/WABIK/**`.

**WYNIK GŁÓWNY: narzędzia działają, śmierć S1 NIE zachodzi, a smoke dostarczył
ZNALEZISKO PIERWSZEJ WAGI (pierwszy pomiar trackera przy dwóch obiektach
w programie):**

1. **Konfiguracja A (s1_smoke): wabik ŁAMIE sędziowanie intruza przy orbicie.**
   Intruz-kotwica c08_s01 + wabik W-LOITER (r=10, sektor 140–220°): sędzia
   FROZEN (GT manifest, świadek 0/3310) dał **D6 FAIL [b_frac]** — frac_band
   0.758, d_min 5.173 (historycznie: PASS, d_min 6.854 S2-PERC2 / 6.877 era
   DEMO-C). Mechanizm NAZWANY pomiarem: single-target tracker + REFRESH
   admituje każdy admitowalny box; dron ORBITUJE intruza, więc kamera
   cyklicznie omiata wabika (433/1423 klatek w stożku; **wabik SAM w stożku:
   170 klatek — admisja 170/170 box+mti+fresh**, wizualia identyczne) ⇒
   **track przeskakiwał na wabika w 364/1430 ticków (25.5 %), wszystkie
   w fazach werdyktowych** — dron był wyciągany z pasma 6–10 m intruza.
   „Rozdzielenie azymutalne" NIE wystarcza przy orbicie — kamera i tak omiata
   pełny okrąg.
2. **Konfiguracja B (s1_rozdzielony): istnieje konfiguracja czysta ⇒ śmierć S1
   nie zachodzi.** Intruz stacjonarny c00_s01 (r=15) + ten sam wabik W-LOITER:
   separacja dron↔wabik > zasięg detekcji przez cały epizod ⇒ **zero klatek
   wabik-sam-w-stożku admitowanych, przeskoki 0/1455, kotwica czysta: D6 PASS,
   d_min 8.078, frac_band 1.000, świadek 0/3367**.
3. **Klasyfikator zachował się poprawnie na obu bootach** (diagnostycznie,
   mieszany track w A): etykieta „–" (podłoga dh_min=1.7 zablokowała; n_W=9) —
   mimo przeskoków nie oflagował epizodu z poważnym intruzem.
4. **Konsekwencja dla S2 (litera PRE):** T-W-TP/T-W-FP/T-W-ORB latają
   z JEDNYM obiektem naraz — przeskoki nie blokują S2. Zjawisko przeskoków =
   zmierzony substrat przyszłej pozycji katalogowej (multi-target/tożsamość
   tracka) — decyzja nazewnicza przy ANEKS_WABIK-1 (CC).

## §1. Bramki i reżim — PASS

Byte-check PRE `f2cbf63b…` ✓ (commit 1 `bf776d20`, osobny). origin=c09c38cb ✓,
gate pusty ✓, porcelain czysty (poza nazwanymi `??` wideo DEMO_C) ✓; piny 5/5,
certy 9/9, FROZEN komplet + FREEZE_PERC2_OPS. **Reżim OPS w obu bootach:**
pin model.sdf (2× OK) + world_hash przed stackiem, profil FastDDS a68a450b
(GUARD sha w driverze), **sonda kadencji preflight PASS 2/2** (dt_p50 0.068;
wynik w manifestach: `wabik.sondy[]`, `uzbrojony_po_sondzie`). Kadencja lotu:
dt_p50 0.068 / frac 0.0 (oba epizody).

## §2. Narzędzia i FREEZE (commit tej sesji)

- `tools/wabik_motion.py` **e690850c** — pusher wabika (GzPoseClient
  name="wabik" READ-ONLY importem; set_pose 20 Hz; GT = `wabik_motion.jsonl`
  cmd/applied — **POZA sędzią**); oryginalny intruder_motion.py NIETKNIĘTY.
- `tools/wabik_s1_boot.sh` — driver-kopia reżimu perc2_s2/democ + DRUGI spawn
  EntityFactory + start pushera; dowód spawnu `gz model --list` → manifest
  (`spawn_proof_gz_model_list`: oba booty z "wabik" i "intruder").
- `wabik_manifest.json` **046fa12b** (gen: `tools/wabik_manifest_gen.py`
  ccdce1b9) — trajektorie W-LOITER / W-STYCZNY / W-ZBLIŻ-ODSKOK + scenariusze
  M-ŁUK / M-POD-ORBITĄ (parametry liczbowo w FREEZE_WABIK; wszystkie v ≤ 1.0;
  polilinie w semantyce istniejących segmentów; BENCH_MANIFEST dopiero w S2 —
  smoke leciał na manifeście DOMYŚLNYM, stąd kotwica 1:1).
- `tools/wabik_sig.py` **475c972e** — klasyfikator progowy (sidecar, posthoc
  z percep_feed; NIE steruje). **Progi FROZEN w `FREEZE_WABIK.md` (napisany
  PRZED smoke)**: V_MOVE 0.30 / V_RAD_MAX 0.30 / DH_MIN_FLOOR 5.0 / R_ZONE 18
  / T_FLAG 12.0 s / WIN 1.0 s — uzasadnienie per cecha z kwantyli NULL
  w FREEZE; kalibracja WYŁĄCZNIE na NULL: **NULL-scan @T=12: etykieta-
  kiedykolwiek 23/115 (20.0 %), końcowa 13/115 (11.3 %)** — dekompozycja:
  19/23 cele v=0.5 wędrujące (zmierzona granica NIEROZRÓŻNIALNOŚCI z PRE §1),
  4/23 v=1.0 z późną akwizycją; etykieta AKTYWNA z ODWOŁANIEM przy złamaniu
  podłogi dh_min<5 (semantyka stanu bieżącego). T_FLAG=12 s = maksimum
  zgodne z limitem TP ≤15 s z PRE §3.2 (NULL-scan pełny w FREEZE).
- `tools/wabik_smoke_analyze.py` — kotwica sędzią (import przyrządu
  perc2_s2_analyze) + stożki/przeskoki (wyniki: `s1/*/wabik_smoke.json`).

## §3. Budżet per boot (deklaracje)

| boot | konfiguracja | powód | wynik |
|---|---|---|---|
| 1 s1_smoke | c08_s01 (eid 8, radialny v=1.0) + W-LOITER r=10 @140–220° | smoke z PROMPT §1.6 | spawn OK, sonda PASS, VALID, breach/REFUSE 0; kotwica ZŁAMANA (pomiar §gł.1) |
| 2 s1_rozdzielony | c00_s01 (eid 0, stacjonarny r=15) + W-LOITER j.w. | zapas użyty świadomie: śmierć S1 wymaga „w ŻADNEJ konfiguracji" — rozstrzygnięcie wymagało drugiej konfiguracji o separacji > zasięg | spawn OK, sonda PASS, VALID, breach/REFUSE 0; kotwica CZYSTA, przeskoki 0 |

Trzeci boot zapasu NIEUŻYTY. Śmierć S1 (PRE §2.4): **NIE zachodzi** — spawn
działa bez dotyku zamrożonych, a tracker utrzymuje intruza w konfiguracji
rozdzielonej (B); litera „przeskoki uniemożliwiają sędziowanie" zaszła
WYŁĄCZNIE w konfiguracji ekspozycji cyklicznej (A) i jest zmierzona, nazwana
i obejściowa w S2 (jeden obiekt naraz — plan PRE §3 bez zmian).

## §4. Artefakty

`results/WABIK/`: **FREEZE_WABIK.md** · **RAPORT_WABIK_S1.md** (ten plik) ·
`wabik_manifest.json` · `tools/` (wabik_motion, wabik_s1_boot, wabik_sig,
wabik_manifest_gen, wabik_smoke_analyze) · `s1/s1_smoke/**`,
`s1/s1_rozdzielony/**` (manifesty z `wabik.sondy[]`/pin/spawn_proof,
percep_feed, demo, trace, qlog, wabik_motion.jsonl, wabik_sig.jsonl,
wabik_smoke.json; boot.ulg wg polityki gitignore, ulog_sha w manifestach).
Korzeń: `PRE_WABIK.md` (commit `bf776d20`). **Push = Olga („wypchnięte" — CC
weryfikuje z repo: kotwicę sędzią, progi vs NULL, zakres).** Po weryfikacji:
ANEKS_WABIK-1 i dopiero wtedy S2. **STOP-WABIK1.**
