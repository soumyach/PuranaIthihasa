# Landing Page, IAM, Navigation, and Experience Plan

## 1. Homepage Objective

The homepage should not feel like a directory. It should convert visitors into one of four actions:

1. Start reading a story.
2. Unlock a digital booklet/drawing kit.
3. Join a quiz or competition.
4. Join a kit/community waitlist.

The homepage promise:

> Stories, temple guides, booklets, games, competitions, and cultural experiences for seekers, families, and communities.

## 2. First-Viewport Design

Keep the current premium visual language:

- `Cinzel`, `Cinzel Decorative`, `Playfair Display`, `Crimson Text`.
- dark devotional background,
- antique gold/saffron accents,
- premium archive/book feel,
- no generic SaaS dashboard layout.

First viewport:

- Brand: `Khatakshetra`.
- Headline: "Unlock your first Khatakshetra story experience in 60 seconds."
- Supporting copy: "Get a cinematic story, digital booklet preview, quiz, drawing kit, and talapatra wisdom card — then unlock more through points, challenges, and referrals."
- Primary CTA: `Unlock Free Story Kit`.
- Secondary CTA: `Explore Experiences`.
- Tertiary low-friction CTA: `Find a Temple Guide`.

The hero may show multiple features, but through one controlled animated experience carousel. The copy and CTA must remain focused.

## 3. Homepage Sections

### Section 1: Hero

Goal: immediate clarity and conversion.

Hero animation frames:

- cinematic story,
- hardbound booklet,
- talapatra card,
- quiz,
- drawing kit,
- temple guide,
- competition/community,
- kit waitlist.

### Section 2: Featured Story Experience

Show one polished story:

- cinematic story card,
- source badge,
- `Read`,
- `Listen`,
- `View Booklet`,
- `Take Quiz`.

First candidate: Rama Navami reader or Dasharatha Meets Shani once source-reviewed.

### Section 3: Digital Booklets

Show the premium hardbound digital experience:

- cover mockup,
- page spread,
- talapatra insert,
- audio button.

CTA: `Open Free Booklet`.

### Section 4: Kids Drawing + Coloring Kits

Show:

- 3 free pages,
- email unlock,
- competition prompt.

CTA: `Start Coloring`.

### Section 5: Quizzes and Competitions

Show:

- Rama Navami quiz,
- Shani Dev quiz,
- upcoming festival challenge.

CTA: `Play a Quiz`.

### Section 6: Temple Guides

Show state/city temple guide preview:

- temple story,
- timings,
- how to reach,
- what not to miss,
- food/prasadam/local tips.

CTA: `Explore Temples`.

### Section 7: Khatakshetra Kits

Show 3 physical/digital product lines:

- Ganesh Chaturthi: The Remover.
- Rath Yatra: The Great Journey.
- Raksha Bandhan + Janmashtami: The Bond and the Butter Thief.

CTA: `Join Kit Waitlist`.

### Section 8: Community Proof

Once available:

- child artwork,
- quiz leaderboard,
- parent comments,
- temple tips,
- referral unlocks.

Do not fake social proof before it exists.

## 4. Minimal Navigation

Use fewer top-level items to maximize conversion.

Recommended desktop nav:

- Stories
- Temples
- Kids
- Kits
- Sign In

Primary button:

- `Start Free`

Mobile nav:

- Home
- Stories
- Play
- Temples
- Profile

Avoid exposing:

- KG,
- admin,
- source ingestion,
- all collections,
- every future feature.

Those should exist, but not dominate navigation.

## 5. Information Architecture

Public:

```text
/
/stories
/stories/:slug
/booklets/:slug
/audio/:slug
/quizzes
/quizzes/:slug
/drawing-kits
/drawing-kits/:slug
/temples
/temples/:state
/temples/:state/:city
/temples/:state/:city/:temple
/kits
/kits/:slug
/community
/competitions/:slug
```

Private/authenticated:

```text
/profile
/profile/booklets
/profile/drawings
/profile/quiz-scores
/profile/unlocks
/profile/referrals
/profile/submissions
```

Internal/admin:

```text
/admin/content
/admin/sources
/admin/entities
/admin/temples
/admin/moderation
/admin/campaigns
```

## 6. IAM Strategy

Use progressive identity. Do not force login too early.

### Anonymous User

Can:

- read public stories,
- view temple guides,
- try first quiz,
- color first free pages,
- view sample booklet.

Track with anonymous id.

### Email User

Created when they:

- unlock more coloring pages,
- save quiz result,
- join kit waitlist,
- enter competition,
- save booklet progress.

Use Supabase Auth magic link or OTP.

### Parent Profile

Stores:

- email,
- name,
- phone optional,
- preferred language,
- country/city,
- child age band,
- consent email,
- consent WhatsApp,
- interests.

### Child-Safe Model

Do not require child accounts initially.

Store child info as parent-provided preferences:

- age band,
- interests,
- unlocks,
- submissions.

Public submissions require parent consent and moderation.

### Admin Roles

Roles:

- `admin`,
- `editor`,
- `reviewer`,
- `moderator`,
- `temple_researcher`,
- `community_manager`.

Moderation required for:

- comments,
- temple tips,
- uploaded artwork,
- competition submissions,
- user-generated questions.

## 7. Conversion Model

Homepage CTA sequence:

1. Free story.
2. Free quiz/drawing action.
3. Email unlock.
4. Profile creation.
5. Referral or competition.
6. Kit waitlist/preorder.

Lead magnets:

- "Unlock 5 Ramayana coloring pages."
- "Get the Shani Dev audio story."
- "Download the Ganesh Chaturthi booklet."
- "Join the festival challenge."
- "Get temple guide updates for your city."

## 8. Conversation Experience

Do not build full chat now, but reserve the surface.

Future conversation should be:

- source-aware,
- story-guided,
- child-safe,
- citation-backed,
- routed by context.

Initial version can be "Ask Khatakshetra":

- ask about a story,
- ask about a deity,
- ask temple practical questions,
- ask for kid explanation,
- ask for quiz questions,
- ask what to read next.

Do not expose this until enough content exists. Otherwise it will feel empty.

## 9. Experience Surfaces

### Booklets

- premium hardbound digital feel,
- page-turn,
- audio,
- talapatra cards,
- source page,
- reflection prompts.

### Quizzes

- beginner/intermediate/advanced,
- story-linked,
- score storage,
- certificates,
- leaderboard optional.

### Multiplayer

Start simple:

- family quiz room,
- one host screen,
- multiple players enter code,
- festival challenge mode.

Later:

- team challenges,
- school/cultural center mode,
- timed competitions.

### Profile

Show:

- saved booklets,
- drawing gallery,
- quiz scores,
- unlocked packs,
- referrals,
- submissions,
- language preference,
- kit waitlist status.

### Community Content

Types:

- parent comments,
- child artwork,
- temple tips,
- festival photos,
- questions,
- story requests.

All public community content should be moderated.

## 10. Immediate Build Recommendation

Build in this order:

1. New Khatakshetra homepage.
2. Story index and one generated story page.
3. Free drawing kit unlock.
4. Quiz page with email score save.
5. Kit waitlist CTA.
6. Profile shell.
7. Temple guide template.
8. Community submission form.
9. Booklet reader.
10. Conversation surface placeholder.

This gives conversion now while keeping the full product visible.
