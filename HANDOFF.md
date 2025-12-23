# Design Tree Studio - Agent Handoff Document

**Last Updated:** December 2024
**Status:** Bootstrap Complete (Phase 4) - Ready for Phase 5+
**Branch:** `claude/seven-coding-tasks-qYnIE`

---

## What Is This Project?

Design Tree Studio is a **self-building AI coding system**. It combines:
- **Memory System** - Infinite context through RAG + Baton handoffs
- **Round Table** - Multi-agent code generation with consensus voting
- **Testing Facility** - Automated 5-tier testing with fix loops
- **Conductor** - Simple orchestrator that coordinates everything

The goal: A system that can **build the rest of itself** and eventually generate complete applications from high-level descriptions.

---

## What's Already Built (Phases 1-4)

### Phase 1: Memory System ✅
**Files:** `app/services/rag_service.py`, `app/services/context_assembler.py`

- ChromaDB vector database for long-term memory
- Categories: `decisions`, `code_changes`, `conversations`, `errors`, `specs`
- Baton system for hot memory handoffs
- Context Assembler with token budget management (15% baton, 25% RAG, 60% current)

### Phase 2: Round Table + Memory ✅
**Files:** `app/services/roundtable_service.py`

- Multi-agent execution (Builder writes, Voters review)
- Consensus mechanism for quality control
- Auto-stores decisions and code changes in RAG
- Context injection from memory system

### Phase 3: Testing Facility ✅
**Files:** `app/services/testing_facility.py`, `app/services/build_test_loop.py`

- 5-tier testing: Syntax, Static, Unit, Integration, App
- Build-Test Loop for automatic fix iterations
- Failure summaries sent back to Builder
- Quality-gated code output

### Phase 4: Conductor ✅
**Files:** `app/services/conductor_service.py`

- Natural language command parsing
- Quick action buttons: `run_build`, `run_tests`, `create_checkpoint`, `check_status`
- Coordinates all systems
- Commands: "run a build round", "run tests", "create checkpoint", "store decision: X"

### Utilities ✅
**Files:** `scripts/seed_rag_knowledge.py`

- Seeds RAG with spec files and architecture knowledge
- Smart text chunking for large documents
- Re-runnable with `--clear` option

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER / UI                                   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CONDUCTOR                                   │
│                   (Natural Language → Actions)                      │
│                                                                     │
│   Commands:                     Quick Actions:                      │
│   • "run a build round"         • run_build                         │
│   • "run tests"                 • run_tests                         │
│   • "create checkpoint"         • create_checkpoint                 │
│   • "store decision: X"         • check_status                      │
│   • "what did we decide..."     • run_full_cycle                    │
└──────────────┬──────────────────────────────────┬───────────────────┘
               │                                  │
               ▼                                  ▼
┌──────────────────────────┐       ┌──────────────────────────────────┐
│      ROUND TABLE         │       │        TESTING FACILITY          │
│                          │       │                                  │
│  • Builder agent         │──────▶│  • Tier 1: Syntax               │
│  • Voter agents          │       │  • Tier 2: Static Analysis      │
│  • Consensus voting      │◀──────│  • Tier 3: Unit Tests           │
│  • Context injection     │       │  • Tier 4: Integration          │
│                          │       │  • Tier 5: App Tests            │
└──────────────┬───────────┘       └──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       MEMORY SYSTEM                                 │
│                                                                     │
│   ┌─────────────────────┐         ┌─────────────────────────────┐   │
│   │   BATON (Hot)       │         │      RAG (Long)             │   │
│   │   • Current state   │         │      • Vector DB            │   │
│   │   • Active task     │         │      • All decisions        │   │
│   │   • Next steps      │         │      • Code history         │   │
│   │   • ~5-10k tokens   │         │      • Searchable           │   │
│   └─────────────────────┘         └─────────────────────────────┘   │
│                                                                     │
│                    ┌─────────────────────────────┐                  │
│                    │    CONTEXT ASSEMBLER        │                  │
│                    │    • Token budgets          │                  │
│                    │    • Auto-baton at 70%      │                  │
│                    └─────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## What Comes Next (Phases 5+)

### Phase 5: Document Ingestion Service
**Priority:** HIGH - Enables bulk knowledge loading
**Effort:** Medium

Create a service that lets users ingest documents, repos, and URLs into RAG:

```python
# New file: app/services/document_ingestion_service.py

class DocumentIngestionService:
    def __init__(self, rag_service):
        self.rag = rag_service

    def ingest_file(self, file_path: str, category: str = "specs"):
        """Read file, chunk it, store each chunk in RAG."""
        content = read_file(file_path)
        chunks = self.chunk_text(content)
        for chunk in chunks:
            self.rag.store(chunk, category, {"source": file_path})

    def ingest_directory(self, dir_path: str, pattern: str = "**/*.md"):
        """Crawl directory, ingest all matching files."""
        for file in glob(dir_path, pattern):
            self.ingest_file(file)

    def ingest_repo(self, repo_path: str):
        """Smart repo ingestion - extract classes, functions, docs."""
        # Ingest Python files with AST parsing
        # Ingest markdown documentation
        # Store with appropriate categories

    def ingest_url(self, url: str):
        """Fetch URL content, parse, chunk, store."""
        content = fetch_and_parse(url)
        chunks = self.chunk_text(content)
        for chunk in chunks:
            self.rag.store(chunk, "specs", {"source": url})
```

**Add Conductor commands:**
- `"ingest file: /path/to/file.md"`
- `"ingest repo: external/agent-os"`
- `"ingest url: https://docs.example.com"`

---

### Phase 6: Agent OS Integration
**Priority:** HIGH - Major capability boost
**Effort:** Medium-High
**Spec:** `/specs/AGENT_OS_INTEGRATION.md`

Agent OS provides intelligent task decomposition. Integration steps:

1. **Clone the repo:**
   ```bash
   mkdir -p external
   git clone [agent-os-repo-url] external/agent-os
   ```

2. **Create adapter:**
   ```python
   # New file: app/adapters/agent_os_adapter.py

   class AgentOSAdapter:
       def __init__(self, agent_os_path: str = "external/agent-os"):
           # Import and initialize Agent OS
           pass

       def create_plan(self, goal: str) -> Plan:
           """Create plan from high-level goal."""
           pass

       def decompose_task(self, task: str) -> List[Task]:
           """Break task into subtasks."""
           pass
   ```

3. **Create integration service:**
   ```python
   # New file: app/services/agent_os_integration.py

   class AgentOSIntegration:
       def __init__(self, agent_os, roundtable, memory, testing):
           self.agent = agent_os
           self.rt = roundtable
           self.memory = memory
           self.testing = testing

       def plan_and_execute(self, goal: str) -> Dict:
           # 1. Get plan from Agent OS
           plan = self.agent.create_plan(goal)

           # 2. Store plan in memory
           self.memory.store(plan, "specs")

           # 3. Execute each task via Round Table
           for task in plan.tasks:
               result = self.rt.execute_round_with_testing(task)
               # Store results, update progress

           return results
   ```

4. **Add Conductor commands:**
   - `"plan: build user authentication"`
   - `"execute plan"`
   - `"show plan status"`

---

### Phase 7: Design OS Integration
**Priority:** MEDIUM - Enhances spec generation
**Effort:** Medium

Design OS generates design documents from requirements. Similar pattern to Agent OS:

1. Clone repo to `external/design-os`
2. Create `app/adapters/design_os_adapter.py`
3. Create `app/services/design_os_integration.py`
4. Wire into pipeline: User → Design OS → Agent OS → Round Table

---

### Phase 8: Boilerplate Factory
**Priority:** LOW (needs Phase 6-7 first)
**Effort:** Medium

Template-based project generation:

```python
class BoilerplateFactory:
    TEMPLATES = {
        "saas_starter": ["auth", "database", "api", "frontend", "billing"],
        "api_backend": ["auth", "database", "api", "docs"],
        "full_stack": ["auth", "database", "api", "frontend", "deployment"]
    }

    def generate(self, template_name: str, customizations: Dict):
        # 1. Get template
        # 2. Generate spec via Design OS
        # 3. Create plan via Agent OS
        # 4. Execute via Round Table + Testing
        # 5. Return complete project
```

---

### Phase 9: Elder Council (Advanced Orchestration)
**Priority:** LOW - Nice to have
**Effort:** High
**Spec:** `/specs/ORCHESTRATOR_SPEC.md` (Phase 5 section)

Upgrade Conductor with:
- Multiple AI models for orchestration decisions
- Complex execution modes (debate, critique)
- Full natural language understanding
- Dynamic workflow selection

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `app/services/rag_service.py` | Long-term vector memory |
| `app/services/context_assembler.py` | Token budget management |
| `app/services/roundtable_service.py` | Multi-agent code generation |
| `app/services/testing_facility.py` | 5-tier testing |
| `app/services/build_test_loop.py` | Auto-fix iterations |
| `app/services/conductor_service.py` | Orchestrator |
| `scripts/seed_rag_knowledge.py` | Bulk knowledge seeder |
| `specs/AGENT_OS_INTEGRATION.md` | Phase 6 detailed spec |
| `specs/MEMORY_SYSTEM_SPEC.md` | Memory system spec |
| `specs/ORCHESTRATOR_SPEC.md` | Conductor/Elder Council spec |

---

## How to Continue Development

### Starting a New Session

1. **Read this document first** - Understand the architecture
2. **Check `/specs/` folder** - Detailed specs for each component
3. **Run tests** to verify current state:
   ```bash
   python tests/test_conductor_service.py
   ```

### Adding New Features

1. **Create service in `app/services/`**
2. **Export from `app/services/__init__.py`**
3. **Add Conductor commands** if user-facing
4. **Write tests in `tests/`**
5. **Update this HANDOFF.md**

### Using the System

```python
# Create Conductor with all integrations
from app.services.conductor_service import create_conductor

conductor = create_conductor(
    db_session=db,
    anthropic_key="...",
    openai_key="...",
    project_path="/path/to/project"
)

# Process natural language commands
result = conductor.process_command("run a build round")

# Or use quick actions
result = conductor.quick_action("run_tests")
```

---

## Important Design Decisions

These are locked-in decisions. Don't change without good reason:

1. **ChromaDB for vectors** - Lightweight, Python-native
2. **Token budget 15/25/60** - Baton/RAG/Current allocation
3. **Auto-baton at 70%** - Prevents context overflow
4. **Local pattern matching first** - Conductor uses regex before AI
5. **Builder/Voter pattern** - Quality through consensus
6. **5-tier testing** - Comprehensive quality gates
7. **Specs in /specs/** - Documentation source of truth

---

## Getting Help

- **Specs:** `/specs/*.md` - Detailed specifications
- **Tests:** `/tests/` - Examples of how things work
- **Architecture:** Read this file's diagram section
- **Code:** Services are well-documented with docstrings

---

## Next Immediate Actions

For the next coding session:

1. **Install dependencies:**
   ```bash
   pip install chromadb sqlalchemy openai anthropic
   ```

2. **Run seed script:**
   ```bash
   python scripts/seed_rag_knowledge.py
   ```

3. **Build Document Ingestion Service** (Phase 5)
   - Create `app/services/document_ingestion_service.py`
   - Add Conductor commands
   - Test with local files

4. **Clone Agent OS repo** (if available)
   ```bash
   git clone [repo-url] external/agent-os
   ```

5. **Start Agent OS integration** (Phase 6)
   - Create adapter
   - Create integration service
   - Wire into Conductor

---

*This document is the source of truth for handoffs between sessions. Update it when making significant changes.*
