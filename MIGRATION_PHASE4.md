# Phase 4 Database Migration

## Schema Changes

Phase 4 adds token tracking fields to the `ChatSession` model.

### New Fields in `chat_sessions` Table

```sql
ALTER TABLE chat_sessions
ADD COLUMN total_prompt_tokens INTEGER DEFAULT 0 NOT NULL,
ADD COLUMN total_completion_tokens INTEGER DEFAULT 0 NOT NULL,
ADD COLUMN total_tokens_used INTEGER DEFAULT 0 NOT NULL;
```

## Migration Options

### Option 1: Recreate Schema (Development Only)

If you're in development and don't have important data:

1. Drop existing schema:
   ```bash
   # In Streamlit app, go to System Status tab
   # (You'll need to add a drop schema button or use psql)
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

2. Run the ALTER TABLE command:
   ```sql
   ALTER TABLE chat_sessions
   ADD COLUMN IF NOT EXISTS total_prompt_tokens INTEGER DEFAULT 0 NOT NULL,
   ADD COLUMN IF NOT EXISTS total_completion_tokens INTEGER DEFAULT 0 NOT NULL,
   ADD COLUMN IF NOT EXISTS total_tokens_used INTEGER DEFAULT 0 NOT NULL;
   ```

3. Verify the changes:
   ```sql
   \d chat_sessions
   ```

### Option 3: Using Alembic (Future)

Alembic migrations will be added in a future phase for automatic schema updates.

## Verification

After migration, verify the new fields exist:

```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'chat_sessions'
  AND column_name IN ('total_prompt_tokens', 'total_completion_tokens', 'total_tokens_used');
```

Expected output:
```
       column_name        | data_type | column_default
--------------------------+-----------+----------------
 total_prompt_tokens      | integer   | 0
 total_completion_tokens  | integer   | 0
 total_tokens_used        | integer   | 0
```

## Notes

- Existing chat sessions will have token counts initialized to 0
- Token tracking will begin with new messages after migration
- No data loss occurs with this migration
