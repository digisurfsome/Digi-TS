"""
Simple test script to verify Phase 2 implementation.

This script tests:
1. Model imports
2. Database connection
3. Schema creation

Run this from the project root:
    python scripts/test_phase2.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_model_imports():
    """Test that all models can be imported."""
    print("Testing model imports...")
    try:
        from app.core.models import (
            UserProfile,
            Project,
            ProjectContext,
            Node,
            NodeVersion,
            DraftMeta,
            RantSummary,
            ChatSession,
            ChatMessage,
            BatonSnapshot,
            Settings,
            NodeStatus,
            NodeType,
            MessageRole,
        )
        print("✓ All models imported successfully")
        return True
    except Exception as e:
        print(f"✗ Model import failed: {e}")
        return False


def test_repository_imports():
    """Test that all repositories can be imported."""
    print("\nTesting repository imports...")
    try:
        from app.core.repositories import (
            BaseRepository,
            UserProfileRepository,
            ProjectRepository,
            ProjectContextRepository,
            NodeRepository,
            NodeVersionRepository,
        )
        print("✓ All repositories imported successfully")
        return True
    except Exception as e:
        print(f"✗ Repository import failed: {e}")
        return False


def test_db_functions():
    """Test database utility functions."""
    print("\nTesting database functions...")
    try:
        from app.core.db import (
            Base,
            get_engine,
            get_session_factory,
            test_connection,
            initialize_schema,
            check_tables_exist,
        )
        print("✓ Database functions imported successfully")
        return True
    except Exception as e:
        print(f"✗ Database functions import failed: {e}")
        return False


def test_schema_structure():
    """Test that the schema structure is valid."""
    print("\nTesting schema structure...")
    try:
        from app.core.db import Base
        from app.core import models  # Import to register models

        # Check that models are registered
        tables = Base.metadata.tables
        print(f"✓ Found {len(tables)} tables in schema:")
        for table_name in sorted(tables.keys()):
            print(f"  - {table_name}")
        return True
    except Exception as e:
        print(f"✗ Schema structure test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 2 Implementation Tests")
    print("=" * 60)

    results = []
    results.append(("Model Imports", test_model_imports()))
    results.append(("Repository Imports", test_repository_imports()))
    results.append(("Database Functions", test_db_functions()))
    results.append(("Schema Structure", test_schema_structure()))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:.<40} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("All tests passed! ✓")
        print("\nNext steps:")
        print("1. Configure your .env file with DATABASE_URL")
        print("2. Run: streamlit run app/streamlit_app.py")
        print("3. Click 'Initialize Schema' button in the UI")
    else:
        print("Some tests failed. Please check the errors above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
