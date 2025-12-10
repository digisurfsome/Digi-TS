# HANDOFF SCRIPT: Design Tree Studio Agent OS Build

**CRITICAL: READ THIS ENTIRE DOCUMENT BEFORE DOING ANYTHING**

---

## STOP. DO NOT CODE YET.

If you're a new agent picking this up, you MUST:

1. Read this entire document (5 min)
2. Read `AGENT_OS_BLUEPRINT.md` (10 min)
3. Understand the phases below
4. Execute phases IN ORDER with testing between each
5. DO NOT skip steps or combine phases

**The previous agent documented everything. Your job is to BUILD, not redesign.**

---

## PHASE OVERVIEW

There are **6 phases**. Execute them in order. Test thoroughly after each phase before moving to the next.

| Phase | Description | Est. Complexity |
|-------|-------------|-----------------|
| 1 | Agent OS Structure & Service | Medium |
| 2 | Enhanced Detection (Rant → Agent OS) | Medium |
| 3 | Live Tree Visualization | Medium |
| 4 | Flash Labels + Gap Detection | Medium |
| 5 | Real-Time Tagging UI | High |
| 6 | Cockpit Dashboard + Idea Bank | High |

---

## PHASE 1: Agent OS Structure & Service

### Goal
Create the Agent OS document structure and a service to manage it.

### Tasks
1. Create `app/services/agent_os_service.py` with:
   - `AgentOSDocument` class (Standards, Product, Specs layers)
   - `create_agent_os_for_project(db, project_id)` - Initialize empty Agent OS
   - `get_agent_os(db, project_id)` - Retrieve current Agent OS
   - `update_agent_os_section(db, project_id, layer, section, content)` - Update a section
   - `get_agent_os_completion_percentage(db, project_id)` - Calculate % complete
   - `get_agent_os_gaps(db, project_id)` - List missing sections

2. Create database model for Agent OS storage (or use JSON in ProjectContext)

3. Export from `app/services/__init__.py`

### Testing Checklist
- [ ] Can create new Agent OS for a project
- [ ] Can retrieve Agent OS
- [ ] Can update individual sections
- [ ] Completion percentage calculates correctly
- [ ] Gaps detection works
- [ ] No import errors
- [ ] App still runs without crashes

### Test Commands
```bash
# Syntax check
python -m py_compile app/services/agent_os_service.py

# Import check
python -c "from app.services.agent_os_service import *; print('OK')"

# Run app locally (if possible)
streamlit run app/streamlit_app.py
```

### Success Criteria
All checkboxes checked. Move to Phase 2.

---

## PHASE 2: Enhanced Detection (Rant → Agent OS)

### Goal
Upgrade the existing node detector to classify content into Agent OS sections.

### Tasks
1. Create `app/services/agent_os_detector.py` with:
   - Detection prompt that classifies into Agent OS sections (not just nodes)
   - `detect_agent_os_elements(user_message, ai_response, api_key)` function
   - Returns list of `DetectedElement` with:
     - `layer`: standards | product | spec
     - `section`: specific section name
     - `content`: the actual content
     - `confidence`: 0.0-1.0
     - `source_text`: what triggered detection

2. Classification logic:
   - "I want it built in React" → STANDARDS > Tech Stack
   - "This is for small teams" → PRODUCT > Target Users
   - "Users need to..." → PRODUCT > Use Cases
   - "The dashboard shows..." → SPEC > Requirements
   - "When they click..." → SPEC > User Stories
   - "It has to work offline" → SPEC > Edge Cases

3. Export from `app/services/__init__.py`

### Testing Checklist
- [ ] Detection prompt works with sample text
- [ ] Correctly classifies tech decisions to Standards
- [ ] Correctly classifies user descriptions to Product
- [ ] Correctly classifies features to Spec
- [ ] Returns proper structure
- [ ] Handles edge cases (empty input, no detections)

### Test Commands
```bash
# Syntax check
python -m py_compile app/services/agent_os_detector.py

# Manual test with sample input (create a test script if needed)
```

### Success Criteria
All checkboxes checked. Move to Phase 3.

---

## PHASE 3: Live Tree Visualization

### Goal
Show ideas organizing into a tree structure as the user chats.

### Tasks
1. Create `app/ui/agent_os_panel.py` with:
   - `render_agent_os_tree(db, project_id)` - Shows tree of detected elements
   - Tree structure: Layer > Section > Items
   - Color coding by layer (Standards=blue, Product=green, Spec=orange)
   - Expandable/collapsible sections

2. Add "Agent OS" tab to main app in `streamlit_app.py`

3. Integrate with chat flow in `layout.py`:
   - After each message, call detector
   - Update Agent OS document
   - Tree reflects new additions

### Testing Checklist
- [ ] Agent OS tab appears in app
- [ ] Tree renders without errors
- [ ] Tree shows correct hierarchy
- [ ] New detections appear in tree
- [ ] Expand/collapse works
- [ ] Colors are correct

### Test Commands
```bash
# Run the app and manually test the UI
streamlit run app/streamlit_app.py
```

### Success Criteria
All checkboxes checked. Move to Phase 4.

---

## PHASE 4: Flash Labels + Gap Detection

### Goal
Show what Agent OS fields need filling, and highlight gaps.

### Tasks
1. Add to `agent_os_panel.py`:
   - `render_flash_labels(db, project_id)` - Shows unfilled sections
   - Visual indicators for empty/partial/complete sections
   - Gap percentage display ("Agent OS: 67% complete")

2. Add gap summary to chat panel:
   - After detection, show "3 new items added, 5 gaps remaining"
   - List top gaps that need filling

3. Add to `agent_os_service.py`:
   - `get_priority_gaps(db, project_id, limit=5)` - Most important missing sections

### Testing Checklist
- [ ] Flash labels appear for empty sections
- [ ] Completion percentage shows correctly
- [ ] Gap list is accurate
- [ ] UI updates when sections are filled
- [ ] Priority gaps are logical

### Success Criteria
All checkboxes checked. Move to Phase 5.

---

## PHASE 5: Real-Time Tagging UI

### Goal
Allow user to tap/click to tag what they're currently talking about.

### Tasks
1. Add tagging buttons to chat panel:
   - Row of buttons: [Overview] [Requirements] [Stories] [Technical] [Metrics]
   - Clicking a button "activates" that tag
   - Next message goes to that section
   - Visual indicator of active tag

2. Add to `layout.py`:
   - Session state for `active_tag`
   - Modified message handling to route to tagged section
   - Tag indicator in chat display

3. Store tagged segments:
   - Track which parts of conversation were tagged
   - Allow viewing by tag (filter chat by section)

### Testing Checklist
- [ ] Tag buttons appear
- [ ] Clicking activates tag (visual feedback)
- [ ] Message routes to correct section
- [ ] Can switch tags mid-conversation
- [ ] Tagged history is preserved

### Success Criteria
All checkboxes checked. Move to Phase 6.

---

## PHASE 6: Cockpit Dashboard + Idea Bank

### Goal
Multiple panels visible at once, plus daily idea review.

### Tasks
1. Create cockpit layout:
   - Grid of small panels
   - Each panel can expand/collapse
   - Panels: Chat, Tree, Agent OS, Gaps, Tags

2. Create Idea Bank:
   - New model: `IdeaBank` or similar
   - Store revolutionary ideas/mechanisms
   - Show on login as "Daily Warmup"
   - Can add/edit/archive ideas

3. Add Idea Bank tab to main app

### Testing Checklist
- [ ] Cockpit layout renders
- [ ] Panels expand/collapse correctly
- [ ] Multiple panels can be open
- [ ] Idea Bank tab appears
- [ ] Can add new ideas
- [ ] Ideas show on login/startup
- [ ] Can archive/edit ideas

### Success Criteria
All checkboxes checked. FULL SYSTEM TEST.

---

## FINAL SYSTEM TEST

After all phases complete:

1. **Fresh start test:**
   - Create new project
   - Start chatting about a feature
   - Verify Agent OS populates automatically
   - Verify tree shows organization
   - Verify gaps are detected

2. **Tagging test:**
   - Use tag buttons while chatting
   - Verify content routes correctly
   - Verify can filter by tag

3. **Completion test:**
   - Fill all Agent OS sections
   - Verify 100% completion shows
   - Export Agent OS document
   - Verify it's properly formatted

4. **Idea Bank test:**
   - Add ideas
   - Close and reopen app
   - Verify ideas show on startup

---

## KEY FILES REFERENCE

```
MODIFY:
- app/services/__init__.py (add exports)
- app/ui/layout.py (integrate detection, add tags)
- app/streamlit_app.py (add tabs)

CREATE:
- app/services/agent_os_service.py
- app/services/agent_os_detector.py
- app/ui/agent_os_panel.py

READ FIRST:
- AGENT_OS_BLUEPRINT.md (full spec)
- app/services/node_detector.py (existing pattern)
- app/core/models.py (existing models)
```

---

## CRITICAL REMINDERS

1. **Test after EVERY phase** - Don't move on until tests pass
2. **Commit after EVERY phase** - `git add . && git commit -m "Phase X complete"`
3. **Don't redesign** - The spec is in AGENT_OS_BLUEPRINT.md, follow it
4. **Don't simplify** - The vision is intentionally ambitious
5. **Voice-first mindset** - User speaks, doesn't type
6. **Preserve raw rant** - Always keep original conversation

---

## IF YOU GET STUCK

1. Re-read AGENT_OS_BLUEPRINT.md
2. Look at existing patterns in node_detector.py
3. Check the 18 mechanisms list
4. Don't invent new approaches - use what's documented

---

## START NOW

1. Read AGENT_OS_BLUEPRINT.md fully
2. Begin Phase 1
3. Test Phase 1
4. Commit Phase 1
5. Continue to Phase 2
6. Repeat until Phase 6 complete
7. Run final system test
8. Report completion

**GO.**
