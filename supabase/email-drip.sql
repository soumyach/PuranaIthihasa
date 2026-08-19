-- ============================================================================
-- Khatakshetra — email send log for the drip sequence
-- Run once in the Supabase SQL editor (Project → SQL Editor → New query).
--
-- WHY a separate table rather than columns on email_subscribers:
--   * one subscriber receives many emails over time, so this is one-to-many
--   * a per-send row is what lets us answer "what did this family actually
--     receive, when, and did it fail?" months later
--   * the UNIQUE index below is the double-send guard. Sending is only ever
--     attempted after this row is claimed, so a cron that runs twice, or two
--     runs overlapping, cannot email the same person the same thing twice.
-- ============================================================================

create table if not exists public.email_sends (
  id                   uuid primary key default gen_random_uuid(),
  email                text        not null,
  template             text        not null,   -- welcome | day2 | day5 | weekly
  -- dedupe_key is what uniqueness is enforced on:
  --   one-shot emails  → the template name ('welcome', 'day2', 'day5')
  --   repeating emails → template + period ('weekly-2026-W34')
  dedupe_key           text        not null,
  status               text        not null default 'pending',  -- pending | sent | failed | skipped
  error                text,
  provider_message_id  text,
  claimed_at           timestamptz not null default now(),
  sent_at              timestamptz,
  metadata             jsonb       not null default '{}'::jsonb
);

-- The double-send guard. Claim-then-send relies on this.
create unique index if not exists email_sends_email_dedupe_uidx
  on public.email_sends (lower(email), dedupe_key);

-- "What has this subscriber been sent?" — the common lookup.
create index if not exists email_sends_email_time_idx
  on public.email_sends (lower(email), claimed_at desc);

-- "What went out today / what failed?" — for the daily check.
create index if not exists email_sends_status_time_idx
  on public.email_sends (status, claimed_at desc);

-- Server-only: every write goes through the service-role key in the cron
-- function. No policies are created, so anon/authenticated cannot read the
-- list of who we email.
alter table public.email_sends enable row level security;

comment on table public.email_sends is
  'One row per email we attempt to send. Claimed before sending; the unique index on (lower(email), dedupe_key) prevents double sends.';

-- ---------------------------------------------------------------------------
-- Convenience view: where each subscriber stands in the sequence.
-- ---------------------------------------------------------------------------
create or replace view public.email_subscriber_progress as
select
  s.email,
  s.created_at                                          as joined_at,
  date_part('day', now() - s.created_at)::int            as days_since_join,
  coalesce(s.weekly_digest, false)                       as weekly_digest,
  coalesce(s.subscribed, true)                           as subscribed,
  max(case when l.template = 'welcome' and l.status = 'sent' then l.sent_at end) as welcome_sent_at,
  max(case when l.template = 'day2'    and l.status = 'sent' then l.sent_at end) as day2_sent_at,
  max(case when l.template = 'day5'    and l.status = 'sent' then l.sent_at end) as day5_sent_at,
  max(case when l.template = 'weekly'  and l.status = 'sent' then l.sent_at end) as last_weekly_sent_at,
  count(l.id) filter (where l.status = 'sent')           as emails_sent,
  count(l.id) filter (where l.status = 'failed')         as emails_failed
from public.email_subscribers s
left join public.email_sends l on lower(l.email) = lower(s.email)
group by s.email, s.created_at, s.weekly_digest, s.subscribed;

comment on view public.email_subscriber_progress is
  'Per-subscriber drip position: when each email went out, how many sent, how many failed.';
