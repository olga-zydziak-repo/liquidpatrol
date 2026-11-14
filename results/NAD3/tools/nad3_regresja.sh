#!/usr/bin/env bash
# results/NAD3/tools/nad3_regresja.sh — regresja NAD3 S1 (PROMPT_NAD3_S1 §4 T): pliki z results/NAD2/s1/regresja_s1.tsv tym samym
# sposobem (pytest -q albo „skrypt” = python rc) + testy NAD3; ROS jazzy i ros2_ws jak w NAD2 S1. Wyjście TSV na stdout.
cd /home/olga/projects/liquidpatrol
set +u
source /opt/ros/jazzy/setup.bash >/dev/null 2>&1
source ros2_ws/install/setup.bash >/dev/null 2>&1
export PYTHONDONTWRITEBYTECODE=1
lista=$(cut -f1 results/NAD2/s1/regresja_s1.tsv)
for f in $lista "$@"; do
  typ=$(grep -P "^\Q$f\E\t" results/NAD2/s1/regresja_s1.tsv | cut -f2)
  if [[ "$typ" == skrypt* ]]; then
    timeout 600 python3 "$f" >/dev/null 2>&1; echo -e "$f\tskrypt rc=$?"
  else
    out=$(timeout 600 python3 -m pytest -q -p no:cacheprovider "$f" 2>&1 | tail -1); echo -e "$f\t$out"
  fi
done
