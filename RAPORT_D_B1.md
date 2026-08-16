# RAPORT_D_B1 — DEMO-B blok B1: token operatora + REFUSE(NO_AUTH) + pełny cykl certów

Data: 2026-08-16. Zakres: **wyłącznie blok B1** (automat + certy + testy deterministyczne, **bez SITL**,
bez świata/kamery/intruza/overlay — to bloki B2+). Reżim: kryteria/frozen/certy nietykalne poza
ratyfikowanym zakresem; prowieniencja per liczba; FAIL=FAIL; **push = Olga**.

## Stan wejściowy (SR-B5)

- HEAD startowy = `origin/master` = `83c7e9c` (Olga pushnęła po ratyfikacji PRE_D). Drzewo **czyste**.
- `certs_selfcheck` **bieg #1** (PIERWSZA czynność sesji, czysty HEAD): **PASS 6/6** — baseline.
- Łańcuch commitów B1 (niepushowane):
  - `c25707e` §0: ANEKS_D1 + korekta A1 (PRE_D).
  - `01f47e8` §2/§4: kod tokenu (język/authz/shield/runner) + testy deterministyczne.
  - `6e4b417` §3: re-certy P1/P4/P5 + regeneracja + selfcheck ×2.
  - `<ten commit>` §5: RAPORT_D_B1.

## Co ZBUDOWANE (§2)

| Warstwa | Plik | Zmiana |
|---|---|---|
| Gramatyka | `r01/language.py` | `OBSERVE_GRANT` = `grant observe` (zamknięta, zero free-form) |
| Admisja/token | `r01/authz.py` | `issue_token` / `token_auth_ok` / `consume_tokens`; podpis HMAC obejmuje CAŁY rekord (tamper `operator_id`/`nonce`/`admission_seq` wykryty) |
| Osłona (TCB) | `r01/shield.py` | `NO_AUTH` = **6. reason**; stan `NOAUTH` **ODWRACALNY** (nie latch); wejście `auth_ok`; gałąź **R-AUTH** wewnątrz OBSERVE |
| Runner (dławik) | `r02/gate_run_r02.py` | ścieżka tokenowa **domyślnie OFF** (`token_gated=False`); `admission_seq` (inkrement na ENTRY), konsumpcja na EXPIRE, `auth_ok`→`shield.step`, log `token_issued`/`token_consumed`/`refuse_no_auth` |

Semantyka (ANEKS_D1 §Semantyka, zamrożona): default-deny; token = podpisana komenda per-epizod;
per-admisja (`admission_seq`, konsumpcja na EXPIRE); pre-autoryzacja zakazana; **R-G i R-POS dominują
nad R-AUTH**; TCB = tylko gałąź decyzji, wyliczenie `auth_ok` w authz; authority gating, **NIE „secure C2"**.

## Co PROVED / PASS (§3)

**P1 (`verify.py`, z3, 1-indukcja): PROVED — 10/10 `unsat`** (base, inv_step, P1a–P1h).
Nowe obligacje:
- **P1g:** `OBSERVE-ALLOW ⇒ auth_ok` — żadnego OBSERVE bez ważnego tokenu (default-deny).
- **P1h (domknięcie):** `¬term ∧ ¬pos ∧ ¬geo ∧ mode=OBSERVE ∧ ¬auth_ok ⇒ REFUSE ∧ reason=NO_AUTH ∧ ¬terminal'`
  (odwracalny; R-G/R-POS jako prekondycje wyżej — dominacja strukturalna).
- P1c rozszerzone o `NO_AUTH`; `domain(rsn),domain(st) ≤ 6`; automat **9 liści** (rozszczep OBSERVE→L_observe|L_auth).

**P4 (`p4_verify.py`): PASS — 24/24 checks** (12 istniejących + 12 tokenu) + property-based
**1500 sekwencji** issue/consume (inwariant: `token_auth_ok` ⇔ istnieje niekonsumowany ALLOW-grant
bieżącego epizodu). Kryte: default-deny, „no OBSERVE without token", pre-auth (PREAUTH), nonce-once
(NONCE_REUSE), per-admisja/EXPIRE, tamper pól tokenu, anti-bypass (gramatyczne `admit('grant observe')`
≠ ważny token).

**P5 (`conformance.py`): PASS — 0 rozbieżności `tau≡shield`, pokrycie 9/9** (400 losowych + **21
celowanych** epizodów). Nowy 9. liść `no_auth` + wektory krzyżowe dominacji `geo_above_auth`,
`pos_above_auth`, `latch_above_auth` + odwracalność `no_auth→token→observe→revoke`.

**`certs_selfcheck`:** bieg #1 (start) **6/6**, bieg #2 (po regeneracji) **6/6**.

### Hashe certów (prowieniencja `model_sha256`, przed → po)

| Cert | Prover | przed (`83c7e9c`) | po (B1) |
|---|---|---|---|
| P1 | verify.py | `fac91fb3ce942999` | **`1a076269a04c5325`** |
| P4 | p4_verify.py | `8e1802b59aab05f5` | **`5b9cbdc73198951d`** |
| P5 | conformance.py | `869c16692d0b1536` | **`7bc53ecb4164f63d`** |
| P2 | geofence.py | `7c382af56606a44a` | `7c382af56606a44a` (bez zmian) |
| P2_eps | eps_verify.py | `8fb1ab19f3e47dbc` | `8fb1ab19f3e47dbc` (bez zmian) |
| P2_vmax3p1 | geofence.py | `7c382af56606a44a` | `7c382af56606a44a` (bez zmian) |

## Testy deterministyczne (§4) — `r01/test_token_authz.py`: PASS 12/12

Przeszukanie przestrzeni stanów **sweepem** (nie próbki bez ziarna). Właściwości i liczność:

| # | Właściwość | Test | Liczność |
|---|---|---|---|
| (i) | ¬token ⇒ OBSERVE nieosiągalne z ŻADNEGO stanu | `no_token_no_observe_from_any_state` | 3 pre-stany × 2 cele × 3 pos_flag = 18 |
| (ii) | token zmienia decyzję TYLKO w OBSERVE | `token_only_affects_observe` | 5 trybów × 2 pos_flag |
| (iii) | EXPIRE konsumuje; re-admisja bez nowego ⇒ NO_AUTH | `authz_expire_consumes_readmission_needs_new` + integracja | — |
| (iv) | pre-auth / zły epizod odrzucane (PREAUTH) | `authz_default_deny_and_preauth` | — |
| (v) | nonce-reuse odrzucany (NONCE_REUSE) | `authz_grant_binds_episode_and_nonce_once` | — |
| (vi) | R-G, R-POS, latch DOMINUJĄ nad R-AUTH | `geofence_/pos_degraded_/latch_dominates_no_auth` | 3 wektory krzyżowe |
| (vii) | `mode_of()` rzuca `PermissionError` przy ≠ALLOW | `mode_of_denies_non_allow` | 4 rekordy (w tym odrzucone tokeny) |
| — | odwracalność NO_AUTH (nie latch) | `no_auth_reversible_nonterminal` | — |
| — | integracja `authz.token_auth_ok`→`shield.step` (AKT1 in-silico) | `integration_authz_drives_shield_...` | — |

Regresja (nienaruszalność): `r01/test_core.py` 10/10, `r02/{test_channel,test_guidance,test_mti,test_deadman}` 25/25 — **PASS**.

## Uzasadnienie NIETKNIĘTYCH P2 / P2-ε / P2_vmax3p1 (D6)

Token operuje **wyłącznie** na gałęzi autoryzacji trybu OBSERVE (klasa ALLOW/REFUSE-odwracalny **poniżej**
R-G i R-POS). Nie dotyka żadnej wielkości bariery geofence: `R_E`, `a_brake`, `v_max`, `V_E` — arytmetyka
zawierania `p + v²/2a ≤ R_E` i plateau P2-ε bez zmian. Provery `geofence.py`/`eps_verify.py` niezmienione
(sha bez zmian, tabela wyżej). Dominacja R-G nad R-AUTH jest **udowodniona** (P1b niezmienione + P1h ma
`¬geo` w przesłance) i **pokryta konformancją** (`geo_above_auth` → GEOFENCE, nie NO_AUTH). Regeneracja
P2* była więc zbędna i celowo pominięta.

## Rozbieżności (jawnie)

1. **Kolejność R-G vs R-POS.** PROMPT §1.5 zapisuje `R-G > R-POS > R-AUTH`. Kod zamrożony R0.3a ma
   faktycznie **R-POS ponad R-G** (bariera na niepewnej pozycji niewiarygodna — prekondycja geofence,
   `RAPORT_R03A`). **Nie zmieniano** tej kolejności (SR-B1). Dla B1 istotne i egzekwowane: **R-AUTH
   poniżej OBU** (żyje w gałęzi OBSERVE). Zapisane w ANEKS_D1 §Semantyka.5; potwierdzone wektorami
   `geo_above_auth` (→GEOFENCE) i `pos_above_auth` (→POS_DEGRADED).
2. **Liczba liści 8→9** (nie „8→9" jako niepewność z promptu, lecz **zmierzone z modelu**): R0.3a miało
   8 liści decyzji; rozszczep OBSERVE na `L_observe|L_auth` daje **9**. Zaraportowane z `P1.json:leaves=9`.
3. **Numery linii dławika** (recon R4 → weryfikacja grepem 2026-08-16): `observe_authority` init **187**,
   `admit_observe` **222–226**, eskalacja `tick()` **389**, `shield.step` **399** — **zgodne z recon**
   (po dodaniu kodu numery przesunięte, ale węzły te same; grep w ANEKS_D1).
4. **Runner nie uruchamiany w B1** (SR-B4: bez SITL). `r02/gate_run_r02.py` importuje `rclpy`/`px4_msgs`
   (workspace `ros2_ws/install`); potwierdzono **parse OK** + **import OK** przy zasourcowanym workspace
   (Runner ma `issue_operator_token`, `NO_AUTH` zaimportowane). Ścieżka tokenowa jest **domyślnie OFF**
   (`token_gated=False`) → zachowanie R0.2/R0.3a bez zmian; logika token↔shield zweryfikowana
   deterministycznie w izolacji (`test_integration_...`). **Pełne wykonanie SITL = blok B2.**
5. **`auth_ok` default `True`** w `shield.step` — dla zgodności wstecznej (legacy OBSERVE bez tokenu).
   Default-deny realizuje się w warstwie authz/runnera (brak tokenu ⇒ `token_auth_ok=False`), nie w
   pythonowym defaulcie osłony. Udokumentowane jako **A-auth** w `P1.json:assumptions`.

## STOP

Blok B1 domknięty: automat + 3 certy (P1 PROVED / P4·P5 PASS) + selfcheck ×2 6/6 + 12 testów
deterministycznych, P2* nietknięte z uzasadnieniem. **Zero SITL, zero nagrań, zero zmian frozen/kamery/
intruza/overlay** (SR-B1…B4 honorowane; SR-B5 spełniony na starcie; brak niepowodzeń środowiska — SR-B6).

**Bloki B2 (choreografia intruza) i dalsze — osobny prompt po przeczytaniu tego raportu przez Olgę.
Push = Olga.**
