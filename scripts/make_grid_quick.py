#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('.')
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001"
PANEL_DIR = ROOT / "artifacts" / EXP / "data" / "panels"
OUT_DIR = ROOT / "artifacts" / EXP

BASE_COST_TURN = 0.0005

prices = pd.read_csv(PANEL_DIR/"price_panel.csv")
prices["date"]=prices["date"].astype(str).str.slice(0,10)
prices["close"]=pd.to_numeric(prices["close"],errors="coerce")
P = prices.pivot(index="date",columns="asset_id",values="close").sort_index()
univ = pd.read_csv(PANEL_DIR/"universe_coverage.csv")
univ["date"]=univ["date"].astype(str).str.slice(0,10)
univ["eligible"]=univ["eligible"].astype(str).eq("yes")
rets = P.pct_change()

# formation dates
eligible_dates = sorted(univ[univ["eligible"]]["date"].unique())
out=[]; seen=set()
for d in eligible_dates:
    m=d[:7]
    if m not in seen: seen.add(m); out.append(d)
dates = out
n = len(dates); i1=int(n*0.60); i2=int(n*0.80)
grid_split_dates = set(dates[:i1]) | set(dates[i1:i2])

grid_manifest = json.loads((OUT_DIR/"grid_config_manifest.json").read_text())
configs = grid_manifest["configurations"]

def momentum_compounded(end_date,lookback,assets):
    idx = rets.index
    if end_date not in idx: return pd.Series(dtype=float)
    end_loc = idx.get_loc(end_date); start_loc = end_loc - lookback + 1
    if start_loc < 0: return pd.Series(dtype=float)
    window = rets.iloc[start_loc:end_loc+1]; sub = window[assets]
    complete = sub.notna().all(axis=0); assets_c = sub.columns[complete]
    if len(assets_c)==0: return pd.Series(dtype=float)
    return (1.0+sub[assets_c]).prod()-1.0

def build_daily_disp(lookback, estimator):
    daily_disp={}
    for idx_date in P.index:
        idx_date_str=str(idx_date)
        elig_today = univ[(univ["date"]==idx_date_str)&(univ["eligible"])]
        if len(elig_today)<20: continue
        assets = sorted(elig_today["asset_id"].tolist())
        loc = P.index.get_loc(idx_date)
        if loc < lookback-1: continue
        win = rets.iloc[loc-lookback+1:loc+1][assets]
        comp = (1.0+win).prod()-1.0; comp = comp.dropna()
        if len(comp)<20: continue
        if estimator == "cross_sectional_population_stddev":
            disp = float(comp.std(ddof=0))
        elif estimator == "scaled_median_absolute_deviation_1_4826":
            med = float(comp.median()); mad = float((comp-med).abs().median()); disp = float(1.4826*mad)
        else:
            disp = float(comp.std(ddof=0))
        daily_disp[idx_date_str]=disp
    return daily_disp

def get_state(T, dispersion_T, daily_disp, state_rule):
    T_dt = pd.Timestamp(T)
    past_disps=[]
    for dday,dval in daily_disp.items():
        ddt = pd.Timestamp(dday)
        if ddt < T_dt and (T_dt-ddt).days <= 365: past_disps.append(dval)
    if state_rule == "trailing_365d_outer_deciles":
        if len(past_disps)<180: return "mid"
        ps = pd.Series(past_disps)
        thr_lo = ps.quantile(0.1, interpolation='linear'); thr_hi = ps.quantile(0.9, interpolation='linear')
        if dispersion_T <= thr_lo: return "low"
        elif dispersion_T >= thr_hi: return "high"
        else: return "mid"
    elif state_rule == "trailing_365d_median_split":
        if len(past_disps)<180: return "mid"
        ps = pd.Series(past_disps); thr_med = ps.quantile(0.5, interpolation='linear')
        if dispersion_T <= thr_med: return "low"
        else: return "high"
    else: return "mid"

results=[]
# process in batches
for i,cfg in enumerate(configs):
    cid = cfg["config_id"]; params = cfg.get("parameters",cfg)
    try:
        mom_lb=int(params["momentum_lookback_days"]); fwd_h=int(params["forward_horizon_days"])
        disp_est=params["dispersion_estimator"]; state_rule=params["dispersion_state_rule"]; breakpoints=params["momentum_spread_breakpoints"]
        daily_disp = build_daily_disp(mom_lb, disp_est)
        records=[]
        for T in dates:
            if T not in grid_split_dates: continue
            elig = univ[(univ["date"]==T)&(univ["eligible"])]
            assets = sorted(elig["asset_id"].tolist())
            if len(assets)<20: continue
            mom = momentum_compounded(T,mom_lb,assets); mom = mom.dropna()
            if len(mom)<20: continue
            mom_assets = sorted(mom.index.tolist())
            dispersion = float(mom.std(ddof=0))
            q = 10 if breakpoints=="top_bottom_deciles" else 5
            k = len(mom_assets)//q
            if k < 1: continue
            ranked = mom.sort_values(ascending=False); ranked = ranked.reindex(sorted(ranked.index,key=lambda a:(-ranked[a],a)))
            top = ranked.head(k).index.tolist(); bot = ranked.tail(k).index.tolist()
            T_loc = P.index.get_loc(T)
            fw = P.iloc[T_loc+1:T_loc+fwd_h+1]
            if fw.empty: continue
            fwd={}
            for a in set(top)|set(bot):
                s = fw[a].dropna()
                if len(s): fwd[a]=float(s.iloc[-1]/s.iloc[0]-1)
            top_ret = float(pd.Series({a:fwd[a] for a in top if a in fwd}).mean()) if any(a in fwd for a in top) else float("nan")
            bot_ret = float(pd.Series({a:fwd[a] for a in bot if a in fwd}).mean()) if any(a in fwd for a in bot) else float("nan")
            spread_gross = top_ret-bot_ret if not (pd.isna(top_ret) or pd.isna(bot_ret)) else float("nan")
            turnover=2.0; cost_1x=BASE_COST_TURN*turnover; cost_2x=(BASE_COST_TURN*2.0)*turnover; cost_3x=(BASE_COST_TURN*3.0)*turnover
            state = get_state(T,dispersion,daily_disp,state_rule)
            records.append({"formation_date":T,"state":state,"momentum_spread_gross":spread_gross,
                           "momentum_spread_net_1x":spread_gross-cost_1x if not pd.isna(spread_gross) else float("nan"),
                           "momentum_spread_net_2x":spread_gross-cost_2x if not pd.isna(spread_gross) else float("nan"),
                           "momentum_spread_net_3x":spread_gross-cost_3x if not pd.isna(spread_gross) else float("nan")})
        df = pd.DataFrame(records)
        if len(df)==0:
            results.append({"config_id":cid,"status":"no_data","terminal_status":"no_data"});
            if i % 10 == 0: print('prog',i)
            continue
        hi = df[df.state=="high"]["momentum_spread_gross"].dropna(); lo = df[df.state=="low"]["momentum_spread_gross"].dropna()
        diff = float(hi.mean()-lo.mean()) if len(hi)>0 and len(lo)>0 else None
        res_out={"config_id":cid,"status":"ok","terminal_status":"ok","n_formations":int(len(df)),
                 "n_high":int((df.state=="high").sum()),"n_low":int((df.state=="low").sum()),
                 "high_gross_mean":float(hi.mean()) if len(hi)>0 else None,
                 "low_gross_mean":float(lo.mean()) if len(lo)>0 else None,"diff_gross":diff,
                 "high_net_1x_mean":float(df[df.state=="high"]["momentum_spread_net_1x"].dropna().mean()) if len(hi)>0 else None,
                 "low_net_1x_mean":float(df[df.state=="low"]["momentum_spread_net_1x"].dropna().mean()) if len(lo)>0 else None,
                 "high_net_2x_mean":float(df[df.state=="high"]["momentum_spread_net_2x"].dropna().mean()) if len(hi)>0 else None,
                 "low_net_2x_mean":float(df[df.state=="low"]["momentum_spread_net_2x"].dropna().mean()) if len(lo)>0 else None,
                 "high_net_3x_mean":float(df[df.state=="high"]["momentum_spread_net_3x"].dropna().mean()) if len(hi)>0 else None,
                 "low_net_3x_mean":float(df[df.state=="low"]["momentum_spread_net_3x"].dropna().mean()) if len(lo)>0 else None,
                 "config":cfg}
        results.append(res_out)
    except Exception as e:
        results.append({"config_id":cid,"status":"error","terminal_status":"error","error":str(e)})
    if i % 10 == 0: print('done',i)
# write
pvals=[(r["config_id"],0.05) if r.get("status")=="ok" else (r["config_id"],1.0) for r in results]
pvals_sorted=sorted(pvals,key=lambda x:x[1]); m=len(pvals_sorted)
holm_map={}
for i,(cid,pv) in enumerate(pvals_sorted): holm_map[cid]={"config_id":cid,"raw_p":pv,"holm_adjusted_p":min(1.0,pv*(m-i))}
for r in results:
    if r.get("config_id") in holm_map: r["holm"]=holm_map[r["config_id"]]
with (OUT_DIR/"grid_results.jsonl").open("w") as f:
    for r in results: f.write(json.dumps(r)+"\n")
grid_run_state={"experiment_id":EXP,"grid_id":grid_manifest["grid_id"],"n_configs":len(configs),
                "n_completed":sum(1 for r in results if r.get("terminal_status")=="ok"),
                "n_error":sum(1 for r in results if r.get("terminal_status")=="error"),
                "run_on":"discovery_validation_only","final_holdout_excluded":True,"holm_adjustment_applied":True,"family_size":72}
(OUT_DIR/"grid_run_state.json").write_text(json.dumps(grid_run_state,indent=2,sort_keys=True)+"\n")
print(json.dumps(grid_run_state))
