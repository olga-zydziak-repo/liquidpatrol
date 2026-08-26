#!/usr/bin/env python3
"""tools/k1_r2_dump.py ARM POINT BOOT — zrzut pól STOP R2 (format boot7, ANEKS_K1-15). Read-only, bez interpretacji."""
import sys, json, os

arm, point, boot = sys.argv[1], sys.argv[2], sys.argv[3]
pstr = point.replace(".", "_")
d = f"results/K1/{arm}/p{pstr}/boot{boot}"
m = json.load(open(f"{d}/manifest.json"))
j = json.load(open(f"{d}/judge.json")) if os.path.exists(f"{d}/judge.json") else {}
h = json.load(open(f"{d}/habitat.json")) if os.path.exists(f"{d}/habitat.json") else {}
w = m.get("watchdog") or {}
sc = m.get("spec_check") or {}
vc = m.get("vmax_check") or {}
ab = m.get("abrake_check") or {}
sn = (m.get("sanity") or {}).get("t_td") or {}
hc = h.get("h2_claim") or {}
pi = m.get("preinj_check") or {}

print(f"=== {arm}@{point} boot{boot} ===")
print(f"run_valid={m.get('run_valid')} | invalid_reason={m.get('invalid_reason')} | kind={m.get('kind')} | "
      f"judge_frozen={m.get('k1_judge_frozen')} shield_frozen={m.get('shield_frozen')}")
print(f"preinj: r@offboard={pi.get('r_offboard_m')} (max {pi.get('r_max_m')}) pass={pi.get('pass')}")
print(f"WATCHDOG: n_reinits={w.get('n_reinits')} sims={w.get('reinit_sims')} reasons={w.get('reinit_reasons')} "
      f"bias_max={w.get('bias_max_absmax')} armed_sim={w.get('armed_sim')} stopped={w.get('stopped_reason')}")
print(f"JUDGE: R_E={j.get('R_E')} breach={j.get('breach')} x_exc={j.get('x_exc')} r_max={j.get('r_max')} "
      f"r_td={j.get('r_td')} t_refuse_rel_s={j.get('t_refuse_rel_s')} t_td_s={j.get('t_td_s')} "
      f"touchdown={j.get('touchdown_found')} eps_td={j.get('eps_pos_touchdown_m')} t_inj_sim={j.get('t_inj_sim')}")
print(f"SPEC: match={sc.get('spec_match')} f_along={sc.get('k1_f_along')}(abs_df {sc.get('abs_df')}) "
      f"r_est_at_cut={sc.get('r_est_at_cut')} r_expected={sc.get('r_expected')} r_ok={sc.get('r_ok')}")
print(f"HABITAT roszczenia: {h.get('verdict')} | dsim_dwall={hc.get('dsim_dwall')} median_rtf={hc.get('median_rtf')} "
      f"min_rtf={hc.get('min_rtf')} n={hc.get('n')}")
print(f"VMAX pass={vc.get('pass')} v_gt_max={vc.get('v_gt_max_cruise')} | "
      f"ABRAKE(dstop) pass={ab.get('pass')} a_meas={ab.get('a_meas')} A_BRAKE={ab.get('A_BRAKE')} reached_stop={ab.get('reached_stop')}")
print(f"SANITY t_td: measured={sn.get('measured_s')} expected_from_h0={sn.get('expected_from_h0_s')} h0={sn.get('h0_m')}")
print(f"stall_in_reaction_window: {m.get('stall_in_reaction_window')}")
print(f"inj_info.n_reinits: {(m.get('inj_info') or {}).get('n_reinits')}")
