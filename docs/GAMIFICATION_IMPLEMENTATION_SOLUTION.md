# Khatakshetra Gamification Implementation Solution

## What We Are Building

Khatakshetra should not feel like a content site with games attached. It should feel like a cultural world where stories, deities, temples, festivals, quizzes, coloring pages, booklets, and kits are all connected experiences.

The product model is:

- **Content is the world**: Ramayana, Ganesha, Shani Dev, Dashavatara, temples, festivals, and deities become explorable Kshetras.
- **Gamification is the physics**: progress, cards, family rooms, Vratas, Kula challenges, and Sabhas create reasons to return.
- **Physical kits are portals**: kit QR Seed Codes eventually unlock premium Kshetras, rare Talapatra cards, and Sabha access.

## Three Interlocking Loops

### 1. Learning Loop

Daily or session-level progress.

Implementation shape:

- Cosmic Map later; journey page now.
- Each Kshetra has nodes: story, quiz, coloring, booklet, family room, reflection.
- Completing nodes lights progress and grows the user's Parampara Tree.
- Quizzes unlock Talapatra cards only after demonstrated understanding.

Built now:

- `ramayana-journey.html` as the first journey spine.
- Persistent progress chip on pages using `site.js`.
- XP and culturally meaningful titles: Shravaka, Jigyasu, Sadhaka, Katha Vachak, Vidwan, Acharya.
- Talapatra reveal after quiz completion.
- Sangraha collection page.

### 2. Kula Loop

Weekly family or small-group belonging.

Implementation shape:

- Kula is a group of 4-12 people.
- Internal-only leaderboard.
- Shared weekly challenge.
- Collective Parampara Tree.
- Card gifting inside the Kula.

Not built yet:

- Real Kula account/group model.
- Shared progress sync.
- Kula moderation.

Reason:

This should follow Supabase Auth. Without real identity, Kula mechanics become fragile and could damage trust.

### 3. Sabha Loop

Seasonal public recognition tied to the Hindu calendar.

Implementation shape:

- Four major Sabhas per year.
- Individual track, Kula track, creative track.
- Winners get physical kits, not only badges.
- Public announcement becomes PR and proof.

Not built yet:

- Competition submissions.
- Moderation/review workflows.
- Winner pages.

Reason:

Sabha should launch after active Kulas exist. Early public competitions with low participation feel weak; the first Sabhas should be invite-only or founding-cohort only.

## Immediate Build Sequence

### Phase 1: The Spine

This is the ASAP slice.

- Replace `window.prompt` signup with a real modal.
- Add persistent progress chip on all content pages.
- Create Ramayana Journey as the first guided path.
- Reveal Talapatra cards after quiz completion.
- Add Sangraha page for earned cards.
- Add shareable WhatsApp completion path.

Status: implemented in this slice.

### Phase 2: Production Identity

Needed before real family/community mechanics.

- Supabase Auth with magic link.
- Tables:
  - `profiles`
  - `user_progress`
  - `user_events`
  - `talapatra_cards`
  - `user_cards`
  - `journey_progress`
  - `signups`
- Sync local progress into Supabase on login.
- Replace local signup capture with API write.

Status: designed, not connected because production Supabase env/project values are not confirmed in repo.

### Phase 3: Collector Hook

- Expand card catalog for Ramayana, Ganesha, Shani Dev, Dashavatara, Devi, Shiva, Vishnu, temples, and festivals.
- Add scratch-style reveal animation.
- Add card silhouettes for unearned cards.
- Add rarity logic:
  - Common: completion
  - Rare: strong score or journey completion
  - Epic: mastery
  - Legendary: Vrata, Sabha, kit QR Seed Code

Status: first simple reveal and storage implemented.

### Phase 4: Kula

- Create Kula by invite link.
- Add Kula home page.
- Show internal weekly challenge.
- Show member progress, not public leaderboard.
- Add card gifting.

### Phase 5: Vrata

- 7-day, 21-day, 40-day commitments.
- Unfinished rather than failed.
- Permanent Vrata Seal on profile.
- 40-day physical certificate or premium unlock.

### Phase 6: Sabha

- Founding cohort Sabha first.
- Invite-only until enough active families exist.
- Public winner pages after quality threshold is met.

## Impact On Current Site

The current build already has content pages, quiz pages, drawing pages, booklets, deity hubs, festival pages, temple pages, and kit interest CTAs. The issue was not lack of pages. The issue was weak orchestration.

This implementation changes the product feel by adding:

- A visible user identity layer.
- A guided journey page.
- A real signup modal.
- A reward reveal after quiz completion.
- A collection page.
- A WhatsApp completion share.

Nothing needs to be thrown away. Existing pages become nodes inside journeys.

## Success Criteria

For the next local validation cycle:

- A parent can understand the first journey in under 10 seconds.
- A child can complete story -> coloring -> quiz without getting lost.
- Quiz completion produces a memorable card reveal.
- The site asks for email at the moment of earned value, not before.
- A family can share completion on WhatsApp.
- Founder can demo this live in an HSR apartment event without explaining the backend.

## What Not To Build First

- Public leaderboard.
- Full community feed.
- Full Sabha infrastructure.
- Overly broad Cosmic Map before one journey works.
- XP as the hero metric.

XP exists as the accounting layer. The visible emotional layer should be Journey, Parampara Tree, Talapatra Cards, Kula, Vrata, and Sabha.
