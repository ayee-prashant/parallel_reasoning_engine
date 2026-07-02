import asyncio
import time
import uuid
from typing import List, Dict, Any, Tuple
from experiments.parallel_reasoning_engine.config import ExperimentConfig, default_config
from experiments.parallel_reasoning_engine.ollama_client import OllamaClient
from experiments.parallel_reasoning_engine.logger import engine_logger
from experiments.parallel_reasoning_engine.engine import EngineNode, EngineEdge

class SequentialEngine:
    def __init__(self, config: ExperimentConfig = None):
        self.config = config or default_config
        self.client = OllamaClient(
            host=self.config.ollama_host, 
            model=self.config.ollama_model,
            max_concurrency=self.config.max_concurrency
        )

    async def run(self, root_decision: str) -> Dict[str, Any]:
        """Run the sequential reasoning engine baseline."""
        start_time = time.time()
        engine_logger.reset_metrics()
        engine_logger.log_info(f"Starting Sequential Engine baseline run for: '{root_decision}'")

        nodes: Dict[str, EngineNode] = {}
        edges: List[EngineEdge] = []

        # Create Root Node
        root_node = EngineNode(
            title=root_decision,
            description="The starting decision point of the sequential exploration.",
            node_type="root",
            depth=0,
            worker_id="sequential"
        )
        nodes[root_node.id] = root_node

        # ── Phase 1: Batch Root Generation ────────────────────────────────────
        phase1_start = time.time()
        engine_logger.log_info("--- SEQ PHASE 1: Generating Root + Depth-1 Children ---")
        
        system_prompt = (
            "You are a scenario reasoning AI. Your task is to generate a set of exactly 5 immediate, direct consequences of the decision.\n"
            "Include a mix of node types: RISK, OPPORTUNITY, NEUTRAL.\n"
            "Output in a structured JSON array format, return ONLY valid JSON.\n"
            "Format:\n"
            "[\n"
            "  {\n"
            "    \"title\": \"Short Title (3-6 words)\",\n"
            "    \"description\": \"1-2 sentence explanation.\",\n"
            "    \"node_type\": \"consequence|risk|opportunity|neutral\",\n"
            "    \"confidence_level\": \"Very High|High|Medium|Low|Speculative\",\n"
            "    \"impact\": \"LOW|MEDIUM|HIGH|CRITICAL\"\n"
            "  }, ...\n"
            "]"
        )
        
        prompt = f"The user is thinking about: '{root_decision}'. Generate the 5 direct consequences."
        raw_output = await self.client.generate(prompt, system_prompt, temperature=0.6)
        
        try:
            parsed = self.client.extract_and_parse_json(raw_output)
            if not isinstance(parsed, list):
                parsed = [parsed]
                
            for item in parsed[:5]:
                node = EngineNode(
                    title=item.get("title", "Consequence"),
                    description=item.get("description", "Details."),
                    node_type=item.get("node_type", "consequence"),
                    depth=1,
                    worker_id="sequential",
                    metadata={
                        "confidence_level": item.get("confidence_level", "Medium"),
                        "impact": item.get("impact", "MEDIUM")
                    }
                )
                nodes[node.id] = node
                edges.append(EngineEdge(source_id=root_node.id, target_id=node.id, relationship_type="causes"))
                engine_logger.increment_nodes_generated()
        except Exception as e:
            engine_logger.log_error(f"Sequential Phase 1 failed to parse: {e}. Raw: {raw_output[:100]}")
            # Quick fallback mock nodes if generation fails to avoid crashing benchmark
            self._create_fallback_children(root_node, nodes, edges, 1)

        # ── Phase 2: Expand Depth-1 → Depth-2 (Select Top 3) ──────────────────
        phase2_start = time.time()
        engine_logger.log_info("--- SEQ PHASE 2: Expanding Depth-1 Nodes ---")
        
        d1_nodes = [n for n in nodes.values() if n.depth == 1]
        # Rank D1 nodes using a simplified priority score (Impact + Confidence)
        d1_nodes.sort(key=self._score_seq_node, reverse=True)
        nodes_to_expand_d1 = d1_nodes[:3] # Expand top 3
        
        for p_node in nodes_to_expand_d1:
            await self._expand_node(p_node, 2, nodes, edges)

        # ── Phase 3: Expand Depth-2 → Depth-3 (Select Top 2) ──────────────────
        phase3_start = time.time()
        engine_logger.log_info("--- SEQ PHASE 3: Expanding Depth-2 Nodes ---")
        
        d2_nodes = [n for n in nodes.values() if n.depth == 2]
        d2_nodes.sort(key=self._score_seq_node, reverse=True)
        nodes_to_expand_d2 = d2_nodes[:2] # Expand top 2
        
        for p_node in nodes_to_expand_d2:
            await self._expand_node(p_node, 3, nodes, edges)

        # ── Phase 4: Critic Pass ──────────────────────────────────────────────
        phase4_start = time.time()
        engine_logger.log_info("--- SEQ PHASE 4: Critic Pass ---")
        # Run a single critic LLM call to suggest key risk details or hidden assumptions
        critic_summary = await self._run_critic(root_decision, list(nodes.values()))
        
        end_time = time.time()
        execution_stats = engine_logger.compile_stats(
            start_time=start_time,
            phase_times={
                "p1_root": phase2_start - phase1_start,
                "p2_expand_d1": phase3_start - phase2_start,
                "p3_expand_d2": phase4_start - phase3_start,
                "p4_critic": end_time - phase4_start
            },
            raw_node_count=len(nodes),
            consolidated_node_count=len(nodes), # No consolidation in standard sequential
            compressed_node_count=len(nodes)   # No compression in standard sequential
        )
        
        return {
            "root_decision": root_decision,
            "graph": {
                "nodes": [n.to_dict() for n in nodes.values()],
                "edges": [e.to_dict() for e in edges]
            },
            "critic_pass": critic_summary,
            "execution_stats": execution_stats
        }

    async def _expand_node(self, parent_node: EngineNode, target_depth: int, nodes: Dict[str, EngineNode], edges: List[EngineEdge]):
        """Expand a node sequentially by generating children."""
        system_prompt = (
            "You are a scenario reasoning AI. Generate exactly 2 direct consequence nodes of the parent node.\n"
            "Output in a structured JSON array format, return ONLY valid JSON.\n"
            "Format:\n"
            "[\n"
            "  {\n"
            "    \"title\": \"Short Title (3-6 words)\",\n"
            "    \"description\": \"1-2 sentence explanation.\",\n"
            "    \"node_type\": \"consequence|risk|opportunity|neutral\",\n"
            "    \"confidence_level\": \"Very High|High|Medium|Low|Speculative\",\n"
            "    \"impact\": \"LOW|MEDIUM|HIGH|CRITICAL\"\n"
            "  }, ...\n"
            "]"
        )
        
        prompt = (
            f"PARENT NODE:\n"
            f"Title: {parent_node.title}\n"
            f"Description: {parent_node.description}\n"
            f"Generate 2 next-step consequences."
        )
        
        raw_output = await self.client.generate(prompt, system_prompt, temperature=0.6)
        try:
            parsed = self.client.extract_and_parse_json(raw_output)
            if not isinstance(parsed, list):
                parsed = [parsed]
                
            for item in parsed[:2]:
                node = EngineNode(
                    title=item.get("title", "Consequence"),
                    description=item.get("description", "Details."),
                    node_type=item.get("node_type", "consequence"),
                    depth=target_depth,
                    worker_id="sequential",
                    metadata={
                        "confidence_level": item.get("confidence_level", "Medium"),
                        "impact": item.get("impact", "MEDIUM")
                    }
                )
                nodes[node.id] = node
                edges.append(EngineEdge(source_id=parent_node.id, target_id=node.id, relationship_type="causes"))
                engine_logger.increment_nodes_generated()
        except Exception as e:
            engine_logger.log_error(f"Sequential expansion failed for '{parent_node.title}': {e}")
            self._create_fallback_children(parent_node, nodes, edges, target_depth)

    async def _run_critic(self, root_decision: str, all_nodes: List[EngineNode]) -> Dict[str, Any]:
        """Critic pass analyzing the generated nodes for hidden assumptions."""
        titles = [n.title for n in all_nodes if n.node_type != "root"]
        system_prompt = (
            "You are a scenario critic AI. Analyze the reasoning forest titles and identify:\n"
            "1. Hidden Assumptions (underlying beliefs)\n"
            "2. Blind Spots (unexplored areas)\n"
            "Output your findings in a JSON object with keys 'hidden_assumptions' and 'blind_spots', both lists of strings.\n"
            "Return ONLY valid JSON."
        )
        
        prompt = (
            f"Root Decision: {root_decision}\n"
            f"Generated consequences: {', '.join(titles[:15])}\n"
            f"Provide critic analysis."
        )
        
        raw_output = await self.client.generate(prompt, system_prompt, temperature=0.5)
        try:
            return self.client.extract_and_parse_json(raw_output)
        except Exception:
            return {
                "hidden_assumptions": ["Underlying status quo remains stable."],
                "blind_spots": ["Socio-economic feedback loops are under-explored."]
            }

    def _score_seq_node(self, node: EngineNode) -> float:
        # Simple helper score for selection: impact weight + confidence weight
        impact_map = {"LOW": 1.0, "MEDIUM": 2.0, "HIGH": 3.0, "CRITICAL": 4.0}
        conf_map = {"Very High": 5.0, "High": 4.0, "Medium": 3.0, "Low": 2.0, "Speculative": 1.0}
        
        impact = impact_map.get(node.metadata.get("impact", "MEDIUM").upper(), 2.0)
        confidence = conf_map.get(node.metadata.get("confidence_level", "Medium"), 3.0)
        return impact + confidence

    def _create_fallback_children(self, parent: EngineNode, nodes: Dict[str, EngineNode], edges: List[EngineEdge], depth: int):
        """Mock fallback node generation if LLM crashes or outputs invalid format."""
        for i in range(2):
            node = EngineNode(
                title=f"Consequence {i+1} of {parent.title[:20]}",
                description=f"Automated fallback reasoning step detailing causal progression at depth {depth}.",
                node_type="consequence",
                depth=depth,
                worker_id="sequential",
                metadata={"confidence_level": "Medium", "impact": "MEDIUM"}
            )
            nodes[node.id] = node
            edges.append(EngineEdge(source_id=parent.id, target_id=node.id, relationship_type="causes"))
            engine_logger.increment_nodes_generated()
            
