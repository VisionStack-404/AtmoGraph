import csv
import os
import re
import hashlib
import json
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


# --------------------------------------------------
# 1. Project and database configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"

load_dotenv(PROJECT_ROOT / ".env")

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE", "amtograph")


# --------------------------------------------------
# 2. Helper functions
# --------------------------------------------------

def read_csv(filename):
    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def clean_value(value):
    """Convert numeric strings to numbers and preserve other values."""

    if value is None:
        return None

    value = value.strip()

    if not value:
        return None

    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value):
        number = float(value)
        return int(number) if number.is_integer() else number

    # Preserve values such as W, >50 and --
    return value


def make_id(name):
    """Create a consistent ID from a name."""

    return re.sub(r"[^A-Za-z0-9]+", "_", name.strip()).strip("_").upper()


# --------------------------------------------------
# 3. Prepare Mineral nodes
# --------------------------------------------------

def prepare_minerals(rows):

    minerals = []

    for row in rows:
        name = row["Mineral_Group"].strip()

        minerals.append({
            "mineral_id": make_id(name),
            "name": name,
            "source": clean_value(row.get("Source")),
            "year": clean_value(row.get("Year")),
            "units": clean_value(row.get("Units")),
            "critical_mineral": clean_value(row.get("Critical_mineral")),
            "primary_production": clean_value(row.get("Primary_prod")),
            "secondary_production": clean_value(row.get("Secondary_prod")),
            "production_notes": clean_value(row.get("Prod_notes")),
            "apparent_consumption": clean_value(row.get("Apparent_Consumption")),
            "consumption_notes": clean_value(row.get("Consumption_Notes")),
            "net_import_reliance": clean_value(row.get("Net_Import_Reliance")),
            "primary_import_sources_2021_24": clean_value(
                row.get("Primary_import_sources_2021-24")
            ),
            "import_source_notes": clean_value(row.get("Import_source_notes")),
            "leading_source_country": clean_value(row.get("Leading_source_country")),
            "leading_country_production": clean_value(row.get("Leading_country_prod")),
            "leading_source_percent_world": clean_value(
                row.get("Leading_source_precent_world")
            ),
            "world_total_production": clean_value(row.get("World_total_prod")),
            "world_production_notes": clean_value(row.get("World_prod_notes")),
        })

    return minerals


# --------------------------------------------------
# 4. Prepare Country nodes and import records
# --------------------------------------------------

def prepare_import_data(rows, minerals):

    mineral_ids = {m["mineral_id"] for m in minerals}
    countries = {}
    import_records = []

    for row in rows:
        mineral_id = make_id(row["Mineral"].strip())

        if mineral_id not in mineral_ids:
            raise ValueError(f"Unknown mineral in import data: {row['Mineral']}")

        importer = row["Importing_Country"].strip()

        if not importer:
            raise ValueError("Importing country is missing.")

        importer_id = make_id(importer)
        countries[importer_id] = importer

        source_country = (row.get("Source_Country") or "").strip()

        is_aggregate = (
            (row.get("Source_Type") or "").strip().lower() == "aggregate_other"
            or (row.get("Source_Category") or "").strip().lower() == "other"
        )

        if is_aggregate:
            source_country = ""

        source_country_id = make_id(source_country) if source_country else None

        if source_country_id:
            countries[source_country_id] = source_country

        # A stable ID based on the original row
        row_text = json.dumps(row, sort_keys=True, ensure_ascii=False)
        record_id = hashlib.sha256(row_text.encode("utf-8")).hexdigest()

        import_records.append({
            "record_id": record_id,
            "mineral_id": mineral_id,
            "importing_country_id": importer_id,
            "source_country_id": source_country_id,
            "source_category": clean_value(row.get("Source_Category")),
            "source_type": clean_value(row.get("Source_Type")),
            "import_share_percent": clean_value(row.get("Import_Share_Percent")),
            "net_import_reliance_2025": clean_value(
                row.get("Net_Import_Reliance_2025")
            ),
            "nir_figure3": clean_value(row.get("NIR_Figure3")),
            "critical_mineral_flag": clean_value(row.get("Critical_Mineral_Flag")),
            "data_period": clean_value(row.get("Data_Period")),
        })

    return countries, import_records


# --------------------------------------------------
# 5. Prepare application properties
# --------------------------------------------------

def prepare_applications(rows, minerals):

    mineral_ids = {m["mineral_id"] for m in minerals}
    applications = []

    for row in rows:
        mineral_id = make_id(row["Mineral"].strip())

        if mineral_id not in mineral_ids:
            raise ValueError(f"Unknown mineral in applications: {row['Mineral']}")

        applications.append({
            "mineral_id": mineral_id,
            "application_critical_mineral": clean_value(
                row.get("Critical_Mineral")
            ),
            "primary_applications": clean_value(row.get("Primary_Applications")),
            "category_note": clean_value(row.get("Category_Note")),
            "applications_data_source": clean_value(row.get("Data_Source")),
            "applications_source_file": clean_value(row.get("Source_File")),
        })

    return applications


# --------------------------------------------------
# 6. Neo4j Cypher queries
# --------------------------------------------------

CREATE_MINERALS = """
UNWIND $rows AS row
MERGE (m:Mineral {mineral_id: row.mineral_id})
SET m += row
"""

CREATE_COUNTRIES = """
UNWIND $rows AS row
MERGE (c:Country {country_id: row.country_id})
SET c.name = row.name
"""

CREATE_IMPORT_RECORDS = """
UNWIND $rows AS row

MATCH (importer:Country {country_id: row.importing_country_id})
MATCH (m:Mineral {mineral_id: row.mineral_id})

MERGE (r:ImportSourceRecord {record_id: row.record_id})
SET r += row

MERGE (importer)-[:HAS_IMPORT_RECORD]->(r)
MERGE (r)-[:FOR_MINERAL]->(m)
"""

CREATE_SOURCE_RELATIONSHIPS = """
UNWIND $rows AS row

WITH row
WHERE row.source_country_id IS NOT NULL

MATCH (r:ImportSourceRecord {record_id: row.record_id})
MATCH (c:Country {country_id: row.source_country_id})

MERGE (r)-[:SOURCE_COUNTRY]->(c)
"""

CREATE_LEADING_PRODUCER_RELATIONSHIPS = """
UNWIND $rows AS row

MATCH (c:Country {country_id: row.country_id})
MATCH (m:Mineral {mineral_id: row.mineral_id})

MERGE (c)-[r:LEADING_PRODUCER_FOR]->(m)

SET r.production = row.production,
    r.share_of_world_percent = row.share_of_world_percent,
    r.world_total_production = row.world_total_production,
    r.year = row.year,
    r.units = row.units
"""

UPDATE_APPLICATIONS = """
UNWIND $rows AS row

MATCH (m:Mineral {mineral_id: row.mineral_id})

SET m.application_critical_mineral = row.application_critical_mineral,
    m.primary_applications = row.primary_applications,
    m.category_note = row.category_note,
    m.applications_data_source = row.applications_data_source,
    m.applications_source_file = row.applications_source_file
"""


# --------------------------------------------------
# 7. Main ingestion function
# --------------------------------------------------

def ingest_graph():

    if not all([URI, USERNAME, PASSWORD]):
        raise ValueError("Neo4j credentials are missing from .env")

    mineral_rows = read_csv("ev_minerals.csv")
    import_rows = read_csv("mineral_import_sources.csv")
    application_rows = read_csv("mineral_applications.csv")

    minerals = prepare_minerals(mineral_rows)

    countries, import_records = prepare_import_data(
        import_rows, minerals
    )

    applications = prepare_applications(
        application_rows, minerals
    )

    # Add leading production countries to the Country nodes
    leading_relationships = []

    for mineral in minerals:
        country_name = mineral["leading_source_country"]

        if country_name:
            country_id = make_id(country_name)
            countries[country_id] = country_name

            leading_relationships.append({
                "country_id": country_id,
                "mineral_id": mineral["mineral_id"],
                "production": mineral["leading_country_production"],
                "share_of_world_percent": mineral["leading_source_percent_world"],
                "world_total_production": mineral["world_total_production"],
                "year": mineral["year"],
                "units": mineral["units"],
            })

    country_rows = [
        {"country_id": country_id, "name": name}
        for country_id, name in countries.items()
    ]

    print("CSV files loaded successfully.")
    print("Minerals:", len(minerals))
    print("Countries:", len(country_rows))
    print("Import records:", len(import_records))
    print("Applications:", len(applications))
    print("Leading producer relationships:", len(leading_relationships))

    driver = GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD)
    )

    try:
        driver.verify_connectivity()

        with driver.session(database=DATABASE) as session:

            def write_graph(tx):

                tx.run(CREATE_MINERALS, rows=minerals).consume()

                tx.run(CREATE_COUNTRIES, rows=country_rows).consume()

                tx.run(
                    CREATE_IMPORT_RECORDS,
                    rows=import_records
                ).consume()

                tx.run(
                    CREATE_SOURCE_RELATIONSHIPS,
                    rows=import_records
                ).consume()

                tx.run(
                    CREATE_LEADING_PRODUCER_RELATIONSHIPS,
                    rows=leading_relationships
                ).consume()

                tx.run(
                    UPDATE_APPLICATIONS,
                    rows=applications
                ).consume()

            session.execute_write(write_graph)

            print("\nGraph ingestion completed successfully!")

            print("\nNode counts:")

            result = session.run("""
                MATCH (n)
                UNWIND labels(n) AS label
                RETURN label, count(n) AS total
                ORDER BY label
            """)

            for record in result:
                print(f"{record['label']}: {record['total']}")

            print("\nRelationship counts:")

            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS relationship, count(r) AS total
                ORDER BY relationship
            """)

            for record in result:
                print(f"{record['relationship']}: {record['total']}")

    finally:
        driver.close()


if __name__ == "__main__":
    ingest_graph()