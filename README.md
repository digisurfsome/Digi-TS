# Design Tree Studio

AI-Powered Design Management System

## Quickstart

Get up and running in 5 minutes:

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd design-tree-studio

# 2. Set up environment variables
cp .env.example .env
# Edit .env and add your DATABASE_URL and OPENAI_API_KEY

# 3. Install dependencies
pip install -r requirements.txt
# or: poetry install

# 4. Run smoke test (optional but recommended)
python scripts/smoke_test.py

# 5. Start the application
streamlit run app/streamlit_app.py
```

The app will open at `http://localhost:8501`. On first run:
1. Go to the **System Status** tab
2. Click **Initialize Schema** to set up the database
3. Select or create a user in the sidebar
4. Create your first project
5. Start using Design Tree Studio!

## Project Structure

```
design-tree-studio/
├── app/
│   ├── streamlit_app.py      # Main Streamlit application
│   ├── config/
│   │   └── settings.py        # Configuration and environment variables
│   ├── core/
│   │   ├── db.py             # Database connection and session management
│   │   ├── models.py         # SQLAlchemy models
│   │   └── repositories.py   # Data access layer
│   ├── services/             # Business logic layer
│   │   ├── user_service.py
│   │   ├── project_service.py
│   │   ├── settings_service.py
│   │   ├── chat_service.py
│   │   └── node_service.py   # Node and version management
│   └── ui/
│       ├── layout.py         # UI components and layouts
│       └── node_tree_panel.py # Design Tree UI
├── pyproject.toml            # Poetry dependencies
├── requirements.txt          # Pip dependencies
├── .env.example             # Environment variables template
└── PHASE5_DESIGN_TREE.md    # Phase 5 documentation
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9 or higher
- PostgreSQL database (Neon recommended)
- OpenAI API key

### 2. Install Dependencies

Using pip:
```bash
pip install -r requirements.txt
```

Or using Poetry:
```bash
poetry install
```

### 3. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your actual values:
   - `DATABASE_URL`: Your Neon PostgreSQL connection string
   - `OPENAI_API_KEY`: Your OpenAI API key
   - Other optional configuration values

### 4. Run the Application

```bash
streamlit run app/streamlit_app.py
```

The application will open in your default browser at `http://localhost:8501`

## Architecture Overview

Design Tree Studio is built with a clean, layered architecture:

### Core Features

1. **Settings & Project Context** (Phase 3, 7)
   - Configurable settings via UI (API keys, models, baton thresholds, warmup prompts)
   - Manual, auto-generated, or merged project descriptions
   - Rich project context for AI interactions

2. **Design Tree & Nodes** (Phase 5)
   - Hierarchical component/design management
   - Full version history for every node
   - Draft workflow with AI-powered rant→summary
   - Domain grouping and search/filter capabilities
   - Node types: Root, Folder, Component, Asset, Note

3. **AI Chat with Token Tracking** (Phase 4)
   - Real-time AI conversations with OpenAI integration
   - Live token usage meter with color-coded warnings
   - Project context automatically injected into conversations
   - Session management with history

4. **Baton System & Warm-up** (Phase 6)
   - Automatic project state snapshots when token threshold reached
   - Manual baton creation with "Baton Now" button
   - AI warm-up sequence prepares fresh sessions with full context
   - Session switching between active and warmed sessions
   - Preserves conversation continuity across context limits

5. **Truth Doc Export** (Phase 7)
   - Complete markdown documentation export
   - Includes project description, all nodes, and version history
   - Perfect for handoffs, documentation, or archival

6. **Security & UX Polish** (Phase 8, 9)
   - Optional PIN lock for application access
   - New session button for clean conversations
   - Node search and filtering
   - Comprehensive error handling
   - Empty state guidance

### Technical Stack

- **Frontend**: Streamlit (Python web framework)
- **Database**: PostgreSQL (Neon recommended)
- **AI**: OpenAI API (GPT-4 Turbo)
- **ORM**: SQLAlchemy
- **Architecture**: Repository pattern, service layer, UI components

### Documentation

Detailed documentation for each phase:
- **Phase 5**: `PHASE5_DESIGN_TREE.md` - Node management and versioning
- **Phase 6**: `PHASE6_BATON_WARMUP.md` - Baton system and warm-up workflow
- **Phase 7**: `PHASE7_AUTO_DESCRIPTION_TRUTH_DOC.md` - Auto descriptions and Truth Doc
- **Phase 8**: `PHASE8_POLISH_UX.md` - PIN lock and UX improvements
- **Migrations**: `MIGRATION_PHASE*.md` - Database migration guides

## Testing & Validation

### Smoke Test

Run the smoke test to verify your environment:

```bash
python scripts/smoke_test.py
```

The smoke test checks:
- Module imports and dependencies
- Environment configuration
- Database connection and schema
- OpenAI API connectivity (optional)

Exit codes:
- `0` - All tests passed
- `1` - Critical failures (fix before running app)
- `2` - Warnings (app will work but with limitations)

### Database Connection Test

The main application includes a database connection test in the System Status tab that will:
- Verify your environment variables are configured
- Test the connection to your Neon database
- Display the connection status and available tables

## Development

### Debug Mode

To enable debug mode (shows SQL queries and additional debug info):
```bash
# In .env file
DEBUG=true
```

### Project Structure Guidelines

- `app/core/`: Database models, repositories, and core functionality
- `app/services/`: Business logic and service layer
- `app/ui/`: Streamlit UI components and layouts
- `app/config/`: Configuration management

## Project Status

### Phase 1: Complete ✅
- Basic project structure
- Dependency management
- Database connection setup
- Streamlit app with DB testing

### Phase 2: Complete ✅
- 11 comprehensive database models
- Repository pattern for data access
- Schema initialization and validation

### Phase 3: Complete ✅
- Project selector and management UI
- Settings configuration (12 fields)
- Project context editor
- User management

### Phase 4: Complete ✅
- AI chat panel with OpenAI integration
- Real-time token tracking
- Token usage meter with progress bar
- Chat history and session management
- "Baton now" placeholder

**⚠️ Database Migration Required**: If upgrading from Phase 3, see `MIGRATION_PHASE4.md`

### Phase 5: Complete ✅
- Design Tree node management UI
- Node versioning with full history
- Domain grouping and organization
- Draft management workflow
- AI-powered rant→summary with OpenAI
- Node editor with version control
- Status transitions (Draft, Active, Archived, Deleted)
- Attach summaries to existing nodes or create new ones

**📚 See `PHASE5_DESIGN_TREE.md` for detailed documentation**

### Phase 6: Complete ✅
- Baton snapshot generation with AI-generated project overview
- Manual baton creation via "Baton Now" button
- Auto-baton triggered when token threshold reached
- Warm-up sequence using configurable warmup_prompt_1..4
- Session switcher for warmed pending sessions
- Warm-up message filtering (hidden by default, toggle to show)
- Session status tracking (ACTIVE, WARMING, WARMED_PENDING, ARCHIVED)
- Comprehensive project state capture in batons
- Fresh token budget with preserved context

**⚠️ Database Migration Required**: See `MIGRATION_PHASE6.md`
**📚 See `PHASE6_BATON_WARMUP.md` for detailed documentation and workflow review**

### Phase 7: Complete ✅
- Auto project description generation from nodes using AI
- Description mode selector (Manual, Auto, Merged)
- AI-powered comprehensive project analysis and summarization
- Truth Doc markdown export with full project documentation
- Preview and download functionality for Truth Doc
- Complete component index with version history
- Integrated description modes in Batons and exports
- Project Context UI with regenerate and preview features

**⚠️ Database Migration Required**: See `MIGRATION_PHASE7.md`
**📚 See `PHASE7_AUTO_DESCRIPTION_TRUTH_DOC.md` for detailed documentation and workflow review**

### Phase 8: Complete ✅
- PIN lock for basic application security
- Current project and session display for better user orientation
- "New session (no baton)" button for clean slate conversations
- Node search/filter for quick navigation in large projects
- Comprehensive error handling review and documentation
- UX improvements and session state management
- Help text for PIN recovery and graceful fallbacks

**📚 See `PHASE8_POLISH_UX.md` for detailed documentation and workflow review**

### Phase 9: Complete ✅
- Full codebase cleanup pass (removed dead code, debug prints, stale TODOs)
- Naming and terminology consistency verification
- Settings and environment variable alignment
- Comprehensive smoke test script for environment verification
- README enhancements (Quickstart, Architecture overview, Testing sections)
- Code style and syntax validation
- Production-ready codebase with zero technical debt

**📚 See `PHASE9_CLEANUP_SMOKE_TEST.md` for detailed documentation and review**

## Troubleshooting

### Database Connection Issues

1. Verify your `DATABASE_URL` is correct in `.env`
2. Ensure your Neon database is active
3. Check that the connection string includes `?sslmode=require`
4. Test connectivity to your database host

### Import Errors

Make sure you're running the app from the project root:
```bash
# From the design-tree-studio directory
streamlit run app/streamlit_app.py
```

## License

MIT
