#!/usr/bin/env python3
"""
Design Tree Studio - Smoke Test Script

Quick verification that the application can boot and talk to DB + OpenAI.
Run this before deploying or after environment setup.

Usage:
    python scripts/smoke_test.py

Exit codes:
    0 - All tests passed
    1 - Critical failures (DB connection, missing tables)
    2 - Warning failures (OpenAI not configured)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables if dotenv is available
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # dotenv not installed, environment variables should be set manually
    env_path = project_root / ".env"
    pass


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_test(name: str, status: str, details: str = ""):
    """Print a test result."""
    symbols = {
        "PASS": "✓",
        "FAIL": "✗",
        "SKIP": "○",
        "WARN": "⚠"
    }
    symbol = symbols.get(status, "?")

    color_codes = {
        "PASS": "\033[92m",  # Green
        "FAIL": "\033[91m",  # Red
        "SKIP": "\033[93m",  # Yellow
        "WARN": "\033[93m",  # Yellow
    }
    reset = "\033[0m"

    color = color_codes.get(status, "")
    print(f"{color}{symbol} {name:.<50} {status}{reset}")
    if details:
        print(f"  {details}")


def test_imports():
    """Test that all core modules can be imported."""
    print_header("Testing Module Imports")

    try:
        from app.config.settings import settings
        print_test("Import settings", "PASS")
    except Exception as e:
        print_test("Import settings", "FAIL", str(e))
        return False

    try:
        from app.core.db import get_db, test_connection, check_tables_exist
        print_test("Import database utilities", "PASS")
    except Exception as e:
        print_test("Import database utilities", "FAIL", str(e))
        return False

    try:
        from app.core.models import (
            UserProfile, Project, Node, ChatSession, Settings
        )
        print_test("Import data models", "PASS")
    except Exception as e:
        print_test("Import data models", "FAIL", str(e))
        return False

    try:
        from app.services import (
            get_or_create_default_user,
            list_all_users,
            create_project,
        )
        print_test("Import services", "PASS")
    except Exception as e:
        print_test("Import services", "FAIL", str(e))
        return False

    return True


def test_environment():
    """Test environment configuration."""
    print_header("Testing Environment Configuration")

    from app.config.settings import settings

    # Check DATABASE_URL
    if settings.DATABASE_URL:
        print_test("DATABASE_URL configured", "PASS",
                   f"Database: {settings.DATABASE_URL[:30]}...")
        db_configured = True
    else:
        print_test("DATABASE_URL configured", "FAIL",
                   "DATABASE_URL not set in environment")
        db_configured = False

    # Check OPENAI_API_KEY
    if settings.OPENAI_API_KEY:
        key_preview = settings.OPENAI_API_KEY[:10] + "..." if len(settings.OPENAI_API_KEY) > 10 else settings.OPENAI_API_KEY
        print_test("OPENAI_API_KEY configured", "PASS",
                   f"Key starts with: {key_preview}")
        openai_configured = True
    else:
        print_test("OPENAI_API_KEY configured", "WARN",
                   "OpenAI API key not set (optional for setup)")
        openai_configured = False

    # Check app name and version
    print_test("Application name", "PASS", settings.APP_NAME)
    print_test("Application version", "PASS", settings.APP_VERSION)

    return db_configured, openai_configured


def test_database_connection():
    """Test database connection."""
    print_header("Testing Database Connection")

    from app.core.db import test_connection
    from app.config.settings import settings

    if not settings.DATABASE_URL:
        print_test("Database connection", "SKIP", "DATABASE_URL not configured")
        return False

    try:
        success, message = test_connection()

        if success:
            print_test("Database connection", "PASS", message)
            return True
        else:
            print_test("Database connection", "FAIL", message)
            return False

    except Exception as e:
        print_test("Database connection", "FAIL", str(e))
        return False


def test_database_schema():
    """Test database schema and tables."""
    print_header("Testing Database Schema")

    from app.core.db import check_tables_exist
    from app.config.settings import settings

    if not settings.DATABASE_URL:
        print_test("Database schema", "SKIP", "DATABASE_URL not configured")
        return False

    try:
        tables_exist, existing_tables = check_tables_exist()

        # Expected tables
        expected_tables = {
            'users', 'projects', 'project_contexts', 'nodes', 'node_versions',
            'draft_metas', 'rant_summaries', 'chat_sessions', 'chat_messages',
            'baton_snapshots', 'settings'
        }

        if tables_exist and len(existing_tables) > 0:
            print_test("Database schema initialized", "PASS",
                       f"Found {len(existing_tables)} tables")

            # Check if all expected tables exist
            missing_tables = expected_tables - set(existing_tables)

            if missing_tables:
                print_test("All expected tables present", "WARN",
                           f"Missing tables: {', '.join(missing_tables)}")
            else:
                print_test("All expected tables present", "PASS",
                           "All 11 expected tables found")

            # List tables in detail
            print("\n  Tables found:")
            for table in sorted(existing_tables):
                marker = "✓" if table in expected_tables else "?"
                print(f"    {marker} {table}")

            return True
        else:
            print_test("Database schema initialized", "FAIL",
                       "No tables found - run schema initialization")
            return False

    except Exception as e:
        print_test("Database schema", "FAIL", str(e))
        return False


def test_openai_api():
    """Test OpenAI API connection."""
    print_header("Testing OpenAI API")

    from app.config.settings import settings

    if not settings.OPENAI_API_KEY:
        print_test("OpenAI API test", "SKIP",
                   "OPENAI_API_KEY not configured")
        return False

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Make a minimal test call
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "user", "content": "Respond with just the word 'pong'"}
            ],
            max_tokens=10,
            temperature=0
        )

        reply = response.choices[0].message.content.strip()

        print_test("OpenAI API connection", "PASS",
                   f"Test call successful (model: {settings.OPENAI_MODEL})")
        print_test("OpenAI API response", "PASS",
                   f"Received: {reply}")

        return True

    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower():
            print_test("OpenAI API connection", "FAIL",
                       "Invalid API key")
        elif "rate" in error_msg.lower():
            print_test("OpenAI API connection", "WARN",
                       "Rate limit or quota issue")
        else:
            print_test("OpenAI API connection", "FAIL",
                       f"Error: {error_msg[:100]}")

        return False


def main():
    """Run all smoke tests."""
    print_header("Design Tree Studio - Smoke Test")
    print(f"Project root: {project_root}")
    print(f"Environment file: {env_path}")

    # Track overall status
    critical_failures = []
    warnings = []

    # Test 1: Module imports
    if not test_imports():
        critical_failures.append("Module imports failed")

    # Test 2: Environment configuration
    db_configured, openai_configured = test_environment()
    if not db_configured:
        critical_failures.append("DATABASE_URL not configured")
    if not openai_configured:
        warnings.append("OPENAI_API_KEY not configured (optional)")

    # Test 3: Database connection
    if db_configured:
        db_connected = test_database_connection()
        if not db_connected:
            critical_failures.append("Database connection failed")
    else:
        db_connected = False

    # Test 4: Database schema
    if db_connected:
        schema_ok = test_database_schema()
        if not schema_ok:
            critical_failures.append("Database schema not initialized or incomplete")

    # Test 5: OpenAI API (optional)
    if openai_configured:
        openai_ok = test_openai_api()
        if not openai_ok:
            warnings.append("OpenAI API test failed")

    # Summary
    print_header("Test Summary")

    if critical_failures:
        print("\n❌ CRITICAL FAILURES:")
        for failure in critical_failures:
            print(f"  - {failure}")

    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")

    if not critical_failures and not warnings:
        print("\n✅ ALL TESTS PASSED!")
        print("\nYour Design Tree Studio environment is ready to use.")
        print("Run: streamlit run app/streamlit_app.py")
        exit_code = 0
    elif not critical_failures:
        print("\n✅ CRITICAL TESTS PASSED (with warnings)")
        print("\nYour environment is functional but has warnings.")
        print("Run: streamlit run app/streamlit_app.py")
        exit_code = 2
    else:
        print("\n❌ SMOKE TEST FAILED")
        print("\nPlease fix critical issues before running the application.")
        print("\nQuick fixes:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in DATABASE_URL and OPENAI_API_KEY")
        print("  3. Run: streamlit run app/streamlit_app.py")
        print("  4. Initialize database schema in the UI")
        exit_code = 1

    print("\n" + "=" * 70 + "\n")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
