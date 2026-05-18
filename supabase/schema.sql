-- Supabase schema for Khatakshetra.
-- Repo/project name: PuranaIthihasa.
-- This is the recommended starting point; run after creating the Supabase project.

create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

create table if not exists public.app_users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  full_name text,
  phone text,
  preferred_language text default 'en',
  country text,
  city text,
  child_age_band text,
  source text,
  consent_email boolean default true,
  consent_whatsapp boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.email_captures (
  id uuid primary key default gen_random_uuid(),
  email_id text not null,
  cta text not null,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  unique (email_id, cta)
);

create table if not exists public.user_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.app_users(id) on delete set null,
  anonymous_id text,
  event_name text not null,
  event_properties jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists public.sources (
  id text primary key,
  title text not null,
  tradition text,
  language text,
  translator text,
  license_status text not null default 'unknown',
  source_url text,
  notes text,
  review_status text not null default 'unreviewed',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.source_sections (
  id text primary key,
  source_id text references public.sources(id) on delete cascade,
  parent_id text references public.source_sections(id) on delete set null,
  title text not null,
  section_path text,
  source_url text,
  raw_text text,
  extracted_notes jsonb default '{}'::jsonb,
  review_status text not null default 'unreviewed',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.kg_nodes (
  id text primary key,
  slug text unique not null,
  node_type text not null,
  name text not null,
  summary text,
  aliases jsonb default '[]'::jsonb,
  properties jsonb default '{}'::jsonb,
  review_status text not null default 'seed',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.kg_edges (
  id uuid primary key default gen_random_uuid(),
  from_node_id text references public.kg_nodes(id) on delete cascade,
  to_node_id text references public.kg_nodes(id) on delete cascade,
  edge_type text not null,
  source_section_id text references public.source_sections(id) on delete set null,
  confidence numeric(4,3) default 0.700,
  review_status text not null default 'unreviewed',
  properties jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  unique (from_node_id, to_node_id, edge_type, source_section_id)
);

create table if not exists public.stories (
  id text primary key,
  slug text unique not null,
  title text not null,
  summary text,
  kid_summary text,
  adult_cinematic_narrative text,
  kids_narrative_5_8 text,
  kids_narrative_9_12 text,
  aeo_short_answer text,
  seo jsonb default '{}'::jsonb,
  language text not null default 'en',
  review_status text not null default 'draft',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.story_sources (
  story_id text references public.stories(id) on delete cascade,
  source_section_id text references public.source_sections(id) on delete cascade,
  usage_note text,
  primary key (story_id, source_section_id)
);

create table if not exists public.story_entities (
  story_id text references public.stories(id) on delete cascade,
  node_id text references public.kg_nodes(id) on delete cascade,
  role text,
  primary key (story_id, node_id)
);

create table if not exists public.quizzes (
  id text primary key,
  slug text unique not null,
  title text not null,
  age_band text,
  language text not null default 'en',
  questions jsonb not null,
  related_story_ids jsonb default '[]'::jsonb,
  review_status text not null default 'draft',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.quiz_attempts (
  id uuid primary key default gen_random_uuid(),
  quiz_id text references public.quizzes(id) on delete set null,
  user_id uuid references public.app_users(id) on delete set null,
  anonymous_id text,
  score integer,
  total integer,
  answers jsonb default '[]'::jsonb,
  completed_at timestamptz default now()
);

create table if not exists public.unlocks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.app_users(id) on delete cascade,
  unlock_type text not null,
  unlock_key text not null,
  source_event text,
  expires_at timestamptz,
  created_at timestamptz default now(),
  unique (user_id, unlock_type, unlock_key)
);

create table if not exists public.referrals (
  id uuid primary key default gen_random_uuid(),
  referrer_user_id uuid references public.app_users(id) on delete cascade,
  referred_email text,
  referral_code text not null,
  status text not null default 'sent',
  created_at timestamptz default now(),
  converted_at timestamptz
);

create table if not exists public.competitions (
  id text primary key,
  slug text unique not null,
  title text not null,
  festival text,
  age_bands jsonb default '[]'::jsonb,
  starts_at timestamptz,
  ends_at timestamptz,
  rules text,
  status text not null default 'draft',
  created_at timestamptz default now()
);

create table if not exists public.submissions (
  id uuid primary key default gen_random_uuid(),
  competition_id text references public.competitions(id) on delete set null,
  user_id uuid references public.app_users(id) on delete set null,
  submission_type text not null,
  title text,
  asset_url text,
  caption text,
  parent_consent boolean default false,
  moderation_status text not null default 'pending',
  created_at timestamptz default now(),
  reviewed_at timestamptz
);

create table if not exists public.products (
  id text primary key,
  slug text unique not null,
  brand text not null,
  title text not null,
  lead_tag text,
  status text not null default 'waitlist',
  data jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.temple_profiles (
  id text primary key,
  slug text unique not null,
  name text not null,
  aliases jsonb default '[]'::jsonb,
  primary_deity_node_id text references public.kg_nodes(id) on delete set null,
  state text,
  city text,
  locality text,
  country text default 'India',
  address text,
  latitude numeric(10,7),
  longitude numeric(10,7),
  official_website text,
  google_place_id text,
  map_url text,
  timings jsonb default '{}'::jsonb,
  ritual_timings jsonb default '[]'::jsonb,
  festivals jsonb default '[]'::jsonb,
  how_to_reach jsonb default '{}'::jsonb,
  nearby_food jsonb default '[]'::jsonb,
  nearby_places jsonb default '[]'::jsonb,
  accessibility_notes text,
  etiquette_notes text,
  story_summary text,
  sthala_purana text,
  source_refs jsonb default '[]'::jsonb,
  freshness_status text not null default 'unverified',
  last_verified_at timestamptz,
  review_status text not null default 'draft',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.temple_content_sources (
  id uuid primary key default gen_random_uuid(),
  temple_id text references public.temple_profiles(id) on delete cascade,
  source_type text not null,
  source_url text,
  source_title text,
  extracted_summary text,
  raw_snapshot jsonb default '{}'::jsonb,
  captured_at timestamptz default now(),
  review_status text not null default 'unreviewed'
);

create table if not exists public.comments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.app_users(id) on delete set null,
  target_type text not null,
  target_id text not null,
  body text not null,
  parent_id uuid references public.comments(id) on delete cascade,
  moderation_status text not null default 'pending',
  created_at timestamptz default now(),
  reviewed_at timestamptz
);

create table if not exists public.user_tips (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.app_users(id) on delete set null,
  temple_id text references public.temple_profiles(id) on delete cascade,
  tip_type text not null,
  title text,
  body text not null,
  visit_month text,
  moderation_status text not null default 'pending',
  created_at timestamptz default now(),
  reviewed_at timestamptz
);

create index if not exists idx_user_events_user_id on public.user_events(user_id);
create index if not exists idx_user_events_event_name on public.user_events(event_name);
create index if not exists idx_kg_edges_from on public.kg_edges(from_node_id);
create index if not exists idx_kg_edges_to on public.kg_edges(to_node_id);
create index if not exists idx_stories_slug on public.stories(slug);
create index if not exists idx_submissions_competition on public.submissions(competition_id);
create index if not exists idx_temple_profiles_state_city on public.temple_profiles(state, city);
create index if not exists idx_temple_profiles_deity on public.temple_profiles(primary_deity_node_id);
create index if not exists idx_comments_target on public.comments(target_type, target_id);
create index if not exists idx_user_tips_temple on public.user_tips(temple_id);
