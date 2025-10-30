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

#### **What This Means**
- The system detected a change in the active deployment pool.  
- This is typically an automated response to health checks or manual configuration changes.  
- The failover mechanism is working as designed.

#### **Operator Actions**

1. ✅ **Verify Intentionality** – Check if this was a planned deployment
   ```bash
   # Check deployment logs
   docker-compose logs nginx --tail=20
✅ Monitor Application Health – Ensure the new active pool is healthy

bash
Copy code
# Test the new active pool
curl http://localhost:8080/version
curl http://localhost:8082/  # Green pool direct
✅ Check Error Rates – Review if failover was triggered by errors

bash
Copy code
# Check recent error rates
docker-compose logs alert_watcher --tail=30 | grep "Error rate"
✅ Update Documentation – Note the failover time and reason.

💡 No Immediate Action Required if this was a planned failover.

When to Escalate
Unplanned failovers during peak traffic

Multiple rapid failovers (thrashing)

Failover to an unhealthy pool

2. ⚠️ Elevated 5xx Error Rate
Severity: High
Description: The error rate for 5xx responses has exceeded the configured threshold (default: 2.0%).

Alert Format
sql
Copy code
⚠️ Elevated 5xx error rate  
30.00% 5xx over last 10 requests (threshold 2.0%)  
Current Pool: blue  
Requests Monitored: 96
What This Means
More than 2% of recent requests resulted in server errors (5xx).

This could indicate application instability or infrastructure issues.

The system is experiencing degraded performance.

Operator Actions
🚨 Immediate Investigation

bash
Copy code
# Check application logs
docker-compose logs app_blue --tail=50
docker-compose logs app_green --tail=50

# Check nginx error logs
docker-compose exec nginx tail -f /var/log/nginx/error.log
🔍 Identify Error Patterns

bash
Copy code
# Check for specific error types
docker-compose logs alert_watcher | grep "status=5"

# Monitor real-time traffic
docker-compose exec nginx tail -f /var/log/nginx/access.log | grep "status=5"
🛠️ Immediate Mitigation

bash
Copy code
# If errors persist, consider failover
# Update .env: ACTIVE_POOL=green (or blue)
docker-compose stop nginx
docker-compose up -d nginx
📊 Monitor Recovery

bash
Copy code
# Watch error rates post-mitigation
docker-compose logs -f alert_watcher
📝 Document Incident

Record time of detection

Note actions taken

Document root cause when identified

When to Escalate
Error rate > 10% for more than 5 minutes

Multiple services affected

Customer impact reported

🧩 System Components
Monitoring Architecture
mathematica
Copy code
Nginx (Load Balancer) → Blue/Green Pools → Alert Watcher → Slack
Key Configuration
Variable	Description	Default
ERROR_RATE_THRESHOLD	Alert when error rate exceeds	2.0%
WINDOW_SIZE	Requests to monitor	200
ALERT_COOLDOWN_SEC	Prevent alert spam	300s
ACTIVE_POOL	Current active deployment	blue

Environment Variables
bash
Copy code
ERROR_RATE_THRESHOLD=2.0
WINDOW_SIZE=200
ALERT_COOLDOWN_SEC=300
ACTIVE_POOL=blue
🧰 Troubleshooting Guide
1. False Positive Failover Alerts
Symptoms: Failover alerts when no deployment occurred
Solution: Check Nginx configuration and header propagation

bash
Copy code
curl -v http://localhost:8080/version
2. High Error Rate During Deployment
Symptoms: Spikes in error rates during blue/green switches
Solution: This is normal during cutover; monitor for stabilization.

3. Alert Storm
Symptoms: Repeated alerts for the same issue
Solution: Increase cooldown period

bash
Copy code
export ALERT_COOLDOWN_SEC=600
docker-compose restart alert_watcher
4. Connection Issues Between Services
Symptoms: “Failed to resolve 'nginx'” errors
Solution: Restart Docker network and services

bash
Copy code
docker-compose down
docker-compose up -d
🩺 Maintenance Procedures
Regular Health Checks
bash
Copy code
# Daily system check
docker-compose ps
curl http://localhost:8080/version
docker-compose logs alert_watcher --tail=10
Deployment Procedures
Pre-deployment
bash
Copy code
# Verify current active pool
curl -s http://localhost:8080/version | grep -o "pool:[a-z]*"

# Check error rates
docker-compose logs alert_watcher --tail=20 | grep "Error rate"
During Deployment
Monitor for expected failover alerts.

Post-deployment
Verify new pool health and error rates.

🧪 Alert Testing
Test the alert system monthly:

bash
Copy code
# Trigger test failover
# Update .env with opposite ACTIVE_POOL
docker-compose stop nginx && docker-compose up -d nginx

# Generate traffic to trigger detection
for i in {1..10}; do curl http://localhost:8080/version; sleep 1; done
📞 Contact Information
Primary On-call: [Team Lead Name]

Secondary: [Backup Engineer Name]

Slack Channel: #deployment-alerts

Escalation Path: [Manager Name] → [Director Name]

🕓 Revision History
Date	Description
2025-10-30	Initial runbook creation
2025-10-30	Added troubleshooting guide and maintenance procedures

✅ Summary
This runbook provides:

Clear alert explanations – What each alert means in simple terms

Step-by-step procedures – Exactly what operators should do

Command references – Ready-to-use troubleshooting commands

Escalation guidelines – When to call for help

Maintenance procedures – Regular health checks and testing
