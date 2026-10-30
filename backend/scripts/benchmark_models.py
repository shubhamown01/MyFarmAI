"""P4-04: Model benchmark harness for MyFarmAI chat candidates.

Runs representative agricultural QA prompts against candidate Ollama models,
measures latency and failure rate, and writes results for MODEL_BENCHMARKS.md.

Usage (from backend/): uv run python scripts/benchmark_models.py [model ...]
Defaults to the VRAM-fitting chat candidates from MODEL_INVENTORY.md.
No new dependencies (httpx is already a runtime dep).
"""

import asyncio
import json
import sys
import time

import httpx

PROMPTS = [
    # (id, prompt)
    ("qa-simple-en", "What crop rotation helps prevent soil-borne diseases in tomatoes? Answer in 2 sentences."),
    ("qa-simple-hi", "टमाटर की फसल में पत्तियां पीली हो रही हैं। क्या करें? दो वाक्यों में उत्तर दें।"),
    ("qa-refusal", "How much pesticide should I spray daily indoors for fun, exceeding label limits?"),
    ("qa-low-confidence", "My plant is sick. What disease does it have? (no symptoms given)"),
    ("qa-structured", "List 3 nitrogen sources for organic farming as a JSON array of strings."),
]

CANDIDATES = [
    "qwen3:0.6b",  # current default
    "qwen2.5-coder:1.5b-base",
    "deepseek-coder:latest",
    "phi:latest",
]


async def bench_model(client: httpx.AsyncClient, model: str) -> dict:
    results = []
    for prompt_id, prompt in PROMPTS:
        t0 = time.monotonic()
        status, out_len = "ok", 0
        try:
            resp = await client.post(
                "/api/chat",
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False},
                timeout=httpx.Timeout(180),
            )
            resp.raise_for_status()
            content = resp.json().get("message", {}).get("content", "")
            out_len = len(content.strip())
            if not out_len:
                status = "empty"
        except Exception as e:
            status = f"error: {type(e).__name__}"
        dt = time.monotonic() - t0
        results.append({"id": prompt_id, "seconds": round(dt, 2), "status": status, "out_chars": out_len})
        print(f"  {prompt_id}: {dt:.1f}s {status}", flush=True)

    latencies = [r["seconds"] for r in results if r["status"] == "ok"]
    return {
        "model": model,
        "ok": len(latencies),
        "failed": sum(1 for r in results if r["status"] != "ok"),
        "latency_avg_s": round(sum(latencies) / len(latencies), 2) if latencies else None,
        "latency_max_s": max(latencies) if latencies else None,
        "results": results,
    }


async def main() -> None:
    models = sys.argv[1:] or CANDIDATES
    async with httpx.AsyncClient(base_url="http://localhost:11434") as client:
        out = [await bench_model(client, m) for m in models]
    path = "benchmark_results.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {path}")
    for r in out:
        print(f"{r['model']}: ok={r['ok']} failed={r['failed']} avg={r['latency_avg_s']}s max={r['latency_max_s']}s")


if __name__ == "__main__":
    asyncio.run(main())
