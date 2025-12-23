# Testing Chunks Guide

**Purpose:** Test each component independently before integration

---

## Phase 1: Memory System - Test Chunks

### Chunk 1A: RAG Service (Standalone)

**File:** `app/services/rag_service.py`

**Test Script:**
```python
# tests/test_rag_standalone.py

def test_rag_store_and_retrieve():
    """Test RAG works in isolation."""
    from app.services.rag_service import RAGService

    # Initialize
    rag = RAGService(persist_directory="./test_data/chromadb")

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

    stats = rag.get_stats()
    assert stats["total"] >= 3
    print(f"✓ Stats: {stats}")

    # Test 4: Get relevant context
    context = rag.get_relevant_context("database setup")
    assert len(context) > 0
    print(f"✓ Context retrieval works")

    print("\n✅ RAG Service: ALL TESTS PASSED")

if __name__ == "__main__":
    test_rag_store_and_retrieve()
```

**Run:** `python tests/test_rag_standalone.py`

**Pass Criteria:**
- [ ] Can store documents
- [ ] Can retrieve by query
- [ ] Multiple categories work
- [ ] Stats are accurate

---

### Chunk 1B: Enhanced Baton Service (Standalone)

**File:** `app/services/baton_service.py`

**Test Script:**
```python
# tests/test_baton_standalone.py

def test_baton_service():
    """Test Baton works in isolation."""
    from app.services.baton_service import EnhancedBatonService
    from app.core.db import get_test_db

    db = get_test_db()
    baton_service = EnhancedBatonService(db)

    # Test 1: Generate baton
    baton = baton_service.generate_baton(
        custom_sections={
            "current_state": "Building the auth module",
            "completed_items": "- Database setup\n- User model",
            "pending_items": "- Login endpoint\n- JWT tokens",
            "next_steps": "Implement login flow"
        }
    )
    assert baton.id is not None
    print(f"✓ Generated baton ID: {baton.id}")

    # Test 2: Load baton as string
    baton_str = baton_service.load_baton(baton.id)
    assert "Building the auth module" in baton_str
    assert "Database setup" in baton_str
    print(f"✓ Loaded baton ({len(baton_str)} chars)")

    # Test 3: Get latest baton
    latest = baton_service.get_latest_baton()
    assert latest.id == baton.id
    print(f"✓ Latest baton retrieved")

    # Test 4: Token count
    assert baton.token_count > 0
    print(f"✓ Token count: {baton.token_count}")

    print("\n✅ Baton Service: ALL TESTS PASSED")

if __name__ == "__main__":
    test_baton_service()
```

**Run:** `python tests/test_baton_standalone.py`

**Pass Criteria:**
- [ ] Can generate baton
- [ ] Can load as formatted string
- [ ] Can get latest
- [ ] Token counting works

---

### Chunk 1C: Context Assembler (Requires 1A + 1B)

**File:** `app/services/context_assembler.py`

**Test Script:**
```python
# tests/test_context_assembler.py

def test_context_assembler():
    """Test Context Assembler integrates RAG + Baton."""
    from app.services.rag_service import RAGService
    from app.services.baton_service import EnhancedBatonService
    from app.services.context_assembler import ContextAssembler
    from app.core.db import get_test_db

    # Setup dependencies
    rag = RAGService(persist_directory="./test_data/chromadb")
    db = get_test_db()
    baton_service = EnhancedBatonService(db)

    # Seed some data
    rag.store("We use JWT for authentication", "decisions")
    rag.store("Auth module is in app/services/auth.py", "code_changes")

    baton = baton_service.generate_baton(
        custom_sections={
            "current_state": "Implementing login endpoint",
            "next_steps": "Add token refresh"
        }
    )

    # Test assembler
    assembler = ContextAssembler(
        baton_service=baton_service,
        rag_service=rag,
        max_context_tokens=100000
    )

    # Test 1: Assemble context
    context = assembler.assemble(
        current_task="implement login endpoint",
        baton_id=baton.id
    )

    assert "Implementing login endpoint" in context  # From baton
    assert "JWT" in context  # From RAG
    print(f"✓ Assembled context ({len(context)} chars)")
    print(f"  Contains baton: ✓")
    print(f"  Contains RAG: ✓")

    # Test 2: Context health
    health = assembler.get_context_health(current_tokens=30000)
    assert health["percentage"] == 30.0
    assert health["status"] == "healthy"
    print(f"✓ Health check: {health['status']} ({health['percentage']}%)")

    # Test 3: Should trigger baton recommendation
    health_high = assembler.get_context_health(current_tokens=75000)
    assert health_high["should_baton"] == True
    print(f"✓ Baton recommendation at 75%: {health_high['should_baton']}")

    print("\n✅ Context Assembler: ALL TESTS PASSED")

if __name__ == "__main__":
    test_context_assembler()
```

**Run:** `python tests/test_context_assembler.py`

**Pass Criteria:**
- [ ] Assembles baton + RAG content
- [ ] Health calculation correct
- [ ] Baton recommendation triggers

---

## Phase 2: Round Table Integration - Test Chunks

### Chunk 2A: Memory Injection (Requires Phase 1)

**Test:** Round Table uses assembled context

```python
# tests/test_rt_memory_integration.py

def test_roundtable_uses_memory():
    """Test Round Table injects memory context."""
    # Setup memory system
    # Create session with memory
    # Execute round
    # Verify context was injected (check prompts sent to agents)
    pass
```

### Chunk 2B: Auto-Storage (Requires Phase 1)

**Test:** Decisions automatically stored in RAG

```python
def test_auto_storage():
    """Test decisions auto-store in RAG."""
    # Execute round with consensus
    # Check RAG for stored decision
    # Check RAG for stored code change
    pass
```

---

## Phase 3: Testing Facility - Test Chunks

### Chunk 3A: Individual Test Tiers

```python
# tests/test_testing_tiers.py

def test_tier1_syntax():
    """Test syntax checking works."""
    from app.services.testing_facility import TestingFacility

    tf = TestingFacility(project_path=".")

    # Valid code
    result = tf.run_syntax_tests(code="x = 1 + 2")
    assert result.status.value == "passed"

    # Invalid code
    result = tf.run_syntax_tests(code="x = 1 +")
    assert result.status.value == "failed"

    print("✅ Tier 1 (Syntax): PASSED")

def test_tier2_linting():
    """Test linting works."""
    # Similar pattern...
    pass

def test_tier3_unit():
    """Test pytest integration works."""
    pass

# ... etc for each tier
```

### Chunk 3B: Full Testing Facility

**Test:** All tiers run together

```python
def test_full_facility():
    """Test all tiers run and compile results."""
    tf = TestingFacility(project_path=".", enabled_tiers=[1,2,3,4,5])
    result = tf.run_all_tests(file_path="app/services/roundtable_service.py")

    assert result.total_tests >= 5
    print(f"Results: {result.passed} passed, {result.failed} failed")
```

### Chunk 3C: Build-Test Loop

**Test:** Loop fixes failures

```python
def test_build_test_loop():
    """Test the fix loop works."""
    # Create intentionally broken code
    # Run loop
    # Verify it attempts fixes
    # Verify it stops at max iterations or success
    pass
```

---

## Phase 4: Orchestrator - Test Chunks

### Chunk 4A: Conductor Command Parsing

```python
def test_conductor_parsing():
    """Test Conductor parses commands correctly."""
    from app.services.conductor_service import ConductorService

    conductor = ConductorService(...)

    # Test command parsing
    result = conductor.process_command(
        "Have agents 1 and 2 brainstorm auth approaches"
    )

    # Should produce set_group_prompt action
    assert any(a.action_type == "set_group_prompt" for a in result["actions"])
```

### Chunk 4B: Quick Actions

```python
def test_quick_actions():
    """Test button-based quick actions work."""
    conductor.quick_action("set_execution_mode", target="parallel")
    conductor.quick_action("execute_round")
```

### Chunk 4C: Full Integration

**Test:** Conductor → Memory → Round Table → Testing

```python
def test_full_integration():
    """Test all systems work together."""
    # Command to conductor
    # Verify memory is used
    # Verify round table executes
    # Verify tests run
    # Verify results stored
```

---

## Testing Sequence Summary

```
PHASE 1:
  1A: RAG alone           ──► TEST ──► ✓
  1B: Baton alone         ──► TEST ──► ✓
  1C: Assembler (1A+1B)   ──► TEST ──► ✓

PHASE 2:
  2A: RT + Memory inject  ──► TEST ──► ✓
  2B: Auto-storage        ──► TEST ──► ✓

PHASE 3:
  3A: Each tier alone     ──► TEST ──► ✓
  3B: All tiers together  ──► TEST ──► ✓
  3C: Build-Test Loop     ──► TEST ──► ✓

PHASE 4:
  4A: Command parsing     ──► TEST ──► ✓
  4B: Quick actions       ──► TEST ──► ✓
  4C: Full integration    ──► TEST ──► ✓

═══════════════════════════════════════
         BOOTSTRAP COMPLETE
═══════════════════════════════════════
```

---

## Copy-Paste Workflow

For each chunk:

1. **Copy** the implementation code from the spec
2. **Paste** into the target file path
3. **Copy** the test script from this guide
4. **Paste** into `tests/test_[chunk_name].py`
5. **Run** the test
6. **Fix** any issues
7. **Move** to next chunk

---

## Quick Reference: What Goes Where

| Spec Section | Paste Into |
|--------------|------------|
| RAG Service class | `app/services/rag_service.py` |
| Baton Service class | `app/services/baton_service.py` |
| Context Assembler class | `app/services/context_assembler.py` |
| Elder Council class | `app/services/elder_service.py` |
| Conductor class | `app/services/conductor_service.py` |
| Testing Facility class | `app/services/testing_facility.py` |
| Build-Test Loop class | `app/services/build_test_loop.py` |
| BatonSnapshot model | `app/core/models.py` (add to existing) |

---

*Test small, test often, integrate carefully.*
