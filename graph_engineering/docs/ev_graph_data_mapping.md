# EV Mineral Graph Data Mapping

## 1. Project Scope

AtmoGraph has shifted to the EV battery critical-minerals supply chain.

The current dataset covers five minerals:
- Lithium
- Nickel
- Cobalt
- Manganese
- Graphite

The data comes from USGS Mineral Commodity Summaries 2026.

This document describes the proposed mapping from processed CSV files
to Neo4j graph entities. It is a design proposal, not an implemented schema.

## 2. Input Datasets

### ev_minerals.csv

Contains one record for each of the five minerals.

Proposed graph mapping:
- Create one Mineral node per mineral.
- Store production, consumption and import reliance information as properties.
- Preserve the reporting year and measurement units.
- Keep source information for traceability.

### mineral_import_sources.csv

Contains import-source information for each mineral.

Important fields:
- Mineral
- Importing_Country
- Source_Country
- Source_Category
- Import_Share_Percent
- Net_Import_Reliance_2025
- Data_Period

Proposed graph mapping:
- Represent importing and source countries as Country nodes.
- Preserve each mineral's import-source record.
- Connect the record to its importing country, source country and mineral.
- Keep import share and reporting period with the record.

The Other category is an aggregate category, not a real country.
Do not create a Country node named Other.

### mineral_applications.csv

Contains the primary applications of each mineral.

Initial mapping:
- Store Primary_Applications as a property of the Mineral node.
- Consider separate Application nodes only after application names
  have been standardised.

## 3. Proposed Graph Entities

### Country

Represents a country involved in the reported mineral import data.

Example:
Chile

### Mineral

Represents one of the five selected EV battery critical minerals.

Example:
Lithium

### ImportSourceRecord

Represents one reported import-source record.

Possible properties:
- import_share_percent
- net_import_reliance_2025
- source_category
- source_type
- data_period

### DisruptionEvent

A future entity for representing disruption information extracted
by the NLP pipeline.

Its final properties and relationships depend on Member 2's output.

## 4. Important Data Handling Rules

1. Do not treat missing values as zero automatically.
2. Preserve special USGS values such as W, E and >50 until their
   meanings and numeric handling are confirmed.
3. Keep 2021-2024 import-source shares separate from 2025
   net-import-reliance information.
4. Do not confuse the leading production country with the
   primary import-source countries.
5. Preserve the original source and reporting period.
6. Keep original source flags for traceability.

## 5. Graph-to-GNN Handoff

The Graph Engineering module will coordinate with Member 3 to
provide graph data for the PyTorch Geometric pipeline.

Proposed exports:
- graph_nodes.csv
- graph_edges.csv

The node IDs, node features, edge types and edge attributes
must be agreed with Member 3 before finalising the export format.

## 6. Current Implementation Status

Completed:
- Python environment setup.
- Basic Python-to-Neo4j connection.
- Initial DataCo-specific schema creation.
- USGS processed datasets prepared by Member 2.
- Initial dataset inspection.

Pending:
- Final EV graph schema.
- CSV-to-Neo4j ingestion.
- Graph retrieval queries.
- Disruption event updates.
- Graph export for Member 3.
- Integration testing.

## 7. Next Steps

1. Review and approve the proposed graph structure.
2. Coordinate node and edge feature requirements with Member 3.
3. Implement the EV-specific Neo4j schema.
4. Load processed mineral datasets.
5. Verify graph nodes and relationships.
