## 🏃 Blue-Green Deployment Runbook (Stage 3 - HNG13)

### 1️⃣ Overview
This runbook provides step-by-step instructions for deploying, monitoring, and troubleshooting the **Blue/Green service** behind **Nginx** with automatic failover, manual toggle, and Slack-based alerts.

---

### 2️⃣ Environment Setup

1. **Clone the repository**
```bash
git clone <your_repo_url>
cd stage-3-task
```

2. **Create `.env` file**
```bash
cp .env.example .env
```
- Ensure variables are correctly set, e.g., `NGINX_TARGET`, `SLACK_WEBHOOK_URL`, `ERROR_RATE_THRESHOLD`, `WINDOW_SIZE`, `ALERT_COOLDOWN_SEC`.

3. **Pull Docker images**
```bash
docker pull yimikaade/wonderful:devops-stage-two
```

4. **Start Docker Compose stack**
```bash
docker compose up -d
```

---

### 3️⃣ Service Access
| Component | URL |
|-----------|-----|
| Gateway | http://<server_ip>:8080/version |
| Blue App | http://<server_ip>:8081/version |
| Green App | http://<server_ip>:8082/version |

Check the active pool:
```bash
curl -i http://<server_ip>:8080/version
```
Response should include `X-App-Pool: blue` initially.

---

### 4️⃣ Monitoring & Alerts

**Watcher (`watcher.py`)** monitors error rates and pool distribution, sending alerts to Slack.

**Steps:**
1. Ensure `.env` has `SLACK_WEBHOOK_URL` configured.
2. Run watcher inside your environment:
```bash
python3 watcher.py
```
3. The watcher logs requests, pool changes, and triggers alerts when error rate exceeds `ERROR_RATE_THRESHOLD`.

**Alert format on Slack:**
```
:fire: High Error Rate Detected!
Error rate exceeded threshold: 6.0% (limit 2.0%)
Time: 2025-10-30 21:41:09
Current Pool: blue
Requests Monitored: 64
Recommended Action: Inspect upstream logs or consider switching pools
```

---

### 5️⃣ Failover Simulation

1. **Confirm Blue is active:**
```bash
curl -i http://<server_ip>:8080/version
```
2. **Simulate Blue failure:**
```bash
curl -X POST http://<server_ip>:8081/chaos/start?mode=error
```
3. **Check Gateway:**
```bash
curl -i http://<server_ip>:8080/version
```
Should show `X-App-Pool: green`.
4. **Restore Blue:**
```bash
curl -X POST http://<server_ip>:8081/chaos/stop
curl -i http://<server_ip>:8080/version
```

---

### 6️⃣ Nginx Manual Pool Switching

1. Edit `.env`:
```
ACTIVE_POOL=green
```
2. Reload Nginx:
```bash
docker exec -it nginx_gateway nginx -s reload
```
3. Confirm active pool:
```bash
curl -i http://<server_ip>:8080/version
```

---

### 7️⃣ Logs

- **Nginx access log:** `/var/log/nginx/access.log blue_green
- **Nginx error log:** `/var/log/nginx/error.log`blue_green
- **Watcher logs:** stdout of `python3 watcher.py`

**Check logs inside container:**
```bash
docker exec -it nginx_gateway cat /var/log/nginx/access.log blue_green
```

---

### 8️⃣ Troubleshooting

**Slack alerts not showing:**
- Ensure `SLACK_WEBHOOK_URL` is correct.
- Check network connectivity from watcher container.
- Verify Python `requests` library is installed.

**Watcher not detecting errors:**
- Ensure `/fail` endpoint works: `curl -i http://<server_ip>:8080/fail`
- Confirm `NGINX_TARGET` points to correct gateway URL.
- Make sure `ERROR_RATE_THRESHOLD` is set low enough for testing.

**Nginx routing issues:**
- Inspect `nginx.conf.template` and `/etc/nginx/conf.d/default.conf`
- Test upstreams individually:
```bash
curl -i http://<server_ip>:8081/version
curl -i http://<server_ip>:8082/version
```

---

### 9️⃣ Cleanup
```bash
docker compose down
```
Removes containers, networks, and volumes.

---

**Author:** Adetola Ajala
**Track:** DevOps — HNG13 Internship
