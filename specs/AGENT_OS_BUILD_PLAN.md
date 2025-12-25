# Agent OS Build Plan: Complete Digi-TS System

**Purpose:** Build out the complete Digi-TS with Agent OS integration, unified workspace, and CLI/Dashboard architecture
**Format:** Agent OS 3-Layer Context + Phased Build

---

## Quick Reference: Testing System (For Future Agents)

After this build is complete, the next phase adds testing capabilities. Here's the concept:

1. **AI doesn't just suggest tests - it RUNS them**
   - Fills in prompts, toggles switches, sets up next test while current runs
   - 100x faster than human testing

2. **Two types of logging feed one system:**
   - Error reporting (does it work?)
   - Test criteria reporting (is it optimal?)
   - Both feed into one dashboard for AI to judge

3. **Test the WHOLE system together**
   - Components might work alone but fail together
   - Need integrated testing once all mechanisms are wired

4. **Discover truths through testing**
   - Some things become proven → remove testing
   - Some things stay situational → keep testing
   - System gets simpler over time as truths emerge

5. **AI controls testing loop:**
   - Creates test ideas
   - Fills in the test parameters
   - Runs tests
   - Analyzes results
   - Suggests conclusions
   - Human confirms or redirects

*This testing layer gets built AFTER the core system is complete.*

---

## Three-Layer Context

### Layer 1: Standards

```yaml
project_standards:
  language: Python 3.10+
  primary_framework: Streamlit
  future_framework: CLI core + Dashboard (React/Next.js)

code_style:
  - PEP 8 compliant
  - Type hints on all functions
  - Docstrings (Google style)
  - No magic numbers - use constants
  - Config-driven, not hardcoded

architecture_patterns:
  - Service layer (business logic)
  - Repository pattern (data access)
  - Dependency injection
  - Event-driven where async needed

file_structure:
  app/
    config/        # Settings, constants
    core/          # Models, database
    services/      # Business logic
    ui/            # Streamlit panels
  cli/             # CLI interface (future)
  specs/           # Documentation, plans

naming:
  files: snake_case.py
  classes: PascalCase
  functions: snake_case
  constants: UPPER_SNAKE_CASE

testing:
  unit: pytest
  integration: pytest + fixtures
  physical: Playwright + vision model

memory:
  vector_db: ChromaDB
  session: Baton system
  persistence: SQLite/PostgreSQL
```

### Layer 2: Product

```yaml
product_name: Digi-TS (Design Tree Studio)

vision: |
  AI-powered software development platform that transforms
  stream-of-consciousness ideas into working, tested software
  through multi-agent collaboration with human oversight.

target_users:
  power_users:
    interface: CLI
    needs: Speed, scripting, full control
  regular_users:
    interface: Dashboard (Streamlit now, React later)
    needs: Visual feedback, guided workflow

core_value_props:
  - Rant to working software
  - Multi-agent consensus (not single AI opinion)
  - Hallucination detection via qualification
  - Memory across sessions
  - Framework-agnostic design output

user_flows:
  1_input:
    - User provides rant/idea (text, voice, document)
    - System asks clarifying questions
    - Outputs crisp design spec

  2_planning:
    - Design spec enters 3-layer context
    - Task decomposition into phases
    - Each phase independently testable

  3_execution:
    - Qualified agents assigned
    - Roundtable (sequential) or Parallel mode
    - Knowledge injected before coding
    - Code generated with consensus

  4_output:
    - Working code files
    - Universal design tokens
    - Translatable to any framework

current_state: |
  Roundtable exists but not unified with Parallel.
  Agent OS (rant→spec) exists but not 3-layer context.
  RAG exists but no bulk import.
  LIMB test exists but not auto-wired.
  Design system missing (Universal Design OS).
```

### Layer 3: Specs

```yaml
integrations_needed:

  agent_os_context:
    purpose: 3-layer context system
    layers:
      standards: Coding DNA applied to ALL projects
      product: Vision/roadmap for THIS project
      specs: What we're building NOW
    injection: Before every agent execution

  unified_workspace:
    purpose: Merge Roundtable + Parallel
    modes:
      sequential: Builder → Voters → Consensus
      parallel: All agents answer same question
      hybrid: Parallel build → Sequential review
    toggle: User switches mode in UI

  universal_design_os:
    purpose: Framework-agnostic design system
    components:
      tokens: Colors, spacing, typography, radius
      patterns: Button, Card, Input, Table abstracts
      templates: 5-10 pre-built looks
    translation: AI converts to React, Vue, Svelte, Streamlit, etc.

  qualification_gate:
    purpose: Auto-test all new agents
    trigger: Before any agent joins execution
    test: LIMB or similar
    action: Pass → work, Fail → new instance

  bulk_rag_import:
    purpose: Import knowledge from URLs/chats
    sources: URLs, chat exports, documents
    output: Vector embeddings in ChromaDB
    timing: Available for injection before coding

database_models:
  existing:
    - Project, Session, ChatMessage
    - RoundtableSession, RoundtableAgent
    - Decision, CodeChange
  new:
    - DesignContext (3 layers)
    - DesignToken, DesignTemplate
    - QualificationResult
    - KnowledgeSource

api_structure:
  current: Streamlit-only (no API)
  future:
    - REST API for CLI access
    - WebSocket for real-time streaming
    - Same backend, multiple frontends
```

---

## Phased Build Plan

### Phase 1: 3-Layer Context System

**Goal:** Implement Standards/Product/Specs context that injects into every agent execution

**Files to Create:**
```
app/services/context_service.py     # Manages 3 layers
app/core/models.py                  # Add DesignContext model
app/ui/context_panel.py             # UI to edit layers
```

**Tasks:**

```yaml
1.1:
  name: Create DesignContext model
  description: |
    Database model storing 3-layer context per project.
    Fields: project_id, standards (JSON), product (JSON), specs (JSON)
  file: app/core/models.py
  action: Add model class

1.2:
  name: Create context service
  description: |
    Service to load, save, and format context for injection.
    Methods:
    - get_context(project_id) → dict with all 3 layers
    - save_context(project_id, layer, content)
    - format_for_injection(context) → string for system prompt
  file: app/services/context_service.py
  action: Create new file

1.3:
  name: Inject context into Roundtable
  description: |
    Modify roundtable execution to load context and inject
    into system prompt before any agent runs.
  file: app/services/roundtable_service.py
  action: Modify execute_round() to include context

1.4:
  name: Create context editor UI
  description: |
    Panel to view/edit all 3 layers.
    Tabs: Standards | Product | Specs
    Each with text area for YAML/JSON content.
  file: app/ui/context_panel.py
  action: Create new file

1.5:
  name: Wire context panel to main app
  description: |
    Add context panel to sidebar navigation.
    Load context when project selected.
  file: app/streamlit_app.py
  action: Add navigation and panel rendering
```

**Acceptance Criteria:**
- [ ] Can create/edit 3-layer context per project
- [ ] Context loads automatically when project selected
- [ ] Context injects into agent system prompts
- [ ] Context visible in execution logs

---

### Phase 2: Unified Workspace (Roundtable + Parallel)

**Goal:** Single workspace with mode toggle for sequential vs parallel execution

**Files to Modify:**
```
app/ui/roundtable_panel.py          # Add mode toggle, merge parallel display
app/services/roundtable_service.py  # Add parallel execution path
```

**Tasks:**

```yaml
2.1:
  name: Add mode toggle to workspace header
  description: |
    Add toggle switch: Sequential ↔ Parallel
    Store mode in session state.
    Visual indicator of current mode.
  file: app/ui/roundtable_panel.py
  action: Add toggle component in header

2.2:
  name: Implement parallel execution in service
  description: |
    Add method to run all agents simultaneously on same prompt.
    parallel_execute(agents, prompt) → list of responses
    Each agent gets same input, runs independently.
  file: app/services/roundtable_service.py
  action: Add parallel execution method

2.3:
  name: Merge results display
  description: |
    Sequential: Show builder output, then votes, then decision
    Parallel: Show all responses side-by-side
    Use same visual styling for both modes.
  file: app/ui/roundtable_panel.py
  action: Add conditional rendering based on mode

2.4:
  name: Enable mode switching mid-session
  description: |
    User can switch modes without losing:
    - Current task prompt
    - Agent selection
    - Previous results
    Clear only mode-specific state.
  file: app/ui/roundtable_panel.py
  action: Handle mode switch gracefully

2.5:
  name: Add hybrid mode option
  description: |
    Parallel build (all agents code) → Sequential review (voters judge)
    Combines both approaches for complex tasks.
  file: app/services/roundtable_service.py
  action: Add hybrid execution flow
```

**Acceptance Criteria:**
- [ ] Mode toggle visible and functional
- [ ] Sequential mode works as before
- [ ] Parallel mode runs all agents at once
- [ ] Can switch modes without data loss
- [ ] Hybrid mode available for complex tasks

---

### Phase 3: Universal Design OS

**Goal:** Framework-agnostic design tokens and patterns with AI translation

**Files to Create:**
```
app/services/design_os_service.py       # Token management, translation
app/ui/design_os_panel.py               # Design studio UI
templates/design_tokens/                 # Token files
  schema.json
  default_dark.json
  default_light.json
```

**Tasks:**

```yaml
3.1:
  name: Create design token schema
  description: |
    Define universal token format:
    {
      "colors": { "primary": "#xxx", "background": "#xxx", ... },
      "spacing": { "sm": "4px", "md": "8px", ... },
      "typography": { "heading": "Inter", "body": "Inter", ... },
      "radius": { "button": "6px", "card": "8px", ... },
      "shadows": { "sm": "...", "md": "...", ... }
    }
  file: templates/design_tokens/schema.json
  action: Create schema definition

3.2:
  name: Create default templates
  description: |
    Pre-built token sets:
    - Modern Dark (current Digi-TS style)
    - Clean Light
    - Custom (empty for user definition)
  files:
    - templates/design_tokens/default_dark.json
    - templates/design_tokens/default_light.json
  action: Create token files

3.3:
  name: Create design OS service
  description: |
    Methods:
    - load_tokens(template_name) → dict
    - save_tokens(project_id, tokens)
    - translate_to(tokens, framework) → code string
    Frameworks: react, vue, svelte, streamlit, css
  file: app/services/design_os_service.py
  action: Create new file

3.4:
  name: Create AI translation layer
  description: |
    Use LLM to convert abstract tokens to framework code.
    "Given these tokens, generate a React component library"
    "Given these tokens, generate Streamlit CSS"
  file: app/services/design_os_service.py
  action: Add translation methods with LLM calls

3.5:
  name: Create design studio UI
  description: |
    Visual editor for tokens:
    - Color pickers for color tokens
    - Sliders for spacing/radius
    - Font selectors for typography
    - Live preview of changes
    - Export to selected framework
  file: app/ui/design_os_panel.py
  action: Create new file

3.6:
  name: Wire design tokens to code generation
  description: |
    When generating UI code, include design tokens.
    Agent receives: "Use these design tokens: {...}"
    Output matches project's visual style.
  file: app/services/roundtable_service.py
  action: Include tokens in code generation prompts
```

**Acceptance Criteria:**
- [ ] Can create/edit design tokens
- [ ] Multiple pre-built templates available
- [ ] Can translate tokens to at least 3 frameworks
- [ ] Design studio shows live preview
- [ ] Generated code uses project tokens

---

### Phase 4: Auto-Qualification Gate

**Goal:** Every new agent instance automatically tested before joining work

**Files to Modify:**
```
app/services/agent_qualification_service.py   # Add auto-trigger
app/services/roundtable_service.py            # Wire qualification
app/ui/roundtable_panel.py                    # Show qualification status
```

**Tasks:**

```yaml
4.1:
  name: Create qualification trigger
  description: |
    Before any agent joins Roundtable execution:
    1. Check if qualified recently (cache)
    2. If not, run quick LIMB test
    3. Pass → allow to work
    4. Fail → request new instance
  file: app/services/agent_qualification_service.py
  action: Add auto_qualify() method

4.2:
  name: Wire qualification to execution
  description: |
    In Roundtable execute_round():
    - Before builder runs, qualify builder
    - Before voters run, qualify voters
    - Skip if qualified in last N hours
  file: app/services/roundtable_service.py
  action: Add qualification checks

4.3:
  name: Show qualification status in UI
  description: |
    Badge on each agent: ✓ Qualified | ⏳ Testing | ✗ Failed
    Show last qualification time.
    Button to re-qualify manually.
  file: app/ui/roundtable_panel.py
  action: Add status indicators

4.4:
  name: Handle qualification failure
  description: |
    On failure:
    1. Log the failure with details
    2. Notify user: "Agent X failed qualification"
    3. Offer: Use anyway (risky) | Get new instance
  file: app/services/roundtable_service.py
  action: Add failure handling flow

4.5:
  name: Add qualification cache
  description: |
    Cache results to avoid re-testing constantly.
    Config: qualification_cache_hours = 4
    Clear cache on model change.
  file: app/services/agent_qualification_service.py
  action: Add caching mechanism
```

**Acceptance Criteria:**
- [ ] Agents auto-qualify before execution
- [ ] Qualification status visible in UI
- [ ] Failed agents don't silently work
- [ ] Cache prevents excessive testing
- [ ] Manual re-qualification available

---

### Phase 5: Bulk RAG Import

**Goal:** Import knowledge from URLs and documents into RAG for agent injection

**Files to Create/Modify:**
```
app/services/knowledge_import_service.py   # Import orchestration
app/ui/knowledge_import_panel.py           # Import UI
app/services/rag_service.py                # Add bulk import
```

**Tasks:**

```yaml
5.1:
  name: Create knowledge import service
  description: |
    Orchestrates import from various sources:
    - URLs (single or batch)
    - Text files
    - Chat exports
    Returns structured content for RAG.
  file: app/services/knowledge_import_service.py
  action: Create new file

5.2:
  name: Add URL extraction
  description: |
    Fetch URL, parse HTML, extract:
    - Main content (skip nav/footer)
    - Sections with headings
    - Code blocks
    - Key terms
    Return structured JSON.
  file: app/services/knowledge_import_service.py
  action: Add extract_from_url() method

5.3:
  name: Add bulk import to RAG
  description: |
    Take structured content, embed it, store in ChromaDB.
    Categorize by: domain, project, type
    Make searchable for injection.
  file: app/services/rag_service.py
  action: Add bulk_import() method

5.4:
  name: Create import UI
  description: |
    Panel with:
    - URL input (single or paste list)
    - File upload
    - Import button with progress
    - Preview before confirming
    - Category selection
  file: app/ui/knowledge_import_panel.py
  action: Create new file

5.5:
  name: Wire knowledge to context injection
  description: |
    When agent executes, relevant knowledge is retrieved
    and injected alongside 3-layer context.
    "Here's relevant domain knowledge: ..."
  file: app/services/context_service.py
  action: Add knowledge retrieval to injection
```

**Acceptance Criteria:**
- [ ] Can import from URLs
- [ ] Can import from files
- [ ] Content searchable in RAG
- [ ] Knowledge injects into agent prompts
- [ ] Import progress visible in UI

---

### Phase 6: CLI Foundation

**Goal:** Create CLI interface that can control the system

**Files to Create:**
```
cli/__init__.py
cli/main.py               # Entry point
cli/commands/
  project.py              # Project commands
  agent.py                # Agent commands
  run.py                  # Execution commands
```

**Tasks:**

```yaml
6.1:
  name: Create CLI structure
  description: |
    Set up click-based CLI with command groups.
    Entry point: digts (or dts for short)
    Uses same services as Streamlit UI.
  files:
    - cli/__init__.py
    - cli/main.py
  action: Create CLI skeleton

6.2:
  name: Add project commands
  description: |
    digts project new <name>
    digts project list
    digts project open <name>
    digts project context show
    digts project context set <layer> <file>
  file: cli/commands/project.py
  action: Create project commands

6.3:
  name: Add agent commands
  description: |
    digts agent list
    digts agent add <name> --model <model>
    digts agent qualify <name>
    digts agent remove <name>
  file: cli/commands/agent.py
  action: Create agent commands

6.4:
  name: Add execution commands
  description: |
    digts run "<task prompt>"
    digts run --mode parallel "<task prompt>"
    digts run --file task.md
    Output streams to terminal.
  file: cli/commands/run.py
  action: Create run commands

6.5:
  name: Add to pyproject.toml
  description: |
    Register CLI entry point.
    pip install -e . enables digts command.
  file: pyproject.toml
  action: Add entry point configuration

6.6:
  name: Ensure CLI uses same backend
  description: |
    CLI imports same services as Streamlit.
    No duplicate logic.
    Database shared.
  file: cli/main.py
  action: Wire to existing services
```

**Acceptance Criteria:**
- [ ] `digts` command available after install
- [ ] Can manage projects from CLI
- [ ] Can manage agents from CLI
- [ ] Can run tasks from CLI
- [ ] Output streams properly
- [ ] Same backend as dashboard

---

## Execution Summary

| Phase | Name | Key Deliverable |
|-------|------|-----------------|
| 1 | 3-Layer Context | Standards/Product/Specs injected into agents |
| 2 | Unified Workspace | Roundtable + Parallel with mode toggle |
| 3 | Universal Design OS | Framework-agnostic tokens + translation |
| 4 | Auto-Qualification | LIMB test before every agent execution |
| 5 | Bulk RAG Import | URL/document knowledge → searchable memory |
| 6 | CLI Foundation | Terminal control of entire system |

**Build Order:** 1 → 2 → 3 → 4 → 5 → 6 (mostly sequential, some parallelizable)

**After This Build:** System is complete and usable. Next phase adds testing capabilities with AI-controlled test loops.
