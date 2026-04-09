"""Run SQL files against Azure SQL Database."""
import sys
import pyodbc

SERVER = "sql-nasta-poc.database.windows.net"
DATABASE = "NastaDB"
USERNAME = "sqladmin"
PASSWORD = "Nasta1234!"
DRIVER = "{SQL Server}"

conn_str = f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Encrypt=yes;TrustServerCertificate=no"

def run_sql_file(filepath: str):
    print(f"Connecting to {SERVER}/{DATABASE}...")
    conn = pyodbc.connect(conn_str)
    conn.autocommit = True
    cursor = conn.cursor()

    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()

    # Split into individual statements: find lines that end with ;
    # and use those as statement boundaries
    import re
    # Remove comment-only lines
    lines = [l for l in sql.split("\n") if not l.strip().startswith("--")]
    full_sql = "\n".join(lines)
    # Split on semicolons that are followed by a newline or end of string
    raw = re.split(r";\s*(?=\n|$)", full_sql)
    statements = [s.strip() for s in raw if s.strip()]

    print(f"Running {len(statements)} statements from {filepath}...")
    success = 0
    errors = 0
    for i, stmt in enumerate(statements):
        if not stmt or stmt.startswith("--"):
            continue
        try:
            cursor.execute(stmt)
            success += 1
        except pyodbc.Error as e:
            errors += 1
            if i < 5 or errors < 3:  # Show first few errors
                print(f"  Error on statement {i+1}: {e}")

    cursor.close()
    conn.close()
    print(f"Done: {success} succeeded, {errors} failed")

if __name__ == "__main__":
    for f in sys.argv[1:]:
        run_sql_file(f)
