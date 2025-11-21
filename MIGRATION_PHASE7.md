# Phase 7 Database Migration

## Schema Changes

Phase 7 adds auto-generated project descriptions and description mode selection, requiring updates to the `project_contexts` table.

### 1. New Enum Type: DescriptionMode

```sql
CREATE TYPE descriptionmode AS ENUM ('manual', 'auto', 'merge');
```

### 2. Updates to `project_contexts` Table

```sql
-- Add auto_description column for AI-generated descriptions
ALTER TABLE project_contexts
ADD COLUMN auto_description TEXT;

-- Add description_mode column for mode selection
ALTER TABLE project_contexts
ADD COLUMN description_mode descriptionmode DEFAULT 'manual' NOT NULL;
```

## Migration Options

### Option 1: Recreate Schema (Development Only)

If you're in development and don't have important data:

1. Drop existing schema:
   ```bash
   # In Streamlit app, go to System Status tab
   # or use psql to drop tables
   ```

2. Reinitialize schema:
   - Go to System Status tab
   - Click "Initialize Schema" button
   - All tables will be recreated with new fields

### Option 2: Manual SQL Update (Production)

If you have existing data to preserve:

1. Connect to your Neon database:
   ```bash
   psql "your_database_url_here"
   ```

2. Run the migration commands:
   ```sql
   -- Create new enum type
   CREATE TYPE descriptionmode AS ENUM ('manual', 'auto', 'merge');

   -- Update project_contexts table
   ALTER TABLE project_contexts
   ADD COLUMN IF NOT EXISTS auto_description TEXT;

   ALTER TABLE project_contexts
   ADD COLUMN IF NOT EXISTS description_mode descriptionmode DEFAULT 'manual' NOT NULL;
   ```

3. Verify the changes:
   ```sql
   -- Check project_contexts
   \d project_contexts
   ```

## Verification

After migration, verify the new fields exist:

### ProjectContext auto_description

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'project_contexts'
  AND column_name = 'auto_description';
```

Expected output:
```
   column_name    | data_type | is_nullable
------------------+-----------+-------------
 auto_description | text      | YES
```

### ProjectContext description_mode

```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'project_contexts'
  AND column_name = 'description_mode';
```

Expected output:
```
   column_name    |   data_type   | column_default
------------------+---------------+----------------
 description_mode | USER-DEFINED  | 'manual'
```

## Notes

- Existing project contexts will have `description_mode` set to 'manual' by default
- Existing project contexts will have `auto_description` as NULL until generated
- The DescriptionMode enum supports three modes:
  - `manual`: Use only the manually entered content field
  - `auto`: Use only the AI-generated auto_description field
  - `merge`: Combine both manual and auto descriptions
- No data loss occurs with this migration
- Auto descriptions can be generated on-demand via the "🔄 Regenerate" button in Project Context UI

## Phase 7 Features

These schema changes enable:

### Auto Project Description
- **generate_auto_project_description()**: Analyzes all project nodes and generates a comprehensive description
- Uses OpenAI (DEFAULT_SUMMARY_MODEL) to create structured markdown
- Captures project structure, domains, components, and relationships
- Stored in `project_contexts.auto_description`

### Description Mode Selector
- **Manual Only**: Uses `content` field (traditional behavior)
- **Auto-Generated Only**: Uses `auto_description` field
- **Merged**: Combines both with clear sections
- Affects:
  - Baton snapshot generation
  - Truth Doc export
  - Project context display

### Truth Doc Export
- Comprehensive markdown documentation
- Includes project overview with selected description mode
- Component index grouped by domain
- Detailed sections for each component with version history
- Download as .md file or copy to clipboard
- Optional inclusion of archived/deleted nodes

## Configuration Integration

Uses existing Settings:
- **DEFAULT_SUMMARY_MODEL**: Model for auto description generation (e.g., "gpt-4-turbo-preview")
- **OPENAI_API_KEY**: Required for AI-generated descriptions

## UI Features

### Project Context Tab
- **Description Mode Selector**: Choose Manual/Auto/Merge
- **Manual Description Editor**: Traditional text area for manual entry
- **Auto Description Display**: Read-only view of AI-generated description
- **Regenerate Button**: Generate fresh auto description from current nodes
- **Preview Combined**: See how description will appear in Batons/Truth Doc

### Truth Doc Tab
- **Export Options**: Include/exclude archived nodes
- **Preview**: View first 100 lines before download
- **Export**: Generate complete markdown document
- **Download**: Save as .md file with timestamped filename
- **Copy**: View full markdown in code block for clipboard copy

## Benefits

- **Automatic Documentation**: AI generates descriptions from actual project structure
- **Flexibility**: Choose between manual, auto, or combined descriptions
- **Consistency**: Auto descriptions stay up-to-date with project changes
- **Comprehensive Export**: Truth Doc provides complete project documentation
- **Version Control Friendly**: Markdown format works with git
- **Handoff Ready**: Perfect for team transitions or client deliverables

## Example Workflows

### Generate Auto Description
1. Build out your project nodes in Design Tree
2. Go to Project Context tab
3. Click "🔄 Regenerate" under Auto Description
4. AI analyzes all nodes and creates comprehensive description
5. Switch Description Mode to "Auto" or "Merge"
6. Auto description now used in Batons and Truth Doc

### Export Truth Doc
1. Go to Truth Doc tab
2. Click "👁️ Preview" to see first 100 lines
3. Click "📥 Export" to generate full document
4. Download .md file or copy from code block
5. Share with team, commit to repo, or archive

### Use Merged Mode
1. Write manual context with design guidelines and constraints
2. Generate auto description from nodes
3. Set Description Mode to "Merged"
4. Both descriptions appear in Batons/Truth Doc
5. Manual: team guidelines, Auto: current structure

## Database Migration Required

**⚠️ IMPORTANT**: This migration is required for Phase 7 functionality.

New schema fields:
- CREATE TYPE descriptionmode
- ALTER TABLE project_contexts ADD COLUMN auto_description
- ALTER TABLE project_contexts ADD COLUMN description_mode

See migration commands above for complete instructions.
