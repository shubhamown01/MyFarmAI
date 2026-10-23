# Phase P10 — Performance & Reliability

**Status:** ⏳ READY (awaits P4 service + P8 ag behavior + P9 security)  
**Prerequisite:** P4 service deployed; P8/P9 complete  
**Blocks:** P11

---

## 1. Objective

Establish reproducible benchmarks, reliability targets, and operational procedures for the PersonaPlex voice service to ensure production readiness.

---

## 2. Benchmark Suite

### P10-01: Latency Benchmarks

| Metric | Definition | Target (A100 80GB) | Measurement Method |
|--------|------------|-------------------|-------------------|
| **First-audio latency** | User stops speaking → first audio chunk | < 500 ms | Timestamp: `user_stop` → `first_audio_chunk` |
| **End-to-end latency** | User stops → agent starts speaking | < 800 ms | Timestamp: `user_stop` → `agent_first_audio` |
| **Interruption latency** | User interrupts → agent stops | < 300 ms | Timestamp: `interrupt_signal` → `agent_stop` |
| **Backchannel latency** | User backchannel → agent acknowledges | < 200 ms | Timestamp: `backchannel` → `agent_ack` |
| **Cold start** | Service start → `/health/ready` OK | < 60 sec | Timestamp: `process_start` → `ready_ok` |
| **Model load time** | Process start → model ready | < 30 sec | Timestamp: `process_start` → `model_loaded` |

### P10-02: Throughput & Concurrency

| Metric | Target (A100 40GB) | Target (A100 80GB) | Measurement |
|--------|-------------------|-------------------|-------------|
| Max concurrent sessions | 2 | 4 | Ramp until OOM/503 |
| Sessions per minute | 4 | 8 | Sustained 10 min |
| Audio throughput | 24 kbps/session | 24 kbps/session | Measured |
| GPU utilization | 70–90% | 60–80% | `nvidia-smi` avg |

---

## 3. Reliability Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Uptime | 99.9% (monthly) | Health check success rate |
| MTBF | > 72 hours | Mean time between failures |
| MTTR | < 5 minutes | Mean time to recovery |
| Graceful degradation | Text chat works when voice down | Integration test |
| Session survival | > 99.9% sessions complete | Session completion rate |

---

## 3. Failure Mode Testing

### P10-03: Required Failure Tests

| Failure Scenario | Test Method | Expected Behavior |
|------------------|-------------|-------------------|
| GPU OOM | Load 2× max sessions | 429 on new sessions; existing continue |
| GPU disconnect | `nvidia-smi -r` during inference | 503 `GPU_UNAVAILABLE`; sessions terminate cleanly |
| Model corruption | Flip bit in weights | Load fails fast; clear error |
| Network partition | Block egress to PersonaPlex | Buffer 5s; reconnect or 503 |
| Client disconnect | Close WS mid-stream | Cleanup session; release resources |
| Audio buffer overflow | Send 10 min audio | 413 `AUDIO_TOO_LARGE` |
| Invalid audio format | Upload MP3 as PCM | 400 `INVALID_AUDIO_FORMAT` |
| Empty audio | 0-byte chunk | 400 `EMPTY_AUDIO` |
| Concurrent overload | 10× max sessions | Queue/429; no OOM |
| Model reload | Hot reload on config change | Zero-downtime if possible |

---

## 3. Benchmark Automation

```bash
# benchmark.sh
#!/usr/bin/env bash
set -euo pipefail

SERVICE_URL="${VOICE_SERVICE_URL:-http://localhost:8002}"
RESULTS_DIR="benchmarks/$(date +%Y%m%d_%H%M%S)"

mkdir -p "$RESULTS_DIR"

echo "=== PersonaPlex Benchmark Suite ==="
echo "Service: $SERVICE_URL"
echo "Results: $RESULTS_DIR"

# 1. Health checks
echo "--- Health Checks ---"
curl -s "$SERVICE_URL/health/live" | jq .
curl -s "$SERVICE_URL/health/ready" | jq .

# 2. Model info
curl -s "$SERVICE_URL/v1/model/info" | jq .

# 3. Latency benchmarks (requires test audio corpus)
python3 benchmark_latency.py --url "$SERVICE_URL" --output "$RESULTS_DIR/latency.json"

# 4. Concurrency test
python3 benchmark_concurrency.py --url "$SERVICE_URL" --max-sessions 4 --duration 600

# 5. Failure injection
python3 benchmark_failures.py --url "$SERVICE_URL"

# 6. Generate report
python3 generate_report.py --input "$RESULTS_DIR" --output "$RESULTS_DIR/REPORT.md"

echo "Benchmark complete. Report: $RESULTS_DIR/REPORT.md"
```

---

## 3. Reliability Testing

### P10-04: Long-Run Stability Test
```bash
# stability_test.sh
# Run for 24 hours with simulated load
# Metrics collected every 60s:
# - Active sessions
# - VRAM/RAM usage
# - Error rate
# - Latency percentiles
# - GPU temperature
# Alert if: error rate > 1%, latency p99 > 2s, VRAM > 90%
```

### P10-05: Chaos Engineering
| Experiment | Tool | Frequency |
|------------|------|-----------|
| Kill PersonaPlex pod | `kubectl delete pod` | Weekly |
| Network partition | `tc qdisc add netem` | Monthly |
| GPU stress | `gpu-burn` | Monthly |
| Disk full simulation | `fallocate -l 90% /tmp` | Monthly |

---

## 3. Monitoring & Alerting

### P10-06: Key Metrics & Alerts

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| `personaplex_sessions_active` | > 80% max | > 95% max | Scale up / reject new |
| `personaplex_vram_used_gb` | > 80% total | > 95% total | Reject new sessions |
| `personaplex_inference_latency_p99` | > 1.5s | > 3s | Investigate GPU load |
| `personaplex_error_rate` | > 0.1% | > 1% | Page on-call |
| `personaplex_gpu_temp_c` | > 80°C | > 90°C | Throttle / alert |
| `personaplex_session_duration_avg` | > 20 min | > 25 min | Check for stuck sessions |

### Dashboards Required
- **Service Overview:** Sessions, latency, errors, throughput
- **GPU Utilization:** VRAM, compute, temperature, power
- **Audio Quality:** Latency, interruption rate, backchannel rate
- **Business:** Sessions/day, unique users, fallback rate

---

## 3. Acceptance Criteria

- [ ] All latency benchmarks meet targets on target hardware
- [ ] Concurrency limits enforced without OOM
- [ ] All failure mode tests pass with expected behavior
- [ ] 24-hour stability test passes (error rate < 0.1%)
- [ ] Metrics exported and dashboards operational
- [ ] Alert rules configured and tested
- [ ] Runbooks exist for top 5 failure scenarios
- [ ] Capacity planning document with scaling triggers

---

## 4. Status Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| Latency benchmarks | NOT STARTED | ❌ | Requires P2 hardware |
| Concurrency tests | NOT STARTED | ❌ | |
| Failure injection | NOT STARTED | ❌ | |
| Stability test | NOT STARTED | ❌ | 24-hour run |
| Chaos experiments | NOT STARTED | ❌ | |
| Metrics/alerts | NOT STARTED | ❌ | Prometheus/Grafana |
| Runbooks | NOT STARTED | ❌ | Top 5 failures |

---

## 4. Dependencies

- **Requires:** P4 (service), P8 (ag behavior), P9 (security)
- **Blocks:** P11 (production readiness)