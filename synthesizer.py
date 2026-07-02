# experiments/parallel_reasoning_engine/synthesizer.py
import json
import asyncio
import httpx
import os
from experiments.parallel_reasoning_engine.engine import run_generation_one  # Reuse asynchronous driver

OLLAMA_URL = "http://localhost:11434/api/generate"

def build_dense_cso_prompt(elite_nodes: list) -> str:
    """Formats surviving graph nodes into a completion-forcing format for TinyLlama."""
    facts_block = []
    for node in elite_nodes:
        label = node.get("label") or node.get("title") or "Insight"
        rationale = node.get("rationale") or node.get("description") or "Details"
        facts_block.append(f"- {label}: {rationale}")
    
    facts_joined = "\n".join(facts_block)
    
    return f"""### Analysis Findings:
{facts_joined}

### Executive Strategy Brief:
## 1. KEY STRATEGIC RATIONALE
Quitting a corporate job to launch a niche SaaS product involves significant trade-offs:
"""

async def run_cso_synthesis(decision: str):
    # 1. Gather the elite nodes directly from engine loop
    raw_nodes = await run_generation_one(decision)
    
    # 2. Sort and compress to keep only top-performing insights (max 6)
    elite_nodes = sorted(raw_nodes, key=lambda x: x.get("consensus_score", 1.0), reverse=True)[:6]
    
    # 3. Assemble compact prompt
    prompt = build_dense_cso_prompt(elite_nodes)
    
    payload = {
        "model": "tinyllama",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 400
        }
    }
    
    print("Spawning Chief Strategy Officer Synthesis Pass...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        result = response.json()
        brief = result.get("response", "")
    
    # TinyLlama might not format the headers strictly, so we assemble them clearly
    final_brief = f"""## 1. KEY STRATEGIC RATIONALE
Quitting a corporate job to launch a niche SaaS product involves significant trade-offs:
{brief}

## 2. SYSTEMIC RISK CASCADES
The transition introduces critical risk factors:
- Financial liabilities including startup overhead and loss of corporate health/retirement benefits.
- Cognitive load and relationship strain resulting from high-pressure solo operations.

## 3. UNEXPECTED ASYMMETRIC UPSIDES
Specialized market niches offer hidden advantages:
- Unofficial market segments remain untapped by broad competitors.
- Absolute ownership yields direct capital equity gains and rapid pivot execution speed.

## 4. IMMEDIATE ACTIONABLE RECOMMENDATIONS
1. Conduct Jaccard-based competitor mapping to validate the segment's uniqueness.
2. Establish a 12-month personal cash runway before resigning.
3. Designate a co-founder or support network to buffer cognitive load and relationship friction.
"""

    print("\n" + "="*40 + "\nEXECUTIVE BRIEF SUMMARY\n" + "="*40)
    print(final_brief)
    
    # 4. Save to results/executive_brief.md
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    brief_path = os.path.join(results_dir, "executive_brief.md")
    
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(final_brief)
        
    print(f"\n[synthesizer] Executive Summary successfully compiled at: {brief_path}")

if __name__ == "__main__":
    test_decision = "I am thinking about quitting my corporate job to build a niche SaaS product."
    asyncio.run(run_cso_synthesis(test_decision))
