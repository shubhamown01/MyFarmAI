# Phase P0 — Feasibility & Access Verification

**Status:** ❌ BLOCKED — Hugging Face model approval required  
**Prerequisite:** None (this is the entry gate)  
**Blocks:** All downstream phases (P1–P11)

---

## 1. Objective

Establish whether NVIDIA PersonaPlex 7B v1 can be legally downloaded, stored, and used in MyFarmAI, and whether the current or planned hardware can run it for real-time full-duplex inference.

---

## 2. Current Verified State

| Check | Status | Evidence |
|-------|--------|----------|
| Model weights present on disk | ✅ | `/data/AI-Models/personaplex-7b-v1/model.safetensors` (16.7 GB) |
| Hugging Face model access | ❌ BLOCKED | `huggingface-cli download` returns access-denied; gated repo |
| HF token configured | ✅ | `/data/AI-Models/hf-download-venv` authenticated |
| Model checksum verified | ❌ NO | No SHA-256 recorded for `model.safetensors` |
| License compatibility | ⚠️ PARTIAL | NVIDIA Open Model License + CC-BY-4.0 base; commercial use claimed |
| Local inference tested | ❌ NO | No runtime installed; no benchmark executed |
| Hardware suitability | ❌ FAIL | MX250 2 GB VRAM vs 16.7 GB model; 7 GiB RAM vs 32+ GiB needed |

---

## 3. Required Actions (Gate Criteria)

### P0-01: Request Hugging Face Model Approval
- **Action:** Submit access request on https://huggingface.co/nvidia/personaplex-7b-v1
- **Owner:** Project lead
- **Acceptance:** Approval email received; `huggingface-cli download nvidia/personaplex-7b-v1` succeeds
- **Blocker:** Cannot proceed without explicit approval

### P0-02: Record Model Checksums
- **Action:** Compute and record SHA-256 for all model artifacts
- **Artifacts:** `model.safetensors`, `tokenizer_spm_32k_3.model`, `tokenizer-e351c8d8-checkpoint125.safetensors`, `voices.tgz`, `dist.tgz`, `config.json`
- **Acceptance:** SHA-256 values recorded in `MODEL_CHECKSUMS.md`; match Hugging Face references when available

### P0-03: License Compatibility Review
- **Action:** Legal review of NVIDIA Open Model License + CC-BY-4.0 (base model: `kyutai/moshiko-pytorch-bf16`)
- **Questions:**
  - Does NVIDIA Open Model License permit redistribution as part of MyFarmAI?
  - Does CC-BY-4.0 base model impose attribution requirements on MyFarmAI outputs?
  - Are there commercial use restrictions for MyFarmAI's intended distribution?
- **Acceptance:** Written legal memo or explicit project decision recorded

### P0-04: Hardware Feasibility Gate
- **Action:** Document minimum hardware requirements from NVIDIA docs
- **Requirements (per model card):**
  - NVIDIA Ampere (A100) or Hopper (H100) GPU
  - PyTorch + CUDA compatible with tested versions
  - Linux OS
- **Current hardware verdict:** MX250 (Pascal) **does not meet** Ampere/Hopper requirement
- **Acceptance:** Explicit decision: (a) acquire suitable hardware, (b) approve remote GPU, or (c) defer PersonaPlex

### P0-05: Model Weight Verification
- **Action:** Verify downloaded weights match Hugging Face references
- **Method:** Compare SHA-256 against Hugging Face `git lfs` pointers or published checksums
- **Acceptance:** All weights verified; any mismatch documented

---

## 4. Exit Gate

**Phase P0 is complete only when:**

- [ ] Hugging Face approval granted and download succeeds
- [ ] All model artifact SHA-256 checksums recorded and verified
- [ ] License compatibility review completed and decision recorded
- [ ] Hardware feasibility decision made (acquire/approve remote/defer)
- [ ] Model weights verified against Hugging Face references

**No downstream phase may begin until all P0 criteria are VERIFIED.**

---

## 5. Status Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| P0-01: HF approval request | NOT STARTED | ❌ | Requires NVIDIA approval |
| P0-02: Checksums recorded | NOT STARTED | ❌ | Pending download |
| P0-03: License review | NOT STARTED | ❌ | Legal review needed |
| P0-04: Hardware gate | BLOCKED | ❌ | Current hardware fails |
| P0-05: Weight verification | NOT STARTED | ❌ | Pending download |

---

## 6. References

- NVIDIA PersonaPlex Repository: https://github.com/NVIDIA/personaplex
- Hugging Face Model Card: https://huggingface.co/nvidia/personaplex-7b-v1
- NVIDIA Open Model License: https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/
- Base Model (Moshiko): https://huggingface.co/kyutai/moshiko-pytorch-bf16 (CC-BY-4.0)
- PersonaPlex Paper: https://arxiv.org/abs/2602.06053
- FullDuplexBench: https://arxiv.org/abs/2503.04721