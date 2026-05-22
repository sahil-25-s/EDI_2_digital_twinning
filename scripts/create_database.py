"""
Create the PostgreSQL database named in DATABASE_URL (if it does not exist).

Usage (from project root, after setting DATABASE_URL in env_files/.env):
    python scripts/create_database.py

Requires: psycopg2-binary, a running PostgreSQL server, and credentials with permission to CREATE DATABASE.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlparse

# Load env_files/.env
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

env_path = os.path.join(ROOT, "env_files", ".env")
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("Install psycopg2-binary: pip install psycopg2-binary")
    sys.exit(1)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("Set DATABASE_URL in env_files/.env first.")
    print("Example: postgresql://postgres:yourpassword@localhost:5432/edi_digital_twin")
    sys.exit(1)

parsed = urlparse(DATABASE_URL)
db_name = (parsed.path or "").lstrip("/")
if not db_name:
    print("DATABASE_URL must include a database name.")
    sys.exit(1)

# Connect to maintenance DB (postgres) to create target database
maintenance_path = parsed._replace(path="/postgres").geturl()
if maintenance_path.startswith("postgresql://"):
    maintenance_path = maintenance_path.replace("postgresql://", "", 1)

# urlparse doesn't give psycopg2 conninfo easily; build from parts
conn_kwargs = {
    "host": parsed.hostname or "localhost",
    "port": parsed.port or 5432,
    "user": parsed.username or "postgres",
    "password": parsed.password or "",
    "dbname": "postgres",
}

print(f"Connecting to PostgreSQL at {conn_kwargs['host']}:{conn_kwargs['port']} as {conn_kwargs['user']}...")
conn = psycopg2.connect(**conn_kwargs)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
exists = cur.fetchone()
if exists:
    print(f"Database '{db_name}' already exists.")
else:
    cur.execute(f'CREATE DATABASE "{db_name}"')
    print(f"Created database '{db_name}'.")
cur.close()
conn.close()
print("Done. Next: flask db upgrade")
