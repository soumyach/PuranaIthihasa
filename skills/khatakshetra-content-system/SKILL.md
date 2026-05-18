---
name: khatakshetra-content-system
description: Use when creating, auditing, or expanding Khatakshetra content packs for stories, deity hubs, festivals, temples, quizzes, coloring books, booklets/PDFs, SEO/AEO metadata, source notes, relationship maps, gamification unlocks, and public-safe copy.
---

# Khatakshetra Content System

## Core Rule

Produce visible value first: a visitor should immediately be able to read, play, color, download/print, save progress, or join an unlock path. Do not expose internal terms such as seed, content graph, placeholder, validation, TODO, KG, pipeline, planned, or source review.

## Content Unit

For each story, deity, festival, temple, or collection create:

- Quick AEO answer
- SEO title, description, FAQ, and internal links
- Adult cinematic narrative
- Kids 5-8 version
- Kids 9-12 version
- Character-dialogue/skit version
- Descriptive article version
- Public-friendly source and variant notes
- Related people, places, texts, festivals, temples, and activities
- Solo quiz and family-room quiz
- Points, level, unlock, and referral mechanics
- Coloring/drawing prompt plus image generation prompt
- Booklet/PDF outline
- Signup or kit-interest CTA

## Workflow

1. Pick the content type and schema:
   - Story pack: `content/templates/story-pack.schema.json`
   - Temple guide: `content/templates/temple-profile.schema.json`
   - Deity/festival/game additions: follow existing JSON structure in `content/`.
2. Check public copy with `scripts/audit_public_copy.py`.
3. Keep factual humility:
   - Use “traditional retelling” or “variant traditions” for non-finalized references.
   - Never claim a specific textual source unless the source location is present.
4. Create all child experiences together:
   - story -> quiz -> coloring/page prompt -> booklet/PDF -> unlock.
5. Add relationships using visitor-facing labels:
   - “Related people, places, texts, and ideas”
   - Avoid backend labels like nodes, edges, graph, KG.
6. Add image prompts but do not publish rough diagrams as final coloring books.

## Gamification

Use points only when they signal real progress:

- Quiz correct answer: small XP
- Quiz completion: completion XP
- Family-room completion: social XP
- Coloring download/submission: creative XP
- Verified temple tip: contribution XP
- Referral conversion: community XP

Levels should unlock concrete value: PDF booklets, coloring packs, festival challenges, talapatra cards, or kit early access.

## References

- Read `references/content-quality.md` when writing story/deity/festival copy.
- Read `references/gamification.md` when designing account progress, points, rooms, and unlocks.
- Read `references/image-prompts.md` when creating visual prompts or coloring-book briefs.

