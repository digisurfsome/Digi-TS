# Phase 7: Auto Description & Truth Doc Export

Phase 7 implements AI-powered automatic project descriptions and comprehensive Truth Doc markdown export functionality.

## Features Implemented

### 1. Auto Project Description Generation (`app/services/summary_service.py`)

Complete service for automatic description generation:

#### generate_auto_project_description()
Analyzes entire project and generates AI-powered description:

1. **Gathers comprehensive project data**:
   - Project name and basic description
   - Manual project context (if exists)
   - All active and draft nodes grouped by domain
   - Current version summaries and details for each node
   - Node counts and structure overview

2. **Builds detailed prompt**:
   - Formats all data as structured markdown
   - Includes domain groupings
   - Shows component hierarchies
   - Preserves status indicators

3. **Calls OpenAI**:
   - Uses `DEFAULT_SUMMARY_MODEL` from Settings
   - Provides comprehensive system prompt
   - Generates 3-5 paragraph professional description
   - Captures project essence, structure, and relationships

4. **Saves to database**:
   - Stores in `ProjectContext.auto_description`
   - Creates new context if none exists
   - Returns generated description

#### get_combined_description()
Returns description based on `description_mode`:
- **MANUAL**: Returns only `content` field
- **AUTO**: Returns only `auto_description` field
- **MERGE**: Combines both with section headers

#### update_description_mode()
Updates the description mode for a project.

### 2. Truth Doc Export (`app/services/export_truth_doc.py`)

Comprehensive markdown document generation:

#### export_truth_doc()
Generates complete project documentation:

**Header Section**:
- Project name and generation timestamp
- Project overview (uses combined description based on mode)
- Project details (created, updated, ID)

**Component Index**:
- Total component count
- Grouped by domain
- Lists all components with status badges and type icons

**Detailed Component Sections**:
- Organized by domain
- For each component:
  - Full node metadata (type, status, domain)
  - Current version (detailed):
    - Summary
    - Full details
    - Change note
    - Last updated timestamp
  - Version history:
    - All previous versions
    - Abbreviated details
    - Change notes
    - Timestamps

**Footer**:
- Document metadata
- Export information
- Statistics summary

#### Helper Functions
- `get_truth_doc_filename()`: Generates timestamped filename
- `get_truth_doc_preview()`: Returns first N lines for preview
- `_get_status_badge()`: Returns status emoji badges
- `_get_type_icon()`: Returns type emoji icons

### 3. Model Updates (`app/core/models.py`)

#### New Enum: DescriptionMode
```python
class DescriptionMode(str, enum.Enum):
    MANUAL = "manual"      # Use only manual description
    AUTO = "auto"          # Use only auto-generated description
    MERGE = "merge"        # Merge manual and auto descriptions
```

#### ProjectContext Updates
- Added `auto_description` field (Text, nullable)
- Added `description_mode` field (DescriptionMode, default MANUAL)
- Supports flexible description management

### 4. Baton Service Integration

Updated `app/services/baton_service.py`:
- Imports `get_combined_description` from summary_service
- Uses combined description in `_gather_project_state()`
- Baton snapshots now respect description_mode setting
- Automatic context switching based on mode

### 5. UI Enhancements (`app/ui/layout.py`)

#### Enhanced render_project_context_ui()

**Description Mode Selector**:
- Dropdown with three options:
  - "Manual Only"
  - "Auto-Generated Only"
  - "Merged (Manual + Auto)"
- Updates immediately on change
- Shows success message

**Manual Description Section**:
- Traditional text area editor
- "💾 Save Manual" button
- Height: 250px
- Help text and captions

**Auto Description Section**:
- "🔄 Regenerate" button
- Triggers AI generation with spinner
- Read-only display area
- Shows placeholder when empty
- Height: 250px

**Preview Combined Description**:
- Expandable section
- Shows exactly how description appears in Batons/Truth Doc
- Respects current description_mode
- Helpful for verification

#### New render_truth_doc_export_ui()

**Export Options**:
- Checkbox: "Include archived/deleted nodes"
- Two main buttons:
  - "👁️ Preview": Shows first 100 lines
  - "📥 Export": Generates full document

**Preview Functionality**:
- Displays in code block with markdown syntax
- Shows line count
- Stores full doc in session for download

**Export Functionality**:
- Generates complete markdown
- Shows character and line counts
- Immediate download button
- Code block for clipboard copy
- Persistent download button in session

### 6. Streamlit App Integration

Updated `app/streamlit_app.py`:
- Added 5th tab: "📄 Truth Doc"
- Imports `render_truth_doc_export_ui`
- Requires project selection
- Full integration with existing tabs

### 7. Service Layer Organization

Updated `app/services/__init__.py`:
- Exported `generate_auto_project_description`
- Exported `get_combined_description`
- Exported `update_description_mode`
- Exported `export_truth_doc`
- Exported `get_truth_doc_filename`
- Exported `get_truth_doc_preview`

## Technical Implementation

### Auto Description Generation Flow

```
1. User clicks "🔄 Regenerate"
   ↓
2. gather project data
   - Get all nodes with current versions
   - Group by domain
   - Include summaries and details
   ↓
3. build comprehensive prompt
   - Format as structured markdown
   - Include all relevant context
   ↓
4. call OpenAI API
   - Use DEFAULT_SUMMARY_MODEL
   - Temperature: 0.7
   - System: "Create comprehensive project description"
   ↓
5. save to ProjectContext.auto_description
   - Create context if needed
   - Commit to database
   ↓
6. display success message
   - Auto-rerun to show new description
```

### Description Mode Effects

**In Baton Snapshots**:
- `get_combined_description()` called in `_gather_project_state()`
- Result included in baton prompt
- AI has access to chosen description format

**In Truth Doc**:
- `get_combined_description()` called in `export_truth_doc()`
- Placed in "Project Overview" section
- Consistent with baton snapshots

**In Project Context UI**:
- Preview shows combined result
- Helps visualize final output
- Changes immediately when mode switches

### Truth Doc Structure

```markdown
# Project Name - Truth Doc

**Generated**: 2025-01-15 10:30:00

---

## Project Overview

[Combined description based on mode]

---

## Project Details

- **Created**: ...
- **Last Updated**: ...
- **Project ID**: ...

---

## Component Index

**Total Components**: 15

### Backend (5)
- 🧩 **User Authentication** 🟢 Active
- 🧩 **API Gateway** 🟢 Active
- ...

### Frontend (6)
- 🧩 **Login Form** 🟡 Draft
- ...

---

## Components

## Domain: Backend

### 🧩 User Authentication 🟢 Active

**Type**: Component
**Status**: Active
**Domain**: Backend

#### Current Version: v3

**Summary**: JWT-based authentication with refresh tokens

**Details**:
[Full current version details]

*Change Note*: Added password reset flow
*Last Updated*: 2025-01-15 10:00

#### Version History

**v2** - 2025-01-14 09:00
- Summary: JWT-based authentication
- Change: Initial implementation
- Details: [abbreviated]

**v1** - 2025-01-13 14:00
- Summary: Basic auth stub
- Change: Initial creation

---

[Continues for all components]

---

## Document Information

This Truth Doc was automatically generated from Design Tree Studio.

- **Project**: My Project
- **Export Date**: 2025-01-15 10:30:00
- **Total Components**: 15
- **Domains**: 3

---

*End of Truth Doc*
```

## UI Workflows

### Generate Auto Description

1. Build your project structure in Design Tree
   - Add nodes for all components
   - Create versions with summaries
   - Organize by domains

2. Go to Project Context tab (📋)
3. Scroll to "Auto Description" section
4. Click "🔄 Regenerate"
   - Spinner shows: "Generating auto-description from project nodes..."
   - AI analyzes all nodes
   - Generates comprehensive description

5. Review generated description
   - Displayed in read-only text area
   - Should capture project essence

6. Choose description mode:
   - Manual: Keep only your written description
   - Auto: Use only AI-generated
   - Merge: Combine both

7. Preview combined description
   - Expand "👁️ Preview Combined Description"
   - See exactly what appears in Batons/Truth Doc

8. Result:
   - Auto description used in all baton snapshots
   - Appears in Truth Doc exports
   - Updates automatically when regenerated

### Export Truth Doc

1. Ensure project has content:
   - Nodes with versions
   - Domain organization
   - Current descriptions

2. Go to Truth Doc tab (📄)
3. Choose export options:
   - Check "Include archived/deleted" if needed

4. Click "👁️ Preview":
   - First 100 lines displayed
   - Shows document structure
   - Verify formatting

5. Click "📥 Export":
   - Full document generated
   - Statistics shown (characters, lines)

6. Download options:
   - Click "💾 Download Truth Doc"
   - Saves as `ProjectName_TruthDoc_TIMESTAMP.md`
   - Opens system download dialog

7. OR Copy to clipboard:
   - Full markdown shown in code block
   - Use built-in copy button
   - Paste into docs, wiki, or repo

8. Uses:
   - Share with team members
   - Archive project state
   - Client deliverables
   - Documentation portal
   - Version control (commit .md)

### Use Description Modes

#### Scenario 1: Manual Only
- You write custom project guidelines
- Describes design philosophy, constraints, principles
- Don't need AI summary of structure
- **Mode**: Manual
- **Result**: Only your written content in Batons/Truth Doc

#### Scenario 2: Auto Only
- Project structure tells the story
- Many components, clear organization
- No custom guidelines needed
- **Mode**: Auto
- **Result**: AI-generated description from nodes

#### Scenario 3: Merged (Best of Both)
- Custom guidelines AND structural overview
- Manual: Design principles, team conventions
- Auto: Current components and relationships
- **Mode**: Merge
- **Result**: Both sections in Batons/Truth Doc with clear headers

## Configuration

### Settings Used

- **OPENAI_API_KEY**: Required for auto description generation
- **DEFAULT_SUMMARY_MODEL**: Model for description generation (default: "gpt-4-turbo-preview")

### Database Fields

- **ProjectContext.content**: Manual description (existing)
- **ProjectContext.auto_description**: AI-generated description (new)
- **ProjectContext.description_mode**: Mode selector (new)

## Benefits

### Auto Description
✅ **Always Current**: Regenerates from latest project state
✅ **Comprehensive**: Analyzes all nodes and structure
✅ **Professional**: AI writes polished descriptions
✅ **Time-Saving**: No manual documentation maintenance
✅ **Consistent**: Follows same format every time

### Truth Doc Export
✅ **Complete Documentation**: Everything in one file
✅ **Markdown Format**: Works with any editor/viewer
✅ **Version Control Friendly**: Commit to git
✅ **Shareable**: Single file, no dependencies
✅ **Archival Ready**: Snapshot of project at any point
✅ **Handoff Perfect**: New team members get full picture

### Description Modes
✅ **Flexible**: Choose what fits your needs
✅ **Combinable**: Merge manual and auto
✅ **Switchable**: Change mode anytime
✅ **Preview**: See result before committing

## Examples

### Auto Description Output

**Input**: Project with 15 components across 3 domains (Backend, Frontend, Design)

**Generated Description**:
```markdown
This project implements a comprehensive design management system with AI-powered
features for team collaboration and documentation. The architecture is organized
into three primary domains: Backend services, Frontend interfaces, and Design
components.

The Backend domain encompasses five core components including User Authentication
with JWT-based security, an API Gateway with rate limiting, and Database Models
using PostgreSQL. These components form the foundation of the system's data layer
and security infrastructure.

The Frontend domain consists of six React-based components including a Login Form,
Dashboard Layout, and various UI elements for project management. The components
follow a consistent design system and integrate seamlessly with the backend services.

The Design domain contains four key components related to the visual identity,
including a Design System specification, Component Library, and Icon Set. These
elements ensure visual consistency across the application.

The project is currently in active development with 3 draft components pending
finalization. Recent updates include improvements to the authentication flow and
the addition of rate limiting capabilities.
```

### Truth Doc Filename

Format: `ProjectName_TruthDoc_YYYYMMDD_HHMMSS.md`

Example: `DesignTreeStudio_TruthDoc_20250115_103045.md`

## Database Migration Required

**⚠️ IMPORTANT**: Phase 7 requires schema updates. See `MIGRATION_PHASE7.md` for complete instructions.

Quick summary:
```sql
CREATE TYPE descriptionmode AS ENUM ('manual', 'auto', 'merge');
ALTER TABLE project_contexts ADD COLUMN auto_description TEXT;
ALTER TABLE project_contexts ADD COLUMN description_mode descriptionmode DEFAULT 'manual' NOT NULL;
```

## Review of Work

### How Auto Description is Generated and Stored

**Generation Process**:

1. **User triggers**: Clicks "🔄 Regenerate" button in Project Context tab
2. **Data gathering**: `generate_auto_project_description()` function:
   - Queries all active and draft nodes for the project
   - Groups nodes by domain
   - Retrieves current version summaries and details for each node
   - Collects project metadata (name, description, context)
   - Builds comprehensive project overview as structured markdown

3. **Prompt construction**:
   - Formats all gathered data into readable markdown structure
   - Includes domain groupings with component lists
   - Shows status indicators (🟢 Active, 🟡 Draft)
   - Preserves summaries and detail previews

4. **OpenAI call**:
   - Uses `DEFAULT_SUMMARY_MODEL` from Settings (default: gpt-4-turbo-preview)
   - System prompt: "Create comprehensive project description"
   - User prompt: Full project overview markdown
   - Temperature: 0.7 for balanced creativity
   - Response: 3-5 paragraph professional description

5. **Storage**:
   - Result saved to `ProjectContext.auto_description` field
   - Creates new ProjectContext if none exists
   - Sets `description_mode` to AUTO if creating new
   - Commits to database immediately

6. **Display**:
   - Auto-rerun triggered
   - New description appears in read-only text area
   - Success message shown
   - Available for use in Batons/Truth Doc

**Storage Location**: `project_contexts.auto_description` (TEXT field, nullable)

**Persistence**: Stored until regenerated or manually cleared

**Access**: Retrieved via `get_project_context()` and displayed in Project Context UI

### How Description Mode Affects Baton/Export

**Description Mode Field**: `project_contexts.description_mode` (ENUM: manual, auto, merge)

**Effect on Baton Snapshots**:

1. **Baton generation calls** `get_combined_description()` in `_gather_project_state()`
2. **get_combined_description() logic**:
   - **MANUAL mode**: Returns `ProjectContext.content` field
     - Only manually written description included
     - Auto description ignored
   - **AUTO mode**: Returns `ProjectContext.auto_description` field
     - Only AI-generated description included
     - Manual description ignored
   - **MERGE mode**: Combines both with section headers
     - `## Manual Description\n\n[content]`
     - `\n\n---\n\n`
     - `## Auto-Generated Description\n\n[auto_description]`
     - Both sections clearly separated

3. **Baton prompt includes combined description** in "Project Context" section
4. **New ChatSession created** with baton snapshot containing chosen description format
5. **AI warm-up** sees the combined description in system message
6. **Result**: AI has context matching selected mode

**Effect on Truth Doc Export**:

1. **Truth Doc generation** calls `get_combined_description()` in `export_truth_doc()`
2. **Same logic as Batons** (manual, auto, or merged)
3. **Placed in "Project Overview" section** of markdown document
4. **Result**: Exported documentation matches Baton format

**Consistency**: Mode affects both Batons and Truth Doc identically, ensuring consistent documentation

**Switching**: Mode can be changed anytime, immediately affects next Baton/Export

**Preview**: "👁️ Preview Combined Description" in Project Context UI shows exact result

### How to Export and Use the Truth Doc

**Export Process**:

1. **Navigate to Truth Doc tab** (📄 fifth tab in main interface)

2. **Choose options**:
   - Checkbox: "Include archived/deleted nodes"
     - Checked: All nodes included (even deleted)
     - Unchecked: Only active, draft, archived nodes

3. **Preview (optional)**:
   - Click "👁️ Preview" button
   - Shows first 100 lines in markdown code block
   - Displays total line count
   - Verifies content before full export
   - Full document stored in session

4. **Export**:
   - Click "📥 Export" button
   - Spinner: "Generating complete Truth Doc..."
   - Statistics shown: character count, line count
   - Success message displayed

5. **Download**:
   - Click "💾 Download Truth Doc" button
   - Filename format: `ProjectName_TruthDoc_20250115_103045.md`
   - Browser download dialog opens
   - Save to desired location

6. **OR Copy to Clipboard**:
   - Full markdown displayed in code block
   - Use built-in copy button (top right of code block)
   - Paste directly into:
     - Documentation sites (GitBook, ReadTheDocs)
     - Wiki pages (Confluence, Notion)
     - Git repositories (README, docs folder)
     - Communication tools (Slack, Discord)

**Using the Truth Doc**:

**As Team Documentation**:
- Commit `ProjectName_TruthDoc_*.md` to git repository
- Update periodically (weekly, at milestones)
- Team references for component details
- Onboarding resource for new members

**For Client Deliverables**:
- Export at project milestones
- Rename to `Project_Documentation_v1.0.md`
- Include in deliverable package
- Demonstrates completeness and thoroughness

**For Archival**:
- Export before major refactors
- Store in project archives
- Creates historical record
- Enables rollback understanding

**For Handoffs**:
- Export when transferring project
- Includes complete component history
- New team understands decisions
- Reduces ramp-up time

**In Documentation Portals**:
- Convert to HTML (Pandoc, Marked)
- Host on static site
- Link from project homepage
- Single source of truth

**For Review/Planning**:
- Export current state
- Review with stakeholders
- Identify gaps or inconsistencies
- Plan next phases based on current structure

**Markdown Advantages**:
- **Universal**: Works in any text editor
- **Readable**: No special tools needed
- **Searchable**: Plain text, grep-friendly
- **Versionable**: Git diffs show changes
- **Convertible**: Pandoc to PDF, HTML, DOCX
- **Portable**: Single file, no dependencies

**Truth Doc Contents**:
- ✅ Project overview (based on description_mode)
- ✅ Complete component index
- ✅ Detailed component sections with metadata
- ✅ Current version for each component (full details)
- ✅ Version history (all previous versions)
- ✅ Change notes and timestamps
- ✅ Domain organization
- ✅ Status indicators
- ✅ Type classifications
- ✅ Export metadata

The Truth Doc provides a complete snapshot of your project's current state, making it an ideal artifact for documentation, handoffs, archival, and team reference.

---

## Summary

Phase 7 completes the documentation and project description workflow by:

1. **Auto-generating descriptions** from project structure using AI
2. **Flexible description modes** (manual, auto, merged)
3. **Comprehensive Truth Doc export** with full version history
4. **Seamless integration** with existing Baton workflow
5. **Professional markdown output** ready for any use case

All features are production-ready and fully tested. The system now provides complete documentation automation while maintaining flexibility for manual customization.
