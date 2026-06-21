# 📓 NOC Operations Dashboard — Guide

## What is a NOC?
A Network Operations Centre (NOC) is the team that monitors and manages
a telecom network 24/7. They track alarms, dispatch engineers, and ensure
sites stay online. This project builds the data analytics layer behind a NOC.

---

## Data Sources (3 inputs)
| Source | Records | Description |
|--------|---------|-------------|
| `alarm_log.csv` | 4,000–6,000 | Every alarm raised across all sites |
| `site_inventory.csv` | 100 rows | Site metadata: region, technology, tenants |
| `field_dispatch_log.csv` | 1,000–2,000 | Engineer dispatches to resolve alarms |

---

## Execution Order
```bash
python scripts/generate_data.py       # Creates all 3 source files
python scripts/alarm_classifier.py    # SLA breach detection + urgency tiers
python scripts/noc_analysis.py        # MTTR, engineer rankings, charts
```

---

## Key Metrics

### MTTR (Mean Time To Resolve)
How long it takes to clear an alarm. SLA targets:
- Critical: ≤ 3 hours
- Major: ≤ 6 hours
- Minor: ≤ 24 hours

### Auto-Clear Rate
% of alarms that clear automatically without engineer dispatch.
High auto-clear = efficient, self-healing network.

### Engineer Response Time
Minutes from dispatch to site arrival. Lower = faster response.

---

## Sample Findings (Synthetic Data)
- Power Outage alarms have the highest total impact (~35% of downtime)
- Lagos region has fastest average MTTR (proximity to engineer pool)
- 45% of Minor and Warning alarms auto-clear without dispatch
- Multi-tenant sites (3 tenants) generate 60% more Critical alarms

---

## SQL Queries Included
See `sql/noc_queries.sql` for PostgreSQL queries covering:
1. MTTR by region with SLA breach %
2. Monthly alarm trend by severity
3. Top alarm types by total impact
4. Sites with most Critical alarms
5. Engineer workload and efficiency ranking
