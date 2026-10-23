# Phase P3 — Hardware Deployment Strategy

**Status:** ⏳ READY (awaits P2 benchmark results)  
**Prerequisite:** P2 complete (benchmark results, hardware verdict)  
**Blocks:** P4–P11

---

## 1. Objective

Define three deployment targets with explicit hardware requirements, performance thresholds, and cost/privacy trade-offs. The strategy must be executable without mandatory paid cloud services.

---

## 2. Deployment Targets

### Target 1: Development Feasibility (Current Machine)
**Purpose:** Feasibility experiments only; NOT for production or real-time use

| Resource | Spec | Suitability |
|----------|------|-------------|
| GPU | NVIDIA MX250 (2 GB VRAM) | ❌ Cannot run PersonaPlex |
| RAM | 7 GiB total, ~2 GiB free | ❌ Insufficient |
| Use Case | Documentation, planning, CPU-only mock tests | Only |

**Verdict:** Current machine **cannot run PersonaPlex**. Use only for documentation, planning, and CPU-only development.

---

### Target 2: Local GPU Workstation (Primary Production Target)
**Purpose:** Self-hosted, zero recurring cost, full privacy control

#### Minimum Hardware Spec
| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| GPU | NVIDIA A100 40 GB or H100 | A100 80 GB / H100 80 GB | Ampere/Hopper required |
| VRAM | 24 GB | 40–80 GB | Model + KV cache + overhead |
| System RAM | 32 GiB | 64+ GiB | OS + PyTorch + model + overhead |
| CPU | 8+ cores, AVX2 | 16+ cores, AVX-512 | PyTorch + audio processing |
| Disk (OS) | 100 GB NVMe | 500 GB NVMe | OS, containers, runtime |
| Disk (Models) | 100 GB | 500 GB | `/data/AI-Models/` on separate drive |
| Network | 1 Gbps LAN | 10 Gbps LAN | Low-latency local access |
| Power | 800 W PSU | 1200 W PSU | GPU + CPU + overhead |

#### Deployment Options
| Option | Cost | Privacy | Latency | Maintenance |
|--------|------|---------|---------|-------------|
| On-prem workstation | $15k–$30k (A100) | ✅ Full control | ✅ < 10 ms LAN | Self-managed |
| Rack server (colocated) | $20k–$40k + hosting | ✅ Full control | ✅ < 5 ms LAN | Shared/managed |
| GPU cloud (reserved) | $2–$5/hr | ⚠️ Provider access | ✅ Low | Provider-managed |

#### Local Network Topology
```
┌─────────────────────────────────────────────────────────────┐
│                     Local LAN (1–10 Gbps)                    │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  GPU Server  │  MyFarmAI    │  Web Clients │  Android Dev   │
│  (PersonaPlex)│  Backend    │  (Web/Phone) │  (Physical)    │
│  Port 8002   │  Port 8000   │  Port 3000   │  USB/ADB       │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

---

### Target 3: Remote GPU Infrastructure (Conditional)
**Purpose:** Only if explicitly approved; costs and privacy implications accepted

| Option | Provider | Cost Est. | Privacy Risk | Approval Required |
|--------|----------|-----------|--------------|-------------------|
| RunPod | runpod.io | $1.50–$3/hr (A100) | ⚠️ Shared infra | Explicit |
| Lambda Labs | lambdalabs.com | $1.50–$2.50/hr | ⚠️ Shared infra | Explicit |
| Vast.ai | vast.ai | $0.80–$2/hr | ⚠️ Shared infra | Explicit |
| AWS/GCP/Azure | Major cloud | $3–$6/hr (A100) | ⚠️ Full provider access | Explicit + contract |
| NVIDIA DGX Cloud | NVIDIA | $37k/mo (A100) | ⚠️ NVIDIA access | Explicit + contract |

**Gate:** No remote GPU provisioned without:
- [ ] Explicit written approval from project owner
- [ ] Cost ceiling documented and approved
- [ ] Privacy impact assessment signed
- [ ] Data processing agreement (DPA) reviewed
- [ ] Exit strategy documented (model weights return to local)

---

## 3. Network & Security by Target

| Aspect | Target 1 (Dev) | Target 2 (Local) | Target 3 (Remote) |
|--------|----------------|------------------|-------------------|
| Network | Loopback only | Private LAN (10 Gbps) | VPN/WireGuard + TLS |
| Auth | Dev tokens | mTLS + OAuth | mTLS + OAuth + VPN |
| Model Access | Local filesystem | NFS/bind mount | Encrypted EFS/S3 |
| Audio Transport | WebSocket (loopback) | WebSocket (LAN) | WebSocket (WSS) + VPN |
| Monitoring | Local logs | Prometheus/Grafana | CloudWatch + local |

---

## 4. Migration Path

| From | To | Trigger | Steps |
|------|-----|---------|-------|
| Dev (Target 1) | Local (Target 2) | P2 benchmark confirms need | 1. Procure GPU server<br>2. Deploy PersonaPlex service<br>3. Update AI gateway config<br>4. Run integration tests |
| Local (Target 2) | Remote (Target 3) | Scale beyond local capacity | 1. Approve remote budget<br>2. Sign DPA<br>3. Deploy to approved provider<br>4. Update DNS/gateway config |

---

## 4. Resource Budget

| Category | Target 2 (Local) | Target 3 (Remote, monthly) |
|----------|------------------|----------------------------|
| Hardware (CAPEX) | $20k–$40k (one-time) | $0 |
| Electricity | ~$150–$300/mo | Included |
| Network | Existing LAN | VPN ($50–$200/mo) |
| Cloud GPU (hrs) | $0 | $2k–$5k/mo @ 70% util |
| Maintenance | Self-managed | Provider SLA |
| **Total Year 1** | **$22k–$44k** | **$26k–$62k** |

---

## 5. Acceptance Criteria

- [ ] Three deployment targets documented with hardware specs
- [ ] Network topology diagrams for each target
- [ ] Cost models with Year 1 and Year 3 projections
- [ ] Privacy impact assessment for each target
- [ ] Explicit approval gate for Target 3 (no auto-provision)
- [ ] Migration runbooks between targets documented
- [ ] Hardware verdict from P2 referenced and consistent

---

## 5. Status Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| Target 1 documented | VERIFIED | ✅ | Current machine documented |
| Target 2 spec | NOT STARTED | ❌ | Requires P2 hardware verdict |
| Target 3 conditional | NOT STARTED | ❌ | Requires explicit approval |
| Network diagrams | NOT STARTED | ❌ | |
| Cost models | NOT STARTED | ❌ | |
| Migration runbooks | NOT STARTED | ❌ | |

---

## 5. Dependencies

- **Requires:** P2 benchmark complete (hardware verdict)
- **Blocks:** P4 (service deployment depends on target selection)