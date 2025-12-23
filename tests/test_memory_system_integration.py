"""
Test Chunk: Full Memory System Integration

Tests the complete Memory System:
- RAG + Context Assembler working together
- End-to-end workflow
"""

import os
import shutil
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_full_memory_system():
    """Test the complete Memory System integration."""
    from app.services.rag_service import RAGService
    from app.services.context_assembler import ContextAssembler

    print("=" * 60)
    print("MEMORY SYSTEM INTEGRATION TEST")
    print("=" * 60)

    # Setup
    test_dir = "./test_data/chromadb_integration_test"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    # Initialize services
    rag = RAGService(persist_directory=test_dir)
    assembler = ContextAssembler(db=None, rag_service=rag, max_context_tokens=100000)
    print("\n✓ Services initialized")

    # Simulate a development session
    print("\n--- Simulating Development Session ---\n")

    # Store initial specs
    rag.store_spec(
        spec_name="Memory System",
        content="Build a memory system with Baton (hot) + RAG (long) memory",
        spec_type="requirement"
    )
    print("✓ Stored spec: Memory System requirement")

    # Store decisions made
    rag.store_decision(
        decision="Use ChromaDB for vector storage",
        context="Simple, local, fast, good for development",
        tags=["architecture", "database"]
    )
    print("✓ Stored decision: ChromaDB selection")

    rag.store_decision(
        decision="Token budget: 15% baton, 25% RAG, 60% conversation",
        context="Based on typical context window needs"
    )
    print("✓ Stored decision: Token budget allocation")

    # Store code changes
    rag.store_code_change(
        summary="Created RAGService class",
        files=["app/services/rag_service.py"],
        details="Implemented store, retrieve, convenience methods"
    )
    print("✓ Stored code change: RAGService")

    rag.store_code_change(
        summary="Created ContextAssembler class",
        files=["app/services/context_assembler.py"],
        details="Implemented context assembly with token budgets"
    )
    print("✓ Stored code change: ContextAssembler")

    # Store an error that was fixed
    rag.store_error(
        error="ChromaDB Settings API changed in v0.4.0",
        solution="Use PersistentClient instead of Client with Settings",
        file="app/services/rag_service.py"
    )
    print("✓ Stored error: ChromaDB API fix")

    # Store conversation summary
    rag.store_conversation(
        summary="Discussed Memory System architecture",
        key_points=[
            "Baton = hot memory (current state)",
            "RAG = long memory (searchable history)",
            "Context Assembler combines both"
        ]
    )
    print("✓ Stored conversation summary")

    # Check stats
    stats = rag.get_stats()
    print(f"\n✓ RAG Stats: {stats}")

    # Test retrieval
    print("\n--- Testing Retrieval ---\n")

    # Query about ChromaDB
    results = rag.retrieve("what vector database are we using", n_results=3)
    assert any("ChromaDB" in r["content"] for r in results)
    print(f"✓ Query 'vector database': Found ChromaDB decision")

    # Query about token budget
    results = rag.retrieve("token allocation", n_results=3)
    assert any("15%" in r["content"] or "budget" in r["content"].lower() for r in results)
    print(f"✓ Query 'token allocation': Found budget decision")

    # Query about code changes
    results = rag.retrieve("what files were created", n_results=5)
    assert any("rag_service" in r["content"].lower() for r in results)
    print(f"✓ Query 'files created': Found code changes")

    # Test context assembly
    print("\n--- Testing Context Assembly ---\n")

    context = assembler.assemble(
        current_task="implement Memory System tests",
        include_baton=False,
        include_rag=True
    )

    assert len(context) > 0
    assert "Relevant History" in context
    print(f"✓ Assembled context: {len(context)} chars")

    # Check context health
    health = assembler.get_context_health(current_tokens=40000)
    print(f"✓ Context health at 40%: {health['status']} - {health['recommendation']}")

    # Simulate approaching context limit
    health_warning = assembler.get_context_health(current_tokens=72000)
    assert health_warning["should_baton"] == True
    print(f"✓ Context health at 72%: {health_warning['status']} - should_baton={health_warning['should_baton']}")

    # Clean up
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    print("\n" + "=" * 60)
    print("✅ MEMORY SYSTEM INTEGRATION: ALL TESTS PASSED")
    print("=" * 60)
    return True


def test_persistence():
    """Test that RAG data persists across service restarts."""
    from app.services.rag_service import RAGService

    test_dir = "./test_data/chromadb_persistence_test"

    # Clean up any previous test data
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    # First instance - store data
    rag1 = RAGService(persist_directory=test_dir)
    rag1.store("Persistent test data", "decisions")
    print("✓ Stored data in first instance")

    stats1 = rag1.get_stats()
    print(f"✓ Stats before restart: {stats1}")

    # Simulate restart - create new instance
    rag2 = RAGService(persist_directory=test_dir)
    stats2 = rag2.get_stats()
    print(f"✓ Stats after restart: {stats2}")

    # Verify data persisted
    results = rag2.retrieve("Persistent test", n_results=1)
    assert len(results) > 0
    assert "Persistent test data" in results[0]["content"]
    print("✓ Data persisted across restart")

    # Clean up
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    print("\n✅ Persistence Test: PASSED")
    return True


if __name__ == "__main__":
    try:
        test_full_memory_system()
        print("\n")
        test_persistence()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure chromadb is installed: pip install chromadb")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
