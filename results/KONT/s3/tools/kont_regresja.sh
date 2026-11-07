#!/usr/bin/env bash
# results/KONT/s3/tools/kont_regresja.sh — regresja PROMPT_KONT_S3 §3: każdy plik testów repo (git ls-files,
# test_*.py / tests_*.py) osobno w pytest, w środowisku stanowiska (ROS jazzy + ros2_ws, jak harness/*.sh).
# Plik bez testów pytest (0 zebranych) uruchamiany jako skrypt (python3 <plik>), liczy się kod wyjścia.
# Użycie: bash results/KONT/s3/tools/kont_regresja.sh <wyjście.tsv>
set -o pipefail
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"
OUT="${1:?wyjście.tsv}"
set +u
source /opt/ros/jazzy/setup.bash
source "$ROOT/ros2_ws/install/setup.bash"
export PYTHONPATH="$ROOT:$ROOT/.certdeps:$PYTHONPATH"
: > "$OUT"
fail=0
while read -r f; do
    o=$(timeout 900 python3 -m pytest -q -p no:cacheprovider "$f" 2>&1 | tail -1)
    if [[ "$o" == *"no tests ran"* ]]; then
        timeout 900 python3 "$f" > /dev/null 2>&1
        rc=$?
        o="skrypt rc=$rc"
        [ $rc -ne 0 ] && fail=1
    elif [[ "$o" == *failed* || "$o" == *error* ]]; then
        fail=1
    fi
    printf '%s\t%s\n' "$f" "$o" >> "$OUT"
done < <(git ls-files | grep -E '(^|/)(test_[^/]*|tests_[^/]*)\.py$')
echo "regresja: $( [ $fail -eq 0 ] && echo PASS || echo FAIL ) ($(wc -l < "$OUT") plików) → $OUT"
exit $fail
