"""Unit tests for Supabase migration script URL building, password encoding, and validation.

Verifies:
1. Passwords containing reserved characters (@, #, %, :, /, ?, &, +, [, ]) are safely percent-encoded.
2. Hostnames are never corrupted by special characters in passwords.
3. Templates with [YOUR-PASSWORD] placeholders are correctly resolved.
4. Masking never leaks raw passwords in logs or outputs.
5. Rejection of invalid targets: localhost, 127.0.0.1, ::1, 0.0.0.0, farmconnect_db.
6. Rejection of Transaction Pooler port 6543 for DDL migrations.
7. Acceptance of Session Pooler port 5432 and Direct Connection port 5432.
8. Automatic enforcement of sslmode=require.
"""

import pytest
import urllib.parse
import sqlalchemy as sa
from scripts.migrate_to_supabase import (
    encode_password,
    build_supabase_url,
    validate_supabase_url,
    mask_url,
)


def test_encode_password_handles_all_reserved_uri_characters():
    """Verify that encode_password percent-encodes all reserved characters."""
    raw_passwords = {
        "P@ssword@123": "P%40ssword%40123",
        "Secret#123": "Secret%23123",
        "Pass/word?": "Pass%2Fword%3F",
        "P%a&s+s:1[2]": "P%25a%26s%2Bs%3A1%5B2%5D",
        "Simple123": "Simple123",
    }
    for raw, expected in raw_passwords.items():
        assert encode_password(raw) == expected


def test_build_supabase_url_with_at_in_password():
    """Verify password containing '@' does not corrupt the hostname or port."""
    template = "postgresql://postgres.myprojectref:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
    password = "MyComplex@Password@2026!"

    built_url = build_supabase_url(template, password)

    # Validate using urllib.parse
    parsed = urllib.parse.urlsplit(built_url)
    assert parsed.username == "postgres.myprojectref"
    assert urllib.parse.unquote(parsed.password) == password
    assert parsed.hostname == "aws-0-ap-south-1.pooler.supabase.com"
    assert parsed.port == 5432
    assert parsed.path == "/postgres"
    assert "sslmode=require" in parsed.query

    # Validate using SQLAlchemy URL parser
    sa_url = sa.make_url(built_url)
    assert sa_url.host == "aws-0-ap-south-1.pooler.supabase.com"
    assert sa_url.password == password
    assert sa_url.port == 5432


def test_build_supabase_url_with_all_special_characters():
    """Verify password with multiple special characters constructs valid URL."""
    template = "postgresql://postgres.test:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    password = "P#s$w%o&r*d/1:2?3+4[5]"

    built_url = build_supabase_url(template, password)
    parsed = urllib.parse.urlsplit(built_url)
    assert parsed.hostname == "aws-0-us-east-1.pooler.supabase.com"
    assert urllib.parse.unquote(parsed.password) == password
    assert parsed.port == 5432

    sa_url = sa.make_url(built_url)
    assert sa_url.host == "aws-0-us-east-1.pooler.supabase.com"
    assert sa_url.password == password


def test_template_case_insensitive_placeholders():
    """Verify [YOUR-PASSWORD], [your-password], [PASSWORD], <password> are recognized."""
    placeholders = ["[YOUR-PASSWORD]", "[your-password]", "[Password]", "[PASSWORD]", "<password>"]
    password = "SafePassword123"

    for ph in placeholders:
        tmpl = f"postgresql://postgres.ref:{ph}@aws-0.pooler.supabase.com:5432/postgres"
        built = build_supabase_url(tmpl, password)
        assert ph not in built
        parsed = urllib.parse.urlsplit(built)
        assert urllib.parse.unquote(parsed.password) == password


def test_build_supabase_url_appends_sslmode_if_missing():
    """Verify that sslmode=require is automatically appended when missing."""
    template = "postgresql://postgres.ref:[YOUR-PASSWORD]@aws-0.pooler.supabase.com:5432/postgres"
    built = build_supabase_url(template, "Pass123")
    assert "sslmode=require" in built


def test_mask_url_never_exposes_password():
    """Verify that mask_url replaces passwords with '******'."""
    sensitive_passwords = [
        "P@ssword@123",
        "Secret#Hash123",
        "NormalPassword99",
        "Pass/With/Slashes",
    ]
    for pw in sensitive_passwords:
        url = build_supabase_url(
            "postgresql://postgres.ref:[YOUR-PASSWORD]@aws-0.pooler.supabase.com:5432/postgres",
            pw,
        )
        masked = mask_url(url)
        assert pw not in masked
        assert ":******@" in masked
        assert "aws-0.pooler.supabase.com" in masked
        assert "postgres.ref" in masked


def test_validate_supabase_url_accepts_session_pooler():
    """Verify that Supabase Session Pooler on port 5432 is accepted and identified."""
    url = "postgresql://postgres.myproj:secret%40pass@aws-0-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require"
    val = validate_supabase_url(url)
    assert val["host"] == "aws-0-ap-south-1.pooler.supabase.com"
    assert val["port"] == 5432
    assert "Session Pooler" in val["connection_mode"]
    assert val["username"] == "postgres.myproj"
    assert val["database"] == "postgres"
    assert val["sslmode"] == "require"


def test_validate_supabase_url_accepts_direct_connection():
    """Verify that Supabase Direct Connection on port 5432 is accepted."""
    url = "postgresql://postgres:secret%40pass@db.myprojectref.supabase.co:5432/postgres?sslmode=require"
    val = validate_supabase_url(url)
    assert val["host"] == "db.myprojectref.supabase.co"
    assert val["port"] == 5432
    assert val["connection_mode"] == "Direct Connection"


def test_validate_supabase_url_rejects_transaction_pooler_port_6543():
    """Verify that port 6543 on pooler.supabase.com is rejected for migrations."""
    url = "postgresql://postgres.myproj:secret@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"
    with pytest.raises(ValueError, match="Port 6543 is Supabase Transaction Pooler"):
        validate_supabase_url(url)


def test_validate_supabase_url_rejects_localhost_and_loopback():
    """Verify that localhost, 127.0.0.1, ::1, and 0.0.0.0 are rejected."""
    bad_urls = [
        "postgresql://postgres:pass@localhost:5432/postgres?sslmode=require",
        "postgresql://postgres:pass@127.0.0.1:5432/postgres?sslmode=require",
        "postgresql://postgres:pass@[::1]:5432/postgres?sslmode=require",
        "postgresql://postgres:pass@0.0.0.0:5432/postgres?sslmode=require",
        "postgresql://postgres:pass@test.localhost:5432/postgres?sslmode=require",
    ]
    for url in bad_urls:
        with pytest.raises(RuntimeError, match="Migration target CANNOT be localhost/loopback"):
            validate_supabase_url(url)


def test_validate_supabase_url_rejects_local_farmconnect_db():
    """Verify that local farmconnect_db is rejected."""
    url = "postgresql://postgres:pass@localhost:5432/farmconnect_db?sslmode=require"
    with pytest.raises(RuntimeError):
        validate_supabase_url(url)


def test_validate_supabase_url_rejects_missing_database_name():
    """Verify URL with no database path is rejected."""
    url = "postgresql://postgres:pass@aws-0.pooler.supabase.com:5432/?sslmode=require"
    with pytest.raises(ValueError, match="missing database name"):
        validate_supabase_url(url)


def test_validate_supabase_url_rejects_missing_password():
    """Verify URL with no password is rejected."""
    url = "postgresql://postgres@aws-0.pooler.supabase.com:5432/postgres?sslmode=require"
    with pytest.raises(ValueError, match="missing password"):
        validate_supabase_url(url)


def test_validate_supabase_url_rejects_missing_sslmode():
    """Verify URL without sslmode=require is rejected."""
    url = "postgresql://postgres:pass@aws-0.pooler.supabase.com:5432/postgres"
    with pytest.raises(ValueError, match="SSL must be required"):
        validate_supabase_url(url)
