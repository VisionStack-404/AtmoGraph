# Graph Engineering Project Structure

This directory contains the Graph Engineering module for the AtmoGraph project.

## Directory guide

- `data/raw/` — original supply-chain datasets.
- `data/processed/` — cleaned and transformed datasets.
- `cypher/` — Neo4j Cypher scripts and queries.
- `src/` — Python source code for graph ingestion and database operations.
- `tests/` — tests for graph creation, ingestion, and queries.
- `docs/` — technical notes and module documentation.

## Initial scope

The first prototype will establish a Neo4j supply-chain graph schema, create sample entities and relationships, and demonstrate basic graph queries.

Planned initial entity types include Supplier, Port, and Factory. Relationship types and properties will be agreed with the project team before integration.
