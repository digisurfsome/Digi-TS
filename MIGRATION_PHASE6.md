# Phase 6 Database Migration

## Schema Changes

Phase 6 adds baton snapshot generation and warm-up functionality, requiring several schema updates.

### 1. New Enum Type: SessionStatus

```sql
CREATE TYPE sessionstatus AS ENUM ('active', 'warming', 'warmed_pending', 'archived');
```

### 2. Updates to `chat_sessions` Table

```sql
-- Add status column for warm-up workflow
ALTER TABLE chat_sessions
ADD COLUMN status sessionstatus DEFAULT 'active' NOT NULL;
```

### 3. Updates to `chat_messages` Table

```sql
-- Add is_warmup flag to identify warm-up messages
ALTER TABLE chat_messages
ADD COLUMN is_warmup BOOLEAN DEFAULT FALSE NOT NULL;
```

### 4. Updates to `baton_snapshots` Table

```sql
-- Add session_id to link baton to new warmed session
ALTER TABLE baton_snapshots
ADD COLUMN session_id INTEGER NOT NULL REFERENCES chat_sessions(id);

-- Add user_id for creator tracking
ALTER TABLE baton_snapshots
ADD COLUMN user_id INTEGER NOT NULL REFERENCES user_profiles(id);

-- Add snapshot_body for AI-generated markdown description
ALTER TABLE baton_snapshots
ADD COLUMN snapshot_body TEXT NOT NULL;

-- Add indexes for performance
CREATE INDEX idx_baton_snapshots_session_id ON baton_snapshots(session_id);
CREATE INDEX idx_baton_snapshots_user_id ON baton_snapshots(user_id);
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
   CREATE TYPE sessionstatus AS ENUM ('active', 'warming', 'warmed_pending', 'archived');

   -- Update chat_sessions table
   ALTER TABLE chat_sessions
   ADD COLUMN IF NOT EXISTS status sessionstatus DEFAULT 'active' NOT NULL;

   -- Update chat_messages table
   ALTER TABLE chat_messages
   ADD COLUMN IF NOT EXISTS is_warmup BOOLEAN DEFAULT FALSE NOT NULL;

   -- Update baton_snapshots table
   -- Note: If you have existing baton_snapshots, you may need to handle them differently
   -- These commands assume the table is empty or you're okay with dropping it

   -- Option A: If baton_snapshots is empty, add columns
   ALTER TABLE baton_snapshots
   ADD COLUMN IF NOT EXISTS session_id INTEGER;

   ALTER TABLE baton_snapshots
   ADD COLUMN IF NOT EXISTS user_id INTEGER;

   ALTER TABLE baton_snapshots
   ADD COLUMN IF NOT EXISTS snapshot_body TEXT;

   -- Add foreign key constraints (after populating data if needed)
   ALTER TABLE baton_snapshots
   ADD CONSTRAINT fk_baton_snapshots_session_id
   FOREIGN KEY (session_id) REFERENCES chat_sessions(id);

   ALTER TABLE baton_snapshots
   ADD CONSTRAINT fk_baton_snapshots_user_id
   FOREIGN KEY (user_id) REFERENCES user_profiles(id);

   -- Add indexes
   CREATE INDEX IF NOT EXISTS idx_baton_snapshots_session_id ON baton_snapshots(session_id);
   CREATE INDEX IF NOT EXISTS idx_baton_snapshots_user_id ON baton_snapshots(user_id);

   -- Option B: If you want to start fresh with baton_snapshots
   DROP TABLE IF EXISTS baton_snapshots CASCADE;
   -- Then reinitialize schema from app
   ```

3. Verify the changes:
   ```sql
   -- Check chat_sessions
   \d chat_sessions

   -- Check chat_messages
   \d chat_messages

   -- Check baton_snapshots
   \d baton_snapshots
   ```

## Verification

After migration, verify the new fields exist:

### ChatSession Status

```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'chat_sessions'
  AND column_name = 'status';
```

Expected output:
```
 column_name |   data_type   | column_default
-------------+---------------+----------------
 status      | USER-DEFINED  | 'active'
```

### ChatMessage is_warmup

```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'chat_messages'
  AND column_name = 'is_warmup';
```

Expected output:
```
 column_name | data_type | column_default
-------------+-----------+----------------
 is_warmup   | boolean   | false
```

### BatonSnapshot New Fields

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'baton_snapshots'
  AND column_name IN ('session_id', 'user_id', 'snapshot_body');
```

Expected output:
```
  column_name  | data_type
---------------+-----------
 session_id    | integer
 user_id       | integer
 snapshot_body | text
```

## Notes

- Existing chat sessions will have status 'active' by default
- Existing chat messages will have is_warmup=false by default
- The SessionStatus enum supports the warm-up workflow:
  - `active`: Normal chat session ready for use
  - `warming`: Warm-up prompts are being processed
  - `warmed_pending`: Warm-up complete, ready to switch to
  - `archived`: Session has been archived
- BatonSnapshot now links to the new warmed ChatSession it creates
- No data loss occurs with this migration for chat_sessions and chat_messages
- If you have existing baton_snapshots, you may need to migrate or delete them

## Phase 6 Features

These schema changes enable:
- **Manual Baton**: User clicks "Baton Now" to create a new warmed session
- **Auto Baton**: Automatic baton creation when token threshold is reached
- **Warm-up Flow**: New sessions are pre-warmed with context using warmup_prompt_1..4
- **Session Switching**: Users can switch between active and warmed_pending sessions
- **Warm-up Message Filtering**: UI can hide/show warm-up messages separately
