"""generate_data.py — Alarm log, site inventory, field dispatch data for 100 sites."""
import pandas as pd, numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(33)
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW=os.path.join(BASE,"data","raw"); os.makedirs(RAW,exist_ok=True)
SEVERITIES=["Critical","Major","Minor","Warning"]; SEV_W=[0.15,0.30,0.35,0.20]
TYPES=["Power Outage","High VSWR","Link Down","Battery Low","Generator Fault","Fan Failure","Temp Alert"]
REGIONS=["Lagos","Abuja","Port Harcourt","Kano","Enugu"]
N_SITES=100; START=datetime(2023,1,1)

sites=pd.DataFrame({"site_id":[f"SITE_{str(i).zfill(3)}" for i in range(1,N_SITES+1)],
    "region":np.random.choice(REGIONS,N_SITES),
    "technology":np.random.choice(["2G","3G","4G"],N_SITES,p=[0.1,0.3,0.6]),
    "tenant_count":np.random.choice([1,2,3],N_SITES,p=[0.5,0.35,0.15])})

alarms=[]; dispatches=[]
for _,s in sites.iterrows():
    for _ in range(np.random.randint(20,60)):
        sev=np.random.choice(SEVERITIES,p=SEV_W); atype=np.random.choice(TYPES)
        start=START+timedelta(hours=int(np.random.randint(0,4380)))
        dur=max(0.1,np.random.exponential({"Critical":3.5,"Major":2.0,"Minor":0.8,"Warning":0.3}[sev]))
        end=start+timedelta(hours=dur)
        auto=int(sev in ["Minor","Warning"] and np.random.random()<0.45)
        aid=f"ALM{np.random.randint(100000,999999)}"
        alarms.append({"alarm_id":aid,"site_id":s.site_id,"region":s.region,
            "severity":sev,"alarm_type":atype,"start_time":start,"clear_time":end,
            "duration_hrs":round(dur,2),"auto_cleared":auto})
        if not auto and sev in ["Critical","Major"]:
            resp=np.random.uniform(15,180)
            dispatches.append({"alarm_id":aid,"site_id":s.site_id,
                "engineer_id":f"ENG{np.random.randint(10,30)}",
                "dispatch_time":start+timedelta(minutes=15),
                "arrival_time":start+timedelta(minutes=15+resp),
                "closure_time":end,
                "resolution_code":np.random.choice(["FIXED","WORKAROUND","ESCALATED"])})

pd.DataFrame(alarms).to_csv(f"{RAW}/alarm_log.csv",index=False)
pd.DataFrame(dispatches).to_csv(f"{RAW}/field_dispatch_log.csv",index=False)
sites.to_csv(f"{RAW}/site_inventory.csv",index=False)
print(f"Generated {len(alarms):,} alarms and {len(dispatches):,} dispatches.")
