# Design Tree Studio - Complete User Guide

**AI-Powered Design Management System**

Transform messy brainstorms into structured specifications through AI-assisted documentation.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Interface Overview](#interface-overview)
3. [Core Tabs](#core-tabs)
   - [System Status](#1-system-status)
   - [Settings](#2-settings)
   - [Project Context](#3-project-context)
   - [Design Tree](#4-design-tree)
   - [Agent OS](#5-agent-os)
   - [Idea Bank](#6-idea-bank)
   - [Lab Mode](#7-lab-mode)
   - [Truth Doc](#8-truth-doc)
   - [Process Log](#9-process-log)
   - [Roundtable Coder](#10-roundtable-coder)
4. [Key Features](#key-features)
5. [Daily Workflow](#daily-workflow)
6. [Tips & Tricks](#tips--tricks)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### First Time Setup (5 minutes)

1. **Go to System Status tab** - Check that database is connected
2. **Click "Initialize Schema"** - Creates all required database tables
3. **Go to Settings tab** - Enter your OpenAI API key
4. **Save Settings** - You're ready to go!

### Daily Use (2 minutes)

1. **Select a User** - Use the dropdown in the left sidebar
2. **Select or Create a Project** - Click the project dropdown or "+ New" button
3. **Complete Daily Warmup** - Review your top ideas when prompted
4. **Start Chatting** - Type in the chat box to talk to AI
5. **Organize Ideas** - Use Design Tree and Agent OS tabs

---

## Interface Overview

### Left Side: AI Chat Panel

| Element | What It Does |
|---------|--------------|
| **Project Banner** | Shows current project name |
| **Chat History** | Your conversation with AI |
| **Token Usage Bar** | Shows context budget used (green → yellow → red) |
| **Message Input** | Type your messages here |
| **Send Button** | Send your message |
| **Clear Button** | Start a fresh conversation |
| **Baton Now** | Create a snapshot and start new session |

### Right Side: 10 Feature Tabs

| Tab | Purpose |
|-----|---------|
| **System Status** | Check configuration and database health |
| **Settings** | API keys, models, preferences |
| **Project Context** | Background info AI always knows |
| **Design Tree** | Create and manage project components |
| **Agent OS** | Transform rants into specifications |
| **Idea Bank** | Daily learning system for best ideas |
| **Lab Mode** | Test different feature combinations |
| **Truth Doc** | Export project as documentation |
| **Process Log** | Activity audit trail |
| **Roundtable Coder** | Multi-AI code generation with voting |

### Top Bar Features

| Element | What It Does |
|---------|--------------|
| **Layout Mode Toggle** | Switch between Standard and Cockpit views |
| **Learning Status** | Shows warmup status and active idea count |
| **Ideas Counter** | Quick view of Idea Bank status |

---

## Core Tabs

### 1. System Status

Your dashboard for system health and configuration.

**Configuration Status**
- Shows if all required settings are present
- Displays API key sources (environment or database)
- Overall system readiness indicator

**Database Schema**
- Lists all required tables
- Shows which tables exist vs. missing
- **Initialize Schema** button - Creates missing tables

**When to Use:**
- First time setup
- After updates (to create new tables)
- Troubleshooting connection issues

---

### 2. Settings

Configure your API keys and preferences.

**API Configuration**
| Setting | Description |
|---------|-------------|
| OpenAI API Key | Required for chat and AI features |
| Anthropic API Key | For Claude models in Roundtable |
| Google API Key | For Gemini models in Roundtable |
| Default Chat Model | Which AI model for conversations |
| Default Summary Model | Model for auto-descriptions |

**Context & Baton Settings**
| Setting | Description |
|---------|-------------|
| Max Context Tokens | Limit before baton (1,000-128,000) |
| Auto Baton Threshold | % at which to suggest baton (e.g., 80%) |
| Auto Warmup | Enable/disable automatic AI warmup |

**Warmup Prompts (1-4)**
Pre-conditioning messages sent to AI when starting warmed sessions. Customize these to match your workflow.

**Security**
- PIN Code - Optional app lock (requires PIN to access)

---

### 3. Project Context

Background information that AI always knows about your project.

**Description Modes**
| Mode | What AI Sees |
|------|--------------|
| Manual Only | Only your hand-written context |
| Auto-Generated Only | AI-generated summary from nodes |
| Merged | Both combined |

**How to Use:**
1. Write your project requirements, goals, and guidelines
2. Click **Save Manual**
3. AI will reference this in every conversation

**Pro Tip:** The more context you provide, the better AI responses you'll get.

---

### 4. Design Tree

Organize your project into hierarchical components (Nodes).

**Node Types**
| Icon | Type | Use For |
|------|------|---------|
| 🌳 | Root | Top-level project item |
| 📁 | Folder | Group related things |
| 🧩 | Component | Specific features/parts |
| 🎨 | Asset | Design elements, images |
| 📝 | Note | Documentation, thoughts |

**Node Statuses**
| Status | Meaning |
|--------|---------|
| 🟡 Draft | Work in progress |
| 🟢 Active | Finalized/ready |
| 🔵 Archived | No longer active |
| 🔴 Deleted | Marked for removal |

**Creating Nodes:**
1. Go to Design Tree tab
2. Fill in Name, Type, Description
3. Select initial Status (Draft or Active)
4. Click **Create Node**

**Auto Node Detection:**
As you chat, AI watches for things that should become nodes:
- Feature requests
- Component descriptions
- Design decisions
- Important concepts

When detected, a popup appears:
```
🧩 Search Bar (Component)
Real-time product filtering for dashboard
[Create] [Skip]
```

**Rant → Summary Tab:**
1. Dump messy thoughts in the text area
2. Click **Summarize**
3. AI organizes into structured content
4. Save as new node or attach to existing

---

### 5. Agent OS

Transform stream-of-consciousness rants into structured technical specifications.

**The 3-Layer Structure:**

#### Standards Layer (Technical Foundation)
| Section | Content |
|---------|---------|
| Technology Stack | Frameworks, languages, databases |
| Architecture | System design patterns |
| Coding Patterns | Style conventions, naming |

#### Product Layer (Business Requirements)
| Section | Content |
|---------|---------|
| Vision | High-level product vision |
| Target Users | Personas, demographics |
| Use Cases | User scenarios, journeys |
| Roadmap | MVP, phases, priorities |

#### Specs Layer (Detailed Requirements)
| Section | Content |
|---------|---------|
| Overview | Executive summary |
| Functional Requirements | What it must do |
| Technical Requirements | Constraints, performance |
| User Stories | "As a X, I want Y..." |
| Acceptance Criteria | Definition of done |
| Technical Spec | APIs, data models, edge cases |
| Success Metrics | KPIs, measurements |
| Questions | Open unknowns |

**Key Features:**

**Flash Labels** - Visual completion tracking
- Shows real-time completion status
- Color-coded: [x] Complete, [~] Partial, [ ] Empty
- Percentage completion indicator

**Gap Analysis** - Find what's missing
- Identifies empty/incomplete sections
- Categorizes as Critical or Minor
- Suggests what's needed

**Voice Input Modes:**

*Click-to-Rant:*
1. Select target section from dropdown
2. Click record button
3. Speak content for that section
4. AI transcribes and adds to section

*Real-Time Tagging:*
1. Start continuous recording
2. Speak naturally
3. Press tag buttons to mark section switches
4. System organizes by tags automatically

---

### 6. Idea Bank

Your daily learning system - actively surfaces best ideas to build confidence.

**Daily Warmup** (appears on login)
- Shows your top 5 rated ideas
- Review before starting work
- Builds confidence through repetition
- Options: "Got it - Start Working", "Add New Idea", "Skip Today"

**Idea Categories**
| Category | Use For |
|----------|---------|
| 💡 Vision | Big picture ideas |
| ⚡ Feature | Specific functionality |
| 🔍 Insight | Learnings, realizations |
| 🔄 Pattern | Recurring solutions |

**Idea Statuses**
| Status | Meaning |
|--------|---------|
| Active | Shows in daily warmups |
| Retired | Internalized, archived |
| Archived | Hidden but preserved |

**Rating System (1-5 stars)**
Higher-rated ideas appear first in warmups.

**AI Detection**
- Click "Find Valuable Ideas"
- AI analyzes recent rants
- Suggests ideas with confidence scores
- Batch-add detected ideas

**Why It Matters:**
- Ideas aren't a graveyard - they're an active daily practice
- Repetition builds confidence
- Your best thinking resurfaces regularly

---

### 7. Lab Mode

Test different feature combinations to optimize your workflow.

**Lab Mode Toggle**
- Enable/Disable testing mode
- Reset All to restore defaults

**Feature Toggles**
Turn individual features on/off:
- Real-Time Tagging
- Click-to-Rant
- Flash Labels
- Gap Detection
- Tag Overlay View
- Multi-Panel View
- Cockpit Mode
- Auto Consolidate
- Post-Rant Analysis

**Configurations**
- Save multiple test setups
- Load presets (e.g., "Voice-Focused")
- Compare different combinations

**Config Levers**
Fine-tune settings:
| Lever | Options |
|-------|---------|
| Detection Sensitivity | Low, Medium, High |
| Flash Label Timing | Immediate, After 5s, Manual |
| Panel Layout | Standard, Cockpit |
| Required Sections | Minimal, Standard, Complete |

---

### 8. Truth Doc

Export your entire project as documentation.

**How to Use:**
1. Go to Truth Doc tab
2. Check "Include Archived/Deleted" if needed
3. Click **Preview** to see first 100 lines
4. Click **Export** to generate full document
5. Click **Download** to save as .md file

**Document Contains:**
- Project name and description
- All nodes with versions
- Node hierarchy
- Design guidelines
- Complete reference

**Great For:**
- Handoffs to team members
- Project backups
- Sharing status
- Documentation archives

---

### 9. Process Log

Audit trail of all system activities.

**Logged Events:**
- Chat messages sent/received
- Nodes created/modified/deleted
- Rants processed
- Batons created
- Sessions started/ended
- Settings changes
- AI operations

**Filtering Options:**
- By date range
- By event type
- By user
- By project

**Use For:**
- Debugging issues
- Tracking activity
- Compliance/audit needs

---

### 10. Roundtable Coder

Multi-agent code generation with consensus voting.

**How It Works:**
1. Create a session
2. Configure agents (Builder, Voters, Reviewers)
3. Create rounds with specific tasks
4. Run the round
5. Agents collaborate and vote
6. Consensus determines if code is approved

**Execution Modes**
| Mode | Description |
|------|-------------|
| Single | Only builder runs (faster) |
| Multi | Builder + Voters with consensus (thorough) |

**Agent Roles**
| Role | What They Do |
|------|--------------|
| Builder | Creates/writes code |
| Voter | Reviews and votes approve/reject |
| Reviewer | Provides detailed feedback |

**Available Models:**
- OpenAI: GPT-4, GPT-4 Turbo, GPT-4o, o1
- Anthropic: Claude 3 Opus, Sonnet, Haiku
- Google: Gemini Pro, Gemini 2.0

**Voting Threshold**
Set percentage required for consensus (50-100%).

**Features:**
- Master Prompt - Base instructions for all agents
- Master Guardrails - Constraints all agents follow
- Test Runner - Validate generated code
- GitHub Integration - Create PRs from results

---

## Key Features

### Baton System

Manages token limits by creating snapshots.

**How It Works:**
1. You chat until tokens get high
2. Click "Baton Now" (or auto-triggers at threshold)
3. AI creates summary of everything
4. Fresh session starts with that summary
5. Continue where you left off!

**Token Usage Colors:**
| Color | Meaning |
|-------|---------|
| 🟢 Green | Plenty of space |
| 🟡 Yellow | Getting full |
| 🟠 Orange | Consider baton |
| 🔴 Red | Create baton now |

### Context Refresh

Intelligent re-orientation when returning after time away.

| Time Away | Refresh Level | What You See |
|-----------|---------------|--------------|
| < 30 min | None | No refresh needed |
| < 1 hour | Minimal | Quick task summary |
| 1-4 hours | Brief | Task + recent decisions |
| 4-24 hours | Medium | Session summary + context |
| 1-3 days | Full | Project overview + recap |
| 3-7 days | Extended | Full project refresh |
| 7+ days | Complete | Onboarding-style refresh |

### Cockpit Mode

Alternative dashboard layout showing 8 panels in a grid:
1. Chat Panel
2. Tree View
3. Gap Analysis
4. Voice Input
5. Full Specification
6. Tag Overlay View
7. Multi-Panel View
8. Settings

Toggle with **Layout Mode** switch in top right.

---

## Daily Workflow

### Morning Startup
1. Open Design Tree Studio
2. Complete **Daily Warmup** - review your top ideas
3. Check **Context Refresh** if returning after time away
4. Start working!

### During Work
1. **Chat** naturally about your project
2. Watch for **Auto Node Detection** popups
3. Use **Agent OS** for structured specifications
4. Monitor **Token Usage** bar
5. Create **Baton** when tokens get high

### End of Day
1. Save any important ideas to **Idea Bank**
2. Create a **Baton** to preserve context
3. Export **Truth Doc** if needed

### Weekly
1. Review **Idea Bank** - retire internalized ideas
2. Check **Lab Mode** metrics if testing features
3. Clean up **Design Tree** - archive completed nodes

---

## Tips & Tricks

1. **Be specific in chat** - Detailed questions get better AI responses

2. **Use Project Context** - More context = better AI understanding

3. **Create Nodes early** - Helps organize as you go

4. **Rate your ideas** - Higher ratings appear first in warmups

5. **Don't skip warmups** - Daily review builds confidence

6. **Baton before 100%** - Don't wait until you hit the limit

7. **Try Cockpit Mode** - Great for complex specifications

8. **Use Voice Input** - Faster than typing for brainstorms

9. **Check Gap Analysis** - Ensures nothing is missed

10. **Lab Mode for optimization** - Find your ideal feature combo

---

## Troubleshooting

### "OpenAI API key not configured"
→ Go to Settings tab and enter your API key, OR set `OPENAI_API_KEY` in environment variables

### Chat not responding
1. Check Process Log for errors
2. Verify API key is correct
3. Check your OpenAI account has credits
4. Try refreshing the page

### "Table does not exist" error
→ Go to System Status tab and click **Initialize Schema**

### Lost my work
- Chat history is saved per session
- Nodes are saved immediately
- Use Truth Doc to export everything
- Batons preserve context

### Token usage stuck at 0
→ Token counting happens after AI responds. Send a message to see usage.

### Warmup not showing
- Check if you already completed it today
- Verify you have active ideas in Idea Bank
- Ideas need status "Active" to appear

### Roundtable not working
- Verify you have the correct API key for the model
- Anthropic models need Anthropic API key
- Google models need Google API key

### Database connection failed
1. Check System Status for connection details
2. Verify DATABASE_URL is set correctly
3. Try the "Test Connection" button

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Enter | Send message (in chat) |
| Ctrl+Enter | New line in text areas |

---

## Settings Reference

| Setting | Default | Description |
|---------|---------|-------------|
| Max Context Tokens | 8,000 | Token limit before baton |
| Auto Baton Threshold | 80% | When to suggest baton |
| Auto Warmup | On | AI warmup on new sessions |
| Description Mode | Merged | How context is combined |

---

## Need Help?

- **System Status tab** - Shows what's working/broken
- **Process Log tab** - Shows detailed activity
- Check error messages - they usually explain the issue
- GitHub Issues: https://github.com/digisurfsome/design-tree-studio/issues

---

*Design Tree Studio v2.0 - AI-Powered Design Management System*
