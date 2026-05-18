# UI Component and Style System

## 1. Design Goal

Khatakshetra should feel like:

> A temple archive, premium storybook, cultural game world, and sacred-object collection in one digital experience.

It must not feel like:

- a generic blog,
- a school worksheet site,
- a SaaS dashboard,
- a noisy kids app,
- a low-trust mythology content farm.

## 2. Visual Identity

### Core Mood

- premium,
- devotional,
- cinematic,
- manuscript-inspired,
- warm,
- alive,
- source-aware,
- playful where appropriate.

### Typography

Use the existing style:

- `Cinzel`: main epic headings, deity/story titles.
- `Cinzel Decorative`: sacred brand moments, cover titles, small ornamental labels.
- `Playfair Display`: emotional subheads, quotes, booklet chapter titles.
- `Crimson Text`: long-form reading, story body, source notes.

Rules:

- No fake "mythological" fonts.
- No negative letter spacing.
- Long reading text must remain comfortable.
- Devanagari/Telugu font stack must be chosen for readability, not ornament.

### Palette

Primary:

- deep temple black/brown: `#080300`
- antique gold: `#C8962C`
- bright gold: `#E8B94F`
- saffron: `#E07B1A`
- warm cream: `#F5E6C8`
- dim cream: `#BEA882`

Secondary:

- forest green,
- deep maroon,
- indigo,
- teal,
- lotus pink.

Rules:

- Use dark surfaces for cinematic immersion.
- Use ivory paper surfaces for booklets, talapatra, and reading inserts.
- Use gold sparingly as signal, not wallpaper.
- Avoid one-note palettes.

## 3. Motion Language

Motion should feel like:

- a book opening,
- a lamp flame,
- a temple bell vibration,
- a talapatra strip sliding,
- a constellation connecting,
- ink filling a drawing,
- quiz cards turning,
- a map route revealing.

Motion should not feel like:

- generic bouncy startup animation,
- random particles,
- heavy video background,
- motion that hides the CTA.

## 4. Core Components

### 4.1 Premium Hero Experience

Purpose: communicate value in one glance.

Elements:

- immersive animated scene,
- headline,
- subhead,
- primary CTA,
- secondary CTA,
- trust line,
- experience preview rail.

Variants:

- homepage hero,
- festival hero,
- story hero,
- temple hero,
- kit hero.

### 4.2 Experience Carousel

Purpose: show the website experience automatically without making users scroll.

Slides:

1. Cinematic story.
2. Hardbound digital booklet.
3. Talapatra wisdom card.
4. Drawing/coloring kit.
5. Quiz battle.
6. Temple guide.
7. Competition/community.
8. Kit waitlist.

Each slide should show:

- visual preview,
- one benefit line,
- one CTA.

Animation:

- 4-5 seconds per slide,
- pause on hover/touch,
- manual dots,
- reduced-motion fallback.

### 4.3 "I Want To..." Selector

Purpose: near-zero discovery friction.

Options:

- Learn a story.
- Understand a deity.
- Explore a temple.
- Play a quiz.
- Open a booklet.
- Start drawing.
- Join a challenge.
- Find a festival kit.

Component style:

- icon + short label,
- no long descriptions,
- quick route to relevant flow.

### 4.4 Story Card

Fields:

- title,
- one-line hook,
- source badge,
- entities,
- read/listen/play buttons.

Style:

- dark manuscript card or ivory page card depending on context,
- 8px radius max,
- gold hairline border.

### 4.5 Booklet Preview

Purpose: premium hardbound digital product.

Elements:

- cover,
- page spread,
- chapter title,
- audio button,
- unlock badge.

Animation:

- page turn,
- gold edge shimmer,
- cover opening.

### 4.6 Talapatra Card

Purpose: sacred-object layer.

Elements:

- Sanskrit/Devanagari or Telugu where relevant,
- transliteration,
- meaning,
- tiny icon,
- play pronunciation.

Style:

- palm-leaf shape,
- engraved look,
- warm bamboo/ivory texture,
- minimal text.

### 4.7 Drawing Kit Surface

Elements:

- tool palette,
- color swatches,
- fill/trace/decorate modes,
- download/save,
- submit to competition.

Style:

- functional, not decorative clutter,
- icons for tools,
- stable canvas dimensions,
- mobile-friendly.

### 4.8 Quiz Card

Elements:

- question,
- answer choices,
- progress,
- score,
- explanation,
- share result.

Modes:

- solo,
- family room,
- competition,
- leaderboard.

Style:

- card flip or answer glow,
- fast feedback,
- no childish confetti overload.

### 4.9 Temple Guide Card

Elements:

- temple name,
- deity,
- city/state,
- open/closed status if available,
- timing freshness,
- story CTA,
- how to reach CTA,
- local tips count.

Style:

- practical but still premium,
- temple image or motif,
- freshness badge is visible.

### 4.10 Community Contribution Card

Types:

- question,
- comment,
- drawing,
- temple tip,
- story request,
- competition submission.

Must show:

- moderation status when private,
- points earned,
- share/referral CTA.

### 4.11 Points and Leaderboard

Purpose: encourage useful contribution, not vanity spam.

Points for:

- quiz completion,
- high quiz score,
- verified temple tip,
- approved artwork,
- story question,
- referral,
- competition participation,
- event speaking/application.

Leaderboard types:

- weekly,
- festival,
- city,
- school/community,
- adults,
- kids with parent consent.

### 4.12 Profile Dashboard

Sections:

- unlocked booklets,
- drawing gallery,
- quiz scores,
- points,
- referrals,
- competition entries,
- temple tips,
- event/speaking opportunities,
- language preferences,
- kit waitlists.

Style:

- quiet and organized,
- less ornate than public pages,
- still uses the Khatakshetra palette.

## 5. Component States

Every interactive component needs:

- default,
- hover/focus,
- loading,
- locked,
- unlocked,
- completed,
- shared,
- error,
- empty.

Locked state should always show the value:

- "Unlock 5 more pages"
- "Save your score"
- "Submit to challenge"
- "Invite 2 friends"

## 6. Accessibility and Performance

- All motion must respect `prefers-reduced-motion`.
- Text must remain readable over animation.
- Mobile first-load must be fast.
- Hero animation should use CSS/JS and optimized images first, video only if compressed.
- Buttons must be large enough for mobile.
- Color contrast must be checked.

## 7. First Build Component Set

Build these first:

1. Hero experience carousel.
2. Primary CTA/email unlock modal.
3. "I want to..." selector.
4. Story card.
5. Booklet preview.
6. Drawing kit preview.
7. Quiz teaser.
8. Temple guide teaser.
9. Kit waitlist card.
10. Points/referral mini-card.

This will make the homepage feel like a premium product ecosystem on day one.
