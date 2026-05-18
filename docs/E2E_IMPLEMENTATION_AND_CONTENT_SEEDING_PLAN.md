# E2E Implementation and Content Seeding Plan

## 1. Correction

The website cannot be only a polished homepage. The homepage is useful only if it sits on top of a strong content engine and enough seed experiences for users to feel, "There is real value here."

The first implementation goal should be:

> Build a local content workbench where every story, deity, festival, text, and temple can become a premium page, booklet, PDF, audio, quiz, drawing kit, and community prompt.

This does not need to be deployed as a production engine now. It can run locally, generate static content/assets, and seed the public website.

## 2. MVP Success Definition

The MVP is successful if:

1. Users sign up for a free story/drawing/booklet unlock.
2. Users express interest in physical festival kits.
3. Users can immediately consume real premium content after signup.
4. We can publish new content from structured data without hand-building every page.
5. We have enough seed content to look credible.

Primary KPI:

- Visitor to email unlock conversion.

Secondary KPIs:

- Kit waitlist clicks.
- Quiz starts/completions.
- Drawing kit starts/downloads.
- Booklet/PDF downloads.
- Temple guide interest.
- Referral/share clicks.

## 3. Required Content Pack Structure

Every story/content item should generate a full pack:

1. Normal page
   - quick answer,
   - summary,
   - source-aware story,
   - related entities,
   - related temples/festivals.

2. Premium storybook
   - hardbound digital reader,
   - page-turn layout,
   - art spreads,
   - talapatra inserts.

3. Downloadable PDF
   - print-ready storybook PDF,
   - family/teacher use,
   - shareable after signup.

4. Audio
   - voiceover script,
   - SSML,
   - pronunciation glossary,
   - chapter markers.

5. Script variants
   - voiceover script,
   - movie/skit dialogue script,
   - descriptive narration.

6. Drawing kit
   - coloring pages,
   - trace/decorate prompts,
   - downloadable originals,
   - submit-to-challenge path.

7. Quiz/game
   - beginner/intermediate/advanced,
   - explanations,
   - score save,
   - share result.

8. SEO/AEO
   - meta title/description,
   - FAQ,
   - direct answer,
   - schema.org JSON-LD.

9. Community
   - questions,
   - comments,
   - contribution prompt,
   - points/leaderboard hook.

## 4. Seed Content Needed Before Serious Launch

### Story Pages: First 25

Ramayana:

1. Rama's birth
2. Vishwamitra's request
3. Tataka Vadha
4. Ahalya liberation
5. Sita Swayamvar
6. Rama's exile
7. Bharata's vow
8. Shabari
9. Hanuman meets Rama
10. Sundara Kanda opening
11. Hanuman finds Sita
12. Rama Setu
13. Ravana's fall
14. Return to Ayodhya

Shani / Purana:

15. Birth of Shani
16. Dasharatha meets Shani
17. Shani and Pippalada

Ganesha:

18. Why Ganesha has an elephant head
19. Ganesha and the fruit of wisdom
20. Ganesha as Vighnaharta

Vishnu / Dashavatara:

21. Matsya
22. Kurma
23. Varaha
24. Narasimha
25. Vamana

### Hub Pages: First 12

1. Ramayana
2. Mahabharata
3. Bhagavad Gita
4. Vishnu
5. Shiva
6. Ganesha / Vinayaka
7. Hanuman
8. Shani
9. Surya
10. Dashavatara
11. Ganesh Chaturthi
12. Rama Navami

### Festival Pages: First 10

1. Ganesh Chaturthi
2. Janmashtami
3. Rama Navami
4. Maha Shivaratri
5. Hanuman Jayanti
6. Navaratri
7. Diwali
8. Rath Yatra
9. Raksha Bandhan
10. Makar Sankranti / Pongal

### Temple Pages: First 10

Choose one city cluster plus a few pan-India anchors.

Recommended first city cluster: Hyderabad, because it can validate temple guide interest quickly.

Hyderabad:

1. Birla Mandir
2. Chilkur Balaji Temple
3. Peddamma Temple
4. Jagannath Temple Hyderabad
5. Karmanghat Hanuman Temple
6. Ujjaini Mahakali Temple

Pan-India anchors:

7. Tirumala Venkateswara Temple
8. Kashi Vishwanath Temple
9. Jagannath Temple Puri
10. Siddhivinayak Temple Mumbai

Each temple page must include:

- story/sthala purana,
- deity,
- timings,
- how to reach,
- what not to miss,
- food/prasadam/local tips,
- source links,
- last verified date,
- user contribution prompt.

## 5. Build Architecture

### Keep Static, Add Local Generator

Do not hand-code every page. Also do not deploy a complex engine yet.

The local generator can live in the repo, run on demand, and output static pages/assets.

Add:

```text
scripts/
  build-site.js
templates/
  story-page.html
  hub-page.html
  booklet-page.html
  quiz-page.html
  temple-page.html
  kit-page.html
public/generated/
  stories/
  hubs/
  booklets/
  quizzes/
  temples/
  pdf/
```

Input:

- `content/story-packs/*.json`
- `content/entities.json`
- `content/collections.json`
- `content/festivals.json`
- `content/temple-priorities.json`

Output:

- static pages,
- sitemap,
- JSON-LD,
- printable booklet HTML,
- downloadable PDFs.

## 6. PDF Download Plan

### Version 1

Create printable HTML booklets:

```text
/booklets/dasharatha-meets-shani.html
/booklets/rama-birth.html
```

Use print CSS:

- A5 booklet style,
- cover page,
- chapter pages,
- art pages,
- talapatra pages,
- activity page,
- source note page.

Users can print/save as PDF immediately.

### Version 2

Generate PDFs during build:

```text
public/generated/pdf/dasharatha-meets-shani.pdf
public/generated/pdf/rama-birth.pdf
```

Recommended implementation:

- Playwright/Chromium or Puppeteer in build script.
- Same HTML source as booklet reader.
- Print CSS controls the PDF.

### Version 3

Personalized PDFs:

- child/family name,
- certificate,
- score,
- challenge entry,
- unlocked pack.

Generate via serverless/job after signup.

## 7. Implementation Task List

### Phase 0: Repo Hygiene

- Confirm repo access/push path.
- Decide whether current ZIP folder becomes repo root or copied into a fresh clone.
- Keep current visual style.
- Preserve Rama Navami reader as an existing page.

### Phase 1: Content System Foundation

- Finalize `story-pack` schema.
- Add `hub` schema.
- Add `temple-profile` schema.
- Add `quiz` schema.
- Add `booklet` fields.
- Add `pdf` export fields.
- Add status fields: draft, source-reviewed, design-reviewed, published.

### Phase 2: Page Generator

- Create static generator.
- Generate story pages.
- Generate hub pages.
- Generate temple pages.
- Generate booklet pages.
- Generate sitemap.
- Keep `robots.txt` active.

### Phase 3: First Real Content Pack

Build one complete pack end-to-end:

- `Dasharatha Meets Shani` or `Rama Birth`.
- Normal page.
- Booklet reader.
- PDF download.
- Quiz.
- Drawing kit.
- Audio script.
- Signup unlock CTA.

Acceptance criteria:

- user can read,
- user can open booklet,
- user can download/print PDF,
- user can take quiz,
- user can sign up,
- user can join related kit/waitlist.

### Phase 4: Seed Batch

Create:

- 10 story packs,
- 5 hub pages,
- 3 festival hubs,
- 5 temple pages,
- 2 quizzes,
- 2 booklet/PDF downloads,
- 1 drawing kit.

### Phase 5: Conversion and Measurement

Implement:

- email capture tags,
- signup source tracking,
- kit waitlist tags,
- quiz start/completion events,
- PDF download event,
- drawing kit unlock event,
- referral/share click event.

### Phase 6: Profile and Community

Implement:

- lightweight profile,
- saved unlocks,
- quiz score storage,
- contribution form,
- comments/questions,
- moderation status,
- points ledger,
- leaderboard.

### Phase 7: Kit Demand Validation

Implement:

- kit waitlist pages,
- "which kit do you want first?" survey,
- preorder interest,
- price sensitivity test,
- referral unlock for kit discount/early access.

## 8. 100x Experience Requirements

The experience becomes 100x only if:

- content is visually beautiful,
- each story creates multiple experiences,
- every page has a next action,
- every unlock gives immediate value,
- every user action earns progress,
- every contribution can become community value,
- downloadable PDFs make it useful offline,
- temple pages solve practical travel questions,
- the product feels alive, not like a static archive.

## 9. What To Build Next

Do not add more random homepage sections yet.

Next exact sequence:

1. Create the visible website structure with placeholder pages.
2. Keep Ramayana as the first real content experience.
3. Create local generator skeleton.
4. Generate one story page from `dasharatha-meets-shani.json`.
5. Generate one booklet page from the same story pack.
6. Add print/PDF CSS.
7. Add download CTA.
8. Add quiz page.
9. Wire email capture around unlocks.
10. Then return to homepage and link to the real generated experience.

This makes the homepage promise true.
