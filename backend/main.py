
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="AtmoGraph API")

# Allow the React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve the graph JSON relative to this file's project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

GRAPH_FILE = (
    PROJECT_ROOT
    / "graph_engineering"
    / "data"
    / "exports"
    / "frontend"
    / "graph.json"
)


def load_graph():
    """Load and validate the exported Neo4j graph."""
    if not GRAPH_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Graph file not found: {GRAPH_FILE}",
        )

    try:
        with GRAPH_FILE.open("r", encoding="utf-8") as file:
            graph_data = json.load(file)

        if not isinstance(graph_data.get("nodes"), list):
            raise ValueError("Graph must contain a nodes list.")

        if not isinstance(graph_data.get("edges"), list):
            raise ValueError("Graph must contain an edges list.")

        return graph_data

    except (json.JSONDecodeError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid graph data: {error}",
        )


@app.get("/")
def root():
    return {"message": "AtmoGraph API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/graph")
def get_graph():
    return load_graph()


@app.get("/api/graph/{node_id}")
def get_node(node_id: str):
    graph_data = load_graph()

    for node in graph_data["nodes"]:
        if node.get("id") == node_id or node.get("node_id") == node_id:
            return node

    raise HTTPException(
        status_code=404,
        detail=f"Node '{node_id}' not found",
    )
