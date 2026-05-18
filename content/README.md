# Structured Content

This directory is the first step toward the knowledge graph.

- `entities.json`: deities, people, rishis, places, texts, temples, festivals, and objects.
- `stories.json`: source-aware story records with SEO/AEO fields.
- `quizzes.json`: quiz content connected to stories.
- `kits.json`: Khatakshetra product records and lead tags.

These files are intentionally simple JSON so the current static site can evolve without a framework migration. The next step is a small build script that turns this content into story pages, quiz pages, and entity pages.
