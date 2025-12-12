# Agent OS Blueprint: Roundtable Coder System

**Project:** Design Tree Studio - Roundtable Coder Module
**Version:** 1.0
**Priority:** CRITICAL - Build this first to bootstrap all other development
**Estimated Build Time:** 9-11 hours (depending on Playwright inclusion)

---

## CRITICAL CONTEXT FOR AGENTS

**READ THIS FIRST:**

This is a **self-bootstrapping system**. Once built, you will use this system to build everything else. The Roundtable Coder provides:

1. **Multiple AI agents** catching each other's mistakes (consensus-based coding)
2. **Infinite context** via Baton system (never lose project knowledge)
3. **Built-in testing** to catch bugs before they stack up
4. **Flexible experimentation** with adjustable everything

**Architecture Note:** This is a SEPARATE module from Design Tree's main functionality. They share:
- Same Streamlit app (different tab)
- Same database (separate tables with `roundtable_` prefix)
- Same Baton infrastructure (separate Baton chains)
- Same API keys

**Do NOT simplify this spec.** Build it exactly as documented.

---

# STANDARDS LAYER

## Technology Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Framework | Streamlit (Python 3.11+) | Existing app |
| AI Providers | Anthropic + OpenAI | Both required |
| Database | SQLAlchemy + SQLite | Same DB, separate tables |
| Context System | Baton | Existing, upgrade for flexibility |
| Testing | pytest, flake8, mypy, Playwright | Built-in testing system |
| Version Control | Git + GitHub API | Full operations |

## Available AI Models

```python
AVAILABLE_MODELS = {
    # Anthropic
    "Opus 4.5": {
        "id": "claude-opus-4-5-20250101",
        "provider": "anthropic",
        "max_tokens": 200000,
        "cost_per_1k_input": 0.015,
        "cost_per_1k_output": 0.075
    },
    "Sonnet 4.5": {
        "id": "claude-sonnet-4-5-20250929",
        "provider": "anthropic",
        "max_tokens": 200000,
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015
    },
    "Sonnet 3.5": {
        "id": "claude-3-5-sonnet-20241022",
        "provider": "anthropic",
        "max_tokens": 200000,
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015
    },
    # OpenAI
    "GPT-4 Turbo": {
        "id": "gpt-4-turbo-preview",
        "provider": "openai",
        "max_tokens": 128000,
        "cost_per_1k_input": 0.01,
        "cost_per_1k_output": 0.03
    },
    "GPT-4o": {
        "id": "gpt-4o",
        "provider": "openai",
        "max_tokens": 128000,
        "cost_per_1k_input": 0.005,
        "cost_per_1k_output": 0.015
    },
    "GPT-4o Mini": {
        "id": "gpt-4o-mini",
        "provider": "openai",
        "max_tokens": 128000,
        "cost_per_1k_input": 0.00015,
        "cost_per_1k_output": 0.0006
    },
}
```

## Architecture

```
design-tree-studio/
├── app/
│   ├── core/
│   │   └── models.py              # MODIFY - Add roundtable models
│   ├── services/
│   │   ├── baton_service.py       # EXISTING - Upgrade for flexibility
│   │   ├── roundtable_service.py  # NEW - Core roundtable logic
│   │   ├── agent_pool_service.py  # NEW - Manage agent instances
│   │   ├── testing_service.py     # NEW - Automated testing
│   │   └── github_service.py      # NEW - GitHub operations
│   ├── ui/
│   │   ├── roundtable_panel.py    # NEW - Main roundtable UI
│   │   ├── testing_panel.py       # NEW - Testing UI
│   │   └── layout.py              # MODIFY - Add roundtable tab
│   └── tests/
│       ├── test_roundtable.py     # NEW - Unit tests
│       └── playwright/            # NEW - UI tests
│           ├── test_app_loads.py
│           ├── test_roundtable_config.py
│           └── test_execution_flow.py
├── streamlit_app.py               # MODIFY - Add roundtable tab
└── requirements.txt               # MODIFY - Add testing deps
```

## Coding Conventions

### Python Style
- Python 3.11+ features allowed
- Type hints on ALL function signatures
- Docstrings for all public functions
- Max line length: 100 characters
- Follow PEP 8 with flake8 enforcement

### Error Handling
```python
# ALWAYS use try/except for external calls
try:
    response = client.messages.create(...)
except anthropic.APIError as e:
    logger.error(f"Anthropic API error: {e}")
    raise RoundtableServiceError(f"Failed to call agent: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### Service Pattern
```python
# Services are initialized with dependencies
class RoundtableService:
    def __init__(self, db: Session, config: Config):
        self.db = db
        self.config = config

    def create_session(self, project_id: int, name: str) -> RoundtableSession:
        """Create a new roundtable session.

        Args:
            project_id: The project this session belongs to
            name: Human-readable session name

        Returns:
            The created RoundtableSession object

        Raises:
            RoundtableServiceError: If session creation fails
        """
        # Implementation
```

### Database Models
```python
# Use SQLAlchemy declarative base
# Prefix all roundtable tables with 'roundtable_'
class RoundtableSession(Base):
    __tablename__ = "roundtable_sessions"

    id = Column(Integer, primary_key=True)
    # ... fields with proper types and constraints
```

---

# PRODUCT LAYER

## Vision

A multi-agent coding collaboration system where multiple AI instances work together, vote on each other's code, and maintain infinite context through the Baton system. This system is used to build itself and all future features of Design Tree Studio.

**Core Value Proposition:**
- Single agent = single point of failure (hallucinations, mistakes, blind spots)
- Multiple agents = consensus-based quality assurance
- Baton system = never lose project context again
- Built-in testing = catch bugs before they stack up

## Target Users

1. **Vibe Coders** - Non-traditional developers who work with AI to build software
2. **Quality-Focused Builders** - Anyone who wants consensus before committing code
3. **Complex Project Builders** - Projects too big for a single context window
4. **AI Tool Developers** - Building and testing AI-assisted development tools

## Core Use Cases

### Use Case 1: Build with Consensus
```
User sets up build task
    │
    ▼
Agent 1 (Builder) writes code
    │
    ▼
Agents 2-5 (Voters) review and vote
    │
    ├── Consensus reached → Accept code
    │
    └── No consensus → Builder revises → Re-vote
```

### Use Case 2: Test Different Approaches
```
Same prompt sent to 3 different models
    │
    ├── Opus 4.5 response
    ├── GPT-4o response
    └── Sonnet 4.5 response
    │
    ▼
Compare outputs, pick best approach
```

### Use Case 3: Continuous Building
```
Round 1: Build feature A
    │ (Baton carries context)
    ▼
Round 2: Review and revise
    │ (Baton carries context)
    ▼
Round 3: Build feature B
    │ (Baton carries context)
    ▼
... continues indefinitely
```

### Use Case 4: Learn What Works
```
Track agent performance over time
    │
    ├── Which models build best?
    ├── Which models catch most bugs?
    └── What prompt patterns work?
    │
    ▼
Optimize roundtable compositions
```

## Roadmap

### Phase 1: Core Roundtable (This Build)
- Multi-agent sessions with voting
- Baton integration for context persistence
- Built-in testing (Tier 1 + 2)
- GitHub integration
- All settings adjustable

### Phase 2: Enhancement (Future)
- Playwright UI testing
- Advanced agent performance analytics
- Template marketplace
- Multi-project support

### Phase 3: Full Marisol Integration (Future)
- Autonomous coding with human oversight
- Self-improving prompts
- Cross-project learning

---

# SPECS LAYER

## Feature Overview

### Roundtable Coder

A new tab in Design Tree Studio that enables multi-agent collaboration with:
- Configurable rounds with multiple agents
- Voting and consensus system
- Master prompts and guardrails
- Baton integration for infinite context
- Built-in automated testing
- GitHub integration for version control
- Full audit logging

---

## UI Components

### 1. Master Configuration Panel

Controls that apply to all agents and the entire session.

```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ MASTER CONFIGURATION                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ MASTER SYSTEM PROMPT (applies to all agents):               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Large editable text area - see Default Master Prompt]  │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [Save] [Load Default] [Push to All Agents]                  │
│                                                             │
│ MASTER GUARDRAILS (rules all agents must follow):           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Large editable text area - see Default Guardrails]     │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [Save] [Load Default] [Push to All Agents]                  │
│                                                             │
│ API KEYS                                                    │
│ Anthropic: [••••••••••••••••] [Test Connection]            │
│ OpenAI:    [••••••••••••••••] [Test Connection]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Advanced Settings Panel

ALL settings are adjustable - NO hardcoded values.

```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ ADVANCED SETTINGS                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ CONTEXT MANAGEMENT                                          │
│ ├─ Context Window Target: [====●=====] 40%                 │
│ │  (Slider: 20% - 60% of model max)                        │
│ ├─ Auto-Baton Trigger:    [====●=====] 80%                 │
│ │  (Slider: 50% - 95% of target)                           │
│ └─ Context Health Display: [✓] Show percentage             │
│                                                             │
│ EXECUTION MODE                                              │
│ ├─ Agent Execution:  ○ Sequential  ● Parallel              │
│ ├─ Revise Flow:      ● Automatic   ○ Manual                │
│ └─ Auto-Loop:        [✓] Loop until consensus              │
│                                                             │
│ VOTING                                                      │
│ ├─ Approval Threshold: [======●===] 66%                    │
│ └─ Require Explanation: [✓] Voters must explain            │
│                                                             │
│ SAFETY                                                      │
│ ├─ Auto-Checkpoint:   [✓] Every [15] minutes               │
│ ├─ Max Revisions:     [5] before forcing manual review     │
│ └─ Timeout per Agent: [120] seconds                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Context Health Indicator

Always-visible display showing context usage as percentage.

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 CONTEXT HEALTH                              [Always On]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ████████████░░░░░░░░░░░░░░░░░░ 42% used                    │
│                                                             │
│ Model: Opus 4.5 (200k max)                                  │
│ Target: 40% = 80,000 tokens                                 │
│ Current: 33,600 tokens                                      │
│ Remaining: 46,400 tokens                                    │
│                                                             │
│ Status: 🟢 Healthy                                          │
│ Baton recommended in: ~12 more exchanges                    │
│                                                             │
│ [Trigger Baton Now] [View Context History]                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Status Colors:
🟢 Green (0-60%): Healthy
🟡 Yellow (60-80%): Caution - consider checkpoint
🔴 Red (80%+): Critical - Baton trigger imminent
```

### 4. Round Configuration Panel

Configure multiple rounds, each with multiple agents.

```
┌─────────────────────────────────────────────────────────────┐
│ 🔄 ROUNDS                                      [+ Add Round]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ROUND 1: Build                            [Delete] [▲▼] │ │
│ │                                                         │ │
│ │ Task Prompt:                                            │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ [Editable task description for this round]        │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ │                                                         │ │
│ │ AGENTS IN THIS ROUND:                    [+ Add Agent]  │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ Agent 1                                           │   │ │
│ │ │ Model: [Opus 4.5        ▼]                        │   │ │
│ │ │ Role:  [Builder         ▼]                        │   │ │
│ │ │ Prompt Override: [Use master ▼] [Edit]            │   │ │
│ │ │ [Remove Agent]                                    │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ Agent 2                                           │   │ │
│ │ │ Model: [Opus 4.5        ▼] (different instance)   │   │ │
│ │ │ Role:  [Voter           ▼]                        │   │ │
│ │ │ Prompt Override: [Use master ▼] [Edit]            │   │ │
│ │ │ [Remove Agent]                                    │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ Agent 3                                           │   │ │
│ │ │ Model: [GPT-4o          ▼]                        │   │ │
│ │ │ Role:  [Voter           ▼]                        │   │ │
│ │ │ Prompt Override: [Use master ▼] [Edit]            │   │ │
│ │ │ [Remove Agent]                                    │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ TEMPLATES                                                   │
│ [Save as Template] [Load Template ▼]                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Agent Roles:**
- `Builder` - Writes code based on task prompt
- `Voter` - Reviews code, votes approve/reject with explanation
- `Reviewer` - Provides detailed review without voting

### 5. Execution Panel

Controls for running rounds and viewing progress.

```
┌─────────────────────────────────────────────────────────────┐
│ ▶️ EXECUTION                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Current: Round 1 of 2                                       │
│ Status: Ready to execute                                    │
│                                                             │
│ [▶ Run Current Round] [⏭ Skip] [🔄 Restart All]            │
│ [⏸ Pause After Each Agent] [🔁 Auto-Loop Until Consensus]  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ PROGRESS                                                    │
│ Agent 1 (Builder): ✅ Complete (45s)                        │
│ Agent 2 (Voter):   🔄 Running... (12s)                      │
│ Agent 3 (Voter):   ⏳ Waiting                               │
│                                                             │
│ Estimated cost this round: $0.45                            │
│ Total session cost: $1.23                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6. Results Panel

Display agent outputs and voting results.

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 RESULTS - Round 1                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ AGENT 1 (Opus 4.5) - BUILDER                           │ │
│ │ Time: 45s | Tokens: 2,340 | Cost: $0.28                │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ [Code output with syntax highlighting]            │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ │ [Copy Code] [View Full] [Apply to Codebase]            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ AGENT 2 (Opus 4.5) - VOTER                    👍 APPROVE│ │
│ │ Time: 23s | Tokens: 890 | Cost: $0.09                  │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ [Vote explanation and feedback]                   │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ AGENT 3 (GPT-4o) - VOTER                      👎 REJECT│ │
│ │ Time: 18s | Tokens: 1,120 | Cost: $0.08                │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ [Vote explanation with specific issues]           │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ═══════════════════════════════════════════════════════════ │
│ CONSENSUS: 1/2 voters approved (50%) - BELOW THRESHOLD (66%)│
│                                                             │
│ [🔄 Revise & Re-vote] [✅ Override & Accept] [❌ Reject]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7. Testing Panel

Built-in automated testing system.

```
┌─────────────────────────────────────────────────────────────┐
│ 🧪 TESTING                                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ AUTO-TEST SETTINGS                                          │
│ [✓] Run tests after each build                             │
│ [✓] Block voting until tests pass                          │
│ [✓] Auto-send failures to builder                          │
│                                                             │
│ TESTS TO RUN                                                │
│ ┌─ Tier 1 (Fast ~5-30s) ──────────────────────────────────┐ │
│ │ [✓] Syntax Check        [✓] Linting (flake8)           │ │
│ │ [✓] Import Validation   [✓] Type Check (mypy)          │ │
│ │ [✓] Unit Tests (pytest)                                │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─ Tier 2 (Medium ~30-60s) ───────────────────────────────┐ │
│ │ [✓] App Start Test      [✓] Database Tests             │ │
│ │ [✓] Dependency Check    [ ] Security Scan (bandit)     │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─ Tier 3 (UI - Playwright) ──────────────────────────────┐ │
│ │ [ ] App loads correctly [ ] Forms work                 │ │
│ │ [ ] All tabs accessible [ ] Screenshot comparison      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [▶ Run Selected] [▶ Run All]                               │
│                                                             │
│ RESULTS: ⚠️ 6/8 PASSED (23.4s)                             │
│ ├─ ✅ Syntax Check       ├─ ✅ App Start                   │
│ ├─ ✅ Imports            ├─ ✅ Database                    │
│ ├─ ⚠️ Linting (3 warn)  ├─ ✅ Dependencies                │
│ ├─ ✅ Type Check         └─ ❌ Unit Tests (2 failed)      │
│                                                             │
│ [View Details] [Send Failures to Builder]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8. GitHub Integration Panel

Full Git operations and baseline management.

```
┌─────────────────────────────────────────────────────────────┐
│ 🐙 GITHUB INTEGRATION                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ CONNECTED REPOSITORIES                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ● design-tree-studio (active)                          │ │
│ │   Branch: main | Last sync: 5 min ago                  │ │
│ │   [Switch Branch ▼] [Pull] [Push] [View Diff]          │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [+ Connect New Repository]                                  │
│                                                             │
│ BASELINE MANAGEMENT                                         │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Current Baseline: v0.5.0-roundtable-start              │ │
│ │ Created: 2024-01-15 10:30 AM                           │ │
│ │                                                         │ │
│ │ [Create New Baseline] [Restore to Baseline]            │ │
│ │ [Copy Baseline to New Branch]                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Baseline History:                                           │
│ • v0.5.0-roundtable-start (current)                        │
│ • v0.4.0-agent-os-complete                                 │
│ • v0.3.0-baton-system                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 9. Checkpoints Panel

Auto-save and recovery system.

```
┌─────────────────────────────────────────────────────────────┐
│ 💾 CHECKPOINTS                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Auto-Checkpoint: [✓] Every [15] minutes                    │
│                                                             │
│ Recent Checkpoints:                                         │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ● 10:45 AM - After Round 3 complete                    │ │
│ │   Context: 38% | Status: Consensus reached             │ │
│ │   [Restore] [View] [Delete]                            │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ ● 10:30 AM - After Round 2 complete                    │ │
│ │   Context: 29% | Status: Consensus reached             │ │
│ │   [Restore] [View] [Delete]                            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Create Manual Checkpoint] [Export All]                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 10. Handoff Generator Panel

Auto-generate handoff documents for session continuity.

```
┌─────────────────────────────────────────────────────────────┐
│ 📋 HANDOFF GENERATOR                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Auto-Generate: [✓] At 70% context                          │
│                                                             │
│ Include in Handoff:                                         │
│ [✓] Session summary          [✓] Test results              │
│ [✓] What was built           [✓] Agent performance         │
│ [✓] What's remaining         [✓] Code diff                 │
│ [✓] Current issues                                          │
│                                                             │
│ [Generate Now] [Copy] [Save to File]                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 11. Import Design Tree Context

Pull specs from Design Tree projects into Roundtable sessions.

```
┌─────────────────────────────────────────────────────────────┐
│ 📥 IMPORT DESIGN TREE CONTEXT                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Available Projects:                                         │
│ ○ Design Tree Studio v2 (45 nodes)                         │
│ ● Marisol AI System (128 nodes) [selected]                 │
│ ○ E-commerce Platform (67 nodes)                           │
│                                                             │
│ Import Options:                                             │
│ [✓] Project overview     [✓] Technical requirements        │
│ [✓] Component specs      [ ] Full conversation history     │
│ [✓] Truth Doc export                                        │
│                                                             │
│ Preview: 12,450 tokens will be added                        │
│                                                             │
│ [Import Selected]                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 12. Agent Performance Panel

Track which models perform best over time.

```
┌─────────────────────────────────────────────────────────────┐
│ 📈 AGENT PERFORMANCE                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ BUILDER PERFORMANCE (acceptance rate)                       │
│ Opus 4.5      ████████████████████░░░░ 87% (26/30)         │
│ Sonnet 4.5    ██████████████████░░░░░░ 78% (18/23)         │
│ GPT-4o        ████████████████░░░░░░░░ 72% (13/18)         │
│                                                             │
│ VOTER PERFORMANCE (issues caught)                           │
│ GPT-4o        ████████████████████████ 34 issues           │
│ Opus 4.5      ██████████████████░░░░░░ 28 issues           │
│ Sonnet 4.5    ████████████████░░░░░░░░ 22 issues           │
│                                                             │
│ BEST COMBINATION                                            │
│ Builder: Opus 4.5 + Voters: GPT-4o, Sonnet 4.5             │
│ Success: 94% | Avg revisions: 1.2                          │
│                                                             │
│ [Export] [Reset] [Full History]                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 13. Audit Log Panel

Complete history of all actions for learning and debugging.

```
┌─────────────────────────────────────────────────────────────┐
│ 📜 AUDIT LOG                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Filter: [All Rounds ▼] [All Agents ▼] [All Outcomes ▼]     │
│                                                             │
│ 10:45:23 | Round 1 | Agent 1 (Opus) | BUILD | 2,340 tokens │
│ 10:46:08 | Round 1 | Agent 2 (Opus) | VOTE: 👍 | 890 tkns  │
│ 10:46:26 | Round 1 | Agent 3 (GPT)  | VOTE: 👎 | 1,120 tkns│
│ 10:46:27 | Round 1 | CONSENSUS: FAIL (50% < 66%)           │
│ 10:47:15 | Round 1 | Agent 1 (Opus) | REVISE | 1,890 tkns  │
│ 10:47:45 | Round 1 | Agent 2 (Opus) | VOTE: 👍 | 450 tkns  │
│ 10:48:02 | Round 1 | Agent 3 (GPT)  | VOTE: 👍 | 380 tkns  │
│ 10:48:03 | Round 1 | CONSENSUS: PASS (100% >= 66%)         │
│                                                             │
│ STATISTICS                                                  │
│ Total Rounds: 5 | Revisions: 3 | Avg Consensus: 1.6        │
│ Total Cost: $4.56 | Total Tokens: 34,560                   │
│                                                             │
│ [Export] [Clear] [View Statistics]                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Models

```python
# Add to app/core/models.py

from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime

class SessionStatus(PyEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class AgentRole(PyEnum):
    BUILDER = "builder"
    VOTER = "voter"
    REVIEWER = "reviewer"

class VoteType(PyEnum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


class RoundtableSession(Base):
    """A roundtable coding session with multiple rounds."""
    __tablename__ = "roundtable_sessions"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    name = Column(String(255), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    master_prompt = Column(Text)
    master_guardrails = Column(Text)
    voting_threshold = Column(Float, default=0.66)
    context_target_percent = Column(Float, default=0.40)
    auto_baton_trigger_percent = Column(Float, default=0.80)
    execution_mode = Column(String(20), default="sequential")  # sequential, parallel
    revise_mode = Column(String(20), default="automatic")  # automatic, manual
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rounds = relationship("RoundtableRound", back_populates="session", cascade="all, delete-orphan")
    checkpoints = relationship("RoundtableCheckpoint", back_populates="session", cascade="all, delete-orphan")


class RoundtableRound(Base):
    """A single round within a session."""
    __tablename__ = "roundtable_rounds"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("roundtable_sessions.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    name = Column(String(255))
    task_prompt = Column(Text)
    status = Column(String(50), default="pending")  # pending, running, completed
    consensus_reached = Column(Boolean, default=False)
    consensus_percentage = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    session = relationship("RoundtableSession", back_populates="rounds")
    agents = relationship("RoundtableAgent", back_populates="round", cascade="all, delete-orphan")


class RoundtableAgent(Base):
    """An agent configured for a specific round."""
    __tablename__ = "roundtable_agents"

    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("roundtable_rounds.id"), nullable=False)
    agent_order = Column(Integer, default=0)
    model = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)  # anthropic, openai
    role = Column(Enum(AgentRole), nullable=False)
    prompt_override = Column(Text, nullable=True)
    use_master_prompt = Column(Boolean, default=True)

    round = relationship("RoundtableRound", back_populates="agents")
    responses = relationship("RoundtableResponse", back_populates="agent", cascade="all, delete-orphan")


class RoundtableResponse(Base):
    """A response from an agent."""
    __tablename__ = "roundtable_responses"

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("roundtable_agents.id"), nullable=False)
    iteration = Column(Integer, default=1)  # For revisions
    content = Column(Text)
    vote = Column(Enum(VoteType), nullable=True)
    vote_reason = Column(Text, nullable=True)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("RoundtableAgent", back_populates="responses")


class RoundtableCheckpoint(Base):
    """A saved checkpoint for recovery."""
    __tablename__ = "roundtable_checkpoints"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("roundtable_sessions.id"), nullable=False)
    name = Column(String(255))
    context_percentage = Column(Float)
    session_state = Column(Text)  # JSON serialized state
    is_auto = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("RoundtableSession", back_populates="checkpoints")


class RoundtableTemplate(Base):
    """Saved round configurations for reuse."""
    __tablename__ = "roundtable_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_data = Column(Text)  # JSON serialized configuration
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentPerformance(Base):
    """Track agent performance over time."""
    __tablename__ = "roundtable_agent_performance"

    id = Column(Integer, primary_key=True)
    model = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    total_tasks = Column(Integer, default=0)
    successful_tasks = Column(Integer, default=0)
    issues_caught = Column(Integer, default=0)  # For voters
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## Service Layer

### RoundtableService

```python
# app/services/roundtable_service.py

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import anthropic
import openai

class RoundtableService:
    """Core service for managing roundtable sessions."""

    def __init__(self, db: Session, anthropic_key: str = None, openai_key: str = None):
        self.db = db
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key) if anthropic_key else None
        self.openai_client = openai.OpenAI(api_key=openai_key) if openai_key else None

    # Session Management
    def create_session(self, name: str, project_id: int = None) -> RoundtableSession:
        """Create a new roundtable session."""
        pass

    def get_session(self, session_id: int) -> RoundtableSession:
        """Get a session by ID."""
        pass

    def update_session_settings(self, session_id: int, settings: Dict) -> RoundtableSession:
        """Update session settings."""
        pass

    # Round Management
    def add_round(self, session_id: int, name: str, task_prompt: str) -> RoundtableRound:
        """Add a round to a session."""
        pass

    def remove_round(self, round_id: int) -> bool:
        """Remove a round."""
        pass

    def reorder_rounds(self, session_id: int, round_ids: List[int]) -> bool:
        """Reorder rounds in a session."""
        pass

    # Agent Management
    def add_agent(self, round_id: int, model: str, role: str, prompt_override: str = None) -> RoundtableAgent:
        """Add an agent to a round."""
        pass

    def remove_agent(self, agent_id: int) -> bool:
        """Remove an agent."""
        pass

    def update_agent(self, agent_id: int, updates: Dict) -> RoundtableAgent:
        """Update agent configuration."""
        pass

    # Execution
    def execute_round(self, round_id: int, baton_context: str = None) -> Dict:
        """Execute all agents in a round."""
        pass

    def call_agent(self, agent: RoundtableAgent, prompt: str, context: str) -> RoundtableResponse:
        """Make API call to a single agent."""
        pass

    def calculate_consensus(self, round_id: int) -> Dict:
        """Calculate voting consensus for a round."""
        pass

    def revise_and_revote(self, round_id: int, feedback: List[str]) -> Dict:
        """Send feedback to builder and re-run voting."""
        pass

    # Templates
    def save_template(self, session_id: int, name: str, description: str = None) -> RoundtableTemplate:
        """Save current configuration as template."""
        pass

    def load_template(self, template_id: int, session_id: int) -> bool:
        """Load template into session."""
        pass

    # Checkpoints
    def create_checkpoint(self, session_id: int, name: str = None, is_auto: bool = False) -> RoundtableCheckpoint:
        """Create a checkpoint."""
        pass

    def restore_checkpoint(self, checkpoint_id: int) -> bool:
        """Restore session to checkpoint."""
        pass

    # Performance Tracking
    def update_performance(self, model: str, role: str, success: bool, tokens: int, cost: float, issues_caught: int = 0):
        """Update agent performance stats."""
        pass

    def get_performance_stats(self) -> Dict:
        """Get all performance statistics."""
        pass
```

### TestingService

```python
# app/services/testing_service.py

import subprocess
import ast
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"

@dataclass
class TestResult:
    name: str
    status: TestStatus
    duration: float
    message: Optional[str] = None
    details: Optional[List[str]] = None

class TestingService:
    """Automated testing service for roundtable code."""

    def __init__(self, project_path: str):
        self.project_path = project_path

    # Tier 1: Basic Tests
    def run_syntax_check(self, code: str) -> TestResult:
        """Validate Python syntax."""
        pass

    def run_import_check(self, filepath: str) -> TestResult:
        """Verify all imports resolve."""
        pass

    def run_linting(self, filepath: str) -> TestResult:
        """Run flake8 linting."""
        pass

    def run_type_check(self, filepath: str) -> TestResult:
        """Run mypy type checking."""
        pass

    def run_unit_tests(self, test_path: str = "tests/") -> TestResult:
        """Run pytest unit tests."""
        pass

    # Tier 2: Intermediate Tests
    def run_app_start_test(self, app_file: str, timeout: int = 30) -> TestResult:
        """Verify app starts without crash."""
        pass

    def run_dependency_check(self) -> TestResult:
        """Verify all requirements installed."""
        pass

    def run_security_scan(self, filepath: str) -> TestResult:
        """Run bandit security scan."""
        pass

    # Tier 3: Playwright
    def run_playwright_tests(self, test_files: List[str]) -> List[TestResult]:
        """Run Playwright UI tests."""
        pass

    # Master Runner
    def run_all_tests(self, tiers: List[int], code: str = None, filepath: str = None) -> Dict:
        """Run all enabled tests."""
        pass
```

---

## Default Prompts

### Default Master Prompt

```
You are an expert software developer working on Design Tree Studio.

PROJECT CONTEXT:
Design Tree Studio is a Streamlit application that helps users organize design projects
and generate documentation through AI-assisted conversations. Key features:
- Node-based project organization
- AI chat with OpenAI/Anthropic integration
- Baton system for context persistence
- Auto-detection of components from conversations
- Truth Doc export

TECH STACK:
- Python 3.11+
- Streamlit for UI
- SQLAlchemy for database
- OpenAI/Anthropic APIs for AI

CODING STANDARDS:
- Use type hints on all function signatures
- Include docstrings for public functions
- Handle errors with try/except
- Follow existing patterns in the codebase
- Use services layer for business logic
- Use models for data structures
- Max line length: 100 characters

YOUR TASK:
Follow the specific task prompt provided. Write production-quality code that integrates
cleanly with the existing codebase.
```

### Default Guardrails

```
ABSOLUTE RULES - NEVER VIOLATE:

1. SCOPE: Only modify files explicitly mentioned in the task
2. PRESERVATION: Never delete existing code without explicit instruction
3. IMPORTS: Preserve all existing imports, add new ones as needed
4. SECRETS: Never hardcode API keys, passwords, or secrets
5. ERRORS: Always include error handling (try/except)
6. TESTING: Mentally test your code before submitting
7. PATTERNS: Follow existing patterns in the codebase
8. DOCUMENTATION: Add docstrings to new public functions
9. TYPES: Include type hints on function signatures
10. CLARITY: If requirements are unclear, state assumptions explicitly

VOTING RULES (for voters):
- APPROVE only if code is production-ready
- REJECT if there are bugs, missing error handling, or security issues
- Always explain your vote with specific references to the code
- Be constructive - explain HOW to fix issues
```

---

## Build Phases

### Build Protocol

**CRITICAL:** After EACH phase, run the test protocol before moving to the next phase.

```
Phase N
   │
   ├── Build the code
   │
   ├── Run tests:
   │   ├── Syntax check
   │   ├── Import check
   │   ├── Unit tests for this phase
   │   └── App start test
   │
   ├── Fix any failures
   │
   └── Only then proceed to Phase N+1
```

### Phase A: Database & Models (30 min)

**Tasks:**
1. Add all roundtable models to `app/core/models.py`
2. Create database migration
3. Test model creation

**Test Criteria:**
- [ ] Can create RoundtableSession
- [ ] Can create RoundtableRound with agents
- [ ] Can create RoundtableResponse
- [ ] Can create RoundtableCheckpoint
- [ ] Can create RoundtableTemplate
- [ ] Can create AgentPerformance
- [ ] All relationships work correctly

---

### Phase B: Core Service - Basic Operations (1 hour)

**Tasks:**
1. Create `app/services/roundtable_service.py`
2. Implement AVAILABLE_MODELS constant
3. Implement create_session, get_session, update_session_settings
4. Implement add_round, remove_round
5. Implement add_agent, remove_agent, update_agent

**Test Criteria:**
- [ ] Can create session with all settings
- [ ] Can add/remove rounds
- [ ] Can add/remove/update agents
- [ ] Settings persist correctly

---

### Phase C: Execution Engine (1 hour)

**Tasks:**
1. Implement call_agent (single API call to Anthropic/OpenAI)
2. Implement execute_round (run all agents)
3. Implement calculate_consensus
4. Add timeout handling
5. Add error recovery

**Test Criteria:**
- [ ] Can make API call to Anthropic
- [ ] Can make API call to OpenAI
- [ ] Sequential execution works
- [ ] Parallel execution works
- [ ] Consensus calculation correct
- [ ] Timeouts handled gracefully

---

### Phase D: Basic UI (1 hour)

**Tasks:**
1. Create `app/ui/roundtable_panel.py`
2. Add "Roundtable" tab to main app
3. Implement Master Configuration panel
4. Implement Advanced Settings panel
5. Implement Round Configuration panel (add/remove rounds, agents)

**Test Criteria:**
- [ ] Roundtable tab appears
- [ ] Can edit master prompt
- [ ] Can adjust all settings
- [ ] Can add/remove rounds
- [ ] Can add/remove agents
- [ ] Settings save correctly

---

### Phase E: Execution UI (45 min)

**Tasks:**
1. Implement Execution panel with run controls
2. Show progress during execution
3. Implement Results panel with code display
4. Show voting results and consensus
5. Add action buttons (revise, accept, reject)

**Test Criteria:**
- [ ] Run button executes round
- [ ] Progress updates in real-time
- [ ] Results display with syntax highlighting
- [ ] Votes display correctly
- [ ] Consensus calculated and shown
- [ ] Action buttons work

---

### Phase F: Baton Integration (45 min)

**Tasks:**
1. Inject Baton context into agent calls
2. Save round results back to Baton
3. Implement context window percentage tracking
4. Implement auto-baton trigger
5. Add Context Health Indicator

**Test Criteria:**
- [ ] Baton context passed to agents
- [ ] Results saved to Baton
- [ ] Context percentage displays correctly
- [ ] Auto-baton triggers at threshold
- [ ] Health indicator updates

---

### Phase G: Master Prompt System (30 min)

**Tasks:**
1. Implement master prompt persistence
2. Implement "Push to All Agents" function
3. Implement per-agent prompt override
4. Add default prompts
5. Add guardrails system

**Test Criteria:**
- [ ] Master prompt saves/loads
- [ ] Push to all agents works
- [ ] Individual overrides work
- [ ] Defaults load correctly
- [ ] Guardrails apply to all agents

---

### Phase H: GitHub Integration (1 hour)

**Tasks:**
1. Create `app/services/github_service.py`
2. Implement repo connection
3. Implement branch listing/switching
4. Implement pull/push operations
5. Implement baseline create/restore/copy

**Test Criteria:**
- [ ] Can connect to repo
- [ ] Can list/switch branches
- [ ] Can pull/push
- [ ] Can create baseline
- [ ] Can restore to baseline
- [ ] Can copy baseline to new branch

---

### Phase I: Checkpoints & Handoffs (45 min)

**Tasks:**
1. Implement auto-checkpoint system
2. Implement manual checkpoint creation
3. Implement checkpoint restoration
4. Implement handoff document generator
5. Add checkpoint/handoff UI panels

**Test Criteria:**
- [ ] Auto-checkpoint triggers on interval
- [ ] Manual checkpoint works
- [ ] Restore restores full state
- [ ] Handoff document generates correctly
- [ ] Handoff includes all required sections

---

### Phase J: Testing System (1.5 hours)

**Tasks:**
1. Create `app/services/testing_service.py`
2. Implement Tier 1 tests (syntax, imports, lint, types, pytest)
3. Implement Tier 2 tests (app start, dependencies)
4. Create Testing Panel UI
5. Add "Run Tests" to Execution Panel
6. Implement auto-test after build
7. Implement "Send Failures to Builder" flow

**Test Criteria:**
- [ ] Syntax check works
- [ ] Import check works
- [ ] Linting works
- [ ] Type check works
- [ ] Unit tests run
- [ ] App start test works
- [ ] Results display in UI
- [ ] Auto-test runs after builds
- [ ] Failures route to builder

---

### Phase K: Audit & Performance (30 min)

**Tasks:**
1. Implement audit log storage
2. Implement audit log UI with filters
3. Implement statistics calculation
4. Implement cost tracking
5. Implement agent performance tracking
6. Add Performance panel

**Test Criteria:**
- [ ] All actions logged
- [ ] Filters work correctly
- [ ] Statistics accurate
- [ ] Costs tracked per round
- [ ] Performance updates after each task
- [ ] Recommendations generate

---

### Phase L: Templates & Import (30 min)

**Tasks:**
1. Implement save template
2. Implement load template
3. Implement Import Design Tree Context
4. Add template management UI

**Test Criteria:**
- [ ] Can save current config as template
- [ ] Can load template into session
- [ ] Can import Design Tree project context
- [ ] Token preview accurate

---

### Phase M: Polish & Final Testing (1 hour)

**Tasks:**
1. Full integration testing
2. UI polish and consistency
3. Error message improvements
4. Documentation updates
5. Final bug fixes

**Test Criteria:**
- [ ] All features work together
- [ ] UI is consistent
- [ ] Errors are clear and helpful
- [ ] No crashes on edge cases
- [ ] Performance acceptable

---

## Build Time Summary

| Phase | Description | Time |
|-------|-------------|------|
| A | Database & Models | 30 min |
| B | Core Service | 1 hour |
| C | Execution Engine | 1 hour |
| D | Basic UI | 1 hour |
| E | Execution UI | 45 min |
| F | Baton Integration | 45 min |
| G | Master Prompt System | 30 min |
| H | GitHub Integration | 1 hour |
| I | Checkpoints & Handoffs | 45 min |
| J | Testing System | 1.5 hours |
| K | Audit & Performance | 30 min |
| L | Templates & Import | 30 min |
| M | Polish & Final Testing | 1 hour |
| | | |
| **TOTAL** | | **~11 hours** |

---

## Success Criteria

Complete system allows:

### Core Features
- [ ] Creating multi-round sessions
- [ ] Adding multiple agents per round (any model)
- [ ] Configuring master prompt and guardrails
- [ ] Executing rounds with progress display
- [ ] Viewing results with votes
- [ ] Calculating consensus
- [ ] Revising and re-voting
- [ ] Sequential AND parallel execution modes

### Context Management
- [ ] Context health indicator (percentage)
- [ ] Auto-baton trigger at configurable threshold
- [ ] Context persisting via Baton
- [ ] Import Design Tree context

### Safety & Recovery
- [ ] Auto-checkpoint system
- [ ] Manual checkpoint creation
- [ ] Checkpoint restoration
- [ ] Handoff document generator

### Testing
- [ ] Tier 1+2 automated testing
- [ ] Auto-send failures to builder
- [ ] Test results display

### Version Control
- [ ] GitHub repo connection
- [ ] Branch switching
- [ ] Pull/push operations
- [ ] Baseline management

### Analytics
- [ ] Full audit trail
- [ ] Cost tracking
- [ ] Agent performance tracking
- [ ] Best combination recommendations

### Configuration
- [ ] ALL settings adjustable via UI
- [ ] Template save/load
- [ ] Default prompts

---

## Requirements.txt Additions

```
# AI Providers
anthropic>=0.18.0
openai>=1.12.0

# Testing
flake8>=6.0.0
mypy>=1.0.0
pytest>=7.0.0
bandit>=1.7.0

# UI Testing (optional - Phase K)
playwright>=1.40.0
pytest-playwright>=0.4.0

# GitHub
PyGithub>=2.1.0
```

---

## Quick Reference

### Model IDs
```
Anthropic:
- claude-opus-4-5-20250101
- claude-sonnet-4-5-20250929
- claude-3-5-sonnet-20241022

OpenAI:
- gpt-4-turbo-preview
- gpt-4o
- gpt-4o-mini
```

### Context Limits
```
Claude models: ~200k tokens
GPT-4 models: ~128k tokens

Recommended target: 40% of max
Auto-baton trigger: 80% of target
```

### Voting Thresholds
```
Simple Majority: 50%
Supermajority: 66% (default)
Unanimous: 100%
```

---

**END OF AGENT OS BLUEPRINT**

*This system, once built, becomes the tool for building everything else. Treat it as highest priority.*
