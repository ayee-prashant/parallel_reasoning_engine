# experiments/parallel_reasoning_engine/context_manager.py

def assemble_compact_context(worker_persona: str, task_objective: str, current_node: dict, style_config: dict) -> str:
    """
    Assembles a high-density, low-token context window strictly aligned 
    with modern context engineering principles.
    """
    # 1. Front-load the Static Mission and Goal
    context_blocks = [
        f"# MISSION\n{worker_persona}",
        f"\n# OBJECTIVE\n{task_objective}",
    ]
    
    # 2. Inject Curated Dynamic Facts (Ancestry and State)
    provenance_str = ", ".join(current_node.get("provenance", []))
    context_blocks.append(
        f"\n# KNOWN FACTS\n"
        f"• Parent Node: {current_node.get('label', 'None')}\n"
        f"• Lineage: [{provenance_str}]\n"
        f"• Current Consensus Score: {current_node.get('consensus_score', 1.0)}"
    )
    
    # 3. Inject Constraints & Style Parameters
    context_blocks.append(
        f"\n# CONSTRAINTS\n"
        f"• Engine: CPU Only\n"
        f"• Style Matrix: {style_config.get('active_style', 'balanced')}\n"
        f"• Max Output Tokens: 300"
    )
    
    # 4. Enforce Structured Output Schema
    context_blocks.append(
        f"\n# OUTPUT SCHEMA\n"
        f"Respond ONLY as a JSON object matching this key-value signature:\n"
        f'{{"nodes": [{{"label": "Headline", "type": "insight", "rationale": "Reasoning"}}]}}'
    )
    
    return "\n".join(context_blocks)
