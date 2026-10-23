# Phase P1 — Shared Model Storage & Lifecycle

**Status:** ⏳ READY (awaits P0 completion)  
**Prerequisite:** P0 complete (HF approval, checksums, license decision, hardware decision)  
**Blocks:** P2–P11

---

## 1. Objective

Establish a reusable, versioned, and verifiable model storage convention at `/data/AI-Models/` that supports:
- Multiple projects (MyFarmAI, ATHENA, future) sharing one model copy
- Integrity verification, versioning, and provenance tracking
- Safe cleanup, recovery from interrupted downloads, and cache management
- No model weights in Git; large artifacts on `/data` HDD

---

## 2. Scope

| In Scope | Out of Scope |
|----------|--------------|
| Directory layout convention for `/data/AI-Models/` | Modifying system package managers |
| Checksum manifest (`MODEL_CHECKSUMS.md`) | Model quantization or conversion |
| Download, verify, and resume procedures | Training or fine-tuning pipelines |
| Version tagging and provenance metadata | Model serving runtime (P2) |
| Cache management for Hugging Face / PyTorch | Other projects' internal configs |
| Cleanup and recovery procedures | |

---

## 3. Directory Layout Convention

```
/data/AI-Models/
├── personaplex-7b-v1/                    # Model directory (versioned)
│   ├── model.safetensors                 # Primary weights (16.7 GB)
│   ├── tokenizer_spm_32k_3.model
│   ├── tokenizer-e351c8d8-checkpoint125.safetensors
│   ├── voices.tgz
│   ├── dist.tgz
│   ├── config.json
│   ├── README.md                         # Original model card
│   ├── MODEL_CHECKSUMS.md                # SHA-256 manifest (this phase)
│   ├── MODEL_PROVENANCE.md               # Source, date, version, license
│   └── .cache/                           # HF/PyTorch cache (excluded from backup)
│
├── .shared-cache/                        # Optional: shared HF/PyTorch cache
│   └── huggingface/
│
├── MODEL_REGISTRY.md                     # Index of all models + versions
└── STORAGE_POLICY.md                     # Retention, cleanup, backup rules
```

---

## 4. Required Artifacts

### P1-01: MODEL_CHECKSUMS.md
**Content:** SHA-256 for every file in model directory
```markdown
# Model Checksums — personaplex-7b-v1
# Generated: <date>
# Source: huggingface.co/nvidia/personaplex-7b-v1

model.safetensors                    <sha256>
tokenizer_spm_32k_3.model            <sha256>
tokenizer-e351c8d8-checkpoint125.safetensors  <sha256>
voices.tgz                           <sha256>
dist.tgz                             <sha256>
config.json                          <sha256>
```

### P1-02: MODEL_PROVENANCE.md
```markdown
# Model Provenance — personaplex-7b-v1
model_id: nvidia/personaplex-7b-v1
version: v1.0
huggingface_url: https://huggingface.co/nvidia/personaplex-7b-v1
github_url: https://github.com/NVIDIA/personaplex
download_date: <date>
downloaded_by: <user>
huggingface_revision: <git commit hash if available>
license: NVIDIA Open Model License Agreement
base_model_license: CC-BY-4.0 (kyutai/moshiko-pytorch-bf16)
commercial_use: Per NVIDIA Open Model License — verify for MyFarmAI
checksums_file: MODEL_CHECKSUMS.md
hardware_requirements: NVIDIA Ampere/Hopper GPU, 24+ GB VRAM
```

### P1-03: MODEL_REGISTRY.md
```markdown
# Model Registry — /data/AI-Models/

| Model | Version | Path | Size | License | Status | Projects |
|-------|---------|------|------|---------|--------|----------|
| personaplex-7b-v1 | v1.0 | personaplex-7b-v1/ | ~20 GB | NVIDIA Open | PENDING | MyFarmAI, ATHENA |
```

### P1-04: STORAGE_POLICY.md
```markdown
# Storage Policy — /data/AI-Models/

## Retention
- Model weights: Permanent until explicit removal decision
- HF/PyTorch caches: Auto-clean after 30 days inactive
- Download artifacts (`.tgz`, partial downloads): Clean after successful extraction

## Backup
- Model weights: Included in `/data` backup (pg_dump equivalent for ML artifacts)
- Checksums/provenance: Included in Git (small text files)
- Caches: NOT backed up (reproducible)

## Cleanup Rules
- Failed/partial downloads: Auto-remove after 24h
- Old cache entries: `find .cache -mtime +30 -delete`
- Duplicate model copies: Prohibited; use symlinks or shared path

## Disk Quotas
- `/data/AI-Models/` soft limit: 100 GB
- Alert at 80% utilization
```

---

## 5. Download & Verification Procedures

### P1-05: Resumable Download Script
```bash
#!/usr/bin/env bash
# download_model.sh — Resumable, verified download
set -euo pipefail

MODEL_ID="nvidia/personaplex-7b-v1"
TARGET_DIR="/data/AI-Models/personaplex-7b-v1"
CHECKSUMS_FILE="$TARGET_DIR/MODEL_CHECKSUMS.md"

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

# Use huggingface-cli with resume support
source /data/AI-Models/hf-download-venv/bin/activate
huggingface-cli download "$MODEL_ID" --local-dir . --resume-download

# Verify checksums
if [[ -f "$CHECKSUMS_FILE" ]]; then
    sha256sum -c "$CHECKSUMS_FILE"
else
    echo "WARNING: No checksums file found; generating..."
    sha256sum $(find . -type f ! -name "MODEL_CHECKSUMS.md" ! -path "./.cache/*") > MODEL_CHECKSUMS.md
fi
```

### P1-06: Verification Script
```bash
#!/usr/bin/env bash
# verify_model.sh — Verify model integrity
set -euo pipefail

TARGET_DIR="/data/AI-Models/personaplex-7b-v1"
cd "$TARGET_DIR"

if [[ ! -f "MODEL_CHECKSUMS.md" ]]; then
    echo "ERROR: No checksums file"
    exit 1
fi

sha256sum -c MODEL_CHECKSUMS.md
```

---

## 6. Cache Management

| Cache | Location | Policy |
|-------|----------|--------|
| Hugging Face Hub cache | `/data/AI-Models/.shared-cache/huggingface/` or `~/.cache/huggingface/` | Symlink to shared; auto-clean 30 days |
| PyTorch Hub cache | `/data/AI-Models/.shared-cache/torch/` or `~/.cache/torch/` | Symlink to shared |
| PersonaPlex runtime cache | `/data/AI-Models/personaplex-7b-v1/.cache/` | Model-local; clean on version change |

---

## 7. Recovery Procedures

| Scenario | Recovery Action |
|--------|-----------------|
| Interrupted download | Re-run `download_model.sh` (resumes via `--resume-download`) |
| Corrupted file (checksum fail) | Delete corrupted file; re-run download |
| Cache corruption | `rm -rf .cache/` or shared cache; re-download on next run |
| Accidental deletion of weights | Re-run download script; verify checksums |
| Disk full during download | Clean caches; resume download |

---

## 8. Acceptance Criteria

- [ ] `MODEL_CHECKSUMS.md` exists with all file SHA-256s
- [ ] `MODEL_PROVENANCE.md` documents source, license, version, hardware reqs
- [ ] `MODEL_REGISTRY.md` indexes PersonaPlex with metadata
- [ ] `STORAGE_POLICY.md` defines retention, backup, cleanup, quotas
- [ ] Download script resumes interrupted downloads
- [ ] Verification script passes on clean model directory
- [ ] Cache directories symlinked to shared location on `/data`
- [ ] No model weights in Git (verified by `git check-ignore`)

---

## 9. Status Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| P1-01: Checksums manifest | NOT STARTED | ❌ | Requires P0 complete |
| P1-02: Provenance metadata | NOT STARTED | ❌ | Requires P0 complete |
| P1-03: Model registry | NOT STARTED | ❌ | |
| P1-04: Storage policy | NOT STARTED | ❌ | |
| P1-05: Download script | NOT STARTED | ❌ | |
| P1-06: Verification script | NOT STARTED | ❌ | |
| Cache symlinks | NOT STARTED | ❌ | |
| Recovery procedures doc | NOT STARTED | ❌ | |

---

## 9. Dependencies

- **Requires:** P0 complete (HF approval, checksums possible, license decision, hardware decision)
- **Blocks:** P2 (runtime prototype needs verified weights)

---

## 10. References

- HF CLI resume download: `huggingface-cli download --resume-download`
- SHA-256 verification: `sha256sum -c CHECKSUMS.md`
- HF cache location: `HF_HOME` env var or `~/.cache/huggingface`