-- Phase 3.6.2 — app chat sessions (same DB as LangGraph checkpoints)
-- Idempotent: safe to run on every API startup.

CREATE TABLE IF NOT EXISTS conversations (
  thread_id UUID PRIMARY KEY,
  user_id TEXT NOT NULL DEFAULT 'local',
  title TEXT NOT NULL DEFAULT 'New chat',
  semantic_layer TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_updated
  ON conversations (user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
  id UUID NOT NULL,
  thread_id UUID NOT NULL REFERENCES conversations (thread_id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  seq INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (thread_id, id)
);

CREATE INDEX IF NOT EXISTS idx_messages_thread_seq
  ON messages (thread_id, seq);
