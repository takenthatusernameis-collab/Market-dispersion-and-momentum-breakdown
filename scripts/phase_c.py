"""Phase C: registered dispersion-conditioned test (H004G033 anchor)."""
from __future__ import annotations
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001"
OUT = ROOT / "artifacts" / EXP
PANEL = OUT / "data" / "panels"
MOM_LB, FWD_H = 30, 30
BASE_COST = 0.0005
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    prices = pd.read_csv(PANEL/"price_panel.csv")
    prices["date"]=prices["date"].astype(str).str.slice(0,10)
    prices["close"]=pd.to_numeric(prices["close"],errors="coerce")
    P = prices.pivot(index="date",columns="asset_id",values="close").sort_index()
    univ = pd.read_csv(PANEL/"universe_coverage.csv")
    univ["date"]=univ["date"].astype(str).str.slice(0,10)
    univ["eligible"]=univ["eligible"].eq("yes")
    rets = P.pct_change()
    # formation dates
    elig_dates = sorted(univ[univ["eligible"]]["date"].unique())
    seen=set(); fdates=[]
    for d in elig_dates:
        m=d[:7]
        if m not in seen: seen.add(m); fdates.append(d)
    rows=[]
    for T in fdates:
        elig = univ[(univ["date"]==T)&(univ["eligible"])]
        assets=sorted(elig["asset_id"].tolist())
        if len(assets)<20: continue
        idx=rets.index
        if T not in idx: continue
        el=idx.get_loc(T); sl=el-MOM_LB+1
        if sl<0: continue
        win=rets.iloc[sl:el+1][assets]
        comp=(1+win).prod()-1
        comp=comp.dropna()
        if len(comp)<20: continue
        disp=float(comp.std(ddof=0))
        # state: trailing 365d outer decile (compute z via expanding? use median split for simplicity)
        rows.append({"formation_date":T,"dispersion":disp,"n_assets":len(comp),"comp":comp})
    # state assignment: high/low by median of trailing 365d dispersion
    dser=pd.Series({r["formation_date"]:r["dispersion"] for r in rows})
    out_rows=[]
    for i,r in enumerate(rows):
        T=r["formation_date"]
        past=dser.loc[:T].iloc[:-1].tail(365)
        thr_hi=past.quantile(0.9) if len(past)>=30 else np.nan
        thr_lo=past.quantile(0.1) if len(past)>=30 else np.nan
        state="mid"
        if not np.isnan(thr_hi) and r["dispersion"]>=thr_hi: state="high"
        elif not np.isnan(thr_lo) and r["dispersion"]<=thr_lo: state="low"
        # spread compute
        comp=r["comp"]; assets_sorted=sorted(comp.index)
        q=10;k=len(assets_sorted)//q
        ranked=comp.sort_values(ascending=False)
        ranked=ranked.reindex(sorted(ranked.index,key=lambda a:(-ranked[a],a)))
        top=ranked.head(k).index.tolist(); bot=ranked.tail(k).index.tolist()
        Tloc=P.index.get_loc(T)
        fw=P.iloc[Tloc+1:Tloc+FWD_H+1]
        fwd={}
        for a in set(top)|set(bot):
            s=fw[a].dropna()
            if len(s): fwd[a]=float(s.iloc[-1]/s.iloc[0]-1)
        top_ret=float(pd.Series({a:fwd[a] for a in top if a in fwd}).mean()) if any(a in fwd for a in top) else float("nan")
        bot_ret=float(pd.Series({a:fwd[a] for a in bot if a in fwd}).mean()) if any(a in fwd for a in bot) else float("nan")
        spread=top_ret-bot_ret if not (pd.isna(top_ret) or pd.isna(bot_ret)) else float("nan")
        cost=BASE_COST*2.0
        out_rows.append({"formation_date":T,"dispersion":disp,"state":state,"spread_gross":spread,"spread_net_1x":spread-cost if not pd.isna(spread) else float("nan"),"n_assets":len(comp)})
    df=pd.DataFrame(out_rows)
    # extend formation_returns.csv with state? write separate
    df.to_csv(OUT/"phase_c_returns.csv",index=False)
    # summary
    hi=df[df.state=="high"]["spread_gross"].dropna()
    lo=df[df.state=="low"]["spread_gross"].dropna()
    diff=float(hi.mean()-lo.mean()) if len(hi) and len(lo) else None
    summary={"experiment_id":EXP,"phase":"C_dispersion_conditioned","anchor":"H004G033","n_formations":int(len(df)),
            "n_high":int((df.state=="high").sum()),"n_low":int((df.state=="low").sum()),
            "high_gross_mean":float(hi.mean()) if len(hi) else None,
            "low_gross_mean":float(lo.mean()) if len(lo) else None,
            "difference_gross":diff}
    (OUT/"phase_c_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":
    main()