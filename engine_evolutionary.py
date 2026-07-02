import asyncio
import uuid
import difflib
import time
import math
import re
from typing import List, Dict, Set, Any, Tuple
from experiments.parallel_reasoning_engine.config import ExperimentConfig, default_config
from experiments.parallel_reasoning_engine.ollama_client import OllamaClient
from experiments.parallel_reasoning_engine.logger import engine_logger

# ── Specialized Worker Colony ────────────────────────────────────────────────
WORKER_COLONY = [
    {
        "id": "worker_finance",
        "name": "Financial Specialist",
        "instruction": "Focus on money, capital costs, return on investment (ROI), cash flow, business margins, economic incentives, and financial viability.",
        "keywords": ["cost", "revenue", "finance", "dollar", "cash", "capital", "profit", "investment", "expense", "budget", "salary", "pay", "income", "economic", "market", "margin"]
    },
    {
        "id": "worker_social",
        "name": "Social Critic",
        "instruction": "Focus on community impact, public relations, worker welfare, labor dynamics, ethical issues, social equity, and human relationships.",
        "keywords": ["social", "community", "worker", "equity", "people", "public", "ethical", "relationship", "family", "labor", "union", "culture", "welfare", "fairness"]
    },
    {
        "id": "worker_tech",
        "name": "Technical Architect",
        "instruction": "Focus on software/hardware systems, tools, technical debt, scaling challenges, system dependencies, infrastructure, and automated workflows.",
        "keywords": ["tech", "software", "hardware", "tool", "infrastructure", "automation", "debt", "viability", "scaling", "system", "code", "architecture", "server", "data"]
    },
    {
        "id": "worker_personal",
        "name": "Psychological Counselor",
        "instruction": "Focus on individual mental health, personal stress, workload, work-life balance, job satisfaction, skill acquisition, and personal autonomy.",
        "keywords": ["stress", "mental", "happiness", "life", "satisfaction", "well-being", "learning", "growth", "burnout", "personal", "autonomy", "morale", "skill", "training"]
    },
    {
        "id": "worker_long_term",
        "name": "Long-term Strategist",
        "instruction": "Focus on structural trends manifesting over years or decades, permanent transitions, generational shifts, and systemic path dependency.",
        "keywords": ["long-term", "future", "years", "decade", "permanent", "generational", "sustainability", "evolution", "trend", "legacy", "permanent", "structural"]
    },
    {
        "id": "worker_short_term",
        "name": "Short-term Tactician",
        "instruction": "Focus on immediate, fast-paced consequences that appear in days or weeks. Spot tactical friction, operational volatility, and immediate transition costs.",
        "keywords": ["immediate", "short-term", "days", "months", "operational", "tactical", "friction", "volatility", "transition", "implementation", "quick", "temporary"]
    },
    {
        "id": "worker_risk",
        "name": "Worst-case Risk Manager",
        "instruction": "Focus on failure modes, structural vulnerabilities, critical risks, worst-case scenarios, and risk cascades. Highlight what can break.",
        "keywords": ["fail", "danger", "worst-case", "disruption", "downside", "risk", "hazard", "threat", "vulnerability", "collapse", "crisis", "accident", "liability"]
    },
    {
        "id": "worker_opportunity",
        "name": "Best-case Opportunity Hunter",
        "instruction": "Focus on positive upside, market expansion, growth catalysts, new opportunities, leverage points, and best-case synergies.",
        "keywords": ["growth", "best-case", "benefit", "upside", "leverage", "opportunity", "synergy", "catalyst", "advantage", "efficiency", "expansion", "saving"]
    },
    {
        "id": "worker_contrarian",
        "name": "Contrarian Analyst",
        "instruction": "Think against the consensus. Focus on counter-intuitive effects, paradoxes, what happens if standard predictions reverse, and hidden feedback loops.",
        "keywords": ["contrarian", "paradox", "counter-intuitive", "reverse", "opposite", "unexpected", "feedback", "defying", "alternative", "unconventional"]
    },
    {
        "id": "worker_historical",
        "name": "Historical Precedent Researcher",
        "instruction": "Focus on historical analogies, past events that resemble this scenario, institutional memory, and repeating patterns of human behavior.",
        "keywords": ["history", "analog", "precedent", "past", "resemble", "historically", "predecessor", "lesson", "parallel", "archival", "traditional"]
    }
]

# ── Dynamic Style Weights ─────────────────────────────────────────
STYLE_WEIGHTS = {
    "balanced": {
        "worker_finance": 1.0,
        "worker_social": 1.0,
        "worker_tech": 1.0,
        "worker_personal": 1.0,
        "worker_long_term": 1.0,
        "worker_short_term": 1.0,
        "worker_risk": 1.0,
        "worker_opportunity": 1.0,
        "worker_contrarian": 1.0,
        "worker_historical": 1.0
    },
    "discovery": {
        "worker_long_term": 1.5,
        "worker_historical": 1.4,
        "worker_contrarian": 1.3,
        "worker_opportunity": 1.2,
        "worker_risk": 1.1,
        "worker_social": 1.0,
        "worker_personal": 0.8,
        "worker_tech": 0.8,
        "worker_finance": 0.8,
        "worker_short_term": 0.8
    },
    "practical": {
        "worker_short_term": 1.5,
        "worker_finance": 1.4,
        "worker_risk": 1.4,
        "worker_tech": 1.3,
        "worker_opportunity": 1.1,
        "worker_long_term": 1.0,
        "worker_personal": 0.8,
        "worker_social": 0.7,
        "worker_contrarian": 0.7,
        "worker_historical": 0.7
    },
    "contrarian": {
        "worker_contrarian": 1.6,
        "worker_risk": 1.4,
        "worker_social": 1.3,
        "worker_long_term": 1.2,
        "worker_historical": 1.1,
        "worker_personal": 0.9,
        "worker_tech": 0.8,
        "worker_finance": 0.8,
        "worker_short_term": 0.8,
        "worker_opportunity": 0.7
    },
    "creative": {
        "worker_opportunity": 1.5,
        "worker_personal": 1.4,
        "worker_historical": 1.3,
        "worker_contrarian": 1.2,
        "worker_social": 1.1,
        "worker_long_term": 1.1,
        "worker_short_term": 0.9,
        "worker_tech": 0.8,
        "worker_finance": 0.8,
        "worker_risk": 0.7
    }
}

# ── Data structures ───────────────────────────────────────────────────────────
class EngineNode:
    def __init__(
        self,
        title: str,
        description: str,
        node_type: str, # consequence, risk, opportunity, assumption, unknown
        depth: int,
        worker_id: str,
        node_id: str = None,
        provenance: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.id = node_id or str(uuid.uuid4())
        self.title = title.strip()
        self.description = description.strip()
        self.node_type = node_type.lower()
        self.depth = depth
        self.worker_id = worker_id
        self.provenance = provenance or [self.id]
        self.metadata = metadata or {}
        self.scores = {}
        self.combined_score = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "node_type": self.node_type,
            "depth": self.depth,
            "worker_id": self.worker_id,
            "provenance": self.provenance,
            "metadata": self.metadata,
            "scores": self.scores,
            "combined_score": self.combined_score
        }

class EngineEdge:
    def __init__(self, source_id: str, target_id: str, relationship_type: str = "causes", edge_id: str = None, provenance: List[str] = None):
        self.id = edge_id or str(uuid.uuid4())
        self.source_id = source_id
        self.target_id = target_id
        self.relationship_type = relationship_type.lower()
        self.provenance = provenance or [self.id]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type,
            "provenance": self.provenance
        }

# Stopwords for Jaccard similarity
STOP_WORDS = {
    "the", "a", "an", "of", "in", "for", "and", "or", "to", "is", "are", "be",
    "will", "may", "could", "would", "by", "on", "at", "from", "with", "as",
    "its", "it", "this", "that", "these", "those", "their", "our", "your",
    "i", "you", "he", "she", "they", "we", "about", "into", "over", "after"
}

def clean_words(text: str) -> Set[str]:
    words = re.findall(r"\b\w{3,}\b", text.lower())
    return {w for w in words if w not in STOP_WORDS}

def calculate_jaccard(title1: str, title2: str) -> float:
    w1, w2 = clean_words(title1), clean_words(title2)
    if not w1 or not w2:
        return 0.0
    return len(w1 & w2) / len(w1 | w2)

# ── Adaptive Evolutionary Consequence Graph Engine ──────────────────────────
class ParallelEngine:
    def __init__(self, config: ExperimentConfig = None):
        self.config = config or default_config
        self.client = OllamaClient(
            host=self.config.ollama_host, 
            model=self.config.ollama_model,
            max_concurrency=self.config.max_concurrency
        )

    async def run(self, root_decision: str, style: str = "balanced") -> Dict[str, Any]:
        """Run the Adaptive Evolutionary Consequence Graph reasoning forest loop."""
        start_time = time.time()
        engine_logger.reset_metrics()
        
        normalized_style = style.lower()
        engine_logger.log_info(f"Starting Evolutionary Engine (TinyLlama) with style: {normalized_style} for: '{root_decision}'")
        
        # Load Style-Specific Weights
        weights = STYLE_WEIGHTS.get(normalized_style, {w["id"]: 1.0 for w in WORKER_COLONY})
        
        # Keep track of active nodes and edges across generations
        active_nodes: Dict[str, EngineNode] = {}
        active_edges: List[EngineEdge] = []

        # Create Root Node
        root_node = EngineNode(
            title=root_decision,
            description="The starting decision point of the scenario exploration.",
            node_type="root",
            depth=0,
            worker_id="system"
        )
        active_nodes[root_node.id] = root_node

        # Select active workers based on config
        active_workers = WORKER_COLONY[:self.config.workers]

        # Multi-Generation Loop
        for gen in range(1, self.config.generations + 1):
            engine_logger.log_info(f"\n--- GENERATION {gen}: Evolving hypotheses ---")
            
            # Phase 1: Generation / Expansion
            if gen == 1:
                # Generate initial G1 nodes from root decision
                new_nodes_list = await self._generate_g1_nodes(active_workers, root_node)
            else:
                # Expand surviving G(n-1) nodes to G(n)
                surviving_parents = [n for n in active_nodes.values() if n.depth == gen - 1]
                new_nodes_list = await self._generate_gn_nodes(active_workers, surviving_parents, gen)

            # Add G(n) raw candidates to the graph
            for parent_id, node in new_nodes_list:
                active_nodes[node.id] = node
                edge = EngineEdge(source_id=parent_id, target_id=node.id, relationship_type="causes")
                active_edges.append(edge)

            # Phase 2: Competition (Scoring & Pruning)
            engine_logger.log_info(f"Running G{gen} Competition...")
            self._score_nodes_evolutionary(root_decision, active_nodes, weights)
            
            # Prune weaker nodes of the CURRENT generation
            non_root_gen_nodes = [n for n in active_nodes.values() if n.depth == gen]
            non_root_gen_nodes.sort(key=lambda n: n.combined_score, reverse=True)
            
            # Keep top nodes of this generation (e.g. top 50%)
            keep_count = max(4, int(len(non_root_gen_nodes) * 0.5))
            surviving_ids = set([root_node.id] + [n.id for n in active_nodes.values() if n.depth < gen])
            
            for idx, node in enumerate(non_root_gen_nodes):
                if idx < keep_count or node.combined_score >= self.config.score_threshold:
                    surviving_ids.add(node.id)
                else:
                    engine_logger.increment_nodes_deleted()

            # Apply G(n) Pruning
            active_nodes = {nid: n for nid, n in active_nodes.items() if nid in surviving_ids}
            active_edges = [e for e in active_edges if e.source_id in surviving_ids and e.target_id in surviving_ids]
            
            engine_logger.log_info(f"G{gen} Competition completed. Survivors: {len(active_nodes)}")

            # Phase 3: Consolidation (Deduplication & consensus merge)
            engine_logger.log_info(f"Running G{gen} Consolidation...")
            active_nodes, active_edges = self._consolidate_graph(root_node, active_nodes, active_edges)
            engine_logger.log_info(f"G{gen} Consolidation completed. Unique nodes: {len(active_nodes)}")

            # Phase 4: Mutation (Mutate elite nodes to branch new ideas)
            if gen < self.config.generations:
                engine_logger.log_info(f"Running G{gen} Mutation...")
                mutated_nodes = await self._mutate_elite_nodes(active_nodes, active_workers, gen)
                for parent_id, node in mutated_nodes:
                    active_nodes[node.id] = node
                    edge = EngineEdge(source_id=parent_id, target_id=node.id, relationship_type="mutated_consequence")
                    active_edges.append(edge)

        # ── Final Compression & Ancestral Reconnection ────────────────────────
        engine_logger.log_info("\n--- FINAL GRAPH RECONSTRUCTION ---")
        compressed_nodes, compressed_edges = self._compress_and_reconnect(
            root_node, active_nodes, active_edges
        )
        
        # Scoring on compressed graph
        self._score_nodes_evolutionary(root_decision, compressed_nodes, weights)

        # ── Decision Formulation ──────────────────────────────────────────────
        decision_output = self._generate_decision_output(root_decision, compressed_nodes, compressed_edges)
        
        end_time = time.time()
        execution_stats = engine_logger.compile_stats(
            start_time=start_time,
            phase_times={
                "evolutionary_runs": end_time - start_time
            },
            raw_node_count=engine_logger.nodes_generated,
            consolidated_node_count=len(active_nodes),
            compressed_node_count=len(compressed_nodes)
        )
        
        return {
            "root_decision": root_decision,
            "style": style,
            "raw_graph": {
                "nodes": [n.to_dict() for n in active_nodes.values()],
                "edges": [e.to_dict() for e in active_edges]
            },
            "consolidated_graph": {
                "nodes": [n.to_dict() for n in active_nodes.values()],
                "edges": [e.to_dict() for e in active_edges]
            },
            "compressed_graph": {
                "nodes": [n.to_dict() for n in compressed_nodes.values()],
                "edges": [e.to_dict() for e in compressed_edges]
            },
            "decision_output": decision_output,
            "execution_stats": execution_stats
        }

    # ── Generation G=1 ────────────────────────────────────────────────────────
    async def _generate_g1_nodes(self, active_workers: List[Dict], root_node: EngineNode) -> List[Tuple[str, EngineNode]]:
        """Concurrency-limited spawning of workers to generate the first generation (G1)."""
        new_nodes = []
        
        async def run_worker(worker):
            system_prompt = (
                f"You are a scenario reasoning AI worker specializing as a '{worker['name']}'.\n"
                f"Your perspective/objective: {worker['instruction']}\n"
                "Generate exactly 4 distinct nodes representing consequences or factors related to this decision:\n"
                "- Node type must be one of: consequence | risk | opportunity | assumption | unknown\n\n"
                "Output ONLY a valid JSON array format. Do NOT include markdown code blocks, text wrapper tags, or conversational filler.\n"
                "Format:\n"
                "[\n"
                "  {\n"
                "    \"title\": \"Short Title (3-6 words, event-focused)\",\n"
                "    \"description\": \"1-2 sentence explanation.\",\n"
                "    \"node_type\": \"consequence|risk|opportunity|assumption|unknown\",\n"
                "    \"confidence_level\": \"Very High|High|Medium|Low|Speculative\",\n"
                "    \"impact\": \"LOW|MEDIUM|HIGH|CRITICAL\"\n"
                "  }, ...\n"
                "]"
            )
            prompt = f"The user is thinking about: '{root_node.title}'. Generate 4 nodes representing your specialist perspective."
            try:
                raw_output = await self.client.generate(prompt, system_prompt, temperature=0.7)
                parsed = self.client.extract_and_parse_json(raw_output)
                if not isinstance(parsed, list):
                    parsed = [parsed]
                
                nodes = []
                for item in parsed:
                    if not isinstance(item, dict):
                        continue
                    node = EngineNode(
                        title=item.get("title", "Consequence"),
                        description=item.get("description", "Detail description."),
                        node_type=item.get("node_type", "consequence"),
                        depth=1,
                        worker_id=worker["id"],
                        metadata={
                            "confidence_level": item.get("confidence_level", "Medium"),
                            "impact": item.get("impact", "MEDIUM")
                        }
                    )
                    nodes.append(node)
                return nodes
            except Exception as e:
                engine_logger.log_error(f"Worker {worker['name']} failed in G1: {e}")
                return self._fallback_nodes(root_node.title, worker["id"], 1)

        tasks = [run_worker(w) for w in active_workers]
        results = await asyncio.gather(*tasks)
        
        for idx, worker_nodes in enumerate(results):
            for node in worker_nodes:
                new_nodes.append((root_node.id, node))
                engine_logger.increment_nodes_generated()
                
        return new_nodes

    # ── Generation G=N (Expansion) ────────────────────────────────────────────
    async def _generate_gn_nodes(self, active_workers: List[Dict], parent_nodes: List[EngineNode], gen: int) -> List[Tuple[str, EngineNode]]:
        """Concurrency-limited spawning of workers to expand G(n-1) nodes to G(n)."""
        new_nodes = []
        if not parent_nodes:
            return []
            
        async def run_worker_expansion(worker, parent_chunk: List[EngineNode]):
            parent_list_str = ""
            for idx, p in enumerate(parent_chunk):
                parent_list_str += f"[{idx+1}] ID: {p.id} | Title: {p.title} | Desc: {p.description}\n"

            system_prompt = (
                f"You are a scenario reasoning AI worker specializing as a '{worker['name']}'.\n"
                f"Your perspective: {worker['instruction']}\n"
                f"TASK: For each of the following parent nodes, generate exactly {self.config.branch_factor} direct consequence nodes.\n"
                "Return ONLY a valid JSON array of consequence objects. Include the parent_id to identify which parent it belongs to.\n"
                "Format:\n"
                "[\n"
                "  {\n"
                "    \"parent_id\": \"The ID of the parent node you are expanding\",\n"
                "    \"title\": \"Short consequence title (3-6 words)\",\n"
                "    \"description\": \"1-2 sentence explanation.\",\n"
                "    \"node_type\": \"consequence|risk|opportunity|unknown\",\n"
                "    \"confidence_level\": \"Very High|High|Medium|Low|Speculative\",\n"
                "    \"impact\": \"LOW|MEDIUM|HIGH|CRITICAL\"\n"
                "  }, ...\n"
                "]"
            )
            
            prompt = (
                f"PARENT NODES TO EXPAND:\n"
                f"{parent_list_str}\n"
                f"Generate exactly {self.config.branch_factor} consequences for EACH parent node."
            )
            
            try:
                raw_output = await self.client.generate(prompt, system_prompt, temperature=0.7)
                parsed = self.client.extract_and_parse_json(raw_output)
                if not isinstance(parsed, list):
                    parsed = [parsed]
                
                nodes = []
                for item in parsed:
                    if not isinstance(item, dict):
                        continue
                    p_id = item.get("parent_id", "")
                    # Match parent
                    parent_exists = any(p.id == p_id for p in parent_chunk)
                    if not parent_exists:
                        p_id = parent_chunk[0].id
                        
                    node = EngineNode(
                        title=item.get("title", "Consequence"),
                        description=item.get("description", "Details."),
                        node_type=item.get("node_type", "consequence"),
                        depth=gen,
                        worker_id=worker["id"],
                        metadata={
                            "confidence_level": item.get("confidence_level", "Medium"),
                            "impact": item.get("impact", "MEDIUM")
                        }
                    )
                    nodes.append((p_id, node))
                return nodes
            except Exception as e:
                engine_logger.log_error(f"Worker {worker['name']} failed in G{gen} expansion: {e}")
                # Fallback sequentially for each node
                fallback_results = []
                for p in parent_chunk:
                    f_nodes = self._fallback_nodes(p.title, worker["id"], gen)
                    for fn in f_nodes:
                        fallback_results.append((p.id, fn))
                return fallback_results

        # Group parents into chunks to avoid passing too much context to a single LLM call
        chunk_size = 3
        chunks = [parent_nodes[i:i + chunk_size] for i in range(0, len(parent_nodes), chunk_size)]
        
        tasks = []
        for chunk in chunks:
            for w in active_workers:
                tasks.append(run_worker_expansion(w, chunk))
                
        results = await asyncio.gather(*tasks)
        for res in results:
            for p_id, node in res:
                new_nodes.append((p_id, node))
                engine_logger.increment_nodes_generated()
                
        return new_nodes

    # ── Phase 4: Mutation G=1 ─────────────────────────────────────────────────
    async def _mutate_elite_nodes(self, nodes: Dict[str, EngineNode], active_workers: List[Dict], gen: int) -> List[Tuple[str, EngineNode]]:
        """Mutate a subset of surviving elite nodes to introduce contrarian/temporal pivots."""
        mutated_nodes = []
        # Keep non-root nodes of current generation
        gen_nodes = [n for n in nodes.values() if n.depth == gen]
        if not gen_nodes:
            return []
            
        # Select mutated parents based on mutation rate
        num_mutate = max(1, int(len(gen_nodes) * self.config.mutation_rate))
        gen_nodes.sort(key=lambda n: n.combined_score, reverse=True)
        elites = gen_nodes[:num_mutate]
        
        async def run_mutation(parent_node: EngineNode, worker: Dict):
            mutation_types = ["contrarian", "temporal_long_term", "systemic_risk"]
            # Choose mutation type based on worker index to distribute options
            mut_type = mutation_types[hash(parent_node.id + worker["id"]) % len(mutation_types)]
            
            system_prompt = (
                f"You are a scenario reasoning AI worker specializing as a '{worker['name']}'.\n"
                f"Your perspective: {worker['instruction']}\n"
                "TASK: Perform a MUTATION on the target node. Generate a single mutated variation:\n"
                f"- Mutation strategy: {mut_type.upper()}\n"
                "- If CONTRARIAN: What if the opposite effect occurs instead?\n"
                "- If TEMPORAL: What happens years later when feedback loops converge?\n"
                "- If SYSTEMIC: What hidden systemic friction or risk does this reveal?\n\n"
                "Output ONLY a valid JSON object format containing title and description. Do NOT include markdown code blocks.\n"
                "Format:\n"
                "{\n"
                "  \"title\": \"Mutated Title (3-6 words)\",\n"
                "  \"description\": \"1-2 sentence explanation of the mutated pathway.\",\n"
                "  \"node_type\": \"consequence|risk|opportunity|unknown\",\n"
                "  \"confidence_level\": \"Medium|Low|Speculative\",\n"
                "  \"impact\": \"LOW|MEDIUM|HIGH\"\n"
                "}"
            )
            
            prompt = (
                f"TARGET NODE TO MUTATE:\n"
                f"Title: {parent_node.title}\n"
                f"Description: {parent_node.description}\n"
                "Mutate this concept according to the strategy."
            )
            
            try:
                raw_output = await self.client.generate(prompt, system_prompt, temperature=0.8)
                parsed = self.client.extract_and_parse_json(raw_output)
                if not isinstance(parsed, dict):
                    raise ValueError("Not a dictionary")
                
                node = EngineNode(
                    title=parsed.get("title", "Mutated Consequence"),
                    description=parsed.get("description", "Mutated details."),
                    node_type=parsed.get("node_type", "consequence"),
                    depth=gen, # Keep in current generation layer
                    worker_id=f"mutation_{worker['id']}",
                    metadata={
                        "confidence_level": parsed.get("confidence_level", "Medium"),
                        "impact": parsed.get("impact", "MEDIUM"),
                        "mutation_source": parent_node.id,
                        "mutation_type": mut_type
                    }
                )
                return node
            except Exception as e:
                engine_logger.log_error(f"Mutation failed for node '{parent_node.title}': {e}")
                return None

        # Run mutations concurrently
        tasks = []
        for elite in elites:
            # Assign contrarian or risk worker for mutation to ensure diversity
            mut_worker = active_workers[hash(elite.id) % len(active_workers)]
            tasks.append(run_mutation(elite, mut_worker))
            
        results = await asyncio.gather(*tasks)
        for parent_node, mut_node in zip(elites, results):
            if mut_node:
                mutated_nodes.append((parent_node.id, mut_node))
                engine_logger.increment_nodes_generated()
                
        return mutated_nodes

    # ── Phase 2: Competition (Scoring) ────────────────────────────────────────
    def _score_nodes_evolutionary(self, root_decision: str, nodes: Dict[str, EngineNode], weights: Dict[str, float]):
        """Score each node using specialized lexical lenses representing specialized worker opinions."""
        for node in nodes.values():
            if node.node_type == "root":
                node.scores = {w["id"]: 1.0 for w in WORKER_COLONY}
                node.combined_score = 1.0
                continue
                
            node_scores = {}
            for worker in WORKER_COLONY:
                w_id = worker["id"]
                w_weight = weights.get(w_id, 1.0)
                
                # Compute Jaccard lexical match with the worker's keywords
                title_clean = clean_words(node.title + " " + node.description)
                kw_set = set(worker["keywords"])
                
                match_count = len(title_clean & kw_set)
                lexical_score = min(1.0, match_count / 3.0) # 3 keywords matched is 1.0
                
                # Base lens scoring adjustments
                lens_score = 0.4 + 0.6 * lexical_score
                
                # Persona-specific logical alignment
                if w_id == "worker_risk" and node.node_type == "risk":
                    lens_score = max(lens_score, 0.8)
                elif w_id == "worker_opportunity" and node.node_type == "opportunity":
                    lens_score = max(lens_score, 0.8)
                elif w_id == "worker_personal" and node.node_type == "personal":
                    lens_score = max(lens_score, 0.8)
                    
                node_scores[w_id] = round(lens_score, 2)

            # Combined Score is weighted average of worker scores
            weighted_sum = 0.0
            weight_sum = 0.0
            for w_id, score in node_scores.items():
                w_weight = weights.get(w_id, 1.0)
                weighted_sum += score * w_weight
                weight_sum += w_weight
                
            node.scores = node_scores
            node.combined_score = round(weighted_sum / weight_sum, 2)

    # ── Phase 3: Jaccard Consolidation ────────────────────────────────────────
    def _consolidate_graph(self, root: EngineNode, nodes: Dict[str, EngineNode], edges: List[EngineEdge]) -> Tuple[Dict[str, EngineNode], List[EngineEdge]]:
        """Consolidate the graph by merging duplicate nodes within the same generation."""
        nodes_list = list(nodes.values())
        nodes_list.sort(key=lambda n: n.depth)
        
        node_map: Dict[str, str] = {n.id: n.id for n in nodes_list}
        depths = set(n.depth for n in nodes_list)
        
        for depth in depths:
            if depth == 0:
                continue
                
            depth_nodes = [n for n in nodes_list if n.depth == depth]
            if len(depth_nodes) < 2:
                continue
                
            visited = set()
            for i, n1 in enumerate(depth_nodes):
                if n1.id in visited:
                    continue
                    
                cluster = [n1]
                visited.add(n1.id)
                
                for n2 in depth_nodes[i+1:]:
                    if n2.id in visited:
                        continue
                        
                    jaccard = calculate_jaccard(n1.title, n2.title)
                    sm_ratio = difflib.SequenceMatcher(None, n1.title.lower(), n2.title.lower()).ratio()
                    similarity = max(jaccard, sm_ratio)
                    
                    if similarity >= self.config.merge_threshold:
                        cluster.append(n2)
                        visited.add(n2.id)
                        engine_logger.increment_nodes_merged()
                        
                if len(cluster) > 1:
                    # Representative node: longest description (specificity)
                    cluster.sort(key=lambda n: len(n.description), reverse=True)
                    rep = cluster[0]
                    
                    merged_provenance = []
                    merged_workers = set()
                    
                    for n in cluster:
                        merged_provenance.extend(n.provenance)
                        merged_workers.add(n.worker_id)
                        node_map[n.id] = rep.id
                        
                    rep.provenance = list(set(merged_provenance))
                    rep.metadata["merged_workers"] = list(merged_workers)

        # Build final consolidated dictionary
        consolidated_nodes: Dict[str, EngineNode] = {}
        for n in nodes_list:
            mapped_id = node_map[n.id]
            if mapped_id not in consolidated_nodes:
                consolidated_nodes[mapped_id] = nodes[mapped_id]
                
        # Remap edges
        consolidated_edges: List[EngineEdge] = []
        seen_edges = set()
        
        for edge in edges:
            new_source = node_map.get(edge.source_id, edge.source_id)
            new_target = node_map.get(edge.target_id, edge.target_id)
            
            if new_source != new_target:
                edge_key = (new_source, new_target)
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    consolidated_edges.append(
                        EngineEdge(
                            source_id=new_source,
                            target_id=new_target,
                            relationship_type=edge.relationship_type,
                            provenance=edge.provenance
                        )
                    )
                    
        return consolidated_nodes, consolidated_edges

    # ── Phase 5: Compression & Ancestral Reconnection ────────────────────────
    def _compress_and_reconnect(self, root: EngineNode, nodes: Dict[str, EngineNode], edges: List[EngineEdge]) -> Tuple[Dict[str, EngineNode], List[EngineEdge]]:
        """Keep only top N% elite evolved nodes and reconnect paths to maintain graph connectivity."""
        non_root_nodes = [n for n in nodes.values() if n.node_type != "root"]
        if not non_root_nodes:
            return {root.id: root}, []
            
        # Target compression ratio
        num_keep = max(5, int(len(non_root_nodes) * self.config.compression_ratio))
        
        non_root_nodes.sort(key=lambda n: n.combined_score, reverse=True)
        surviving_nodes = {root.id: root}
        
        for i, n in enumerate(non_root_nodes):
            if i < num_keep or n.combined_score >= self.config.score_threshold:
                surviving_nodes[n.id] = n
            else:
                engine_logger.increment_nodes_deleted()

        # Build adjacency list
        adj: Dict[str, List[str]] = {nid: [] for nid in nodes}
        for edge in edges:
            adj[edge.source_id].append(edge.target_id)
            
        # Graph Reconnection: Find reachability without going through other survivors
        compressed_edges: List[EngineEdge] = []
        seen_edges = set()
        
        for source_id in surviving_nodes:
            queue = [(source_id, False)]
            visited = set()
            
            while queue:
                curr_id, passed_survivor = queue.pop(0)
                if curr_id in visited:
                    continue
                visited.add(curr_id)
                
                if curr_id != source_id and curr_id in surviving_nodes:
                    edge_key = (source_id, curr_id)
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        compressed_edges.append(
                            EngineEdge(
                                source_id=source_id,
                                target_id=curr_id,
                                relationship_type="indirectly_leads_to" if passed_survivor else "causes"
                            )
                        )
                    continue
                    
                for child_id in adj.get(curr_id, []):
                    is_pruned = passed_survivor or (curr_id != source_id and curr_id not in surviving_nodes)
                    queue.append((child_id, is_pruned))

        return surviving_nodes, compressed_edges

    # ── Decision Formulation ──────────────────────────────────────────────
    def _generate_decision_output(self, root_decision: str, nodes: Dict[str, EngineNode], edges: List[EngineEdge]) -> Dict[str, Any]:
        """Summarize evolved recommendations and critical nodes."""
        non_root = [n for n in nodes.values() if n.node_type != "root"]
        non_root.sort(key=lambda n: n.combined_score, reverse=True)
        
        risks = [n for n in non_root if n.node_type == "risk"]
        opportunities = [n for n in non_root if n.node_type == "opportunity"]
        unknowns = [n for n in non_root if n.node_type == "unknown"]
        actions = [n for n in non_root if n.node_type in ["adaptation", "solution", "consequence"]]
        
        recommended_actions = [
            {
                "title": n.title,
                "description": n.description,
                "score": n.combined_score,
                "why": n.metadata.get("why_generated", "Elite consequence from the evolved reasoning forest.")
            }
            for n in actions[:5]
        ]
        
        key_risks = [
            {
                "title": n.title,
                "description": n.description,
                "impact": n.metadata.get("impact", "HIGH"),
                "confidence": n.metadata.get("confidence_level", "Medium")
            }
            for n in risks[:5]
        ]

        key_opportunities = [
            {
                "title": n.title,
                "description": n.description,
                "impact": n.metadata.get("impact", "HIGH"),
                "confidence": n.metadata.get("confidence_level", "Medium")
            }
            for n in opportunities[:5]
        ]
        
        critical_unknowns = [
            {
                "title": n.title,
                "description": n.description,
                "confidence": n.metadata.get("confidence_level", "Low")
            }
            for n in unknowns[:5]
        ]

        summary = (
            f"Adaptive evolutionary graph analysis of '{root_decision}' evolved {len(non_root)} elite nodes from {engine_logger.nodes_generated} candidates. "
            f"The final evolved forest prioritized {len(recommended_actions)} recommended strategic actions, "
            f"identified {len(key_risks)} key systemic risks, and isolated {len(critical_unknowns)} critical unknowns."
        )

        return {
            "summary": summary,
            "recommended_actions": recommended_actions,
            "key_risks": key_risks,
            "key_opportunities": key_opportunities,
            "critical_unknowns": critical_unknowns
        }

    def _fallback_nodes(self, parent_title: str, worker_id: str, depth: int) -> List[EngineNode]:
        """Mock fallback node generation if Ollama fails."""
        nodes = []
        for i in range(2):
            node = EngineNode(
                title=f"{worker_id.split('_').pop().title()} Factor {i+1} of {parent_title[:20]}",
                description=f"Fallback consequence step generated at depth {depth}.",
                node_type="consequence",
                depth=depth,
                worker_id=worker_id
            )
            nodes.append(node)
        return nodes
