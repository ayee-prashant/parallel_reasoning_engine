import os
import json
import jinja2

TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Parallel Hypothesis Engine - Research Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #030712;
            --bg-card: rgba(17, 24, 39, 0.7);
            --border-card: rgba(255, 255, 255, 0.08);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.15);
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --unknown: #8b5cf6;
            --neutral: #6b7280;
            --font-family: 'Plus Jakarta Sans', sans-serif;
            --font-heading: 'Outfit', sans-serif;
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
            min-height: 100vh;
            overflow-x: hidden;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.1) 0px, transparent 50%),
                radial-gradient(at 50% 0%, rgba(139, 92, 246, 0.08) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(16, 185, 129, 0.05) 0px, transparent 50%);
        }

        header {
            border-bottom: 1px solid var(--border-card);
            padding: 1.5rem 2rem;
            backdrop-filter: blur(10px);
            background-color: rgba(3, 7, 18, 0.5);
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        h1 {
            font-family: var(--font-heading);
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            background: linear-gradient(135deg, #fff 30%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            font-size: 0.875rem;
            color: var(--text-muted);
        }

        main {
            max-width: 1600px;
            margin: 0 auto;
            padding: 2rem;
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 2rem;
        }

        /* Sidebar Navigation */
        .sidebar {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 16px;
            padding: 1.5rem;
            height: fit-content;
            backdrop-filter: blur(12px);
        }

        .sidebar-title {
            font-family: var(--font-heading);
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-main);
        }

        .scenario-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .scenario-btn {
            width: 100%;
            background: none;
            border: 1px solid transparent;
            color: var(--text-muted);
            padding: 0.75rem 1rem;
            border-radius: 10px;
            text-align: left;
            font-family: var(--font-family);
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .scenario-btn:hover {
            background: rgba(255, 255, 255, 0.03);
            color: var(--text-main);
        }

        .scenario-btn.active {
            background: var(--primary-glow);
            border-color: rgba(99, 102, 241, 0.3);
            color: var(--text-main);
            font-weight: 600;
        }

        /* Content Area */
        .content {
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
        }

        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 14px;
            padding: 1.25rem;
            backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .metric-label {
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .metric-values {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }

        .metric-value-primary {
            font-family: var(--font-heading);
            font-size: 1.75rem;
            font-weight: 700;
        }

        .metric-value-secondary {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        /* Compare View Container */
        .dashboard-row {
            display: grid;
            grid-template-columns: 1fr 380px;
            gap: 2rem;
        }

        .viz-card {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            gap: 1rem;
            height: 600px;
            position: relative;
        }

        .viz-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .tab-bar {
            display: flex;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 0.25rem;
            border: 1px solid var(--border-card);
        }

        .tab-btn {
            background: none;
            border: none;
            color: var(--text-muted);
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-family: var(--font-family);
            transition: all 0.2s ease;
        }

        .tab-btn.active {
            background: var(--primary);
            color: #fff;
            font-weight: 500;
        }

        .canvas-container {
            flex: 1;
            width: 100%;
            border-radius: 12px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-card);
            overflow: hidden;
            position: relative;
        }

        svg {
            width: 100%;
            height: 100%;
        }

        /* Inspector Panel */
        .inspector-card {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            height: 600px;
            overflow-y: auto;
        }

        .inspector-title {
            font-family: var(--font-heading);
            font-size: 1.1rem;
            font-weight: 600;
            border-bottom: 1px solid var(--border-card);
            padding-bottom: 0.75rem;
        }

        .inspector-empty {
            color: var(--text-muted);
            font-style: italic;
            font-size: 0.9rem;
            text-align: center;
            margin: auto 0;
        }

        .node-detail-type {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .type-consequence { background: rgba(99, 102, 241, 0.15); color: #818cf8; }
        .type-risk { background: rgba(239, 68, 68, 0.15); color: #f87171; }
        .type-opportunity { background: rgba(16, 185, 129, 0.15); color: #34d399; }
        .type-assumption { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
        .type-unknown { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }

        /* Report Overview */
        .report-section {
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .recommendation-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .recommendation-item {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-card);
            border-radius: 12px;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .recommendation-title {
            font-weight: 600;
            font-size: 0.95rem;
            display: flex;
            justify-content: space-between;
        }

        .recommendation-score {
            font-size: 0.8rem;
            color: var(--primary);
            background: var(--primary-glow);
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
        }

        /* SVG Node styling */
        .node-circle {
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .node-circle:hover {
            transform: scale(1.15);
            filter: brightness(1.2);
        }

        .edge-line {
            fill: none;
            stroke-width: 1.5;
            transition: all 0.3s ease;
        }
        
        .legend {
            position: absolute;
            bottom: 15px;
            left: 15px;
            background: rgba(0,0,0,0.4);
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.8rem;
            display: flex;
            gap: 10px;
            border: 1px solid var(--border-card);
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }

    </style>
</head>
<body>

    <header>
        <div>
            <h1>Parallel Hypothesis Engine</h1>
            <div class="subtitle">Research Evaluation & Visualizer Dashboard (Offline Prototype)</div>
        </div>
        <div>
            <div style="font-size:0.8rem; text-align:right;">
                <div>Host: <span style="color:var(--primary)">Ollama</span></div>
                <div>Model: <span style="color:var(--primary)">TinyLlama</span></div>
            </div>
        </div>
    </header>

    <main>
        <div class="sidebar">
            <div class="sidebar-title">Scenarios</div>
            <ul class="scenario-list" id="scenario-nav">
                <!-- Nav buttons populated by JS -->
            </ul>
        </div>

        <div class="content">
            <!-- Metrics Summary Cards -->
            <div class="metrics-grid" id="metrics-summary">
                <!-- Metrics filled by JS -->
            </div>

            <!-- Visualization Row -->
            <div class="dashboard-row">
                <div class="viz-card">
                    <div class="viz-header">
                        <h3 id="current-scenario-title" style="font-family:var(--font-heading); font-size:1.1rem;">Changing Jobs</h3>
                        <div class="tab-bar">
                            <button class="tab-btn active" onclick="switchGraph('parallel_compressed')">Compressed Graph</button>
                            <button class="tab-btn" onclick="switchGraph('parallel_consolidated')">Consolidated Graph</button>
                            <button class="tab-btn" onclick="switchGraph('parallel_raw')">Raw Workers Forest</button>
                            <button class="tab-btn" onclick="switchGraph('sequential')">Sequential Baseline</button>
                        </div>
                    </div>
                    <div class="canvas-container" id="svg-host">
                        <!-- SVG dynamically rendered here -->
                        <svg id="network-svg"></svg>
                        <div class="legend">
                            <div class="legend-item"><div class="legend-color" style="background:#6366f1"></div>Consequence</div>
                            <div class="legend-item"><div class="legend-color" style="background:#ef4444"></div>Risk</div>
                            <div class="legend-item"><div class="legend-color" style="background:#10b981"></div>Opportunity</div>
                            <div class="legend-item"><div class="legend-color" style="background:#f59e0b"></div>Assumption</div>
                            <div class="legend-item"><div class="legend-color" style="background:#8b5cf6"></div>Unknown</div>
                        </div>
                    </div>
                </div>

                <div class="inspector-card">
                    <div class="inspector-title">Node Inspector</div>
                    <div id="inspector-content" class="inspector-empty">
                        Click on any node in the graph to inspect its details and scores.
                    </div>
                </div>
            </div>

            <!-- Decisions Summary Output -->
            <div class="report-section" id="decision-report">
                <!-- Dynamically compiled decision reports -->
            </div>
        </div>
    </main>

    <script>
        // Inline dataset generated by dashboard.py
        const BENCHMARK_DATA = {{ benchmark_data }};
        
        let currentScenarioId = BENCHMARK_DATA[0].scenario_id;
        let currentGraphType = 'parallel_compressed'; // parallel_compressed, parallel_consolidated, parallel_raw, sequential
        let selectedNode = null;

        // Init navigation
        function initNav() {
            const nav = document.getElementById("scenario-nav");
            nav.innerHTML = "";
            BENCHMARK_DATA.forEach((sc, idx) => {
                const li = document.createElement("li");
                const btn = document.createElement("button");
                btn.className = `scenario-btn ${sc.scenario_id === currentScenarioId ? 'active' : ''}`;
                btn.innerText = `[Style: ${sc.style.toUpperCase()}] ${sc.title}`;
                btn.onclick = () => selectScenario(sc.scenario_id);
                li.appendChild(btn);
                nav.appendChild(li);
            });
        }

        function selectScenario(id) {
            currentScenarioId = id;
            document.querySelectorAll(".scenario-btn").forEach(btn => {
                btn.classList.toggle("active", btn.innerText.includes(BENCHMARK_DATA.find(s => s.scenario_id === id).title));
            });
            renderDashboard();
        }

        function switchGraph(type) {
            currentGraphType = type;
            document.querySelectorAll(".tab-btn").forEach(btn => {
                btn.classList.toggle("active", btn.innerText.toLowerCase().includes(type.split('_').pop()));
            });
            renderGraph();
        }

        function getcolor(type) {
            const colors = {
                "root": "#ffffff",
                "consequence": "#6366f1",
                "risk": "#ef4444",
                "opportunity": "#10b981",
                "assumption": "#f59e0b",
                "unknown": "#8b5cf6",
                "neutral": "#6b7280"
            };
            return colors[type.toLowerCase()] || "#6366f1";
        }

        function renderDashboard() {
            const sc = BENCHMARK_DATA.find(s => s.scenario_id === currentScenarioId);
            document.getElementById("current-scenario-title").innerText = `[Style: ${sc.style.toUpperCase()}] ${sc.title} ("${sc.decision}")`;
            
            // Render metrics comparison
            const summary = document.getElementById("metrics-summary");
            summary.innerHTML = "";
            
            const stats = sc.parallel_engine ? sc.parallel_engine.execution_stats : null;
            const seq_stats = sc.sequential_engine ? sc.sequential_engine.execution_stats : null;
            
            if (stats && seq_stats) {
                // Latency card
                addMetricCard(summary, "Execution Latency", `${stats.execution_time_s}s`, `Sequential: ${seq_stats.execution_time_s}s`);
                // Node expansion density card
                addMetricCard(summary, "Raw Hypotheses", stats.nodes.raw_total, `Sequential: ${seq_stats.nodes.raw_total} nodes`);
                // Compression & Deduplication card
                addMetricCard(summary, "Deduplication Rate", `${Math.round(stats.metrics.duplicate_ratio * 100)}%`, `Merged: ${stats.nodes.merged}`);
                // Memory Delta card
                addMetricCard(summary, "Avg Scoring (Novelty)", `${stats.metrics.compression_ratio * 100}%`, `Compressed: ${stats.nodes.compressed_total}`);
            }

            // Render Graph
            renderGraph();

            // Render Decision Report
            renderReport(sc);
        }

        function addMetricCard(parent, label, value, subtext) {
            const card = document.createElement("div");
            card.className = "metric-card";
            card.innerHTML = `
                <div class="metric-label">${label}</div>
                <div class="metrics-values">
                    <span class="metric-value-primary">${value}</span>
                    <span class="metric-value-secondary">${subtext}</span>
                </div>
            `;
            parent.appendChild(card);
        }

        function renderGraph() {
            const sc = BENCHMARK_DATA.find(s => s.scenario_id === currentScenarioId);
            const svg = document.getElementById("network-svg");
            svg.innerHTML = ""; // Clear
            
            let nodes = [];
            let edges = [];
            
            if (currentGraphType === 'parallel_compressed') {
                nodes = sc.parallel_engine.compressed_graph.nodes;
                edges = sc.parallel_engine.compressed_graph.edges;
            } else if (currentGraphType === 'parallel_consolidated') {
                nodes = sc.parallel_engine.consolidated_graph.nodes;
                edges = sc.parallel_engine.consolidated_graph.edges;
            } else if (currentGraphType === 'parallel_raw') {
                nodes = sc.parallel_engine.raw_graph.nodes;
                edges = sc.parallel_engine.raw_graph.edges;
            } else if (currentGraphType === 'sequential') {
                nodes = sc.sequential_engine.graph.nodes;
                edges = sc.sequential_engine.graph.edges;
            }

            // Simple layout engine: horizontal layers based on depth
            const width = svg.clientWidth || 800;
            const height = svg.clientHeight || 550;
            
            const depthMap = {};
            nodes.forEach(n => {
                if (!depthMap[n.depth]) depthMap[n.depth] = [];
                depthMap[n.depth].push(n);
            });
            
            const maxDepth = Math.max(...nodes.map(n => n.depth));
            const xStep = (width - 160) / maxDepth;
            
            // Assign x, y coordinates
            const nodeCoords = {};
            
            Object.keys(depthMap).forEach(depthStr => {
                const depth = parseInt(depthStr);
                const layerNodes = depthMap[depth];
                const yStep = (height - 80) / (layerNodes.length + 1);
                
                layerNodes.forEach((node, idx) => {
                    const x = 80 + depth * xStep;
                    const y = 40 + (idx + 1) * yStep;
                    nodeCoords[node.id] = { x, y };
                });
            });

            // Draw Edge Curves
            edges.forEach(edge => {
                const s = nodeCoords[edge.source_id];
                const t = nodeCoords[edge.target_id];
                if (s && t) {
                    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                    // Cubic bezier curve for nice connector paths
                    const mx = (s.x + t.x) / 2;
                    const d = `M ${s.x} ${s.y} C ${mx} ${s.y}, ${mx} ${t.y}, ${t.x} ${t.y}`;
                    path.setAttribute("d", d);
                    path.setAttribute("class", "edge-line");
                    path.setAttribute("stroke", "rgba(255,255,255,0.15)");
                    svg.appendChild(path);
                }
            });

            // Draw Node Circles
            nodes.forEach(node => {
                const coord = nodeCoords[node.id];
                if (coord) {
                    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
                    
                    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                    circle.setAttribute("cx", coord.x);
                    circle.setAttribute("cy", coord.y);
                    circle.setAttribute("r", node.node_type === 'root' ? 12 : 8);
                    circle.setAttribute("fill", getcolor(node.node_type));
                    circle.setAttribute("class", "node-circle");
                    circle.setAttribute("stroke", "rgba(255,255,255,0.2)");
                    circle.setAttribute("stroke-width", "1");
                    
                    circle.onclick = () => showNodeDetails(node);
                    
                    // Add light tooltip label
                    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
                    text.setAttribute("x", coord.x);
                    text.setAttribute("y", coord.y - 14);
                    text.setAttribute("text-anchor", "middle");
                    text.setAttribute("fill", "rgba(255,255,255,0.65)");
                    text.setAttribute("font-size", "9px");
                    // truncate text
                    const labelText = node.title.length > 20 ? node.title.substring(0, 18) + "..." : node.title;
                    text.textContent = labelText;
                    
                    g.appendChild(circle);
                    g.appendChild(text);
                    svg.appendChild(g);
                }
            });
        }

        function showNodeDetails(node) {
            const inspector = document.getElementById("inspector-content");
            
            // Format scores list
            let scoresHtml = "";
            if (node.scores && Object.keys(node.scores).length > 0) {
                const isWorkerBased = Object.keys(node.scores).some(k => k.startsWith("worker_"));
                if (isWorkerBased) {
                    let workerScores = "";
                    Object.entries(node.scores).forEach(([wId, val]) => {
                        const name = wId.split("_").slice(1).join(" ").toUpperCase();
                        workerScores += `<div>${name}: <span style="font-weight:600">${Math.round(val * 100)}%</span></div>`;
                    });
                    scoresHtml = `
                        <div style="margin-top: 1rem; border-top:1px solid var(--border-card); padding-top:0.75rem;">
                            <h4 style="font-size:0.85rem; margin-bottom:0.5rem; text-transform:uppercase; color:var(--text-muted)">Worker Specialist Lenses</h4>
                            <div style="display:grid; grid-template-columns: 1fr; gap:0.5rem; font-size:0.8rem;">
                                ${workerScores}
                            </div>
                            <div style="font-size:0.9rem; font-weight:700; margin-top:0.75rem; color:var(--primary)">Combined Decision Score: ${Math.round(node.combined_score * 100)}/100</div>
                        </div>
                    `;
                } else {
                    scoresHtml = `
                        <div style="margin-top: 1rem; border-top:1px solid var(--border-card); padding-top:0.75rem;">
                            <h4 style="font-size:0.85rem; margin-bottom:0.5rem; text-transform:uppercase; color:var(--text-muted)">Hypothesis Scores</h4>
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.5rem; font-size:0.8rem;">
                                <div>Relevance: <span style="font-weight:600">${Math.round(node.scores.relevance * 100)}%</span></div>
                                <div>Novelty: <span style="font-weight:600">${Math.round(node.scores.novelty * 100)}%</span></div>
                                <div>Impact: <span style="font-weight:600">${Math.round(node.scores.impact * 100)}%</span></div>
                                <div>Confidence: <span style="font-weight:600">${Math.round(node.scores.confidence * 100)}%</span></div>
                                <div>Specificity: <span style="font-weight:600">${Math.round(node.scores.specificity * 100)}%</span></div>
                                <div>Actionability: <span style="font-weight:600">${Math.round(node.scores.actionability * 100)}%</span></div>
                            </div>
                            <div style="font-size:0.9rem; font-weight:700; margin-top:0.75rem; color:var(--primary)">Combined Decision Score: ${Math.round(node.combined_score * 100)}/100</div>
                        </div>
                    `;
                }
            }

            let provenanceHtml = "";
            if (node.metadata && node.metadata.merged_workers) {
                provenanceHtml = `
                    <div style="margin-top: 0.75rem; font-size:0.8rem; color:var(--text-muted)">
                        <strong>Worker Consensus:</strong> ${node.metadata.merged_workers.join(', ')}
                    </div>
                `;
            } else if (node.worker_id) {
                provenanceHtml = `
                    <div style="margin-top: 0.75rem; font-size:0.8rem; color:var(--text-muted)">
                        <strong>Generated by:</strong> ${node.worker_id}
                    </div>
                `;
            }

            inspector.innerHTML = `
                <div style="display:flex; flex-direction:column; gap:0.75rem;">
                    <div>
                        <span class="node-detail-type type-${node.node_type}">${node.node_type}</span>
                        <span style="font-size:0.8rem; color:var(--text-muted); float:right;">Depth ${node.depth}</span>
                    </div>
                    <h3 style="font-family:var(--font-heading); font-size:1.2rem; font-weight:600;">${node.title}</h3>
                    <p style="font-size:0.9rem; line-height:1.5; color:var(--text-main);">${node.description}</p>
                    ${provenanceHtml}
                    ${scoresHtml}
                </div>
            `;
        }

        function renderReport(sc) {
            const report = document.getElementById("decision-report");
            report.innerHTML = "";
            
            if (!sc.parallel_engine || !sc.parallel_engine.decision_output) {
                report.innerHTML = "<div class='inspector-empty'>No decision outputs generated.</div>";
                return;
            }
            
            const out = sc.parallel_engine.decision_output;
            
            let recsHtml = "";
            out.recommended_actions.forEach(rec => {
                recsHtml += `
                    <li class="recommendation-item">
                        <div class="recommendation-title">
                            <span>${rec.title}</span>
                            <span class="recommendation-score">Priority Score: ${Math.round(rec.score * 100)}</span>
                        </div>
                        <p style="font-size:0.85rem; color:var(--text-muted); line-height:1.4;">${rec.description}</p>
                        <p style="font-size:0.8rem; color:var(--primary); font-style:italic; margin-top:0.25rem;">Rationale: ${rec.why}</p>
                    </li>
                `;
            });

            let risksHtml = "";
            out.key_risks.forEach(rk => {
                risksHtml += `
                    <div style="border-left: 2px solid var(--danger); padding-left: 10px; margin-bottom: 0.75rem;">
                        <div style="font-weight:600; font-size:0.9rem;">${rk.title}</div>
                        <div style="font-size:0.8rem; color:var(--text-muted)">${rk.description}</div>
                    </div>
                `;
            });

            let oppsHtml = "";
            out.key_opportunities.forEach(op => {
                oppsHtml += `
                    <div style="border-left: 2px solid var(--success); padding-left: 10px; margin-bottom: 0.75rem;">
                        <div style="font-weight:600; font-size:0.9rem;">${op.title}</div>
                        <div style="font-size:0.8rem; color:var(--text-muted)">${op.description}</div>
                    </div>
                `;
            });

            report.innerHTML = `
                <h3 style="font-family:var(--font-heading); font-size:1.2rem; font-weight:600; margin-bottom:1rem;">Decision Formulation Summary</h3>
                <p style="font-size:0.95rem; line-height:1.5; margin-bottom:1.5rem; color:var(--text-muted)">${out.summary}</p>
                
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:2rem;">
                    <div>
                        <h4 style="font-family:var(--font-heading); font-size:1rem; font-weight:600; margin-bottom:1rem; color:var(--primary)">Recommended Strategic Actions</h4>
                        <ul class="recommendation-list">
                            ${recsHtml}
                        </ul>
                    </div>
                    
                    <div style="display:flex; flex-direction:column; gap:1.5rem;">
                        <div>
                            <h4 style="font-family:var(--font-heading); font-size:1rem; font-weight:600; margin-bottom:0.75rem; color:var(--danger)">Key Systemic Risks</h4>
                            ${risksHtml}
                        </div>
                        <div>
                            <h4 style="font-family:var(--font-heading); font-size:1rem; font-weight:600; margin-bottom:0.75rem; color:var(--success)">Primary Opportunities</h4>
                            ${oppsHtml}
                        </div>
                    </div>
                </div>
            `;
        }

        // Run on load
        window.addEventListener('resize', renderGraph);
        initNav();
        renderDashboard();

    </script>
</body>
</html>
"""

def generate_dashboard():
    results_dir = r"d:\RES\experiments\parallel_reasoning_engine\results"
    viz_dir = r"d:\RES\experiments\parallel_reasoning_engine\visualization"
    os.makedirs(viz_dir, exist_ok=True)
    
    json_path = os.path.join(results_dir, "benchmark_data.json")
    if not os.path.exists(json_path):
        print(f"[dashboard] Error: {json_path} does not exist. Run benchmark first.")
        return
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Render using Jinja2
    template = jinja2.Template(TEMPLATE_HTML)
    html_output = template.render(benchmark_data=json.dumps(data))
    
    out_path = os.path.join(viz_dir, "dashboard.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_output)
        
    print(f"[dashboard] Beautiful HTML dashboard compiled successfully at: {out_path}")

if __name__ == "__main__":
    generate_dashboard()
