# Bootstrap Sequence

**Version:** 1.0
**Purpose:** Minimal phases to reach self-building capability
**Goal:** System builds the rest of itself

---

## The Bootstrap Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                     BOOTSTRAP POINT                                  │
│                                                                      │
│   Once these 4 components work together, the system can             │
│   build everything else about itself.                               │
│                                                                      │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│   │   Memory    │  │   Simple    │  │  Builder-   │  │  Simple   │ │
│   │   System    │  │  Round      │  │  Tester     │  │Orchestr-  │ │
│   │             │  │  Table      │  │  Loop       │  │  ator     │ │
│   │  (Baton+    │  │  (exists,   │  │  (quality   │  │  (basic   │ │
│   │   RAG)      │  │   enhance)  │  │   gate)     │  │   control)│ │
│   └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │
│         │                │                │                │        │
│         └────────────────┴────────────────┴────────────────┘        │
│                                    │                                 │
│                                    ▼                                 │
│                        ┌─────────────────────┐                      │
│                        │  SELF-BUILDING      │                      │
│                        │  CAPABILITY         │                      │
│                        └─────────────────────┘                      │
│                                    │                                 │
│                                    ▼                                 │
│   ════════════════════════════════════════════════════════════════  │
│              EVERYTHING BELOW BUILT BY THE SYSTEM                   │
│   ════════════════════════════════════════════════════════════════  │
│                                                                      │
│   Phase 5: Advanced Orchestrator (Conductor, Elders)                │
│   Phase 6: Agent OS Integration                                      │
│   Phase 7: Design OS Integration                                     │
│   Phase 8: Boilerplate Factory                                       │
│   Phase 9: Auto-Deploy System                                        │
│   Phase 10+: Your 50-60 Apps                                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase Overview

| Phase | Component | Status | Estimated Effort | Can Self-Build After? |
|-------|-----------|--------|------------------|----------------------|
| 1 | Memory System (Baton + RAG) | NEW | 1 session | No |
| 2 | Round Table + Memory Integration | ENHANCE | 1 session | No |
| 3 | Builder-Tester Loop | NEW | 1 session | No |
| 4 | Simple Orchestrator | NEW | 1 session | **YES** |
| 5+ | Everything else | SELF-BUILD | N/A | N/A |

---

## PHASE 1: Memory System

**Session Goal:** Implement Baton + RAG for infinite context

### What to Build
- `app/services/rag_service.py` - Vector database integration
- `app/services/context_assembler.py` - Combines Baton + RAG
- Enhance `app/services/baton_service.py` - Better snapshots
- Add `BatonSnapshot` model to `app/core/models.py`
- Basic memory status UI in `app/ui/roundtable_panel.py`

### Key Files to Read First
1. `specs/MEMORY_SYSTEM_SPEC.md` - Full specification
2. `app/services/baton_service.py` - Existing baton code (if any)
3. `app/core/models.py` - Existing data models

### Dependencies
```
chromadb>=0.4.0
```

### Success Criteria
- [ ] RAG stores and retrieves documents
- [ ] Baton captures current state
- [ ] Context Assembler combines both
- [ ] Memory persists across sessions
- [ ] Can query "what did we decide about X" and get answer

### Handoff to Phase 2
Create baton with:
- What was built
- File paths created/modified
- Any issues encountered
- Verification steps completed

---

## PHASE 2: Round Table + Memory Integration

**Session Goal:** Connect existing Round Table to Memory System

### What Already Exists
- `app/services/roundtable_service.py` - Full service with execution
- `app/ui/roundtable_panel.py` - UI panel
- `app/core/models.py` - RoundTable models

### What to Build
- Modify `execute_round()` to inject assembled context
- Auto-store decisions in RAG after consensus
- Auto-store code changes in RAG after builds
- Memory status display in UI
- Auto-baton trigger at 70% context

### Key Integration Points

```python
# In roundtable_service.py execute_round():

# 1. Before execution - inject context
assembled_context = context_assembler.assemble(
    current_task=round_obj.task_prompt
)
system_prompt = assembled_context + "\n\n" + session.master_prompt

# 2. After successful build - store in RAG
if result["success"]:
    rag_service.store_code_change(
        summary=round_obj.task_prompt,
        files=["..."],
        details=builder_response.content[:500]
    )

# 3. After consensus reached - store decision
if consensus["passed"]:
    rag_service.store_decision(
        decision=f"Approved: {round_obj.task_prompt}",
        context=builder_response.content[:200]
    )
```

### Success Criteria
- [ ] Round Table uses assembled context
- [ ] Decisions automatically stored
- [ ] Code changes automatically stored
- [ ] Can start new session with full context
- [ ] Context health displayed in UI

### Handoff to Phase 3
Create baton with:
- Integration complete
- Test results
- Any edge cases found

---

## PHASE 3: Builder-Tester Loop

**Session Goal:** Automated build → test → fix cycle

### What to Build
- `app/services/testing_facility.py` - Comprehensive test runner
- `app/services/build_test_loop.py` - Loop controller
- Integrate testing into round execution
- Testing panel UI

### Test Tiers to Implement
1. **Tier 1**: Syntax (ast.parse)
2. **Tier 2**: Static (flake8, mypy)
3. **Tier 3**: Unit (pytest)
4. **Tier 4**: Integration (database)
5. **Tier 5**: App (import test)

### Key Files to Read First
1. `specs/BUILDER_TESTER_LOOP_SPEC.md` - Full specification
2. `app/services/roundtable_service.py` - Where to integrate

### Dependencies
```
flake8>=6.0.0
mypy>=1.0.0
pytest>=7.0.0
```

### Success Criteria
- [ ] All 5 test tiers run
- [ ] Build-test-fix loop works
- [ ] Auto-fix on failure (up to N iterations)
- [ ] Clear failure reports for builder
- [ ] Tests integrated into round execution

### Handoff to Phase 4
Create baton with:
- Testing facility complete
- Sample test run results
- Integration points documented

---

## PHASE 4: Simple Orchestrator

**Session Goal:** Basic control layer to coordinate everything

### What to Build
- `app/services/conductor_service.py` - Basic Haiku-powered orchestrator
- Simple natural language command parsing
- Quick action buttons
- Connect to Memory, Round Table, and Testing

### Minimum Viable Orchestrator
```python
# Basic commands to support:
"Run a build round"           → execute_round()
"Run tests"                   → testing_facility.run_all_tests()
"Create a checkpoint"         → baton_service.generate_baton()
"What's our context status?"  → context_assembler.get_context_health()
"Store this decision: X"      → rag_service.store_decision()
```

### What NOT to Build Yet
- Elder Council (Phase 5)
- Complex execution modes (Phase 5)
- Debate/Critique modes (Phase 5)
- Full natural language flexibility (Phase 5)

### Success Criteria
- [ ] Basic commands work
- [ ] Orchestrator coordinates Memory + Round Table + Testing
- [ ] Simple UI for control
- [ ] System can execute: task → build → test → fix → store

### After Phase 4: BOOTSTRAP COMPLETE

The system can now:
1. Take a task description
2. Build code (Round Table)
3. Test code (Testing Facility)
4. Fix failures (Build-Test Loop)
5. Remember everything (Memory System)
6. Be controlled simply (Orchestrator)

**Now it builds the rest of itself.**

---

## PHASE 5+: Built By The System

After bootstrap, use the system to build:

### Phase 5: Advanced Orchestrator
- Elder Council service
- Conductor with full NLP
- Parallel/Debate/Critique modes
- Cost tracking dashboard

### Phase 6: Agent OS Integration
- Pull from Agent OS repo
- Integrate planning system
- Add task decomposition
- Workflow automation

### Phase 7: Design OS Integration
- Pull from Design OS repo
- Design document generation
- Spec-to-code pipeline
- Architecture visualization

### Phase 8: Boilerplate Factory
- Enterprise template generation
- Auth, database, API scaffolding
- One-click project creation
- Customization options

### Phase 9: Auto-Deploy
- CI/CD integration
- Staging environments
- Production deployment
- Monitoring setup

### Phase 10+: Your Apps
- 50-60 app ideas
- Built by the system
- Tested by the system
- Deployed by the system

---

## Session Management Protocol

### Starting a New Session

1. **Read the latest baton** (if exists)
2. **Read relevant specs** from `/specs/`
3. **Query RAG** for related decisions
4. **Understand current state** before coding

### Ending a Session

1. **Run all tests** to verify work
2. **Generate baton** with:
   - What was accomplished
   - Files created/modified
   - Issues encountered
   - Next steps
3. **Store key decisions** in RAG
4. **Commit and push** to branch

### Baton Template

```markdown
# Session Baton - [Date]

## Session Goal
[What this session aimed to accomplish]

## Completed
- [x] Task 1
- [x] Task 2
- [ ] Task 3 (partial)

## Files Changed
- `app/services/new_service.py` - Created
- `app/core/models.py` - Modified (added NewModel)
- `app/ui/panel.py` - Modified (added new section)

## Key Decisions
- Chose ChromaDB for RAG (simple, local, fast)
- Token budget: 15% baton, 25% RAG, 60% conversation

## Issues Encountered
- [Issue and how it was resolved]

## Next Steps (for next session)
1. Implement X
2. Test Y
3. Integrate Z

## Tests Status
- Tier 1 (Syntax): ✅ Pass
- Tier 2 (Static): ✅ Pass
- Tier 3 (Unit): ⚠️ 2 failures
- Tier 4 (Integration): ✅ Pass

## Context Usage
- Started at: 0%
- Ended at: ~45%
- Baton recommended: No
```

---

## Quick Reference: What Each Agent Needs

### Phase 1 Agent
**Goal:** Build Memory System
**Read:** `specs/MEMORY_SYSTEM_SPEC.md`
**Create:** `rag_service.py`, `context_assembler.py`
**Test:** Can store and retrieve, context assembles correctly

### Phase 2 Agent
**Goal:** Integrate Memory + Round Table
**Read:** `specs/MEMORY_SYSTEM_SPEC.md`, Phase 1 baton
**Modify:** `roundtable_service.py`, `roundtable_panel.py`
**Test:** Decisions stored, context injected, health displayed

### Phase 3 Agent
**Goal:** Build Testing Facility
**Read:** `specs/BUILDER_TESTER_LOOP_SPEC.md`, Phase 2 baton
**Create:** `testing_facility.py`, `build_test_loop.py`
**Test:** All tiers run, loop fixes failures

### Phase 4 Agent
**Goal:** Build Simple Orchestrator
**Read:** `specs/ORCHESTRATOR_SPEC.md`, Phase 3 baton
**Create:** `conductor_service.py` (basic version)
**Test:** Commands work, coordinates all systems

---

## Estimated Timeline

| Phase | Sessions | Hours | Cumulative |
|-------|----------|-------|------------|
| 1 | 1 | 2-3 | 2-3 hours |
| 2 | 1 | 2-3 | 4-6 hours |
| 3 | 1 | 2-3 | 6-9 hours |
| 4 | 1 | 2-3 | 8-12 hours |
| **BOOTSTRAP** | **4** | **8-12** | **Complete** |
| 5+ | Self-build | Variable | Ongoing |

---

## Critical Success Factors

1. **Each phase creates a working baton** for the next
2. **Tests pass before moving on** - no technical debt
3. **RAG captures all decisions** - nothing lost
4. **Simple before complex** - bootstrap first, enhance later
5. **Use the system to build the system** - after Phase 4

---

*This document is the roadmap. Follow it to bootstrap, then let the system take over.*
