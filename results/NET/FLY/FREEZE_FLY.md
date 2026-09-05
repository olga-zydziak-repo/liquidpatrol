# FREEZE_FLY — przyrząd lotów pozycji 4 (PROMPT_NET_FLY N-F1)

LiquidPatrol · noga sieci · pozycja 4 · zamrożenie przed pierwszym lotem kryterialnym.

## Wagi lecące (z FREEZE_NET, nietykalne — SR-2)
- NCP-20: `net/frozen/ncp.npz` sha256 `0337d5eae1471bb99ef329d939be195a9ea846017045b8ddac22f3d97bc2ae36`
- tiny-MLP: `net/frozen/mlp.npz` sha256 `1d1900235724e938557cf9c614e39935483d51edd75f174cce7c8fb3d72f2270`

## Kod lotu (N-F0/N-F1)
- `r03/controllers/net_controller.py` : `e8c1b6583a6237a53567817a1b7036e51a9d7da5f1e92d5018da8e9781215167`
- `net/fresh_scenarios.py` : `293b64c0cdf94b10658d19392b7a946cb8cc49e421f634126a5fc3abd280ac5c`
- `bench/paired_analyze.py` : `ccb21aad1c8555ac470a9b7efe1af38f3c3399c02b95f66388054bb72b7f6def`

## Świeży zbiór (SR-6, nietykalny po N-F1)
- `results/NET/FLY/scenario_manifest_fresh.json` : `a2dacee65e86a94033e8918bed72efa818ef66f64264472b48814ae299c21dfd` (36 ep, ziarna 11-13 × 12 komórek)
- Generator = `bench.scenarios.gen_episode` przez IMPORT (scenarios.py `fe4f2aeb…` NIETKNIĘTY — O-F1).

## Odziedziczone frozen (ławka + piny, I0.2)
sędzia bench_judge 8ec0fcfb, features 9adc1505, feed track_feed 674d78ab, egzekutor orbit_executor 840514361e
+ executor_params 12c14adb, manifest bazowy e0527026, scenarios fe4f2aeb, instrument kampanii (campaign_analyze
f31e81e3/queue 89619514/finalize 508856dc), bench_flight b8eb68ca; piny shield/config/gate c3ccabe0/base.py.
