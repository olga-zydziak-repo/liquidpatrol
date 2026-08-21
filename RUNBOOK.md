# RUNBOOK — DEMO-B SITL (pułapki uruchamiania biegów)

## env-fail boot-y (nie system — pułapki launcha)
- **Redirect do nieistniejącego katalogu:** `bash run_act_demo.sh ... > results/.../X.launch.log` PADA
  exit 1 przy linii redirectu, jeśli katalog `results/.../` jeszcze nie istnieje. ZAWSZE `mkdir -p`
  katalogu-rodzica PRZED launchem (nie tylko OUTDIR wewnątrz skryptu).
- **Ciężkie komendy Bash równolegle z 210 s settle:** odpalanie git/python/heavy-Bash w tle podczas
  `sleep 210` settle destabilizuje bieg (proces ginie w settle, dzieci px4/agent osierocone, port 8888
  zajęty). W trakcie settle NIE odpalać równoległych ciężkich komend — czekać cicho na notyfikację.
  Sprzątanie osieroconych: `kill -9` po PID + sprawdzić `ss -lun | grep 8888` wolny przed re-launchem.
