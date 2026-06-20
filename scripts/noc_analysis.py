"""noc_analysis.py — MTTR, engineer rankings, alarm breakdown, charts."""
import pandas as pd, numpy as np, matplotlib.pyplot as plt, os

BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW=os.path.join(BASE,"data","raw")
PROC=os.path.join(BASE,"data","processed"); os.makedirs(PROC,exist_ok=True)
OUT=os.path.join(BASE,"outputs"); os.makedirs(OUT,exist_ok=True)

alarms=pd.read_csv(f"{RAW}/alarm_log.csv",parse_dates=["start_time","clear_time"])
sites=pd.read_csv(f"{RAW}/site_inventory.csv")
dispatch=pd.read_csv(f"{RAW}/field_dispatch_log.csv",parse_dates=["dispatch_time","arrival_time","closure_time"])

alarms=alarms.merge(sites[["site_id","region","technology","tenant_count"]],on="site_id",how="left")
dispatch["response_time_mins"]=(dispatch["arrival_time"]-dispatch["dispatch_time"]).dt.total_seconds()/60
master=alarms.merge(dispatch[["alarm_id","engineer_id","response_time_mins","resolution_code"]],on="alarm_id",how="left")
master.to_csv(f"{PROC}/noc_master.csv",index=False)

print("=== MTTR BY REGION ===")
region=master[master["severity"].isin(["Critical","Major"])].groupby("region").agg(
    alarms=("alarm_id","count"), avg_mttr=("duration_hrs","mean"),
    sla_breaches=("duration_hrs",lambda x:(x>3).sum())).reset_index()
region["sla_breach_pct"]=(region["sla_breaches"]/region["alarms"]*100).round(1)
print(region.sort_values("sla_breach_pct",ascending=False).to_string(index=False))
region.to_csv(f"{OUT}/mttr_by_region.csv",index=False)

print("\n=== ENGINEER LEADERBOARD ===")
eng=dispatch.groupby("engineer_id").agg(jobs=("alarm_id","count"),
    avg_resp=("response_time_mins","mean"),
    fixed=("resolution_code",lambda x:(x=="FIXED").sum())).reset_index()
eng["resolution_pct"]=(eng["fixed"]/eng["jobs"]*100).round(1)
print(eng.sort_values("avg_resp").head(10).to_string(index=False))
eng.to_csv(f"{OUT}/engineer_leaderboard.csv",index=False)

fig,axes=plt.subplots(1,2,figsize=(14,6))
fig.suptitle("NOC Operations Dashboard",fontsize=14,fontweight="bold")
region.plot(kind="barh",x="region",y="avg_mttr",ax=axes[0],color="steelblue",legend=False)
axes[0].axvline(3,color="red",linestyle="--",label="SLA 3hrs"); axes[0].legend()
axes[0].set_xlabel("Avg MTTR (hrs)"); axes[0].set_title("MTTR by Region")
sc=master.groupby("severity")["alarm_id"].count()
colors={"Critical":"#e74c3c","Major":"#e67e22","Minor":"#f1c40f","Warning":"#95a5a6"}
sc.plot(kind="bar",ax=axes[1],color=[colors.get(s,"steelblue") for s in sc.index],rot=0)
axes[1].set_title("Alarm Volume by Severity"); axes[1].set_ylabel("Count")
plt.tight_layout(); plt.savefig(f"{OUT}/noc_charts.png",dpi=150,bbox_inches="tight")
print("\n✅ NOC analysis complete.")
