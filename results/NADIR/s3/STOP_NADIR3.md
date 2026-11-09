# STOP-NADIR3 — osłona τ-zegar (bariera piły) + certy P9/P1/P5/P7_nadir + passthrough bitowy; żadna śmierć S3 nie zachodzi

Wykonawca · 9.11.2026 · łańcuch NADIR, PROMPT_NADIR_S3 po ANEKS_NADIR-2.
Bramka §0:
- CO-N2 `ccd6b115`: aneks verbatim, sha256 `6587ad67…e8904989` potwierdzone przez Olgę („sha ok”), KSIĘGA append-only;
- origin = HEAD = `ccd6b115`.

Budowa i certy w `df952e21`, boot B1 i raport w commicie STOP-NADIR3.

## Raport płaski

- **C1 P9_nadir: PROVED.**
  - **Twierdzenie główne:** dla każdego koszyka j ∈ {0…3} i kubełka k < τ*(j) — 87 obligacji — twierdzenie (u ≤ m ⇒ zawieranie przy A-nadir) wychodzi unsat.
  - **Ostrość czterostronna:** sat dla ε_fix + δ, ε_b + δ, R + δ i Δ_D5 + δ (δ = 1/1000).
  - **Arytmetyka:** 12/12 asercji, w tym:
    - τ* = 22/22/22/21 s z reguły PRE §3, zgodne z kodem;
    - ε_fix_freeze z tabeli aneksu (sha zweryfikowane) = 1.5 × max;
    - R_H_MAX 8 m zgodne w osłonie i w producencie ramy;
    - u(0, j) ≤ 2.99 (c08) dla wszystkich j.
  - **A-nadir** jest wypisane w cercie: przyrost dryfu w oknie ≤ ε_b(⌊τ⌋) oraz |p_fix − GT| ≤ ε_fix_freeze(j).
- **C2 P1_nadir: PROVED.** Automat P1_kont z barierą piły w miejscu R-KONT: 18/18 obligacji (P1a–P1o, nom_applied, indukcja) plus **P1p: liście wzajemnie wyłączne i wyczerpujące** (unsat ×2).
- **C3 P5_nadir: PASS.**
  - Zero rozbieżności lustro ≡ produkcja na 4.03 mln ticków fuzzu (10⁵ epizodów), siatce prereg (88 epizodów) i fiksturze S2 (4 cięcia, 4816 ticków).
  - Zgodność modelu τ (P1) z produkcją: 85 300 ticków.
  - Pełne pokrycie: wszystkie reguły, przyczyny τ*/bariera, koszyki 0–3, utrata bez poprawki, drugi epizod.
  - **Passthrough T0 desk:** NadirShield(NADIR_MODE=0) ≡ KontShield i ≡ PatrolShield pełnym dictem na 1.0 mln ticków, 0 różnic.
- **C4 P7_nadir: PROVED.**
  - Wyczerpujący graf monitora GNSS + zegara τ, 4 grafy (163 888–165 908 stanów, do 1.33 mln krawędzi): 0 nieudanych sprawdzeń (a)–(g).
  - Poprawka zeruje τ, a zatrzask REFUSE trwa mimo nowej poprawki. Brak poprawki oznacza koszyk najgorszy. Martwych gałęzi nie ma.
  - Instancja zredukowana z przełączaniem koszyków PASS, z3-duplikat 4/4 unsat.
- **B1 PASSTHROUGH: PASS.** Boot nominalny `NADIR_MODE=0`, `KONT_MODE=0`, 4 epizody:
  - **6636 ticków, decyzja produkcji = decyzja kanonicznego PatrolShield bajt w bajt** (pełny dict, osłona-cień na tych samych wejściach);
  - 0 REFUSE, 0 naruszeń strefy, tempo settle 0.966;
  - selfcheck 13/13 certów PASS w boocie.
- **Red test:** pełny zestaw 43 plików — PASS modulo zastany `r02/test_deadman.py` (`regresja_s3.tsv`). Nowych porażek: 0.
- **Werdykt S3: żadna śmierć S3 nie zachodzi.**
- **Budżet:** S3 1/2 (B2 nieużyta), noga NADIR 11/≤30. Breach 0, REFUSE 0.

## Do CC — nazwane

1. **R_nom 27.30 > R(0, j) = 26.72–27.08.** Przy utracie GNSS, gdy r_est leży w (R(0, j), 27.30], nastąpi natychmiastowy REFUSE(bariera). To kwestia dostępności, nie bezpieczeństwa: twierdzenie główne trzyma. W cercie zapisane opisowo, nie jako obligacja (w KONT R_nom ≤ R(0) było asercją). Czy R_nom pod NADIR obniżyć do min R(0, j) = 26.72, to decyzja CC. W lotach S2 r_est przy cięciu wynosił 3.8–15.9 m.
2. **τ*(j) — moja decyzja wykonawcza.** „Limit litery” dla kubełków τ wzięłam z reguły T* (PRE §3): ε_fix(j) + ε_b(k) + Δ_D5 ≤ m_p50. Koszyk 6–8 m ma przez to τ* = 21 s, pozostałe 22 s. W lotach S2 τ max wynosi 0.23 s, więc limit działa tylko przy długiej utracie znaczników.
3. **Brak poprawki od wejścia w utratę:** τ liczone od zera zegara utraty, jak t_KONT, z koszykiem najgorszym (0.582). Nazwane w kodzie i cercie (P7 (g)).
4. **τ obcinane do 0.** Stempel klatki może wyprzedzić zegar pętli o ułamek ticku. Bez obcięcia ε_b[−1] wziąłby po cichu ostatni element tablicy.
5. **Fikstura S2 offline:** osłona NADIR w żadnym z 4 cięć nie dałaby REFUSE. τ w utracie miało p95 0.20–0.21 s i max 0.22 s, a poprawki z r_h ≥ 8 m odrzucone nową literą były 0–1 na cięcie. Osłona 2d w tych lotach kończyła misję po T* = 22 s.
6. **Driver S3/S4** (`nadir_s3_flight.py`) jest gotowy pod S4: NadirShield dostaje t_fix i koszyk z ramy B+. `KONT_MODE=0` dopuszczam wyłącznie z jawnym `NADIR_S3_PASSTHROUGH=1`.
7. **Przyrząd dry-run:** trace atrapy zostaje pusty (bufor nieopróżniony przed wyjątkiem zatrzymania). Kryterium zastąpiłam selfcheckiem certów i plikiem passthrough, nazwane w docstringu.

## Pliki

- **Osłona:** `r03/nadir_shield.py`.
- **Prover:** `r01/proofs/p9_nadir_verify.py`.
- **Certy:** `r01/proofs/certs/{P1,P5,P7,P9}_nadir.json`.
- **Selfcheck:** `results/NADIR/s3/tools/nadir_certs_selfcheck.py`.
- **Siatka prereg:** `results/NADIR/s3/p5_nadir_grid.json`.
- **Logi:** `p5_stdout.log`, `regresja_s3.tsv`, `dryrun/dryrun_s3.json`.
- **Boot B1:** `b1_passthrough/` (`passthrough.jsonl`, `passthrough_summary.json`).
- **Narzędzia:** `results/NADIR/tools/nadir_s3_*`.

Replikacja: `PYTHONPATH=.certdeps:. python3 -m r01.proofs.p9_nadir_verify all`.

Sygnał: **STOP-NADIR3**. Push = Olga. CC replikuje certy i pisze PROMPT_NADIR_S4 albo aneks.
