# ANEKS_LIQ-1 — przyjęcie S1, kanon wyniku offline, errata progu sondy, drabina po odpadnięciu MLP-k20

CC · 02.10.2026 · łańcuch LIQ (po STOP-LIQ1, commity 0213da1 + de6e855 na origin).
Wykonanie: ARCH-1 w S2 (ten plik pierwszym commitem sesji); poza tym aneks nie zleca działań.

## §1. Przyjęcie STOP-LIQ1

Przyjęte bez zastrzeżeń, po NIEZALEŻNEJ weryfikacji CC wprost z repo (wykonaniem, nie
lekturą): PRE_LIQ.md w korzeniu byte-identyczny z ratyfikowanym (sha256 zgodny z moją
kopią); sha wag gru.npz/mlp20.npz = FREEZE_LIQ 2/2; diff rejestru = dokładnie +2 wpisy
addytywne (droga SR-9); diff launchera sondy = dokładnie 2 hunki (nagłówek + prepend→dowód
stock); model_gate.json: gru PASS / mlp20 FAIL / ncp PASS; dyspersja w JSON zgodna z tabelą
raportu. Gradient-check GRU 4.14e-07, wyrocznia 12/12, pytest 22 passed, wall-time zapisany
(luka R2.8 domknięta), mapowanie hiperparametrów wykonane literą promptu §1(a) z jawną notą
— przyjęte. Decyzja o nazwie launchera (liq_launcher_stock.sh) — przyjęta.

## §2. Wynik S1 i co wolno o nim mówić

**MLP-k20 odpada offline: 1/24 rolloutów (ziarna init: 0/24, 1/24) przy NAJLEPSZYM val-MSE
z trójki (0.0179 vs 0.049).** GRU 24/24 — leci. NCP kanoniczny 24/24 — punkt odniesienia
przyrządu trzyma.

Zdania kanonu (obowiązujące od teraz; każde niesie: ten tor treningu, budżet ~1.9k
parametrów, G13′, model punktowy FEED-B):
- „Pod zamrożonym torem treningu NCP kontrola MLP-k20 nie osiągnęła progu offline pozycji 3;
  porównanie lotne niewykonane" (PRE §2, verbatim).
- „Kontrola okna k=20 przy budżecie ~1.9k parametrów osiąga najlepsze val-MSE z trzech
  architektur i najgorszy rollout (0–1/24); rozjazd model-punktowy↔rollout jest widoczny już
  offline — przy k=5 (2467 parametrów) ujawnił go dopiero lot (8/48). Kolaps stabilny między
  ziarnami inicjalizacji."

**NIE WOLNO:** „okno nie działa w ogólności" (k=20/h=11 to jeden punkt przestrzeni
okno×budżet; k=5/h=32 przechodził offline); awansować liquid z porażki MLP-k20 (PRE §2 —
porażka treningowa kontroli nie jest dowodem mechanizmu); pomijać kwalifikatora toru:
literalne mapowanie dało MLP-k20 lr 0.003/cap 1000 z gałęzi ncp — to część ZAMROŻONEGO
przyrządu; retrening z innym lr po obejrzeniu wyniku byłby strojeniem po fakcie i jest
zakazany w tej nodze (osobna noga, gdyby kiedyś trzeba).

## §3. ERRATA progu sondy STOCK (przed pomiarem; wpis do księgi błędów CC)

Błąd mój, klasa SEKWENCJI KALIBRACJI: próg ABSENT ≤13.0 m ustawiłem w PRE §5 na ślepo,
ZANIM istniał punkt odniesienia, który sam zamówiłem w TYM SAMYM dokumencie (zadanie
biurkowe). Dane biurkowe pokazują: historyczny stock w c11 (F2, świat A3) = 12.86–13.27 m —
siedzi okrakiem na 13.0, więc próg klasyfikowałby reprodukcję historycznego zachowania jako
„nierozstrzygające". Poprawna sekwencja: biurko → próg. Korekta TERAZ jest legalna, bo
(a) sonda jeszcze nie poleciała, (b) korekta używa WYŁĄCZNIE danych historycznych,
(c) separacja w danych jest czysta: stock 12.86–13.27 vs enable_wind L0 14.43–18.45 —
przerwa 13.27–14.43, w którą kładę próg.

**Progi obowiązujące (zastępują PRE §5 w tym jednym punkcie):** pełzanie NIEOBECNE na stock
⇔ z_max ≤ **14.0 m** w 2/2 bootów; POTWIERDZONE ⇔ z_max ≥ 15.0 m w ≥1/2 (bez zmian);
14.0–15.0 ⇒ nierozstrzygające, kwalifikator habitatowy zostaje. Skutki kanoniczne obu
wyników — bez zmian (PRE §5). Zastrzeżenie wykonawcy przyjęte: stock-referencja jest
z INNEGO świata (A3) niż sonda (world_wind_s0) — dlatego raport sondy dodatkowo zestawia
parami per ziarno: probe_s01 vs 18.45 (W L0/s01) i probe_s02 vs 14.43 (W L0/s02), opisowo.

## §4. Drabina werdyktów po odpadnięciu MLP-k20 (konsekwencje PRE, zamrożone PRZED lotami)

- **W0** bez zmian (NCP świeże ≥ 40/48 albo STOP przyrządu).
- **W3 nieewaluowalne w locie** — a jego kierunek offline jest PRZECIWNY (0–1/24): nic
  w tej nodze nie wspiera „okno wystarcza".
- **ŚMIERĆ etykiety wisi wyłącznie na W2:** Δ(GRU) ≤ +2 na wspólnych ważnych ⇒ degradacja
  trwała (PRE §4, bez zmian).
- **W1 pełne NIEOSIĄGALNE** (wymagało obu kontroli w locie). Definiuję **W1′ (częściowe),
  zdanie zamrożone teraz:** Δ(GRU) ≥ +6 ⇒ „NCP-20 przewyższył kontrolę rekurencji o tym
  samym budżecie (Δ≥6/48 par); kontrola okna odpadła offline — przewaga nad GRU wykazana,
  pełna izolacja mechanizmu liquid wymagałaby latającej kontroli okna". W1′ NIE uprawnia do
  zdań pełnego W1.
- **W4** bez zmian (szczelina 3–5). Kontrola lepsza od NCP o ≥3 ⇒ zdanie jawne (PRE §4).
- Predykcje w toku: **P-LIQ-1 ✓, P-LIQ-2 ✗** (rozliczenie formalne w KSIĘDZE przy
  zamknięciu nogi, jak zawsze).

## §5. Kampania po korekcie składu (liczby z PRE, przeskalowane na 2 ramiona)

12 rund × **2 booty** (NCP, GRU) = **24 kryterialne**; parowanie i bloki scenariuszy bez
zmian (48 scenariuszy per ramię, 4/boot); rotacja kolejności ramion per runda. Smoke lotny:
**1 boot (tylko GRU)** — NCP lata torem F2 bez zmian i smoke'a nie potrzebuje. Budżet nogi
po korekcie: 1 smoke + 24 kampania + 2 sonda + 4 powtórki/zapas = **≤31 bootów** (twardy
limit PRE ≤44 bez zmian). Ramię NCP lata DOKŁADNIE ścieżką F2 (CONTROLLER=net, NET_ARM=ncp,
wagi 0337d5ea); GRU przez CONTROLLER=gru (wagi 5ec02755). z_max per epizod per ramię do
tabel — darmowe dane pełzania dla OBU architektur.

## §6. Dalej

PROMPT_LIQ_S2 (smoke + rundy 1–6) obok tego aneksu. S3 = rundy 7–12 + sonda STOCK na
progach §3. Werdykt drabiny — wyłącznie w aneksie zamykającym, po komplecie rund; raporty
sesyjne niosą liczby, nie narrację.
