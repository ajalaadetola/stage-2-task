# Blue/Green Deployment Runbook

## Alerts and Operator Actions

### 🚨 Alert: Failover Detected
**What happened**: Traffic automatically switched from primary to backup pool
**Example**: "Failover detected: blue → green"

**Operator Actions**:
1. Check primary pool health:
   ```bash
   curl http://localhost:8081/healthz
