# Agent OS Blueprint: Roundtable Coder System

**Document Version:** 1.0
**Feature:** Multi-Agent Roundtable Coding with Baton Integration
**Priority:** HIGH - Build this first to use for building everything else

---

## CRITICAL: READ FIRST

This is a **self-bootstrapping feature**. Once built, use it to build the rest of Design Tree Studio. The Roundtable + Baton system gives you:
- Multiple agents catching each other's mistakes
- Infinite context via Baton handoffs
- Flexible testing of different approaches

**Do NOT simplify this spec.** Build it as documented.

---

# LAYER 1: STANDARDS

## Technology Stack
- **Framework:** Streamlit (Python)
- **AI Providers:**
  - Anthropic (Claude Opus 4.5, Sonnet 4.5, Sonnet 3.5)
  - OpenAI (GPT-4 Turbo, GPT-4o, GPT-5.x when available)
- **Database:** SQLAlchemy (existing Design Tree Studio DB)
- **Context System:** Baton (existing, needs flexibility upgrade)

## Architecture

```
app/
├── services/
│   ├── roundtable_service.py    # NEW - Core roundtable logic
│   ├── agent_pool_service.py    # NEW - Manage agent instances
│   └── baton_service.py         # EXISTING - Upgrade for flexibility
├── ui/
│   ├── roundtable_panel.py      # NEW - Main roundtable UI
│   └── layout.py                # MODIFY - Add roundtable tab
├── core/
│   └── models.py                # MODIFY - Add roundtable models
└── streamlit_app.py             # MODIFY - Add roundtable tab
```

## Key Patterns
- Each API call = new agent instance (even same model)
- Master prompts cascade to all agents
- Individual prompts override master
- All responses stored for audit
- Baton context injected automatically

---

# LAYER 2: PRODUCT

## Vision
A multi-agent coding system where multiple AI instances collaborate, vote on each other's work, and maintain infinite context through the Baton system. Used to build itself and all future features.

## Target User
- Vibe coders who can't trust a single agent
- Users who want consensus before committing code
- Anyone building complex features that need multiple perspectives

## Core Use Cases

1. **Build with Consensus**
   - User sets up build task
   - Agent 1 writes code
   - Agents 2-5 vote on code quality
   - Revise until consensus reached

2. **Test Different Approaches**
   - Same prompt to 3 different models
   - Compare outputs
   - Pick best one

3. **Continuous Building**
   - Round 1: Build feature A
   - Round 2: Review and revise
   - Round 3: Build feature B
   - Baton carries context through all rounds

4. **Learn What Works**
   - Audit log shows which agents perform best
   - Adjust prompts based on results
   - Master prompt evolves over time

---

# LAYER 3: SPECS

## Feature: Roundtable Coder

### Overview
A new tab in Design Tree Studio that enables multi-agent collaboration with voting, master prompts, and Baton integration.

---

### UI Components

#### 1. Master Configuration Panel

```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ MASTER CONFIGURATION                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ MASTER SYSTEM PROMPT (applies to all agents):               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ You are an expert software developer working on         │ │
│ │ Design Tree Studio, a Streamlit application. Follow     │ │
│ │ these guidelines:                                       │ │
│ │                                                         │ │
│ │ - Use Python 3.11+ conventions                          │ │
│ │ - Follow existing code patterns in the codebase         │ │
│ │ - Write clean, documented code                          │ │
│ │ - Consider edge cases                                   │ │
│ │ - Test your code mentally before submitting             │ │
│ │ ...                                                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [Save Master Prompt] [Load Default] [Push to All Agents]    │
│                                                             │
│ MASTER GUARDRAILS (rules all agents must follow):           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ - Do NOT modify files outside the specified scope       │ │
│ │ - Do NOT delete existing functionality without asking   │ │
│ │ - Do NOT use deprecated libraries                       │ │
│ │ - Do NOT hardcode secrets or API keys                   │ │
│ │ - ALWAYS include error handling                         │ │
│ │ - ALWAYS preserve existing imports                      │ │
│ │ ...                                                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [Save Guardrails] [Load Default] [Push to All Agents]       │
│                                                             │
│ API KEYS:                                                   │
│ Anthropic: [••••••••••••••••] [Test]                       │
│ OpenAI:    [••••••••••••••••] [Test]                       │
│                                                             │
│ BATON SETTINGS:                                             │
│ Context Window Target: [40___]% of model max                │
│ Auto-Baton: [✓] Trigger at [80]% of target                 │
│                                                             │
│ VOTING SETTINGS:                                            │
│ Approval Threshold: [66]% (2/3 majority)                    │
│ Require Explanation: [✓] Voters must explain vote          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 2. Round Configuration Panel

```
┌─────────────────────────────────────────────────────────────┐
│ 🔄 ROUNDS                                        [+ Add Round]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ROUND 1: Build                              [Delete] [▲▼]│ │
│ │                                                         │ │
│ │ Task Prompt:                                            │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ Implement the roundtable_service.py file with:    │   │ │
│ │ │ - RoundtableSession class                         │   │ │
│ │ │ - Methods for adding/removing agents              │   │ │
│ │ │ - Round execution logic                           │   │ │
│ │ │ - Voting tabulation                               │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ │                                                         │ │
│ │ AGENTS IN THIS ROUND:                      [+ Add Agent]│ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ Agent 1                                           │   │ │
│ │ │ Model: [Opus 4.5        ▼]                        │   │ │
│ │ │ Role:  [Builder         ▼]                        │   │ │
│ │ │ Prompt Override: [Use master ▼] [Edit]            │   │ │
│ │ │ [Remove Agent]                                    │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ Agent 2                                           │   │ │
│ │ │ Model: [Opus 4.5        ▼]                        │   │ │
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
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ROUND 2: Review & Revise                    [Delete] [▲▼]│ │
│ │ ... (similar structure)                                 │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Save Round Configuration as Template]                      │
│ [Load Template ▼]                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 3. Execution Panel

```
┌─────────────────────────────────────────────────────────────┐
│ ▶️ EXECUTION                                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Current: Round 1 of 2                                       │
│ Status: Ready to execute                                    │
│                                                             │
│ [▶ Run Current Round] [⏭ Skip Round] [🔄 Restart All]       │
│ [⏸ Pause After Each Agent] [🔁 Auto-Loop Until Consensus]   │
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

#### 4. Results Panel

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 RESULTS - Round 1                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ AGENT 1 (Opus 4.5) - BUILDER                           │ │
│ │ Time: 45s | Tokens: 2,340 | Cost: $0.28                │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ ```python                                         │   │ │
│ │ │ class RoundtableSession:                          │   │ │
│ │ │     def __init__(self, project_id: int):          │   │ │
│ │ │         self.project_id = project_id              │   │ │
│ │ │         self.agents = []                          │   │ │
│ │ │         self.rounds = []                          │   │ │
│ │ │     ...                                           │   │ │
│ │ │ ```                                               │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ │ [Copy Code] [View Full] [Apply to Codebase]            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ AGENT 2 (Opus 4.5) - VOTER                     👍 APPROVE│ │
│ │ Time: 23s | Tokens: 890 | Cost: $0.09                  │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ The implementation looks solid. Good structure,   │   │ │
│ │ │ proper type hints, and clean separation of        │   │ │
│ │ │ concerns. Minor suggestion: add docstrings to     │   │ │
│ │ │ public methods.                                   │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ AGENT 3 (GPT-4o) - VOTER                       👎 REJECT│ │
│ │ Time: 18s | Tokens: 1,120 | Cost: $0.08                │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ Issues found:                                     │   │ │
│ │ │ 1. Missing error handling in execute_round()      │   │ │
│ │ │ 2. No timeout mechanism for agent calls           │   │ │
│ │ │ 3. Should validate agent roles before execution   │   │ │
│ │ │                                                   │   │ │
│ │ │ Recommend revision before proceeding.             │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ═══════════════════════════════════════════════════════════ │
│ CONSENSUS: 1/2 voters approved (50%) - BELOW THRESHOLD (66%)│
│                                                             │
│ [🔄 Revise & Re-vote] [✅ Override & Accept] [❌ Reject All]│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 5. GitHub Integration Panel

```
┌─────────────────────────────────────────────────────────────┐
│ 🐙 GITHUB INTEGRATION                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Connected Repositories:                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ● design-tree-studio (active)                          │ │
│ │   Branch: main | Last sync: 5 min ago                  │ │
│ │   [Switch Branch ▼] [Pull] [Push] [View Diff]          │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ○ marisol-ai                                           │ │
│ │   Branch: develop | Last sync: 2 hours ago             │ │
│ │   [Activate] [Switch Branch ▼]                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [+ Connect New Repository]                                  │
│                                                             │
│ BASELINE MANAGEMENT:                                        │
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
│ • v0.2.0-basic-chat                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 6. Audit Log Panel

```
┌─────────────────────────────────────────────────────────────┐
│ 📜 AUDIT LOG                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Filter: [All Rounds ▼] [All Agents ▼] [All Outcomes ▼]     │
│                                                             │
│ Session: Roundtable-2024-01-15-001                         │
│                                                             │
│ 10:45:23 | Round 1 | Agent 1 (Opus) | BUILD | 2,340 tokens │
│ 10:46:08 | Round 1 | Agent 2 (Opus) | VOTE: 👍 | 890 tokens │
│ 10:46:26 | Round 1 | Agent 3 (GPT)  | VOTE: 👎 | 1,120 tkns │
│ 10:46:27 | Round 1 | CONSENSUS: FAIL (50% < 66%)           │
│ 10:47:15 | Round 1 | Agent 1 (Opus) | REVISE | 1,890 tokens│
│ 10:47:45 | Round 1 | Agent 2 (Opus) | VOTE: 👍 | 450 tokens │
│ 10:48:02 | Round 1 | Agent 3 (GPT)  | VOTE: 👍 | 380 tokens │
│ 10:48:03 | Round 1 | CONSENSUS: PASS (100% >= 66%)         │
│ 10:48:05 | Round 2 | Started                                │
│ ...                                                         │
│                                                             │
│ [Export Log] [Clear Log] [View Statistics]                  │
│                                                             │
│ STATISTICS:                                                 │
│ • Total Rounds: 5                                           │
│ • Total Revisions: 3                                        │
│ • Avg Consensus Attempts: 1.6                               │
│ • Best Performer: Opus 4.5 (92% approval rate)              │
│ • Most Critical: GPT-4o (caught 8 issues)                   │
│ • Total Cost: $4.56                                         │
│ • Total Tokens: 34,560                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Data Models

```python
# Add to app/core/models.py

class RoundtableSession(Base):
    __tablename__ = "roundtable_sessions"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(255))
    status = Column(Enum(SessionStatus))  # active, paused, completed
    master_prompt = Column(Text)
    master_guardrails = Column(Text)
    voting_threshold = Column(Float, default=0.66)
    created_at = Column(DateTime, default=datetime.utcnow)

    rounds = relationship("RoundtableRound", back_populates="session")


class RoundtableRound(Base):
    __tablename__ = "roundtable_rounds"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("roundtable_sessions.id"))
    round_number = Column(Integer)
    round_type = Column(String(50))  # build, vote, review
    task_prompt = Column(Text)
    status = Column(String(50))  # pending, running, completed
    consensus_reached = Column(Boolean, default=False)

    session = relationship("RoundtableSession", back_populates="rounds")
    agents = relationship("RoundtableAgent", back_populates="round")


class RoundtableAgent(Base):
    __tablename__ = "roundtable_agents"

    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("roundtable_rounds.id"))
    model = Column(String(100))  # claude-opus-4-5, gpt-4o, etc.
    role = Column(String(50))  # builder, voter, reviewer
    prompt_override = Column(Text, nullable=True)

    round = relationship("RoundtableRound", back_populates="agents")
    responses = relationship("AgentResponse", back_populates="agent")


class AgentResponse(Base):
    __tablename__ = "agent_responses"

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("roundtable_agents.id"))
    content = Column(Text)
    vote = Column(String(20), nullable=True)  # approve, reject, abstain
    vote_reason = Column(Text, nullable=True)
    tokens_used = Column(Integer)
    cost = Column(Float)
    duration_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("RoundtableAgent", back_populates="responses")
```

---

### Service Layer

```python
# app/services/roundtable_service.py

AVAILABLE_MODELS = {
    # Anthropic
    "Opus 4.5": {"id": "claude-opus-4-5-20250101", "provider": "anthropic", "max_tokens": 200000},
    "Sonnet 4.5": {"id": "claude-sonnet-4-5-20250929", "provider": "anthropic", "max_tokens": 200000},
    "Sonnet 3.5": {"id": "claude-3-5-sonnet-20241022", "provider": "anthropic", "max_tokens": 200000},
    # OpenAI
    "GPT-4 Turbo": {"id": "gpt-4-turbo-preview", "provider": "openai", "max_tokens": 128000},
    "GPT-4o": {"id": "gpt-4o", "provider": "openai", "max_tokens": 128000},
    "GPT-4o Mini": {"id": "gpt-4o-mini", "provider": "openai", "max_tokens": 128000},
}

AGENT_ROLES = {
    "builder": "Write code based on the task prompt",
    "voter": "Review code and vote approve/reject with explanation",
    "reviewer": "Provide detailed code review without voting",
}

DEFAULT_MASTER_PROMPT = """You are an expert software developer working on Design Tree Studio.

Design Tree Studio is a Streamlit application that helps users organize design projects
and generate documentation through AI-assisted conversations.

Tech Stack:
- Python 3.11+
- Streamlit
- SQLAlchemy
- OpenAI/Anthropic APIs

Follow these principles:
- Write clean, readable, documented code
- Use type hints
- Handle errors gracefully
- Follow existing patterns in the codebase
- Consider edge cases
"""

DEFAULT_GUARDRAILS = """RULES (Do NOT violate these):
1. Do NOT delete or modify code outside the specified scope
2. Do NOT remove existing imports without explicit instruction
3. Do NOT hardcode API keys or secrets
4. Do NOT use deprecated libraries
5. ALWAYS include error handling
6. ALWAYS test your code mentally before submitting
7. ALWAYS preserve existing functionality
8. If unsure, ask for clarification rather than guessing
"""

class RoundtableService:
    def __init__(self, db: Session, anthropic_key: str = None, openai_key: str = None):
        self.db = db
        self.anthropic_key = anthropic_key
        self.openai_key = openai_key

    def create_session(self, project_id: int, name: str) -> RoundtableSession:
        """Create a new roundtable session."""
        pass

    def add_round(self, session_id: int, round_type: str, task_prompt: str) -> RoundtableRound:
        """Add a round to a session."""
        pass

    def add_agent(self, round_id: int, model: str, role: str, prompt_override: str = None) -> RoundtableAgent:
        """Add an agent to a round."""
        pass

    def execute_round(self, round_id: int, baton_context: str = None) -> dict:
        """Execute all agents in a round and collect responses."""
        pass

    def calculate_consensus(self, round_id: int) -> dict:
        """Calculate voting consensus for a round."""
        pass

    def call_agent(self, agent: RoundtableAgent, prompt: str, context: str) -> AgentResponse:
        """Make API call to a single agent."""
        pass
```

---

### Build Phases

#### Phase A: Database & Models (30 min)
1. Add roundtable models to `models.py`
2. Create migration
3. Test model creation

**Test:** Can create RoundtableSession, Round, Agent, Response in DB

---

#### Phase B: Core Service (1 hour)
1. Create `roundtable_service.py`
2. Implement model constants (AVAILABLE_MODELS, AGENT_ROLES)
3. Implement create_session, add_round, add_agent
4. Implement call_agent (single API call)

**Test:** Can create session, add rounds, add agents, make single API call

---

#### Phase C: Execution Engine (1 hour)
1. Implement execute_round (run all agents in sequence)
2. Implement calculate_consensus
3. Add timeout handling
4. Add error recovery

**Test:** Can execute full round with multiple agents, get consensus result

---

#### Phase D: Basic UI (1 hour)
1. Create `roundtable_panel.py`
2. Add to main app as new tab
3. Implement Master Configuration section
4. Implement Round Configuration section (add/remove rounds, agents)

**Test:** Can configure rounds and agents in UI

---

#### Phase E: Execution UI (45 min)
1. Implement execution panel
2. Show progress during execution
3. Display results with voting
4. Add action buttons (revise, accept, reject)

**Test:** Can execute round from UI, see results, take action

---

#### Phase F: Baton Integration (45 min)
1. Inject Baton context into agent calls
2. Save round results back to Baton
3. Add context window settings (configurable %)
4. Implement auto-baton trigger

**Test:** Context persists across rounds, auto-baton triggers at threshold

---

#### Phase G: Master Prompt System (30 min)
1. Implement master prompt storage
2. Implement "Push to All Agents" function
3. Implement per-agent override
4. Add default prompts

**Test:** Master prompt applies to new agents, overrides work

---

#### Phase H: GitHub Integration (1 hour)
1. Add GitHub connection settings
2. Implement repo listing
3. Implement branch switching
4. Implement baseline create/restore/copy

**Test:** Can connect repo, switch branches, create baseline

---

#### Phase I: Audit & Polish (30 min)
1. Implement audit log storage
2. Implement audit log UI
3. Add statistics calculation
4. Add cost tracking

**Test:** Full session logged, stats accurate, costs tracked

---

### Success Criteria

Complete system allows:
- [ ] Creating multi-round sessions
- [ ] Adding multiple agents per round (any model)
- [ ] Configuring master prompt and guardrails
- [ ] Executing rounds with progress display
- [ ] Viewing results with votes
- [ ] Calculating consensus
- [ ] Revising and re-voting
- [ ] Context persisting via Baton
- [ ] GitHub repo management
- [ ] Baseline creation and restoration
- [ ] Full audit trail

---

### Default Master Prompt (Copy-Ready)

```
You are an expert software developer working on Design Tree Studio, a Streamlit application.

PROJECT CONTEXT:
Design Tree Studio helps users organize design projects and generate documentation through AI-assisted conversations. It features:
- Node-based project organization
- AI chat with OpenAI integration
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

YOUR TASK:
Follow the specific task prompt provided. Write production-quality code that integrates cleanly with the existing codebase.
```

---

### Default Guardrails (Copy-Ready)

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

### Estimated Total Build Time

| Phase | Time |
|-------|------|
| A: Database & Models | 30 min |
| B: Core Service | 1 hour |
| C: Execution Engine | 1 hour |
| D: Basic UI | 1 hour |
| E: Execution UI | 45 min |
| F: Baton Integration | 45 min |
| G: Master Prompt System | 30 min |
| H: GitHub Integration | 1 hour |
| I: Audit & Polish | 30 min |
| **TOTAL** | **~7-8 hours** |

With a competent agent and the testing protocol, this should be achievable in 1-2 focused sessions.

---

## APPENDIX: Quick Reference

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

### Context Window Limits
```
Claude models: ~200k tokens
GPT-4 models: ~128k tokens

Recommended usage: 40% for safety margin
Auto-baton trigger: 80% of target
```

### Voting Thresholds
```
Simple Majority: 50%
Supermajority: 66% (recommended)
Unanimous: 100%
```

---

**END OF ROUNDTABLE SPEC**

*This system, once built, becomes the tool for building everything else. Treat it as highest priority.*
