
import json
from collections import Counter
from pathlib import Path

from neo4j import GraphDatabase

from neo4j_connection import URI, USERNAME, PASSWORD, DATABASE


# Locate Graph Engineering directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Actual Neo4j node labels and their unique ID properties
NODE_ID_PROPERTIES = {
    "Mineral": "mineral_id",
    "Country": "country_id",
    "ImportSourceRecord": "record_id",
    "DisruptionEvent": "event_id",
}

# Actual node types supported by AtmoGraph
NODE_LABELS = list(NODE_ID_PROPERTIES.keys())


# Retrieve actual nodes from Neo4j
NODES_QUERY = """
MATCH (n)
WHERE any(label IN labels(n) WHERE label IN $node_labels)
RETURN labels(n) AS labels,
       properties(n) AS properties
"""


# Retrieve actual relationships and their endpoints
EDGES_QUERY = """
MATCH (source)-[r]->(target)
WHERE any(label IN labels(source) WHERE label IN $node_labels)
  AND any(label IN labels(target) WHERE label IN $node_labels)
RETURN labels(source) AS source_labels,
       properties(source) AS source_properties,
       type(r) AS relationship_type,
       properties(r) AS relationship_properties,
       labels(target) AS target_labels,
       properties(target) AS target_properties
"""


def json_safe(value):
    """Convert Neo4j values into JSON-compatible values."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {
            str(key): json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]

    # Handle Neo4j temporal values
    if hasattr(value, "iso_format"):
        return value.iso_format()

    if hasattr(value, "to_native"):
        return json_safe(value.to_native())

    return str(value)


def get_node_label(labels):
    """Identify the AtmoGraph label from a Neo4j node."""

    for label in NODE_LABELS:
        if label in labels:
            return label

    raise ValueError(
        f"Unsupported Neo4j node labels: {labels}"
    )


def get_node_identity(labels, properties):
    """Get the original business ID of a Neo4j node."""

    label = get_node_label(labels)
    id_property = NODE_ID_PROPERTIES[label]

    node_id = properties.get(id_property)

    if node_id is None:
        raise ValueError(
            f"Missing {id_property} for {label} node"
        )

    return label, str(node_id)


def get_display_name(label, properties, node_id):
    """Get a useful display name without inventing data."""

    name_fields = [
        "name",
        "mineral_name",
        "country_name",
        "mineral",
        "title",
        "headline",
        "event_title",
        "record_id",
        "event_id",
    ]

    for field in name_fields:
        value = properties.get(field)

        if value is not None and str(value).strip():
            return str(value)

    return node_id


def retrieve_graph():
    """
    Retrieve actual AtmoGraph nodes and relationships
    and convert them into the frontend JSON structure.
    """

    if not all([URI, USERNAME, PASSWORD]):
        raise ValueError(
            "Missing Neo4j configuration in graph_engineering/.env"
        )

    # Connect using the existing Neo4j configuration
    with GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD)
    ) as driver:

        driver.verify_connectivity()

        with driver.session(database=DATABASE) as session:

            # Retrieve both nodes and relationships
            node_result = session.run(
                NODES_QUERY,
                node_labels=NODE_LABELS
            )

            node_records = list(node_result)

            edge_result = session.run(
                EDGES_QUERY,
                node_labels=NODE_LABELS
            )

            edge_records = list(edge_result)

    # First collect actual node identities
    raw_nodes = []

    for record in node_records:
        labels = record["labels"]
        properties = dict(record["properties"])

        label, original_id = get_node_identity(
            labels,
            properties
        )

        raw_nodes.append({
            "label": label,
            "original_id": original_id,
            "properties": properties,
        })

    # Check whether business IDs are globally unique
    id_counts = Counter(
        node["original_id"] for node in raw_nodes
    )

    nodes = []
    node_id_lookup = {}

    for node in raw_nodes:

        label = node["label"]
        original_id = node["original_id"]
        properties = node["properties"]

        # Use original IDs unless a collision exists
        if id_counts[original_id] > 1:
            frontend_id = f"{label}:{original_id}"
        else:
            frontend_id = original_id

        node_id_lookup[(label, original_id)] = frontend_id

        name = get_display_name(
            label,
            properties,
            original_id
        )

        location = properties.get("location")

        # A Country node represents a geographic location
        if location is None and label == "Country":
            location = properties.get("name") or name

        nodes.append({
            "id": frontend_id,
            "node_id": original_id,
            "name": name,
            "type": label,
            "location": json_safe(location),
            "status": json_safe(properties.get("status")),
            "properties": json_safe(properties),
        })

    # Sort nodes for consistent output
    nodes.sort(
        key=lambda node: (node["type"], node["id"])
    )

    # Convert actual Neo4j relationships into frontend edges
    raw_edges = []

    for record in edge_records:

        source_label, source_id = get_node_identity(
            record["source_labels"],
            dict(record["source_properties"])
        )

        target_label, target_id = get_node_identity(
            record["target_labels"],
            dict(record["target_properties"])
        )

        source_key = (source_label, source_id)
        target_key = (target_label, target_id)

        if source_key not in node_id_lookup:
            raise ValueError(
                f"Source node missing from export: {source_key}"
            )

        if target_key not in node_id_lookup:
            raise ValueError(
                f"Target node missing from export: {target_key}"
            )

        raw_edges.append({
            "source": node_id_lookup[source_key],
            "target": node_id_lookup[target_key],
            "type": record["relationship_type"],
            "properties": json_safe(
                dict(record["relationship_properties"])
            ),
        })

    # Sort edges to make the generated output reproducible
    raw_edges.sort(
        key=lambda edge: (
            edge["source"],
            edge["type"],
            edge["target"],
        )
    )

    edges = []

    for index, edge in enumerate(raw_edges):

        edges.append({
            "id": f"edge-{index}",
            "source": edge["source"],
            "target": edge["target"],
            "type": edge["type"],
            "properties": edge["properties"],
        })

    # Validate relationship endpoints
    exported_node_ids = {
        node["id"] for node in nodes
    }

    for edge in edges:

        if edge["source"] not in exported_node_ids:
            raise ValueError(
                f"Invalid edge source: {edge['source']}"
            )

        if edge["target"] not in exported_node_ids:
            raise ValueError(
                f"Invalid edge target: {edge['target']}"
            )

    # Build final frontend response
    graph_data = {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "data_source": "Neo4j",
            "database": DATABASE,
        }
    }

    return graph_data


def main():

    print("Connecting to AtmoGraph Neo4j database...")

    graph_data = retrieve_graph()

    # Save actual JSON response for Member 4
    output_dir = (
        PROJECT_ROOT
        / "data"
        / "exports"
        / "frontend"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = output_dir / "graph.json"

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            graph_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    # Display validation summary
    print("\nGRAPH RETRIEVAL SUCCESSFUL")

    print(
        "Total nodes:",
        graph_data["metadata"]["total_nodes"]
    )

    print(
        "Total relationships:",
        graph_data["metadata"]["total_edges"]
    )

    print("\nNode types:")

    for label in NODE_LABELS:
        count = sum(
            node["type"] == label
            for node in graph_data["nodes"]
        )

        print(f"{label}: {count}")

    print("\nRelationship types:")

    relationship_counts = Counter(
        edge["type"] for edge in graph_data["edges"]
    )

    for relationship, count in sorted(
        relationship_counts.items()
    ):
        print(f"{relationship}: {count}")

    print("\nJSON validation: PASSED")
    print("JSON saved to:", output_file)


if __name__ == "__main__":
    main()
