# AtmoGraph – Graph Engineering

## 1. Project Overview

AtmoGraph is a Supply Chain Ripple Effect Predictor. It aims to identify how disruptions in one part of a supply chain can affect connected suppliers, ports, factories and downstream businesses.

## 2. My Role

**Member 1 – Graph Engineer**

Responsible for designing and managing the supply-chain graph using Neo4j.

## 3. Responsibilities

- Set up and manage the Neo4j database.
- Design graph nodes such as Supplier, Port and Factory.
- Create relationships between supply-chain entities.
- Import supply-chain CSV data into Neo4j using Python.
- Develop Cypher queries to retrieve and update graph data.
- Implement risk-update query functions.
- Prepare graph data for GNN integration.

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.10+ | Data processing and integration |
| Neo4j | Graph database |
| Cypher | Graph query language |
| Pandas | CSV data processing |
| Neo4j Python Driver | Connecting Python with Neo4j |
| python-dotenv | Environment configuration |
| Git & GitHub | Version control |
| VS Code | Development environment |

## 5. Project Structure

- `data/raw/` – Original supply-chain datasets.
- `data/processed/` – Cleaned datasets.
- `cypher/` – Neo4j queries.
- `src/` – Python source code.
- `tests/` – Testing scripts.
- `docs/` – Project documentation.
- `requirements.txt` – Python dependencies.

For the detailed directory structure, refer to [folder-structure.md](docs/folder-structure.md).

For environment configuration instructions, refer to [setup.md](docs/setup.md).

## 6. Module Workflow

1. Read supply-chain data from CSV files.
2. Process the data using Python and Pandas.
3. Create nodes and relationships in Neo4j.
4. Retrieve connected entities using Cypher.
5. Update graph information when disruptions occur.
6. Provide graph data to the GNN module.

## 7. Team Integration

- **NLP:** Extracts disruption information from news.
- **Graph Engineering:** Stores and connects supply-chain entities.
- **GNN & ML:** Predicts potential downstream disruptions.
- **Frontend & API:** Displays the graph and prediction results.

## 8. Development Plan

- **Week 1:** Neo4j setup and mock supply-chain graph prototype.
- **Week 2:** CSV data ingestion and graph development.
- **Week 3:** Support GNN integration and graph-based predictions.
- **Week 4:** Testing, documentation and final integration.

## 9. Expected Deliverables

- Running Neo4j database.
- Python script to convert CSV data into graph nodes and relationships.
- Cypher risk-update query functions.

## 10. Development Status

**Current Status:** Initial Graph Engineering setup completed, with a successful Python-to-Neo4j database connection.

### Completed Work

- Created the Graph Engineering project structure.
- Installed and configured Neo4j Desktop.
- Created and started the local Neo4j database.
- Configured Python dependencies.
- Created the environment configuration template (`.env.example`).
- Implemented the Python Neo4j connection script.
- Successfully verified database connectivity using the Neo4j Python Driver.
- Executed a test Cypher query through Python.

### Next Steps

- Design the graph schema for Supplier, Port, and Factory nodes.
- Create sample graph nodes and relationships.
- Develop Python scripts for CSV-to-Neo4j data ingestion.
- Implement Cypher queries for graph retrieval and risk updates.
- Prepare graph data for integration with the GNN module.

The graph schema, data ingestion, and risk-update functionality are still under development.