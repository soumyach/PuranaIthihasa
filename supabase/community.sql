-- Khatakshetra — Community features schema (run AFTER schema.sql + rls-policies.sql).
-- Adds the opt-in public leaderboard. user_progress stays private (own-row RLS),
-- so the leaderboard is a SEPARATE table that users explicitly opt into, exposing
-- only a handle + XP + level (no email, no personal data) for the current week.

create table if not exists public.leaderboard_entries (
  user_id    uuid primary key references public.app_users(id) on delete cascade,
  handle     text not null,
  xp         integer not null default 0,
  level      integer not null default 1,
  week_start date not null,
  updated_at timestamptz default now()
);

create index if not exists idx_leaderboard_week_xp on public.leaderboard_entries (week_start, xp desc);

alter table public.leaderboard_entries enable row level security;

-- Anyone may READ the board (it only contains a handle + xp + level).
create policy leaderboard_public_read on public.leaderboard_entries
  for select using (true);

-- A signed-in user may create/update ONLY their own entry.
create policy leaderboard_self_insert on public.leaderboard_entries
  for insert with check (auth.uid() = user_id);
create policy leaderboard_self_update on public.leaderboard_entries
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy leaderboard_self_delete on public.leaderboard_entries
  for delete using (auth.uid() = user_id);
