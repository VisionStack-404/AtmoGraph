
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


# --------------------------------------------------
# 1. Project and database configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EVENTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "nlp_events"
    / "disruption_events.json"
)

load_dotenv(PROJECT_ROOT / ".env")

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE", "amtograph")


# --------------------------------------------------
# 2. Manual country-impact verification
# --------------------------------------------------

# Add a pair ONLY after reviewing the original article
# and confirming that the country was actually affected.
#
# Format:
# ("DISRUPTION_NEWS001", "UNITED_STATES")

VERIFIED_COUNTRY_RELATIONSHIPS = {
    # Add manually verified pairs here.
    
    ("DISRUPTION_NEWS001", "UNITED_STATES"),
    ("DISRUPTION_NEWS002", "CHINA"),
    ("DISRUPTION_NEWS003", "UNITED_STATES"),
    ("DISRUPTION_NEWS004", "INDIA"),
    ("DISRUPTION_NEWS005", "DOMINICAN_REPUBLIC"),

}


# --------------------------------------------------
# 3. Helper functions
# --------------------------------------------------

def make_id(name):
    """Generate IDs using existing graph conventions."""

    return re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        name.strip()
    ).strip("_").upper()


def read_json():

    if not EVENTS_FILE.exists():
        raise FileNotFoundError(
            f"Disruption events file not found: {EVENTS_FILE}"
        )

    with EVENTS_FILE.open("r", encoding="utf-8") as file:
        events = json.load(file)

    if not isinstance(events, list):
        raise ValueError("Expected a JSON list of disruption events.")

    return events


# --------------------------------------------------
# 4. Validate NLP event data
# --------------------------------------------------

def validate_events(events):

    required_fields = [
        "event_id",
        "article_id",
        "article_title",
        "source",
        "article_url",
        "publication_date",
        "disruption_type",
        "explicit_entities",
        "inferred_entities",
        "nlp_confidence",
        "disruption_severity",
        "evidence_summary",
        "entity_verification_status",
    ]

    entity_categories = [
        "minerals",
        "countries",
        "ports_or_facilities",
        "companies_or_organizations",
    ]

    valid_impact_statuses = {
        "affected",
        "mentioned_only",
        "uncertain",
    }

    errors = []
    event_ids = set()

    for index, event in enumerate(events, start=1):

        location = f"Event {index}"

        if not isinstance(event, dict):
            errors.append(f"{location}: Invalid event object.")
            continue

        missing = [
            field for field in required_fields
            if field not in event
        ]

        if missing:
            errors.append(
                f"{location}: Missing fields: {missing}"
            )
            continue

        # Stable event ID validation
        article_id = event["article_id"]
        event_id = event["event_id"]

        expected_id = f"DISRUPTION_{article_id}"

        if event_id != expected_id:
            errors.append(
                f"{location}: Event ID does not match article ID."
            )

        if event_id in event_ids:
            errors.append(
                f"{location}: Duplicate event ID {event_id}"
            )

        event_ids.add(event_id)

        if not isinstance(event["disruption_type"], list):
            errors.append(
                f"{location}: disruption_type must be a list."
            )

        if not isinstance(event["evidence_summary"], str):
            errors.append(
                f"{location}: Invalid evidence_summary."
            )

        # Validate confidence and severity.
        for field in ["nlp_confidence", "disruption_severity"]:

            value = event[field]

            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
            ):
                errors.append(
                    f"{location}: {field} must be numeric or None."
                )

        # Validate explicit and inferred entities.
        for section in ["explicit_entities", "inferred_entities"]:

            entities = event[section]

            if not isinstance(entities, dict):
                errors.append(
                    f"{location}: {section} must be an object."
                )
                continue

            for category in entity_categories:

                records = entities.get(category, [])

                if not isinstance(records, list):
                    errors.append(
                        f"{location}: Invalid {section}.{category}"
                    )
                    continue

                for entity in records:

                    if not isinstance(entity, dict):
                        errors.append(
                            f"{location}: Invalid entity in {category}"
                        )
                        continue

                    name = entity.get("name")

                    if not isinstance(name, str) or not name.strip():
                        errors.append(
                            f"{location}: Entity has no valid name."
                        )
                        continue

                    evidence = entity.get("evidence")

                    if not isinstance(evidence, list) or not evidence:
                        errors.append(
                            f"{location}: Missing evidence for {name}"
                        )
                        continue

                    for item in evidence:

                        if not isinstance(item, dict):
                            errors.append(
                                f"{location}: Invalid evidence for {name}"
                            )
                            continue

                        if not isinstance(item.get("text"), str) or not item["text"].strip():
                            errors.append(
                                f"{location}: Empty evidence text for {name}"
                            )

                        if not isinstance(item.get("source_field"), str) or not item["source_field"].strip():
                            errors.append(
                                f"{location}: Missing source field for {name}"
                            )

                    # Validate country impact classification.
                    if section == "explicit_entities" and category == "countries":

                        status = entity.get("impact_status")
                        relationship_eligible = entity.get(
                            "relationship_eligible"
                        )
                        impact_evidence = entity.get("impact_evidence")

                        if status not in valid_impact_statuses:
                            errors.append(
                                f"{location}: Invalid impact status for {name}"
                            )

                        if not isinstance(relationship_eligible, bool):
                            errors.append(
                                f"{location}: Invalid relationship_eligible for {name}"
                            )

                        if not isinstance(impact_evidence, list):
                            errors.append(
                                f"{location}: Invalid impact evidence for {name}"
                            )
                            continue

                        for item in impact_evidence:

                            if not isinstance(item, dict):
                                errors.append(
                                    f"{location}: Invalid impact evidence for {name}"
                                )
                                continue

                            if not isinstance(item.get("text"), str) or not item["text"].strip():
                                errors.append(
                                    f"{location}: Empty impact evidence for {name}"
                                )

                            if not isinstance(item.get("source_field"), str) or not item["source_field"].strip():
                                errors.append(
                                    f"{location}: Missing impact evidence source for {name}"
                                )

                        if relationship_eligible:
                            if status != "affected" or not impact_evidence:
                                errors.append(
                                    f"{location}: Ineligible country flagged for relationship."
                                )

    if errors:
        raise ValueError(
            "\n".join(errors)
        )

    return True


# --------------------------------------------------
# 5. Prepare events and country relationship candidates
# --------------------------------------------------

def prepare_events(events):

    event_rows = []

    for event in events:

        eligible_countries = []
        countries = event["explicit_entities"].get(
            "countries", []
        )

        for country in countries:

            evidence = country.get("impact_evidence") or []

            if (
                country.get("impact_status") == "affected"
                and country.get("relationship_eligible") is True
                and evidence
            ):

                country_id = make_id(country["name"])

                candidate = {
                    "country_id": country_id,
                    "name": country["name"],
                    "impact_status": country["impact_status"],
                    "impact_note": country.get("impact_note"),
                    "impact_evidence_json": json.dumps(
                        evidence,
                        ensure_ascii=False
                    ),
                }

                eligible_countries.append(candidate)

        # Keep only Neo4j-compatible scalar properties
        # and homogeneous lists. Nested JSON is serialized.
        event_properties = {
            "event_id": event["event_id"],
            "article_id": event["article_id"],
            "article_title": event["article_title"],
            "source": event["source"],
            "article_url": event["article_url"],
            "publication_date": event["publication_date"],
            "disruption_type": event["disruption_type"],

            "explicit_entities_json": json.dumps(
                event["explicit_entities"],
                ensure_ascii=False
            ),

            "inferred_entities_json": json.dumps(
                event["inferred_entities"],
                ensure_ascii=False
            ),

            "nlp_confidence": event["nlp_confidence"],
            "disruption_severity": event["disruption_severity"],

            "evidence_summary": event["evidence_summary"],

            "entity_verification_status":
                event["entity_verification_status"],
        }

        # Only manually reviewed pairs are eligible
        # for actual AFFECTS_COUNTRY relationships.
        verified_countries = [
            country
            for country in eligible_countries
            if (
                event["event_id"],
                country["country_id"]
            ) in VERIFIED_COUNTRY_RELATIONSHIPS
        ]

        event_rows.append({
            "event_id": event["event_id"],
            "properties": event_properties,
            "eligible_countries": eligible_countries,
            "verified_countries": verified_countries,
        })

    return event_rows


# --------------------------------------------------
# 6. Neo4j Cypher queries
# --------------------------------------------------

CREATE_DISRUPTION_EVENTS = """
UNWIND $rows AS row

MERGE (e:DisruptionEvent {
    event_id: row.event_id
})

SET e += row.properties
"""


CREATE_COUNTRY_RELATIONSHIPS = """
UNWIND $rows AS row
UNWIND row.verified_countries AS country

MATCH (e:DisruptionEvent {
    event_id: row.event_id
})

MERGE (c:Country {
    country_id: country.country_id
})

ON CREATE SET
    c.name = country.name

MERGE (e)-[r:AFFECTS_COUNTRY]->(c)

SET r.impact_status = country.impact_status,
    r.impact_note = country.impact_note,
    r.impact_evidence_json = country.impact_evidence_json,
    r.verification_status = 'manually_verified'
"""


# --------------------------------------------------
# 7. Neo4j transaction
# --------------------------------------------------

def write_graph(tx, rows):

    # Create or update all event nodes.
    tx.run(
        CREATE_DISRUPTION_EVENTS,
        rows=rows
    ).consume()

    # Create only manually verified country relationships.
    tx.run(
        CREATE_COUNTRY_RELATIONSHIPS,
        rows=rows
    ).consume()


# --------------------------------------------------
# 8. Main ingestion workflow
# --------------------------------------------------

def ingest_disruption_events():

    if not all([URI, USERNAME, PASSWORD]):
        raise ValueError(
            "Neo4j credentials are missing from .env"
        )

    events = read_json()

    print("JSON file loaded successfully.")
    print("Total events:", len(events))

    validate_events(events)

    print("Event validation: PASSED")

    event_rows = prepare_events(events)

    if not event_rows:
        raise ValueError("No disruption events found.")

    total_candidates = sum(
        len(row["eligible_countries"])
        for row in event_rows
    )

    total_verified = sum(
        len(row["verified_countries"])
        for row in event_rows
    )

    print("\nEvent preparation completed.")
    print("Events prepared:", len(event_rows))
    print("NLP relationship candidates:", total_candidates)
    print("Manually verified relationships:", total_verified)

    print("\nCountry relationship candidates:")

    for row in event_rows:

        for country in row["eligible_countries"]:

            verified = (
                country in row["verified_countries"]
            )

            print(
                row["event_id"],
                "->",
                country["country_id"],
                "| Manually verified:",
                verified
            )

    driver = GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD)
    )

    try:
        driver.verify_connectivity()

        print("\nConnected to Neo4j successfully!")

        with driver.session(database=DATABASE) as session:

            session.execute_write(write_graph, event_rows)

            # Verify event node count.
            result = session.run("""
                MATCH (e:DisruptionEvent)
                RETURN count(e) AS total_events,
                       count(DISTINCT e.event_id) AS unique_events
            """)

            record = result.single()

            print("\nEvent ingestion completed successfully!")
            print("Total event nodes:", record["total_events"])
            print("Unique event IDs:", record["unique_events"])

            # Verify country relationship count.
            result = session.run("""
                MATCH (:DisruptionEvent)-[r:AFFECTS_COUNTRY]->(:Country)
                RETURN count(r) AS total_relationships
            """)

            record = result.single()

            print(
                "AFFECTS_COUNTRY relationships:",
                record["total_relationships"]
            )

    finally:
        driver.close()


# --------------------------------------------------
# 9. Script entry point
# --------------------------------------------------

if __name__ == "__main__":
    ingest_disruption_events()
