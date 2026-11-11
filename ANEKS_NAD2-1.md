# ANEKS_NAD2-1 — po STOP-NAD2-1-FREEZE: kanon czasu nogi = `timestamp_sample`; sprostowanie FREEZE (F_jeden 0.2562 / 0.3376 / 0.4445 / 0.4527 / 0.4527 m); przedział osłony z τ + 0.012 s; REFUSE(τ*) przy τ ≥ 0.95 s; projekt drivera i osłony przyjęty; S1 wznowione

CC · 11.11.2026 · łańcuch NAD2, po STOP-NAD2-1-FREEZE (31657ee0 na
origin). Zmienia liczby zamrożone w ratyfikowanym PRE_NAD2 §4, więc
wymaga sygnału Olgi **„ratyfikuję NAD2-1"**. Sygnały bez numeru albo
nazwy odrzucasz.

## §1. Weryfikacja CC z repo (wykonaniem)

1. **CO-NAD2-0:** PRE_NAD2 byte-check PASS (eea6fcc8…), oba bloki
   verbatim, append-only.
2. **Diagnoza potwierdzona własnym kodem.** Z chwilą porównania
   wziętą z `timestamp_sample`: błąd zakotwiczenia pary 0.197 /
   0.237 / 0.234 / 0.211 / 0.258 m — identycznie jak w raporcie
   reconu, czyli różnica 0.007 m z PRE §1.4 była tą samą
   rozbieżnością; rozwiązanie jednym znacznikiem we wszystkich
   klatkach 0.256 / 0.338 / 0.444 / 0.453 / 0.340 m. Z `timestamp`
   wychodzą liczby z PRE. Pola różnią się o ok. 4 ms.
3. **Replay S4 w kanonie `timestamp_sample` z tabelą §2.2:** 27 253
   ticki, 0 przekroczeń przesłanki, max e_corr′/U 0.398, 0 REFUSE,
   zapas bariery min 1.71 m (c11_s02).
4. **`harness/nadir_fix.py`:** diff przejrzany — przy literze
   domyślnej lista dalekich partnerów jest pusta, dobór partnera
   równoważny dotychczasowemu; własny replay CC na nowym pliku
   odtwarza 27 800 zapisanych decyzji w 100%.
5. **STOP wykonawcy był poprawny:** tolerancja przekroczona
   o 0.0007 m i zatrzymanie zamiast wyboru konwencji, przy której
   liczby przechodzą.

## §2. Decyzje

1. **Kanon czasu nogi:** chwilą porównania z GT jest
   `timestamp_sample` próbki EKF — czas, którego dotyczy stan. Rama
   liczy Δ względem stanu, nie względem chwili publikacji. Kanon
   obowiązuje w narzędziu FREEZE, w błędzie zakotwiczenia, w G
   i w e_corr analizatora (B1).
2. **Sprostowanie PRE_NAD2 §4:** F_jeden = **0.2562 / 0.3376 /
   0.4445 / 0.4527 / 0.4527 m** (było 0.253 / 0.329 / 0.440 / 0.442 /
   0.442). F_para i G bez zmian. Skutek: U trybu „jeden" wyższe
   najwyżej o 0.016 m; u′ przy τ ≤ 0.25 s od 2.757 do 3.141 m,
   bariera 26.01–26.39 m.
3. **Przedział τ w osłonie: z τ + 0.012 s** (wniosek raportu: 0.02 s
   — skorygowany). Horyzont prawdziwy przekraczał τ osłony najwyżej
   o 0.008 s; 0.012 s to 1.5 × to maksimum i mieści nominalną
   kadencję w pierwszym przedziale (0.232 + 0.012 < 0.25). Przy
   0.02 s do drugiego przedziału wpadałoby 12 z 27 253 ticków S4,
   a bariera schodziłaby tam na jeden tick o 0.67 m — ryzyko
   zatrzaśniętej odmowy bez zysku dla dowodu.
4. **(B1) sądzi wobec U przedziału użytego przez osłonę** (numer
   przedziału zapisywany w ticku) — to jest przesłanka, którą
   konsumuje dowód. Zdanie PRE §4 „przedział wybiera większa
   z wartości" dotyczyło replayu; w locie różnica horyzont prawdziwy
   − (τ + 0.012 s) jest obserwablą, oczekiwanie ≤ 0.
5. **REFUSE(τ*) przy τ ≥ τ* − 2 · dt = 0.95 s** — przyjęte
   (konwencja zapasu ticków z KONT i NADIR-I).
6. **Projekt z §3 raportu przyjęty:** osłona dostaje pozycję i cel
   w obu ramach i wybiera ramę po aktualizacji monitora GNSS — w KONT
   poprawioną, w NOMINAL EKF; r_est z ramy wybranej; wyjście
   przeliczane do ramy EKF; R-G-NOM i projekcja promieniowa w tej
   samej ramie; brak poprawki od wejścia ⇒ pole (jeden, koszyk 4),
   τ od zera zegara utraty; launcher NAD2 do promptu smoke.
   **Obligacja C3 obejmuje wybór ramy:** 100% ticków KONT w ramie
   poprawionej, 100% ticków NOMINAL w ramie EKF, tick przejścia
   pokryty testem w obu kierunkach.
7. **Reszta PROMPT_NAD2_S1 bez zmian;** S1 wznawia się od §1.2.
   Odniesienie W2 w kanonie: liczby z §1.3 tego aneksu.

## §3. KSIĘGA (append-only przy commicie §CO)

```
## NADIR-II S1 — konwencja czasu FREEZE (ANEKS_NAD2-1, 11.11.2026)
- STOP-NAD2-1-FREEZE (0 bootów): F_jeden z PRE nie odtworzyło się
  w tolerancji (0.4527 wobec 0.442 m, +0.0107). Przyczyna: tabela
  PRE łączyła dwie konwencje chwili porównania z GT — F_para
  wykonawcy w timestamp_sample, F_jeden CC w timestamp (ok. 4 ms
  później). ✗ projektowe CC: FREEZE złożony z liczb dwóch autorów
  bez wspólnej definicji chwili; prompt reconu kazał podać obie
  konwencje i nie wskazał kanonu. Tolerancja 0.01 m z promptu S1
  zadziałała.
- Decyzja: kanon nogi = timestamp_sample; F_jeden 0.2562 / 0.3376 /
  0.4445 / 0.4527 / 0.4527 m (ratyfikacja NAD2-1). CC odtworzył obie
  konwencje własnym kodem; w kanonie liczby CC i wykonawcy są
  identyczne, także F pary (wyjaśnia różnicę 0.007 m z PRE §1.4).
- Przedział osłony z τ + 0.012 s (wniosek wykonawcy 0.02 s
  skorygowany: przy 0.02 nominalna kadencja przekracza krawędź
  0.25 s w 12 z 27 253 ticków S4); REFUSE(τ*) przy τ ≥ 0.95 s; (B1)
  sądzi wobec przedziału użytego przez osłonę.
- Wykonawca: STOP bez wyboru konwencji pod wynik; stara litera
  w nowym kodzie bez zmiany zachowania (W1 PASS; replay CC: 27 800
  decyzji w 100%).
```

## §CO

Bramka: origin/master == **31657ee0** i sygnał „ratyfikuję NAD2-1"
w wiadomości Olgi. Commit [CO-NAD2-1]: korzeń `ANEKS_NAD2-1.md`
verbatim (byte-check sha256 z wiadomości CC) + KSIĘGA §3
append-only. Potem S1 od §1.2 PROMPT_NAD2_S1 z decyzjami §2 (0
bootów). `STOP_NAD2_1.md` zostaje jak jest; raport końcowy S1
w NOWYM `results/NAD2/s1/STOP_NAD2_1B.md`, sygnał **STOP-NAD2-1B**.
Push = Olga.
