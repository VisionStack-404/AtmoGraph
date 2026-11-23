
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AtmoGraph API",
    description="Supply Chain Ripple Effect Predictor",
    version="1.0.0"
)

# Allow the React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample supply-chain nodes
nodes = [
    {"id": "s1", "name": "Shanghai Supplier", "type": "Supplier",
     "location": "Shanghai, China", "status": "Operational"},
    {"id": "s2", "name": "Tokyo Supplier", "type": "Supplier",
     "location": "Tokyo, Japan", "status": "Operational"},
    {"id": "p1", "name": "Singapore Port", "type": "Port",
     "location": "Singapore", "status": "Operational"},
    {"id": "p2", "name": "Hamburg Port", "type": "Port",
     "location": "Hamburg, Germany", "status": "Operational"},
    {"id": "f1", "name": "Berlin Factory", "type": "Factory",
     "location": "Berlin, Germany", "status": "Operational"},
    {"id": "f2", "name": "Munich Factory", "type": "Factory",
     "location": "Munich, Germany", "status": "Operational"},
    {"id": "w1", "name": "Frankfurt Warehouse", "type": "Warehouse",
     "location": "Frankfurt, Germany", "status": "Operational"},
    {"id": "w2", "name": "Paris Warehouse", "type": "Warehouse",
     "location": "Paris, France", "status": "Operational"},
    {"id": "c1", "name": "London Retailer", "type": "Customer",
     "location": "London, UK", "status": "Operational"},
    {"id": "c2", "name": "New York Retailer", "type": "Customer",
     "location": "New York, USA", "status": "Operational"},
]

# Supply-chain connections
edges = [
    {"id": "e1", "source": "s1", "target": "p1"},
    {"id": "e2", "source": "s1", "target": "p2"},
    {"id": "e3", "source": "s2", "target": "p1"},
    {"id": "e4", "source": "s2", "target": "p2"},
    {"id": "e5", "source": "p1", "target": "f1"},
    {"id": "e6", "source": "p2", "target": "f2"},
    {"id": "e7", "source": "f1", "target": "w1"},
    {"id": "e8", "source": "f2", "target": "w2"},
    {"id": "e9", "source": "w1", "target": "c1"},
    {"id": "e10", "source": "w2", "target": "c2"},
]


@app.get("/")
def home():
    return {
        "message": "Welcome to AtmoGraph API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "AtmoGraph Backend"
    }


@app.get("/api/graph")
def get_graph():
    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "data_source": "sample_data"
        }
    }


@app.get("/api/graph/{node_id}")
def get_node(node_id: str):
    for node in nodes:
        if node["id"] == node_id:
            return node

    return {"error": "Node not found"}
