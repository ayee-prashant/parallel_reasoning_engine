import os
import json
import re

TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Evolutionary Hypothesis Causal DAG Visualizer</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        :root {
            --bg-main: #030712;
            --bg-card: rgba(17, 24, 39, 0.7);
            --border-card: rgba(255, 255, 255, 0.08);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.15);
            --font-family: 'Plus Jakarta Sans', sans-serif;
            --font-heading: 'Outfit', sans-serif;
            
            /* Node Colors */
            --color-root: #ffffff;
            --color-finance: #10b981;
            --color-contrarian: #8b5cf6;
            --color-prepper: #ef4444;
            --color-psychology: #3b82f6;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-main);
            color: var(--text-main);
            font-family: var(--font-family);
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.08) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.05) 0px, transparent 50%);
        }

        header {
            border-bottom: 1px solid var(--border-card);
            padding: 1rem 2rem;
            background-color: rgba(3, 7, 18, 0.5);
            backdrop-filter: blur(12px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 10;
        }

        h1 {
            font-family: var(--font-heading);
            font-size: 1.35rem;
            font-weight: 700;
            background: linear-gradient(135deg, #fff 30%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.2rem;
        }

        main {
            height: calc(100vh - 65px);
            display: grid;
            grid-template-columns: 1fr 360px;
            grid-template-rows: 100%;
            overflow: hidden;
            position: relative;
        }

        #network-container {
            height: 100%;
            width: 100%;
            background: rgba(0, 0, 0, 0.25);
            position: relative;
            overflow: hidden;
        }

        .sidebar {
            background: var(--bg-card);
            border-left: 1px solid var(--border-card);
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            height: 100%;
            overflow-y: auto;
            backdrop-filter: blur(12px);
        }

        .panel-title {
            font-family: var(--font-heading);
            font-size: 1.1rem;
            font-weight: 600;
            border-bottom: 1px solid var(--border-card);
            padding-bottom: 0.75rem;
        }

        .node-inspector {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            height: 100%;
        }

        .inspector-placeholder {
            margin: auto;
            text-align: center;
            color: var(--text-muted);
            font-style: italic;
            font-size: 0.9rem;
        }

        .detail-row {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .detail-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .detail-val {
            font-size: 0.9rem;
            line-height: 1.4;
        }

        .tag-pill {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            width: fit-content;
        }

        .tag-finance { background: rgba(16, 185, 129, 0.15); color: #34d399; }
        .tag-contrarian { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }
        .tag-prepper { background: rgba(239, 68, 68, 0.15); color: #f87171; }
        .tag-psychology { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
        .tag-root { background: rgba(255, 255, 255, 0.15); color: #ffffff; }

        .legend {
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(17, 24, 39, 0.85);
            border: 1px solid var(--border-card);
            padding: 1rem;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            z-index: 5;
            font-size: 0.8rem;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .legend-color {
            width: 14px;
            height: 14px;
            border-radius: 50%;
        }

        .legend-shape {
            display: inline-block;
            border: 1.5px solid var(--text-muted);
            width: 14px;
            height: 14px;
        }

        .shape-circle { border-radius: 50%; }
        .shape-diamond { transform: rotate(45deg); width: 10px; height: 10px; margin-left: 2px; }
    </style>
</head>
<body>

    <header>
        <div>
            <h1>Evolutionary Hypothesis Causal DAG</h1>
            <div class="subtitle">Interactive Causal Forest Topology Map (Phase 4-6 Visualizer)</div>
        </div>
        <div style="font-size: 0.8rem; text-align: right; color: var(--text-muted);">
            <div>Decision Target: <span style="color:#fff; font-weight:500;">Corporate Job to SaaS</span></div>
            <div>Evolutions: <span style="color:var(--primary)">G1 (Lenses) &rarr; G2 (Mutations)</span></div>
        </div>
    </header>

    <main>
        <div id="network-container">
            <div class="legend">
                <div style="font-weight: 600; margin-bottom: 0.25rem; font-size: 0.85rem;">Perspectives (Color)</div>
                <div class="legend-item"><div class="legend-color" style="background:var(--color-root)"></div>Starting Decision Node</div>
                <div class="legend-item"><div class="legend-color" style="background:var(--color-finance)"></div>Financial Analyst</div>
                <div class="legend-item"><div class="legend-color" style="background:var(--color-contrarian)"></div>Contrarian Optimist</div>
                <div class="legend-item"><div class="legend-color" style="background:var(--color-prepper)"></div>Worst-Case Prepper</div>
                <div class="legend-item"><div class="legend-color" style="background:var(--color-psychology)"></div>Psychological Analyst</div>
                
                <div style="font-weight: 600; margin-top: 0.5rem; margin-bottom: 0.25rem; font-size: 0.85rem;">Generations (Shape)</div>
                <div class="legend-item"><span class="legend-shape shape-circle"></span>Generation G=1 (Circles)</div>
                <div class="legend-item"><span class="legend-shape shape-diamond"></span>Generation G=2 Mutated (Diamonds)</div>
            </div>
        </div>

        <div class="sidebar">
            <div class="panel-title">Hypothesis Inspector</div>
            <div id="inspector-panel" class="node-inspector">
                <div class="inspector-placeholder">
                    Click on any node in the causal graph to inspect its evolutionary properties, consensus metrics, and ancestry.
                </div>
            </div>
        </div>
    </main>

    <script>
        const graphData = {{ graph_json }};
        
        // Colors mapping
        const colors = {
            "root": "#ffffff",
            "financial_analyst": "#10b981",
            "contrarian_optimist": "#8b5cf6",
            "worst_case_prepper": "#ef4444",
            "psychological_human_centric": "#3b82f6"
        };

        const nodes = graphData.nodes.map(n => {
            const origin = n.origin_worker || "root";
            const color = colors[origin] || "#6366f1";
            
            // Set shape: G1 standard circle, G2 mutated diamond
            const shape = n.generation === 2 ? "diamond" : (origin === "root" ? "ellipse" : "dot");
            
            // Set size: scaled based on consensus score
            const baseSize = origin === "root" ? 22 : 14;
            const size = baseSize * (n.consensus_score || 1.0);
            
            // Short label for network bubble
            const fullText = n.label || n.title || "";
            const shortLabel = fullText.length > 25 ? fullText.substring(0, 22) + "..." : fullText;

            return {
                id: n.id,
                label: shortLabel,
                title: fullText, // tooltip
                shape: shape,
                size: size,
                color: {
                    background: color,
                    border: "#111827",
                    highlight: {
                        background: color,
                        border: "#ffffff"
                    }
                },
                font: {
                    color: origin === "root" ? "#000000" : "#ffffff",
                    face: "Plus Jakarta Sans",
                    size: origin === "root" ? 13 : 11
                },
                shadow: true,
                borderWidth: 1.5,
                // store original node data
                _raw: n
            };
        });

        const edges = graphData.edges.map(e => ({
            from: e.from,
            to: e.to,
            arrows: "to",
            color: {
                color: "rgba(255, 255, 255, 0.25)",
                highlight: "#6366f1"
            },
            width: 1.5,
            smooth: {
                type: "cubicBezier",
                roundness: 0.5
            }
        }));

        const container = document.getElementById('network-container');
        const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) };
        
        const options = {
            physics: {
                solver: "forceAtlas2Based",
                forceAtlas2Based: {
                    gravitationalConstant: -40,
                    centralGravity: 0.01,
                    springLength: 80,
                    springConstant: 0.08
                },
                stabilization: {
                    iterations: 150
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 300
            }
        };

        const network = new vis.Network(container, data, options);

        network.on("click", function (params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = nodes.find(n => n.id === nodeId);
                if (node && node._raw) {
                    showDetails(node._raw);
                }
            }
        });

        function showDetails(raw) {
            const panel = document.getElementById("inspector-panel");
            const origin = raw.origin_worker || "system_root";
            const tagClass = origin.replace(/_/g, '-');
            const displayOrigin = origin.replace(/_/g, ' ').toUpperCase();
            
            const provenanceList = (raw.provenance || []).map(p => `<li>${p}</li>`).join("");

            panel.innerHTML = `
                <div class="detail-row">
                    <span class="detail-label">Hypothesis Title</span>
                    <span class="detail-val" style="font-weight:600; font-size:0.95rem;">${raw.label || raw.title}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Origin Lens</span>
                    <span class="tag-pill tag-${raw.origin_worker || 'root'}">${displayOrigin}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">Generation</span>
                    <span class="detail-val" style="font-family:var(--font-heading); font-size:1rem; font-weight:600;">G = ${raw.generation || 1}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">Consensus Score</span>
                    <span class="detail-val" style="font-family:var(--font-heading); font-size:1.15rem; font-weight:700; color:var(--primary);">${raw.consensus_score ? raw.consensus_score.toFixed(2) : "1.00"}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">Keyword Alignment Score</span>
                    <span class="detail-val">${raw.alignment_score ? raw.alignment_score.toFixed(2) : "1.00"}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">Causal Rationale</span>
                    <span class="detail-val" style="color:var(--text-muted); font-size:0.85rem;">${raw.rationale || raw.description || "N/A"}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">Parent Ancestor Label</span>
                    <span class="detail-val" style="font-size:0.8rem; font-style:italic;">${raw.parent_id || "None (Root G1 Hypothesis)"}</span>
                </div>

                <div class="detail-row">
                    <span class="detail-label">Provenance Trail</span>
                    <ul style="padding-left:1.1rem; font-size:0.8rem; color:var(--text-muted); display:flex; flex-direction:column; gap:0.2rem;">
                        ${provenanceList}
                    </ul>
                </div>
            `;
        }
    </script>
</body>
</html>
"""

def generate_visual_dag(nodes: list, root_decision: str, output_html_path: str):
    """
    Generate a Vis.js causal graph DAG from the final evolutionary pool.
    We automatically draw edges from:
      1. Root node to all Generation 1 nodes.
      2. G1 parent nodes to G2 mutated children nodes using parent_id matches.
    """
    os.makedirs(os.path.dirname(output_html_path), exist_ok=True)
    
    # 1. Prepare unique node IDs
    nodes_data = []
    
    # Add Root Node
    root_id = "root_decision_node"
    nodes_data.append({
        "id": root_id,
        "label": root_decision,
        "title": root_decision,
        "origin_worker": "root",
        "generation": 0,
        "consensus_score": 1.5,
        "alignment_score": 1.0,
        "rationale": "The starting point for specialized worker colony exploration.",
        "provenance": ["system_root"]
    })
    
    # Map label to unique IDs
    label_to_id = {}
    
    # First, register node IDs and clean up duplicates in labels
    for idx, node in enumerate(nodes):
        node_id = f"node_{idx+1}"
        node["id"] = node_id
        nodes_data.append(node)
        
        # Strip potential quotes/whitespace to match labels robustly
        label = node.get("label") or node.get("title") or ""
        clean_lbl = label.strip().lower()
        label_to_id[clean_lbl] = node_id
        
    # 2. Build Causal Edges
    edges_data = []
    
    for node in nodes:
        node_id = node["id"]
        generation = node.get("generation", 1)
        
        if generation == 1:
            # G1 nodes are daughters of the starting root decision node
            edges_data.append({
                "from": root_id,
                "to": node_id
            })
        elif generation == 2:
            # G2 mutated nodes are linked to their G1 parent
            parent_lbl = node.get("parent_id") or ""
            clean_parent = parent_lbl.strip().lower()
            
            parent_id_found = None
            
            # Find matching parent node by label similarity or substring
            if clean_parent in label_to_id:
                parent_id_found = label_to_id[clean_parent]
            else:
                # Fallback: substring matching
                for lbl, nid in label_to_id.items():
                    if clean_parent in lbl or lbl in clean_parent:
                        parent_id_found = nid
                        break
            
            if parent_id_found:
                edges_data.append({
                    "from": parent_id_found,
                    "to": node_id
                })
            else:
                # If parent not found, fallback: connect to root
                edges_data.append({
                    "from": root_id,
                    "to": node_id
                })
                
    # 3. Compile output dictionary
    graph_dict = {
        "nodes": nodes_data,
        "edges": edges_data
    }
    
    # 4. Render HTML file
    rendered_html = TEMPLATE_HTML.replace("{{ graph_json }}", json.dumps(graph_dict, indent=2))
    
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)
        
    print(f"[visualizer] Causal DAG Visualizer successfully compiled at: {output_html_path}")

if __name__ == "__main__":
    # Test generation from raw results if available
    results_dir = r"d:\RES\experiments\parallel_reasoning_engine\results"
    os.makedirs(results_dir, exist_ok=True)
    
    # We can fetch the latest nodes run
    test_decision = "I am thinking about quitting my corporate job to build a niche SaaS product."
    
    from engine import run_generation_one
    import asyncio
    
    print("[visualizer] Running engine to fetch latest nodes...")
    nodes_pool = asyncio.run(run_generation_one(test_decision))
    
    viz_path = r"d:\RES\experiments\parallel_reasoning_engine\visualization\dag_dashboard.html"
    generate_visual_dag(nodes_pool, test_decision, viz_path)
