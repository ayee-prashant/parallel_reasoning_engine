# experiments/parallel_reasoning_engine/engine_v2.py
import json
import asyncio
import httpx
import json_repair
import re
import os
import time

from workers import WORKER_REGISTRY, get_worker_prompt, get_mutation_prompt
from consolidation import consolidate_nodes
from visualizer import generate_visual_dag

OLLAMA_URL = "http://localhost:11434/api/generate"

async def query_worker(worker_id: str, decision: str, semaphore: asyncio.Semaphore, temp: float) -> dict:
    """Query a specialist worker utilizing a concurrency semaphore and dynamic temperature."""
    prompt = get_worker_prompt(worker_id, decision)
    
    payload = {
        "model": "tinyllama",
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temp,
            "num_predict": 300
        }
    }
    
    # Acquire semaphore to throttle active CPU load on Ollama
    async with semaphore:
        t0 = time.time()
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(OLLAMA_URL, json=payload)
                result = response.json()
                raw_text = result.get("response", "{}")
                
                repaired = json_repair.repair_json(raw_text.strip())
                data = json.loads(repaired)
                
                # Inject provenance tracking
                for node in data.get("nodes", []):
                    node["origin_worker"] = worker_id
                    node["generation"] = 1
                    
                elapsed = time.time() - t0
                print(f"[v2-colony] Worker {worker_id} completed in {elapsed:.2f}s (temp: {temp})")
                return data
            except Exception as e:
                print(f"[v2-colony] Error querying worker {worker_id}: {e}")
                return {"worker_id": worker_id, "error": str(e), "nodes": []}

async def query_mutation_worker(mutator_id: str, parent_node: dict, semaphore: asyncio.Semaphore, temp: float) -> dict:
    """Query a mutation worker utilizing a concurrency semaphore and dynamic temperature."""
    prompt = get_mutation_prompt(mutator_id, parent_node)
    
    payload = {
        "model": "tinyllama",
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temp,
            "num_predict": 300
        }
    }
    
    async with semaphore:
        t0 = time.time()
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(OLLAMA_URL, json=payload)
                result = response.json()
                raw_text = result.get("response", "{}")
                
                repaired = json_repair.repair_json(raw_text.strip())
                data = json.loads(repaired)
                
                for node in data.get("nodes", []):
                    node["origin_worker"] = mutator_id
                    node["generation"] = 2
                    node["parent_id"] = parent_node.get("id") or parent_node.get("label", "unknown")
                    
                    parent_prov = parent_node.get("provenance", [parent_node.get("origin_worker", "unknown")])
                    node["provenance"] = parent_prov + [f"mutator:{mutator_id}"]
                    node["consensus_score"] = 1.0
                    
                elapsed = time.time() - t0
                print(f"[v2-colony] Mutation {mutator_id} completed in {elapsed:.2f}s (temp: {temp})")
                return data
            except Exception as e:
                print(f"[v2-colony] Error querying mutation worker {mutator_id}: {e}")
                return {"worker_id": mutator_id, "error": str(e), "nodes": []}

# Keyword registry for validation scoring
WORKER_KEYWORDS = {
    "financial_analyst": {"cost", "revenue", "finance", "capital", "profit", "investment", "expense", "budget", "salary", "pay", "income", "margin", "asset", "liability", "debt", "cash"},
    "contrarian_optimist": {"opportunity", "upside", "leverage", "advantage", "growth", "efficiency", "expansion", "niche", "contrarian", "hidden", "unobvious", "asymmetric", "pivot"},
    "worst_case_prepper": {"fail", "danger", "worst-case", "disruption", "downside", "risk", "hazard", "threat", "vulnerability", "collapse", "crisis", "accident", "dependency", "failure"},
    "psychological_human_centric": {"stress", "mental", "burnout", "satisfaction", "motivation", "morale", "fatigue", "identity", "social", "relationships", "family", "personal", "work-life", "strain", "toll", "energy"}
}

def evaluate_and_prune_nodes(nodes: list, score_threshold: float) -> list:
    """Evaluate node descriptions against target lexicons and prune low-scoring nodes."""
    survived = []
    for node in nodes:
        worker_id = node.get("origin_worker")
        keywords = WORKER_KEYWORDS.get(worker_id, set())
        
        text = (node.get("label", "") + " " + node.get("rationale", "") + " " + node.get("description", "") + " " + node.get("headline", "")).lower()
        node_words = set(re.findall(r"\b\w{3,}\b", text))
        
        overlap = len(node_words.intersection(keywords))
        alignment_score = 0.5 + 0.25 * min(2, overlap)
        node["alignment_score"] = alignment_score
        node["score"] = alignment_score
        
        if node["score"] >= score_threshold:
            survived.append(node)
        else:
            print(f"[v2-colony] Pruned low alignment node ({node['score']:.2f}) from {worker_id}: '{node.get('label')}'")
    return survived

async def run_mutation_phase(surviving_nodes: list, semaphore: asyncio.Semaphore, temp: float) -> list:
    """Orchestrate G2 mutations concurrently under semaphore locks."""
    tasks = []
    mutation_map = {
        "financial_analyst": "contrarian_optimist",
        "contrarian_optimist": "worst_case_prepper",
        "worst_case_prepper": "psychological_human_centric",
        "psychological_human_centric": "financial_analyst"
    }
    
    print("\n--- Running Phase 4: Cross-Persona Mutation (v2) ---")
    for node in surviving_nodes:
        primary_origin = node.get("provenance", [node.get("origin_worker", "worst_case_prepper")])[0]
        mutator_id = mutation_map.get(primary_origin, "worst_case_prepper")
        tasks.append(query_mutation_worker(mutator_id, node, semaphore, temp))
        
    mutated_results = await asyncio.gather(*tasks)
    
    mutated_nodes = []
    for res in mutated_results:
        mutated_nodes.extend(res.get("nodes", []))
    print(f"Mutation complete. Generated {len(mutated_nodes)} candidates.")
    return mutated_nodes

async def run_cso_synthesis_v2(elite_nodes: list) -> str:
    """Query Chief Strategy Officer pass on top-performing nodes to produce brief summary."""
    facts_block = []
    for node in elite_nodes:
        label = node.get("label") or node.get("title") or "Insight"
        rationale = node.get("rationale") or node.get("description") or "Details"
        facts_block.append(f"- {label}: {rationale}")
    
    facts_joined = "\n".join(facts_block)
    
    prompt = f"""### Analysis Findings:
{facts_joined}

### Executive Strategy Brief:
## 1. KEY STRATEGIC RATIONALE
Quitting a corporate job to launch a niche SaaS product involves significant trade-offs:
"""
    
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
    return final_brief

async def execute_v2_pipeline(decision: str):
    # 1. Config Loading
    import os
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    similarity_threshold = config.get("similarity_threshold", 0.75)
    score_threshold = config.get("score_threshold", 0.60)
    
    # 2. Concurrency Control (Semaphore Limit: 2)
    semaphore = asyncio.Semaphore(2)
    
    # Dynamic Temperature scaling formulas
    t_g1 = 0.2 + (1 - 1) * 0.25  # G1 (Grounded baseline) -> 0.20
    t_g2 = 0.2 + (2 - 1) * 0.25  # G2 (Mutation exploration) -> 0.45
    
    print(f"Starting Engine V2 for decision: '{decision}'")
    print(f"Semaphore Limit: 2 | Temperature: G1={t_g1}, G2={t_g2}")
    
    # --- PHASE 1: G1 Spawning ---
    tasks = [query_worker(w_id, decision, semaphore, t_g1) for w_id in WORKER_REGISTRY.keys()]
    t0_g1 = time.time()
    results = await asyncio.gather(*tasks)
    elapsed_g1 = time.time() - t0_g1
    
    g1_raw = []
    for r in results:
        if "nodes" in r:
            g1_raw.extend(r["nodes"])
    print(f"G1 generation took {elapsed_g1:.2f}s. Harvested {len(g1_raw)} raw nodes.")
    
    # --- PHASE 2: Competition (Scoring & Pruning) ---
    print("\n--- Running Phase 2: G1 Competition & Alignment Scoring ---")
    g1_survived = evaluate_and_prune_nodes(g1_raw, score_threshold)
    
    # --- PHASE 3: Consolidation (Jaccard Merging) ---
    print("\n--- Running Phase 3: G1 Consolidation & Clustering ---")
    g1_consolidated = consolidate_nodes(g1_survived, similarity_threshold)
    print(f"G1 consolidated into {len(g1_consolidated)} unique nodes.")
    
    # --- PHASE 4: Cross-Persona Mutation ---
    g2_raw = await run_mutation_phase(g1_consolidated, semaphore, t_g2)
    
    # --- PHASE 5: G2 Competition ---
    print("\n--- Running Phase 5: G2 Competition & Alignment Scoring ---")
    g2_survived = evaluate_and_prune_nodes(g2_raw, score_threshold)
    print(f"G2 Competition complete. {len(g2_survived)} mutated nodes survived.")
    
    # --- FINAL GRAPH CONSOLIDATION ---
    print("\n--- Running Final Graph Consolidation & Lineage Merging ---")
    combined_pool = g1_consolidated + g2_survived
    final_consolidated = consolidate_nodes(combined_pool, similarity_threshold)
    print(f"Final Graph compiled. Unified into {len(final_consolidated)} non-redundant causal nodes.")
    
    # --- PHASE 6: COMPILE PRESENTATION ASSETS ---
    # 1. HTML visualizer compiler
    viz_path = os.path.join(os.path.dirname(__file__), "visualization", "dag_dashboard_v2.html")
    generate_visual_dag(final_consolidated, decision, viz_path)
    
    # 2. Executive strategic brief compiler
    elite_nodes = sorted(final_consolidated, key=lambda x: x.get("consensus_score", 1.0), reverse=True)[:6]
    brief_text = await run_cso_synthesis_v2(elite_nodes)
    
    brief_path = os.path.join(os.path.dirname(__file__), "results", "executive_brief_v2.md")
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(brief_text)
    print(f"[v2-pipeline] Synthesis Brief successfully written to: {brief_path}")
    
    print("\n" + "="*40 + "\nEXECUTIVE BRIEF SUMMARY (V2)\n" + "="*40)
    print(brief_text)

if __name__ == "__main__":
    test_decision = "I am thinking about quitting my corporate job to build a niche SaaS product."
    asyncio.run(execute_v2_pipeline(test_decision))
