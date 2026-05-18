# Implementation Backlog

## Now: Make the Website Shape Visible

### 1. Placeholder Site Structure

- [ ] Homepage with animated experience carousel.
- [ ] Stories page with Ramayana as the live experience and placeholders for upcoming hubs.
- [ ] Deities page with hub placeholders.
- [ ] Festivals page with 2026 campaign calendar.
- [ ] Temples page with guide placeholders.
- [ ] Games page with quiz/multiplayer/community mechanics preview.
- [ ] Booklets page with PDF/download promise.
- [ ] Drawing kits page with unlock promise.
- [ ] Community page with contribution/points/challenge promise.
- [ ] Kits page with waitlist CTAs.

## Next: Make the Homepage Promise True

### 2. Local Static Generator

- [ ] Create `scripts/build-site.js`.
- [ ] Read JSON from `content/story-packs`, `content/collections`, `content/festivals`, and `content/temple-priorities`.
- [ ] Generate `/generated/stories/:slug.html`.
- [ ] Generate `/generated/booklets/:slug.html`.
- [ ] Generate `/generated/quizzes/:slug.html`.
- [ ] Generate `/generated/temples/:slug.html`.
- [ ] Generate `sitemap.xml`.

### 3. First Complete Story Pack

- [ ] Use `dasharatha-meets-shani.json`.
- [ ] Generate normal story page.
- [ ] Generate premium booklet reader.
- [ ] Add print/PDF CSS.
- [ ] Add downloadable/printable PDF path.
- [ ] Add quiz link.
- [ ] Add drawing kit placeholders.
- [ ] Add email unlock CTA.

### 4. Signup and Measurement

- [ ] Add `starter_story_kit` capture.
- [ ] Add `pdf_download` event.
- [ ] Add `booklet_open` event.
- [ ] Add `quiz_start` and `quiz_complete` events.
- [ ] Add `kit_waitlist` event.
- [ ] Add referral/share click tracking.

### 5. Seed Content Batch 1

- [ ] Rama birth full story pack.
- [ ] Sita Swayamvar full story pack.
- [ ] Hanuman meets Rama full story pack.
- [ ] Birth of Shani full story pack.
- [ ] Why Ganesha has an elephant head full story pack.
- [ ] Dashavatara hub.
- [ ] Ganesha hub.
- [ ] Shani hub.
- [ ] Ganesh Chaturthi hub.
- [ ] Hyderabad temple cluster.

### 6. Homepage Finalization

- [ ] Replace placeholder links with generated pages.
- [ ] Make hero carousel link to real experiences.
- [ ] Add free starter kit unlock flow.
- [ ] Add kit waitlist survey.
- [ ] Add "which content should we build next?" prompt.

## Next: Community and Product Validation

- [ ] Profile shell.
- [ ] Saved unlocks.
- [ ] Quiz score save.
- [ ] Contribution form.
- [ ] Comment/question form.
- [ ] Moderation queue.
- [ ] Points ledger.
- [ ] Leaderboard.
- [ ] Referral unlock.
- [ ] Kit interest survey.

## Later: Scale Engine

- [ ] Source ingestion workflow.
- [ ] Contextual Hindi/Telugu layer.
- [ ] Temple freshness checker.
- [ ] Audio generation pipeline.
- [ ] Image generation/review pipeline.
- [ ] Personalized PDFs.
- [ ] Multiplayer quiz rooms.
