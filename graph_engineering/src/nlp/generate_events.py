
import json
import hashlib
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_CSV = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "news"
    / "historical_disruptions_first_5.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "nlp_events"
OUTPUT_JSON = OUTPUT_DIR / "disruption_events.json"


# --------------------------------------------------
# 2. Stable event ID
# --------------------------------------------------

def generate_event_id(article_id):
    """
    Generate the same event ID for the same article every time.
    """
    return f"DISRUPTION_{str(article_id).strip()}"


# --------------------------------------------------
# 3. Evidence helper
# --------------------------------------------------

def make_evidence(text, source_field):
    if pd.isna(text) or not str(text).strip():
        return []

    return [
        {
            "text": str(text).strip(),
            "source_field": source_field
        }
    ]


# --------------------------------------------------
# 4. Split semicolon-separated values
# --------------------------------------------------

def split_entities(value):
    if pd.isna(value) or not str(value).strip():
        return []

    return [
        item.strip()
        for item in str(value).split(";")
        if item.strip()
    ]


# --------------------------------------------------
# 5. Create one event
# --------------------------------------------------

def create_event(row):

    title = str(row["article_title"]).strip()
    description = str(row["description"]).strip()
    location = str(row["location"]).strip()
    ports = str(row["affected_ports_or_facilities"]).strip()


    # Extract countries and assess whether each country was affected.
    country_matches = []

    country_patterns = [
        ("United States", ["United States", "U.S."]),
        ("China", ["China"]),
        ("India", ["India"]),
        ("Dominican Republic", ["Dominican Republic"]),
        ("Australia", ["Australia"])
    ]

    # Evidence-based assessments for the five reviewed articles.
    # Unknown cases default to uncertain, never automatically affected.
    country_impact_rules = {
        "NEWS001": {
            "United States": {
                "status": "affected",
                "note": "The disruption occurred at U.S. West Coast ports."
            }
        },
        "NEWS002": {
            "China": {
                "status": "affected",
                "note": "The explosion at Tianjin disrupted port operations."
            },
            "Australia": {
                "status": "mentioned_only",
                "note": "Shipments from Australia are mentioned, but the description does not establish a disruption in Australia."
            }
        },
        "NEWS003": {
            "United States": {
                "status": "affected",
                "note": "The disruption affected cargo movements and import logistics in the United States."
            }
        },
        "NEWS004": {
            "India": {
                "status": "affected",
                "note": "The cyberattack disrupted operations at the JNPT terminal in India."
            }
        },
        "NEWS005": {
            "Dominican Republic": {
                "status": "affected",
                "note": "Ports in the Dominican Republic were shut or prepared for closure ahead of Hurricane Maria."
            }
        }
    }

    article_id = str(row["article_id"]).strip()

    for country, patterns in country_patterns:
        evidence = []

        for pattern in patterns:
            for field_name, field_text in [
                ("article_title", title),
                ("description", description),
                ("location", location)
            ]:
                if pattern.lower() in field_text.lower():
                    evidence.extend(
                        make_evidence(pattern, field_name)
                    )

        if evidence:
            assessment = country_impact_rules.get(
                article_id, {}
            ).get(country, {})

            impact_status = assessment.get(
                "status", "uncertain"
            )

            impact_evidence = []

            if impact_status == "affected":
                impact_evidence = make_evidence(
                    description,
                    "description"
                )

            country_matches.append({
                "name": country,
                "evidence": evidence,
                "impact_status": impact_status,
                "impact_evidence": impact_evidence,
                "impact_note": assessment.get(
                    "note",
                    "Insufficient evidence to determine country impact."
                ),
                "relationship_eligible": (
                    impact_status == "affected"
                    and bool(impact_evidence)
                )
            })


    # Extract listed organizations from source metadata.
    companies = []

    for company in split_entities(row["affected_companies"]):
        companies.append({
            "name": company,
            "evidence": make_evidence(
                company,
                "affected_companies"
            ),
            "verification": "Pending full article verification"
        })


    # Extract individual ports/facilities.
    port_entities = []

    known_ports = [
        "U.S. West Coast ports",
        "Tianjin Port",
        "Port of Long Beach",
        "Port of Oakland",
        "Jawaharlal Nehru Port (JNPT)",
        "Gujarat Pipavav Port",
        "La Romana",
        "Samana",
        "Arroyo Barril",
        "Puerto Plata",
        "Manzanillo",
        "San Souci",
        "Haina"
    ]

    for port_name in known_ports:
        if port_name.lower() in ports.lower():
            port_entities.append({
                "name": port_name,
                "evidence": make_evidence(
                    port_name,
                    "affected_ports_or_facilities"
                )
            })

    disruption_types = split_entities(row["disruption_type"])


    return {
        "event_id": generate_event_id(row["article_id"]),
        "article_id": str(row["article_id"]).strip(),
        "article_title": title,
        "source": str(row["source"]).strip(),
        "article_url": str(row["article_link"]).strip(),
        "publication_date": str(row["article_date"]).strip(),

        "disruption_type": disruption_types,

        "explicit_entities": {
            "minerals": [],
            "countries": country_matches,
            "ports_or_facilities": port_entities,
            "companies_or_organizations": companies
        },

        "inferred_entities": {
            "minerals": [],
            "countries": [],
            "ports_or_facilities": [],
            "companies_or_organizations": []
        },

        "nlp_confidence": None,
        "disruption_severity": None,

        "evidence_summary": description,

        "entity_verification_status": str(
            row["entity_verification_status"]
        ).strip()
    }


# --------------------------------------------------
# 6. Main execution
# --------------------------------------------------

def main():

    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {INPUT_CSV}"
        )

    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")

    events = [
        create_event(row)
        for _, row in df.iterrows()
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
        json.dump(events, file, indent=4, ensure_ascii=False)

    print("NLP event generation completed.")
    print(f"Articles processed: {len(events)}")
    print(f"Output file: {OUTPUT_JSON}")

    print("\nGenerated event IDs:")
    for event in events:
        print(event["event_id"])


if __name__ == "__main__":
    main()
