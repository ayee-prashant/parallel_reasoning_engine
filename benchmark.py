import asyncio
import time
import os
import json
from experiments.parallel_reasoning_engine.config import ExperimentConfig
from experiments.parallel_reasoning_engine.engine import ParallelEngine
from experiments.parallel_reasoning_engine.sequential_engine import SequentialEngine

BENCHMARK_SCENARIOS = [
    {
        "id": "career",
        "category": "Career",
        "style": "creative",
        "title": "Changing Jobs",
        "decision": "I am thinking about changing jobs."
    },
    {
        "id": "investment",
        "category": "Investment",
        "style": "practical",
        "title": "Index Fund Investment",
        "decision": "I am thinking about investing 50% of my savings into index funds."
    },
    {
        "id": "startup",
        "category": "Startup",
        "style": "practical",
        "title": "AI SaaS Startup",
        "decision": "I am thinking about starting an AI-powered SaaS business."
    },
    {
        "id": "policy",
        "category": "Policy",
        "style": "discovery",
        "title": "Banning Cash",
        "decision": "The government is considering banning physical cash."
    },
    {
        "id": "personal",
        "category": "Personal",
        "style": "balanced",
        "title": "Relocating City",
        "decision": "I am thinking about moving to a new city."
    },
    {
        "id": "technology",
        "category": "Technology",
        "style": "discovery",
        "title": "Offline LLM Migration",
        "decision": "Our company is planning to migrate all servers to local offline LLMs."
    }
]

import sys

async def run_benchmark():
    config = ExperimentConfig(
        workers=10, 
        max_depth=3, 
        branch_factor=2, 
        merge_threshold=0.55, 
        score_threshold=0.4, 
        compression_ratio=0.15,
        batch_expansion=True
    )
    
    print("======================================================================")
    print("RUNNING PARALLEL HYPOTHESIS ENGINE BENCHMARK")
    print(f"Model: {config.ollama_model} | Host: {config.ollama_host}")
    print("======================================================================")

    results_dir = r"d:\RES\experiments\parallel_reasoning_engine\results"
    os.makedirs(results_dir, exist_ok=True)
    
    scenarios = BENCHMARK_SCENARIOS
    if "--smoke" in sys.argv:
        print("[bench] Running SMOKE TEST: limiting to 1 scenario.")
        scenarios = BENCHMARK_SCENARIOS[:1]
        
    benchmark_results = []
    
    parallel_engine = ParallelEngine(config)
    sequential_engine = SequentialEngine(config)
    
    for sc in scenarios:
        print(f"\nScenario: [{sc['category']}] {sc['title']}")
        print(f"Decision: '{sc['decision']}'")
        
        # 1. Run Sequential Baseline Engine
        print("Running Sequential Baseline Engine...")
        seq_start = time.time()
        try:
            seq_out = await sequential_engine.run(sc["decision"])
            seq_time = time.time() - seq_start
            print(f"Sequential run finished in {seq_time:.2f}s. Generated {seq_out['execution_stats']['nodes']['generated']} nodes.")
        except Exception as e:
            print(f"Sequential Engine failed: {e}")
            seq_out = None
            
        # Cooldown between runs to let CPU stabilize
        await asyncio.sleep(2)
            
        # 2. Run Parallel Hypothesis Engine
        print("Running Parallel Hypothesis Engine...")
        par_start = time.time()
        try:
            par_out = await parallel_engine.run(sc["decision"], style=sc["style"])
            par_time = time.time() - par_start
            print(f"Parallel run finished in {par_time:.2f}s. Raw nodes: {par_out['execution_stats']['nodes']['raw_total']}, Compressed nodes: {par_out['execution_stats']['nodes']['compressed_total']}.")
        except Exception as e:
            print(f"Parallel Engine failed: {e}")
            par_out = None
            
        benchmark_results.append({
            "scenario_id": sc["id"],
            "category": sc["category"],
            "style": sc["style"],
            "title": sc["title"],
            "decision": sc["decision"],
            "sequential_engine": seq_out,
            "parallel_engine": par_out
        })
        
        # Save incremental progress
        with open(os.path.join(results_dir, "benchmark_data.json"), "w", encoding="utf-8") as f:
            json.dump(benchmark_results, f, indent=2)
            
        # Cooldown between scenarios
        await asyncio.sleep(2)
        
    print("\nBenchmark runs completed! Results saved to results/benchmark_data.json")

if __name__ == "__main__":
    asyncio.run(run_benchmark())

