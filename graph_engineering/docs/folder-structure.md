# Graph Engineering Project Structure

This directory contains the Graph Engineering module for the AtmoGraph project.

## 1. Directory Structure

graph_engineering/
├── data/
│   ├── raw/
│   └── processed/
├── cypher/
├── src/
│   └── neo4j_connection.py
├── tests/
├── docs/
│   ├── folder-structure.md
│   └── setup.md
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md

## 2. Directory Guide

- `data/raw/` – Stores original supply-chain datasets before processing.
- `data/processed/` – Stores cleaned and transformed datasets.
- `cypher/` – Contains Neo4j Cypher scripts and queries.
- `src/` – Contains Python source code for graph ingestion and database operations.
- `tests/` – Contains tests for graph creation, data ingestion and queries.
- `docs/` – Contains technical documentation and setup instructions.
- `requirements.txt` – Lists the Python dependencies required by the project.
- `.gitignore` – Specifies files and directories that Git should not track.
- `README.md` – Provides an overview of the Graph Engineering module.
- `.env.example`: Template containing the required Neo4j configuration variables.
- `src/neo4j_connection.py`: Establishes and verifies the Python connection to Neo4j.
- `docs/setup.md`: Explains environment configuration, dependency installation, and database connection setup.

### Security Note

The actual `.env` file contains local database credentials and is excluded from version control.

## 3. Initial Scope

The first prototype will establish a Neo4j supply-chain graph schema, create sample entities and relationships, and demonstrate basic graph queries.

Planned initial entity types include Supplier, Port and Factory. Relationship types and properties will be agreed with the project team before integration.