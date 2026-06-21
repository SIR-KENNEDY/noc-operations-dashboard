-- ══════════════════════════════════════════════════════
-- NOC Operations — SQL Query Collection
-- Compatible with PostgreSQL 13+
-- ══════════════════════════════════════════════════════

-- 1. MTTR by region with SLA breach percentage
SELECT
    s.region,
    COUNT(a.alarm_id)                                                 AS total_alarms,
    ROUND(AVG(a.duration_hrs), 2)                                     AS avg_mttr_hrs,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY a.duration_hrs)::numeric, 2)
                                                                      AS median_mttr_hrs,
    SUM(CASE WHEN a.duration_hrs > 3 AND a.severity = 'Critical' THEN 1 ELSE 0 END)
                                                                      AS critical_sla_breaches,
    ROUND(SUM(CASE WHEN a.duration_hrs > 3 AND a.severity = 'Critical' THEN 1 ELSE 0 END)
        * 100.0 / NULLIF(SUM(CASE WHEN a.severity = 'Critical' THEN 1 ELSE 0 END), 0), 1)
                                                                      AS critical_breach_pct
FROM alarms a
JOIN site_inventory s USING (site_id)
GROUP BY s.region
ORDER BY avg_mttr_hrs DESC;

-- 2. Alarm volume trend by month and severity
SELECT
    DATE_TRUNC('month', start_time)                                   AS month,
    severity,
    COUNT(*)                                                           AS alarm_count,
    ROUND(AVG(duration_hrs), 2)                                       AS avg_duration_hrs,
    SUM(COUNT(*)) OVER (PARTITION BY severity ORDER BY DATE_TRUNC('month', start_time))
                                                                      AS running_total
FROM alarms
GROUP BY DATE_TRUNC('month', start_time), severity
ORDER BY month, severity;

-- 3. Top alarm types by total impact
SELECT
    alarm_type,
    COUNT(*)                                                           AS occurrence_count,
    ROUND(SUM(duration_hrs), 1)                                       AS total_impact_hrs,
    ROUND(AVG(duration_hrs), 2)                                       AS avg_duration_hrs,
    SUM(CASE WHEN auto_cleared THEN 1 ELSE 0 END)                     AS auto_cleared_count,
    ROUND(SUM(CASE WHEN auto_cleared THEN 1 ELSE 0 END)*100.0/COUNT(*), 1)
                                                                      AS auto_clear_pct,
    ROUND(SUM(duration_hrs)/SUM(SUM(duration_hrs)) OVER ()*100, 1)   AS share_of_downtime_pct
FROM alarms
GROUP BY alarm_type
ORDER BY total_impact_hrs DESC;

-- 4. Sites with most frequent Critical alarms
SELECT
    a.site_id, s.region, s.technology, s.tenant_count,
    COUNT(CASE WHEN a.severity='Critical' THEN 1 END)                 AS critical_count,
    ROUND(AVG(CASE WHEN a.severity='Critical' THEN a.duration_hrs END),2)
                                                                      AS avg_critical_mttr,
    ROUND(SUM(a.duration_hrs),1)                                      AS total_downtime_hrs,
    RANK() OVER (ORDER BY COUNT(CASE WHEN a.severity='Critical' THEN 1 END) DESC)
                                                                      AS criticality_rank
FROM alarms a
JOIN site_inventory s USING (site_id)
GROUP BY a.site_id, s.region, s.technology, s.tenant_count
HAVING COUNT(CASE WHEN a.severity='Critical' THEN 1 END) > 0
ORDER BY criticality_rank
LIMIT 20;

-- 5. Engineer workload and efficiency
SELECT
    d.engineer_id,
    COUNT(DISTINCT d.site_id)                                         AS sites_attended,
    COUNT(d.alarm_id)                                                 AS total_dispatches,
    ROUND(AVG(EXTRACT(EPOCH FROM(d.arrival_time-d.dispatch_time))/60),1)
                                                                      AS avg_response_mins,
    SUM(CASE WHEN d.resolution_code='FIXED' THEN 1 ELSE 0 END)        AS resolved,
    ROUND(SUM(CASE WHEN d.resolution_code='FIXED' THEN 1 ELSE 0 END)*100.0/COUNT(*),1)
                                                                      AS fix_rate_pct,
    RANK() OVER (ORDER BY AVG(EXTRACT(EPOCH FROM(d.arrival_time-d.dispatch_time))/60))
                                                                      AS speed_rank
FROM field_dispatch d
WHERE d.arrival_time IS NOT NULL
GROUP BY d.engineer_id
HAVING COUNT(*) >= 5
ORDER BY speed_rank;
