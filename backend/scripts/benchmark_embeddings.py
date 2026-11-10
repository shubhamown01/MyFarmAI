"""P4-08/Model 4: Embedding candidate benchmark — dimensions + latency.

Runs representative agricultural texts (EN + HI + short/long) against the
installed embedding candidates via Ollama /api/embed, records vector
dimensions and latency. No retrieval-quality claim is made here — retrieval
validation requires a vector-store decision (owner approval per master
prompt Model 4 constraints).

Usage (from backend/): uv run python scripts/benchmark_embeddings.py [tags...]
Ollama serial inference: run alone.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

CANDIDATES = [
    "qwen3-embedding:0.6b",
    "nomic-embed-text:latest",
]

TEXTS = [
    ("en-short", "Tomato leaves are turning yellow. What should I do?"),
    (
        "en-long",
        "Crop rotation is the practice of planting different crops in sequence on the same field to break pest and disease cycles, improve soil structure and fertility, and manage nutrients across seasons.",
    ),
    ("hi-short", "टमाटर की फसल में पत्तियां पीली हो रही हैं। क्या करें?"),
    (
        "en-technical",
        "Apply neem oil spray in the evening to avoid leaf burn; repeat after seven days if whitefly pressure persists.",
    ),
]


async def bench(client: httpx.AsyncClient, model: str) -> dict:
    rows = []
    for text_id, text in TEXTS:
        t0 = time.monotonic()
        try:
            resp = await client.post(
                "/api/embed",
                json={"model": model, "input": text},
                timeout=httpx.Timeout(120),
            )
            resp.raise_for_status()
            vectors = resp.json().get("embeddings", [])
            dim = len(vectors[0]) if vectors else 0
            status = "ok" if dim else "empty"
        except Exception as e:
            dim, status = 0, f"error: {type(e).__name__}"
        rows.append(
            {
                "id": text_id,
                "seconds": round(time.monotonic() - t0, 2),
                "dim": dim,
                "status": status,
            }
        )
        print(f"  {text_id}: {rows[-1]['seconds']}s dim={dim} {status}", flush=True)
    ok = [r for r in rows if r["status"] == "ok"]
    return {
        "model": model,
        "dim": ok[0]["dim"] if ok else None,
        "consistent_dim": len({r["dim"] for r in ok}) == 1,
        "ok": len(ok),
        "total": len(rows),
        "avg_s": round(sum(r["seconds"] for r in ok) / len(ok), 2) if ok else None,
        "rows": rows,
    }


if __name__ == "__main__":
    tags = sys.argv[1:] or CANDIDATES

    async def run():
        out = []
        async with httpx.AsyncClient(base_url="http://localhost:11434") as client:
            for tag in tags:
                print(f"{tag}:", flush=True)
                out.append(await bench(client, tag))
        path = Path(__file__).resolve().parent.parent / "embedding_benchmark_results.json"
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
        print(f"Wrote {path}")

    asyncio.run(run())
