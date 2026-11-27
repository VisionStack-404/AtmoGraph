
import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


# --------------------------------------------------
# 1. Project and database configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPORT_DIR = PROJECT_ROOT / "data" / "exports" / "gnn_handoff"

load_dotenv(PROJECT_ROOT / ".env")

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE", "amtograph")


# --------------------------------------------------
# 2. Neo4j node export query
# --------------------------------------------------

EXPORT_NODES = """
MATCH (n)

WITH
    n,
    CASE
        WHEN n:Mineral THEN 'Mineral'
        WHEN n:Country THEN 'Country'
        WHEN n:ImportSourceRecord THEN 'ImportSourceRecord'
        WHEN n:DisruptionEvent THEN 'DisruptionEvent'
        ELSE null
    END AS node_type,

    CASE
        WHEN n:Mineral THEN n.mineral_id
        WHEN n:Country THEN n.country_id
        WHEN n:ImportSourceRecord THEN n.record_id
        WHEN n:DisruptionEvent THEN n.event_id
        ELSE null
    END AS node_id

RETURN
    node_id,
    node_type,
    properties(n) AS properties

ORDER BY node_type, node_id
"""


# --------------------------------------------------
# 3. Neo4j relationship export query
# --------------------------------------------------

EXPORT_EDGES = """
MATCH (source)-[r]->(target)

WITH
    source,
    r,
    target,

    CASE
        WHEN source:Mineral THEN 'Mineral'
        WHEN source:Country THEN 'Country'
        WHEN source:ImportSourceRecord THEN 'ImportSourceRecord'
        WHEN source:DisruptionEvent THEN 'DisruptionEvent'
        ELSE null
    END AS source_type,

    CASE
        WHEN source:Mineral THEN source.mineral_id
        WHEN source:Country THEN source.country_id
        WHEN source:ImportSourceRecord THEN source.record_id
        WHEN source:DisruptionEvent THEN source.event_id
        ELSE null
    END AS source_id,

    CASE
        WHEN target:Mineral THEN 'Mineral'
        WHEN target:Country THEN 'Country'
        WHEN target:ImportSourceRecord THEN 'ImportSourceRecord'
        WHEN target:DisruptionEvent THEN 'DisruptionEvent'
        ELSE null
    END AS target_type,

    CASE
        WHEN target:Mineral THEN target.mineral_id
        WHEN target:Country THEN target.country_id
        WHEN target:ImportSourceRecord THEN target.record_id
        WHEN target:DisruptionEvent THEN target.event_id
        ELSE null
    END AS target_id

RETURN
    source_id,
    source_type,
    type(r) AS relationship_type,
    target_id,
    target_type,
    properties(r) AS properties

ORDER BY relationship_type, source_type, source_id, target_type, target_id
"""


# --------------------------------------------------
# 4. Read graph data from Neo4j
# --------------------------------------------------

def read_graph(tx):

    nodes = tx.run(EXPORT_NODES).data()
    edges = tx.run(EXPORT_EDGES).data()

    return nodes, edges


# --------------------------------------------------
# 5. Validate exported graph records
# --------------------------------------------------

def validate_graph(nodes, edges):

    if not nodes:
        raise ValueError("No graph nodes found in Neo4j.")

    node_keys = set()

    for node in nodes:

        node_id = node.get("node_id")
        node_type = node.get("node_type")

        if not node_id or not node_type:
            raise ValueError(
                "A node has a missing type or stable ID."
            )

        key = (node_type, str(node_id))

        if key in node_keys:
            raise ValueError(
                f"Duplicate node identity: {key}"
            )

        node_keys.add(key)

    for edge in edges:

        source_key = (
            edge.get("source_type"),
            str(edge.get("source_id"))
        )

        target_key = (
            edge.get("target_type"),
            str(edge.get("target_id"))
        )

        if source_key not in node_keys:
            raise ValueError(
                f"Missing source node for relationship: {source_key}"
            )

        if target_key not in node_keys:
            raise ValueError(
                f"Missing target node for relationship: {target_key}"
            )

        if not edge.get("relationship_type"):
            raise ValueError(
                "Relationship type is missing."
            )

    print("\nGraph export validation: PASSED")
    print("Unique node identities:", len(node_keys))
    print("Valid relationship endpoints:", len(edges))

    return True


# --------------------------------------------------
# 6. Create stable node index mappings
# --------------------------------------------------

def create_node_mapping(nodes):

    global_mapping = {}
    type_mapping = defaultdict(dict)

    node_index = 0

    indexed_nodes = sorted(
        nodes,
        key=lambda row: (
            row["node_type"],
            str(row["node_id"])
        )
    )

    for node in indexed_nodes:

        node_type = node["node_type"]
        node_id = str(node["node_id"])

        global_key = f"{node_type}:{node_id}"

        global_mapping[global_key] = node_index

        type_index = len(type_mapping[node_type])

        type_mapping[node_type][node_id] = type_index

        node_index += 1

    mapping = {
        "global_node_to_index": global_mapping,
        "node_to_index_by_type": dict(type_mapping),
        "total_nodes": node_index
    }

    return mapping


# --------------------------------------------------
# 7. Export nodes to CSV
# --------------------------------------------------

def export_nodes(nodes, mapping):

    output_file = EXPORT_DIR / "graph_nodes.csv"

    global_mapping = mapping["global_node_to_index"]
    type_mapping = mapping["node_to_index_by_type"]

    fields = [
        "global_index",
        "type_index",
        "node_id",
        "node_type",
        "properties_json"
    ]

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()

        for node in nodes:

            node_type = node["node_type"]
            node_id = str(node["node_id"])

            properties = node.get("properties") or {}

            global_key = f"{node_type}:{node_id}"

            writer.writerow({
                "global_index": global_mapping[global_key],
                "type_index": type_mapping[node_type][node_id],
                "node_id": node_id,
                "node_type": node_type,
                "properties_json": json.dumps(
                    properties,
                    ensure_ascii=False,
                    default=str,
                    sort_keys=True
                )
            })

    print("Node export saved:", output_file)


# --------------------------------------------------
# 8. Export relationships to CSV
# --------------------------------------------------

def export_edges(edges, mapping):

    output_file = EXPORT_DIR / "graph_edges.csv"

    global_mapping = mapping["global_node_to_index"]
    type_mapping = mapping["node_to_index_by_type"]

    fields = [
        "source_id",
        "source_type",
        "source_global_index",
        "source_type_index",
        "relationship_type",
        "target_id",
        "target_type",
        "target_global_index",
        "target_type_index",
        "properties_json"
    ]

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()

        for edge in edges:

            source_id = str(edge["source_id"])
            source_type = edge["source_type"]

            target_id = str(edge["target_id"])
            target_type = edge["target_type"]

            source_key = f"{source_type}:{source_id}"
            target_key = f"{target_type}:{target_id}"

            properties = edge.get("properties") or {}

            writer.writerow({
                "source_id": source_id,
                "source_type": source_type,
                "source_global_index": global_mapping[source_key],
                "source_type_index": type_mapping[source_type][source_id],

                "relationship_type": edge["relationship_type"],

                "target_id": target_id,
                "target_type": target_type,
                "target_global_index": global_mapping[target_key],
                "target_type_index": type_mapping[target_type][target_id],

                "properties_json": json.dumps(
                    properties,
                    ensure_ascii=False,
                    default=str,
                    sort_keys=True
                )
            })

    print("Edge export saved:", output_file)


# --------------------------------------------------
# 9. Export node mappings
# --------------------------------------------------

def export_mapping(mapping):

    output_file = EXPORT_DIR / "node_mapping.json"

    with output_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            mapping,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("Node mapping saved:", output_file)


# --------------------------------------------------
# 10. Create export summary and feature inventory
# --------------------------------------------------

def create_export_report(nodes, edges):

    node_counts = Counter(
        node["node_type"] for node in nodes
    )

    edge_counts = Counter(
        edge["relationship_type"] for edge in edges
    )

    node_properties = defaultdict(set)
    edge_properties = defaultdict(set)

    for node in nodes:

        properties = node.get("properties") or {}

        node_properties[node["node_type"]].update(
            properties.keys()
        )

    for edge in edges:

        properties = edge.get("properties") or {}

        edge_properties[edge["relationship_type"]].update(
            properties.keys()
        )

    report = {
        "database": DATABASE,
        "total_nodes": len(nodes),
        "total_relationships": len(edges),
        "node_counts": dict(node_counts),
        "relationship_counts": dict(edge_counts),

        "node_property_inventory": {
            key: sorted(value)
            for key, value in node_properties.items()
        },

        "edge_property_inventory": {
            key: sorted(value)
            for key, value in edge_properties.items()
        },

        "validation": {
            "all_node_ids_present": True,
            "all_relationship_endpoints_exist": True,
            "duplicate_node_identities": 0
        },

        "gnn_readiness": {
            "raw_graph_export": True,
            "numerical_features_engineered": False,
            "training_labels_available": False,
            "model_ready": False
        }
    }

    report_file = EXPORT_DIR / "graph_export_report.json"

    with report_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("Export report saved:", report_file)


# --------------------------------------------------
# 11. Main export workflow
# --------------------------------------------------

def export_graph():

    if not all([URI, USERNAME, PASSWORD]):
        raise ValueError(
            "Neo4j configuration missing from .env"
        )

    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    driver = GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD)
    )

    try:

        driver.verify_connectivity()

        print("Connected to Neo4j successfully!")
        print("Database:", DATABASE)

        with driver.session(database=DATABASE) as session:

            nodes, edges = session.execute_read(read_graph)

        print("\nGraph data retrieved.")
        print("Nodes:", len(nodes))
        print("Relationships:", len(edges))

        # Validate before writing exports.
        validate_graph(nodes, edges)

        # Build stable node-index mappings.
        mapping = create_node_mapping(nodes)

        # Export graph data.
        export_nodes(nodes, mapping)
        export_edges(edges, mapping)
        export_mapping(mapping)

        # Export summary.
        create_export_report(nodes, edges)

        print("\n" + "=" * 55)
        print("ATMOGRAPH GRAPH EXPORT COMPLETED SUCCESSFULLY")
        print("=" * 55)

        print("Total nodes:", len(nodes))
        print("Total relationships:", len(edges))
        print("Output directory:", EXPORT_DIR)

    finally:
        driver.close()


if __name__ == "__main__":
    export_graph()
