# Agent OS Blueprint: Design Tree Studio

**Document Version:** 1.0
**Created:** During active development session
**Purpose:** Complete context for any AI agent to continue building this system

---

## CRITICAL: READ THIS FIRST

This document captures the COMPLETE vision, mechanisms, and build plan for Design Tree Studio. If you're a new AI agent picking this up:

1. **Read this entire document before coding anything**
2. **This is not a simple app** - It's a revolutionary approach to AI-assisted development
3. **The mechanisms described here are novel** - Many don't exist anywhere else
4. **Preserve the philosophy** - Don't simplify or water down the vision

---

## LAYER 1: STANDARDS

### Technology Stack
- **Framework:** Streamlit (Python web app)
- **Database:** SQLAlchemy ORM with PostgreSQL (Railway) or SQLite (local)
- **AI:** OpenAI API (GPT-4 Turbo)
- **Deployment:** Railway with Dockerfile

### Architecture
```
design-tree-studio/
├── app/
│   ├── core/
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── database.py        # DB connection
│   │   └── repositories.py    # Data access
│   ├── services/
│   │   ├── chat_service.py    # OpenAI chat integration
│   │   ├── node_service.py    # Node CRUD operations
│   │   ├── baton_service.py   # Context handoff system
│   │   ├── node_detector.py   # Auto-detect nodes from chat
│   │   ├── process_log.py     # Logging service
│   │   └── [NEW] agent_os_service.py  # Agent OS generation
│   ├── ui/
│   │   ├── layout.py          # Main UI components
│   │   └── node_tree_panel.py # Tree visualization
│   └── streamlit_app.py       # Main entry point
├── Dockerfile                  # Railway deployment
├── requirements.txt
└── AGENT_OS_BLUEPRINT.md       # THIS FILE
```

### Coding Patterns
- **Services layer** for all business logic
- **Models** use SQLAlchemy with proper relationships
- **UI** uses Streamlit components with session state
- **Node model** uses `name` (not `title`) and `node_type` (not `domain`)

### Key Files to Understand
- `app/services/node_detector.py` - Current auto-detection (enhance this)
- `app/ui/layout.py` - Main chat interface (add new features here)
- `app/services/__init__.py` - All service exports

---

## LAYER 2: PRODUCT

### The Problem Being Solved

**The Core Issue:**
When you brainstorm with AI, perfect detailed plans emerge in conversation. But when you try to formalize them into documentation (PRD, specs, etc.), details get watered down. It's like the telephone game - every translation loses fidelity.

**The Insight:**
The brainstorm IS the documentation - it's already being written. It just needs to be organized in real-time, not translated afterward.

**Current Reality:**
- AI chat has context limits (token windows)
- You can't go back and accurately grab what was said
- When context resets, you lose everything
- Claude Code isn't optimized for this - it's designed for back-and-forth coding help

**What This Tool Does:**
- Captures EVERYTHING in real-time
- Organizes it into Agent OS structure automatically
- Nothing is lost, nothing is watered down
- Handles context handoffs gracefully (Baton system)
- Trains the USER to think in structured specs

### Target User
- "Vibe coders" - People who build with AI by talking/ranting
- Non-technical founders who think by speaking
- Anyone who produces ideas faster than they can type
- People who hate stopping to "write documentation"

### Core Value Proposition
**Turn stream-of-consciousness rants into production-ready Agent OS specs without stopping to organize.**

### The Vision
After using this tool for months, the user will:
1. Naturally speak in Agent OS format
2. Never lose an idea or detail
3. Have complete specs ready for any coding AI
4. Be able to do "elevator pitch" versions (2/5/10 min summaries)

---

## LAYER 3: SPECS

### Current State (What's Built)

#### Existing Features
1. **Chat Interface** - Talk to AI about your project
2. **Node System** - Create/manage project components
3. **Auto Node Detection** - Detects potential nodes from chat
4. **Baton System** - Handles context handoffs
5. **Truth Doc Export** - Export entire project as markdown
6. **Token Tracking** - Monitor context usage
7. **Process Log** - Debug/monitoring

#### What Needs to Be Built
The **Agent OS Auto-Generator** - The core innovation described below.

---

### THE 18 MECHANISMS

These are the specific features to implement. Each one is revolutionary in its own right.

#### Mechanism 1: Flash Labels (Real-Time Prompts)
**What:** When a new idea/branch is created, show what Agent OS fields need filling.
**How:** Flash on screen: [Overview] [Requirements] [User Stories] [Technical] [Metrics]
**Why:** Guides the rant without stopping it. User learns Agent OS structure by seeing it.
**Priority:** HIGH - Core to the system

#### Mechanism 2: Click-to-Rant (Tap and Talk)
**What:** Click on a label/field, then speak - voice fills that field.
**How:** Tap "Requirements" → Everything spoken goes into Requirements section.
**Why:** No typing. No stopping. Tap and talk at speed of thought.
**Priority:** HIGH - Enables voice-first workflow

#### Mechanism 3: Real-Time Tagging (Tag While Ranting)
**What:** One continuous rant, but tap to TAG sections as you go.
**How:** Talk continuously. Tap buttons to mark "this part = Feature X". Backend tracks timestamps.
**Output:** Two versions: raw rant (preserved) + tagged/organized structure.
**Why:** Rant stays natural. Organization happens simultaneously.
**Priority:** HIGH - Core innovation, nothing like it exists

#### Mechanism 4: Cockpit Dashboard Mode
**What:** Like airplane cockpit - many small panels, all visible, tap to expand.
**How:** Grid of tools. Tap any → expands. Tap again → shrinks. Multiple can be expanded.
**Why:** Everything accessible. User decides what to use moment-to-moment.
**Priority:** MEDIUM - After core mechanisms work

#### Mechanism 5: Independent Mode Testing
**What:** Test each approach separately before combining.
**How:** Hour 1: Only tagging mode. Hour 2: Only batch mode. Hour 3: Only labels. Then combine.
**Why:** Learn what works through actual use. Data-driven decisions.
**Priority:** MEDIUM - Part of testing infrastructure

#### Mechanism 6: Post-Rant Dissection (Fallback)
**What:** If nothing happens in real-time, AI analyzes entire rant afterward.
**How:** Click "Analyze" → AI processes full rant → Extracts to Agent OS → Shows gaps.
**Why:** Safety net. Some days you just want to flow. Organization can happen after.
**Priority:** HIGH - Fallback that always works

#### Mechanism 7: Gap Detection + Fill Request
**What:** System identifies what's missing from Agent OS spec.
**How:** "You covered X, Y, Z but missing A, B" → Can voice-fill gaps.
**Why:** User doesn't know what they don't know. System sees the gaps.
**Priority:** HIGH - Ensures completeness

#### Mechanism 8: Raw Rant Preservation
**What:** ALWAYS keep original unstructured rant, no matter what.
**How:** Every word recorded verbatim. Never modified. Can always access source.
**Why:** Raw rant IS the truth. Organization might miss nuance. Can re-analyze later.
**Priority:** MUST HAVE - Non-negotiable

#### Mechanism 9: Training Effect
**What:** Using the system trains the user to think in Agent OS format.
**How:** Flash labels show what's needed. User anticipates them over time. Becomes natural.
**Outcome:** After months, user speaks fluently in Agent OS.
**Priority:** LOW (happens naturally) - Track for feedback

#### Mechanism 10: Voice-First Everything
**What:** Entire system designed for voice, not typing.
**How:** Tap to select field. Voice fills content. Minimal typing.
**Future:** Custom speech-to-text for better accuracy.
**Priority:** HIGH - Core philosophy

#### Mechanism 11: Idea Bank (Daily Warmup)
**What:** Bank of best ideas reviewed DAILY when logging in.
**How:** Log in → See best ideas first. Review for few minutes. Build confidence.
**Why:** Not "save for later" - it's "use every day until it's in your DNA."
**Priority:** HIGH - Novel concept, universally applicable

#### Mechanism 12: Raw Rant + Tag Overlay Toggle
**What:** Toggle filter that shows tags overlaid on raw rant.
**How:** Default: raw text. Toggle: tags appear inline. Hover: shows Agent OS location.
**Why:** See connections without losing original. Visual understanding of structure.
**Priority:** MEDIUM - Enhancement to core

#### Mechanism 13: Multi-Monaco Live Fill
**What:** Watch multiple Agent OS sections being filled simultaneously.
**How:** Mini Monaco editors pop up. See cursors filling Features, Requirements, Technical at once.
**Why:** Visual feedback. Learn structure by watching. Motivating.
**Priority:** MEDIUM - Visual enhancement

#### Mechanism 14: Click-to-Expand Live Fill
**What:** Any mini Monaco window can expand for more detail.
**How:** Click small window → Expands to larger view → See full context.
**Why:** Can focus on any section. Dive deeper when needed.
**Priority:** LOW - Enhancement to #13

#### Mechanism 15: Gap Percentage + Fill Request
**What:** Show exact completion percentage and what's missing.
**How:** "Agent OS: 87% complete. Missing: 8 items across 5 sections."
**Why:** Clear metric. Guides to 100% completion. Gamification.
**Priority:** HIGH - Drives completeness

#### Mechanism 16: Pause/Resume with Context Refresh
**What:** Pause work, come back later with scaled context refresh.
**How:** Away 1 hour = quick summary. Away 1 week = full walkthrough.
**Why:** Life happens. System adapts to time away.
**Priority:** MEDIUM - Quality of life

#### Mechanism 17: Voice Output / Read Back
**What:** System talks TO user. Listen while doing other tasks.
**How:** "Read me the current spec." Listen while taking supplements, eating, etc.
**Why:** Don't have to read everything. Audio expands usability.
**Priority:** FUTURE - After core works

#### Mechanism 18: Pattern-Based Screen Combos
**What:** System learns which sections fill together, auto-shows them.
**How:** "When you talk about UI, these 3 sections fill" → Auto-arrange screens.
**Why:** Personalized. Learns your patterns.
**Priority:** LOW - Long-term enhancement

---

### BUILD PHASES

#### Phase 1: Foundation (MVP)
**Goal:** Working system with basic real-time organization

| Feature | Description | Status |
|---------|-------------|--------|
| Agent OS Structure | 3-layer document template | TO BUILD |
| Enhanced Detection | Classify to Agent OS sections (not just nodes) | TO BUILD |
| Raw Preservation | Save original rant exactly | TO BUILD |
| Simple Live Tree | See ideas organize as you talk | PARTIAL (node detection exists) |
| Consolidate Button | Process full rant → Agent OS output | TO BUILD |

**Files to Create/Modify:**
- `app/services/agent_os_service.py` (NEW)
- `app/ui/agent_os_panel.py` (NEW)
- `app/ui/layout.py` (ADD agent OS tab)

#### Phase 2: Core Mechanisms
**Goal:** The revolutionary features

| Feature | Mechanism # | Status |
|---------|-------------|--------|
| Flash Labels | #1 | TO BUILD |
| Click-to-Rant | #2 | TO BUILD |
| Real-Time Tagging | #3 | TO BUILD |
| Gap Detection | #7 | TO BUILD |
| Gap Percentage | #15 | TO BUILD |

#### Phase 3: Visual Feedback
**Goal:** Watch Agent OS being built

| Feature | Mechanism # | Status |
|---------|-------------|--------|
| Tag Overlay Toggle | #12 | TO BUILD |
| Multi-Monaco Live Fill | #13 | TO BUILD |
| Click-to-Expand | #14 | TO BUILD |

#### Phase 4: Flexibility & Testing
**Goal:** Try different approaches

| Feature | Mechanism # | Status |
|---------|-------------|--------|
| Cockpit Dashboard | #4 | TO BUILD |
| Independent Testing | #5 | TO BUILD |
| Lab Mode | - | TO BUILD |
| Config Levers | - | TO BUILD |

#### Phase 5: Learning & Memory
**Goal:** System that grows with user

| Feature | Mechanism # | Status |
|---------|-------------|--------|
| Idea Bank | #11 | TO BUILD |
| Pause/Resume | #16 | TO BUILD |
| Pattern Learning | #18 | FUTURE |

#### Phase 6: Voice Integration
**Goal:** Full audio in/out

| Feature | Mechanism # | Status |
|---------|-------------|--------|
| Voice Output | #17 | FUTURE |
| Better STT | #10 | FUTURE |
| Voice Commands | - | FUTURE |

---

### AGENT OS OUTPUT FORMAT

When the system generates an Agent OS document, it should follow this structure:

```markdown
# Agent OS: [Feature/Project Name]

## STANDARDS LAYER

### Technology Stack
- [Tech decisions mentioned]

### Architecture
- [Structural decisions]

### Coding Patterns
- [Style/pattern decisions]

---

## PRODUCT LAYER

### Vision
[What problem does this solve? Ultimate goal?]

### Target Users
[Who is this for?]

### Core Use Cases
1. [Use case 1]
2. [Use case 2]

### Roadmap
- Phase 1: [Current]
- Phase 2: [Next]
- Future: [Long-term]

---

## SPEC LAYER

### Feature: [Name]

#### Overview
[Brief description]

#### Requirements
**Functional:**
1. [Requirement 1]
2. [Requirement 2]

**Technical:**
1. [Requirement 1]
2. [Requirement 2]

#### User Stories
- As a [user], I want to [action] so that [benefit]

#### Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

#### Technical Specification
- API Endpoints: [if any]
- Data Models: [if any]
- Dependencies: [what's needed first]
- Edge Cases: [what to handle]

#### Success Metrics
[How do we measure if this worked?]

---

## GAPS / QUESTIONS
- [ ] [Missing info 1]
- [ ] [Missing info 2]

## COMPLETION: [X]%
```

---

### DETECTION LOGIC

When analyzing conversation, classify each piece of information:

| User Says | Classification | Agent OS Location |
|-----------|---------------|-------------------|
| "I want it built in React" | Tech Decision | STANDARDS → Tech Stack |
| "This is for small remote teams" | Target User | PRODUCT → Target Users |
| "The whole point is simplicity" | Vision | PRODUCT → Vision |
| "Users need to create tasks fast" | Use Case | PRODUCT → Use Cases |
| "The dashboard shows all tasks" | Feature Requirement | SPEC → Requirements |
| "When they click, it should..." | User Story | SPEC → User Stories |
| "It has to work offline" | Technical Requirement | SPEC → Edge Cases |
| "Success means 2x faster" | Metric | SPEC → Success Metrics |
| "Should handle 1000 users" | Constraint | SPEC → Technical Spec |

---

### THE PHILOSOPHY (Important for Any New Agent)

1. **This is NOT just another note-taking app.** It's a real-time thought-to-spec converter.

2. **The brainstorm IS the documentation.** Don't treat them as separate steps.

3. **Voice-first, not type-first.** User thinks at speaking speed. Typing breaks flow.

4. **Nothing is ever lost.** Raw rant always preserved. Can always go back.

5. **The system teaches the user.** Over time, they learn to think in Agent OS format.

6. **Test everything.** Don't hard-code one approach. Build flexibility to experiment.

7. **Old coding mindset is WRONG for this.** Traditional development couldn't afford to experiment. Vibe coding can test anything.

8. **The user is a RANTER.** They produce ideas every 20 seconds in flow state. Don't interrupt with questions. Queue them for later.

9. **Visual feedback matters.** Seeing ideas organize helps produce better ideas. It's a feedback loop.

10. **This solves the context window problem.** When context resets, the spec document persists. The tool IS the memory.

---

### WHAT EXISTS VS WHAT NEEDS BUILDING

**ALREADY BUILT:**
- Basic Streamlit app structure
- Chat with OpenAI integration
- Node system (create, edit, delete, version)
- Auto-node detection from chat (basic)
- Baton system for context handoffs
- Token tracking
- Truth Doc export
- Process logging
- User/Project management
- Settings management

**NEEDS BUILDING (Priority Order):**
1. Agent OS document structure/template
2. Enhanced detection → Agent OS sections (not just nodes)
3. Live Tree visualization during chat
4. Flash Labels showing what's needed
5. Gap detection and percentage
6. Click-to-Rant with voice input
7. Real-Time Tagging interface
8. Consolidate → Agent OS generation
9. Idea Bank tab
10. Cockpit Dashboard mode

---

### IMMEDIATE NEXT STEPS

If you're a new agent continuing this work:

1. **Read this entire document first**
2. **Check the current codebase** - Especially `node_detector.py` and `layout.py`
3. **Start with Phase 1** - Agent OS structure and enhanced detection
4. **Test with user** - They will rant, you capture, iterate
5. **Don't simplify** - This vision is intentionally ambitious

---

### CONTEXT FOR HANDOFF

This blueprint was created during an active development session. The user (project owner) has been designing this system through conversation. Key points:

- User thinks by speaking, not typing
- User has ADHD-like flow states - produces ideas rapidly
- User is non-technical but highly creative
- User learned from expert who uses Agent OS for coding
- User wants this to become the standard for vibe coding

**The irony:** We're building a tool to solve context loss, while experiencing context loss. This document is the bridge until the tool exists.

---

## APPENDIX: THE REVOLUTIONARY IDEAS (Idea Bank)

These mechanisms are universally applicable beyond this app:

### 1. Real-Time Tagging While Ranting
Talk continuously + tap to tag = organized output without stopping flow. No one does this.

### 2. Flash Labels (Guided Ranting)
Show what's NEEDED, not what's been SAID. Guides thinking without interrupting.

### 3. Gap Percentage + Fill Request
Not "what did you say" but "what's still missing." System knows completeness.

### 4. Idea Bank (Daily Warmup)
Review best ideas daily until they're in your DNA. Ideas compound with repetition.

### 5. Pause/Resume with Scaled Refresh
Time away determines context refresh depth. 1 hour vs 1 week = different summaries.

### 6. Multi-Monaco Live Fill
Watch documentation being written in multiple places simultaneously as you speak.

---

**END OF BLUEPRINT**

*If you're an AI agent reading this: The user trusts you to continue this vision. Don't let them down. Build something revolutionary.*
