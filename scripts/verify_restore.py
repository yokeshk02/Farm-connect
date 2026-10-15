"""Safe restore verification script for FarmConnect PostgreSQL backups.

Restores a custom-format dump into a strictly isolated temporary database:
'farmconnect_restore_test'.
Verifies table counts, schema integrity, extensions, and exclusion constraints,
then cleans up the temporary database.
NEVER restores over or touches 'farmconnect_db'.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

TEMP_TEST_DB = "farmconnect_restore_test"


def find_pg_binary(binary_name: str) -> str:
    """Locate PostgreSQL binary in system PATH or standard installation paths."""
    found = shutil.which(binary_name)
    if found:
        return found
    candidate_dirs = [
        Path(r"C:\Program Files\PostgreSQL\15\bin"),
        Path(r"C:\Program Files\PostgreSQL\16\bin"),
        Path(r"C:\Program Files\PostgreSQL\14\bin"),
    ]
    for d in candidate_dirs:
        bin_path = d / f"{binary_name}.exe"
        if bin_path.exists():
            return str(bin_path)
    raise FileNotFoundError(f"Could not locate '{binary_name}'.")


def run_restore_verification(dump_path: str | Path):
    dump_file = Path(dump_path).resolve()
    if not dump_file.exists():
        raise FileNotFoundError(f"Backup dump file not found: {dump_file}")

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set.")

    parsed = urlparse(db_url)
    prod_db_name = parsed.path.lstrip("/")
    user = parsed.username or "postgres"
    password = parsed.password or ""
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432

    # CRITICAL SAFETY CHECK: Destination cannot be the production/development database
    if TEMP_TEST_DB == prod_db_name:
        raise RuntimeError(
            f"SAFETY ABORT: Temporary verification database name matches production database '{prod_db_name}'!"
        )

    print(f"[*] Validating dump archive: {dump_file.name} ({dump_file.stat().st_size} bytes)")
    print(f"[*] Safe target verification database: '{TEMP_TEST_DB}' on {host}:{port}")
    print("[*] Protected primary database: DO NOT TOUCH")

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    # 1. Connect to default 'postgres' database to create fresh isolated test database
    admin_conn_str = f"postgresql://{user}:{password}@{host}:{port}/postgres"
    with psycopg.connect(admin_conn_str, autocommit=True) as conn:
        with conn.cursor() as cur:
            # Terminate any stray connections to test DB
            cur.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{TEMP_TEST_DB}' AND pid <> pg_backend_pid();
            """)
            cur.execute(f"DROP DATABASE IF EXISTS {TEMP_TEST_DB};")
            cur.execute(f"CREATE DATABASE {TEMP_TEST_DB};")
            print(f"[+] Created temporary isolated database: '{TEMP_TEST_DB}'")

    try:
        # Pre-create btree_gist extension in test database
        test_conn_str = f"postgresql://{user}:{password}@{host}:{port}/{TEMP_TEST_DB}"
        with psycopg.connect(test_conn_str, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

        # 2. Execute pg_restore
        pg_restore_path = find_pg_binary("pg_restore")
        cmd = [
            pg_restore_path,
            "-h", host,
            "-p", str(port),
            "-U", user,
            "-d", TEMP_TEST_DB,
            "--no-owner",
            "--no-privileges",
            "-v",
            str(dump_file),
        ]

        print("[*] Running pg_restore into temporary database...")
        res = subprocess.run(cmd, env=env, capture_output=True, text=True)
        # Note: pg_restore may return 1 if there are minor warnings (e.g., extension already exists)
        if res.returncode not in (0, 1):
            clean_err = res.stderr.replace(password, "******") if password else res.stderr
            raise RuntimeError(f"pg_restore failed with code {res.returncode}:\n{clean_err}")

        # 3. Verify restored schema and tables in the temporary database
        with psycopg.connect(test_conn_str) as conn:
            with conn.cursor() as cur:
                # Check tables
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
                tables = [r[0] for r in cur.fetchall()]
                print(f"[+] Restored tables found ({len(tables)}): {', '.join(tables)}")

                expected_tables = {
                    "users", "user_locations", "provider_profiles", "machinery",
                    "machinery_photos", "machinery_rates", "machinery_availability",
                    "bookings", "booking_status_history", "contact_enquiries",
                    "otp_verifications", "alembic_version"
                }
                missing = expected_tables - set(tables)
                if missing:
                    raise AssertionError(f"Missing expected tables in restored DB: {missing}")

                # Check alembic migration version
                cur.execute("SELECT version_num FROM alembic_version;")
                alembic_ver = cur.fetchone()[0]
                print(f"[+] Restored Alembic revision: {alembic_ver}")

                # Check btree_gist extension
                cur.execute("SELECT extname FROM pg_extension WHERE extname='btree_gist';")
                assert cur.fetchone() is not None, "btree_gist extension missing in restored database!"
                print("[+] Verified extension: btree_gist installed")

                # Check exclusion constraint on bookings
                cur.execute("""
                    SELECT conname FROM pg_constraint
                    WHERE conname = 'exclude_overlapping_confirmed_bookings';
                """)
                constraint = cur.fetchone()
                assert constraint is not None, "Exclusion constraint 'exclude_overlapping_confirmed_bookings' missing in restored DB!"
                print("[+] Verified constraint: exclude_overlapping_confirmed_bookings active")

        # 4. Compare row counts between original primary DB and temporary restored DB
        print("\n[*] Comparing table row counts between original and restored databases:")
        print(f"{'Table Name':<28} | {'Original Rows':<15} | {'Restored Rows':<15} | {'Status':<10}")
        print("-" * 75)

        orig_conn_str = f"postgresql://{user}:{password}@{host}:{port}/{prod_db_name}"
        with psycopg.connect(orig_conn_str) as orig_conn, psycopg.connect(test_conn_str) as test_conn:
            with orig_conn.cursor() as orig_cur, test_conn.cursor() as test_cur:
                for tbl in sorted(expected_tables):
                    orig_cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                    orig_count = orig_cur.fetchone()[0]

                    test_cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                    test_count = test_cur.fetchone()[0]

                    status = "MATCH" if orig_count == test_count else "MISMATCH"
                    print(f"{tbl:<28} | {orig_count:<15} | {test_count:<15} | {status:<10}")
                    assert orig_count == test_count, f"Row count mismatch for {tbl}: original={orig_count}, restored={test_count}"

        print("-" * 75)
        print("[+] RESTORATION VERIFICATION PASSED: All tables, constraints, extensions, and row counts match 100%.")

    finally:
        # 4. Cleanup: Drop temporary test database
        print(f"[*] Cleaning up temporary verification database '{TEMP_TEST_DB}'...")
        with psycopg.connect(admin_conn_str, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{TEMP_TEST_DB}' AND pid <> pg_backend_pid();
                """)
                cur.execute(f"DROP DATABASE IF EXISTS {TEMP_TEST_DB};")
        print(f"[+] Cleaned up '{TEMP_TEST_DB}'. Verification complete.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_dump = sys.argv[1]
    else:
        # Pick latest dump in backups/
        backup_dir = BASE_DIR / "backups"
        dumps = sorted(backup_dir.glob("*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not dumps:
            print("[-] No dump files found in backups/ directory to verify.", file=sys.stderr)
            sys.exit(1)
        target_dump = dumps[0]

    try:
        run_restore_verification(target_dump)
        print("[+] SUCCESS: Restore verification completed with zero impact on primary database.")
    except Exception as e:
        print(f"[-] ERROR: {e}", file=sys.stderr)
        sys.exit(1)
