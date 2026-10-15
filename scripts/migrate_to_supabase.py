"""Safe, idempotent end-to-end migration runner for FarmConnect -> Supabase.

Applies:
1. Connection validation (enforces remote host, sslmode=require, rejects localhost).
2. Safe password handling: supports URI templates with [YOUR-PASSWORD] and percent-encodes
   reserved characters (e.g. @, #, %, :, /, ?) so hostnames are never corrupted.
3. Supports Supabase Session Pooler (port 5432) for IPv4 network compatibility.
4. Schema preflight check (checks public schema emptiness and btree_gist extension).
5. Alembic migration to target head 'aeacc557d85c' with fail-closed engine assertion.
6. Schema verification (checks 12 tables, btree_gist, exclusion constraint).
7. Comprehensive data migration for all application tables from local PostgreSQL (READ-ONLY) -> Supabase.
8. Target verification (row count comparisons, password authentication verification).

Credentials are NEVER logged or displayed.
"""

import os
import sys
import re
import getpass
import urllib.parse
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
import psycopg

# Load local .env for source database connection
load_dotenv(BASE_DIR / ".env")

PASSWORD_PLACEHOLDER_REGEX = re.compile(r"\[YOUR-PASSWORD\]|\[PASSWORD\]|<password>", re.IGNORECASE)


def encode_password(password: str) -> str:
    """Safely percent-encode password for use in PostgreSQL database URLs.
    
    All reserved URI characters including @, :, /, #, ?, %, &, +, [, ] are encoded.
    """
    if not password:
        return ""
    # safe="" ensures that every non-unreserved character is percent-encoded.
    return urllib.parse.quote(password, safe="")


def build_supabase_url(template_or_url: str, password: str | None = None) -> str:
    """Construct a valid Supabase database URL from a template and password.
    
    Supports:
    1. Template containing '[YOUR-PASSWORD]' (case-insensitive), with password provided.
    2. URL without password (e.g. postgresql://user@host:5432/dbname), with password provided.
    3. Complete URL with already-encoded password.
    
    Enforces 'postgresql://' scheme and 'sslmode=require'.
    """
    if not template_or_url or not template_or_url.strip():
        raise ValueError("Database connection URL or template cannot be empty.")

    raw = template_or_url.strip().strip("'\"")
    if raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql://", 1)

    # Check if placeholder is present in the URI
    if PASSWORD_PLACEHOLDER_REGEX.search(raw):
        if not password:
            raise ValueError("Password is required when using a connection template containing [YOUR-PASSWORD].")
        encoded_pw = encode_password(password)
        raw = PASSWORD_PLACEHOLDER_REGEX.sub(encoded_pw, raw, count=1)
    elif password:
        # User passed a URI without placeholder, but provided password separately.
        # Check if URL already has user without password (e.g. postgresql://postgres.ref@host:port/db)
        parsed = urllib.parse.urlsplit(raw)
        if parsed.username and not parsed.password:
            encoded_pw = encode_password(password)
            netloc = f"{parsed.username}:{encoded_pw}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            raw = urllib.parse.urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))

    # Ensure sslmode=require in query params
    parsed = urllib.parse.urlsplit(raw)
    query_params = urllib.parse.parse_qs(parsed.query)
    if "sslmode" not in query_params:
        query_params["sslmode"] = ["require"]
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        raw = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))

    return raw


def mask_url(url: str) -> str:
    """Mask credentials in database URL for safe display and logging.
    
    Guarantees password is NEVER exposed.
    """
    if not url:
        return "<not set>"
    try:
        if PASSWORD_PLACEHOLDER_REGEX.search(url):
            return PASSWORD_PLACEHOLDER_REGEX.sub("******", url)

        parsed = urllib.parse.urlsplit(url)
        netloc = ""
        if parsed.username:
            netloc += parsed.username
            if parsed.password or ":" in parsed.netloc.split("@")[0]:
                netloc += ":******"
            netloc += "@"
        netloc += parsed.hostname or ""
        if parsed.port:
            netloc += f":{parsed.port}"
        return urllib.parse.urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
    except Exception:
        return "postgresql://<sanitized-credentials>@<host>/<db>"


def validate_supabase_url(db_url: str) -> dict:
    """Validate that the target URL is a safe, valid remote Supabase database URL.
    
    Returns a dict with parsed metadata (host, port, username, database, connection_mode).
    Raises RuntimeError or ValueError if invalid or unsafe.
    """
    if not db_url or not db_url.strip():
        raise ValueError("Database connection URL cannot be empty.")

    raw_url = db_url.strip().strip("'\"")
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)

    parsed = urllib.parse.urlsplit(raw_url)
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("postgresql", "postgres"):
        raise ValueError(f"Invalid URL scheme '{scheme}'. Must be 'postgresql'.")

    host = (parsed.hostname or "").lower().strip()
    if not host:
        raise ValueError("Database connection URL missing valid hostname.")

    # CRITICAL: Reject localhost and loopback addresses
    if host in ("localhost", "127.0.0.1", "::1", "0.0.0.0") or host.endswith(".localhost"):
        raise RuntimeError(f"CRITICAL SAFETY ERROR: Migration target CANNOT be localhost/loopback ('{host}')!")

    path = (parsed.path or "").strip().lstrip("/")
    if not path:
        raise ValueError("Database connection URL missing database name (e.g. /postgres).")

    if path.lower() == "farmconnect_db" and host in ("localhost", "127.0.0.1", "::1"):
        raise RuntimeError("CRITICAL SAFETY ERROR: Target points to local farmconnect_db!")

    port = parsed.port or 5432

    # Check port & mode:
    # 5432 on pooler.supabase.com is Session Mode (supports DDL migrations & IPv4)
    # 5432 on db.[ref].supabase.co is Direct Connection (supports DDL migrations)
    # 6543 on pooler.supabase.com is Transaction Mode (NOT suitable for DDL migrations)
    connection_mode = "Direct Connection"
    if "pooler.supabase.com" in host:
        if port == 5432:
            connection_mode = "Supabase Session Pooler (port 5432 - IPv4 & DDL compatible)"
        elif port == 6543:
            connection_mode = "Supabase Transaction Pooler (port 6543)"
            raise ValueError(
                "CRITICAL: Port 6543 is Supabase Transaction Pooler, which does NOT support "
                "Alembic DDL migrations. Please use the Session Pooler on port 5432 instead."
            )

    # Username check
    username = parsed.username or ""
    if not username:
        raise ValueError("Database connection URL missing username.")

    # Password check
    password = parsed.password
    if not password:
        raise ValueError("Database connection URL missing password.")

    # SSL check
    query_params = urllib.parse.parse_qs(parsed.query)
    sslmode = query_params.get("sslmode", [""])[0].lower()
    if sslmode not in ("require", "verify-full", "verify-ca"):
        raise ValueError(f"SSL must be required. 'sslmode=require' is missing or invalid (got '{sslmode}').")

    return {
        "url": raw_url,
        "host": host,
        "port": port,
        "username": username,
        "database": path,
        "connection_mode": connection_mode,
        "sslmode": sslmode,
    }


def obtain_supabase_url() -> str:
    """Prompt user or read environment variable for Supabase connection URL.
    
    Supports:
    1. Dashboard URI template containing '[YOUR-PASSWORD]'.
    2. Prompting for database password separately with hidden input.
    3. Automatic percent-encoding of special characters in passwords.
    4. SUPABASE_DATABASE_URL environment variable.
    """
    env_url = os.getenv("SUPABASE_DATABASE_URL")
    if env_url:
        if PASSWORD_PLACEHOLDER_REGEX.search(env_url):
            env_pw = os.getenv("SUPABASE_DB_PASSWORD")
            if not env_pw:
                print("[*] SUPABASE_DATABASE_URL contains [YOUR-PASSWORD] placeholder.")
                env_pw = getpass.getpass("Enter Supabase Database Password (hidden): ")
            return build_supabase_url(env_url, env_pw)
        return build_supabase_url(env_url)

    print("\n" + "=" * 72)
    print("Supabase Connection Setup")
    print("=" * 72)
    print("From your Supabase Dashboard:")
    print("  Go to: Project Settings -> Database -> Connection string -> URI")
    print("  Select: 'Connection Pooler' (Session mode, port 5432 for IPv4 compatibility)")
    print("  Or:     'Direct Connection' (port 5432)")
    print("=" * 72)

    try:
        template = input("\nEnter Supabase URI Template (or press Enter to cancel):\n> ").strip()
    except (EOFError, OSError):
        raise RuntimeError("Cannot prompt for Supabase URI in non-interactive environment. Set SUPABASE_DATABASE_URL.")

    if not template:
        raise RuntimeError("Migration cancelled: No Supabase URI provided.")

    if PASSWORD_PLACEHOLDER_REGEX.search(template) or "@" not in template.split("//")[-1].split(":")[0]:
        try:
            pw = getpass.getpass("\nEnter Supabase Database Password (input is hidden):\n> ").strip()
        except (EOFError, OSError):
            raise RuntimeError("Cannot prompt for password in non-interactive environment.")
        if not pw:
            raise RuntimeError("Migration cancelled: Database password cannot be empty.")
        final_url = build_supabase_url(template, pw)
    else:
        # Check if multiple '@' symbols are present in unencoded password
        parts = template.split("@")
        if len(parts) > 2:
            print("[!] Notice: Detected multiple '@' symbols in URI. Password contains unencoded reserved characters.")
            print("[!] Please enter password separately so it will be percent-encoded safely.")
            try:
                pw = getpass.getpass("\nEnter Supabase Database Password (input is hidden):\n> ").strip()
            except (EOFError, OSError):
                raise RuntimeError("Cannot prompt for password in non-interactive environment.")
            user_part = parts[0]
            host_part = parts[-1]
            reconstructed_template = f"{user_part}:[YOUR-PASSWORD]@{host_part}"
            final_url = build_supabase_url(reconstructed_template, pw)
        else:
            final_url = build_supabase_url(template)

    return final_url


def run_preflight_check(supabase_url: str):
    """Inspect remote Supabase database prior to applying schema."""
    print(f"[*] Connecting to Supabase target: {mask_url(supabase_url)}...")
    with psycopg.connect(supabase_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            pg_ver = cur.fetchone()[0]
            print(f"[+] Remote PostgreSQL Version: {pg_ver.split(',')[0]}")

            cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'btree_gist';")
            ext = cur.fetchone()
            if ext:
                print(f"[+] Extension 'btree_gist' is installed (v{ext[1]}).")
            else:
                print("[!] Notice: 'btree_gist' not yet active. Alembic migration will execute CREATE EXTENSION.")

            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            existing_tables = [r[0] for r in cur.fetchall()]
            if existing_tables:
                print(f"[!] Notice: Found {len(existing_tables)} existing tables in public schema: {existing_tables}")
                if "users" in existing_tables or "alembic_version" in existing_tables:
                    print("[!] Target already contains tables.")
            else:
                print("[+] Public schema is clean (0 user tables). Ready for initial migration.")

    return True


def apply_schema_migration(supabase_url: str):
    """Execute Alembic migrations directly against validated Supabase URL."""
    print("[*] Applying Alembic migrations to Supabase...")

    # 1. Force environment overrides to ensure local .env is completely overridden
    os.environ["DATABASE_URL"] = supabase_url
    os.environ["APP_ENV"] = "production"
    os.environ["MOCK_OTP_ENABLED"] = "false"
    if not os.getenv("SECRET_KEY") or os.getenv("SECRET_KEY") == "farmconnect-insecure-default-key-change-me":
        os.environ["SECRET_KEY"] = "fc-migration-temporary-validation-key-837482"

    # 2. Directly update config classes before app creation
    from config import ProductionConfig, DevelopmentConfig
    ProductionConfig.SQLALCHEMY_DATABASE_URI = supabase_url
    DevelopmentConfig.SQLALCHEMY_DATABASE_URI = supabase_url

    from app import create_app
    from flask_migrate import upgrade

    app = create_app("production")
    with app.app_context():
        # 3. Fail-closed engine assertion: verify engine host is NOT localhost
        engine = app.extensions['migrate'].db.engine
        engine_host = engine.url.host
        if engine_host in ("localhost", "127.0.0.1", "::1"):
            raise RuntimeError(f"FATAL: Migration engine attempted to target local database host '{engine_host}'!")

        print(f"[*] Engine successfully bound to target host: {engine_host} (port: {engine.url.port})")
        upgrade()

    print("[+] Alembic upgrade completed successfully.")


def verify_supabase_schema(supabase_url: str):
    """Verify all 12 tables, constraints, and revision head on Supabase."""
    print("[*] Verifying schema and constraints on Supabase...")
    expected_tables = {
        "alembic_version",
        "booking_status_history",
        "bookings",
        "contact_enquiries",
        "machinery",
        "machinery_availability",
        "machinery_photos",
        "machinery_rates",
        "otp_verifications",
        "provider_profiles",
        "user_locations",
        "users",
    }

    with psycopg.connect(supabase_url) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
            """)
            actual_tables = {r[0] for r in cur.fetchall()}
            missing = expected_tables - actual_tables
            if missing:
                raise RuntimeError(f"Missing expected tables in Supabase schema: {missing}")
            print(f"[+] All 12 expected tables verified in Supabase public schema.")

            cur.execute("SELECT version_num FROM alembic_version;")
            head = cur.fetchone()
            if not head or head[0] != "aeacc557d85c":
                raise RuntimeError(f"Unexpected Alembic revision on Supabase: {head}")
            print(f"[+] Alembic revision verified at head: {head[0]}")

            cur.execute("""
                SELECT conname 
                FROM pg_constraint 
                WHERE conname = 'exclude_overlapping_confirmed_bookings';
            """)
            if not cur.fetchone():
                raise RuntimeError("Exclusion constraint 'exclude_overlapping_confirmed_bookings' is missing!")
            print("[+] Database exclusion constraint 'exclude_overlapping_confirmed_bookings' verified active.")


def get_table_columns(cur, table_name: str) -> list[str]:
    """Retrieve column names for a table in public schema in ordinal order."""
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    return [r[0] for r in cur.fetchall()]


def migrate_data(source_url: str, supabase_url: str):
    """Migrate all application records in dependency order from local DB to Supabase."""
    print("\n[*] Starting data migration from local PostgreSQL to Supabase...")
    print(f"[*] Source: {mask_url(source_url)} (READ-ONLY)")
    print(f"[*] Target: {mask_url(supabase_url)}")

    if source_url == supabase_url:
        raise RuntimeError("FATAL: Source and target URLs are identical! Aborting.")

    tables_in_order = [
        "users",
        "contact_enquiries",
        "provider_profiles",
        "user_locations",
        "machinery",
        "machinery_availability",
        "machinery_photos",
        "machinery_rates",
        "bookings",
        "booking_status_history",
        "otp_verifications",
    ]

    with psycopg.connect(source_url) as src_conn, psycopg.connect(supabase_url) as dst_conn:
        # Enforce read-only transaction on source session
        with src_conn.cursor() as src_cur:
            src_cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;")

        with src_conn.cursor() as src_cur, dst_conn.cursor() as dst_cur:
            for tbl in tables_in_order:
                src_cur.execute(f'SELECT COUNT(*) FROM "{tbl}";')
                row_count = src_cur.fetchone()[0]
                if row_count == 0:
                    print(f"[*] Table '{tbl}': 0 rows (skipped).")
                    continue

                cols = get_table_columns(src_cur, tbl)
                col_list_str = ", ".join(f'"{c}"' for c in cols)
                placeholders = ", ".join(["%s"] * len(cols))

                src_cur.execute(f'SELECT {col_list_str} FROM "{tbl}";')
                rows = src_cur.fetchall()
                print(f"[*] Migrating table '{tbl}': {len(rows)} record(s)...")

                if tbl == "otp_verifications":
                    insert_sql = f"""
                        INSERT INTO "{tbl}" ({col_list_str}) 
                        VALUES ({placeholders}) 
                        ON CONFLICT (id) DO NOTHING;
                    """
                else:
                    update_cols = [c for c in cols if c != "id"]
                    update_clause = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in update_cols)
                    insert_sql = f"""
                        INSERT INTO "{tbl}" ({col_list_str}) 
                        VALUES ({placeholders}) 
                        ON CONFLICT (id) DO UPDATE SET {update_clause};
                    """

                for r in rows:
                    dst_cur.execute(insert_sql, r)

                print(f"[+] Successfully migrated {len(rows)} record(s) into '{tbl}'.")

            dst_conn.commit()
            print("[+] All data committed to Supabase successfully.")


def verify_target_data(source_url: str, supabase_url: str):
    """Verify row counts match across all tables and verify password authentication compatibility."""
    print("\n[*] Comparing table row counts between local source and Supabase target:")
    tables = [
        "users",
        "provider_profiles",
        "user_locations",
        "machinery",
        "machinery_rates",
        "machinery_availability",
        "machinery_photos",
        "bookings",
        "booking_status_history",
        "contact_enquiries",
        "otp_verifications",
        "alembic_version",
    ]

    with psycopg.connect(source_url) as src_conn, psycopg.connect(supabase_url) as dst_conn:
        with src_conn.cursor() as src_cur, dst_conn.cursor() as dst_cur:
            print(f"{'Table Name':<28} | {'Local Rows':<12} | {'Supabase Rows':<14} | Status")
            print("-" * 72)
            all_matched = True
            for tbl in tables:
                src_cur.execute(f'SELECT COUNT(*) FROM "{tbl}";')
                src_cnt = src_cur.fetchone()[0]
                dst_cur.execute(f'SELECT COUNT(*) FROM "{tbl}";')
                dst_cnt = dst_cur.fetchone()[0]
                status = "MATCH" if src_cnt == dst_cnt else "MISMATCH"
                if status != "MATCH":
                    all_matched = False
                print(f"{tbl:<28} | {src_cnt:<12} | {dst_cnt:<14} | {status}")
            print("-" * 72)

            if not all_matched:
                raise RuntimeError("Row count mismatch detected between local and Supabase databases!")

            dst_cur.execute("SELECT id, role, password_hash FROM users WHERE role = 'ADMIN' LIMIT 1;")
            admin_row = dst_cur.fetchone()
            if admin_row:
                has_hash = bool(admin_row[2] and admin_row[2].startswith(("scrypt:", "pbkdf2:")))
                print(f"[+] Admin account password hash format verified: {has_hash}")

    print("[+] SUCCESS: Data migration and verification complete!")


def main():
    print("=" * 72)
    print("FarmConnect — Supabase End-to-End Migration Runner")
    print("=" * 72)

    source_url = os.getenv("LOCAL_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not source_url:
        print("[-] ERROR: LOCAL_DATABASE_URL or DATABASE_URL not found in .env.", file=sys.stderr)
        sys.exit(1)

    try:
        supabase_url = obtain_supabase_url()
        validation = validate_supabase_url(supabase_url)
        print(f"[+] Target validated: {mask_url(supabase_url)}")
        print(f"[+] Connection mode: {validation['connection_mode']}")
        print(f"[+] Remote Host:    {validation['host']}:{validation['port']}")
        print(f"[+] Database:       {validation['database']}")
        print(f"[+] SSL Mode:       {validation['sslmode']}")

        # Step 1: Pre-flight check
        run_preflight_check(supabase_url)

        # Step 2: Schema migration
        apply_schema_migration(supabase_url)

        # Step 3: Schema verification
        verify_supabase_schema(supabase_url)

        # Step 4: Data migration
        migrate_data(source_url, supabase_url)

        # Step 5: Data verification
        verify_target_data(source_url, supabase_url)

        print("\n" + "=" * 72)
        print("[+] MIGRATION TO SUPABASE COMPLETE AND VERIFIED!")
        print("=" * 72)

    except Exception as exc:
        print(f"\n[-] MIGRATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
