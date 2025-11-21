# Phase 6: Baton Snapshot Generation + Warm-up

Phase 6 implements the baton snapshot system with automatic warm-up functionality, enabling seamless context preservation and session continuation.

## Features Implemented

### 1. Baton Service Layer (`app/services/baton_service.py`)

Complete baton management with:

#### generate_baton()
Creates a comprehensive project snapshot and new warmed session:

1. **Gathers project state**:
   - Project context (manual + auto descriptions)
   - All active nodes with current version summaries
   - Recent NodeVersion changes (last 10)
   - Pending draft nodes
   - Metadata (node counts, timestamps)

2. **Builds baton prompt**:
   - Uses `baton_description_prompt` from Settings
   - Formats project state as structured markdown
   - Groups nodes by domain
   - Highlights recent changes and drafts

3. **Calls OpenAI**:
   - Uses `DEFAULT_SUMMARY_MODEL` from Settings
   - Generates comprehensive snapshot_body (markdown)
   - Creates structured project overview

4. **Creates new chat session**:
   - Links to project and user
   - Status set to `WARMING` or `WARMED_PENDING`
   - Includes baton snapshot as system message

5. **Runs warm-up sequence** (if enabled):
   - Processes each `warmup_prompt_1` through `warmup_prompt_4`
   - Sends prompts marked with `is_warmup=True`
   - Gets AI responses to prime context
   - Updates token counts
   - Marks session as `WARMED_PENDING` when complete

#### check_auto_baton_trigger()
Determines if auto-baton should be created:
- Calculates token usage percentage
- Compares against `auto_baton_threshold_percent`
- Checks if baton already exists for current session
- Returns true if threshold exceeded and no baton exists

#### Other Functions
- `get_warmed_sessions()` - Lists all warmed_pending sessions
- `switch_to_session()` - Deactivates old session, activates new one

### 2. Model Updates (`app/core/models.py`)

#### New Enum: SessionStatus
```python
class SessionStatus(str, enum.Enum):
    ACTIVE = "active"              # Normal active session
    WARMING = "warming"            # Warm-up in progress
    WARMED_PENDING = "warmed_pending"  # Ready to switch to
    ARCHIVED = "archived"          # Archived session
```

#### ChatSession Updates
- Added `status` field (SessionStatus, default ACTIVE)
- Tracks session lifecycle through warm-up process

#### ChatMessage Updates
- Added `is_warmup` field (Boolean, default False)
- Identifies warm-up messages for filtering

#### BatonSnapshot Updates
- Added `session_id` - Links to new warmed session
- Added `user_id` - Creator tracking
- Added `snapshot_body` - AI-generated markdown description
- Added relationships to ChatSession and UserProfile

### 3. UI Updates (`app/ui/layout.py`)

#### Enhanced render_chat_panel()

**Warmed Session Notification:**
- Success banner when warmed sessions are available
- Shows count of pending warmed sessions

**Session Switcher:**
- Expandable "🔄 Switch to Warmed Session" section
- Lists all warmed_pending sessions with creation time
- "Switch" button for each session
- Handles session transition seamlessly

**Token Meter Integration:**
- Existing token meter unchanged
- Auto-baton triggers based on threshold
- Visual indication when approaching limit

**Conversation Display:**
- **Warm-up Toggle**: Checkbox to "Show warm-up" messages
- Filters warm-up messages by default
- Shows 🔥 indicator for warm-up messages when visible
- System messages (baton snapshots) visible with toggle

**Manual Baton Button:**
- Replaced placeholder "Baton Now" with functional button
- Shows spinner during creation
- Displays success message with new session title
- Handles errors gracefully

**Auto Baton Trigger:**
- Checks after each chat message send
- Triggers when `percent_used >= auto_baton_threshold_percent`
- Shows info message during creation
- Updates baton type to "auto"
- Notifies user when ready

**Session Management:**
- Tracks `current_chat_session_id` in session_state
- Supports switching between sessions
- Maintains context across page interactions

### 4. Migration Guide (`MIGRATION_PHASE6.md`)

Comprehensive migration documentation with:
- SQL commands for all schema changes
- Development vs. production migration paths
- Verification queries
- Notes on existing data handling

## Workflow: Manual Baton

### User Clicks "🎯 Baton Now"

1. **Gather State**: Service collects all project data
2. **Generate Description**: OpenAI creates snapshot markdown
3. **Create Session**: New ChatSession with status=WARMING
4. **Save Baton**: BatonSnapshot created and linked to session
5. **Add System Message**: Baton content added to new session
6. **Run Warm-up** (if auto_warmup_enabled=true):
   - Process warmup_prompt_1 → AI response
   - Process warmup_prompt_2 → AI response
   - Process warmup_prompt_3 → AI response
   - Process warmup_prompt_4 → AI response
   - All marked with is_warmup=True
7. **Mark Ready**: Session status → WARMED_PENDING
8. **Notify User**: Success message displayed
9. **User Switches**: Clicks "Switch" in session switcher
10. **Session Activated**: New session status → ACTIVE, old → inactive

### What Happens Under the Hood

**Baton Snapshot Contains:**
```markdown
# Project: My Design Project

## Project Description
[Project description from database]

## Project Context
[Manual context from ProjectContext]

## Current State
- Total Nodes: 15
- Draft Nodes: 3

## Active Nodes by Domain
### Backend
- 🟢 **User Authentication** (component)
  - JWT-based authentication with refresh tokens
- 🟢 **API Gateway** (component)
  - Central routing with rate limiting

### Frontend
- 🟡 **Login Form** (component) [DRAFT]
  - React component with form validation

## Recent Changes
- **User Authentication** v3: Added password reset flow
  - Updated security requirements
- **API Gateway** v2: Implemented rate limiting
  - Added Redis integration

## Pending Drafts
- **Login Form** (Frontend)
  - React component with form validation
- **Dashboard Layout** (Frontend)
  - Main app dashboard wireframe
```

**Warm-up Sequence:**
1. System message with baton snapshot
2. User message (warmup_prompt_1): "Review the project context..."
3. Assistant response: AI processes and confirms understanding
4. User message (warmup_prompt_2): "What are the key components?"
5. Assistant response: AI lists components from context
6. ... continues for all configured prompts

**Result:**
- New session has full project context loaded
- AI is "warmed up" with understanding of project
- Ready for immediate productive conversation
- Old session preserved for reference

## Workflow: Auto Baton

### Triggered After Chat Message

1. **User Sends Message**: Normal chat interaction
2. **AI Responds**: Token counts updated
3. **Check Threshold**:
   - percent_used = (total_tokens_used / max_context_tokens) * 100
   - Compare with auto_baton_threshold_percent (e.g., 80%)
4. **If Threshold Exceeded**:
   - Check if baton already created for this session
   - If not, automatically trigger generate_baton()
   - Set snapshot_type = "auto"
5. **Notify User**:
   - "Token threshold reached! Creating auto-baton..."
   - "Auto-baton created! A new warmed session is ready."
6. **User Continues**: Can keep using current session
7. **User Switches When Ready**: Expander shows available warmed session

### Auto-Baton Example Timeline

```
Session 1 starts:
  - 0 tokens used (0%)

After 10 messages:
  - 4,000 tokens used (50%)
  - 🟢 Green meter

After 20 messages:
  - 6,000 tokens used (75%)
  - 🟡 Yellow meter

After 25 messages:
  - 6,500 tokens used (81%)
  - 🟠 Orange meter
  - **AUTO-BATON TRIGGERED**
  - Session 2 created in background
  - Warm-up runs automatically

After 30 messages:
  - 7,500 tokens used (94%)
  - 🔴 Red meter
  - User sees: "🎯 New warmed session ready! (1 available)"
  - User clicks "Switch" when convenient

Session 2 activated:
  - 0 tokens used (0%)
  - Full context from Session 1 via baton
  - Fresh token budget
  - Conversation continues seamlessly
```

## Warm-up Messages

### Storage
- Stored in `chat_messages` table
- Flagged with `is_warmup = TRUE`
- Included in session token counts
- Part of conversation history

### Display
- **Default**: Hidden from chat view
- **With Toggle**: Visible with 🔥 indicator
- **Purpose**: Don't clutter main conversation
- **Useful For**: Debugging, understanding AI context

### Example Display (Toggle ON)

```
💬 AI Chat

[Conversation]

📋 System: Project Snapshot (Baton)
[Truncated preview...]

👤 User: Review the project context... 🔥
🤖 Assistant: I've reviewed the project... 🔥

👤 User: What are the key components? 🔥
🤖 Assistant: The key components are... 🔥

👤 User: Actually, let's talk about authentication
🤖 Assistant: Sure! Looking at the User Authentication component...
```

## Configuration

### Settings Used

1. **baton_description_prompt**: Template for baton generation
   - Default: Comprehensive snapshot instructions
   - Customizable per project needs

2. **auto_warmup_enabled**: Boolean
   - true: Run warm-up after baton creation
   - false: Just create baton, no warm-up

3. **warmup_prompt_1 through warmup_prompt_4**: Warm-up prompts
   - Default: Review context, list components, etc.
   - Skips empty prompts
   - Processed sequentially

4. **auto_baton_threshold_percent**: Integer (0-100)
   - Default: 80
   - Triggers auto-baton when exceeded

5. **max_context_tokens**: Integer
   - Default: 8000
   - Used for percentage calculation

6. **DEFAULT_SUMMARY_MODEL**: String
   - Default: "gpt-4-turbo-preview"
   - Used for baton generation

7. **DEFAULT_CHAT_MODEL**: String
   - Default: "gpt-4-turbo-preview"
   - Used for warm-up responses

## Technical Implementation Details

### State Machine: ChatSession.status

```
              generate_baton()
NEW ────────────────────────────► WARMING
                                     │
                                     │ _run_warmup_sequence_sync()
                                     │
                                     ▼
                              WARMED_PENDING
                                     │
                                     │ switch_to_session()
                                     │
                                     ▼
                                  ACTIVE
                                     │
                                     │ (time passes)
                                     │
                                     ▼
                                 ARCHIVED
```

### Baton State Data Structure

```python
{
    "project": {
        "id": 1,
        "name": "My Project",
        "description": "..."
    },
    "context": {
        "manual_description": "...",
        "auto_description": None
    },
    "nodes": [
        {
            "id": 5,
            "title": "User Authentication",
            "domain": "Backend",
            "type": "component",
            "status": "active",
            "current_version": 3,
            "summary": "JWT-based authentication...",
            "details": "..."
        }
    ],
    "recent_changes": [...],
    "drafts": [...],
    "node_count": 15,
    "draft_count": 3,
    "timestamp": "2025-01-15T10:30:00"
}
```

### Token Tracking

- Warm-up messages included in session token counts
- Each warm-up contributes to total_tokens_used
- New session starts with only warm-up tokens
- Fresh budget for actual conversation

### Error Handling

- Baton generation failures: Show error, keep current session
- Warm-up failures: Log error, continue with remaining prompts
- Auto-baton failures: Show warning, don't interrupt conversation
- Switch failures: Show error, keep current session

## Benefits

1. **Context Preservation**: Full project state captured in baton
2. **Seamless Continuation**: Warmed sessions ready instantly
3. **Fresh Token Budget**: Avoid context window limitations
4. **Automatic Management**: Auto-baton triggers at threshold
5. **Filtered Display**: Warm-up messages don't clutter UI
6. **Flexible Control**: Manual baton for immediate needs
7. **Cost Efficient**: Only warm up when switching
8. **History Maintained**: Old sessions preserved for reference

## Testing Checklist

- [x] Manual baton creation works
- [x] Auto-baton triggers at threshold
- [x] Warm-up sequence executes correctly
- [x] Warm-up messages stored with is_warmup=True
- [x] Warm-up toggle filters messages
- [x] Session switcher displays warmed sessions
- [x] Switch to session updates statuses
- [x] Token counts include warm-up
- [x] Baton snapshot contains all project data
- [x] OpenAI integration generates good summaries
- [x] Error handling works for all failure modes
- [x] UI updates reflect session changes
- [x] Multiple warmed sessions supported
- [x] Session state persists across page interactions

## Migration Required

**⚠️ DATABASE MIGRATION REQUIRED**: See `MIGRATION_PHASE6.md` for detailed instructions.

Key changes:
- New enum type: `SessionStatus`
- ChatSession.status field (enum)
- ChatMessage.is_warmup field (boolean)
- BatonSnapshot.session_id, user_id, snapshot_body fields

## Review of Work

### How Manual Baton Works End-to-End

1. **User clicks "🎯 Baton Now" button** in chat panel
2. **generate_baton() is called** with current session details
3. **Project state gathered**: All nodes, contexts, changes, drafts collected into structured dict
4. **OpenAI generates snapshot**: Using baton_description_prompt template, creates markdown overview
5. **New ChatSession created**: With status=WARMING, linked to project/user
6. **BatonSnapshot saved**: Contains snapshot_body (markdown) and state_data (JSON)
7. **System message added**: Baton content added as first message in new session
8. **Warm-up sequence runs** (if enabled):
   - warmup_prompt_1 sent as user message (is_warmup=True) → AI response
   - warmup_prompt_2 sent → AI response
   - warmup_prompt_3 sent → AI response
   - warmup_prompt_4 sent → AI response
   - All responses marked is_warmup=True and included in token counts
9. **Session marked WARMED_PENDING**: Ready for user to switch to
10. **User notified**: Success message shows new session title
11. **User sees "Switch" option**: In expandable "🔄 Switch to Warmed Session" section
12. **User clicks "Switch"**: Old session deactivated, new session activated (status→ACTIVE)
13. **Conversation continues**: With full context from baton, fresh token budget

### How Auto Baton is Triggered by the Meter

1. **User sends chat message**: Normal conversation flow
2. **AI responds**: send_chat_message() updates session token counts
3. **Auto-baton check runs**: check_auto_baton_trigger() called after response
4. **Calculation performed**:
   ```python
   percent_used = (session.total_tokens_used / max_context_tokens) * 100
   # Example: (6500 / 8000) * 100 = 81.25%
   ```
5. **Threshold comparison**:
   - If percent_used >= auto_baton_threshold_percent (e.g., 80%)
   - AND no auto-baton exists for this session yet
   - THEN trigger auto-baton
6. **Auto-baton created**: Same as manual, but snapshot_type="auto"
7. **User notified**: "Token threshold reached! Creating auto-baton..."
8. **Creation completes**: "Auto-baton created! A new warmed session is ready."
9. **Token meter shows warning**: 🟠/🔴 indicator based on percentage
10. **Banner appears**: "🎯 New warmed session ready! (1 available)"
11. **User continues current session**: No interruption to workflow
12. **User switches when convenient**: Expander shows warmed session waiting

### How Warm-up Messages are Generated and Where They're Stored/Displayed

**Generation:**
1. When generate_baton() runs with run_warmup=True
2. Checks auto_warmup_enabled setting
3. Collects warmup_prompt_1 through warmup_prompt_4 from settings
4. For each non-empty prompt:
   - Creates ChatMessage with role=USER, is_warmup=True, content=prompt
   - Saves to database
   - Calls OpenAI API with full conversation history so far
   - Creates ChatMessage with role=ASSISTANT, is_warmup=True, content=response
   - Saves to database
   - Updates session token counts
5. Sequence runs synchronously, prompts processed in order
6. Session marked WARMED_PENDING when complete

**Storage:**
- Table: `chat_messages`
- Fields:
  - session_id: Links to new ChatSession
  - role: USER or ASSISTANT
  - content: Prompt text or AI response
  - is_warmup: TRUE (distinguishes from normal messages)
  - token_count: Completion tokens (for assistant messages)
  - model_used: Model name
  - created_at: Timestamp
- Included in session.total_tokens_used
- Part of permanent conversation history

**Display:**
- **Default (Show warm-up = OFF)**:
  - Warm-up messages filtered out
  - Only real conversation visible
  - Clean, uncluttered chat view

- **With Toggle ON (Show warm-up = ON)**:
  - All messages visible chronologically
  - Warm-up messages show 🔥 indicator
  - System message (baton snapshot) shown first
  - Warm-up user prompts → AI responses → real conversation
  - Helps understand what context AI has

- **Toggle Control**:
  - Checkbox in chat panel header: "Show warm-up"
  - Default: unchecked (false)
  - Persists in session_state during page use
  - Resets on page reload (intentional for clean default)

**Example Message Flow in Database:**
```
Session 42 (WARMED_PENDING):
  Message 1: role=SYSTEM, is_warmup=False
    "# Project Snapshot (Baton)\n\n## Project: My Project..."

  Message 2: role=USER, is_warmup=True
    "Review the project context and confirm your understanding..."

  Message 3: role=ASSISTANT, is_warmup=True, tokens=150
    "I've reviewed the project context. This is a design management..."

  Message 4: role=USER, is_warmup=True
    "What are the key components in the project?"

  Message 5: role=ASSISTANT, is_warmup=True, tokens=200
    "The key components include: 1. User Authentication..."

  [After switch to ACTIVE]

  Message 6: role=USER, is_warmup=False
    "Let's discuss the authentication flow in detail"

  Message 7: role=ASSISTANT, is_warmup=False, tokens=180
    "Based on the User Authentication component I reviewed..."
```

This completes the Phase 6 implementation of Baton snapshot generation with comprehensive warm-up functionality!
