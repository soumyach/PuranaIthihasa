# Khatakshetra Site As-Is State

Last updated: 2026-05-19

## Plain-English Summary

The site currently has a working static experience layer with:

- A conversion-focused homepage.
- A story library.
- A Ramayana starter story experience.
- A Shani Dev story experience.
- Ganesha and Dashavatara story packs.
- Solo quizzes.
- Pass-the-device family quiz rooms.
- A digital painting tool.
- A real Ramayana coloring book using existing paintable images.
- Basic deity hubs.
- Festival hub cards.
- Temple guide cards.
- Kit landing pages.
- Community and gamification direction.

But the site is not yet a fully polished product experience. The content exists in different maturity levels:

- Ramayana is the most complete.
- Shani has strong narrative content but less finished visual/booklet output.
- Ganesha and Dashavatara have structured story packs but need final art and designed PDFs.
- Deity, festival, and temple pages are mostly structured hub cards, not deep final content pages yet.
- Gamification exists as a lightweight local-browser prototype, not account-backed production behavior yet.

## Is Ramayana Navigable as a Journey?

Short answer: partially.

Ramayana currently works as a navigable experience, but not yet as the ideal guided journey.

### What Works Now

A visitor can move through:

1. `stories.html`
   - Finds the Ramayana Starter pack.
2. `story-experience.html?pack=ramayana-starter`
   - Tabbed experience with:
     - Story
     - Kids version
     - References and related people/places/texts
     - Quiz
     - Booklet/PDF mode
     - Coloring book
     - Games
3. `quiz-game.html?quiz=rama-navami-beginner`
   - Solo Ramayana quiz with XP.
4. `quiz-room.html?quiz=rama-navami-beginner`
   - Family-room pass-the-device quiz with XP.
5. `coloring-book-ramayana.html`
   - 13 real paintable Ramayana coloring pages.
6. `paint.html?image=...`
   - Digital coloring canvas for each page.
7. `storybook-ramayana.html`
   - Premium storybook-style page.
8. `booklet-ramayana-starter.html`
   - Print-ready booklet preview.

### What Is Missing

Ramayana is not yet a smooth chapter journey like:

`Start -> Chapter 1 -> Quiz -> Coloring -> Unlock Chapter 2 -> Booklet -> Family Room -> Completion Ring`.

It needs:

- A visible journey map/progress rail.
- Chapter-by-chapter next buttons.
- Completion state for each chapter.
- One canonical Ramayana journey page instead of several separate entry points.
- Better “unlock next” logic.
- A stronger emotional landing hook before the content.
- Cleaner premium booklet/PDF export.

## Current Public Pages

### Home

File: `index.html`

Purpose:

- Main conversion page.
- Shows the Khatakshetra offer: stories, booklets, drawing kits, quizzes, temples, festivals, kits.
- Has email capture CTAs.

Current maturity:

- Good structure.
- Needs stronger hero and animation polish.
- Needs clearer product demonstration of actual experiences.

### Stories

File: `stories.html`

Purpose:

- Story library and launch pack discovery.
- Links to Ramayana, Shani, Ganesha, Dashavatara.
- Renders story cards from `content/stories.json`.

Current maturity:

- Usable library page.
- Needs deeper story catalog and better filtering by deity/festival/source.

### Story Experience

File: `story-experience.html`

Purpose:

- Generic story pack renderer.
- Supports story, kids mode, references, quiz, booklet, coloring, and games.

Current packs:

- `ramayana-starter`
- `dasharatha-meets-shani`
- `ganesha-beginnings`
- `dashavatara`

Current maturity:

- This is the strongest reusable experience shell.
- Needs better UX design and more guided journey logic.

### Ramayana Storybook

File: `storybook-ramayana.html`

Purpose:

- Premium printable storybook style for Ramayana.

Current maturity:

- Useful proof of direction.
- Needs final editorial design and true PDF export.

### Ramayana Booklet

File: `booklet-ramayana-starter.html`

Purpose:

- Print-ready booklet preview.

Current maturity:

- HTML print view exists.
- Not yet a final downloadable designed PDF file.

### Ramayana Coloring Book

File: `coloring-book-ramayana.html`

Purpose:

- Real paintable Ramayana coloring book.
- Uses existing `ChildrenBook/` images.

Current assets:

- Cover
- Ayodhya kingdom
- Putrakameshti
- Rama's birth
- The four brothers
- Learning from the sage
- Young Sita
- Sita Swayamvar
- Marriage
- Happy family
- Kaikeyi's wish
- Rama's decision
- Exile

Current maturity:

- Functional.
- This is the most real coloring-book experience currently.

### Paint Tool

File: `paint.html`

Purpose:

- Opens an image and lets the user paint over it digitally.
- Supports download.
- Awards local XP for open/download.

Current maturity:

- Functional basic digital coloring.
- Needs better fill tools, undo, eraser quality, brush UX, mobile polish, and saved gallery.

### Drawing Kits

File: `drawing-kits.html`

Purpose:

- Lists coloring/drawing collections.
- Pulls pages from story packs.
- Links paintable files into the paint tool.

Current maturity:

- Useful index.
- Needs high-quality generated art for non-Ramayana collections.

### Games

File: `games.html`

Purpose:

- Quiz library.
- Topic filters.
- Board-game idea cards.
- Shows local XP/level progress.

Current maturity:

- Functional quiz launcher.
- Needs real board-game downloads, richer multiplayer, room codes, sharing, and account-backed progress.

### Solo Quiz

File: `quiz-game.html`

Purpose:

- Plays one quiz from `content/quizzes.json`.
- Awards local XP.

Current maturity:

- Functional.
- Needs better UX, answer review, progress map, rewards, share cards.

### Family Quiz Room

File: `quiz-room.html`

Purpose:

- Pass-the-device multiplayer quiz.
- Multiple named players on one device.
- Awards local XP.

Current maturity:

- Functional but basic.
- Not true online multiplayer yet.
- Needs room codes, remote players, account association, leaderboards, and family history.

### Deities

File: `deities.html`

Purpose:

- Lists deity hubs and structured deity packs.

Current maturity:

- Good inventory.
- Needs richer visual design and deeper content per deity.

### Deity Detail

File: `deity.html?slug=...`

Purpose:

- Generic deity hub page.
- Shows quick summary, story path, quiz links, coloring/booklet direction, and relationships.

Current maturity:

- Functional dynamic hub.
- Currently shallow for many deities because full story/booklet/coloring assets are not complete.

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

### Shani Dev Story

File: `story-shani-dev.html`

Purpose:

- Dedicated Shani Dev story page.
- Uses `content/story-packs/dasharatha-meets-shani.json`.

Current maturity:

- Stronger content than design.
- Should eventually merge into or redirect toward the generic story-experience shell.

### Festivals

File: `festivals.html`

Purpose:

- Renders 2026 festival cards from `content/festival-pages-2026.json`.
- Links quiz/family room/kit interest.

Current maturity:

- Functional hub cards.
- Needs individual festival detail pages.

Current festival cards:

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

### Temple Guides

File: `temples.html`

Purpose:

- Renders temple guide cards from `content/temple-guides.json`.
- Includes story, how to reach, what not to miss, food nearby, and tip CTA.

Current maturity:

- Useful initial structure.
- Not yet full city/state temple guide product.
- Needs individual temple pages, current timings, source links, map links, reviews/vlog summaries, and moderation.

Current temple guides:

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

### Booklets

File: `booklets.html`

Purpose:

- Booklet shelf.
- Links Ramayana storybook/coloring book and story experiences.

Current maturity:

- Good index.
- Needs actual exported PDF files and polished booklet templates.

### Community

File: `community.html`

Purpose:

- Explains community direction: questions, temple tips, artwork, competitions, referrals, points, events.

Current maturity:

- Concept page.
- Needs real auth, comments, moderation, submissions, profile, and leaderboards.

### Kits

File: `kits.html`

Purpose:

- Khatakshetra physical festival kit landing page.
- Ganesh Chaturthi, Rath Yatra, Raksha Bandhan + Janmashtami direction.

Current maturity:

- Strong concept.
- Needs commerce/waitlist backend, SKU details, pricing, fulfillment readiness.

### Rama Navami Reader

File: `rama-navami-reader.html`

Purpose:

- Older standalone high-design Rama Navami reader page.

Current maturity:

- Rich standalone page.
- Needs alignment with current story engine and navigation.

## Content Files

### Story Packs

Location: `content/story-packs/`

- `ramayana-starter.json`: most complete. Has adult/kids stories, art plates, 13 paintable pages, quiz mapping, booklet structure.
- `dasharatha-meets-shani.json`: strong narrative. Has adult/kids stories, voiceover, dialogue, descriptive script, quiz mapping, talapatra cards, coloring prompts.
- `ganesha-beginnings.json`: structured story pack. Needs final images and PDF.
- `dashavatara.json`: structured story pack plus ten avatar cards. Needs final images and PDF.

### Quizzes

Location: `content/quizzes.json`

Current count: 10 quizzes.

### Deity Packs

Location: `content/deity-experience-packs.json`

Current count: 16 deity packs.

Current maturity:

- Summary-level content, relationships, quiz mapping, coloring/booklet direction.
- Not yet full story-pack depth for every deity.

### Coloring Books

Location: `content/coloring-books.json`

Current collections:

- Ramayana Starter: available with real images.
- Ganesha Beginnings: prompt-ready.
- Dashavatara: prompt-ready.
- Shani Dev: prompt-ready.
- Core Deity Symbols: prompt-ready.

Important truth:

- Only Ramayana has a polished real coloring-book asset set.
- Other coloring collections are not final production-quality images yet.

### Festival Pages

Location: `content/festival-pages-2026.json`

Current count: 10.

Current maturity:

- Good structured cards.
- Needs full pages and deeper SEO/AEO content.

### Temple Guides

Location: `content/temple-guides.json`

Current count: 10.

Current maturity:

- Useful first cards.
- Needs full pages, verified practical data, map links, source links, reviews/vlog summaries.

### Gamification

Location: `content/gamification.json`

Current maturity:

- Good first model.
- Needs expert review.
- Needs account-backed implementation.

### Content Engine Skill

Location: `skills/khatakshetra-content-system/`

Purpose:

- Guides future content creation.
- Defines content unit structure.
- Defines public copy audit.
- Defines image prompt and gamification direction.

Current maturity:

- Useful operating manual.
- Not yet a full automated content engine.

## Current Image State

### Real Images Available

Ramayana coloring images:

- `ChildrenBook/*.png`

Kit/product images:

- `assets/khatakshetra-ganesh-kit.png`
- `assets/khatakshetra-rath-kit.png`
- `assets/khatakshetra-raksha-janmashtami-kit.png`

Other assets:

- `assets/shani-dev-character.png`
- `assets/dashavatara-symbol-wheel.svg`

Simple SVG coloring pages:

- `coloring/*.svg`

### Not Yet Done

No new full premium image generation batch has been completed for:

- 16 deity hero images.
- Final Ganesha coloring book.
- Final Shani coloring book.
- Final Dashavatara coloring book.
- Core deity symbol coloring book.
- Temple guide images.
- Final booklet art plates.

## Current Backend State

### What Exists

Supabase schema has tables for:

- Users
- Email capture
- Events
- Sources
- Source sections
- Stories
- Quizzes
- Quiz attempts
- User progress
- Points ledger
- Quiz rooms
- Quiz room results
- Unlocks
- Referrals
- Competitions
- Submissions
- Products
- Temple profiles
- Temple content sources
- Comments
- User tips

### What Is Not Yet Wired

- Real Supabase auth.
- Real email persistence from all CTAs.
- Production user profile.
- Saved quiz attempts.
- Saved family room history.
- Saved artwork gallery.
- Moderated community.
- Temple tip approval workflow.

## Navigation Reality

The site currently works as a network of pages, not yet a single cohesive product journey.

Current navigation pattern:

- Home -> Stories / Play / Drawing / Booklets / Deities / Temples / Festivals / Kits.
- Story pages link to quiz, coloring, booklet.
- Quiz pages link back to story.
- Coloring pages link to paint tool.
- Deity pages link to story/quiz/drawing.

Needed navigation upgrade:

- A unified journey shell for each major content path.
- Progress-aware “continue” CTAs.
- Clear “next best action” on every page.
- Completion rings.
- Unlock reveals.
- Account/profile menu.
- Better breadcrumbs.
- Related content carousels.

## Biggest Gaps

1. Ramayana needs a true guided journey, not only tabs and linked pages.
2. Non-Ramayana visual assets are not production quality yet.
3. PDFs are HTML print views, not final exported files.
4. Deity pages are shallow compared to the ambition.
5. Festival and temple pages are hub cards, not full SEO/AEO pages.
6. Gamification is local-only and needs real account backing.
7. Community is concept-level.
8. Content engine is defined as a skill/manual but not implemented as runnable scripts yet.
9. Homepage still needs stronger emotional hook and product demonstration.
10. Search indexing needs ongoing work beyond robots/sitemap.

## Recommended Next Build Step

Build a real Ramayana Journey page first:

`ramayana-journey.html`

It should show:

- Chapter path with 5-8 scenes.
- For each scene: read, listen later, quiz, color, reflect.
- Progress ring.
- Unlock next chapter.
- Family-room challenge.
- PDF booklet completion.
- CTA to save progress by email.

Why this first:

- Ramayana already has the strongest content and images.
- It will become the template for Shani, Ganesha, Dashavatara, and deity hubs.
- It will make the site feel like an actual product instead of a collection of pages.

## Recommended Content Engine Step

Build `scripts/content-engine/` next with:

- `audit_content_inventory.js`
- `generate_story_pack.js`
- `generate_quiz.js`
- `generate_booklet_html.js`
- `generate_coloring_manifest.js`
- `export_pdf.js`

The engine should write to the structured content files, and the pages should render from those files.

## Full Structured Content Register

This section is the canonical as-is inventory for the current repo. It should be updated whenever a story, deity/god hub, festival, quiz, temple guide, coloring book, booklet, or content-engine output changes.

### Story Pack Register

| Pack | File | Public entry | Current content | Current gaps |
|---|---|---|---|---|
| Ramayana Starter | `content/story-packs/ramayana-starter.json` | `story-experience.html?pack=ramayana-starter` | Adult story, kids versions, references, related people/places/texts, quiz mapping, booklet structure, art plates, 13 real paintable pages | Needs guided chapter journey, final PDF export, stronger unlock flow |
| Shani Dev / Dasharatha Meets Shani | `content/story-packs/dasharatha-meets-shani.json` | `story-experience.html?pack=dasharatha-meets-shani`, `story-shani-dev.html` | Strong adult story, kids versions, voiceover script, dialogue script, descriptive script, quiz mapping, booklet, talapatra cards, 3 coloring SVGs | Needs final source verification, premium visual set, final PDF export |
| Ganesha Beginnings | `content/story-packs/ganesha-beginnings.json` | `story-experience.html?pack=ganesha-beginnings` | Adult story, kids versions, quiz mapping, Ganesh Chaturthi kit link, booklet structure, talapatra cards, 3 coloring SVGs/prompts | Needs final generated coloring book, final story art, designed PDF |
| Dashavatara | `content/story-packs/dashavatara.json` | `story-experience.html?pack=dashavatara` | Adult story, kids versions, quiz mapping, booklet structure, talapatra cards, 10 avatar cards, 3 coloring SVGs/prompts | Needs all 10 avatar story pages, final coloring book, final PDF |

### God / Deity Hub Register

Location: `content/deity-experience-packs.json`

Page pattern: `deity.html?slug={slug}`

| Deity / Hub | Slug | Story status | Quiz | Coloring / drawing | Booklet path | Relationships captured | Current visual status |
|---|---|---|---|---|---|---|---|
| Vishnu | `vishnu` | Summary-level | `dashavatara-beginner` | Dashavatara coloring | Dashavatara: Ten Ways Vishnu Restores Balance | Lakshmi, Rama, Krishna, Dashavatara | Prompted only; needs final Vishnu hero and symbol art |
| Shiva | `shiva` | Summary-level | `shiva-beginner` | Core deity symbols | Shiva: Transformation and Grace | Parvati, Ganesha, Subrahmanya, Kailasa | Prompted only; needs final Shiva art |
| Brahma | `brahma` | Summary-level | `saraswati-beginner` | Core deity symbols | Brahma and the Four Directions | Saraswati, Vedas, Creation cycles | Prompted only; needs final Brahma art |
| Parvati | `parvati` | Summary-level | `devi-navratri-beginner` | Ganesha beginnings | Parvati: Strength with Tenderness | Shiva, Ganesha, Subrahmanya, Durga | Prompted only; needs final Parvati art |
| Lakshmi | `lakshmi` | Summary-level | `lakshmi-diwali-beginner` | Core deity symbols | Lakshmi: The Light of Abundance | Vishnu, Diwali, Samudra Manthana | Prompted only; needs final Lakshmi art |
| Saraswati | `saraswati` | Summary-level | `saraswati-beginner` | Core deity symbols | Saraswati: The Blessing of Learning | Brahma, Vasant Panchami, Veena | Prompted only; needs final Saraswati art |
| Ganesha | `ganesha` | Full starter pack exists | `ganesha-beginner` | Ganesha coloring SVGs/prompts | Ganesha: Before Every Beginning | Parvati, Shiva, Subrahmanya, Mouse vahana | Kit image exists; final coloring/story art still needed |
| Subrahmanya | `subrahmanya` | Summary-level | `subrahmanya-surya-beginner` | Core deity symbols | Subrahmanya: The Vel of Courage | Shiva, Parvati, Ganesha, Skanda Sashti | Prompted only; needs final Subrahmanya art |
| Hanuman | `hanuman` | Connected to Ramayana pack | `rama-navami-beginner` | Ramayana coloring | Hanuman: Strength That Serves | Rama, Sita, Sundara Kanda, Kishkindha | Some Ramayana art exists; needs Hanuman-specific set |
| Shani Dev | `shani-dev` | Full starter pack exists | `shani-dev-beginner` | Shani coloring SVGs/prompts | Shani Dev: The Necessary Teacher | Surya, Chhaya, Dasharatha, Saturday worship | Character image exists; final booklet/coloring art needed |
| Surya Dev | `surya-dev` | Summary-level | `subrahmanya-surya-beginner` | Core deity symbols | Surya: The Chariot of Light | Shani, Chhaya, Sanjna, Ratha Saptami | Prompted only; needs final Surya art |
| Indra | `indra` | Summary-level | `devi-navratri-beginner` | Core deity symbols | Indra: Power and Responsibility | Devas, Govardhana, Varuna, Vritra | Prompted only; needs final Indra art |
| Varuna | `varuna` | Summary-level | `subrahmanya-surya-beginner` | Core deity symbols | Varuna: Waters and Cosmic Order | Ocean, Rama sea prayer, Indra | Prompted only; needs final Varuna art |
| Kubera | `kubera` | Summary-level | `lakshmi-diwali-beginner` | Core deity symbols | Kubera: Wealth with Responsibility | Lakshmi, Dhanteras, Alakapuri, Ravana | Prompted only; needs final Kubera art |
| Durga | `durga` | Summary-level | `devi-navratri-beginner` | Core deity symbols | Durga: Courage Across Nine Nights | Parvati, Navratri, Mahishasura, Devi | Prompted only; needs final Durga art |
| Kali | `kali` | Summary-level | `devi-navratri-beginner` | Core deity symbols | Kali: Fierce Compassion | Parvati, Dasa Mahavidya, Time, Transformation | Prompted only; needs final Kali art |

Important: the 16 deity hubs are captured structurally, but most are not yet deep content pages. The next step is to generate one full story pack per deity or deity collection.

### Temple Guide Register

Location: `content/temple-guides.json`

Page: `temples.html`

| Temple | City / State | Primary deity | Story captured | How-to-reach captured | What-not-to-miss captured | Food nearby captured | Current gaps |
|---|---|---|---|---|---|---|---|
| Tirumala Venkateswara Temple | Tirupati, Andhra Pradesh | Venkateswara / Vishnu | Yes | Yes | Suprabhatam tradition, Laddu prasadam, Hill route atmosphere | Temple prasadam, Tirupati vegetarian meals | Needs timings, official links, darshan rules, map, source verification |
| Kashi Vishwanath Temple | Varanasi, Uttar Pradesh | Shiva | Yes | Yes | Ganga darshan, Evening aarti nearby, Old city walk | Kachori sabzi, Banarasi sweets, Lassi | Needs timings, entry gates, official links, map, source verification |
| Jagannath Temple | Puri, Odisha | Jagannath / Krishna | Yes | Yes | Mahaprasad, Rath Yatra context, Puri beach sunrise | Mahaprasad at Ananda Bazaar, Odia vegetarian food | Needs timings, access rules, official links, map, source verification |
| Meenakshi Amman Temple | Madurai, Tamil Nadu | Meenakshi / Parvati | Yes | Yes | Gopuram details, Thousand-pillar hall, Evening rituals | Madurai idli, Jigarthanda, Temple-street vegetarian meals | Needs timings, official links, ritual schedule, map, source verification |
| Ramanathaswamy Temple | Rameswaram, Tamil Nadu | Shiva | Yes | Yes | Temple corridors, Sacred wells, Dhanushkodi trip | South Indian vegetarian meals, Local tiffin | Needs timings, ritual process, official links, map, source verification |
| Somnath Temple | Somnath, Gujarat | Shiva | Yes | Yes | Sea-facing temple view, Evening light and sound show, Prabhas Patan context | Gujarati thali, Temple-town vegetarian meals | Needs timings, official links, map, source verification |
| Mahakaleshwar Temple | Ujjain, Madhya Pradesh | Shiva | Yes | Yes | Bhasma aarti booking rules, Mahakal corridor, Shipra river | Poha-jalebi, Ujjain snacks, Vegetarian thali | Needs current booking process, official links, map, source verification |
| Siddhivinayak Temple | Mumbai, Maharashtra | Ganesha | Yes | Yes | Tuesday darshan rhythm, Modak offering context, Prabhadevi area | Mumbai snacks, Vegetarian restaurants nearby | Needs timings, queue details, official links, map, source verification |
| Kamakhya Temple | Guwahati, Assam | Kamakhya / Devi | Yes | Yes | Nilachal Hill view, Ambubachi context, Shakti Peetha story | Assamese vegetarian options, Temple-area meals | Needs timings, ritual guidance, official links, map, source verification |
| Sabarimala | Pathanamthitta, Kerala | Ayyappa | Yes | Yes | Vrata discipline, Forest pilgrimage context, Makara season rules | Pilgrim annadanam where available, Kerala vegetarian meals en route | Needs seasonal rules, official links, route data, source verification |

Important: temple details are captured at a first-guide/card level. They are not yet full temple travel pages. The site still needs individual temple URLs, source links, timings, maps, review/vlog summaries, accessibility notes, and last-verified dates.

### Festival Register

Location: `content/festival-pages-2026.json`

Page: `festivals.html`

| Festival | 2026 date captured | Story captured | Quiz | Creative path | CTA |
|---|---:|---|---|---|---|
| Raksha Bandhan | August 28, 2026 | Yes | `krishna-beginner` | Rakhi mandala and promise card | Raksha/Janmashtami kit interest |
| Krishna Janmashtami | September 4, 2026 | Yes | `krishna-beginner` | Baby Krishna, butter pot, flute, dahi handi | Raksha/Janmashtami kit interest |
| Ganesh Chaturthi | September 14, 2026 | Yes | `ganesha-beginner` | Ganesha, modak, mouse vahana, bamboo platform | Ganesh kit interest |
| Navratri | October 11-19, 2026 | Yes | `devi-navratri-beginner` | Navadurga symbols, lion, lotus, lamp, garba circle | Navratri challenge |
| Dussehra | October 20, 2026 | Yes | `rama-navami-beginner` | Rama with bow, Ravana context card, victory lamps | Dussehra challenge |
| Diwali | November 8, 2026 | Yes | `lakshmi-diwali-beginner` | Diyas, Lakshmi lotus, Ayodhya lights, rangoli | Diwali unlock |
| Guru Nanak Jayanti | November 24, 2026 | Yes | `saraswati-beginner` | Lamp, kirtan, langar, seva symbols | Festival challenge |
| Maha Shivaratri | To verify by panchang | Yes | `shiva-beginner` | Shiva lingam, bilva leaves, damru, trishula, moon | Shivaratri unlock |
| Rath Yatra | To verify by panchang | Yes | `krishna-beginner` | Jagannath chariot, wheels, flags, ropes | Rath Yatra kit |
| Hanuman Jayanti | To verify by region | Yes | `rama-navami-beginner` | Hanuman mace, mountain, folded hands, Rama name | Hanuman challenge |

Important: festivals are captured as hub cards, not full festival pages. They need individual pages with rituals, stories, activities, kit path, FAQs, schema, and region/date notes.

### Quiz Register

Location: `content/quizzes.json`

Pages:

- Solo: `quiz-game.html?quiz={slug}`
- Family room: `quiz-room.html?quiz={slug}`
- Library: `games.html`

| Quiz | Slug | Current use |
|---|---|---|
| Rama Navami Beginner Quiz | `rama-navami-beginner` | Ramayana, Dussehra, Hanuman-linked paths |
| Shani Dev Beginner Quiz | `shani-dev-beginner` | Shani Dev path |
| Ganesha Beginner Quiz | `ganesha-beginner` | Ganesha and Ganesh Chaturthi path |
| Dashavatara Beginner Quiz | `dashavatara-beginner` | Vishnu/Dashavatara path |
| Shiva Beginner Quiz | `shiva-beginner` | Shiva and Maha Shivaratri path |
| Krishna Beginner Quiz | `krishna-beginner` | Krishna, Janmashtami, Rath Yatra path |
| Devi and Navratri Beginner Quiz | `devi-navratri-beginner` | Devi, Durga, Kali, Navratri path |
| Lakshmi and Diwali Beginner Quiz | `lakshmi-diwali-beginner` | Lakshmi, Kubera, Diwali path |
| Saraswati Beginner Quiz | `saraswati-beginner` | Saraswati, Brahma, Guru Nanak Jayanti placeholder quiz path |
| Subrahmanya and Surya Beginner Quiz | `subrahmanya-surya-beginner` | Subrahmanya, Surya, Varuna path |

Important: these are starter quizzes. They are not yet deep quiz ladders with beginner/intermediate/advanced levels.

### Coloring / Drawing Register

Location: `content/coloring-books.json`

| Coloring collection | Status | Page / assets | Current gaps |
|---|---|---|---|
| My First Ramayana Coloring Book | Available | `coloring-book-ramayana.html`, `ChildrenBook/*.png` | Needs improved digital coloring UX and PDF export |
| Ganesha Beginnings Coloring Book | Prompt-ready plus simple SVGs | `coloring/ganesha-*.svg`, story pack prompts | Needs final premium generated line art |
| Dashavatara Symbol Coloring Book | Prompt-ready plus simple SVGs | `coloring/dashavatara-symbols.svg`, `coloring/narasimha-prahlada.svg`, `coloring/vamana-umbrella.svg` | Needs full 10-avatar coloring book |
| Shani Dev Discipline Coloring Pages | Prompt-ready plus simple SVGs | `coloring/shani-*.svg` | Needs final premium line art and devotional style QA |
| Core Deity Symbols Coloring Book | Prompt-ready | Manifest only | Needs final generated symbol pages |

### Larger Text Coverage Register

Location: `content/purana-itihasa-coverage.json`

Currently captured as roadmap/coverage inventory:

- Itihasas: Ramayana, Mahabharata.
- Primary text: Bhagavad Gita.
- 18 Mahapuranas:
  - Brahma Purana
  - Padma Purana
  - Vishnu Purana
  - Shiva Purana
  - Bhagavata Purana
  - Narada Purana
  - Markandeya Purana
  - Agni Purana
  - Bhavishya Purana
  - Brahmavaivarta Purana
  - Linga Purana
  - Varaha Purana
  - Skanda Purana
  - Vamana Purana
  - Kurma Purana
  - Matsya Purana
  - Garuda Purana
  - Brahmanda Purana

First expansion topics captured:

- Sundara Kanda
- Bhagavad Gita chapter path
- Samudra Manthana
- Narasimha and Prahlada
- Gajendra Moksha
- Markandeya and Devi
- Shiva and Ganga
- Skanda birth
- Rukmini and Krishna
- Savitri and Satyavan

Important: these are coverage targets, not completed story experiences yet.

### Exact “Real vs Structured vs Missing” State

| Category | Real user-facing content exists | Structured data exists | Still missing |
|---|---|---|---|
| Ramayana | Yes | Yes | Guided journey, PDF export, stronger UX |
| Shani Dev | Yes | Yes | Final images, source validation, PDF export |
| Ganesha | Partial | Yes | Final images, PDF export, stronger kit page linkage |
| Dashavatara | Partial | Yes | Full 10-avatar pages, images, PDF |
| 16 deity hubs | Basic pages | Yes | Full stories, art, PDFs, SEO depth |
| Festivals | Hub cards | Yes | Individual festival pages |
| Temples | Hub cards | Yes | Individual full temple guides with verified data |
| Quizzes | Yes | Yes | Quiz ladders, better multiplayer, account persistence |
| Coloring | Ramayana yes; others simple/prompted | Yes | Premium generated art for non-Ramayana |
| Community | Concept page | Schema exists | Auth, comments, moderation, profiles |
| Gamification | Local prototype | Schema and JSON model exist | Real account-backed progress and refined expert loop |

