# ANEKS_K2-7 — skuteczność porządków doc-only (A1/A3/A4) + reguła ARCH-1

CC · 11.09.2026 · łańcuch K2 (kolejny po ANEKS_K2-6). Werdykt nogi K2 (PASS 12/12) nietknięty.

## §1. A1 skuteczne
RAPORT_K2 §7 = **kanon roszczeń K2 obowiązujący** (re-publikacja ANEKS_K2-6 §2 z jawną prowieniencją
rekonstrukcji). Każdy materiał zewnętrzny cytuje odtąd §7 raportu, nie pamięć sesji. Rozbieżność R2
audytu CC v2 zamknięta.

## §2. A3 skuteczne
Linia push w §6 zaktualizowana po weryfikacji origin (683fcdf / 788bb26 / 1e58658 potwierdzone na
origin/master przez wykonawcę). Pozycja 6 jest realnie na origin — rozbieżność R1 audytu zamknięta
w części dotyczącej K2.

## §3. A4 skuteczne
Ścieżka scenario_manifest w §5 doprecyzowana (results/BENCH/scenario_manifest.json, sha e0527026
niezmienione).

## §4. REGUŁA ARCH-1 (programowa, trwała)
Od tej chwili każdy aneks ratyfikacyjny CC jest **commitowany pełnym tekstem do repo** w najbliższej
sesji wykonawczej (korzeń repo, wzór ANEKS_K2-0/-1). Łata lukę R3 audytu CC v2: łańcuchy ratyfikacji
nie były dotąd samonośne w repo (K1: 1/19 plików, K2: 2/7, NET: 1/6, INFRA-3: 0/4). ANEKS_K2-7,
ANEKS_NET-6, PRE_FV oraz przyszły ANEKS_FV-0 wchodzą w pierwszym commicie sesji FV-S1.

## §5. Commit
24f884d przyjęty w zakresie A1/A3/A4. Push = Olga.
