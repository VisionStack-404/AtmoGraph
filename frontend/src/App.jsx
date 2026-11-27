
import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";

import {
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";
import "./index.css";

const API_URL = "http://127.0.0.1:8000/api/graph";

const colors = {
  Country: "#38bdf8",
  Mineral: "#a78bfa",
  ImportSourceRecord: "#34d399",
  DisruptionEvent: "#fb7185",
};

const categoryOptions = [
  { label: "All Categories", value: "All" },
  { label: "Countries", value: "Country" },
  { label: "Minerals", value: "Mineral" },
  { label: "Import Records", value: "ImportSourceRecord" },
  { label: "Disruption Events", value: "DisruptionEvent" },
];

const getNodePosition = (type, index) => {
  const layouts = {
    DisruptionEvent: { x: 0, columns: 2 },
    Country: { x: 450, columns: 2 },
    ImportSourceRecord: { x: 1000, columns: 3 },
    Mineral: { x: 1750, columns: 2 },
  };

  const layout = layouts[type] || { x: 2200, columns: 2 };

  return {
    x: layout.x + (index % layout.columns) * 220,
    y: Math.floor(index / layout.columns) * 160,
  };
};

// All graph and dashboard logic lives inside this component.
function GraphDashboard() {
  const { fitView, setViewport, zoomIn, zoomOut } = useReactFlow();

  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

  // Initial graph loading and refresh
  const fetchGraph = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      const response = await axios.get(API_URL);

      const categoryCounters = {
        Country: 0,
        Mineral: 0,
        ImportSourceRecord: 0,
        DisruptionEvent: 0,
      };

      const graphNodes = response.data.nodes.map((item) => {
        const color = colors[item.type] || "#64748b";

        const index = categoryCounters[item.type] ?? 0;
        categoryCounters[item.type] = index + 1;

        const nodeLabel =
          item.type === "ImportSourceRecord"
            ? `Import Record · ${String(item.id).slice(0, 6)}`
            : `${item.name}\n${item.type}`;

        return {
          id: item.id,
          position: getNodePosition(item.type, index),

          data: {
            label: nodeLabel,
            details: item,
          },

          style: {
            width: 190,
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

        data: {
          relationshipType: edge.type,
          properties: edge.properties,
        },

        animated: true,

        style: {
          stroke: "#64748b",
          strokeWidth: 1.5,
          opacity: 0.65,
        },

        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: "#64748b",
        },
      }));

      setNodes(graphNodes);
      setEdges(graphEdges);

      // Preserve selected node if it still exists
      setSelectedNode((currentSelectedNode) => {
        if (!currentSelectedNode) return null;

        const updatedNode = graphNodes.find(
          (node) => node.id === currentSelectedNode.id
        );

        return updatedNode ? updatedNode.data.details : null;
      });

    } catch (err) {
      console.error("Graph API error:", err);

      setError(
        "Unable to load graph data. Check whether the FastAPI backend is running."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  // Refresh and reset graph filters
  const handleRefresh = async () => {
    setSelectedCategory("All");
    setSelectedNode(null);
    setSearchQuery("");

    await fetchGraph(true);
  };

  // Step 12: Fit the complete graph into the canvas
  const handleFitView = () => {
    fitView({
      padding: 0.2,
      duration: 700,
      minZoom: 0.1,
      maxZoom: 1.5,
    });
  };

  // Step 12: Reset to initial viewport
  const handleResetView = () => {
    fitView({
      padding: 0.2,
      duration: 700,
      minZoom: 0.1,
      maxZoom: 1.5,
    });
  };

  const categoryCounts = useMemo(() => {
    const counts = {
      All: nodes.length,
      Country: 0,
      Mineral: 0,
      ImportSourceRecord: 0,
      DisruptionEvent: 0,
    };

    nodes.forEach((node) => {
      const type = node.data.details.type;
      if (counts[type] !== undefined) counts[type] += 1;
    });

    return counts;
  }, [nodes]);

  const filteredSearchResults = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    if (!query) return [];

    return nodes
      .filter((node) => {
        const details = node.data.details;

        return (
          String(details.name || "").toLowerCase().includes(query) ||
          String(details.id || "").toLowerCase().includes(query) ||
          String(details.type || "").toLowerCase().includes(query)
        );
      })
      .slice(0, 8);
  }, [nodes, searchQuery]);

  const handleSearchSelect = (node) => {
    setSelectedCategory("All");
    setSelectedNode(node.data.details);
    setSearchQuery("");
  };

  const displayNodes = nodes.map((node) => {
    const isSelected = node.id === selectedNode?.id;

    const isConnected = selectedNode
      ? edges.some(
          (edge) =>
            (edge.source === selectedNode.id && edge.target === node.id) ||
            (edge.target === selectedNode.id && edge.source === node.id)
        )
      : false;

    const matchesCategory =
      selectedCategory === "All" ||
      node.data.details.type === selectedCategory;

    let opacity = 1;

    if (selectedNode) {
      opacity = isSelected || isConnected ? 1 : 0.18;
    } else if (selectedCategory !== "All") {
      opacity = matchesCategory ? 1 : 0.12;
    }

    return {
      ...node,
      style: {
        ...node.style,
        opacity,
        borderColor: isSelected ? "#facc15" : node.style.borderColor,
        borderWidth: isSelected ? 3 : 1,
        boxShadow: isSelected
          ? "0 0 18px rgba(250, 204, 21, 0.65)"
          : "none",
      },
    };
  });

  const displayEdges = edges.map((edge) => {
    const isConnected =
      selectedNode &&
      (edge.source === selectedNode.id ||
        edge.target === selectedNode.id);

    const sourceNode = nodes.find((node) => node.id === edge.source);
    const targetNode = nodes.find((node) => node.id === edge.target);

    const touchesSelectedCategory =
      selectedCategory === "All" ||
      sourceNode?.data.details.type === selectedCategory ||
      targetNode?.data.details.type === selectedCategory;

    let stroke = "#64748b";
    let strokeWidth = 1.5;
    let opacity = 0.65;

    if (selectedNode) {
      stroke = isConnected ? "#facc15" : "#64748b";
      strokeWidth = isConnected ? 3 : 1.5;
      opacity = isConnected ? 1 : 0.08;
    } else if (selectedCategory !== "All") {
      opacity = touchesSelectedCategory ? 0.75 : 0.06;
    }

    return {
      ...edge,
      animated: true,
      style: { ...edge.style, stroke, strokeWidth, opacity },
      markerEnd: {
        ...edge.markerEnd,
        color: isConnected ? "#facc15" : "#64748b",
      },
    };
  });

  const connectedRelationships = selectedNode
    ? edges
        .filter(
          (edge) =>
            edge.source === selectedNode.id ||
            edge.target === selectedNode.id
        )
        .map((edge) => {
          const isOutgoing = edge.source === selectedNode.id;

          const relatedNodeId = isOutgoing ? edge.target : edge.source;

          const relatedNode = nodes.find(
            (node) => node.id === relatedNodeId
          );

          return {
            id: edge.id,
            relatedNodeId,
            relationshipType: edge.data?.relationshipType,
            direction: isOutgoing ? "Outgoing" : "Incoming",
            relatedNodeName:
              relatedNode?.data.details.name || relatedNodeId,
            relatedNodeType:
              relatedNode?.data.details.type || "Unknown",
          };
        })
    : [];

  const handleRelationshipClick = (relatedNodeId) => {
    const relatedNode = nodes.find(
      (node) => node.id === relatedNodeId
    );

    if (relatedNode) {
      setSelectedCategory("All");
      setSelectedNode(relatedNode.data.details);
    }
  };

  const handleRelationshipKeyDown = (event, relatedNodeId) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleRelationshipClick(relatedNodeId);
    }
  };

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>AtmoGraph</h1>
          <p>EV Battery Critical Minerals Supply Dependency Graph</p>
        </div>

        <span className="status">
          {loading
            ? "CONNECTING..."
            : error
            ? "API ERROR"
            : refreshing
            ? "REFRESHING..."
            : "API CONNECTED"}
        </span>
      </header>

      <main className="dashboard">
        <section className="welcome">
          <h2>Critical Minerals Supply Network</h2>
          <p>
            Explore relationships between minerals, countries, import
            records and disruption events using the actual graph data.
          </p>
        </section>

        {/* Search */}
        <section className="search-section">
          <div className="search-heading">
            <h3>Search Graph Nodes</h3>
            <p>Find nodes by name, ID or category.</p>
          </div>

          <div className="search-container">
            <div className="search-input-wrapper">
              <span className="search-icon">⌕</span>

              <input
                type="text"
                className="graph-search-input"
                placeholder="Search India, INDIA, Mineral, DisruptionEvent..."
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                disabled={loading || Boolean(error)}
              />

              {searchQuery && (
                <button
                  type="button"
                  className="clear-search"
                  onClick={() => setSearchQuery("")}
                  aria-label="Clear search"
                >
                  ×
                </button>
              )}
            </div>

            {searchQuery.trim() && (
              <div className="search-results">
                {filteredSearchResults.length > 0 ? (
                  <>
                    <div className="search-results-heading">
                      {filteredSearchResults.length} matching result(s)
                    </div>

                    {filteredSearchResults.map((node) => (
                      <button
                        type="button"
                        key={node.id}
                        className="search-result-item"
                        onClick={() => handleSearchSelect(node)}
                      >
                        <span
                          className="search-result-indicator"
                          style={{
                            background:
                              colors[node.data.details.type] || "#64748b",
                          }}
                        />

                        <span className="search-result-info">
                          <strong>
                            {node.data.details.name || node.id}
                          </strong>
                          <small>
                            {node.id} · {node.data.details.type}
                          </small>
                        </span>

                        <span className="search-result-arrow">→</span>
                      </button>
                    ))}
                  </>
                ) : (
                  <div className="no-search-results">
                    No matching nodes found.
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Category Filters */}
        <section className="category-filter-section">
          <div className="category-filter-heading">
            <div>
              <h3>Filter by Category</h3>
              <p>Focus on a particular type of node in the graph.</p>
            </div>

            <span className="filter-count">
              {selectedCategory === "All"
                ? nodes.length
                : categoryCounts[selectedCategory]} NODES
            </span>
          </div>

          <div className="category-filter-buttons">
            {categoryOptions.map((category) => (
              <button
                type="button"
                key={category.value}
                className={`category-filter-button ${
                  selectedCategory === category.value ? "active" : ""
                }`}
                onClick={() => setSelectedCategory(category.value)}
                disabled={loading || Boolean(error)}
                style={{
                  "--category-color":
                    category.value === "All"
                      ? "#38bdf8"
                      : colors[category.value],
                }}
              >
                <span>{category.label}</span>
                <span className="category-count">
                  {categoryCounts[category.value] ?? 0}
                </span>
              </button>
            ))}
          </div>

          <p className="filter-description">
            {selectedCategory === "All"
              ? "Showing all graph categories."
              : `Highlighting ${
                  categoryOptions.find(
                    (category) => category.value === selectedCategory
                  )?.label
                }. Other nodes remain visible but dimmed.`}
          </p>
        </section>

        {/* Statistics */}
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
            <strong>
              {new Set(
                nodes.map((node) => node.data.details.type)
              ).size}
            </strong>
          </div>

          <div className="stat-card">
            <span>Data Source</span>
            <strong className="small-value">Neo4j</strong>
          </div>
        </section>

        {error && <div className="error-banner">{error}</div>}

        {/* Graph */}
        <section className="graph-section">
          <div className="graph-heading">
            <div>
              <h3>Global Critical Minerals Graph</h3>
              <p>
                Graph data retrieved through the AtmoGraph FastAPI backend
              </p>
            </div>

            <div className="graph-actions">
              <button
                type="button"
                className="refresh-graph-button"
                onClick={handleRefresh}
                disabled={loading || refreshing}
              >
                <span className={refreshing ? "refresh-icon spinning" : "refresh-icon"}>
                  ↻
                </span>
                {refreshing ? "Refreshing..." : "Refresh Graph"}
              </button>

              <span className="live-label">{nodes.length} NODES</span>
            </div>
          </div>

          {/* Step 12: View controls */}
          <div className="graph-view-toolbar">
            <button
              type="button"
              onClick={handleFitView}
              disabled={loading || nodes.length === 0}
            >
              <span>⛶</span> Fit to Screen
            </button>

            <button
              type="button"
              onClick={handleResetView}
              disabled={loading || nodes.length === 0}
            >
              <span>⟲</span> Reset View
            </button>

            <button
              type="button"
              onClick={() => zoomIn({ duration: 250 })}
              disabled={loading || nodes.length === 0}
            >
              + Zoom In
            </button>

            <button
              type="button"
              onClick={() => zoomOut({ duration: 250 })}
              disabled={loading || nodes.length === 0}
            >
              − Zoom Out
            </button>
          </div>

          <div className="graph-canvas">
            {loading ? (
              <p className="loading-message">
                Loading critical minerals graph...
              </p>
            ) : nodes.length > 0 ? (
              <ReactFlow
                nodes={displayNodes}
                edges={displayEdges}
                fitView
                fitViewOptions={{ padding: 0.2 }}
                minZoom={0.1}
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
              <p className="loading-message">Graph unavailable.</p>
            )}
          </div>

          <div className="legend">
            <span>🔵 Country</span>
            <span>🟣 Mineral</span>
            <span>🟢 Import Source Record</span>
            <span>🔴 Disruption Event</span>
          </div>
        </section>

        {/* Node Details */}
        {selectedNode && (
          <section className="details-panel">
            <div className="details-heading">
              <h3>Node Details</h3>
              <button onClick={() => setSelectedNode(null)}>Close</button>
            </div>

            <p><strong>Name:</strong> {selectedNode.name}</p>
            <p><strong>ID:</strong> {selectedNode.id}</p>
            <p><strong>Type:</strong> {selectedNode.type}</p>
            <p>
              <strong>Location:</strong>{" "}
              {selectedNode.location ?? "Not available"}
            </p>
            <p>
              <strong>Status:</strong>{" "}
              {selectedNode.status ?? "Not available"}
            </p>

            <h4>Properties</h4>
            <pre>
              {JSON.stringify(selectedNode.properties, null, 2)}
            </pre>

            <h4>
              Connected Relationships ({connectedRelationships.length})
            </h4>

            {connectedRelationships.length > 0 ? (
              <div className="relationships-list">
                {connectedRelationships.map((relationship) => (
                  <div
                    key={relationship.id}
                    className="relationship-card"
                    onClick={() =>
                      handleRelationshipClick(relationship.relatedNodeId)
                    }
                    onKeyDown={(event) =>
                      handleRelationshipKeyDown(
                        event,
                        relationship.relatedNodeId
                      )
                    }
                    role="button"
                    tabIndex={0}
                    title={`View ${relationship.relatedNodeName}`}
                  >
                    <strong>{relationship.relationshipType}</strong>
                    <p>{relationship.direction} relationship</p>
                    <p>
                      Connected Node: {relationship.relatedNodeName}
                    </p>
                    <p>Category: {relationship.relatedNodeType}</p>
                    <small>Click to view connected node →</small>
                  </div>
                ))}
              </div>
            ) : (
              <p>No connected relationships found.</p>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

// ReactFlowProvider gives GraphDashboard access to useReactFlow()
function App() {
  return (
    <ReactFlowProvider>
      <GraphDashboard />
    </ReactFlowProvider>
  );
}

export default App;
