# 🧭 Blue/Green Deployment Alert Runbook

## 📘 Overview
This runbook provides guidance for responding to alerts from the **Blue/Green deployment monitoring system**.  
The system monitors traffic routing between blue and green environments and alerts on **failovers** and **error rate thresholds**.

---

## ⚠️ Alert Types

### 1. 🚨 Failover Detected
**Severity**: Warning  
**Description**: Traffic has automatically switched between blue and green deployment pools.

#### **Alert Format**

🚨 Failover detected: blue → green
Failover detected at 2025-10-30T19:35:22.123456Z
Window=15, errors=2 (13.33%)
Release: green-1.0.0
Upstream status: 500, 200
Upstream addr: 172.18.0.2:3000, 172.18.0.3:3000
