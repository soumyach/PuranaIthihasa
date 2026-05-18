# Khatakshetra System Plan

Public brand/domain: **Khatakshetra** (`khatakshetra.com`).

Repository/project name: **PuranaIthihasa**.

## 0. Current Repo Reality

The current PuranaIthihasa repo is a lightweight static Vercel site:

- `index.html` redirects to `rama-navami-reader.html`.
- `rama-navami-reader.html` contains the full Rama Navami reader, carousel, coloring-book modal, myth-buster content, and email capture UI.
- `Images/` and `ChildrenBook/` contain seed Ramayana images.
- `api/email-capture.js` stores email captures in Supabase.
- `vercel.json` rewrites `/` to the Rama Navami reader.

This is not yet a scalable content platform, but it is a strong prototype base. The next move should be to preserve the current page as a launch artifact while introducing structured content and generated pages around it.

## 1. Product Thesis

Build the most trusted, enjoyable, and commercially useful Hindu culture platform for families:

1. Trusted source layer: original-text-aware story pages, source citations, entity pages, temple pages, festival pages, and multilingual summaries.
2. Enjoyment layer: readings, quizzes, coloring books, printable activities, simple games, board-game mechanics, and competition loops.
3. Commerce/community layer: premium Khatakshetra kits, waitlists, user submissions, family challenges, schools/cultural centers, and festival campaigns.

The key insight: Khatakshetra should not be "a mythology blog." It should become a culture operating system where every story, deity, place, festival, temple, product, game, and user activity is connected.

## 2. Guardrail: Content Rights

Do not bulk rephrase modern copyrighted books into seed content, including uploaded commercial PDFs, unless we have explicit rights from the publisher/author. We can use them as reading inspiration, for internal notes, or to identify candidate topics, but not as a substitute-text generator.

Use this content policy:

- Public domain sources: safe for ingestion and adaptation with attribution.
- Open web translations: treat as "read/reference" unless license is clear.
- WisdomLib and ValmikiRamayan.net: useful for source discovery and citations, but do not blindly scrape and republish full translations without validating terms.
- Modern books: do not paraphrase chapter-by-chapter into replacement content.
- Best launch pattern: source-aware original retellings written from multiple references, with citations and provenance metadata.

## 3. System Architecture

### Phase 1: Static Plus Structured Content

Keep the current static site simple, but add structured data files:

```text
content/
  stories/
    ramayana/
    puranas/
    festivals/
  entities/
    people/
    deities/
    places/
    texts/
    temples/
  quizzes/
  games/
  kits/
  i18n/
```

Each page can still be generated into static HTML/JSON for Vercel. We do not need a heavy CMS immediately.

### Phase 2: Content API

Add a lightweight API layer:

- `/api/search`
- `/api/entity/:slug`
- `/api/story/:slug`
- `/api/quiz/:slug`
- `/api/graph/neighbors/:entityId`
- `/api/lead`
- `/api/challenge-submission`

Start with JSON files or Supabase tables. Move to a graph database only when the graph queries become real product features.

### Phase 3: Lightweight Entity Graph Service

Use a lightweight entity graph for linkages first. Do not let "building the KG" become the product before users see value.

- Stories connect to deities, people, places, texts, festivals, temples, virtues, objects, and products.
- Entities connect through typed relations.
- Every generated claim has provenance and confidence.

Recommended stack:

- Short term: JSON-LD files + Supabase/Postgres tables.
- Medium term: Postgres + `pgvector` + graph-like edge table.
- Later: Neo4j or Memgraph if graph traversal becomes central.

Do not start with Neo4j unless there is a working content pipeline and graph traversal is already a visible product feature. It will slow launch.

## 4. Knowledge Graph Ontology

### Core Node Types

- `Deity`: Rama, Sita, Shiva, Ganesha, Shani, Surya, Chhaya.
- `Person`: Dasharatha, Janaka, Bharata, Kaikeyi.
- `RishiMuni`: Valmiki, Vishwamitra, Narada, Pippalada.
- `Place`: Ayodhya, Mithila, Lanka, Kailasa, Puri.
- `Temple`: Jagannath Temple Puri, Shani Shingnapur, etc.
- `Text`: Valmiki Ramayana, Skanda Purana, Mahabharata.
- `BookSection`: Bala Kanda, Ayodhya Kanda, Skanda Purana Kashi Khanda.
- `Story`: Rama's birth, Sita Swayamvar, Dasharatha meets Shani.
- `Festival`: Rama Navami, Ganesh Chaturthi, Rath Yatra, Janmashtami.
- `Virtue`: dharma, devotion, restraint, courage, humility.
- `Object`: bow, chariot, modak, bamboo talapatra strip.
- `Product`: kit, printable, coloring book, game board.
- `Activity`: quiz, coloring page, board game, build craft.

### Core Edge Types

- `APPEARS_IN`: entity -> text/story.
- `PART_OF`: story -> text section.
- `TAKES_PLACE_AT`: story -> place.
- `ASSOCIATED_WITH`: deity/person -> festival/object/place.
- `FAMILY_OF`: person/deity -> person/deity.
- `TEACHES`: story -> virtue.
- `SOURCE_FOR`: text section -> story.
- `CELEBRATED_BY`: festival -> activity/product.
- `HAS_TEMPLE`: deity -> temple.
- `PILGRIMAGE_OF`: temple/place -> text/festival.
- `TRANSLATED_AS`: content -> language version.
- `HAS_KID_VERSION`: story -> child version.
- `HAS_AUDIO_VERSION`: story -> reading/voiceover.
- `HAS_QUIZ`: story/festival -> quiz.
- `INSPIRES_PRODUCT`: story/festival -> kit.

### Story Schema

```json
{
  "id": "story.ramayana.rama-birth",
  "slug": "rama-birth",
  "title": "The Birth of Rama",
  "tradition": ["Vaishnava", "Ramayana"],
  "sourceRefs": [
    {
      "text": "Valmiki Ramayana",
      "section": "Bala Kanda",
      "sarga": "18",
      "url": "https://www.valmikiramayan.net/"
    }
  ],
  "summary": "Short factual summary.",
  "retellingAdult": "Original retelling.",
  "retellingKids": "Simpler retelling.",
  "entities": ["deity.rama", "person.dasharatha", "place.ayodhya"],
  "themes": ["dharma", "divine birth", "kingdom"],
  "seo": {
    "title": "Rama Birth Story: Valmiki Ramayana Source, Meaning, and Festival Link",
    "description": "Learn the story of Rama's birth from the Valmiki Ramayana with meaning, characters, places, and Rama Navami activities."
  },
  "aeo": {
    "shortAnswer": "Rama was born to King Dasharatha and Queen Kausalya in Ayodhya after the Putrakameshti yajna.",
    "faq": []
  },
  "languages": ["en", "hi", "te"]
}
```

## 5. Content Pipeline

### Ingestion

Inputs:

- Public-domain translations.
- Original Sanskrit source references.
- Permissioned sources.
- Temple official pages where available.
- User/researcher-submitted temple lore marked as unverified until reviewed.

Pipeline:

1. Fetch or manually add source section metadata.
2. Extract entities, places, relationships, and candidate stories.
3. Generate source-aware story notes.
4. Human review for factual and devotional sensitivity.
5. Generate three outputs:
   - trusted adult page,
   - kids version,
   - activity/quiz/game version.
6. Translate into Hindi and Telugu.
7. Publish with schema.org structured data.

### Agentic Workflow

Use LLM agents, but keep provenance strict:

- `Source Librarian`: finds source passages and stores citations.
- `Entity Extractor`: proposes KG nodes and relationships.
- `Story Reteller`: writes original retellings from notes, not copy-paste text.
- `Child Adaptation Agent`: rewrites for age bands 5-8 and 9-12.
- `Quiz/Game Agent`: generates MCQs, riddles, sequencing games, memory cards.
- `SEO/AEO Agent`: creates title, meta, FAQ, short answer, related links.
- `Reviewer Agent`: flags unsupported claims, contradictions, sensitive retellings.
- `Translation Agent`: creates Hindi/Telugu versions with glossary protection.

All generated content must store:

- source references,
- model used,
- generation date,
- reviewer status,
- confidence level,
- claims needing review.

## 6. SEO and AEO Architecture

### Page Types

Build programmatic pages for:

- `/stories/rama-birth`
- `/deities/rama`
- `/places/ayodhya`
- `/texts/valmiki-ramayana/bala-kanda/sarga-18`
- `/festivals/rama-navami`
- `/temples/jagannath-temple-puri`
- `/kids/ramayana-coloring-book`
- `/quizzes/rama-navami`
- `/kits/ganesh-chaturthi-the-remover`

### Structured Data

Use JSON-LD:

- `Article`
- `FAQPage`
- `BreadcrumbList`
- `CreativeWork`
- `Person` where appropriate, but better as custom linked data for mythological figures.
- `Product` for kits.
- `Event` for festival dates and challenges.
- `EducationalResource` for kids activities.

### AEO Blocks

Every page should contain:

- 40-word direct answer.
- 120-word explanation.
- FAQ with 5-8 questions.
- "Source trail" section.
- "Related stories" from KG.
- "For kids" version.
- "Play/quiz/color" CTA.

### Internal Linking Rule

No story page should be a dead end. Each story page must link to:

- primary deity/person page,
- source text page,
- place page,
- festival page if relevant,
- one quiz/activity,
- one product or email capture if relevant.

## 7. Tomorrow-Ready Build Plan

Goal: by tomorrow, ship a credible seed version that shows the flywheel:

Story -> entity links -> SEO page -> kids activity -> quiz/game -> kit waitlist.

### Day 0 / Tonight

1. Preserve current Rama Navami page.
2. Add structured content directory and first JSON schemas.
3. Add 10 seed story records:
   - Rama's birth
   - Vishwamitra asks for Rama
   - Tataka Vadha
   - Ahalya liberation
   - Sita Swayamvar
   - Rama exile
   - Bharata's vow
   - Hanuman meets Rama
   - Dasharatha meets Shani
   - Birth of Shani
4. Add entity seed set:
   - Rama, Sita, Lakshmana, Hanuman, Dasharatha, Bharata, Vishwamitra, Valmiki, Narada, Shani, Surya, Chhaya, Shiva.
5. Add first quiz JSON:
   - Rama Navami quiz
   - Shani Dev quiz
6. Add product landing data for:
   - Ganesh Chaturthi: The Remover
   - Rath Yatra: The Great Journey
   - Raksha Bandhan + Janmashtami: The Bond and the Butter Thief

### Day 1

1. Create a new homepage:
   - "Stories, games, and heirloom festival kits for Hindu families."
   - Feature Rama Navami reader.
   - Feature Khatakshetra kit waitlist.
   - Feature kids coloring book.
   - Feature quizzes.
2. Add a Story Index page.
3. Add an Entity Explorer page.
4. Add a simple Quiz page from JSON.
5. Add a "related names and places" section showing connected entities for one story.
6. Add SEO basics:
   - title/description,
   - canonical,
   - Open Graph,
   - JSON-LD,
   - sitemap-ready URLs.

### Day 2-7

1. Build static generator so JSON becomes pages.
2. Add multilingual fields for Hindi and Telugu.
3. Add Supabase tables for leads, quiz scores, story feedback, and content entities.
4. Add admin/import scripts for source references.
5. Create 50 seed story pages.
6. Create 10 kids quizzes.
7. Create 10 coloring pages.
8. Create 3 kit landing pages.

## 8. Games and Activities

### Fast HTML Games

- Memory match: deity, symbol, vehicle, place.
- Story sequence: drag events into order.
- Dharma dilemma: choose action and see Ramayana/Purana parallel.
- Map journey: Ayodhya to Lanka, Puri Rath route, Krishna Mathura-Vrindavan.
- Quiz ladder: answer 10 questions to unlock certificate.
- Coloring modal: already present, can be generalized.

### Board Game Concepts

- `Rama's Path`: cooperative journey board game where family helps Rama cross story milestones.
- `Rath Pull`: strategy game around devotion, teamwork, and resource cards.
- `Ganesha Begins`: obstacle-removal board game for ages 5-8.
- `Shani's Lessons`: older-kid karma/consequence decision game.

### Competition Loop

- Monthly festival challenge.
- Upload photo/artwork/quiz score.
- Parent consent and moderation.
- Certificate generated.
- Winners featured on community page.
- Email loop brings families back for next festival.

## 9. Khatakshetra Product Architecture

Positioning:

> Heirloom-quality Hindu culture kits for modern families.

Launch order:

1. Ganesh Chaturthi: The Remover.
2. Raksha Bandhan + Janmashtami: The Bond and the Butter Thief.
3. Rath Yatra: The Great Journey.

Every kit:

- one thing to make,
- one story to remember,
- one sacred object to preserve,
- one moment to share.

Digital companion:

- kit landing page,
- story page,
- QR to reading/audio,
- quiz,
- upload challenge,
- related stories,
- temple/festival explainer,
- product waitlist or purchase.

## 10. Data Model for Monetization

Capture these events:

- email signup,
- kit interest by festival,
- coloring unlock,
- quiz start/completion/score,
- story page feedback,
- language preference,
- child age band,
- parent interest: kit, school, temple, community, bulk order.

Lead tags:

- `main_page`
- `kids_coloring_book`
- `ganesh_kit`
- `rath_yatra_kit`
- `raksha_janmashtami_kit`
- `quiz_rama_navami`
- `quiz_shani_dev`
- `school_bulk`
- `nri_family`

The current email API only accepts `main_page` and `kids_coloring_book`; this should be expanded before kit pages launch.

## 11. Technical Direction

### Keep Now

- Vercel static hosting.
- Supabase email capture.
- Existing images and coloring modal.
- One-file prototype speed.

### Add Next

- `/content/*.json`
- `/scripts/build-pages.js`
- generated static pages
- `sitemap.xml`
- `robots.txt`
- common CSS/JS split out from the giant HTML file
- entity/story/quiz schemas

### Later

- Next.js or Astro if static generation grows.
- Postgres/Supabase for production content.
- pgvector for semantic search.
- Neo4j/Memgraph only after graph UX proves valuable.
- Real chat experience grounded in KG + source excerpts.

## 12. Search Strategy

Own long-tail queries first:

- "Why does Shani Dev look down?"
- "Rama birth story for kids"
- "Ganesh Chaturthi story for children"
- "What is the meaning of Rath Yatra for kids?"
- "Valmiki Ramayana Ahalya story"
- "Who is Chhaya Devi?"
- "Rama Navami activities for kids"
- "Hindu festival kits for children"
- "Ganesh Chaturthi craft kit"

Each article must beat generic content by adding:

- source reference,
- original retelling,
- kid version,
- quiz/activity,
- relationship map,
- festival/product link.

## 13. Immediate Questions

1. Confirm final brand voice for `Khatakshetra`: devotional-family, scholarly-source-aware, or premium cultural learning.
2. First launch CTA: waitlist only, preorder, or "join challenge"?
3. Audience priority: India urban parents, NRI Hindu families, schools/cultural centers, or all three with separate landing pages?
4. Content stance: scholarly-neutral, devotional-family, or devotional but source-aware?
5. Languages for day one: English only with Hindi/Telugu coming soon, or visible trilingual pages from the start?
6. Commerce stack: Shopify, Razorpay payment links, or waitlist first?
7. Community: should user submissions be public immediately after moderation, or private family gallery first?

## 14. Recommended Decision

For the next 24 hours:

- Use `Khatakshetra` as the public website, content brand, community brand, and kit brand.
- Treat `PuranaIthihasa` as the Git/project name only.
- Launch with English-first content, but make Hindi/Telugu fields part of the schema now.
- Do not build chat yet.
- Build content pages, temple guides, quizzes, drawing/booklet experiences, and kit waitlists first.
- Keep the first entity graph lightweight: canonical names, aliases, places, texts, titles, source sections, and related links.
- Use Ganesh Chaturthi as the first commerce story.

This gives us speed without losing the long-term architecture.
