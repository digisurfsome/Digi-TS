"""
Test Chunk 1C: Context Assembler (Requires RAG + Baton)

Tests the Context Assembler integration:
- Assembles baton + RAG content
- Health calculation
- Baton recommendation triggers
"""

import os
import shutil
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_context_assembler():
    """Test Context Assembler integrates RAG + Baton."""
    from app.services.rag_service import RAGService
    from app.services.context_assembler import ContextAssembler

    # Use test directory for RAG
    test_dir = "./test_data/chromadb_assembler_test"

    # Clean up any previous test data
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    # Initialize RAG
    rag = RAGService(persist_directory=test_dir)
    print("✓ RAG Service initialized")

    # Seed some data in RAG
    rag.store("We use JWT for authentication", "decisions")
    rag.store("Auth module is in app/services/auth.py", "code_changes")
    rag.store("User login requires email and password", "specs")
    print("✓ Seeded RAG with test data")

    # Create assembler (without DB for this standalone test)
    assembler = ContextAssembler(
        db=None,  # No DB for this test
        rag_service=rag,
        max_context_tokens=100000
    )
    print("✓ Context Assembler initialized")

    # Test 1: Context health at various levels
    health_low = assembler.get_context_health(current_tokens=30000)
    assert health_low["percentage"] == 30.0
    assert health_low["status"] == "healthy"
    assert health_low["should_baton"] == False
    print(f"✓ Health check at 30%: {health_low['status']} (should_baton={health_low['should_baton']})")

    health_mid = assembler.get_context_health(current_tokens=60000)
    assert health_mid["status"] == "caution"
    assert health_mid["should_baton"] == False
    print(f"✓ Health check at 60%: {health_mid['status']} (should_baton={health_mid['should_baton']})")

    health_high = assembler.get_context_health(current_tokens=75000)
    assert health_high["status"] == "critical"
    assert health_high["should_baton"] == True
    print(f"✓ Health check at 75%: {health_high['status']} (should_baton={health_high['should_baton']})")

    health_critical = assembler.get_context_health(current_tokens=90000)
    assert "CRITICAL" in health_critical["recommendation"]
    print(f"✓ Health check at 90%: {health_critical['recommendation'][:50]}...")

    # Test 2: Assemble context (RAG only, no baton since no DB)
    context = assembler.assemble(
        current_task="implement login endpoint",
        include_baton=False,  # No DB connection
        include_rag=True
    )

    assert "JWT" in context  # From RAG
    assert "Relevant History" in context
    print(f"✓ Assembled context with RAG ({len(context)} chars)")
    print(f"  Contains RAG content: ✓")

    # Test 3: Budget allocation
    budget = assembler.get_budget_allocation()
    assert budget["baton_percentage"] == 15
    assert budget["rag_percentage"] == 25
    assert budget["current_percentage"] == 60
    print(f"✓ Budget allocation: Baton={budget['baton_percentage']}%, RAG={budget['rag_percentage']}%, Current={budget['current_percentage']}%")

    # Test 4: Token counting and truncation
    long_text = "A" * 500000  # Very long text
    truncated = assembler._truncate(long_text, max_tokens=1000)
    assert len(truncated) < len(long_text)
    assert "truncated" in truncated
    print(f"✓ Truncation works (500000 chars -> {len(truncated)} chars)")

    # Test 5: Empty context handling
    empty_context = assembler.assemble(
        current_task="",
        include_baton=False,
        include_rag=False
    )
    assert empty_context == ""
    print("✓ Empty context handled correctly")

    # Clean up
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    print("\n✅ Context Assembler: ALL TESTS PASSED")
    return True


if __name__ == "__main__":
    try:
        test_context_assembler()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure chromadb is installed: pip install chromadb")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
