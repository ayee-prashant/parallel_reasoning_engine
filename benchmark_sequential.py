# experiments/parallel_reasoning_engine/benchmark_sequential.py
import json
import httpx
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"  # Locally pulled baseline model (8B scale)

def get_sequential_cot_prompt(decision: str) -> str:
    return f"""You are an elite, deep sequential reasoning model. 
Evaluate this decision thoroughly: "{decision}"

TASK:
Explore all immediate, second-order, and third-order consequences. 
Break down the analysis systematically across these core perspective axes:
1. Financial & Capital Overhead Costs
2. Contrarian & Hidden Asymmetric Upsides
3. Systemic Risk Cascades & Failures
4. Psychological Friction & Burnout

CONSTRAINTS:
Reason step-by-step through a continuous, linear chain of thought. Do not summarize early. 
Provide granular, deep, and rigorous details for each axis.
"""

def run_sequential_benchmark():
    decision_text = "I am thinking about quitting my corporate job to build a niche SaaS product."
    payload = {
        "model": MODEL_NAME,
        "prompt": get_sequential_cot_prompt(decision_text),
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 1500  # Allocating space to capture matching token footprint
        }
    }
    
    print(f"Running Sequential Deep CoT Benchmark on {MODEL_NAME}...")
    
    try:
        with httpx.Client(timeout=None) as client:
            response = client.post(OLLAMA_URL, json=payload)
            result = response.json()
            
        brief = result.get("response", "")
        
        # Capture strict token accounting variables from Ollama response metadata
        metrics = {
            "benchmark_model": MODEL_NAME,
            "prompt_tokens": result.get("prompt_eval_count", 0),
            "completion_tokens": result.get("eval_count", 0),
            "total_tokens_consumed": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
        }
        
        # Save output structures relative to script directory
        script_dir = os.path.dirname(__file__)
        results_dir = os.path.join(script_dir, "results")
        os.makedirs(results_dir, exist_ok=True)
        
        brief_path = os.path.join(results_dir, "executive_brief_sequential.md")
        with open(brief_path, "w", encoding="utf-8") as f:
            f.write(brief)
            
        metrics_path = os.path.join(results_dir, "scientific_metrics_sequential.json")
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
            
        print("Sequential baseline run completed successfully.")
        print(json.dumps(metrics, indent=2))
        
    except Exception as e:
        print(f"Benchmark execution failed: {str(e)}")

if __name__ == "__main__":
    run_sequential_benchmark()
