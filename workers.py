import json
import asyncio
import httpx

# 1. Define the diverse lenses
WORKER_REGISTRY = {
    "financial_analyst": {
        "persona": "You are a ruthless Financial Risk Analyst. Analyze decisions strictly through capital, overhead, opportunity costs, and cash flow sustainability.",
        "focus": "economic trade-offs, financial liabilities, resource drain"
    },
    "contrarian_optimist": {
        "persona": "You are an aggressive Contrarian Optimist. Look past immediate risks to find hidden, high-upside asymmetric advantages everyone else is missing.",
        "focus": "unobvious opportunities, massive upside, hidden leverage"
    },
    "worst_case_prepper": {
        "persona": "You are a defensive Risk Mitigator. Assume total systemic failure. Find vulnerabilities, fragile assumptions, and downstream catastrophic risks.",
        "focus": "second-order failures, hidden dependencies, unmitigated risks"
    },
    "psychological_human_centric": {
        "persona": "You are a Behavioral Psychologist. Focus strictly on mental fatigue, identity shift, social impact, burnout, and emotional friction.",
        "focus": "cognitive load, relationship strain, long-term motivation"
    }
}

from experiments.parallel_reasoning_engine.context_manager import assemble_compact_context

# 2. Structural response schema enforced for TinyLlama
def get_worker_prompt(worker_id: str, context: str) -> str:
    meta = WORKER_REGISTRY[worker_id]
    return f"""
System: {meta['persona']}
Current Decision Context: "{context}"

Task: Generate exactly 2 distinct causal concepts focusing specifically on: {meta['focus']}.
For each concept, write:
1. A concise headline (under 5 words).
2. The core mechanism / rationale (why/how it happens).

Respond ONLY as a JSON object matching this schema:
{{
  "nodes": [
    {{"label": "Headline", "type": "insight", "rationale": "Detailed reasoning"}}
  ]
}}
"""

MUTATION_REGISTRY = {
    "financial_analyst": "Translate this psychological or technical insight into direct capital overhead, financial risk, or asset drain.",
    "contrarian_optimist": "Look at this risk or failure point. What hidden asymmetric upside or massive pivot advantage does it create?",
    "worst_case_prepper": "Assume this opportunity or idea faces total systemic failure. What hidden dependency causes it to collapse?",
    "psychological_human_centric": "Analyze this financial or risk factor. What is its direct toll on human energy, burnout, and emotional friction?"
}

def get_mutation_prompt(mutator_id: str, parent_node: dict) -> str:
    pressure = MUTATION_REGISTRY[mutator_id]
    label = parent_node.get('label') or parent_node.get('title') or "Concept"
    rationale = parent_node.get('rationale') or parent_node.get('description') or "Details"
    
    return f"""
System: You are an expert strategist mutating a concept.
Parent Concept Label: "{label}"
Parent Concept Rationale: "{rationale}"

Task: Apply this analytical pressure to mutate the concept: {pressure}
Generate exactly 1 mutated variation. Do not use placeholders or Lorem Ipsum.

Respond ONLY as a JSON object matching this schema:
{{
  "nodes": [
    {{"label": "Mutated Headline", "type": "mutation", "rationale": "New mutated rationale"}}
  ]
}}
"""

