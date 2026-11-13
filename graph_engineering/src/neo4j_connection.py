import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


# Locate the Graph Engineering directory
BASE_DIR = Path(__file__).resolve().parents[1]

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Database configuration
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE", "amtograph")


def connect_to_neo4j():

    if not all([URI, USERNAME, PASSWORD]):
        raise ValueError("Missing Neo4j configuration in .env")

    try:
        with GraphDatabase.driver(
            URI,
            auth=(USERNAME, PASSWORD)
        ) as driver:

            # Verify database connection
            driver.verify_connectivity()

            print("Successfully connected to Neo4j!")

            # Execute a test query
            with driver.session(database=DATABASE) as session:

                result = session.run(
                    "RETURN 'AtmoGraph Connected!' AS message"
                )

                record = result.single()

                print(record["message"])

    except Exception as error:
        print("Connection failed:", error)


if __name__ == "__main__":
    connect_to_neo4j()