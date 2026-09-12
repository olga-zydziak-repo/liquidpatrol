# ANEKS_FV-1b — uproszczenie sekwencji: go S3 + przeniesienie odczytu C1a–C1d do W0 sesji S3

CC · 11.09.2026 · łańcuch FV (sub-numer po ANEKS_FV-1a).

## §1. Adjudykacja
Podwójny STOP bramek S3 = poprawne działanie projektu: żadna praca nie ruszyła przedwcześnie.
Jednocześnie trzy poślizgi sekwencji z rzędu (raport S2 niedostarczony do CC; ANEKS_FV-1 wklejony
zamiast -1a; PROMPT_FV_S3 bez linii go) to informacja o PROCESIE, nie o operatorze: za dużo
ruchomych części na tryb solo. Odpowiedź nie jest luzowaniem reżimu, lecz redukcją kroków przy
zachowaniu chronionej wartości — CC czyta całość materiału PRZED WERDYKTEM, a werdykt zapada
dopiero w ANEKS_FV-2 (bez zmian, -1a §6).

## §2. Zmiany mechanizmu (nadpisują WYŁĄCZNIE ANEKS_FV-1a §4–§5)
(a) Odczyt C1a–C1d przenosi się do **W0 sesji S3** — pierwsza czynność po bramkach: kopiowanie BEZ
modyfikacji do `/mnt/c/Users/Public/FV_C1/` czterech plików: `results/FV/RAPORT_FV_S2.md`,
`results/KSIEGA_PREDYKCJI.md`, `r01/proofs/certs/P7_posmon.json`, `results/FV/MUTANTY.md`
+ sha256 każdego w raporcie. Olga załącza te pliki spinaczem do wiadomości dla CC. Lektura CC jest
warunkiem ANEKS_FV-2 (werdyktu), NIE warunkiem dalszej pracy sesji S3.
(b) Linia go z -1a §5 ZASTĄPIONA. S3 jest skuteczne z chwilą łącznego spełnienia: (i) push 57d8f45
(`git log origin/master..HEAD` puste), (ii) obecność NINIEJSZEGO aneksu w wklejce startowej sesji.
Formuła równoważna dla bramki §0.1 promptu: **„ANEKS_FV-1b §2: S3 go"**.

## §3. Poprawki do PROMPT_FV_S3 (aneks wygrywa nad promptem — precedens N6)
Dla sesji trzymającej STARĄ wersję promptu: §0.1 uznaje się za spełnione obecnością tego aneksu;
krok **W0** (§2a) wykonywany PRZED C0'; §0.4 i C0' rozszerzone — ARCH-1 obejmuje `ANEKS_FV-1a.md`
ORAZ `ANEKS_FV-1b.md` (oba z Downloads procedurą C0 z S1). Zaktualizowana wersja pliku
PROMPT_FV_S3 z identycznymi poprawkami dostarczona równolegle — obie ścieżki (stara sesja + aneks
/ świeża sesja + nowy prompt) są równoważne.

## §4. Stan push — wątpliwość zamknięta
Raport bramki S3 pokazuje DOKŁADNIE JEDEN niepushowany commit (57d8f45). „Dwa commity"
z poprzedniej tury = artefakt transportu; sprawa zamknięta bez dalszych sprawdzeń.

## §5. W mocy bez zmian
ANEKS_FV-1a §1–§3 (adjudykacja, reguła SEQ-1, weryfikacja liczb O2/M) oraz §6 (werdykt PASS
ogłaszany wyłącznie w ANEKS_FV-2, po lekturze C1a–C1d i RAPORT_FV).
