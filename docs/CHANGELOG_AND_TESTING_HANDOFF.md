# Khatakshetra Changelog And Testing Handoff

## Current Git State

Latest pushed implementation before this handoff:

- `77d916b Add holistic product blueprint`
- `31f96ba Fix paint and add Ramayana path game`
- `0e2fe31 Fix digital coloring paint page`
- `52fbf58 Add gamified journey spine`

This document summarizes what changed, what is live in the repo, and how another teammate should test it.

## Feature List

### 1. Ramayana Journey

File:

- `ramayana-journey.html`

What it does:

- Creates a guided five-node Ramayana path.
- Connects story, coloring, signup/save, solo quiz, and family quiz.
- Awards progress through localStorage.
- Shows Parampara Tree progress.
- Shows completion/share section when all nodes are complete.

Test URL:

- `http://127.0.0.1:8796/ramayana-journey.html`

Expected behavior:

- Click `Begin Journey`.
- Complete nodes one by one.
- Progress panel updates.
- Completion section appears after all nodes are marked complete.

### 2. Digital Coloring Book

Files:

- `coloring-book-ramayana.html`
- `paint.html`

What it does:

- Shows the Ramayana coloring page lineup.
- Each page has `Paint digitally`.
- Digital paint page lets a child select colors, draw over the image, clear paint, and download artwork.

Test URLs:

- `http://127.0.0.1:8796/coloring-book-ramayana.html`
- `http://127.0.0.1:8796/paint.html?image=ChildrenBook%2FCover.png&title=Cover`

Expected behavior:

- Open coloring book.
- Click `Paint digitally`.
- Select a swatch.
- Draw on the image with mouse, trackpad, or touch.
- Change brush size.
- Clear paint.
- Download artwork.

Important note:

- Use `http://127.0.0.1:8796/...` or the live site for the best paint/download behavior.
- `file://...` may restrict download/export behavior in some browsers, though drawing should still work.

### 3. Solo Quiz

File:

- `quiz-game.html`

What it does:

- Loads quiz content from `content/quizzes.json`.
- Runs a five-question quiz.
- Awards progress.
- Reveals a Talapatra card after quiz completion.
- Links back to story pack and family room.

Test URL:

- `http://127.0.0.1:8796/quiz-game.html?quiz=rama-navami-beginner`

Expected behavior:

- Quiz questions render.
- Answer choices show correct/wrong states.
- End screen shows score and progress.
- Talapatra reveal modal appears.
- Card appears later in Sangraha.

### 4. Family Quiz Room

File:

- `quiz-room.html`

What it does:

- Pass-the-device family quiz.
- Designed for parent/child/grandparent style use.
- Awards family/community progress.

Test URL:

- `http://127.0.0.1:8796/quiz-room.html?quiz=rama-navami-beginner`

Expected behavior:

- Add or use family players.
- Answer questions turn by turn.
- End screen shows family score.
- Progress is awarded.

### 5. Ramayana Path Game

File:

- `ramayana-path-game.html`

What it does:

- Adds a real playable Ramayana board/path game beyond quiz-only play.
- User rolls 1-3 spaces.
- User answers story/dharma prompts.
- User earns Dharma, Courage, and Seva tokens.
- Completion reveals a Hanuman Talapatra card.

Test URL:

- `http://127.0.0.1:8796/ramayana-path-game.html`

Expected behavior:

- Click `Start Game`.
- Click `Roll`.
- Choose an answer for the current story space.
- Token counts update.
- Board position advances.
- Final space triggers completion and card reveal.

### 6. Sangraha Card Collection

File:

- `sangraha.html`

What it does:

- Reads locally earned Talapatra cards.
- Shows user progress and card collection.
- Acts as the first collector layer.

Test URL:

- `http://127.0.0.1:8796/sangraha.html`

Expected behavior:

- Before earning cards, page shows empty state.
- After quiz/game completion, earned cards appear.

### 7. Progress And Signup Layer

File:

- `site.js`

What it does:

- Replaces `window.prompt` with a modal.
- Tracks local profile, XP, title, tracks, unlocks, events, and cards.
- Shows persistent progress chip.
- Supports Talapatra card reveal.

Expected behavior:

- Any page loading `site.js` shows a small progress chip.
- Signup CTA opens a modal instead of browser prompt.
- Progress survives refresh in the same browser.

### 8. Game Library Entry

File:

- `games.html`

What it does:

- Adds direct hero CTA to `ramayana-path-game.html`.
- Keeps quiz library.
- Shows board/game templates.
- The Ramayana Story Path has `Play now`.

Test URL:

- `http://127.0.0.1:8796/games.html`

Expected behavior:

- Hero has `Play Ramayana Path`.
- Board games section includes Ramayana Story Path.
- Clicking `Play now` opens the game.

### 9. Holistic Product Blueprint

File:

- `docs/KHATAKSHETRA_HOLISTIC_PRODUCT_BLUEPRINT.md`

What it does:

- Explains vision, audiences, games, community, gamification, retention, KG, content engine, temple engine, SEO/AEO, backend direction, and contributor responsibilities.
- Intended as the starting point for new teammates.

### 10. LLM And Crawler Files

Files:

- `llms.txt`
- `llm.txt`
- `robots.txt`
- `sitemap.xml`

What they do:

- `llms.txt` gives LLM agents a product summary and key routes.
- `llm.txt` is a singular alias pointing to `llms.txt`.
- `robots.txt` allows public pages/docs and disallows private/API/account areas.
- `sitemap.xml` includes the new major pages and the holistic blueprint doc.

## How To Run Locally

From the preview folder:

```bash
cd /Users/vellankisriharsha/Documents/Codex/2026-05-17/files-mentioned-by-the-user-mahagatha/PuranaIthihasa-main
python3 -m http.server 8796 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8796/
```

## Recommended Demo Flow

1. Open `ramayana-journey.html`.
2. Start the journey.
3. Open story pack briefly.
4. Open coloring book.
5. Paint a page digitally.
6. Open Ramayana Path Game.
7. Play two or three turns.
8. Open solo quiz.
9. Complete quiz and show Talapatra reveal.
10. Open Sangraha and show card collection.
11. Ask for email/save interest through modal.

## Known Limitations

- Progress is currently localStorage-based, not Supabase-backed.
- Paint download works best through HTTP/live site, not direct `file://`.
- Ramayana Path Game is a first playable version, not final visual polish.
- Kula, Sabha, Vrata, contribution moderation, and real user accounts are designed but not fully implemented.
- Content is seeded, but many deity/story/festival/temple pages still need richer production content.

## Next Engineering Priorities

1. Supabase Auth and progress sync.
2. Proper signup persistence.
3. Better mobile QA for paint and game.
4. Visual polish for Ramayana Path Game.
5. Ganesha journey.
6. Shani Dev journey.
7. Card catalog expansion.
8. Real share card generation.
9. Kula prototype.

## Next Content Priorities

1. Complete Ramayana pack.
2. Complete Shani Dev pack.
3. Complete Ganesha pack.
4. Complete Dashavatara collection.
5. Add core deity story/quiz/coloring/booklet relationships.
6. Add first 10 polished temple guides.
7. Create Ganesha, Shani, Dashavatara, Devi coloring sets.
