// 1. Mineral nodes
CREATE CONSTRAINT mineral_id_unique IF NOT EXISTS
FOR (m:Mineral)
REQUIRE m.mineral_id IS UNIQUE;

// 2. Country nodes
CREATE CONSTRAINT country_id_unique IF NOT EXISTS
FOR (c:Country)
REQUIRE c.country_id IS UNIQUE;

// 3. Import source records
CREATE CONSTRAINT import_record_id_unique IF NOT EXISTS
FOR (r:ImportSourceRecord)
REQUIRE r.record_id IS UNIQUE;