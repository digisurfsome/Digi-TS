# Roundtable Coder - Phase 1 Build (A-E Only)

**SCOPE: Phases A through E ONLY**
**Estimated Time: ~5 hours**
**Goal: Working MVP that can execute rounds with agents**

---

## CRITICAL INSTRUCTIONS

### STOP AFTER PHASE E

You are building **ONLY phases A-E**. Do not build anything else.

After Phase E is complete and tested:
1. Stop building
2. Report what was completed
3. The user will handle the remaining phases separately

### FUTURE PHASES (DO NOT BUILD)

These will be built later by another agent or using the Roundtable itself:
- Phase F: Enhanced Baton integration
- Phase G: Master prompt system
- Phase H: GitHub integration
- Phase I: Checkpoints & handoffs
- Phase J: Testing system
- Phase K+: Audit, templates, polish

**Be aware these exist** so you don't paint yourself into a corner, but **do NOT implement them**.

---

## What You're Building

A new "Roundtable" tab in Design Tree Studio that allows:
- Creating coding sessions with multiple rounds
- Adding multiple AI agents per round (Opus, GPT, etc.)
- Executing rounds and seeing results
- Basic voting and consensus display

---

## Architecture

### Files to Create/Modify

```
app/
├── core/
│   └── models.py              # MODIFY - Add roundtable models
├── services/
│   └── roundtable_service.py  # NEW - Core roundtable logic
├── ui/
│   └── roundtable_panel.py    # NEW - Main roundtable UI
└── streamlit_app.py           # MODIFY - Add roundtable tab
```

### Database: Same SQLite, Separate Tables

Add tables with `roundtable_` prefix to existing database. Do NOT create a separate database.

---

## Phase A: Database & Models (30 min)

### Task
Add roundtable models to `app/core/models.py`

### Models to Add

```python
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
    """A roundtable coding session."""
    __tablename__ = "roundtable_sessions"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    name = Column(String(255), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    master_prompt = Column(Text)
    master_guardrails = Column(Text)
    voting_threshold = Column(Float, default=0.66)
    execution_mode = Column(String(20), default="single")  # "single" or "multi"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rounds = relationship("RoundtableRound", back_populates="session", cascade="all, delete-orphan")


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

    round = relationship("RoundtableRound", back_populates="agents")
    responses = relationship("RoundtableResponse", back_populates="agent", cascade="all, delete-orphan")


class RoundtableResponse(Base):
    """A response from an agent."""
    __tablename__ = "roundtable_responses"

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("roundtable_agents.id"), nullable=False)
    iteration = Column(Integer, default=1)
    content = Column(Text)
    vote = Column(Enum(VoteType), nullable=True)
    vote_reason = Column(Text, nullable=True)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("RoundtableAgent", back_populates="responses")
```

### Test Criteria for Phase A
- [ ] Can create RoundtableSession in database
- [ ] Can create RoundtableRound linked to session
- [ ] Can create RoundtableAgent linked to round
- [ ] Can create RoundtableResponse linked to agent
- [ ] All relationships work (session.rounds, round.agents, etc.)
- [ ] App still starts without errors

---

## Phase B: Core Service (1 hour)

### Task
Create `app/services/roundtable_service.py` with basic operations.

### Available Models

```python
AVAILABLE_MODELS = {
    # Anthropic
    "Opus 4.5": {
        "id": "claude-opus-4-5-20250101",
        "provider": "anthropic",
        "max_tokens": 200000
    },
    "Sonnet 4.5": {
        "id": "claude-sonnet-4-5-20250929",
        "provider": "anthropic",
        "max_tokens": 200000
    },
    "Sonnet 3.5": {
        "id": "claude-3-5-sonnet-20241022",
        "provider": "anthropic",
        "max_tokens": 200000
    },
    # OpenAI
    "GPT-4 Turbo": {
        "id": "gpt-4-turbo-preview",
        "provider": "openai",
        "max_tokens": 128000
    },
    "GPT-4o": {
        "id": "gpt-4o",
        "provider": "openai",
        "max_tokens": 128000
    },
    "GPT-4o Mini": {
        "id": "gpt-4o-mini",
        "provider": "openai",
        "max_tokens": 128000
    },
}

AGENT_ROLES = {
    "builder": "Write code based on the task prompt",
    "voter": "Review code and vote approve/reject with explanation",
    "reviewer": "Provide detailed code review without voting",
}
```

### Service Methods to Implement

```python
class RoundtableService:
    def __init__(self, db: Session, anthropic_key: str = None, openai_key: str = None):
        self.db = db
        self.anthropic_client = None
        self.openai_client = None
        if anthropic_key:
            import anthropic
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
        if openai_key:
            import openai
            self.openai_client = openai.OpenAI(api_key=openai_key)

    # Session Management
    def create_session(self, name: str, project_id: int = None) -> RoundtableSession:
        """Create a new roundtable session."""
        # Implementation required

    def get_session(self, session_id: int) -> RoundtableSession:
        """Get a session by ID."""
        # Implementation required

    def list_sessions(self) -> List[RoundtableSession]:
        """List all sessions."""
        # Implementation required

    def update_session(self, session_id: int, **kwargs) -> RoundtableSession:
        """Update session settings."""
        # Implementation required

    def delete_session(self, session_id: int) -> bool:
        """Delete a session."""
        # Implementation required

    # Round Management
    def add_round(self, session_id: int, name: str, task_prompt: str) -> RoundtableRound:
        """Add a round to a session."""
        # Implementation required

    def update_round(self, round_id: int, **kwargs) -> RoundtableRound:
        """Update round settings."""
        # Implementation required

    def delete_round(self, round_id: int) -> bool:
        """Delete a round."""
        # Implementation required

    # Agent Management
    def add_agent(self, round_id: int, model_name: str, role: str, prompt_override: str = None) -> RoundtableAgent:
        """Add an agent to a round."""
        # Implementation required

    def update_agent(self, agent_id: int, **kwargs) -> RoundtableAgent:
        """Update agent configuration."""
        # Implementation required

    def delete_agent(self, agent_id: int) -> bool:
        """Delete an agent."""
        # Implementation required
```

### Test Criteria for Phase B
- [ ] Can create session with create_session()
- [ ] Can retrieve session with get_session()
- [ ] Can add round to session with add_round()
- [ ] Can add agent to round with add_agent()
- [ ] Can update and delete all entities
- [ ] Service initializes with API keys from settings

---

## Phase C: Execution Engine (1 hour)

### Task
Add execution methods to RoundtableService.

### Methods to Add

```python
    # In RoundtableService class:

    def call_agent(self, agent: RoundtableAgent, system_prompt: str, user_prompt: str) -> RoundtableResponse:
        """Make API call to a single agent and store response."""
        # Must handle both Anthropic and OpenAI based on agent.provider
        # Must track tokens, cost, duration
        # Must store response in database
        # Implementation required

    def execute_round(self, round_id: int, execution_mode: str = "single") -> dict:
        """Execute all agents in a round.

        Args:
            round_id: The round to execute
            execution_mode: "single" (builder only) or "multi" (builder + voters)

        Returns:
            dict with results, votes, consensus info
        """
        # Get round and its agents
        # Build system prompt (master prompt + guardrails)
        # Build user prompt (task prompt + any context)
        #
        # If execution_mode == "single":
        #     Only run the first builder agent
        #
        # If execution_mode == "multi":
        #     Run builder first
        #     Then run all voters with builder's output
        #     Calculate consensus
        #
        # Implementation required

    def calculate_consensus(self, round_id: int) -> dict:
        """Calculate voting consensus for a round.

        Returns:
            {
                "total_voters": int,
                "approvals": int,
                "rejections": int,
                "percentage": float,
                "threshold": float,
                "passed": bool,
                "feedback": list[str]  # Voter feedback for builder
            }
        """
        # Implementation required
```

### API Call Examples

**Anthropic:**
```python
response = self.anthropic_client.messages.create(
    model=model_id,
    max_tokens=4096,
    system=system_prompt,
    messages=[{"role": "user", "content": user_prompt}]
)
content = response.content[0].text
tokens_in = response.usage.input_tokens
tokens_out = response.usage.output_tokens
```

**OpenAI:**
```python
response = self.openai_client.chat.completions.create(
    model=model_id,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
)
content = response.choices[0].message.content
tokens_in = response.usage.prompt_tokens
tokens_out = response.usage.completion_tokens
```

### Test Criteria for Phase C
- [ ] call_agent() works with Anthropic models
- [ ] call_agent() works with OpenAI models
- [ ] execute_round() runs in "single" mode (builder only)
- [ ] execute_round() runs in "multi" mode (builder + voters)
- [ ] calculate_consensus() returns correct percentages
- [ ] Responses are stored in database
- [ ] Tokens and costs are tracked

---

## Phase D: Basic UI (1 hour)

### Task
Create `app/ui/roundtable_panel.py` and add tab to main app.

### UI Structure

```
┌─────────────────────────────────────────────────────────────┐
│ 🔄 ROUNDTABLE CODER                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ SESSION                                                     │
│ [Select Session ▼] [+ New Session] [Delete]                │
│                                                             │
│ Session Name: [________________________]                    │
│                                                             │
│ EXECUTION MODE ← IMPORTANT: Single/Multi toggle            │
│ ○ Single Agent (Builder only, no voting)                   │
│ ● Multi-Agent (Builder + Voters with consensus)            │
│                                                             │
│ Voting Threshold: [====●=====] 66%                         │
│ (Only applies in Multi-Agent mode)                          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ ROUNDS                                         [+ Add Round]│
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Round 1                                        [Delete] │ │
│ │                                                         │ │
│ │ Task: [________________________________________]        │ │
│ │                                                         │ │
│ │ Agents:                                   [+ Add Agent] │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ 1. [Opus 4.5 ▼] [Builder ▼]              [Remove]  │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ 2. [GPT-4o ▼]   [Voter ▼]                [Remove]  │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key UI Elements

1. **Session selector** - Dropdown to select/create sessions
2. **Execution mode toggle** - Single vs Multi agent (REQUIRED)
3. **Voting threshold slider** - 50% to 100%
4. **Round cards** - Each round with task prompt and agents
5. **Agent rows** - Model dropdown, role dropdown, remove button
6. **Add buttons** - For rounds and agents

### Test Criteria for Phase D
- [ ] Roundtable tab appears in main app
- [ ] Can create new session
- [ ] Can switch between sessions
- [ ] Can toggle Single/Multi execution mode
- [ ] Can adjust voting threshold
- [ ] Can add/remove rounds
- [ ] Can add/remove agents with model/role selection
- [ ] Changes persist to database

---

## Phase E: Execution UI (45 min)

### Task
Add execution controls and results display to the UI.

### UI Addition

```
┌─────────────────────────────────────────────────────────────┐
│ EXECUTION                                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Current Round: [Round 1 ▼]                                 │
│                                                             │
│ [▶ Run Round]  [🔄 Re-run]                                 │
│                                                             │
│ Status: Ready / Running... / Complete                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ RESULTS                                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ AGENT 1 (Opus 4.5) - BUILDER                           │ │
│ │ Tokens: 2,340 | Cost: $0.28 | Time: 45s                │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ [Code/response output here]                       │   │ │
│ │ │ With syntax highlighting if code                  │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ │ [Copy] [View Full]                                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ (If Multi-Agent mode:)                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ AGENT 2 (GPT-4o) - VOTER                      👍 APPROVE│ │
│ │ Tokens: 890 | Cost: $0.09 | Time: 23s                  │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ [Vote explanation]                                │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ CONSENSUS: 2/2 approved (100%) ✅ PASSED                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

1. **Round selector** - Which round to execute
2. **Run button** - Triggers execution
3. **Status indicator** - Shows progress
4. **Results display** - Shows each agent's response
5. **Vote display** - Shows approve/reject with emoji
6. **Consensus bar** - Shows voting result and pass/fail

### Test Criteria for Phase E
- [ ] Can select round to execute
- [ ] Run button executes the round
- [ ] Status updates during execution
- [ ] Builder response displays with content
- [ ] Voter responses display with votes (in multi mode)
- [ ] Consensus calculation displays correctly
- [ ] Token counts and costs show
- [ ] Copy button works
- [ ] Single mode shows only builder result
- [ ] Multi mode shows builder + voters + consensus

---

## Default Prompts (For Testing)

### Default System Prompt
```
You are an expert software developer. Write clean, well-documented code.
Follow best practices and handle errors appropriately.
```

### Default Voter Prompt Addition
```
Review the code provided by the builder.

Your response MUST start with one of:
- APPROVE: [your explanation]
- REJECT: [your explanation with specific issues]

Be specific about what's good or what needs fixing.
```

---

## Testing Protocol

After completing each phase:

1. **Syntax check** - Does the code have any syntax errors?
2. **Import check** - Do all imports resolve?
3. **App start check** - Does `streamlit run streamlit_app.py` start without errors?
4. **Functionality check** - Do the test criteria pass?

Only proceed to the next phase after current phase passes all checks.

---

## Summary

| Phase | What | Time | Key Deliverable |
|-------|------|------|-----------------|
| A | Models | 30m | Database tables for roundtable |
| B | Service | 1h | CRUD operations for sessions/rounds/agents |
| C | Execution | 1h | API calls and consensus calculation |
| D | Basic UI | 1h | Configuration interface |
| E | Execution UI | 45m | Run button and results display |

**Total: ~5 hours**

After Phase E, you have a working Roundtable that can:
- Create sessions with rounds and agents
- Run rounds in single-agent OR multi-agent mode
- Display results with voting (in multi mode)
- Calculate consensus

**STOP after Phase E. Do not continue to Phase F or beyond.**
