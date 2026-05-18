# Visual and Script Generation Pipeline

## 1. Principle

Every serious content item should generate a complete media pack, not only text.

Khatakshetra content should become:

- a normal article,
- a cinematic story,
- a premium booklet,
- a voiceover,
- a dialogue/skit script,
- a descriptive narration,
- image prompts,
- character sheets,
- coloring/drawing pages,
- quiz/game assets,
- social share cards.

This lets one researched story become many useful experiences.

## 2. Required Script Types

### Type 1: Voiceover Script

Purpose:

- audio story,
- YouTube narration,
- reels/shorts,
- bedtime listening,
- premium booklet read-aloud.

Style:

- short lines,
- tone markers,
- SSML breaks,
- strong rhythm,
- cinematic but reverent,
- pronunciation glossary.

Output fields:

- `voiceoverScript`
- `ssml`
- `chapterMarkers`
- `pronunciationGlossary`
- `musicBrief`
- `soundCueNotes`

### Type 2: Character Dialogue / Skit Script

Purpose:

- movie-like scenes,
- school/cultural center performances,
- animated shorts,
- multiplayer/family role-play,
- reels with character voices.

Style:

- character names,
- scene heading,
- stage/action notes,
- dialogue,
- emotion cues,
- child-safe version when needed.

Output fields:

- `sceneTitle`
- `characters`
- `setting`
- `dialogue`
- `actionNotes`
- `performanceNotes`
- `durationEstimate`

Example:

```text
SCENE: THE WARNING IN AYODHYA

DASHARATHA stands before the royal astrologers.

ASTROLOGER:
Maharaja, Shani moves toward Rohini. If the path is pierced, the rains may fail.

DASHARATHA:
Then this is not a matter for the sky alone. It is a matter for every hungry child on Earth.
```

### Type 3: Descriptive Script

Purpose:

- article narration,
- booklets,
- visual scene description,
- accessibility,
- image generation,
- documentary pacing.

Style:

- rich but controlled prose,
- source-aware,
- fewer performance markers,
- more scene atmosphere,
- clear factual grounding.

Output fields:

- `descriptiveNarrative`
- `sceneDescriptions`
- `visualMotifs`
- `symbolism`
- `sourceNotes`

## 3. Visual Generation Flow

Every story pack should produce:

1. Hero image prompt.
2. Character sheet prompts.
3. Key scene prompts.
4. Booklet spread prompts.
5. Coloring page prompts.
6. Social share card prompts.
7. Thumbnail prompt.
8. Motion prompt for animated hero/video.

## 4. Visual Style Rules

Preserve Khatakshetra visual identity:

- premium devotional archive,
- Indian epic cinematic art,
- warm ivory paper,
- antique gold,
- deep green/maroon/indigo,
- temple mural / miniature / manuscript inspiration,
- readable sacred dignity,
- no cheap cartoon deity art,
- no generic fantasy armor,
- no horror tone for deities like Shani or Kali.

For children:

- gentler expressions,
- clean silhouettes,
- clear actions,
- less visual violence,
- line-art versions for coloring.

## 5. Image Prompt Schema

```json
{
  "visuals": {
    "heroPrompt": "",
    "motionHeroPrompt": "",
    "characterSheets": [],
    "scenePrompts": [],
    "bookletSpreadPrompts": [],
    "coloringPagePrompts": [],
    "thumbnailPrompts": [],
    "socialCardPrompts": [],
    "negativePrompt": "cheap cartoon, horror, gore, distorted hands, unreadable text, disrespectful deity depiction"
  }
}
```

## 6. Motion / Animation Use

Motion should communicate value, not distract.

Use:

- slow parallax on hero art,
- glowing constellation/entity links,
- page-turn transitions for booklets,
- talapatra cards sliding like sacred strips,
- quiz cards flipping,
- drawing kit color fill animation,
- temple map path reveal,
- subtle gold-line drawing animations.

Avoid:

- excessive particle effects,
- generic bouncy SaaS motion,
- animations that slow the first CTA,
- unreadable hero text over busy video.

## 7. Production Workflow

For each story:

1. Source brief.
2. Entity links.
3. Three script types.
4. Visual prompt pack.
5. Generate draft images.
6. Human review for sacred accuracy and style.
7. Create booklet/drawing/social assets.
8. Publish.

All generated images should store:

- prompt,
- model,
- date,
- story id,
- asset type,
- review status,
- license/usage notes.

## 8. Immediate Build Target

For the first showcase story, create:

- one cinematic hero image,
- four story scene images,
- one character sheet,
- two coloring pages,
- one hardbound booklet cover,
- one motion hero concept,
- voiceover script,
- skit script,
- descriptive script.

This becomes the repeatable media pack template.
