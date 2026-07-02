import json
import asyncio
import httpx
import json_repair
import re
from workers import WORKER_REGISTRY, get_worker_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"

async def query_worker(worker_id: str, decision: str) -> dict:
    prompt = get_worker_prompt(worker_id, decision)
    
    payload = {
        "model": "tinyllama",
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.3,  # Keep it slightly creative but grounded
            "num_predict": 300   # Allow enough tokens to fully output JSON
        }
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(OLLAMA_URL, json=payload)
            result = response.json()
            raw_text = result.get("response", "{}")
            
            # Use json_repair to robustly handle incomplete/malformed outputs
            repaired = json_repair.repair_json(raw_text.strip())
            data = json.loads(repaired)
            
            # Inject provenance tracking
            for node in data.get("nodes", []):
                node["origin_worker"] = worker_id
                node["generation"] = 1
            return data
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error querying worker {worker_id}: {e}")
            return {"worker_id": worker_id, "error": str(e), "nodes": []}

WORKER_KEYWORDS = {
    "financial_analyst": {"cost", "revenue", "finance", "capital", "profit", "investment", "expense", "budget", "salary", "pay", "income", "margin", "asset", "liability", "debt", "cash"},
    "contrarian_optimist": {"opportunity", "upside", "leverage", "advantage", "growth", "efficiency", "expansion", "niche", "contrarian", "hidden", "unobvious", "asymmetric"},
    "worst_case_prepper": {"fail", "danger", "worst-case", "disruption", "downside", "risk", "hazard", "threat", "vulnerability", "collapse", "crisis", "accident", "dependency", "failure"},
    "psychological_human_centric": {"stress", "mental", "burnout", "satisfaction", "motivation", "morale", "fatigue", "identity", "social", "relationships", "family", "personal", "work-life", "strain"}
}

def evaluate_and_prune_nodes(nodes: list, score_threshold: float) -> list:
    """Evaluate generated nodes against origin worker keyword registry and prune below threshold."""
    survived = []
    for node in nodes:
        worker_id = node.get("origin_worker")
        keywords = WORKER_KEYWORDS.get(worker_id, set())
        
        # Safely extract text fields to match keywords against
        text = (node.get("label", "") + " " + node.get("rationale", "") + " " + node.get("description", "") + " " + node.get("headline", "")).lower()
        node_words = set(re.findall(r"\b\w{3,}\b", text))
        
        # Calculate alignment overlap
        overlap = len(node_words.intersection(keywords))
        
        # Alignment score: 0.5 (no matches), 0.75 (1 match), 1.0 (2+ matches)
        alignment_score = 0.5 + 0.25 * min(2, overlap)
        node["alignment_score"] = alignment_score
        node["score"] = alignment_score  # Assume base score is 1.0
        
        if node["score"] >= score_threshold:
            survived.append(node)
        else:
            print(f"Pruned node from {worker_id} due to low alignment score {node['score']:.2f}: '{node.get('label')}'")
            
    return survived

async def query_mutation_worker(mutator_id: str, parent_node: dict) -> dict:
    """Query a worker to mutate a parent node using custom mutator instructions."""
    from workers import get_mutation_prompt
    prompt = get_mutation_prompt(mutator_id, parent_node)
    
    payload = {
        "model": "tinyllama",
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.3,
            "num_predict": 300
        }
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(OLLAMA_URL, json=payload)
            result = response.json()
            raw_text = result.get("response", "{}")
            
            repaired = json_repair.repair_json(raw_text.strip())
            data = json.loads(repaired)
            
            # Inject ancestry/provenance tracking
            for node in data.get("nodes", []):
                node["origin_worker"] = mutator_id
                node["generation"] = 2
                node["parent_id"] = parent_node.get("id") or parent_node.get("label", "unknown")
                
                # Provenance: Parent provenance + mutator
                parent_prov = parent_node.get("provenance", [parent_node.get("origin_worker", "unknown")])
                node["provenance"] = parent_prov + [f"mutator:{mutator_id}"]
                node["consensus_score"] = 1.0  # Baseline consensus for the new hybrid node
                
            return data
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error querying mutation worker {mutator_id}: {e}")
            return {"worker_id": mutator_id, "error": str(e), "nodes": []}

async def run_mutation_phase(surviving_nodes: list) -> list:
    """Execute cross-persona mutation on surviving nodes concurrently."""
    tasks = []
    # Matrix mapping to assign the mutation target
    mutation_map = {
        "financial_analyst": "contrarian_optimist",
        "contrarian_optimist": "worst_case_prepper",
        "worst_case_prepper": "psychological_human_centric",
        "psychological_human_centric": "financial_analyst"
    }
    
    print("\n--- Running Phase 4: Cross-Persona Mutation ---")
    for node in surviving_nodes:
        # Determine who should mutate this node based on its primary origin
        primary_origin = node.get("provenance", [node.get("origin_worker", "worst_case_prepper")])[0]
        mutator_id = mutation_map.get(primary_origin, "worst_case_prepper")
        
        # Build async task
        tasks.append(query_mutation_worker(mutator_id, node))
        
    mutated_results = await asyncio.gather(*tasks)
    
    mutated_nodes = []
    for res in mutated_results:
        mutated_nodes.extend(res.get("nodes", []))
        
    print(f"Mutation complete. Injected {len(mutated_nodes)} mutated variations into G=2.")
    return mutated_nodes

async def run_generation_one(decision: str):
    import os
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    similarity_threshold = config.get("similarity_threshold", 0.75)
    score_threshold = config.get("score_threshold", 0.60)
    
    print(f"Spawning G1 worker colony for decision: '{decision}'")
    tasks = [query_worker(w_id, decision) for w_id in WORKER_REGISTRY.keys()]
    
    results = await asyncio.gather(*tasks)
    
    # Gather raw pool
    g1_raw = []
    for r in results:
        if "nodes" in r:
            g1_raw.extend(r["nodes"])
            
    print(f"Generation G=1 Complete. Harvested {len(g1_raw)} raw hypotheses.")
    
    # Phase 2: Competition (Scoring & Pruning) for G1
    print("\n--- Running Phase 2: G1 Competition & Alignment Scoring ---")
    g1_survived = evaluate_and_prune_nodes(g1_raw, score_threshold)
    print(f"G1 Competition complete. {len(g1_survived)} of {len(g1_raw)} nodes survived global thresholding.")
    
    # Phase 3: Consolidation (Jaccard Merging) for G1
    print("\n--- Running Phase 3: G1 Consolidation & Clustering ---")
    from consolidation import consolidate_nodes
    g1_consolidated = consolidate_nodes(g1_survived, similarity_threshold)
    print(f"G1 Consolidation complete. Merged into {len(g1_consolidated)} unique nodes.")
    
    # Phase 4: Mutation
    g2_raw = await run_mutation_phase(g1_consolidated)
    
    # Phase 5: G2 Expansion & Competition
    print("\n--- Running Phase 5: G2 Competition & Alignment Scoring ---")
    g2_survived = evaluate_and_prune_nodes(g2_raw, score_threshold)
    print(f"G2 Competition complete. {len(g2_survived)} of {len(g2_raw)} mutated nodes survived.")
    
    # Final Consolidation: Merge G1 survivors + G2 mutated survivors
    print("\n--- Running Final Graph Consolidation & Lineage Merging ---")
    combined_pool = g1_consolidated + g2_survived
    final_consolidated = consolidate_nodes(combined_pool, similarity_threshold)
    print(f"Final Graph compiled. Unified into {len(final_consolidated)} non-redundant causal nodes.")
    
    return final_consolidated

if __name__ == "__main__":
    test_decision = "I am thinking about quitting my corporate job to build a niche SaaS product."
    nodes = asyncio.run(run_generation_one(test_decision))
    print("\nFinal Evolutionary Causal Cosequence Pool:")
    print(json.dumps(nodes, indent=2))
