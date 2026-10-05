# RAPORT_2A_S2b — naprawy N1/N2 + powtórka etapu A (A1b/A2b) + etap B od nowa

CC · 05.10.2026 · łańcuch 2A · ANEKS_2A-1 §6 (samowykonalny) · po STOP-2A2 (0dd749a na origin).
Reguła nadrzędna dotrzymana (shadow: tylko klatki + stan pokładowy; GT u sędziów offline).

## §0. Bramka wejścia i commity sesji

origin/master = 0dd749a; ahead pusty; porcelain pełny CZYSTY; piny 5/5; certy 9/9; sha 8/8
(w tym bench_flight `2972a48a` PRZED N1). Commity: (1) `b22dbc6` ARCH-1 ANEKS_2A-1 verbatim
(sha kopii `37357c49…`); (2) `5af1e54` N1+N2+testy+FREEZE_2A update; (3) ten STOP-2A2b.

## §1. Naprawy (ratyfikowane ANEKS_2A-1 §3) — diffy verbatim

**N1 — jednostki yaw na granicy MAVSDK** (`bench/bench_flight.py`, TRZECIA edycja — jawne
rozszerzenie PRE_2A §2-D6; sha `2972a48a` → `05137098abc1c31e6d3f70ca80e6b721487330131fa8a39181355b659f523a43`):

```diff
@@ -395,7 +395,12 @@ async def main():
                 await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
             else:
                 v = cmd["v_ned"]
-                await d.offboard.set_velocity_ned(VelocityNedYaw(v[0], v[1], v[2], cmd.get("yaw", 0.0)))
+                # ANEKS_2A-1 N1: kontrolery emitują yaw w RADIANACH (atan2, konwencja wewnętrzna
+                # bez zmian); pole VelocityNedYaw jest STOPNIOWE (yaw_deg) — konwersja jednostek
+                # WYŁĄCZNIE na tej granicy. Przed N1 surowe radiany (±π→±3.14°) trzymały nos ~N
+                # przez pięć nóg (nośne dopiero dla kamery — RAPORT_2A_S2 §3).
+                await d.offboard.set_velocity_ned(
+                    VelocityNedYaw(v[0], v[1], v[2], math.degrees(cmd.get("yaw", 0.0))))
```

Test granicy (test_aneks1): wyrażenie WYJĘTE ZE ŹRÓDŁA, cmd yaw=π ⇒ **180.0**; `math.degrees`
występuje w pliku DOKŁADNIE RAZ (kontrolery dalej emitują radiany).

**N2 — bramkowanie REFRESH** (`harness/feed_vision.py`; sha `0ce7569c` →
`0a97512106d8ca708c77329fd2bff50e8fe9b5fc0b06da5fa6b7eb5992a2f5de`; feed_sha `ffccf86b…` →
`d6a3367b210f47e79b2ea9b33151235d3a2a0ac21c4ad2b93dfa93092673a895` — parametry bramkowania
weszły do sha prowieniencji). Rdzeń (pełny diff w `git show 5af1e54`):
- REFRESH wyłącznie boxem, który (a) spełnia koniunkcję admisyjną NA KLATCE
  (central z `last_conj` kanału — ta sama geometria co brama ENTRY — ∧ mti_ok), ALBO
  (b) leży ≤ **REFRESH_GATE_M = 3.0 m** (decyzja wykonawcza, kalibracja klas z danych S2:
  FeedB p95 1.26 m + ruch celu + jitter zasięgu ~1 m, vs FP tła ≥5 m) od predykcji tracku
  (last_pos + trk_vel·Δt). Inaczej ZOH z rosnącym age; top-1 tła NIGDY nie odświeża tracku.
- **Sufit wieku tracku FEEDU** = θ_age 3.0 s: kanał frozen odświeża własny wiek KAŻDYM boxem
  przy locku (`target_channel.py:123` — „Refresh locka NIE stosuje ani edge-margin, ani
  conf/MTI"), więc wygaśnięcie orzeka FEED i resetuje kanał (API, nie edycja) ⇒ pełna
  re-admisja ENTRY k=3 struktura∧MTI. Zdarzenie logowane `FEED_EXPIRE`.

Testy: `results/2A/tools/test_aneks1.py` **6/6 PASS** (tło nie przeciąga tracku → FEED_EXPIRE
→ re-admisja pełną bramą; okno predykcji; noga central wymagana; feed_sha zmieniony).
Regresja pełna: **102 (katalogi) + 85 (tests_*) = 187 unikalnych PASS, 0 FAIL** (wyłączenia
jak S1: brake_test/test_deadman — rclpy na poziomie modułu). FREEZE_2A zaktualizowany.

## §2. Booty powtórki (oba VALID; REFUSE=0, breach=0; reżim S2: shadow po armed, FEED=B, GZ_IP)

| | **A1b = `stageA/A1b_c08_s03`** | **A2b = `stageA/A2b_c11_s01`** |
|---|---|---|
| dsw / V2′ / D6 | **0.9951** / VALID / success | **0.9908** / VALID / success |
| t_entry / d_min | 2.28 s / 5.20 m | 1.96 s / 6.83 m |
| klatki shadow (gap p50) | 686 (0.068 s = 14.7 Hz) | 1357 (0.068 s = 14.7 Hz) |
| boxy / fresh (admitowane) | 560 / 141 (gate: mti 106, okno 35) | 1183 / 386 (mti 344, okno 42) |
| ENTRY / FEED_EXPIRE [s sim] | 119.8 (err 29.5 m!), 140.1 / 135.2 | 110.2 (err **2.63 m**) / 199.9 (po epizodzie) |
| jpg (lokalnie, sha w manifeście) | 152, `e7e88a98…` | 174, `30181c2c…` |

## §3. Sanity naprawy yaw (ANEKS §4) — **PASS ×2** + kontrola negatywna

Mediana |yaw_drona − az(do tracku)| w orbicie po ustaleniu (5 s): **A1b 4.66°** (p95 11.55,
n=1255) · **A2b 4.11°** (p95 11.0, n=1259) — próg ≤15°. Kontrola negatywna przyrządu: A1
sprzed N1 → **75.16° FAIL** (narzędzie rozróżnia). Nos realnie śledzi komendę.

## §4. Bramka A (progi PRE §3, bez zmian)

**(i) pokrycie RZECZYWISTE:** orbit **1.0000 PASS ×2** (A1b 2169/2169, A2b 2173/2173 —
naprawa N1 zamyka znalezisko S2 w fazie nośnej); approach **FAIL ×2**: A1b **0.8977**
(79/88 — 2 ticki od progu), A2b **0.6484** (59/91). Mechanizm approach: slew nosa na
początku epizodu — faza approach trwa ~4–5 s, nos startuje od headingu hoveru; c11 (bearing
270°) wymaga większego skrętu niż c08 (bearing 0°). Po ustaleniu nos trzyma 4–5° (§3) —
to koszt przejściowy slew, nie błąd śledzenia. Werdykt progowy: **(i) FAIL** (approach),
orbit PASS. **(ii) dsw:** 0.9951 / 0.9908 **PASS ×2** bez retry (pasmo LIQ 0.9544–1.0).
**(iii) quat:** PASS ×2 (2981/2981 i 2994/2994, norma 0.999999–1.000001, vs attitude PX4
p50 0.64°/1.78°).

## §5. Etap B od nowa (percep_judge 363c37b7 frozen; progi bez zmian)

| metryka | próg | **A1b** | **A2b** | **pooled** | FeedB (te same booty) |
|---|---|---|---|---|---|
| kadencja świeżych p50 [Hz] | ≥8 | **3.79 FAIL** | **7.58 FAIL** (o włos) | **7.58 FAIL** | 9.62 |
| latencja capture→update p95 [s] | ≤0.25 | **0.072 PASS** | **0.048 PASS** | **0.052 PASS** | ~0.2 (konstr.) |
| błąd NED p95 [m] | ≤3.0 | **42.58 FAIL** (p50 8.16, n=448) | **40.84 FAIL** (p50 7.71, n=1041) | **40.93 FAIL** | 1.353 / 1.265 |
| dekompozycja kąt p50/p95 [°] | — | 45.6 / 60.7 | 30.5 / 56.9 | — | 3.11 / 6.96 (S1) |
| dekompozycja zasięg p50 (bias) [m] | — | 5.31 (+5.83) | 6.27 (+9.28) | — | 0.33 (+0.03) |
| FP-admisje >5 m / świeże w GT | — | 117/123 | 258/346 | — | — |

**Klasyfikacja progowa (wypisana; wnioski kanoniczne → ANEKS_2A-2):**
**B(i) FAIL** (7.58 < 8 pooled; per boot 3.79/7.58) · **B(ii) PASS** (0.052 s, 4.8× zapasu) ·
**B(iii) FAIL**, w tym **p95 > 6.0 m ⇒ wyjątek ekonomiczny obowiązuje normalnie od powtórki
(ANEKS_2A-1 §2) — na stole C-sonda 2 bootów**.

## §6. Atrybucja mechanizmu (twarda, z wykonania — do ANEKS_2A-2)

1. **N1 domknięte:** nos śledzi (mediana 4.1–4.7°), pokrycie orbity 1.000 ×2 — znalezisko
   yaw z S2 naprawione i zmierzone.
2. **Ogniwem limitującym jest DETEKTOR-top-1 w geometrii orbitującej:** przy celu w kadrze
   przez 100% orbity i dużym (~80–105 px szerokości), top-1 YOLO-World leży NIE na intruzie
   w ~97% klatek A1b i ~88–97% A2b — WSZYSTKIE boxy vs GT: A1b odległość pikselowa p50
   298 px, frakcja <2 m NED = 0.01, <5 m = 0.03 (n=480); A2b p50 281 px, <2 m 0.03, <5 m
   0.12 (n=981). Tło = klatter naziemny (ciemne sześciany/budynki); klatka dowodowa:
   `A2b…/sanity/worst_fresh_t151.1.png` — intruz duży w centrum, box na odległym sześcianie
   (conf 0.0017, w_px→Z błędne → err 67 m). W S2 (nos na N) detektor trafiał, gdy cel stał
   na tle NIEBA — ta sama słabość separacji od tła co lekcja r02 (CATCH: conf separator
   kruchy; tu conf telemetryczne ~1e-3 bez mocy separującej — polityka A1 top-1 bez progu).
3. **Projekcja NIE jest winna:** te same boxy przeliczone offline dokładnym quatem z trace
   dają err identyczny (p50 8.01 vs 8.30 live); staleness attitude w shadow p50 0.64°.
   Pinhole na PRAWDZIWYM celu: best 0.80 m (A1b) / **0.65 m** (A2b); ENTRY A2b 2.63 m.
4. **MTI pod ciągłą rotacją (~20°/s) koincyduje też z tłem** (rezyduum derotacji — ta sama
   klasa co D1/REGATE „rezyduum translacji"): mti_ok na 211/686 klatek A1b, a gate=mti
   przepuścił boxy tła (fresh-mti err p50 8.5 m); ENTRY A1b @119.8 padł na tło (29.5 m)
   mimo k=3∧MTI. **N2 działa zgodnie ze specyfikacją** (fresh to 25% boxów — brama tnie;
   FEED_EXPIRE w locie + re-admisja pełną bramą: A1b 135.2→140.1), ale brama admisyjna
   struktura∧MTI sama w sobie nie separuje tła przy tej scenie i rotacji.
5. Niska kadencja świeżych (3.8–7.6 Hz) jest POCHODNĄ selektywności bramy przy złych boxach
   (tor czasowo zdrowy: klatki 14.7 Hz, YOLO p50 ~15 ms, latencja świeżych p95 ≤0.072 s).

## §7. Artefakty i budżet

Booty lotne nogi po S2b: **4 VALID** (A1_r4, A2, A1b, A2b) z ≤31 (+3 env-faile nie-próby
S2; diagi 0-lotne poza licznikiem — ANEKS_2A-1 §5). Sanity-klatki: **6 nowych PNG**
(`A1b…/sanity/`, `A2b…/sanity/`: best 0.80/0.65 m, worst 47.7/67.2 m, entry 29.5/2.63 m).
`shadow_feed.jsonl` commitowane ×2; jpg lokalnie (sha zbiorów w manifestach); narzędzie
nowe: `sanity_yaw.py` (kontrola negatywna wykonana). Dowody shadow per boot jak w S2
(topics.txt, meta-wiersz z sha, `.gz_ip_proof`).

## §8. STOP-2A2b

Commit artefaktów (naprawy już w `5af1e54`; tu booty b + analizy + sanity + raport),
porcelain po commicie CZYSTY, **push = Olga**. Dalej: **ANEKS_2A-2** (go/no-go etapu C;
na stole: wyjątek ekonomiczny B(iii) ⇒ C-sonda, status B(i) przy kadencji-pochodnej-jakości,
approach-slew vs próg (i), oraz pytanie czy detektor-ogniwo w tej scenie czyni zdanie
„percepcja limituje dokładnością" kanonem nogi). STOP.
