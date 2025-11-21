# Design Tree Studio

AI-Powered Design Management System

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

## Testing Database Connection

The main application page includes a database connection test that will:
- Verify your environment variables are configured
- Test the connection to your Neon database
- Display the connection status

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
