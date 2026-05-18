# Contextual Translation Plan

## Principle

Do not translate words. Translate cultural meaning.

Khatakshetra should launch English-first, but every content object should be designed for contextual Hindi and Telugu versions.

## What Contextual Translation Means

For each language version:

- preserve deity names and key terms,
- explain Sanskrit concepts naturally,
- adapt idioms rather than translating literally,
- preserve devotional warmth,
- keep source citations stable,
- keep kids content age-appropriate,
- localize examples where useful.

## Translation Layers

1. **Canonical terms**
   - Rama, Sita, Shani, dharma, puja, darshan, prasadam.
   - Maintain glossary per language.

2. **Narrative translation**
   - Rewrite sentence rhythm for the language.
   - Avoid English sentence structure in Hindi/Telugu.

3. **AEO translation**
   - Question phrasing should match how people actually ask in that language.

4. **Child adaptation**
   - A child version in Telugu/Hindi may need different simplicity than direct English translation.

5. **SEO localization**
   - Keyword research must be language-specific, not translated from English keywords.

## Data Fields

Every story should support:

```json
{
  "languages": {
    "en": {},
    "hi": {},
    "te": {}
  },
  "glossary": [],
  "translationNotes": [],
  "reviewStatusByLanguage": {}
}
```

## Review

Every non-English page needs:

- native-language review,
- devotional tone review,
- child-safety review if applicable,
- SEO/AEO review.
