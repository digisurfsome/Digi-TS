# QUICK START: For AI Agents Continuing This Project

**Read time: 2 minutes**

---

## WHAT IS THIS?

Design Tree Studio is a **real-time thought-to-spec converter**. Users rant/brainstorm out loud, and the system automatically organizes it into Agent OS documentation format.

**The core insight:** The brainstorm IS the documentation. Don't translate afterward - capture and organize in real-time.

---

## CURRENT STATE

**Working:**
- Streamlit app deployed on Railway
- Chat with OpenAI integration
- Basic node detection from chat
- Baton system for context handoffs
- Token tracking

**Needs Building:**
- Agent OS auto-generation (the main feature)
- Real-time tagging while ranting
- Flash labels showing what's needed
- Gap detection and fill requests
- Live tree visualization

---

## YOUR FIRST TASK

Read `AGENT_OS_BLUEPRINT.md` in the repo root. It contains:
- All 18 mechanisms to implement
- Build phases with priorities
- Detection logic
- Philosophy and principles

---

## KEY FILES

```
app/services/node_detector.py  ← Enhance this for Agent OS detection
app/ui/layout.py               ← Main UI, add Agent OS panel here
app/services/__init__.py       ← Export new services
AGENT_OS_BLUEPRINT.md          ← Full specification (READ THIS)
```

---

## THE USER

- Thinks by speaking, not typing
- Produces ideas rapidly (every 20 seconds in flow)
- Non-technical but highly creative
- DON'T interrupt with questions - queue them for later
- Wants voice-first, not type-first

---

## WHAT TO BUILD FIRST

1. **Agent OS document structure** - Template for the 3-layer format
2. **Enhanced detection** - Classify rant segments into Agent OS sections
3. **Live tree view** - Show ideas organizing as they speak
4. **Flash labels** - Show what Agent OS fields need filling
5. **Gap percentage** - "87% complete, 13% gaps to fill"

---

## DON'T DO THIS

- Don't simplify the vision - it's intentionally ambitious
- Don't hard-code one approach - build for testing multiple
- Don't interrupt flow state - queue questions for breaks
- Don't lose the raw rant - always preserve original

---

## PHILOSOPHY (Quick Version)

1. Brainstorm = Documentation (same thing, just needs organizing)
2. Voice-first (speaking speed > typing speed)
3. Nothing ever lost (raw rant always preserved)
4. System teaches user (they learn Agent OS by using it)
5. Test everything (build flexibility to experiment)

---

## IF YOU GET CUT OFF

The full blueprint is in `AGENT_OS_BLUEPRINT.md` - it persists in the repo. Any new agent can pick up from there.

---

**Now go read the full blueprint and start building.**
