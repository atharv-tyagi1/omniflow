"""
pgvector_setup.py — Run this ONCE after PostgreSQL is installed.
Creates the omniflow database/user and installs pgvector.

Usage:
    python pgvector_setup.py

Requires: psycopg (pip install psycopg[binary])
The postgres superuser password will be prompted.
"""
import subprocess
import sys
import os


PG_BIN_PATHS = [
    r"C:\Program Files\PostgreSQL\17\bin",
    r"C:\Program Files\PostgreSQL\16\bin",
    r"C:\Program Files\PostgreSQL\15\bin",
]

def find_psql():
    for p in PG_BIN_PATHS:
        psql = os.path.join(p, "psql.exe")
        if os.path.exists(psql):
            return p, psql
    return None, None

def run_psql(pg_bin, user, command, db="postgres", password="postgres"):
    env = dict(os.environ, PGPASSWORD=password)
    cmd = [os.path.join(pg_bin, "psql.exe"), "-U", user, "-d", db, "-c", command]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    print("STDOUT:", result.stdout)
    if result.returncode != 0:
        print("STDERR:", result.stderr)
    return result.returncode == 0

pg_bin, psql_path = find_psql()
if not pg_bin:
    print("ERROR: Could not find psql.exe in known PostgreSQL install paths.")
    sys.exit(1)

print(f"Found psql at: {psql_path}")

# Prompt for postgres superuser password
import getpass
pg_password = getpass.getpass("Enter PostgreSQL 'postgres' superuser password (set during install): ")

# Create user
print("\n--- Creating omniflow role ---")
run_psql(pg_bin, "postgres", "CREATE USER omniflow WITH PASSWORD 'omniflow_dev_2024';", password=pg_password)

# Create database
print("\n--- Creating omniflow database ---")
run_psql(pg_bin, "postgres", "CREATE DATABASE omniflow OWNER omniflow;", password=pg_password)

# Grant privileges
print("\n--- Granting privileges ---")
run_psql(pg_bin, "postgres", "GRANT ALL PRIVILEGES ON DATABASE omniflow TO omniflow;", db="omniflow", password=pg_password)

# Install pgvector extension
print("\n--- Installing pgvector extension ---")
ok = run_psql(pg_bin, "postgres", "CREATE EXTENSION IF NOT EXISTS vector;", db="omniflow", password=pg_password)
if ok:
    print("pgvector extension installed successfully!")
else:
    print("NOTE: pgvector may not be bundled with this PostgreSQL install.")
    print("Download pgvector from: https://github.com/pgvector/pgvector/releases")

# Verify
print("\n--- Verification ---")
run_psql(pg_bin, "postgres", "SELECT version();", db="omniflow", password=pg_password)
run_psql(pg_bin, "postgres", "SELECT extname, extversion FROM pg_extension WHERE extname='vector';", db="omniflow", password=pg_password)

print("\nSetup complete. Run Alembic migrations next.")
