"""
Test Chunk 1A: RAG Service (Standalone)

Tests the RAG service in isolation to verify:
- Document storage
- Retrieval by query
- Multiple categories
- Statistics tracking
"""

import os
import shutil
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_rag_store_and_retrieve():
    """Test RAG works in isolation."""
    from app.services.rag_service import RAGService

    # Use a test directory
    test_dir = "./test_data/chromadb_test"

    # Clean up any previous test data
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    # Initialize
    rag = RAGService(persist_directory=test_dir)
    print("✓ RAG Service initialized")

    # Test 1: Store a decision
    doc_id = rag.store(
        content="We decided to use PostgreSQL for the database",
        category="decisions",
        metadata={"project": "test"}
    )
    assert doc_id is not None
    print(f"✓ Stored document: {doc_id}")

    # Test 2: Retrieve by query
    results = rag.retrieve(
        query="what database are we using",
        categories=["decisions"],
        n_results=3
    )
    assert len(results) > 0
    assert "PostgreSQL" in results[0]["content"]
    print(f"✓ Retrieved: {results[0]['content'][:50]}...")

    # Test 3: Store different categories
    rag.store("Fixed bug in auth module", "code_changes")
    rag.store("Login flow requirements", "specs")
    rag.store("TypeError in user service fixed by adding null check", "errors")
    rag.store("Discussed API design for user endpoints", "conversations")

    stats = rag.get_stats()
    assert stats["total"] >= 5
    print(f"✓ Stats: {stats}")

    # Test 4: Get relevant context
    context = rag.get_relevant_context("database setup")
    assert len(context) > 0
    print(f"✓ Context retrieval works ({len(context)} chars)")

    # Test 5: Convenience methods
    rag.store_decision(
        decision="Use JWT for authentication",
        context="More secure than sessions",
        tags=["auth", "security"]
    )
    print("✓ store_decision works")

    rag.store_code_change(
        summary="Added user authentication",
        files=["auth.py", "user.py"],
        details="Implemented JWT-based auth"
    )
    print("✓ store_code_change works")

    rag.store_error(
        error="ImportError: No module named 'jwt'",
        solution="pip install PyJWT",
        file="auth.py"
    )
    print("✓ store_error works")

    # Test 6: Project filtering
    rag.store(
        content="Project A specific decision",
        category="decisions",
        project_id=1
    )
    rag.store(
        content="Project B specific decision",
        category="decisions",
        project_id=2
    )

    results_a = rag.retrieve("project decision", project_id=1)
    print(f"✓ Project filtering works ({len(results_a)} results for project 1)")

    # Test 7: Get all by category
    all_decisions = rag.get_all_by_category("decisions")
    assert len(all_decisions) >= 3
    print(f"✓ Get all by category works ({len(all_decisions)} decisions)")

    # Final stats
    final_stats = rag.get_stats()
    print(f"\n✓ Final stats: {final_stats}")

    # Clean up
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    print("\n✅ RAG Service: ALL TESTS PASSED")
    return True


if __name__ == "__main__":
    try:
        test_rag_store_and_retrieve()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure chromadb is installed: pip install chromadb")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
