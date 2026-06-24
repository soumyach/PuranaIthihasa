-- Per-email subscription preferences for the welcome + weekly emails.
-- `email_captures` remains the raw capture log; this table is the source of
-- truth for subscribe / unsubscribe / weekly-digest, keyed by an unguessable
-- per-email token used in unsubscribe + preferences links.
-- Run once in the Supabase SQL editor (after schema.sql).

create extension if not exists pgcrypto;

create table if not exists public.email_subscribers (
  email          text primary key,
  token          uuid not null default gen_random_uuid(),
  subscribed     boolean not null default true,
  weekly_digest  boolean not null default true,
  source_cta     text,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create unique index if not exists email_subscribers_token_idx on public.email_subscribers (token);

-- Server-only: the /api/email-capture and /api/preferences endpoints use the
-- service role (which bypasses RLS). No anon/public policies are added, so the
-- public anon key cannot read or modify subscribers. Access is via token only.
alter table public.email_subscribers enable row level security;
