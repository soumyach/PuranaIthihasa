/**
 * prerender.mjs — Static SEO page generator for khatakshetra.com
 * Node ESM, no external dependencies (fs + path only).
 * Writes deity/<slug>.html, festival/<slug>.html, temple/<slug>.html
 * under the parent directory of this script (../deity, ../festival, ../temple).
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const CONTENT = path.join(ROOT, 'content');

// ── helpers ──────────────────────────────────────────────────────────────────

function readJSON(file) {
  return JSON.parse(fs.readFileSync(path.join(CONTENT, file), 'utf8'));
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

/** Truncate a string to maxLen chars at a word boundary, add ellipsis. */
function truncate(str, maxLen = 155) {
  if (!str || str.length <= maxLen) return str || '';
  const cut = str.lastIndexOf(' ', maxLen);
  return str.slice(0, cut > 0 ? cut : maxLen) + '…';
}

function escHtml(str) {
  return (str || '')
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/** Common <head> block shared by all pages. */
function headBlock({ title, description, canonicalUrl, ogType = 'article', extraJsonLd = '' }) {
  const safeTitle = escHtml(title);
  const safeDesc = escHtml(description);
  return `<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${safeTitle}</title>
  <meta name="description" content="${safeDesc}">
  <link rel="canonical" href="${canonicalUrl}">

  <!-- Open Graph -->
  <meta property="og:type" content="${ogType}">
  <meta property="og:title" content="${safeTitle}">
  <meta property="og:description" content="${safeDesc}">
  <meta property="og:url" content="${canonicalUrl}">
  <meta property="og:site_name" content="Khatakshetra">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="${safeTitle}">
  <meta name="twitter:description" content="${safeDesc}">

  <!-- Fonts (matching site) -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Cinzel+Decorative:wght@400;700&family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">

  <!-- Site stylesheet -->
  <link rel="stylesheet" href="/site.css">
  <link rel="stylesheet" href="/seo.css">

  <!-- JSON-LD -->
  ${extraJsonLd}
</head>`;
}

/** Top nav matching site structure. */
function navBlock() {
  return `<nav class="site-nav" aria-label="Main navigation">
  <a href="/" class="site-brand">Khatakshetra</a>
  <ul>
    <li><a href="/stories">Stories</a></li>
    <li><a href="/deities">Deities</a></li>
    <li><a href="/games">Games</a></li>
    <li><a href="/festivals">Festivals</a></li>
    <li><a href="/temples">Temples</a></li>
  </ul>
</nav>`;
}

function footerBlock() {
  return `<footer class="site-footer">
  <p>&copy; Khatakshetra. Exploring Puranas and Itihasa for families.</p>
</footer>
<script src="/site.js"></script>`;
}

// ── DEITY PAGES ───────────────────────────────────────────────────────────────

function buildDeityPage(entity, pack) {
  const { slug, name, summary, alsoKnownAs = [], related = [] } = entity;
  const canonicalUrl = `https://khatakshetra.com/deity/${slug}`;

  // Title: keyword-rich
  const pageTitle = `${name} — Story, Meaning, Symbolism & Quiz | Khatakshetra`;
  const metaDesc = truncate(summary, 155);

  // Key facts list
  const aka = alsoKnownAs.length
    ? `<li><strong>Also known as:</strong> ${escHtml(alsoKnownAs.join(', '))}</li>`
    : '';

  // Related entities cross-links (filter to deities only)
  const relatedDeityLinks = related
    .filter(r => r.startsWith('deity.') || r.startsWith('avatar.') || r.startsWith('mahavidya.'))
    .map(r => {
      const relSlug = r.replace(/^(deity\.|avatar\.|mahavidya\.)/, '');
      const label = relSlug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      return `<a href="/deity/${relSlug}">${escHtml(label)}</a>`;
    });

  // Pack-enriched fields
  let packSection = '';
  let quizSlug = '';
  if (pack) {
    quizSlug = pack.quiz || '';
    const rels = (pack.relationships || []).join(', ');
    const booklet = pack.booklet || '';
    packSection = `
    <section class="deity-pack">
      <h2>Explore ${escHtml(name)} on Khatakshetra</h2>
      ${booklet ? `<p><strong>Featured booklet:</strong> ${escHtml(booklet)}</p>` : ''}
      ${rels ? `<p><strong>Key relationships:</strong> ${escHtml(rels)}</p>` : ''}
      ${pack.story ? `<p>${escHtml(pack.story)}</p>` : ''}
      <ul class="cta-links">
        ${quizSlug ? `<li><a href="/deity.html?slug=${slug}#quiz">Take the ${escHtml(name)} quiz</a></li>` : ''}
        <li><a href="/deity.html?slug=${slug}">Full interactive experience &rarr;</a></li>
        ${quizSlug ? `<li><a href="/quiz-game.html?quiz=${quizSlug}">Play the ${escHtml(name)} quiz</a></li>` : ''}
      </ul>
    </section>`;
  } else {
    packSection = `
    <section class="deity-pack">
      <h2>Explore ${escHtml(name)} on Khatakshetra</h2>
      <ul class="cta-links">
        <li><a href="/deity.html?slug=${slug}">Full interactive experience &rarr;</a></li>
        <li><a href="/deities">Browse all deities</a></li>
      </ul>
    </section>`;
  }

  // JSON-LD: Article + BreadcrumbList + optional FAQPage
  const articleLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: pageTitle,
    description: metaDesc,
    url: canonicalUrl,
    publisher: {
      '@type': 'Organization',
      name: 'Khatakshetra',
      url: 'https://khatakshetra.com'
    },
    mainEntityOfPage: canonicalUrl
  };

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://khatakshetra.com/' },
      { '@type': 'ListItem', position: 2, name: 'Deities', item: 'https://khatakshetra.com/deities' },
      { '@type': 'ListItem', position: 3, name: name, item: canonicalUrl }
    ]
  };

  // FAQ from AEO short-answer style — use summary as a basic FAQ
  const faqLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: [
      {
        '@type': 'Question',
        name: `Who is ${name}?`,
        acceptedAnswer: { '@type': 'Answer', text: summary }
      }
    ]
  };
  if (alsoKnownAs.length) {
    faqLd.mainEntity.push({
      '@type': 'Question',
      name: `What are the other names of ${name}?`,
      acceptedAnswer: { '@type': 'Answer', text: alsoKnownAs.join(', ') }
    });
  }

  const extraJsonLd = [
    `<script type="application/ld+json">${JSON.stringify(articleLd)}</script>`,
    `<script type="application/ld+json">${JSON.stringify(breadcrumbLd)}</script>`,
    `<script type="application/ld+json">${JSON.stringify(faqLd)}</script>`
  ].join('\n  ');

  const html = `<!DOCTYPE html>
<html lang="en">
${headBlock({ title: pageTitle, description: metaDesc, canonicalUrl, ogType: 'article', extraJsonLd })}
<body>
${navBlock()}
<main class="deity-page">
  <article>
    <header class="entity-header">
      <h1>${escHtml(name)}</h1>
      ${aka ? `<ul class="key-facts">${aka}</ul>` : ''}
    </header>

    <section class="entity-summary">
      <p>${escHtml(summary)}</p>
    </section>

    ${relatedDeityLinks.length ? `
    <section class="related-entities">
      <h2>Related Deities</h2>
      <ul class="related-links">
        ${relatedDeityLinks.map(l => `<li>${l}</li>`).join('\n        ')}
      </ul>
    </section>` : ''}

    ${packSection}
  </article>
</main>
${footerBlock()}
</body>
</html>`;

  return html;
}

// ── FESTIVAL PAGES ────────────────────────────────────────────────────────────

function buildFestivalPage(festival) {
  const { slug, title, date, story, quiz, coloring, kitCta } = festival;
  const canonicalUrl = `https://khatakshetra.com/festival/${slug}`;

  const pageTitle = `${title} 2026 — Story, Date & Family Activities | Khatakshetra`;
  const metaDesc = truncate(`${title} ${date}: ${story}`, 155);

  const articleLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: pageTitle,
    description: metaDesc,
    url: canonicalUrl,
    publisher: {
      '@type': 'Organization',
      name: 'Khatakshetra',
      url: 'https://khatakshetra.com'
    },
    mainEntityOfPage: canonicalUrl
  };

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://khatakshetra.com/' },
      { '@type': 'ListItem', position: 2, name: 'Festivals', item: 'https://khatakshetra.com/festivals' },
      { '@type': 'ListItem', position: 3, name: title, item: canonicalUrl }
    ]
  };

  const faqLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: [
      {
        '@type': 'Question',
        name: `When is ${title} 2026?`,
        acceptedAnswer: { '@type': 'Answer', text: `${title} in 2026 falls on ${date}.` }
      },
      {
        '@type': 'Question',
        name: `What is the story of ${title}?`,
        acceptedAnswer: { '@type': 'Answer', text: story }
      }
    ]
  };

  const extraJsonLd = [
    `<script type="application/ld+json">${JSON.stringify(articleLd)}</script>`,
    `<script type="application/ld+json">${JSON.stringify(breadcrumbLd)}</script>`,
    `<script type="application/ld+json">${JSON.stringify(faqLd)}</script>`
  ].join('\n  ');

  const html = `<!DOCTYPE html>
<html lang="en">
${headBlock({ title: pageTitle, description: metaDesc, canonicalUrl, ogType: 'article', extraJsonLd })}
<body>
${navBlock()}
<main class="festival-page">
  <article>
    <header class="entity-header">
      <h1>${escHtml(title)}</h1>
      <p class="festival-date"><strong>2026 Date:</strong> ${escHtml(date)}</p>
    </header>

    <section class="entity-summary">
      <p>${escHtml(story)}</p>
    </section>

    <section class="festival-activities">
      <h2>Family Activities for ${escHtml(title)}</h2>
      <ul class="cta-links">
        ${quiz ? `<li><a href="/quiz-game.html?quiz=${escHtml(quiz)}">Take the ${escHtml(title)} quiz</a></li>` : ''}
        ${coloring ? `<li><a href="/drawing-kits">Coloring activity: ${escHtml(coloring)}</a></li>` : ''}
        ${kitCta ? `<li><a href="/kits?kit=${escHtml(kitCta)}">Get the ${escHtml(title)} activity kit</a></li>` : ''}
        <li><a href="/festivals">Browse all festivals</a></li>
      </ul>
    </section>
  </article>
</main>
${footerBlock()}
</body>
</html>`;

  return html;
}

// ── TEMPLE PAGES ──────────────────────────────────────────────────────────────

function buildTemplePage(temple) {
  const { slug, name, city, state, primaryDeity, story, howToReach, whatNotToMiss = [], foodNearby = [] } = temple;
  const canonicalUrl = `https://khatakshetra.com/temple/${slug}`;

  const pageTitle = `${name} — Story, Timings & How to Reach | Khatakshetra`;
  const metaDesc = truncate(`${name} in ${city}, ${state}. Deity: ${primaryDeity}. ${story}`, 155);

  const placeLd = {
    '@context': 'https://schema.org',
    '@type': 'Place',
    name: name,
    description: story,
    url: canonicalUrl,
    address: {
      '@type': 'PostalAddress',
      addressLocality: city,
      addressRegion: state,
      addressCountry: 'IN'
    }
  };

  const breadcrumbLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://khatakshetra.com/' },
      { '@type': 'ListItem', position: 2, name: 'Temples', item: 'https://khatakshetra.com/temples' },
      { '@type': 'ListItem', position: 3, name: name, item: canonicalUrl }
    ]
  };

  const faqLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: [
      {
        '@type': 'Question',
        name: `Where is ${name} located?`,
        acceptedAnswer: { '@type': 'Answer', text: `${name} is located in ${city}, ${state}, India.` }
      },
      {
        '@type': 'Question',
        name: `How to reach ${name}?`,
        acceptedAnswer: { '@type': 'Answer', text: howToReach }
      },
      {
        '@type': 'Question',
        name: `What is the main deity of ${name}?`,
        acceptedAnswer: { '@type': 'Answer', text: `The primary deity of ${name} is ${primaryDeity}.` }
      }
    ]
  };

  const extraJsonLd = [
    `<script type="application/ld+json">${JSON.stringify(placeLd)}</script>`,
    `<script type="application/ld+json">${JSON.stringify(breadcrumbLd)}</script>`,
    `<script type="application/ld+json">${JSON.stringify(faqLd)}</script>`
  ].join('\n  ');

  const wnmItems = whatNotToMiss.map(item => `<li>${escHtml(item)}</li>`).join('\n          ');
  const foodItems = foodNearby.map(item => `<li>${escHtml(item)}</li>`).join('\n          ');

  // Derive deity slug for linking
  const deitySlugMap = {
    'Venkateswara / Vishnu': 'vishnu',
    'Shiva': 'shiva',
    'Jagannath / Krishna': 'krishna',
    'Meenakshi / Parvati': 'parvati',
    'Ganesha': 'ganesha',
    'Kamakhya / Devi': 'durga',
    'Ayyappa': null
  };
  const deityLink = deitySlugMap[primaryDeity]
    ? `<a href="/deity/${deitySlugMap[primaryDeity]}">${escHtml(primaryDeity)}</a>`
    : escHtml(primaryDeity);

  const html = `<!DOCTYPE html>
<html lang="en">
${headBlock({ title: pageTitle, description: metaDesc, canonicalUrl, ogType: 'article', extraJsonLd })}
<body>
${navBlock()}
<main class="temple-page">
  <article>
    <header class="entity-header">
      <h1>${escHtml(name)}</h1>
      <p class="temple-location">${escHtml(city)}, ${escHtml(state)}</p>
    </header>

    <section class="entity-summary">
      <p>${escHtml(story)}</p>
    </section>

    <section class="temple-facts">
      <h2>Key Facts</h2>
      <ul class="key-facts">
        <li><strong>Deity:</strong> ${deityLink}</li>
        <li><strong>City:</strong> ${escHtml(city)}</li>
        <li><strong>State:</strong> ${escHtml(state)}</li>
        <li><strong>How to reach:</strong> ${escHtml(howToReach)}</li>
      </ul>
    </section>

    ${wnmItems ? `
    <section class="what-not-to-miss">
      <h2>What Not to Miss</h2>
      <ul>
          ${wnmItems}
      </ul>
    </section>` : ''}

    ${foodItems ? `
    <section class="food-nearby">
      <h2>Food Nearby</h2>
      <ul>
          ${foodItems}
      </ul>
    </section>` : ''}

    <section class="temple-guide-cta">
      <h2>Plan Your Visit</h2>
      <ul class="cta-links">
        <li><a href="/temples">Browse all temple guides</a></li>
        <li><a href="/community">Share your temple tip with the community</a></li>
      </ul>
    </section>
  </article>
</main>
${footerBlock()}
</body>
</html>`;

  return html;
}

// ── MAIN ──────────────────────────────────────────────────────────────────────

// ── STORY PAGES ───────────────────────────────────────────────────────────────

function buildStoryPage(story) {
  const { slug, title, summary, kidSummary, seo = {}, aeo = {}, sourceRefs = [], themes = [], entities = [], relatedActivities = [] } = story;
  const canonicalUrl = `https://khatakshetra.com/story/${slug}`;
  const pageTitle = (seo.title ? seo.title : `${title} — Ramayana & Purana Story`) + ' | Khatakshetra';
  const metaDesc = truncate(seo.description || summary, 155);

  const deityLinks = entities
    .filter(e => e.startsWith('deity.'))
    .map(e => {
      const s = e.replace(/^deity\./, '');
      const label = s.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      return `<a href="/deity/${s}">${escHtml(label)}</a>`;
    });

  const quizLinks = relatedActivities
    .filter(a => a.startsWith('quiz.'))
    .map(a => `<li><a href="/quiz-game.html?quiz=${a.replace(/^quiz\./, '')}">Play the related quiz</a></li>`);

  const sources = sourceRefs.map(r => {
    const label = [r.text, r.section, r.sarga ? `Sarga ${r.sarga}` : ''].filter(Boolean).join(' · ');
    return r.url
      ? `<li><a href="${escHtml(r.url)}" target="_blank" rel="noopener noreferrer">${escHtml(label)}</a></li>`
      : `<li>${escHtml(label)}</li>`;
  }).join('\n        ');

  const articleLd = { '@context': 'https://schema.org', '@type': 'Article', headline: pageTitle, description: metaDesc, url: canonicalUrl, publisher: { '@type': 'Organization', name: 'Khatakshetra', url: 'https://khatakshetra.com' }, mainEntityOfPage: canonicalUrl };
  const breadcrumbLd = { '@context': 'https://schema.org', '@type': 'BreadcrumbList', itemListElement: [ { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://khatakshetra.com/' }, { '@type': 'ListItem', position: 2, name: 'Stories', item: 'https://khatakshetra.com/stories' }, { '@type': 'ListItem', position: 3, name: title, item: canonicalUrl } ] };
  const faqLd = { '@context': 'https://schema.org', '@type': 'FAQPage', mainEntity: [ { '@type': 'Question', name: `What is the story of ${title}?`, acceptedAnswer: { '@type': 'Answer', text: aeo.shortAnswer || summary } } ] };

  const extraJsonLd = [
    `<script type="application/ld+json">${JSON.stringify(articleLd)}</script>`,
    `<script type="application/ld+json">${JSON.stringify(breadcrumbLd)}</script>`,
    `<script type="application/ld+json">${JSON.stringify(faqLd)}</script>`
  ].join('\n  ');

  return `<!DOCTYPE html>
<html lang="en">
${headBlock({ title: pageTitle, description: metaDesc, canonicalUrl, ogType: 'article', extraJsonLd })}
<body>
${navBlock()}
<main class="story-page">
  <article>
    <header class="entity-header">
      <h1>${escHtml(title)}</h1>
    </header>
    <section class="entity-summary">
      <p>${escHtml(summary)}</p>
      ${kidSummary ? `<p><strong>For children:</strong> ${escHtml(kidSummary)}</p>` : ''}
    </section>
    ${themes.length ? `<section class="story-themes"><h2>Themes</h2><div class="tag-row">${themes.map(t => `<span class="tag">${escHtml(t)}</span>`).join('')}</div></section>` : ''}
    ${deityLinks.length ? `<section class="related-entities"><h2>Who's in this story</h2><ul class="related-links">${deityLinks.map(l => `<li>${l}</li>`).join('')}</ul></section>` : ''}
    <section class="story-activities">
      <h2>Explore this story</h2>
      <ul class="cta-links">
        ${quizLinks.join('\n        ')}
        <li><a href="/stories">All stories</a></li>
      </ul>
    </section>
    ${sources ? `<section class="story-sources"><h2>Sources</h2><ul>${sources}</ul></section>` : ''}
  </article>
</main>
${footerBlock()}
</body>
</html>`;
}

// ── SITEMAP ───────────────────────────────────────────────────────────────────

function writeSitemap(entities, packBySlug, festivals, temples, stories) {
  const base = 'https://khatakshetra.com';
  const urls = [];
  const add = (loc, priority) => urls.push(`  <url><loc>${base}${loc}</loc><priority>${priority}</priority></url>`);
  add('/', '1.0');
  ['/stories', '/deities', '/games', '/festivals', '/temples'].forEach(u => add(u, '0.9'));
  add('/daily', '0.9'); add('/which-character', '0.8'); add('/paths', '0.7');
  ['/ramayana-journey', '/ramayana-path-game'].forEach(u => add(u, '0.8'));
  ['/booklets', '/drawing-kits', '/kits', '/coloring-book-ramayana', '/storybook-ramayana', '/rama-navami-reader'].forEach(u => add(u, '0.7'));
  ['/sangraha', '/community'].forEach(u => add(u, '0.6'));
  ['ramayana-starter', 'dasharatha-meets-shani', 'ganesha-beginnings', 'dashavatara'].forEach(p => add(`/story-experience?pack=${p}`, '0.8'));
  entities.filter(e => e.type === 'Deity' || packBySlug[e.slug]).forEach(e => add(`/deity/${e.slug}`, '0.7'));
  festivals.forEach(f => add(`/festival/${f.slug}`, '0.8'));
  temples.forEach(t => add(`/temple/${t.slug}`, '0.8'));
  stories.forEach(s => add(`/story/${s.slug}`, '0.7'));
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join('\n')}\n</urlset>\n`;
  fs.writeFileSync(path.join(ROOT, 'sitemap.xml'), xml, 'utf8');
}

// ── MAIN ──────────────────────────────────────────────────────────────────────

function main() {
  const entities = readJSON('entities.json');
  const packs = readJSON('deity-experience-packs.json');
  const festivals = readJSON('festival-pages-2026.json');
  const temples = readJSON('temple-guides.json');
  const stories = readJSON('stories.json');

  // Build slug→pack map
  const packBySlug = {};
  for (const p of packs) packBySlug[p.slug] = p;

  // Deity pages: entities with type "Deity" OR any entity with a matching pack
  const deityDir = path.join(ROOT, 'deity');
  ensureDir(deityDir);
  let deityCount = 0;
  const skipped = [];

  for (const entity of entities) {
    const hasPack = packBySlug[entity.slug];
    const isDeity = entity.type === 'Deity';

    if (!isDeity && !hasPack) {
      // Skip non-Deity entities without a pack (Place, Text, Collection, Person, etc.)
      skipped.push(`${entity.slug} (type=${entity.type}, no pack)`);
      continue;
    }

    const pack = hasPack || null;
    const html = buildDeityPage(entity, pack);
    const outPath = path.join(deityDir, `${entity.slug}.html`);
    fs.writeFileSync(outPath, html, 'utf8');
    deityCount++;
  }

  // Festival pages
  const festivalDir = path.join(ROOT, 'festival');
  ensureDir(festivalDir);
  let festivalCount = 0;

  for (const festival of festivals) {
    const html = buildFestivalPage(festival);
    fs.writeFileSync(path.join(festivalDir, `${festival.slug}.html`), html, 'utf8');
    festivalCount++;
  }

  // Temple pages
  const templeDir = path.join(ROOT, 'temple');
  ensureDir(templeDir);
  let templeCount = 0;

  for (const temple of temples) {
    const html = buildTemplePage(temple);
    fs.writeFileSync(path.join(templeDir, `${temple.slug}.html`), html, 'utf8');
    templeCount++;
  }

  // Story pages
  const storyDir = path.join(ROOT, 'story');
  ensureDir(storyDir);
  let storyCount = 0;
  for (const story of stories) {
    fs.writeFileSync(path.join(storyDir, `${story.slug}.html`), buildStoryPage(story), 'utf8');
    storyCount++;
  }

  // Sitemap: covers static pages + all generated entity/story pages.
  writeSitemap(entities, packBySlug, festivals, temples, stories);

  console.log(`Done.`);
  console.log(`  Deity pages:   ${deityCount}`);
  console.log(`  Festival pages: ${festivalCount}`);
  console.log(`  Temple pages:   ${templeCount}`);
  console.log(`  Story pages:    ${storyCount}`);
  console.log(`  Skipped:        ${skipped.length}`);
  console.log(`  sitemap.xml written.`);
  if (skipped.length) console.log(`  Skipped list:  ${skipped.join('; ')}`);
}

main();
