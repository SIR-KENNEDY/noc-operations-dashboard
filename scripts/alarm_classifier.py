"""
alarm_classifier.py
===================
Classifies alarms by urgency tier, estimates expected resolution time,
and flags alarms likely to breach SLA before resolution.

Run after generate_data.py
"""
import pandas as pd
import numpy as np
import os

BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW     = os.path.join(BASE, "data", "raw")
PROC    = os.path.join(BASE, "data", "processed")
OUTPUTS = os.path.join(BASE, "outputs")
os.makedirs(PROC, exist_ok=True); os.makedirs(OUTPUTS, exist_ok=True)

df    = pd.read_csv(f"{RAW}/alarm_log.csv", parse_dates=["start_time","clear_time"])
sites = pd.read_csv(f"{RAW}/site_inventory.csv")
df    = df.merge(sites[["site_id","region","tenant_count"]], on="site_id", how="left")

print("="*55)
print("  ALARM CLASSIFICATION & SLA RISK ENGINE")
print("="*55)

# ── SLA THRESHOLDS (hours) ─────────────────────────────────────────
SLA_HOURS = {"Critical": 3.0, "Major": 6.0, "Minor": 24.0, "Warning": 48.0}

# ── CLASSIFY ALARMS ────────────────────────────────────────────────
df["sla_threshold_hrs"]  = df["severity"].map(SLA_HOURS)
df["sla_breached"]       = (df["duration_hrs"] > df["sla_threshold_hrs"]).astype(int)
df["breach_margin_hrs"]  = (df["duration_hrs"] - df["sla_threshold_hrs"]).round(2)

# Urgency tier (compound: severity + tenant count)
def urgency(row):
    base = {"Critical":4,"Major":3,"Minor":2,"Warning":1}.get(row["severity"],1)
    tenant_bump = 1 if row["tenant_count"] >= 3 else 0
    score = base + tenant_bump
    return {5:"URGENT",4:"HIGH",3:"MEDIUM",2:"LOW",1:"INFO"}.get(score,"MEDIUM")

df["urgency_tier"] = df.apply(urgency, axis=1)

print(f"\nAlarm Summary:")
print(f"  Total alarms: {len(df):,}")
print(f"  SLA breaches: {df['sla_breached'].sum():,} ({df['sla_breached'].mean()*100:.1f}%)")
print(f"\nSLA Breach Rate by Severity:")
breach_rate = df.groupby("severity").agg(
    alarms=("alarm_id","count"),
    breaches=("sla_breached","sum"),
    avg_duration=("duration_hrs","mean"),
).reset_index()
breach_rate["breach_pct"] = (breach_rate["breaches"]/breach_rate["alarms"]*100).round(1)
print(breach_rate.sort_values("breach_pct", ascending=False).to_string(index=False))

print(f"\nUrgency Distribution:")
print(df["urgency_tier"].value_counts().to_string())

df.to_csv(f"{PROC}/alarms_classified.csv", index=False)
print(f"\n✅ Classified alarms saved.")
