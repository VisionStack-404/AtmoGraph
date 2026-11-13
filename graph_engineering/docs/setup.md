# Graph Engineering – Development Environment Setup

This document explains how to prepare the Python development environment for the AtmoGraph Graph Engineering module.

## 1. Prerequisites

Install the following software:

- Python 3.10 or later.
- Visual Studio Code.
- Git.
- Neo4j Desktop for local graph database development.

## 2. Navigate to the Project Directory

Open the terminal in the repository and run:

```bash
cd graph_engineering
```

## 3. Create a Python Virtual Environment

Create an isolated Python environment:

```bash
python -m venv .venv
```

## 4. Activate the Virtual Environment

For Windows Command Prompt:

```bash
.venv\Scripts\activate.bat
```

For Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

## 5. Install Project Dependencies

Install the required Python packages from `requirements.txt`:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The initial dependencies include:

- `pandas` – CSV data processing.
- `neo4j` – Neo4j database connectivity through Python.
- `python-dotenv` – Environment variable management.

## 6. Neo4j Database Setup

Neo4j will be used to store and manage the supply-chain graph.

The database setup will include:

1. Installing and opening Neo4j Desktop.
2. Creating a local Neo4j database.
3. Configuring the database credentials.
4. Connecting the Python application to Neo4j.

The Python database connection and graph implementation will be added during the upcoming development stages.

## 7. Environment and Security

- Keep the virtual environment inside `.venv/`.
- Store database credentials in a local `.env` file when connection configuration is implemented.
- Never commit passwords, credentials or secret configuration files to Git.
- Ensure `.venv/`, `.env` and Python cache files are excluded through `.gitignore`.


## Neo4j Database Configuration and Python Connection

### 1. Start Neo4j

- Open Neo4j Desktop.
- Open the AtmoGraph project.
- Start the local database instance.

### 2. Configure Environment Variables

Copy the example configuration file:

    Copy-Item .env.example .env

Open the `.env` file and configure:

    NEO4J_URI=neo4j://127.0.0.1:7687
    NEO4J_USERNAME=neo4j
    NEO4J_PASSWORD=your_local_database_password
    NEO4J_DATABASE=amtograph

Replace the password placeholder with your actual local database password.

### 3. Install Python Dependencies

From the graph_engineering directory, run:

    python -m pip install -r requirements.txt

### 4. Test the Database Connection

Run:

    python src/neo4j_connection.py

Expected output:

    Successfully connected to Neo4j!
    AtmoGraph Connected!

This confirms that the Python application can connect to the configured Neo4j database and execute a test Cypher query.

### 5. Security

- Never commit the actual `.env` file.
- Keep database credentials private.
- Commit `.env.example` with placeholder values.

## 8. Development Notes

All Python dependencies should be maintained in `requirements.txt`.

Developers should activate the virtual environment before installing packages or running project scripts.
