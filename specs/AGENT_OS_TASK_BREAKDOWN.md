# Agent OS Task Breakdown: Ultimate Digi-TS Build

**Version:** 1.0
**Created:** 2024-12-24
**Purpose:** Agent OS formatted tasks for building the ultimate system

---

## Three-Layer Context

### Layer 1: Standards (Coding Standards)

```yaml
coding_standards:
  language: Python 3.10+
  framework: Streamlit
  style:
    - PEP 8 compliant
    - Type hints required
    - Docstrings (Google style)
  testing:
    - pytest for unit tests
    - Playwright for browser tests
  architecture:
    - Service layer pattern
    - Repository pattern for data
    - Dependency injection

naming:
  files: snake_case.py
  classes: PascalCase
  functions: snake_case
  constants: UPPER_SNAKE_CASE

imports:
  order:
    - Standard library
    - Third-party
    - Local imports
  style: absolute imports preferred
```

### Layer 2: Product (What We're Building)

```yaml
product_name: Digi-TS (Design Tree Studio)
description: |
  AI-powered software development platform that takes a rant/idea
  and produces working, tested software through multi-agent collaboration.

core_features:
  - Rant to crisp design transformation
  - Multi-agent coding (Roundtable)
  - Physical browser testing
  - Automatic error fixing
  - Knowledge memory (RAG)
  - Hallucination detection

user_types:
  power_users:
    interface: CLI
    needs: Speed, scripting, automation
  regular_users:
    interface: Dashboard (Streamlit)
    needs: Visual feedback, easy onboarding

key_flows:
  1_rant_to_design:
    input: Stream of consciousness text
    output: Structured design spec

  2_design_to_plan:
    input: Design spec
    output: Phased implementation plan

  3_plan_to_code:
    input: Phase tasks
    output: Working code files

  4_code_to_test:
    input: Code + test specs
    output: Test results + screenshots

  5_fix_loop:
    input: Failed test results
    output: Fixed code
```

### Layer 3: Specs (Technical Specifications)

```yaml
integrations:
  streamtest:
    purpose: Physical browser testing
    files:
      - browser_controller.py
      - physical_test_loop.py
      - gemini_client.py
    dependencies:
      - playwright
      - google-generativeai

  knowledge_extractor:
    purpose: Bulk RAG import
    files:
      - knowledge_extractor.py
      - smart_crawler.py
      - url_checker.py
    dependencies:
      - beautifulsoup4
      - requests

  design_os:
    purpose: Universal design tokens
    files:
      - design_os_service.py
      - token_translator.py
    outputs:
      - JSON design tokens
      - Framework-specific code

database:
  type: SQLite (dev), PostgreSQL (prod)
  orm: SQLAlchemy
  migrations: Alembic

api_models:
  - OpenAI (GPT-4, GPT-5)
  - Anthropic (Claude Opus 4.5)
  - Google (Gemini)
  - OpenRouter (fallback)
```

---

## Phase Breakdown

### Phase 1: StreamTest Integration

**Goal:** Enable physical browser testing with visual verification

```yaml
phase: 1
name: StreamTest Integration
priority: CRITICAL
estimated_tasks: 8
dependencies: []

acceptance_criteria:
  - Can launch browser and navigate to app URL
  - Can take screenshots and send to Gemini
  - Can execute click/type/scroll actions
  - Test results display in UI
  - Failed tests route to Roundtable

tasks:
  1.1:
    name: Copy browser controller
    action: Copy StreamTest browser_controller.py
    files:
      - FROM: /home/user/external/StreamTest/browser_controller.py
      - TO: /home/user/Digi-TS/app/services/browser_controller.py
    modifications:
      - Update imports for Digi-TS structure
      - Add config integration

  1.2:
    name: Create Gemini client
    action: Create vision client for screenshots
    files:
      - FROM: /home/user/external/StreamTest/gemini_client.py
      - TO: /home/user/Digi-TS/app/services/gemini_vision_client.py
    features:
      - get_action(screenshot, instruction)
      - assess_completion(screenshot, instruction)

  1.3:
    name: Create physical test loop
    action: Implement test execution loop
    files:
      - FROM: /home/user/external/StreamTest/agent_loop.py
      - TO: /home/user/Digi-TS/app/services/physical_test_loop.py
    features:
      - run_test_step(step, browser, gemini)
      - run_test_case(test_case, browser, gemini)
      - run_test_suite(suite, browser, gemini)

  1.4:
    name: Create test manual parser
    action: Parse markdown test manuals
    files:
      - FROM: /home/user/external/StreamTest/test_manual_parser.py
      - TO: /home/user/Digi-TS/app/services/test_manual_parser.py
    features:
      - parse_test_manual(file_path)
      - Extract test cases and steps

  1.5:
    name: Create physical testing service
    action: High-level service orchestrating tests
    files:
      - NEW: /home/user/Digi-TS/app/services/physical_testing_service.py
    features:
      - run_physical_tests(app_url, test_manual)
      - Integration with error loop

  1.6:
    name: Create test reporter
    action: Generate test reports
    files:
      - FROM: /home/user/external/StreamTest/reporter.py
      - TO: /home/user/Digi-TS/app/services/test_reporter.py
    features:
      - generate_report(results)
      - save_report(report)
      - Screenshots + pass/fail status

  1.7:
    name: Create physical testing panel
    action: Streamlit UI for physical tests
    files:
      - NEW: /home/user/Digi-TS/app/ui/physical_testing_panel.py
    features:
      - URL input
      - Test manual upload
      - Run button
      - Real-time progress
      - Results display

  1.8:
    name: Wire error loop to Roundtable
    action: Route failures back for fixing
    files:
      - MODIFY: /home/user/Digi-TS/app/services/physical_testing_service.py
      - MODIFY: /home/user/Digi-TS/app/services/roundtable_service.py
    features:
      - on_test_failure(results) → create fix round
      - Re-run tests after fix
```

---

### Phase 2: Knowledge Extractor Integration

**Goal:** Enable bulk knowledge import from URLs into RAG

```yaml
phase: 2
name: Knowledge Extractor Integration
priority: HIGH
estimated_tasks: 6
dependencies: []

acceptance_criteria:
  - Can check URL accessibility (green/yellow/red)
  - Can extract content from single URL
  - Can batch extract from multiple URLs
  - Extracted content imports to RAG
  - Progress shown during extraction

tasks:
  2.1:
    name: Copy knowledge extractor
    action: Copy core extraction logic
    files:
      - FROM: /home/user/external/Knowledge-Extractor/extractor.py
      - TO: /home/user/Digi-TS/app/services/knowledge_extractor.py
    modifications:
      - Update imports
      - Integrate with app config

  2.2:
    name: Copy URL checker
    action: Add accessibility checking
    files:
      - FROM: /home/user/external/Knowledge-Extractor/url_checker.py
      - TO: /home/user/Digi-TS/app/services/url_checker.py
    features:
      - check_url(url) → green/yellow/red
      - Cache for repeated checks

  2.3:
    name: Copy smart crawler
    action: Add link following
    files:
      - FROM: /home/user/external/Knowledge-Extractor/crawler.py
      - TO: /home/user/Digi-TS/app/services/smart_crawler.py
    features:
      - crawl_course(url, description)
      - Follow relevant links only

  2.4:
    name: Modify RAG service for bulk import
    action: Add batch import capability
    files:
      - MODIFY: /home/user/Digi-TS/app/services/rag_service.py
    features:
      - bulk_import(extractions)
      - Automatic categorization
      - Deduplication

  2.5:
    name: Create knowledge import panel
    action: Streamlit UI for imports
    files:
      - NEW: /home/user/Digi-TS/app/ui/knowledge_import_panel.py
    features:
      - URL input (single or list)
      - Accessibility check button
      - Extract button
      - Progress bar
      - Preview before import

  2.6:
    name: Add streaming progress
    action: Real-time extraction feedback
    files:
      - MODIFY: /home/user/Digi-TS/app/services/knowledge_extractor.py
    features:
      - Yield progress updates
      - Handle in UI with st.status
```

---

### Phase 3: Unified Workspace

**Goal:** Merge Roundtable and Parallel Chat into single workspace

```yaml
phase: 3
name: Unified Workspace
priority: HIGH
estimated_tasks: 5
dependencies: [Phase 1]

acceptance_criteria:
  - Single panel with mode toggle
  - Sequential mode = current Roundtable
  - Parallel mode = current Parallel Chat
  - Can switch modes mid-session
  - Shared agent pool

tasks:
  3.1:
    name: Create mode toggle component
    action: Add sequential/parallel toggle
    files:
      - MODIFY: /home/user/Digi-TS/app/ui/roundtable_panel.py
    features:
      - Toggle button in header
      - Session state for mode
      - Persist mode preference

  3.2:
    name: Merge agent display
    action: Unified agent results view
    files:
      - MODIFY: /home/user/Digi-TS/app/ui/roundtable_panel.py
    features:
      - Sequential: builder output, then votes
      - Parallel: side-by-side responses
      - Same visual styling

  3.3:
    name: Unify agent pool
    action: Shared agents across modes
    files:
      - MODIFY: /home/user/Digi-TS/app/services/roundtable_service.py
    features:
      - get_agents() for both modes
      - Mode-appropriate execution

  3.4:
    name: Add mode switching
    action: Switch modes without losing context
    files:
      - MODIFY: /home/user/Digi-TS/app/ui/roundtable_panel.py
    features:
      - Preserve task prompt
      - Preserve agent selection
      - Clear mode-specific state

  3.5:
    name: Deprecate parallel_chat_panel
    action: Remove separate panel
    files:
      - MODIFY: /home/user/Digi-TS/app/streamlit_app.py
    changes:
      - Remove parallel chat from sidebar
      - Update navigation
      - Redirect to unified workspace
```

---

### Phase 4: Design OS Layer

**Goal:** Add 3-layer context and universal design tokens

```yaml
phase: 4
name: Design OS Layer
priority: MEDIUM
estimated_tasks: 6
dependencies: []

acceptance_criteria:
  - Standards layer defined and used
  - Product layer captures features
  - Specs layer has technical details
  - Design tokens are framework-agnostic
  - Can translate tokens to React/Vue/Svelte

tasks:
  4.1:
    name: Create context structure
    action: Define 3-layer context format
    files:
      - NEW: /home/user/Digi-TS/app/services/design_os_service.py
    features:
      - DesignContext class
      - standards_layer
      - product_layer
      - specs_layer

  4.2:
    name: Create design token schema
    action: Universal token format
    files:
      - NEW: /home/user/Digi-TS/templates/design_tokens/schema.json
    tokens:
      - colors (primary, secondary, etc.)
      - typography (fonts, sizes)
      - spacing (margins, padding)
      - components (button, input, card)

  4.3:
    name: Create token translator
    action: Convert tokens to frameworks
    files:
      - NEW: /home/user/Digi-TS/app/services/token_translator.py
    features:
      - to_react(tokens)
      - to_vue(tokens)
      - to_svelte(tokens)
      - to_css(tokens)

  4.4:
    name: Create Design OS panel
    action: UI for managing design context
    files:
      - NEW: /home/user/Digi-TS/app/ui/design_os_panel.py
    features:
      - Edit 3 layers
      - Token editor
      - Framework preview

  4.5:
    name: Integrate with Agent OS
    action: Include context in agent prompts
    files:
      - MODIFY: /home/user/Digi-TS/app/services/agent_os_service.py
    features:
      - Inject standards into system prompt
      - Include product context
      - Reference specs

  4.6:
    name: Create token extraction
    action: Extract tokens from existing sites
    files:
      - NEW: /home/user/Digi-TS/app/services/token_extractor.py
    features:
      - Analyze CSS from URL
      - Extract color palette
      - Extract typography
```

---

### Phase 5: Hallucination Testing

**Goal:** Detect and prevent agent hallucinations during execution

```yaml
phase: 5
name: Hallucination Testing
priority: HIGH
estimated_tasks: 5
dependencies: [Phase 1, Phase 3]

acceptance_criteria:
  - Agents tested before joining
  - Periodic checks during execution
  - Failed agents flagged/replaced
  - Confidence scores visible
  - Logging of all checks

tasks:
  5.1:
    name: Create hallucination detector
    action: Core detection logic
    files:
      - NEW: /home/user/Digi-TS/app/services/hallucination_detector.py
    features:
      - pre_qualify(agent)
      - runtime_check(agent, context)
      - confidence_score(responses)

  5.2:
    name: Enhance LIMB test
    action: Add runtime test variants
    files:
      - MODIFY: /home/user/Digi-TS/app/services/agent_qualification_service.py
    features:
      - quick_check() - 2-3 questions
      - full_check() - all phases
      - contextual_check(domain)

  5.3:
    name: Add periodic checking to Roundtable
    action: Check agents during execution
    files:
      - MODIFY: /home/user/Digi-TS/app/services/roundtable_service.py
    features:
      - Check every N steps
      - Pause on failure
      - Agent replacement option

  5.4:
    name: Create confidence display
    action: Show agent reliability
    files:
      - MODIFY: /home/user/Digi-TS/app/ui/roundtable_panel.py
    features:
      - Confidence badge per agent
      - History of checks
      - Alerts on low confidence

  5.5:
    name: Add monitoring/logging
    action: Track all hallucination checks
    files:
      - MODIFY: /home/user/Digi-TS/app/services/hallucination_detector.py
    features:
      - Log all check results
      - Track patterns
      - Dashboard for monitoring
```

---

### Phase 6: CLI Interface

**Goal:** Add command-line interface for power users

```yaml
phase: 6
name: CLI Interface
priority: MEDIUM
estimated_tasks: 6
dependencies: [Phase 1, Phase 2, Phase 3]

acceptance_criteria:
  - digts command available
  - Can run full workflow from CLI
  - Config file support
  - Output formatting (JSON, table, plain)

tasks:
  6.1:
    name: Create CLI structure
    action: Set up click-based CLI
    files:
      - NEW: /home/user/Digi-TS/cli/__init__.py
      - NEW: /home/user/Digi-TS/cli/main.py
    dependencies:
      - click
      - rich (for output formatting)

  6.2:
    name: Implement core commands
    action: Add main workflow commands
    files:
      - NEW: /home/user/Digi-TS/cli/commands/rant.py
      - NEW: /home/user/Digi-TS/cli/commands/plan.py
      - NEW: /home/user/Digi-TS/cli/commands/code.py
      - NEW: /home/user/Digi-TS/cli/commands/test.py
    commands:
      - digts rant "Build a todo app"
      - digts plan
      - digts code --phase 1
      - digts test --physical

  6.3:
    name: Add config command
    action: Manage configuration
    files:
      - NEW: /home/user/Digi-TS/cli/commands/config.py
    commands:
      - digts config set key value
      - digts config get key
      - digts config list

  6.4:
    name: Add agent commands
    action: Manage agents from CLI
    files:
      - NEW: /home/user/Digi-TS/cli/commands/agent.py
    commands:
      - digts agent list
      - digts agent qualify <name>
      - digts agent add <name> --model <model>

  6.5:
    name: Add project commands
    action: Project management
    files:
      - NEW: /home/user/Digi-TS/cli/commands/project.py
    commands:
      - digts project new <name>
      - digts project list
      - digts project open <name>

  6.6:
    name: Create setup.py/pyproject.toml
    action: Enable pip install
    files:
      - MODIFY: /home/user/Digi-TS/pyproject.toml
    features:
      - Entry point: digts
      - Dependencies
      - Version management
```

---

## Execution Order

```
Week 1: Phase 1 (StreamTest) - CRITICAL for testing loop
Week 2: Phase 2 (Knowledge Extractor) - Bulk RAG import
Week 3: Phase 3 (Unified Workspace) - Merge UIs
Week 4: Phase 4 (Design OS) - 3-layer context
Week 5: Phase 5 (Hallucination Testing) - Agent reliability
Week 6: Phase 6 (CLI) - Power user interface
```

---

## Summary

Total Tasks: 36
Critical Path: Phase 1 → Phase 5 → Phase 3
Parallel Tracks: Phase 2, Phase 4 (can run alongside)

Key Files to Create:
- `app/services/browser_controller.py`
- `app/services/physical_testing_service.py`
- `app/services/knowledge_extractor.py`
- `app/services/design_os_service.py`
- `app/services/hallucination_detector.py`
- `cli/main.py`

Key Files to Modify:
- `app/ui/roundtable_panel.py` (mode toggle, confidence display)
- `app/services/roundtable_service.py` (unified execution, checks)
- `app/services/rag_service.py` (bulk import)
- `app/services/agent_os_service.py` (3-layer context)

*This is the roadmap. Execute phase by phase, test each phase, then proceed.*
