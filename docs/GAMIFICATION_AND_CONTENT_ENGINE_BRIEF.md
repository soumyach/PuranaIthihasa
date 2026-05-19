# Khatakshetra Gamification and Content Engine Brief

## One-line Vision

Khatakshetra should become the most trusted and enjoyable digital home for Hindu stories, festivals, deities, temples, family learning, quizzes, coloring books, booklets, and premium cultural kits.

## What We Are Building

Khatakshetra is not just a story website. It is a cultural experience system with four connected layers:

1. Read and learn: stories, deity hubs, festival pages, temple guides, quick summaries, source notes, and booklets.
2. Play and practice: solo quizzes, family-room quizzes, printable board/card games, drawing/coloring, completion paths, and challenges.
3. Contribute and belong: temple tips, comments, questions, family submissions, local competitions, referrals, and community recognition.
4. Convert and monetize: email capture, kit waitlists, festival kit interest, digital unlocks, premium PDFs, competitions, and eventually physical Khatakshetra kits.

The dream outcome is not only "kids learn mythology." It is bigger:

- Adults and children rediscover stories together.
- Families understand the "why" behind festivals, gods, temples, rituals, and life lessons.
- Kids get enjoyable activities instead of passive reading.
- Adults get depth, meaning, and source humility.
- Families return because there is always a next unlock, festival, challenge, guide, or story path.
- The product eventually supports premium cultural kits, digital downloads, community events, and local competitions.

## Target Audiences

- Parents with children ages 5-12 who want culture to feel meaningful, not forced.
- Adults who want accessible but serious Hindu story learning.
- NRIs and Indian families who want cultural transmission at home.
- Grandparents who want to gift stories and activities.
- Schools, temples, Bala Vihar groups, Telugu/Hindi/English cultural groups.
- Temple travelers who want story plus practical travel guidance.

## Core Product Promise

Every important deity, story, festival, or temple should eventually have:

- Quick AEO answer.
- Cinematic adult story.
- Kids 5-8 story.
- Kids 9-12 story.
- Character dialogue/skit version.
- Descriptive article.
- Quiz.
- Family-room quiz.
- Coloring book or drawing kit.
- Premium booklet/PDF.
- Related deities, people, places, texts, festivals, temples, and activities.
- Source and variant notes.
- Signup, unlock, or contribution path.

## Success Criteria

### Acquisition

- Organic search impressions for deity, festival, story, and temple queries.
- AEO visibility for "who/what/why" answers.
- CTR from Google and social shares.
- New visitors from festival pages and temple guides.

### Activation

- Email signup rate from homepage and story pages.
- First action rate: quiz start, coloring page open, booklet open, temple guide view.
- Story-to-play conversion.
- Coloring page open-to-download conversion.

### Engagement

- Quiz completion rate.
- Family-room creation rate.
- Repeat visits per user within 7/30 days.
- Completion of deity/festival/story paths.
- Unlock completion rate.
- Contribution rate for temple tips, comments, questions, and submissions.

### Community

- Invite/referral conversion.
- Local/city/temple-group challenge participation.
- Helpful votes or moderation approvals on user tips.
- Number of active family groups or quiz rooms.

### Monetization

- Kit waitlist signup rate.
- Festival kit interest by SKU.
- Premium PDF/booklet interest.
- Event/competition participation.
- Email list growth before festival drops.

## Current Gamification Model

The current version implements a lightweight local progress model in the browser and prepares backend tables for production.

### Tracks

- Story Mastery: reading, quiz answers, quiz completion, booklet printing.
- Creative Practice: coloring page opens, artwork downloads, drawing-kit completion.
- Temple Seva: approved temple tips, current timing updates, food/local tips, accessibility notes.
- Community: family quiz rooms, referrals, helpful comments, event participation.

### Levels

1. Listener: starter story and solo quiz.
2. Seeker: first coloring page and progress ring.
3. Story Keeper: PDF booklet spread.
4. Family Champion: family-room challenge and share card.
5. Temple Friend: festival preview and temple contribution path.
6. Khatakshetra Contributor: leaderboard eligibility, event invites, and early kit access.

### Current XP Events

- Correct quiz answer: 10 XP.
- Solo quiz complete: 50 XP.
- Family room complete: 75 XP.
- Coloring page opened: 15 XP.
- Coloring download: 40 XP.
- Booklet print: 60 XP.
- Temple tip saved: 80 XP.
- Referral saved: 120 XP.

### Current Implementation Status

- Local browser profile exists in `site.js`.
- Solo quiz awards XP in `quiz-game.html`.
- Family-room quiz awards XP in `quiz-room.html`.
- Coloring open/download awards XP in `paint.html`.
- Games page renders current level/XP in `games.html`.
- Supabase schema now includes `user_progress`, `points_ledger`, `quiz_rooms`, and `quiz_room_results`.

## Gamification Concerns to Solve

The current model is functional but still too basic. It risks becoming points/badges/leaderboard theater unless we sharpen it.

The stronger direction should be:

### 1. Completion Rings

Each user should see partially complete paths:

- Complete Ramayana Starter: read story, play quiz, color one page, open booklet.
- Complete Ganesha Path: story, quiz, modak coloring page, obstacle card, kit interest.
- Complete Temple Friend Path: read temple story, save guide, add tip, invite family.

The psychological driver is closure: people want to finish visible incomplete sets.

### 2. Hyper-local Competition

Avoid only global leaderboards. Instead use winnable rooms:

- Family room.
- Cousins group.
- City league.
- School/class league.
- Temple group.
- Age-band festival challenge.
- Telugu/Hindi/English language cohort.

The win should feel possible.

### 3. Competence Feedback

Scores should signal real mastery, not activity.

Examples:

- Ramayana Listener -> Ramayana Explainer -> Ramayana Story Keeper.
- Deity Knowledge: Beginner, Intermediate, Confident.
- Temple Contributor quality score after approved tips.
- Quiz categories: Memory, Meaning, Source Awareness, Ritual Understanding.

### 4. Variable Reward

After completing an action, reveal a meaningful unlock:

- Talapatra card.
- Coloring page.
- Booklet spread.
- Festival challenge entry.
- Family share card.
- Kit early access.
- Rare story card.

This should not be random junk. The reward should deepen the experience.

### 5. Community Status Should Be Earned

Contribution points should require moderation/helpfulness, not just posting.

Good status examples:

- Temple Friend.
- Story Helper.
- Festival Captain.
- Local Guide.
- Family Quiz Host.
- Trusted Contributor.

Bad status examples:

- Empty badge for logging in.
- Global leaderboard for everyone.
- Streak pressure with no cultural meaning.

## Questions for Gamification Expert

1. What should the first 7-day loop be for a parent and child after signup?
2. What is the smallest meaningful completion path that creates pride and return behavior?
3. Should XP be global, track-based, or mostly path-based?
4. How should family-room multiplayer work for children, parents, and grandparents?
5. How should local leagues be structured so they feel winnable?
6. What unlocks are strong enough to motivate repeat engagement?
7. How do we avoid badge theater?
8. What should be public status vs private family progress?
9. How should referrals fit without cheapening the brand?
10. How should contribution quality be scored for temple tips and community answers?
11. What should be the engagement loop before festivals?
12. How do we design competition formats that are safe and respectful for kids?

## What Already Exists in the Repo

### Story Packs

Location: `content/story-packs/`

- `ramayana-starter.json`: Ramayana story, kids versions, art plates, 13 paintable pages, quiz mapping, booklet structure.
- `dasharatha-meets-shani.json`: Shani Dev story, kids versions, voiceover/dialogue/descriptive scripts, quiz mapping, booklet, talapatra cards.
- `ganesha-beginnings.json`: Ganesha story, kids versions, kit direction, quiz mapping, booklet, coloring prompts.
- `dashavatara.json`: Dashavatara story, kids versions, quiz mapping, booklet, coloring prompts, and ten avatar cards.

### Quizzes

Location: `content/quizzes.json`

Current quiz topics include:

- Rama Navami / Ramayana beginner.
- Shani Dev beginner.
- Ganesha beginner.
- Dashavatara beginner.
- Shiva beginner.
- Krishna beginner.
- Devi/Navratri beginner.
- Lakshmi/Diwali beginner.
- Saraswati beginner.
- Subrahmanya/Surya beginner.

Pages:

- Solo quiz: `quiz-game.html`.
- Family-room quiz: `quiz-room.html`.
- Quiz library: `games.html`.

### Coloring and Drawing

Real paintable Ramayana pages:

- `ChildrenBook/Cover.png`
- `ChildrenBook/Ayodhya kingdom.png`
- `ChildrenBook/Putrakameshti.png`
- `ChildrenBook/Rama's birth.png`
- `ChildrenBook/the four brothers.png`
- `ChildrenBook/Learning from the sage.png`
- `ChildrenBook/Young Sita.png`
- `ChildrenBook/Sita Swayamvar.png`
- `ChildrenBook/Marriage.png`
- `ChildrenBook/Happy family.png`
- `ChildrenBook/Kaikeyi's wish.png`
- `ChildrenBook/Rama's decision.png`
- `ChildrenBook/Exile.png`

Simple SVG coloring pages:

- `coloring/ganesha-doorway.svg`
- `coloring/ganesha-modak.svg`
- `coloring/ganesha-wisdom.svg`
- `coloring/shani-chariot.svg`
- `coloring/shani-dev.svg`
- `coloring/shani-patience-symbols.svg`
- `coloring/dashavatara-symbols.svg`
- `coloring/narasimha-prahlada.svg`
- `coloring/vamana-umbrella.svg`
- `coloring/ramayana-ayodhya.svg`
- `coloring/ramayana-swayamvar.svg`
- `coloring/ramayana-hanuman.svg`

Coloring book inventory:

- `content/coloring-books.json`

Pages:

- `coloring-book-ramayana.html`
- `drawing-kits.html`
- `paint.html`

### Booklets and PDFs

Booklet structures exist in:

- `content/story-packs/ramayana-starter.json`
- `content/story-packs/dasharatha-meets-shani.json`
- `content/story-packs/ganesha-beginnings.json`
- `content/story-packs/dashavatara.json`

Pages:

- `booklets.html`
- `storybook-ramayana.html`
- `booklet-ramayana-starter.html`
- `story-experience.html?pack=...`

Current state: HTML booklet views exist, print/save-as-PDF works through browser print. We have not yet generated final designed PDF files as static downloadable files.

### Deity Hubs

Location:

- `content/deity-experience-packs.json`
- `content/entities.json`

Current 16 deity packs:

- Vishnu
- Shiva
- Brahma
- Parvati
- Lakshmi
- Saraswati
- Ganesha
- Subrahmanya
- Hanuman
- Shani Dev
- Surya Dev
- Indra
- Varuna
- Kubera
- Durga
- Kali

Pages:

- `deities.html`
- `deity.html?slug=ganesha`
- `deity.html?slug=shani-dev`
- and so on.

### Festivals

Location:

- `content/festival-pages-2026.json`

Current festival hubs:

- Raksha Bandhan
- Krishna Janmashtami
- Ganesh Chaturthi
- Navratri
- Dussehra
- Diwali
- Guru Nanak Jayanti
- Maha Shivaratri
- Ratha Yatra
- Hanuman Jayanti

Page:

- `festivals.html`

### Temple Guides

Location:

- `content/temple-guides.json`

Current 10 guides:

- Tirumala Venkateswara Temple
- Kashi Vishwanath Temple
- Jagannath Temple, Puri
- Meenakshi Amman Temple
- Ramanathaswamy Temple
- Somnath Temple
- Mahakaleshwar Temple
- Siddhivinayak Temple
- Kamakhya Temple
- Sabarimala

Page:

- `temples.html`

### Content System Skill

Location:

- `skills/khatakshetra-content-system/SKILL.md`
- `skills/khatakshetra-content-system/references/content-quality.md`
- `skills/khatakshetra-content-system/references/gamification.md`
- `skills/khatakshetra-content-system/references/image-prompts.md`
- `skills/khatakshetra-content-system/scripts/audit_public_copy.py`

Purpose:

- Keep story/deity/festival/temple content consistent.
- Prevent internal strategy language from leaking into public pages.
- Define content unit requirements.
- Define image prompt quality rules.
- Define gamification principles.

## Were Images Generated?

No new AI image set was generated in the latest implementation pass.

What happened:

- Existing Ramayana coloring pages were restored and wired back into the site.
- Existing kit mockup images were used from `assets/`.
- Existing simple SVG coloring pages were wired into drawing/story pages.
- Prompt-ready coloring book manifests were created for Ganesha, Shani, Dashavatara, and core deities.

What is still needed:

- Generate premium deity hero images for all 16 deity hubs.
- Generate premium coloring-book line art for Ganesha, Shani, Dashavatara, and core deities.
- Generate booklet art plates for Ganesha, Shani, Dashavatara, Vishnu, Shiva, Devi, Lakshmi, Saraswati, Hanuman, Surya, etc.
- Replace rough SVGs with polished line-art pages or use them only as temporary developer assets.
- Export final PDF assets, not only HTML print views.

## Content Engine We Need Next

The next system should run locally first and publish curated JSON/assets into the repo.

### Engine Inputs

- Source URL or local PDF.
- Topic: story, deity, festival, temple, collection.
- Audience: adult, kids 5-8, kids 9-12.
- Language: English first, Telugu/Hindi later with contextual adaptation.
- Asset type: story, quiz, booklet, coloring prompt, hero image prompt, temple guide.

### Engine Stages

1. Source collection
   - Scrape/ingest public-domain or permitted sources.
   - Parse local PDFs where legally usable.
   - Store source metadata and rights status.

2. Story extraction
   - Extract people, places, deity names, story beats, rituals, values, and variant notes.
   - Do not publish exact-source claims without source location.

3. Narrative creation
   - Adult cinematic story.
   - Kids 5-8 story.
   - Kids 9-12 story.
   - Dialogue/skit script.
   - Descriptive article.
   - Voiceover script later.

4. Experience generation
   - Solo quiz.
   - Family-room quiz.
   - Booklet outline.
   - Talapatra cards.
   - Coloring book prompt.
   - Board/card game idea.
   - Completion path and unlock.

5. Visual production
   - Generate hero image prompts.
   - Generate coloring book prompts.
   - Generate final image assets.
   - QA for style, safety, readability, cultural respect, and text errors.

6. Publishing
   - Write story pack JSON.
   - Write entity/deity relationships.
   - Update sitemap.
   - Update public pages.
   - Run public-copy audit.
   - Run JSON validation.

### Proposed Engine Files

- `scripts/content-engine/ingest_source.js`
- `scripts/content-engine/generate_story_pack.js`
- `scripts/content-engine/generate_quiz.js`
- `scripts/content-engine/generate_coloring_prompts.js`
- `scripts/content-engine/generate_booklet_html.js`
- `scripts/content-engine/audit_content_pack.js`
- `scripts/content-engine/export_pdf.js`

### Source of Truth

The content source of truth should be structured JSON first:

- `content/story-packs/*.json`
- `content/entities.json`
- `content/deity-experience-packs.json`
- `content/quizzes.json`
- `content/coloring-books.json`
- `content/festival-pages-2026.json`
- `content/temple-guides.json`

Public pages should render from these files.

## Immediate Next Priorities

1. Build the local content engine scripts.
2. Generate final Ganesha, Shani, Dashavatara, and core deity coloring pages.
3. Expand each 16 deity hub from summary-level to full story-pack level.
4. Generate final PDF booklets for Ramayana Starter, Shani Dev, Ganesha, and Dashavatara.
5. Add account-backed Supabase save/merge instead of local-only progress.
6. Design the 7-day gamification loop with expert input.
7. Add moderation flow for temple tips and community content.
8. Add SEO/AEO detail pages for each deity, festival, temple, and story pack.

