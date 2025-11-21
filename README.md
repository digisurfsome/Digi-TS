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
│   └── ui/
│       └── layout.py         # UI components and layouts
├── pyproject.toml            # Poetry dependencies
├── requirements.txt          # Pip dependencies
└── .env.example             # Environment variables template
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

## Phase 1 Complete

This is Phase 1 of the project, which includes:
- ✅ Basic project structure
- ✅ Dependency management (pyproject.toml, requirements.txt)
- ✅ Environment configuration loading
- ✅ SQLAlchemy database connection setup
- ✅ Minimal Streamlit app with DB connection test

## Next Steps

- Phase 2: Define database schema and models
- Phase 3: Implement core functionality
- Phase 4: Add AI integration with OpenAI

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
