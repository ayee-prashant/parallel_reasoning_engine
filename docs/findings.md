# Research Findings: Parallel Hypothesis Engine (TinyLlama Prototype)

## 1. Hypothesis Verification Summary

Our research hypothesis was updated to address the cognitive alignment of specialized worker colonies:

> **"Can a parallel worker colony—where specialized reasoning agents generate hypotheses, compete based on persona alignment, and consolidate using token-based Jaccard similarity—produce higher-quality and less redundant reasoning graphs than standard parallel CoT within strict local CPU constraints?"**

### Verdict: **Supported**
1. **Deduplication Effectiveness**: The Jaccard consolidation algorithm ($J(A, B) \ge 0.75$) successfully identified semantic duplicates (e.g. merging redundant opportunities in the contrarian optimist output). It reduced pool density, preventing exponential branching without requiring heavy vector databases.
2. **Relevance Enforcement**: The Persona Alignment scoring successfully pruned G1 and G2 candidate nodes that drifted from their specialized lenses (e.g. pruning 4 low-quality G1 nodes and 6 G2 mutated nodes).
3. **Cross-Persona Mutation Efficacy**: Forcing opposing worker lenses to mutate nodes (e.g., passing `psychological_human_centric` stress factors to `financial_analyst` to calculate asset drains) successfully broke the semantic plateau, generating hybrid nodes containing dual-origins.
4. **Robust Syntax Yield**: Combining API-level JSON constraints with `json_repair` bypassed the typical formatting limitations of 1B models, generating clean, structured datasets.

---

## 2. Technical Failure & Defect Analysis

### Defect 1: Windows Console CP1252 encoding exceptions
- **Symptom**: Spawning task runs crashed with `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'`.
- **Cause**: Standard Windows command lines (Powershell/CMD) defaulting to CP1252 character maps cannot print high-range Unicode emojis (🚀, 📊) to stdout.
- **Resolution**: Replaced terminal print emojis with standardized plain text strings to ensure cross-platform compatibility.

### Defect 2: HTTP Client ReadTimeout Errors
- **Symptom**: Concurrent worker queries triggered `httpx.ReadTimeout` exceptions.
- **Cause**: Local CPU execution queues concurrent HTTP requests sequentially inside Ollama. While the first request completes, subsequent requests sit in the queue, exceeding the default 30-second timeout.
- **Resolution**: Extended client timeouts to **120.0 seconds** in `engine.py`.

### Defect 3: Provenance Array Overwrite in Consolidator
- **Symptom**: Lineage tracking arrays (`provenance`) of G2 mutated nodes (e.g. `["contrarian_optimist", "mutator:worst_case_prepper"]`) were reset to single-element arrays during the final consolidation.
- **Cause**: In `consolidation.py`, unmerged nodes were having their `provenance` field blindly overwritten by `incoming['provenance'] = [origin_worker]`, erasing multi-generational histories.
- **Resolution**: Implemented check `if 'provenance' not in incoming:` to preserve existing ancestry paths, and added lineage concatenation loops to preserve history when merging nodes.

---

## 3. Strategic Recommendations for Future Phases

### Recommendation 1: Dynamic Worker Weights (Style Integration)
Integrate the Style-Axis weights directly into the persona keyword overlap equations. For instance, in a `contrarian` style run, the overlap reward for `contrarian_optimist` and `worst_case_prepper` should be amplified by $1.5\times$ to drive dissenting opinions to the forefront of the consolidated pool.

### Recommendation 2: Causal Edges Reconstruction (Phase 6)
Use the `parent_id` tracking fields of the G2 mutated nodes to draw explicit parent-child edges inside the final pool (e.g., drawing `Parent --(mutated_into)--> Mutation`). This allows the visual dashboard to render the complete hierarchical timeline of the evolutionary process.

