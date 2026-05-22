"""Add users.name column if missing (run if flask db upgrade was not applied)."""

import os
import sys

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

url = os.environ.get("DATABASE_URL")
if not url:
    print("Set DATABASE_URL in env_files/.env")
    sys.exit(1)

from sqlalchemy import create_engine, inspect, text

engine = create_engine(url)
insp = inspect(engine)
if "name" in {c["name"] for c in insp.get_columns("users")}:
    print("Column users.name already exists.")
    sys.exit(0)

with engine.begin() as conn:
    conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(120)"))
    conn.execute(text("UPDATE users SET name = email WHERE name IS NULL"))
    conn.execute(text("ALTER TABLE users ALTER COLUMN name SET NOT NULL"))

print("Added users.name column successfully.")
