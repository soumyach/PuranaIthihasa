# Khatakshetra Holistic Product Blueprint

## 1. One-Line Vision

Khatakshetra is a premium Hindu culture experience platform where stories, deities, temples, festivals, games, coloring books, booklets, family challenges, community, and physical kits become one connected learning world.

The project repository is `PuranaIthihasa`; the public brand is `Khatakshetra`.

## 2. What We Are Not Building

We are not building:

- A generic mythology blog.
- A passive story archive.
- A quiz-only learning site.
- A kids-only activity site.
- A public leaderboard app with shallow points and badges.
- A one-time festival kit storefront.

We are building a cultural enrichment system that families can return to weekly, use around festivals, share with relatives, and eventually subscribe to or buy kits from.

## 3. Core Product Thesis

Content is the world. Gamification is the physics. Community is the retention layer. Physical kits are portals.

That means:

- Every story should connect to deities, people, places, texts, values, festivals, temples, games, quizzes, coloring, booklets, and kits.
- Every action should move the user somewhere: unlock a card, light a journey node, grow a tree, complete a family challenge, or prepare for a festival.
- Every physical kit should activate a digital experience, not sit outside the platform.

## 4. Primary Audiences

### Children

Need:

- Stories they can understand.
- Coloring and drawing.
- Simple games.
- Collectible cards.
- Progress they can see.

What they should feel:

- "I want to unlock the next card."
- "I can tell this story."
- "I want to show this to my parents/grandparents."

### Parents

Need:

- Trustworthy source-aware content.
- Low-friction activities.
- A meaningful way to teach culture without having to prepare everything themselves.
- Premium, non-cheap-feeling experiences.
- Reasons to sign up, return, and eventually buy.

What they should feel:

- "This is not random screen time."
- "My child is learning something I care about."
- "This can become a weekly family ritual."

### Adults And GenZ Learners

Need:

- Deeper story layers.
- Source notes and variants.
- Life lessons.
- philosophical interpretation.
- Temple and festival context.

What they should feel:

- "I finally understand why this story matters."
- "This is beautiful enough to share."
- "This is serious without feeling dry."

### Grandparents, Temples, Schools, And Cultural Groups

Need:

- Family/group participation.
- Event and competition formats.
- Printable and digital materials.
- Moderated contribution paths.

What they should feel:

- "This helps us pass stories forward."
- "This can be used in a class, apartment event, temple gathering, or family call."

## 5. Three Experience Loops

### Loop 1: Learning Loop

Daily or session-level progress.

Core mechanic:

- User enters a Kshetra.
- User completes nodes: story, quiz, coloring, booklet, game, reflection.
- Completion grows the Parampara Tree and unlocks Talapatra Cards.

Current implementation:

- `ramayana-journey.html`: first guided journey.
- `story-experience.html`: story pack experience.
- `coloring-book-ramayana.html`: coloring book gallery.
- `paint.html`: digital coloring.
- `quiz-game.html`: solo quiz.
- `quiz-room.html`: pass-the-device family quiz.
- `ramayana-path-game.html`: first simple board/path game.
- `sangraha.html`: user card collection.

Next improvements:

- Make journey state more visual.
- Add Ganesha journey.
- Add Shani Dev journey.
- Add Dashavatara collection path.
- Add full Cosmic Map after at least 3 journeys exist.

### Loop 2: Kula Loop

Weekly family/group retention.

Future mechanic:

- A Kula is a private group of 4-12 people.
- It may include parents, children, cousins, grandparents, temple friends, or classmates.
- A Kula gets a weekly challenge.
- Members can compare progress internally.
- Members can gift Talapatra Cards.
- The Kula grows a collective Parampara Tree.

Important rule:

- Do not start with a public global leaderboard.
- Use internal Kula leaderboards first.
- Public competition comes later through Sabha.

Required backend:

- Auth.
- Group table.
- Membership table.
- Progress events.
- Card ownership.
- Weekly challenge assignment.
- Kula moderation roles.

### Loop 3: Sabha Loop

Seasonal competition and public recognition.

Future mechanic:

- Sabhas are tied to the Hindu calendar, not arbitrary quarters.
- Example tracks:
  - Story quiz.
  - Family/Kula quiz.
  - Coloring or drawing submission.
  - Story retelling.
  - Skit/script submission.
  - Temple story contribution.

Important rule:

- Do not launch a public Sabha too early.
- First Sabhas should be founding-cohort or invite-only.
- Winners should receive physical kits, not only badges.

## 6. Game System

Games should not be decorative. A game must teach story comprehension, values, sequence, relationships, or ritual context.

### Game Types

- Solo quiz.
- Family quiz room.
- Board/path game.
- Card matching game.
- Story sequencing game.
- Dharma choice game.
- Temple trail game.
- Festival challenge game.
- Coloring/drawing challenge.

### Currently Implemented

- Solo quiz engine.
- Pass-the-device family quiz.
- Ramayana Story Path board game.
- Progress/XP awards.
- Talapatra card reveal.

### Near-Term Game Backlog

1. Ramayana Story Path polish:
   - Better board visuals.
   - Multiple players.
   - Better win screen.
   - Printable board version.
2. Dashavatara Match:
   - Match avatar to cosmic problem.
   - Match symbol to avatar.
3. Shani Slow Path:
   - Patience/consequence/reflection game.
4. Ganesha Obstacle Path:
   - Choose wise action to remove obstacles.
5. Temple Trail:
   - Follow story, ritual, timing, location clues.

## 7. Gamification System

XP exists as accounting, not as the emotional hero.

Visible emotional mechanics should be:

- Journey nodes.
- Parampara Tree.
- Talapatra Cards.
- Sangraha collection.
- Kula progress.
- Vrata seals.
- Sabha recognition.

### Titles

Current title ladder:

- Shravaka: The Listener.
- Jigyasu: The Curious.
- Sadhaka: The Seeker.
- Katha Vachak: The Storyteller.
- Vidwan: The Learned.
- Acharya: The Teacher.

### Talapatra Cards

Cards should be earned after meaningful action.

Examples:

- Quiz completion.
- 80 percent+ score.
- 100 percent score.
- Journey completion.
- Vrata completion.
- Sabha participation.
- Kit QR unlock.

Rarity:

- Common: basic completion.
- Rare: strong completion or journey completion.
- Epic: mastery.
- Legendary: Sabha, Vrata, or physical kit unlock.

Important rule:

- Do not let a child earn an important card without understanding something real.

### Vrata

Future commitment mechanic.

Examples:

- 7-day Ganesha Kshetra Vrata.
- 21-day Ramayana starter Vrata.
- 40-day family culture Vrata.

Failure language:

- Never say failed.
- Say unfinished, restart, or resume.

## 8. Community System

Community should start as contribution and participation, not a noisy social feed.

### Contribution Types

- Temple tips.
- Temple timings corrections.
- Travel guidance.
- Ritual explanation.
- Local food recommendations.
- Festival photos.
- Story questions.
- Child artwork.
- Family challenge entries.
- Regional variants.
- Translation/context corrections.

### Moderation Principle

User content should not go live without quality controls.

Recommended stages:

1. Private submission.
2. Internal review.
3. Helpful votes or moderator approval.
4. Public display.
5. Contributor status only after sustained quality.

### Community Roles

- Family member.
- Kula leader.
- Temple contributor.
- Story contributor.
- Reviewer.
- Sabha participant.
- Founding family.

## 9. Knowledge Graph Direction

The KG should support discovery and trust. It should not block content launch.

### Initial KG Approach

Start with lightweight structured relationships:

- Entity names.
- Aliases.
- Entity type.
- Related stories.
- Related texts.
- Related deities.
- Related people.
- Related places.
- Related temples.
- Related festivals.
- Related values.
- Related games.
- Related booklets.

This is enough for:

- Internal linking.
- SEO/AEO.
- "Related stories" modules.
- Deity hubs.
- Festival pages.
- Temple pages.
- Quiz generation.
- Future conversational answers.

### Entity Types

- Deity.
- Avatar.
- Rishi or muni.
- Person.
- Place.
- Temple.
- Text.
- Purana.
- Itihasa.
- Festival.
- Ritual.
- Value.
- Object.
- Story.
- Game.
- Booklet.
- Kit.

### Relationship Types

- appears_in.
- child_of.
- spouse_of.
- avatar_of.
- devotee_of.
- teacher_of.
- located_in.
- associated_with.
- celebrated_during.
- has_ritual.
- has_symbol.
- has_vehicle.
- has_story.
- has_quiz.
- has_coloring_page.
- has_booklet.
- has_game.
- source_text.
- variant_of.

### KG Data Shape

Preferred local format:

```json
{
  "id": "deity.ganesha",
  "type": "deity",
  "name": "Ganesha",
  "aliases": ["Ganapati", "Vinayaka", "Vighnaharta"],
  "summary": "Ganesha is worshipped before beginnings and remembered as remover of obstacles.",
  "relationships": [
    { "type": "child_of", "target": "deity.shiva" },
    { "type": "child_of", "target": "deity.parvati" },
    { "type": "has_festival", "target": "festival.ganesh-chaturthi" },
    { "type": "has_story", "target": "story.ganesha-elephant-head" }
  ]
}
```

### Long-Term KG Storage

Options:

- Supabase Postgres tables for structured relationships.
- Postgres JSONB for flexible relationship metadata.
- Later: Neo4j or graph database only if relationship queries become too complex.

Recommendation:

- Start with Postgres plus JSON content files.
- Do not add graph database complexity before content and UX prove demand.

## 10. Content Engine

The content engine is the production line for story experiences.

### Each Story Pack Should Contain

- Title.
- Slug.
- One-line hook.
- Adult cinematic narration.
- Kids 5-8 version.
- Kids 9-12 version.
- Dialogue/skit version.
- Descriptive article version.
- Source note.
- Related entities.
- Related places.
- Related festivals.
- Quiz questions.
- Coloring page specs.
- Booklet sections.
- Talapatra cards.
- Game hooks.
- SEO title.
- Meta description.
- AEO FAQ.
- Contextual translation notes.

### Content Standards

- Source-aware.
- Clear when a variant exists.
- No fake citations.
- No "seed content" or internal words on public pages.
- Cinematic but respectful.
- Meaningful for parents.
- Simple enough for kids.
- Deep enough for adults.

### Translation Principle

Do not perform literal translation only.

For Hindi and Telugu:

- Preserve cultural context.
- Use familiar devotional vocabulary.
- Keep story meaning, not just sentence structure.
- Validate terms with native speakers or reviewers.

## 11. Visual And Coloring System

### Visual Identity

Khatakshetra should feel like:

- Temple archive.
- Premium family learning.
- Indian ritual warmth.
- Storybook craft.

Avoid:

- Cheap cartoon-only look.
- Random AI fantasy.
- Dark irrelevant backgrounds.
- Generic stock imagery.

### Coloring Books

Coloring pages should be:

- Paintable digitally.
- Printable.
- Line-art-first.
- Story-sequenced.
- Child-friendly.
- Available as individual pages and full books.

Current:

- Ramayana coloring book exists.
- Digital paint page exists.

Needs:

- Ganesha coloring book.
- Shani Dev coloring book.
- Dashavatara coloring book.
- Devi/Navratri coloring book.
- Temple coloring pages.

## 12. Temple Guide Engine

Temple pages should combine devotion, story, and travel utility.

Each temple guide should include:

- Temple name.
- Deity.
- Location.
- Core story.
- Source/legend note.
- Rituals.
- Timings.
- Best time to visit.
- How to reach.
- Nearby places.
- Food/restaurants.
- What not to miss.
- Photos/videos/vlog references.
- User tips.
- Connected festivals.
- Connected stories.
- Connected deities.

Important:

- Timings, travel, restaurants, and reviews are time-sensitive and must be verified before publishing.

## 13. SEO And AEO System

Khatakshetra should be structured for:

- Google Search.
- AI answer engines.
- Rich snippets.
- Internal discovery.
- Festival-season landing pages.

### Core SEO Surfaces

- Homepage.
- Story pages.
- Deity hubs.
- Festival pages.
- Temple guides.
- Coloring book pages.
- Booklet/PDF pages.
- Game pages.
- Kit pages.
- FAQ blocks.
- Structured data.
- Sitemap.
- Robots.
- `llms.txt`.

### AEO Requirements

Every important page should answer:

- What is this story?
- Who are the key people/deities?
- Which text/source is it associated with?
- What is the meaning?
- Why is it celebrated?
- What can children do with it?
- What related stories should I read next?

## 14. Backend And Storage Direction

### Short Term

Static pages plus JSON content files.

Current working approach:

- HTML pages.
- `content/*.json`.
- localStorage progress.
- email intent capture scaffolding.

### Production Backend

Recommended:

- Supabase Auth.
- Supabase Postgres.
- Supabase Storage for user submissions and generated PDFs.
- Vercel hosting.

### Core Tables

- profiles.
- signups.
- user_events.
- user_progress.
- journeys.
- journey_progress.
- cards.
- user_cards.
- kulas.
- kula_members.
- challenges.
- challenge_submissions.
- quizzes.
- quiz_attempts.
- story_entities.
- relationships.
- temple_guides.
- user_temple_tips.
- kit_interest.

### Analytics

Track:

- Email captured.
- Journey started.
- Journey completed.
- Coloring opened.
- Coloring downloaded.
- Quiz started.
- Quiz completed.
- Family room opened.
- Game started.
- Game completed.
- Card earned.
- Share clicked.
- Kit interest clicked.

## 15. Retention Strategy

### Daily Or Session Retention

- Journey node progress.
- Quiz unlocks.
- Coloring pages.
- Card reveals.

### Weekly Retention

- Kula challenge.
- New story drop.
- New coloring page.
- Family quiz room.

### Festival Retention

- Seasonal Kshetra activation.
- Limited-time cards.
- Festival kits.
- Sabha challenges.

### Long-Term Retention

- Parampara Tree.
- Sangraha collection.
- Vrata seals.
- Kula identity.
- Public recognition.
- Physical kit bridge.

## 16. Commerce And Kits

Kits are not separate merchandise. They are physical extensions of the digital world.

Each kit should include:

- Hero craft.
- Story booklet.
- Sacred object.
- Activity layer.
- Parent guide.
- Challenge/share card.
- QR Seed Code.

QR Seed Code should unlock:

- Premium journey.
- Rare Talapatra cards.
- Kit-specific coloring pages.
- Sabha eligibility.
- Kula challenge.

## 17. Current Site State

Current implemented pages include:

- `index.html`: homepage.
- `stories.html`: story library.
- `story-experience.html`: story pack shell.
- `story-shani-dev.html`: Shani Dev story page.
- `ramayana-journey.html`: guided Ramayana journey.
- `ramayana-path-game.html`: playable Ramayana path game.
- `quiz-game.html`: solo quiz.
- `quiz-room.html`: family quiz room.
- `coloring-book-ramayana.html`: Ramayana coloring book.
- `paint.html`: digital coloring.
- `sangraha.html`: card collection.
- `deities.html`: deity hubs.
- `deity.html`: deity detail page.
- `festivals.html`: festival pages.
- `temples.html`: temple guide index.
- `booklets.html`: booklet/PDF area.
- `drawing-kits.html`: drawing kits.
- `kits.html`: kit interest.
- `community.html`: early community concept.

## 18. Immediate Priorities

### Product

1. Make Ramayana journey feel polished end-to-end.
2. Make paint/coloring smooth on mobile and desktop.
3. Improve Ramayana path game visuals.
4. Add Ganesha journey.
5. Add Shani Dev journey.
6. Make Sangraha cards more visual.

### Content

1. Finish Ramayana story pack.
2. Finish Shani Dev pack.
3. Finish Ganesha pack.
4. Finish Dashavatara hub.
5. Create 16 core deity hubs with story, quiz, coloring, and relationships.
6. Create festival pages for priority 2026 festivals.
7. Create first 10 temple guides.

### Backend

1. Supabase Auth.
2. Signup storage.
3. User progress sync.
4. Card ownership.
5. Quiz attempts.
6. Journey progress.

### Growth

1. Founder demo script.
2. HSR founding family waitlist.
3. WhatsApp share cards.
4. Kit interest flow.
5. Weekly story email.

## 19. What Contributors Should Do

### Engineers

- Keep pages usable without backend where possible.
- Use structured JSON for content.
- Do not hardcode future claims as if they are live.
- Avoid internal terms on public pages.
- Make every feature mobile-friendly.

### Content Writers

- Follow the narrative style guide.
- Create multiple modes for each story.
- Add relationship metadata.
- Add quiz questions.
- Add AEO FAQs.
- Mark source confidence.

### Designers

- Preserve premium temple-archive identity.
- Make games and coloring feel polished.
- Avoid cheap/generic art.
- Build reusable components.

### Growth/Community

- Focus on signup moments after value is experienced.
- Design family challenges.
- Use WhatsApp sharing.
- Start with founding families.
- Avoid empty public community surfaces.

## 20. North-Star Demo Flow

For an early parent-child demo:

1. Open Ramayana Journey.
2. Show story node.
3. Open coloring book.
4. Paint a page.
5. Play Ramayana Path Game.
6. Play a quiz.
7. Reveal Talapatra Card.
8. Open Sangraha.
9. Ask for email or kit interest.

The emotional pitch:

> "This turns culture into something your child can read, play, color, remember, and share with the family."

## 21. Operating Principle

One thing to read. One thing to play. One thing to make. One thing to unlock. One reason to return.

Every Khatakshetra experience should pass that test.
