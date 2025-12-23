"""
Test Roundtable + Memory System Integration (Phase 2)

Tests:
- Memory injection into roundtable execution
- Auto-storage of decisions in RAG
- Auto-storage of code changes in RAG
- Memory status retrieval
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_memory_system_imports():
    """Test that memory system imports work correctly."""
    print("Testing Memory System imports...")

    try:
        from app.services.rag_service import RAGService
        print("  ✓ RAGService imported")
    except ImportError as e:
        print(f"  ✗ RAGService import failed: {e}")
        return False

    try:
        from app.services.context_assembler import ContextAssembler, EnhancedBatonService
        print("  ✓ ContextAssembler imported")
        print("  ✓ EnhancedBatonService imported")
    except ImportError as e:
        print(f"  ✗ Context Assembler import failed: {e}")
        return False

    try:
        from app.services.roundtable_service import RoundtableService, MEMORY_SYSTEM_AVAILABLE
        print(f"  ✓ RoundtableService imported")
        print(f"  ✓ MEMORY_SYSTEM_AVAILABLE = {MEMORY_SYSTEM_AVAILABLE}")
    except ImportError as e:
        print(f"  ✗ RoundtableService import failed: {e}")
        return False

    print("✅ All imports successful\n")
    return True


def test_roundtable_service_with_memory():
    """Test RoundtableService initialization with memory services."""
    print("Testing RoundtableService with Memory System...")

    from app.services.rag_service import RAGService
    from app.services.context_assembler import ContextAssembler
    from app.services.roundtable_service import RoundtableService

    # Initialize RAG service with test directory
    test_dir = "./test_data/chromadb_rt"
    rag = RAGService(persist_directory=test_dir)
    print(f"  ✓ RAGService initialized at {test_dir}")

    # Create a mock database session (for testing without real DB)
    class MockSession:
        def query(self, model):
            return MockQuery()
        def add(self, obj):
            pass
        def commit(self):
            pass
        def refresh(self, obj):
            pass

    class MockQuery:
        def filter(self, *args):
            return self
        def order_by(self, *args):
            return self
        def first(self):
            return None
        def all(self):
            return []

    mock_db = MockSession()

    # Initialize Context Assembler
    assembler = ContextAssembler(db=mock_db, rag_service=rag)
    print("  ✓ ContextAssembler initialized")

    # Initialize RoundtableService with memory
    service = RoundtableService(
        db=mock_db,
        rag_service=rag,
        context_assembler=assembler
    )
    print("  ✓ RoundtableService initialized with memory")

    # Check memory is enabled
    assert service.memory_enabled == True, "Memory should be enabled"
    print("  ✓ memory_enabled = True")

    assert service.rag_service is not None, "RAG service should be set"
    print("  ✓ rag_service is set")

    assert service.context_assembler is not None, "Context assembler should be set"
    print("  ✓ context_assembler is set")

    print("✅ RoundtableService with Memory: PASSED\n")
    return True


def test_memory_status():
    """Test memory status retrieval."""
    print("Testing Memory Status retrieval...")

    from app.services.rag_service import RAGService
    from app.services.context_assembler import ContextAssembler
    from app.services.roundtable_service import RoundtableService

    # Mock session
    class MockSession:
        def query(self, model):
            return MockQuery()

    class MockQuery:
        def filter(self, *args):
            return self
        def order_by(self, *args):
            return self
        def first(self):
            return None

    mock_db = MockSession()

    # Initialize services
    rag = RAGService(persist_directory="./test_data/chromadb_rt")
    assembler = ContextAssembler(db=mock_db, rag_service=rag)
    service = RoundtableService(db=mock_db, rag_service=rag, context_assembler=assembler)

    # Get memory status
    status = service.get_memory_status()
    print(f"  Memory Status: {status}")

    assert status["enabled"] == True, "Memory should be enabled"
    print("  ✓ enabled = True")

    assert status["rag_available"] == True, "RAG should be available"
    print("  ✓ rag_available = True")

    assert status["context_assembler_available"] == True, "Context assembler should be available"
    print("  ✓ context_assembler_available = True")

    assert status["rag_stats"] is not None, "RAG stats should be present"
    print(f"  ✓ RAG stats: {status['rag_stats']}")

    print("✅ Memory Status: PASSED\n")
    return True


def test_context_assembly_for_roundtable():
    """Test context assembly works for roundtable tasks."""
    print("Testing Context Assembly for Roundtable...")

    from app.services.rag_service import RAGService
    from app.services.context_assembler import ContextAssembler

    # Mock session
    class MockSession:
        def query(self, model):
            return MockQuery()

    class MockQuery:
        def filter(self, *args):
            return self
        def order_by(self, *args):
            return self
        def first(self):
            return None

    mock_db = MockSession()

    # Initialize services
    rag = RAGService(persist_directory="./test_data/chromadb_rt")

    # Seed some test data in RAG
    rag.store_decision(
        decision="Use async/await for API calls",
        context="Improves performance and readability"
    )
    rag.store_code_change(
        summary="Added error handling to API module",
        files=["api/handlers.py"],
        details="Try/catch blocks for all external calls"
    )
    print("  ✓ Seeded test data in RAG")

    # Create assembler
    assembler = ContextAssembler(db=mock_db, rag_service=rag)

    # Assemble context for a task
    context = assembler.assemble(
        current_task="implement API error handling",
        include_rag=True,
        include_baton=False  # Skip baton for this test (requires real DB)
    )

    print(f"  Assembled context length: {len(context)} chars")

    # Context should contain RAG results
    assert len(context) > 0, "Context should not be empty"
    print("  ✓ Context assembled successfully")

    # Should contain relevant content from RAG
    assert "error" in context.lower() or "api" in context.lower(), "Context should contain relevant content"
    print("  ✓ Context contains relevant content")

    print("✅ Context Assembly: PASSED\n")
    return True


def test_manual_decision_storage():
    """Test manual decision storage through service."""
    print("Testing Manual Decision Storage...")

    from app.services.rag_service import RAGService
    from app.services.context_assembler import ContextAssembler
    from app.services.roundtable_service import RoundtableService

    # Mock session
    class MockSession:
        def query(self, model):
            return MockQuery()

    class MockQuery:
        def filter(self, *args):
            return self
        def order_by(self, *args):
            return self
        def first(self):
            return None

    mock_db = MockSession()

    # Initialize services
    rag = RAGService(persist_directory="./test_data/chromadb_rt")
    assembler = ContextAssembler(db=mock_db, rag_service=rag)
    service = RoundtableService(db=mock_db, rag_service=rag, context_assembler=assembler)

    # Store a manual decision
    result = service.store_manual_decision(
        decision="Use PostgreSQL for main database",
        context="Better performance for complex queries",
        project_id=1
    )

    assert result == True, "Decision storage should succeed"
    print("  ✓ Manual decision stored successfully")

    # Verify it's in RAG
    results = rag.retrieve(
        query="PostgreSQL database",
        categories=["decisions"]
    )

    assert len(results) > 0, "Should find the stored decision"
    print(f"  ✓ Found {len(results)} matching decisions")

    print("✅ Manual Decision Storage: PASSED\n")
    return True


def cleanup_test_data():
    """Clean up test data directories."""
    import shutil
    test_dir = "./test_data/chromadb_rt"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"Cleaned up {test_dir}")


def run_all_tests():
    """Run all Phase 2 integration tests."""
    print("=" * 60)
    print("PHASE 2: Roundtable + Memory Integration Tests")
    print("=" * 60)
    print()

    tests = [
        ("Memory System Imports", test_memory_system_imports),
        ("RoundtableService with Memory", test_roundtable_service_with_memory),
        ("Memory Status Retrieval", test_memory_status),
        ("Context Assembly", test_context_assembly_for_roundtable),
        ("Manual Decision Storage", test_manual_decision_storage),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    # Cleanup
    cleanup_test_data()

    if failed == 0:
        print("\n🎉 ALL PHASE 2 TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
