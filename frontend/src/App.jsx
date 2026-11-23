
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";
import "./index.css";

const nodeStyle = {
  width: 165,
  padding: 12,
  borderRadius: 10,
  color: "#f8fafc",
  fontWeight: 600,
  fontSize: 13,
  textAlign: "center",
  border: "1px solid #475569",
  background: "#1e293b",
};

const createNode = (id, label, type, x, y, color) => ({
  id,
  position: { x, y },
  data: { label: `${label}\n${type}` },
  style: {
    ...nodeStyle,
    border: `1px solid ${color}`,
    background: `${color}22`,
  },
});

const initialNodes = [
  createNode("s1", "Shanghai Supplier", "Supplier", 0, 80, "#38bdf8"),
  createNode("s2", "Tokyo Supplier", "Supplier", 0, 300, "#38bdf8"),

  createNode("p1", "Singapore Port", "Port", 260, 80, "#a78bfa"),
  createNode("p2", "Hamburg Port", "Port", 260, 300, "#a78bfa"),

  createNode("f1", "Berlin Factory", "Factory", 520, 80, "#34d399"),
  createNode("f2", "Munich Factory", "Factory", 520, 300, "#34d399"),

  createNode("w1", "Frankfurt Warehouse", "Warehouse", 780, 80, "#fbbf24"),
  createNode("w2", "Paris Warehouse", "Warehouse", 780, 300, "#fbbf24"),

  createNode("c1", "London Retailer", "Customer", 1040, 80, "#fb7185"),
  createNode("c2", "New York Retailer", "Customer", 1040, 300, "#fb7185"),
];

const initialEdges = [
  ["s1", "p1"],
  ["s1", "p2"],
  ["s2", "p1"],
  ["s2", "p2"],
  ["p1", "f1"],
  ["p2", "f2"],
  ["f1", "w1"],
  ["f2", "w2"],
  ["w1", "c1"],
  ["w2", "c2"],
].map(([source, target], index) => ({
  id: `edge-${index}`,
  source,
  target,
  animated: true,
  style: { stroke: "#64748b", strokeWidth: 2 },
  markerEnd: {
    type: MarkerType.ArrowClosed,
    color: "#64748b",
  },
}));

function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>AtmoGraph</h1>
          <p>Supply Chain Ripple Effect Predictor</p>
        </div>
        <span className="status">DEMO NETWORK</span>
      </header>

      <main className="dashboard">
        <section className="welcome">
          <div>
            <h2>Supply Chain Network</h2>
            <p>
              Explore suppliers, ports, factories, warehouses
              and customers through an interconnected network.
            </p>
          </div>
        </section>

        <section className="stats">
          <div className="stat-card">
            <span>Total Nodes</span>
            <strong>10</strong>
          </div>
          <div className="stat-card">
            <span>Connections</span>
            <strong>10</strong>
          </div>
          <div className="stat-card">
            <span>Node Categories</span>
            <strong>5</strong>
          </div>
          <div className="stat-card">
            <span>Data Source</span>
            <strong className="small-value">Mock Data</strong>
          </div>
        </section>

        <section className="graph-section">
          <div className="graph-heading">
            <div>
              <h3>Global Supply Chain Graph</h3>
              <p>Illustrative network for Week 1 development</p>
            </div>
            <span className="live-label">10 NODES</span>
          </div>

          <div className="graph-canvas">
            <ReactFlow
              nodes={initialNodes}
              edges={initialEdges}
              fitView
              fitViewOptions={{ padding: 0.2 }}
              minZoom={0.2}
              maxZoom={2}
              nodesConnectable={false}
            >
              <Background color="#334155" gap={20} />
              <Controls />
              <MiniMap
                nodeColor={(node) => node.style?.borderColor || "#64748b"}
                maskColor="rgba(15, 23, 42, 0.7)"
              />
            </ReactFlow>
          </div>

          <div className="legend">
            <span>🔵 Supplier</span>
            <span>🟣 Port</span>
            <span>🟢 Factory</span>
            <span>🟡 Warehouse</span>
            <span>🔴 Customer</span>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
