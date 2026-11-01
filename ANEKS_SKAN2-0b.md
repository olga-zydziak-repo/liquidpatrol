# ANEKS_SKAN2-0b — remedium zegara: zatrzymać systemd-timesyncd w WSL na czas sesji, jedna próba próbnika, bez powtarzania do skutku

CC · 1.11.2026 · łańcuch SKAN2, po drugim STOP-SKAN2-ZEGAR (962b0b4a lokalnie,
budżet 0/8). Uzupełnia ANEKS_SKAN2-0 §3.1. PRE_SKAN2 i kryterium bramki
(każdy skok ≤ 1.2 s ∧ ≤ 3 skoki w 60 s) zostają bez zmian.

## §1. Diagnoza z danych

Skok realtime względem monotonic przy równym biegu między skokami oznacza,
że zegar gościa WSL chodzi wolniej od źródła czasu, a coś okresowo dociąga
realtime krokiem. Dziś 1.01 i 1.02 s co 33.3 s (≈ 3 %), godzinę później 1.71 s;
w WK-IV 2.2–3.3 s. Amplituda rośnie, więc powtarzanie próbnika do skutku
byłoby ciche luzowanie bramki. Wykonawca słusznie go nie powtórzył.
Kandydat na źródło kroku wskazany w WK-IV to `systemd-timesyncd`. Nic w torze
lotu nie czyta realtime (ANEKS_SKAN2-0 §2). Jeśli nikt go nie dociąga, realtime
biegnie razem z monotonic, bez skoków, a V2′ liczone z wall staje się
pomiarem bez artefaktu.

## §2. Remedium (jedna próba)

1. Zapis stanu przed: `timedatectl status`, `systemctl is-active
   systemd-timesyncd`, `cat /sys/devices/system/clocksource/clocksource0/current_clocksource`
   do `results/SKAN2/s1/zegar_stan_przed.txt`.
2. `sudo systemctl stop systemd-timesyncd` (sudo podaje Olga). **Stop, nie
   disable.** Po zakończeniu sesji (STOP dowolnego rodzaju) wykonać `sudo systemctl
   start systemd-timesyncd` i zapisać stan po. W manifestach bootów pole
   `zegar: {"timesyncd": "stopped", "clocksource": …}`.
3. **Jeden** próbnik 60 s według ANEKS_SKAN2-0 §3.1.
   - PASS ⇒ boot 1 bB_c1011. Przed bootem 2 próbnik bez ponownego
     zatrzymywania (timesyncd dalej zatrzymany). PASS ⇒ boot 2, FAIL ⇒ STOP.
   - FAIL ⇒ krok realtime robi coś innego niż timesyncd (najpewniej
     synchronizacja czasu hosta Hyper-V/WSL). STOP-SKAN2-ZEGAR, przywrócenie
     timesyncd. Następne podejście dopiero po pełnym restarcie Windows: Start →
     Uruchom ponownie, nie Zamknij, laptop na zasilaczu. Po restarcie znowu
     §2.1–§2.3, znowu jedna próba. Bez trzeciego podejścia tej samej nocy.
4. W locie bez zmian: V2′ literą, etykieta „artefakt zegara” opisowo,
   dolecenia jak w ANEKS_SKAN2-0 §3.3.

## §3. Wykonanie

Zapisz ten aneks verbatim do korzenia jako `ANEKS_SKAN2-0b.md`; byte-check
sha256 z wiadomości CC. Commit z `zegar_przed_b1.jsonl` i
`zegar_stan_przed.txt`:
`SKAN2 [ANEKS-0b]: remedium zegara (timesyncd stop na sesję), dowód próbnika`.
Potem §2.2–§2.3. Reszta PROMPT_SKAN2_S1 i ANEKS_SKAN2-0 bez zmian.
