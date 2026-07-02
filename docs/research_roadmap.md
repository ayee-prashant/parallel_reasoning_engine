# Empirical Evaluation & Research Roadmap: Parallel Hypothesis Engine

This document formalizes the research roadmap for evaluating the **Parallel Hypothesis Engine (TinyLlama Prototype)**. It serves as an onboarding and guidance template for humans and agents running experiments on this codebase.

---

## 🔬 Core Architectural Hypothesis

> **"Decision quality depends more on the quality of selection among many candidate reasoning paths than on increasing the reasoning depth of a single path."**

This architecture treats intelligence not as a linear thinking depth problem, but as an **evolutionary selection problem** (emergence from selection).

---

## 📊 Empirical Experiments Registry

To validate this hypothesis, run the following benchmark suites using the configuration parameters:

### 1. Branch Count Scaling (10 – 500 Branches)
* **Goal**: Determine when return-on-compute diminishes.
* **Method**:
  - Run the colony with $N = 4, 10, 50, 100, 200$ workers.
  - **Metrics**: 
    - *Duplicate Ratio*: Number of merged nodes / total generated nodes.
    - *Novelty Ratio*: Number of distinct, unmerged nodes surviving consolidation.
    - *Inference Latency*: Total CPU runtime.

### 2. Generational Evolution Depth ($G = 1$ to $G = 5$)
* **Goal**: Experimentally determine if decision quality plateaus after G2 or continues to improve.
* **Method**:
  - Run the evolutionary loop extending past Generation 2.
  - **Metrics**:
    - *Semantic Stagnation*: Tracing token cosine similarity or phrasing repetition across generation depths.
    - *Pruning Rate*: Percentage of nodes culled per generation.

### 3. Compute Allocation Trade-offs (Model vs. Branches)
* **Goal**: Measure the optimal allocation of a fixed token budget.
* **Method**:
  - Compare **TinyLlama (1.1B)** × 200 parallel branches against **Qwen-2.5 (7B)** × 20 branches and **Llama-3 (8B)** × 5 branches.
  - **Metrics**:
    - *Quality per Token*: Human/evaluator grading of the final strategic summary divided by total token cost.

### 4. Semantic Convergence Stability (Seed Variance)
* **Goal**: Verify if selection is deterministic or highly random.
* **Method**:
  - Execute the identical decision prompt over 20 iterations with randomized seeds.
  - **Metrics**:
    - *Graph Jaccard Distance*: Measuring topological overlap between the 20 resulting final DAGs.

---

## 🛠️ Mitigating Current Structural Limitations

### 1. The Heuristic Trap: Persona Keyword Scoring
- **Problem**: Nodes survive because they match expected vocabulary ($S_{align}$), not because they are logically correct.
- **Mitigation (Phase 7)**: Replace static lexicons with **Epistemic Selection Oracles**:
  - Run a lightweight validation pass (e.g. using a CPU-quantized DeBERTa classifier) to grade the causal link's logic.
  - Penalize nodes that assert facts conflicting with a predefined "Known Truth" facts database.

### 2. Semantic vs. Epistemic Deduplication
- **Problem**: Jaccard similarity ($J \ge 0.75$) groups identical wording, not identical truth values.
- **Mitigation (Phase 7)**: Utilize **Entailment Scoring**. Merge nodes if Node A logically entails Node B ($A \implies B$), rather than relying purely on overlapping vocabulary sets.

---

## 🗺️ Path to Decision-Consequence Graphs

To transition the prototype from evolving **text** to evolving **strategic decisions**, we must map the data pipeline to support causal consequences:

```
        [ Starting Strategic Decision ]
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
[ Consequence Branch A ]   [ Consequence Branch B ]
         │                           │
         ▼                           ▼
  [ Evidence Base ]           [ Evidence Base ]
         │                           │
         ▼                           ▼
 [ Critical Unknowns ]       [ Critical Unknowns ]
         │                           │
         └─────────────┬─────────────┘
                       ▼
            [ Decision Quality Grade ]
```

### Next-Gen Causal Node Schema Requirements:
1. **`node_type`**: Restrict to `decision`, `consequence`, `evidence`, or `unknown`.
2. **`evidence_links`**: Array of verified document references or web-grounded URLs.
3. **`dissonance_score`**: Measuring contradiction against known constraints (e.g. if capital requirement exceeds budget).

---

## 🛠️ Implementation Blueprints

### 1. Token Budget Equalizer Loop (`benchmark_suite.py`)
To monitor computational parity during trials, use this accounting class to parse Ollama response fields:

```python
class TokenAccountant:
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def log_metrics(self, response_json: dict):
        self.total_prompt_tokens += response_json.get("prompt_eval_count", 0)
        self.total_completion_tokens += response_json.get("eval_count", 0)

    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens
```

### 2. Causal Node Typing Schema
Enforce structural identity checking on memory nodes:

```python
from typing import List, Literal, TypedDict

class CausalNode(TypedDict):
    node_id: str
    node_type: Literal["decision", "consequence", "evidence", "unknown"]
    label: str
    rationale: str
    evidence_links: List[str]  # Maps to verified document hashes or URLs
    dissonance_score: float    # Flips to high if contradicting constraints
    provenance: List[str]
    consensus_score: float
```

### 3. Natural Language Inference Entailment Check (`entailment.py`)
Replace lexical overlap with NLI logics utilizing lightweight ONNX models on CPU:

```python
def check_epistemic_entailment(node_a: str, node_b: str) -> str:
    """
    Evaluates logical relationship between Node A and Node B.
    Returns: 'entailment' (merge), 'contradiction' (flag), or 'neutral' (separate).
    """
    # Standard NLI logic:
    # Premise: "Quitting my corporate job introduces direct asset drain."
    # Hypothesis: "I will face severe financial liabilities immediately."
    # Output: Entailment (Merge nodes and preserve parent_id)
    pass
```

