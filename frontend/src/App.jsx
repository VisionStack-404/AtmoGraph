
import { useEffect, useState } from "react";
import axios from "axios";

import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";
import "./index.css";

const API_URL = "http://127.0.0.1:8000/api/graph";

// Positions for the sample supply-chain layout
const positions = {
  s1: { x: 0, y: 80 },
  s2: { x: 0, y: 300 },
  p1: { x: 260, y: 80 },
  p2: { x: 260, y: 300 },
  f1: { x: 520, y: 80 },
  f2: { x: 520, y: 300 },
  w1: { x: 780, y: 80 },
  w2: { x: 780, y: 300 },
  c1: { x: 1040, y: 80 },
  c2: { x: 1040, y: 300 },
};

const colors = {
  Supplier: "#38bdf8",
  Port: "#a78bfa",
  Factory: "#34d399",
  Warehouse: "#fbbf24",
  Customer: "#fb7185",
};

function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await axios.get(API_URL);

        const graphNodes = response.data.nodes.map((item, index) => {
          const color = colors[item.type] || "#64748b";

          return {
            id: item.id,
            position: positions[item.id] || {
              x: (index % 3) * 260,
              y: Math.floor(index / 3) * 180,
            },
            data: {
              label: `${item.name}\n${item.type}`,
              details: item,
            },
            style: {
              width: 165,
              padding: 12,
              borderRadius: 10,
              color: "#f8fafc",
              fontWeight: 600,
              fontSize: 13,
              textAlign: "center",
              whiteSpace: "pre-line",
              border: `1px solid ${color}`,
              background: `${color}22`,
            },
          };
        });

        const graphEdges = response.data.edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          animated: true,
          style: {
            stroke: "#64748b",
            strokeWidth: 2,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: "#64748b",
          },
        }));

        setNodes(graphNodes);
        setEdges(graphEdges);
      } catch (err) {
        console.error("Graph API error:", err);
        setError(
          "Unable to load graph data. Check whether the FastAPI backend is running."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchGraph();
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>AtmoGraph</h1>
          <p>Supply Chain Ripple Effect Predictor</p>
        </div>

        <span className="status">
          {loading ? "CONNECTING..." : error ? "API ERROR" : "API CONNECTED"}
        </span>
      </header>

      <main className="dashboard">
        <section className="welcome">
          <h2>Supply Chain Network</h2>
          <p>
            Explore suppliers, ports, factories, warehouses
            and customers through an interconnected network.
          </p>
        </section>

        <section className="stats">
          <div className="stat-card">
            <span>Total Nodes</span>
            <strong>{nodes.length}</strong>
          </div>

          <div className="stat-card">
            <span>Connections</span>
            <strong>{edges.length}</strong>
          </div>

          <div className="stat-card">
            <span>Node Categories</span>
            <strong>{new Set(nodes.map((n) => n.data.details.type)).size}</strong>
          </div>

          <div className="stat-card">
            <span>Data Source</span>
            <strong className="small-value">FastAPI Sample</strong>
          </div>
        </section>

        {error && <div className="error-banner">{error}</div>}

        <section className="graph-section">
          <div className="graph-heading">
            <div>
              <h3>Global Supply Chain Graph</h3>
              <p>Graph data retrieved from the AtmoGraph API</p>
            </div>

            <span className="live-label">{nodes.length} NODES</span>
          </div>

          <div className="graph-canvas">
            {loading ? (
              <p className="loading-message">Loading supply-chain graph...</p>
            ) : !error ? (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                fitView
                fitViewOptions={{ padding: 0.2 }}
                minZoom={0.2}
                maxZoom={2}
                nodesConnectable={false}
                onNodeClick={(_, node) =>
                  setSelectedNode(node.data.details)
                }
              >
                <Background color="#334155" gap={20} />
                <Controls />
                <MiniMap
                  nodeColor={(node) =>
                    node.style?.borderColor || "#64748b"
                  }
                  maskColor="rgba(15, 23, 42, 0.7)"
                />
              </ReactFlow>
            ) : (
              <p className="loading-message">
                Graph unavailable.
              </p>
            )}
          </div>

          <div className="legend">
            <span>🔵 Supplier</span>
            <span>🟣 Port</span>
            <span>🟢 Factory</span>
            <span>🟡 Warehouse</span>
            <span>🔴 Customer</span>
          </div>
        </section>

        {selectedNode && (
          <section className="details-panel">
            <div className="details-heading">
              <h3>Node Details</h3>
              <button onClick={() => setSelectedNode(null)}>
                Close
              </button>
            </div>

            <p><strong>Name:</strong> {selectedNode.name}</p>
            <p><strong>ID:</strong> {selectedNode.id}</p>
            <p><strong>Type:</strong> {selectedNode.type}</p>
            <p><strong>Location:</strong> {selectedNode.location}</p>
            <p><strong>Status:</strong> {selectedNode.status}</p>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
