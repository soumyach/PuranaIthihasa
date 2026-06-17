-- Khatakshetra — Row-Level Security + sync columns.
-- Run this AFTER schema.sql, once, in the Supabase SQL editor.
--
-- WHY THIS IS REQUIRED: the browser uses the PUBLIC anon key. Without RLS,
-- anyone could read or write every row. These policies restrict each user to
-- their OWN rows. Server-only tables (email_captures, user_events) get RLS
-- enabled with NO public policy, so only the service-role key (which bypasses
-- RLS) can write them — exactly what /api/email-capture and /api/event use.

-- 1. Columns the client sync needs (idempotent) -----------------------------
alter table public.user_progress add column if not exists cards jsonb not null default '[]'::jsonb;
alter table public.user_progress add column if not exists daily jsonb not null default '{}'::jsonb;

-- Upserts target one row per user; enforce uniqueness on user_id.
create unique index if not exists user_progress_user_id_uidx
  on public.user_progress (user_id) where user_id is not null;

-- 2. Enable RLS ---------------------------------------------------------------
alter table public.app_users          enable row level security;
alter table public.user_progress      enable row level security;
alter table public.quiz_attempts      enable row level security;
alter table public.unlocks            enable row level security;
alter table public.referrals          enable row level security;
alter table public.submissions        enable row level security;
alter table public.user_tips          enable row level security;
alter table public.comments           enable row level security;
-- Server-only (no policy below = only service role can touch them):
alter table public.email_captures     enable row level security;
alter table public.user_events        enable row level security;

-- 3. Own-row policies ---------------------------------------------------------
-- app_users: a signed-in user can read/insert/update only their own row.
create policy app_users_self_select on public.app_users
  for select using (auth.uid() = id);
create policy app_users_self_upsert on public.app_users
  for insert with check (auth.uid() = id);
create policy app_users_self_update on public.app_users
  for update using (auth.uid() = id) with check (auth.uid() = id);

-- user_progress: full own-row access.
create policy user_progress_self_all on public.user_progress
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- quiz_attempts: insert + read own.
create policy quiz_attempts_self_ins on public.quiz_attempts
  for insert with check (auth.uid() = user_id);
create policy quiz_attempts_self_sel on public.quiz_attempts
  for select using (auth.uid() = user_id);

-- unlocks + referrals: own-row.
create policy unlocks_self_all on public.unlocks
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy referrals_self_all on public.referrals
  for all using (auth.uid() = referrer_user_id) with check (auth.uid() = referrer_user_id);

-- Community / UGC (used once those features ship):
-- submit own; everyone can read APPROVED items.
create policy submissions_self_ins on public.submissions
  for insert with check (auth.uid() = user_id);
create policy submissions_read_approved on public.submissions
  for select using (moderation_status = 'approved' or auth.uid() = user_id);

create policy user_tips_self_ins on public.user_tips
  for insert with check (auth.uid() = user_id);
create policy user_tips_read_approved on public.user_tips
  for select using (moderation_status = 'approved' or auth.uid() = user_id);

create policy comments_self_ins on public.comments
  for insert with check (auth.uid() = user_id);
create policy comments_read_approved on public.comments
  for select using (moderation_status = 'approved' or auth.uid() = user_id);

-- NOTE: content tables (stories, quizzes, kg_nodes, temple_profiles, ...) are
-- intentionally NOT used by the client — content is served from /content JSON +
-- static pages. Leave them as-is (or enable RLS with a public-read policy only
-- if you later decide to serve content from the DB).
