# Research Architecture: Parallel Hypothesis Engine (TinyLlama Prototype)

## 1. System Design

The Parallel Hypothesis Engine explores cascading consequences of high-stakes decisions by leveraging a specialized agent colony instead of standard sequential Chain-of-Thought (CoT) or homogeneous parallel expansions. 

The architecture is built as an asynchronous DAG generation engine targeting local CPU commodity hardware. It shifts reasoning from "linear path search" to "natural selection over cognitive diversity."

```
                         [Root Decision Prompt]
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
 [Financial Analyst]      [Contrarian Optimist]     [Worst-Case Prepper] ...
   (Economic Lens)          (Asymmetric Upside)        (Systemic Risk)
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   ▼
                       [Generation 1 Raw Pool]
                                   │
                                   ▼
                     [Persona Alignment Scoring]  <── (Keyword Profiles)
                                   │
                                   ▼
                       [Global Threshold Filter]  <── (score_threshold: 0.60)
                                   │
                                   ▼
                     [Jaccard Similarity Merge]   <── (similarity_threshold: 0.75)
                                   │
                                   ▼
                    [Consolidated Hypothesis Pool]
```

---

## 2. Dynamic Style-Axis Weights (Strict Invariant I-3 Compliance)

To comply with the What If Maps architectural invariants—specifically **Invariant I-3 (No DOMAIN axis)**—the engine maps specialized worker weights to cognitive **Styles** rather than scenario domains. This prevents the model from generating static, consultancylike categories, focusing instead on dynamic causal pathways.

The active styles configuration adjusts the weight influence of worker scores during competition scoring:

| Reasoning Style | Primary Cognitive Lens | Supporting Lenses | Target Focus |
|---|---|---|---|
| **Balanced** | Uniform weights (1.0) | None | Unbiased structural baseline synthesis. |
| **Discovery** | Long-Term, Historical, Contrarian | Opportunity | Promotes unconventional, multi-year causal chains. |
| **Practical** | Short-Term, Finance, Risk | Technical | Focuses on capital expenditure, execution speed, and tactical blockers. |
| **Contrarian** | Contrarian, Risk | Social, Historical | Exposes consensus biases, structural blind spots, and systemic risk cascades. |
| **Creative** | Opportunity, Personal | Historical, Social | Focuses on asymmetric upsides and behavioral/social human elements. |

---

## 3. Two-Tiered Competition (Selection Phase)

To control entropy and keep the hypothesis pool clean under compute constraints, candidates must pass a two-tiered competition gauntlet before consolidation:

### Tier 1: Persona Alignment Scoring
Each node is evaluated against the keyword profile of its originating worker lens to ensure cognitive compliance.
- Let $W_{id}$ be the originating worker id, and $K(W_{id})$ be its corresponding set of specialized keywords.
- Let $T(Node)$ be the set of unique words extracted from the node's title, label, and rationale.
- The alignment overlap $O$ is defined as:
  $$O = |T(Node) \cap K(W_{id})|$$
- The alignment score $S_{align}$ decays the node's structural weight if the agent drifts away from its persona guidelines:
  $$S_{align} = 0.50 + 0.25 \times \min(2, O)$$
  *(Thus: 0 matches = 0.50 score, 1 match = 0.75 score, 2+ matches = 1.00 score)*

### Tier 2: Global Thresholding
Nodes falling below the defined threshold are pruned:
$$S_{align} < \text{score\_threshold} \implies \text{Pruned}$$
Under our default setup, the $\text{score\_threshold} = 0.60$. Consequently, any generated node with zero specialized keyword matches (scoring 0.50) is automatically deleted.

---

## 4. Jaccard-Based Consolidation (Deduplication Phase)

To handle semantic overlaps without resorting to heavy, CPU-intensive embedding models, we implement a token-based Jaccard similarity index.

### Mathematical Formulation
For any two nodes $A$ and $B$, their text fields are tokenized into normalized keyword sets $Set_A$ and $Set_B$ (excluding common grammatical stop words). The similarity $J(A, B)$ is calculated as:
$$J(A, B) = \frac{|Set_A \cap Set_B|}{|Set_A \cup Set_B|}$$

- If $J(A, B) \ge \text{similarity\_threshold}$ (default: 0.75), nodes $A$ and $B$ are merged.
- **Consensus Accumulation**: The surviving node is rewarded for consensus agreement. Its score increases dynamically:
  $$S_{consensus} = 1.0 + 0.2 \times N_{merges}$$
- **Provenance Lineage**: The merged node retains the `origin_worker` identifiers of all parent nodes in a `provenance` array, preserving auditing traces.

---

## 5. Cross-Persona Mutation (Phase 4)

To prevent cognitive echoing and break semantic plateaus, Gen 1 consolidated nodes undergo cross-persona mutation. Surviving concepts are passed to an opposing worker lens which evaluates the idea under adversarial analytical pressure:

| Parent Node Primary Origin | Mutator Agent Persona | Mutation Pressure Applied |
|---|---|---|
| `financial_analyst` | `contrarian_optimist` | Identify the unquantifiable asymmetric upside within this financial risk. |
| `contrarian_optimist` | `worst_case_prepper` | Assume this opportunity fails completely. Pinpoint the fatal systemic flaw. |
| `worst_case_prepper` | `psychological_human_centric` | Evaluate the direct psychological toll of preparing for this system failure. |
| `psychological_human_centric` | `financial_analyst` | Translate this behavioral friction into direct economic overhead or capital cost. |

---

## 6. Next-Gen Expansion & Final Consolidation (Phase 5)

1. **G2 Spawning**: The cross-persona mutations generate child variations, forming the Generation 2 ($G=2$) candidate pool.
2. **G2 Competition**: The mutated variations are scored using the persona alignment keyword filters of the mutator agents, and pruned if they fall below the `score_threshold` (0.60).
3. **Final Unified Graph Consolidation**: The surviving G2 mutated nodes are merged into the original G1 consolidated pool using Jaccard token-based consolidation. This establishes cross-generational consensus linkages.

---

## 7. Auditable Causal Lineage Tracking

When a node undergoes mutation or Jaccard merging, its history is cataloged in the output dictionary:
- `parent_id`: Tracks the unique identifier of the ancestral node in $G=1$.
- `generation`: Indicates the evolutionary step ($1 \implies G1$, $2 \implies G2$ mutated child).
- `provenance`: An ordered list mapping the evolutionary journey, e.g., `["psychological_human_centric", "mutator:financial_analyst"]` tells us the concept was conceived by the Psychological agent and transformed by the Financial worker.

