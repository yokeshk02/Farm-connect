"""Safe PostgreSQL database backup utility for FarmConnect.

Uses pg_dump custom format (-Fc) for atomic, compressed, flexible backups.
Credentials are passed strictly via subprocess environment variables and never logged or displayed.
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def find_pg_binary(binary_name: str) -> str:
    """Locate PostgreSQL binary in system PATH or standard installation paths."""
    # Check PATH first
    found = shutil.which(binary_name)
    if found:
        return found

    # Search standard Windows PostgreSQL install directories
    candidate_dirs = [
        Path(r"C:\Program Files\PostgreSQL\15\bin"),
        Path(r"C:\Program Files\PostgreSQL\16\bin"),
        Path(r"C:\Program Files\PostgreSQL\14\bin"),
    ]
    for d in candidate_dirs:
        bin_path = d / f"{binary_name}.exe"
        if bin_path.exists():
            return str(bin_path)

    raise FileNotFoundError(
        f"Could not locate '{binary_name}'. Ensure PostgreSQL client tools are installed and on PATH."
    )


def create_backup(target_dir: str | None = None) -> Path:
    """Execute pg_dump to produce a timestamped custom-format archive."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set in environment or .env file.")

    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip("/")
    user = parsed.username or "postgres"
    password = parsed.password or ""
    host = parsed.hostname or "localhost"
    port = str(parsed.port or 5432)

    # Determine backup output directory
    backup_dir = Path(target_dir) if target_dir else (BASE_DIR / "backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"{db_name}_backup_{timestamp}.dump"

    pg_dump_path = find_pg_binary("pg_dump")

    cmd = [
        pg_dump_path,
        "-h", host,
        "-p", port,
        "-U", user,
        "-Fc",              # Custom archive format (compressed, supports parallel pg_restore)
        "-v",               # Verbose
        "-f", str(backup_file),
        db_name,
    ]

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    print(f"[*] Starting backup of database '{db_name}' on {host}:{port}...")
    print(f"[*] Destination: {backup_file}")

    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # Scrub any accidental credential leaks from error output
        clean_err = result.stderr.replace(password, "******") if password else result.stderr
        raise RuntimeError(f"pg_dump failed with exit code {result.returncode}:\n{clean_err}")

    # Verify backup exists and is non-empty
    if not backup_file.exists():
        raise RuntimeError(f"Backup file was not created: {backup_file}")

    file_size = backup_file.stat().st_size
    if file_size == 0:
        backup_file.unlink(missing_ok=True)
        raise RuntimeError("Backup completed but produced an empty (0 byte) file.")

    size_kb = file_size / 1024
    print(f"[+] Backup successfully completed: {backup_file.name}")
    print(f"[+] Backup file size: {size_kb:.2f} KB ({file_size} bytes)")
    print(f"[+] Absolute path: {backup_file.resolve()}")
    return backup_file


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        created_file = create_backup(out_dir)
        print("[+] SUCCESS: Database backup verified and ready.")
    except Exception as exc:
        print(f"[-] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
