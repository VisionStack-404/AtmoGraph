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
| Python | Data processing and integration |
| Neo4j | Graph database |
| Cypher | Graph query language |
| Pandas | CSV data processing |
| Git & GitHub | Version control |
| VS Code | Development environment |

## 5. Project Structure
- `data/raw/` – Original datasets
- `data/processed/` – Cleaned datasets
- `cypher/` – Neo4j queries
- `src/` – Python source code
- `tests/` – Testing scripts
- `docs/` – Project documentation

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
Initial project structure created. Neo4j setup and graph implementation are planned.