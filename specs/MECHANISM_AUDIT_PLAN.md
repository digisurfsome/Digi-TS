# Mechanism Audit & Rebuild Plan

**For:** Next Agent Session
**Context:** Opus 4.5 with full context window
**Goal:** Analyze each mechanism, identify gaps, rebuild properly, add testing capabilities

---

## Executive Summary

The user has built **mechanism prototypes** across multiple repos. These represent IDEAS that should work, but were coded pre-Opus 4.5 with less capable models. The code may not properly implement the intended logic.

**Your job:**
1. Reverse-engineer what each mechanism is SUPPOSED to do
2. Analyze if the current code actually does that
3. Identify gaps (intent vs implementation)
4. Rebuild properly with Opus 4.5
5. Add testing/alteration knobs throughout
6. Connect mechanisms into unified system

**User context:** Not a coder. Came up with ideas, AI coded them. Cannot verify if code matches intent. Needs you to be the expert who audits and fixes.

---

## The Big Picture Flow

```
USER RANT
    ↓
CRISP DESIGN (AI asks clarifying questions until spec is clear)
    ↓
AGENT OS PLAN (Break into phases, each testable)
    ↓
ROUNDTABLE CODING (Multiple agents, consensus-based)
    │
    │   ← Knowledge injection RIGHT BEFORE coding
    │     (coding standards, domain knowledge, etc.)
    │
    ↓
PHYSICAL TESTING (Run app, detect errors visually)
    ↓
ERROR LOOP (Send failures back to Roundtable)
    ↓
WORKING SOFTWARE
```

**Key insight from user:** The knowledge injection happens "a split second before" the agent codes. Remind them of best practices RIGHT BEFORE execution.

---

## Mechanism #1: Roundtable Coder

**Location:** `/home/user/Digi-TS/app/services/roundtable_service.py`

### What It's SUPPOSED To Do

```
1. Multiple agents with roles (Builder, Voter, Reviewer)
2. Builder(s) generate code for a task
3. Voter(s) review and vote (approve/reject/revise)
4. Consensus determines if code is accepted
5. If rejected, iterate with feedback
6. Store decisions in memory (RAG)
```

### What To Audit

1. **Multi-agent execution:**
   - Do multiple builders actually run? Or just `builders[0]`?
   - Check line ~880: `builder = builders[0]` - is this intentional or bug?

2. **Voting mechanism:**
   - Do voters actually get builder output?
   - Is vote counting implemented?
   - What happens on tie/split vote?

3. **Consensus logic:**
   - What threshold for acceptance?
   - Does rejection trigger re-iteration?

4. **Knowledge injection:**
   - Is there a pre-execution step that injects standards?
   - Where does domain knowledge get loaded?

### Gap Analysis Questions

- [ ] Does `execute_round()` run all builders or just first?
- [ ] Does `process_votes()` actually count votes?
- [ ] Is there a `inject_knowledge()` or similar before execution?
- [ ] What triggers iteration on rejection?

### Testing Knobs To Add

```python
ROUNDTABLE_CONFIG = {
    "num_builders": 1,           # How many builders run
    "num_voters": 2,             # How many voters
    "consensus_threshold": 0.66, # % needed to pass
    "max_iterations": 3,         # Retry limit
    "inject_standards": True,    # Load coding standards before
    "inject_domain": True,       # Load domain knowledge before
    "log_all_outputs": True,     # Debug logging
}
```

---

## Mechanism #2: Physical Testing (StreamTest)

**Location:** `/home/user/external/StreamTest/`

### What It's SUPPOSED To Do

```
1. Launch browser, navigate to app URL
2. Parse test manual (markdown with test cases)
3. For each test step:
   a. Screenshot current state
   b. Send to vision model: "What action for this instruction?"
   c. Execute action (click/type/scroll)
   d. Screenshot result
   e. Send to vision model: "Did instruction complete?"
   f. Mark pass/fail
4. Collect failures
5. Send failures to Roundtable for fixing
6. Re-run tests after fix
```

### What User Said About It

- "The errors kept coming back as defined" - detection worked
- "It would build some of them" - fixes partially worked
- "Not doing it clean" - the FIX code wasn't clean, not the test detection
- Problem was the Roundtable fixing, not the test finding

### What To Audit

1. **Test detection:**
   - Is Gemini the right model for vision?
   - Does it accurately identify what's on screen?
   - Does it give actionable instructions?

2. **Action execution:**
   - Are click coordinates accurate?
   - Does typing work reliably?
   - Timing issues between actions?

3. **Pass/fail assessment:**
   - How does it know "instruction complete"?
   - False positives? False negatives?

4. **Error handoff:**
   - What exactly gets sent to Roundtable?
   - Screenshots? Error messages? Both?
   - Is context sufficient for fixer to understand?

### Knowledge Injection (User Mentioned)

The user said StreamTest had:
- "Basic coding principles" loaded before fixing
- "Database knowledge" loaded
- Clean code design 101 being referenced

**Check if this exists in code. If not, it needs to be added.**

### Gap Analysis Questions

- [ ] Is knowledge injection implemented or just planned?
- [ ] What format are errors sent to Roundtable?
- [ ] Is there a retry loop or one-shot?
- [ ] Can we swap Gemini for Claude vision easily?

### Testing Knobs To Add

```python
PHYSICAL_TEST_CONFIG = {
    "vision_model": "gemini-2.0",    # Swappable
    "screenshot_before_action": True,
    "screenshot_after_action": True,
    "action_delay_ms": 500,          # Between actions
    "max_actions_per_step": 50,
    "pass_confidence_threshold": 0.8,
    "save_all_screenshots": True,
    "error_context_format": "detailed", # minimal, detailed, verbose
}
```

---

## Mechanism #3: Knowledge Extractor

**Location:** `/home/user/external/Knowledge-Extractor/`

### What It's SUPPOSED To Do

```
1. Take URL(s) as input
2. Fetch page content (HTTP or Playwright for protected sites)
3. Parse HTML, extract main content
4. Group into sections (heading → paragraphs → images)
5. Extract terms and definitions
6. Output structured JSON
7. Feed into RAG for agent knowledge
```

### What User Said About It

- "Actually did a great job"
- "Put in a great format"
- Used for photographer terminology
- Fed to agents RIGHT BEFORE they'd reverse-engineer images

### What To Audit

1. **Extraction quality:**
   - Does section grouping work?
   - Are terms/definitions accurate?
   - Image context preserved?

2. **RAG integration:**
   - Does extracted JSON actually go into ChromaDB?
   - Is it retrievable during agent execution?
   - Timing: is it injected "right before" coding?

3. **Domain flexibility:**
   - Works for photography terminology
   - Does it work for coding docs? API docs?

### Gap Analysis Questions

- [ ] Is RAG import implemented or manual?
- [ ] When/how does extracted knowledge get injected?
- [ ] Is extraction customizable per domain?
- [ ] Batch processing working?

### Testing Knobs To Add

```python
EXTRACTOR_CONFIG = {
    "use_browser": False,           # Playwright fallback
    "min_section_length": 50,       # Skip tiny sections
    "extract_images": True,
    "extract_code_blocks": True,
    "max_pages_per_crawl": 20,
    "auto_import_to_rag": True,
    "rag_category": "domain_knowledge",
}
```

---

## Mechanism #4: Agent OS (Rant → Spec)

**Location:** `/home/user/Digi-TS/app/services/agent_os_service.py`

### What It's SUPPOSED To Do

```
1. Take raw rant/stream-of-consciousness input
2. AI asks clarifying questions until complete
3. Transform into structured specification
4. Break into phases (each independently testable)
5. Each phase has: description, files, tests, acceptance criteria
```

### What To Audit

1. **Rant processing:**
   - Does it actually ask clarifying questions?
   - Or just process whatever is given?

2. **Gap detection:**
   - Does it identify missing information?
   - Does it prompt user or guess?

3. **Phase breakdown:**
   - Are phases actually independent?
   - Are acceptance criteria testable?

### Gap Analysis Questions

- [ ] Is clarifying question loop implemented?
- [ ] Does phase breakdown match Agent OS spec format?
- [ ] Are phases connected to Roundtable execution?

---

## Mechanism #5: RAG Memory System

**Location:** `/home/user/Digi-TS/app/services/rag_service.py`

### What It's SUPPOSED To Do

```
1. Store decisions, code changes, conversations
2. Vector search for relevant context
3. Inject into agent prompts when relevant
4. Learn from past sessions
```

### What To Audit

1. **Storage:**
   - What's actually being stored?
   - Embeddings working?

2. **Retrieval:**
   - Is it injected into prompts?
   - At what point in execution?

3. **Knowledge injection timing:**
   - "Right before" agent executes
   - Is this implemented?

---

## Audit Process For Each Mechanism

```
FOR EACH MECHANISM:

1. READ THE CODE
   - Main service file
   - UI panel if exists
   - Tests if exist

2. DOCUMENT WHAT IT DOES
   - Step by step, what does the code actually do?
   - Not what it's supposed to do - what it DOES

3. COMPARE TO INTENT
   - Based on user description, what SHOULD it do?
   - Where are the gaps?

4. LIST ISSUES
   - Missing functionality
   - Bugs or incorrect logic
   - Hardcoded values that should be configurable

5. DESIGN FIX
   - What changes needed?
   - What config knobs to add?

6. IMPLEMENT
   - Rebuild the mechanism properly
   - Add testing capabilities
   - Add AI-controllable settings

7. TEST
   - Does it work as intended now?
   - Can settings be altered?
   - Does AI testing logic work?
```

---

## Testing & Alteration System

**The user's key insight:**

> "The only way you can test is by altering"

Every mechanism needs:

### 1. Configuration Knobs
```python
# Every setting externalized
config = {
    "setting_name": default_value,
    # ...
}
```

### 2. AI Test Controller
```python
class AITestController:
    """AI brain that controls testing."""

    def suggest_test(self, mechanism, current_config):
        """AI suggests what to test next."""
        pass

    def analyze_result(self, test_result):
        """AI analyzes test outcome."""
        pass

    def suggest_alteration(self, results_history):
        """AI suggests config changes to try."""
        pass
```

### 3. Result Logging
```python
# Every test run logged
test_log = {
    "timestamp": ...,
    "mechanism": ...,
    "config_used": {...},
    "result": {...},
    "ai_analysis": "..."
}
```

### 4. A/B Testing Support
```python
# Run same task with different configs
results_a = run_with_config(config_a)
results_b = run_with_config(config_b)
comparison = ai_compare(results_a, results_b)
```

---

## Execution Order

### Session 1: Roundtable Audit
1. Read `roundtable_service.py` completely
2. Document actual execution flow
3. Identify gaps (multi-agent, voting, injection)
4. Add config knobs
5. Rebuild if needed

### Session 2: Physical Testing Audit
1. Read StreamTest files
2. Document actual flow
3. Check knowledge injection exists
4. Add config knobs
5. Wire error→roundtable loop

### Session 3: Knowledge Extractor Audit
1. Read extractor files
2. Test extraction quality
3. Wire to RAG import
4. Add injection timing

### Session 4: Agent OS + RAG Audit
1. Read both services
2. Document flows
3. Connect clarifying questions
4. Verify injection timing

### Session 5: Integration
1. Connect all mechanisms
2. End-to-end test
3. Add AI test controller
4. Document final system

---

## Summary For Next Agent

**Don't assume anything works.**

Read the code. Document what it ACTUALLY does. Compare to what it SHOULD do. Fix the gaps. Add testing knobs. Rebuild with Opus 4.5 quality.

The mechanisms are good ideas. The implementation may be flawed. Your job is to make the implementation match the idea.

**Start with Roundtable** - it's the core. If multi-agent consensus doesn't work, nothing else matters.
