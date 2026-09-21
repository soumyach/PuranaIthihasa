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
const SITE = 'https://khatakshetra.com';
const OG_FALLBACK = '/Images/home/fullbleed-lamps.jpg';

/**
 * Pick the best share image available on disk. Every generated page previously
 * shipped with NO og:image, so a shared deity/festival/story/season link
 * rendered as a blank grey card in WhatsApp and on social — on exactly the
 * pages we are about to push.
 */
function ogImageFor(candidates) {
  for (const rel of (candidates || [])) {
    if (!rel) continue;
    const clean = rel.replace(/^\//, '');
    if (fs.existsSync(path.join(ROOT, clean))) return '/' + clean;
  }
  return OG_FALLBACK;
}

function headBlock({ title, description, canonicalUrl, ogType = 'article', extraJsonLd = '', image = OG_FALLBACK }) {
  const safeTitle = escHtml(title);
  const safeDesc = escHtml(description);
  const safeImage = escHtml(image.indexOf('http') === 0 ? image : SITE + image);
  return `<head>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-X9NTBSLFTJ"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', 'G-X9NTBSLFTJ');
  </script>
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
  <meta property="og:image" content="${safeImage}">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="${safeTitle}">
  <meta name="twitter:description" content="${safeDesc}">
  <meta name="twitter:image" content="${safeImage}">

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

// The channels, in one place. site.js holds the same pair for the hand-written
// pages; change both together if a handle ever moves.
const SOCIAL = {
  youtube: 'https://www.youtube.com/@Khatakshetra',
  instagram: 'https://www.instagram.com/khatakshetra/'
};

// Set in main() from seasons.json, so switching Ganapati -> Navaratri is a
// content change, not a code change.
let FOOTER_SEASON = null;

function footerBlock() {
  const season = FOOTER_SEASON
    ? ` &middot; <a href="/${FOOTER_SEASON.slug}">${escHtml(FOOTER_SEASON.label)}</a>`
    : '';
  return `<footer class="site-footer">
  <p>&copy; Khatakshetra. Exploring Puranas and Itihasa for families.</p>
  <nav class="site-footer-links" aria-label="Footer">
    <a href="/">Home</a> &middot; <a href="/stories">Stories</a> &middot; <a href="/games">Play</a> &middot; <a href="/paint">Colour</a> &middot; <a href="/temples">Temples</a> &middot; <a href="/daily">Daily</a>${season} &middot; <a href="/about">About</a> &middot; <a href="/contact">Contact</a>
  </nav>
  <nav class="site-footer-social" aria-label="Khatakshetra on social media">
    <span>Follow the stories:</span>
    <a href="${SOCIAL.youtube}" target="_blank" rel="noopener" data-kx-social="footer">YouTube</a> &middot;
    <a href="${SOCIAL.instagram}" target="_blank" rel="noopener" data-kx-social="footer">Instagram</a>
  </nav>
</footer>
<script src="/analytics.js"></script>
<script src="/site.js"></script>`;
}

/**
 * Reusable membership block. Generated pages previously had no email field at
 * all, so every visitor an SEO result or a campaign link delivered had no way
 * to become a member. site.js wires [data-signup-form] globally, so this is
 * markup-only — no per-page script, one implementation to maintain.
 */
function joinBlock({ cta, heading, copy, button = 'Join Khatakshetra Family — free' }) {
  return `<section class="kx-join">
      <div class="kx-eyebrow">Khatakshetra Family — Free</div>
      <h2>${escHtml(heading)}</h2>
      <p>${escHtml(copy)}</p>
      <form class="kx-join-form" data-signup-form data-cta="${escHtml(cta)}">
        <div class="kx-join-fields" data-signup-fields>
          <input type="email" name="email" placeholder="your@email.com" aria-label="Your email" required>
          <button class="kx-btn kx-btn-primary" type="submit">${escHtml(button)}</button>
        </div>
        <p class="kx-status" data-status role="status"></p>
      </form>
      <p class="kx-fine">Free forever &middot; no child account needed &middot; unsubscribe in one click.</p>
      <p class="kx-alt"><a href="/start">Or start the free 7-day family journey &rarr;</a></p>
    </section>`;
}


// Populated in main() before the deity/festival pages are built, so an existing
// page can point at the season it belongs to without a parallel URL tree.
const ONRAMP = { deity: {}, festival: {} };

// ── SEASONS (Ganapati pilot; Navaratri reuses these unchanged) ────────────────
//
// The provenance system is the point of this template. Khatakshetra's promise is
// "source-aware stories", so the interface has to SHOW provenance rather than
// bury it in a footer. Three classes:
//   mula      — what a text actually says (paraphrased), with the edition named
//   tradition — received or later tradition, labelled as such
//   drishti   — our own reading, never passed off as scripture
//
// Citation honesty rule: a source renders a LINK only when verified === true.
// Unverified sources render at khaṇḍa (book) level with the edition named and an
// explicit note, because chapter numbering differs between witnesses and a wrong
// verse locator would destroy the credibility the whole season rests on.

const SOURCE_CLASS = {
  mula: { label: 'Mūla · what the text says', cls: 'sc-mula' },
  tradition: { label: 'Tradition · received telling', cls: 'sc-tradition' },
  drishti: { label: 'Drishti · our reading', cls: 'sc-drishti' }
};

function sourceBadge(kind) {
  const meta = SOURCE_CLASS[kind];
  if (!meta) return '';
  return `<span class="kx-sc ${meta.cls}">${escHtml(meta.label)}</span>`;
}

/** The exact provenance of a claim: text, locator, edition, and a link if checked. */
function provenancePanel(sources, opts = {}) {
  const list = (sources || []).filter(Boolean);
  if (!list.length) return '';
  const rows = list.map((r) => {
    const link = (r.verified && r.url)
      ? ` <a href="${escHtml(r.url)}" target="_blank" rel="noopener" data-kx-source="${escHtml(r.text || '')}">Read the source &rarr;</a>`
      : '';
    const flag = r.verified
      ? '<span class="kx-prov-ok" title="Checked against the linked edition">checked</span>'
      : '<span class="kx-prov-pending" title="Cited at book level; verse locator not yet checked against the edition">book level</span>';
    return `<li>
        <strong>${escHtml(r.text || '')}</strong>${r.locator ? ` &mdash; ${escHtml(r.locator)}` : ''} ${flag}
        ${r.edition ? `<div class="kx-prov-ed">${escHtml(r.edition)}</div>` : ''}
        ${r.note ? `<div class="kx-prov-note">${escHtml(r.note)}</div>` : ''}
        ${link ? `<div class="kx-prov-link">${link}</div>` : ''}
      </li>`;
  }).join('\n      ');
  return `<aside class="kx-prov">
      <p class="kx-prov-h">${escHtml(opts.heading || 'Where this comes from')}</p>
      <ul>
      ${rows}
      </ul>
    </aside>`;
}

// A small mooshika who scurries in and settles at Ganesha's feet. Pure CSS,
// decorative only (aria-hidden), and it simply appears in place when the
// visitor has asked for reduced motion.
function mooshika() {
  return `<div class="kx-mooshika" aria-hidden="true">
        <svg viewBox="0 0 126 66" xmlns="http://www.w3.org/2000/svg">
          <!-- facing RIGHT, because he is running toward Ganesha -->
          <path class="kx-moo-tail" d="M23 50C11 53 2 47 4 37c1-5 5-8 9-8"
            stroke="currentColor" stroke-width="2.6" stroke-linecap="round" fill="none"/>
          <ellipse class="kx-moo-foot kx-moo-foot-a" cx="44" cy="57" rx="6.5" ry="3.4" fill="currentColor"/>
          <ellipse class="kx-moo-foot kx-moo-foot-b" cx="72" cy="57" rx="6.5" ry="3.4" fill="currentColor"/>
          <circle cx="74" cy="24" r="11.5" fill="currentColor"/>
          <circle cx="74" cy="24" r="5.5" fill="#3a2407" opacity=".45"/>
          <path d="M22 52C12 50 12 34 25 30c12-4 34-6 52-2 10 2 20 6 28 12 3 2 7 4 10 5 2 .6 2 2.4 0 3-5 1.5-11 2-17 1-10 5-38 8-56 7-10-.6-16-2-20-4Z"
            fill="currentColor"/>
          <circle cx="97" cy="41" r="2.3" fill="#3a2407" opacity=".85"/>
          <circle cx="116" cy="46" r="2" fill="#3a2407" opacity=".5"/>
          <path d="M112 50c4 3 8 4 12 4M112 52c3 4 6 6 10 7" stroke="currentColor"
            stroke-width="1.5" stroke-linecap="round" opacity=".75"/>
        </svg>
      </div>`;
}

function seasonHero(season, sub) {
  const copy = `<div class="kx-hero-copy">
        <p class="kx-eyebrow">${escHtml(season.eyebrow || 'Khatakshetra · Season')}</p>
        <h1>${escHtml(sub ? sub.title : season.title)}</h1>
        <p class="kx-season-thesis">${escHtml(sub ? sub.hook : season.thesis)}</p>
        ${sub ? `<p class="kx-season-back"><a href="/${escHtml(season.slug)}">&larr; ${escHtml(season.title)}</a></p>` : ''}
      </div>`;

  // Only the season home gets the full two-column hero; the article pages stay
  // a single reading column.
  if (sub) return `<header class="kx-season-hero">${copy}</header>`;

  const art = ogImageFor([season.ogImage]);
  return `<header class="kx-season-hero is-hub">
      ${copy}
      <div class="kx-hero-art">
        <img src="${escHtml(art)}" alt="${escHtml(season.title)}" fetchpriority="high"
          onerror="this.closest('.kx-hero-art').classList.add('is-bare')">
        ${mooshika()}
      </div>
    </header>`;
}

function seasonNav(season, currentSlug) {
  const items = season.features.map((f) => {
    const here = f.slug === currentSlug;
    return here
      ? `<span class="is-here">${escHtml(f.navTitle || f.title)}</span>`
      : `<a href="/${escHtml(season.slug)}/${escHtml(f.slug)}">${escHtml(f.navTitle || f.title)}</a>`;
  }).join('');
  return `<nav class="kx-season-nav" aria-label="${escHtml(season.title)}">
      <a href="/${escHtml(season.slug)}"${currentSlug ? '' : ' class="is-here"'}>Season home</a>${items}
    </nav>`;
}

function sourceShelf(season) {
  if (!season.sourceShelf || !season.sourceShelf.length) return '';
  const rows = season.sourceShelf.map((r) => `<li>
        <strong>${escHtml(r.text)}</strong>
        ${r.verified && r.url ? ` <a href="${escHtml(r.url)}" target="_blank" rel="noopener" data-kx-source="${escHtml(r.text)}">open &rarr;</a>` : ''}
        <div class="kx-prov-ed">${escHtml(r.edition || '')}</div>
        <div class="kx-prov-note">${escHtml(r.use || '')}</div>
      </li>`).join('\n        ');
  return `<section class="kx-shelf">
      <h2>The source shelf</h2>
      <p class="kx-shelf-note">${escHtml(season.editionNote || '')}</p>
      <ul>
        ${rows}
      </ul>
    </section>`;
}

function buildSeasonHub(season) {
  const canonicalUrl = `https://khatakshetra.com/${season.slug}`;
  const pageTitle = season.seoTitle || season.title;
  const metaDesc = truncate(season.seoDescription || season.thesis, 155);

  const ld = {
    '@context': 'https://schema.org', '@type': 'CollectionPage',
    name: pageTitle, description: metaDesc, url: canonicalUrl,
    isPartOf: { '@type': 'WebSite', name: 'Khatakshetra', url: 'https://khatakshetra.com/' }
  };
  const crumbs = {
    '@context': 'https://schema.org', '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://khatakshetra.com/' },
      { '@type': 'ListItem', position: 2, name: season.title, item: canonicalUrl }
    ]
  };

  const cards = season.features.map((f) => `<a class="kx-feat" href="/${escHtml(season.slug)}/${escHtml(f.slug)}">
        <h3>${escHtml(f.navTitle || f.title)}</h3>
        <p>${escHtml(f.hook || '')}</p>
        <span class="kx-feat-go">Read it &rarr;</span>
      </a>`).join('\n      ');

  const eight = season.features.find((f) => f.kind === 'forms');
  const rail = eight ? `<section class="kx-rail-wrap">
      <h2>The eight, at a glance</h2>
      <p class="kx-rail-note">${escHtml(eight.caution || '')}</p>
      <ol class="kx-rail">
        ${eight.forms.map((f) => `<li><a href="/${escHtml(season.slug)}/${escHtml(eight.slug)}#${escHtml(f.slug)}">
          <img class="kx-rail-art" src="/Images/ganapati/${escHtml(f.slug)}-form.jpg" alt=""
            loading="lazy" onerror="this.remove()">
          <span class="kx-rail-form">${escHtml(f.form)}</span>
          <span class="kx-rail-vs">confronts</span>
          <span class="kx-rail-asura">${escHtml(f.asura)}</span>
          <span class="kx-rail-obs">${escHtml(f.obstacle)} &middot; ${escHtml(f.gloss)}</span>
        </a></li>`).join('\n        ')}
      </ol>
    </section>` : '';

  const soon = (season.comingSoon || []).length ? `<section class="kx-soon">
      <h2>Still being written</h2>
      <p class="kx-shelf-note">We would rather publish four pages we can stand behind than eight we cannot.</p>
      <ul>
        ${season.comingSoon.map((c) => `<li><strong>${escHtml(c.title)}</strong><div>${escHtml(c.note)}</div></li>`).join('\n        ')}
      </ul>
    </section>` : '';

  return `<!DOCTYPE html>
<html lang="en">
${headBlock({ title: pageTitle, description: metaDesc, canonicalUrl, ogType: 'website',
  image: ogImageFor([season.ogImage]),
  extraJsonLd: [`<script type="application/ld+json">${JSON.stringify(ld)}</script>`,
                `<script type="application/ld+json">${JSON.stringify(crumbs)}</script>`].join('\n  ') })}
<body class="kx-season" data-kx-season="${escHtml(season.slug)}">
${navBlock()}
<main class="season-page is-hub">
${seasonHero(season)}
${seasonNav(season, '')}

  <section class="kx-season-intro">
    <p>${escHtml(season.intro || '')}</p>
    <p class="kx-season-legend">
      ${sourceBadge('mula')} ${sourceBadge('tradition')} ${sourceBadge('drishti')}
    </p>
  </section>

  <section class="kx-feats">
    <h2>Start here</h2>
    <div class="kx-feat-grid">
      ${cards}
    </div>
  </section>

${rail}

${joinBlock({
    cta: `season_${season.slug}`,
    heading: 'Get one of these a week, free',
    copy: 'Join Khatakshetra Family and we will send one story at a time — with the sources named, a question to ask your children, and a page they can colour.'
  })}

${soon}

${sourceShelf(season)}
</main>
${footerBlock()}
</body>
</html>`;
}

function buildSeasonForms(season, feature) {
  const canonicalUrl = `https://khatakshetra.com/${season.slug}/${feature.slug}`;
  const pageTitle = feature.seoTitle || feature.title;
  const metaDesc = truncate(feature.seoDescription || feature.hook, 155);

  const ld = {
    '@context': 'https://schema.org', '@type': 'Article',
    headline: pageTitle, description: metaDesc, url: canonicalUrl,
    publisher: { '@type': 'Organization', name: 'Khatakshetra', url: 'https://khatakshetra.com' },
    mainEntityOfPage: canonicalUrl
  };
  const crumbs = {
    '@context': 'https://schema.org', '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://khatakshetra.com/' },
      { '@type': 'ListItem', position: 2, name: season.title, item: `https://khatakshetra.com/${season.slug}` },
      { '@type': 'ListItem', position: 3, name: feature.navTitle || feature.title, item: canonicalUrl }
    ]
  };

  // <details> rather than a JS accordion: keyboard-accessible, works with JS
  // off, and deep-linkable. One page now; each form can become its own /story/
  // page later without changing this data.
  const forms = feature.forms.map((f, i) => `<details class="kx-form" id="${escHtml(f.slug)}" data-kx-form="${escHtml(f.slug)}">
        <summary>
          <span class="kx-form-n">${i + 1}</span>
          <span class="kx-form-head">
            <span class="kx-form-name">${escHtml(f.form)}</span>
            <span class="kx-form-vs">confronts ${escHtml(f.asura)}</span>
            <span class="kx-form-obs">${escHtml(f.obstacle)} &mdash; ${escHtml(f.gloss)}</span>
          </span>
          <span class="kx-form-khanda">Khaṇḍa ${escHtml(String(f.khanda))}</span>
        </summary>
        <div class="kx-form-body">
          <!-- Art is referenced unconditionally and removes itself if the file
               is not there yet, so the page is correct before and after upload. -->
          <div class="kx-form-art">
            <figure><img src="/Images/ganapati/${escHtml(f.slug)}-form.jpg" alt="${escHtml(f.form)}"
              loading="lazy" onerror="this.closest('figure').remove()">
              <figcaption>${escHtml(f.form)}</figcaption></figure>
            <figure><img src="/Images/ganapati/${escHtml(f.slug)}-asura.jpg" alt="${escHtml(f.asura)}"
              loading="lazy" onerror="this.closest('figure').remove()">
              <figcaption>${escHtml(f.asura)}</figcaption></figure>
          </div>
          <p class="kx-form-hook">${escHtml(f.hook || '')}</p>
          <div class="kx-claim">
            ${sourceBadge('mula')}
            <p>${escHtml(f.mula || '')}</p>
          </div>
          ${f.note ? `<p class="kx-form-note"><strong>A distinction we keep:</strong> ${escHtml(f.note)}</p>` : ''}
          <div class="kx-claim">
            ${sourceBadge('drishti')}
            <p>${escHtml(f.drishti || '')}</p>
          </div>
          ${f.visual ? `<p class="kx-form-visual"><strong>How we picture it:</strong> ${escHtml(f.visual)}</p>` : ''}
        </div>
      </details>`).join('\n      ');

  return `<!DOCTYPE html>
<html lang="en">
${headBlock({ title: pageTitle, description: metaDesc, canonicalUrl, ogType: 'article',
  image: ogImageFor([season.ogImage]),
  extraJsonLd: [`<script type="application/ld+json">${JSON.stringify(ld)}</script>`,
                `<script type="application/ld+json">${JSON.stringify(crumbs)}</script>`].join('\n  ') })}
<body class="kx-season" data-kx-season="${escHtml(season.slug)}">
${navBlock()}
<main class="season-page">
${seasonHero(season, feature)}
${seasonNav(season, feature.slug)}

  <section class="kx-season-intro">
    <div class="kx-claim">
      ${sourceBadge('mula')}
      <p>${escHtml(feature.intro || '')}</p>
    </div>
    ${feature.caution ? `<p class="kx-caution"><strong>What we do not claim:</strong> ${escHtml(feature.caution)}</p>` : ''}
    ${provenancePanel(feature.sources)}
  </section>

  <section class="kx-forms">
    <h2>The eight manifestations</h2>
    <p class="kx-shelf-note">Open any one. Each has the story as the khaṇḍa tells it, and our reading kept visibly separate.</p>
    <div class="kx-forms-list">
      ${forms}
    </div>
  </section>

  ${feature.pattern ? `<section class="kx-pattern">
    <h2>What the eight share</h2>
    <div class="kx-claim">
      ${sourceBadge('drishti')}
      <p>${escHtml(feature.pattern)}</p>
    </div>
  </section>` : ''}

${joinBlock({
    cta: `season_${season.slug}_${feature.slug}`,
    heading: 'One story a week, with the sources',
    copy: 'Join free and we will send these one at a time, so the eight are not a wall of text — with a question to ask at the table.'
  })}

${sourceShelf(season)}
</main>
${footerBlock()}
</body>
</html>`;
}

function buildSeasonArticle(season, feature) {
  const canonicalUrl = `https://khatakshetra.com/${season.slug}/${feature.slug}`;
  const pageTitle = feature.seoTitle || feature.title;
  const metaDesc = truncate(feature.seoDescription || feature.hook, 155);

  const ld = {
    '@context': 'https://schema.org', '@type': 'Article',
    headline: pageTitle, description: metaDesc, url: canonicalUrl,
    publisher: { '@type': 'Organization', name: 'Khatakshetra', url: 'https://khatakshetra.com' },
    mainEntityOfPage: canonicalUrl
  };
  const crumbs = {
    '@context': 'https://schema.org', '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://khatakshetra.com/' },
      { '@type': 'ListItem', position: 2, name: season.title, item: `https://khatakshetra.com/${season.slug}` },
      { '@type': 'ListItem', position: 3, name: feature.navTitle || feature.title, item: canonicalUrl }
    ]
  };

  const sections = (feature.sections || []).map((sec) => `<section class="kx-sec">
        <h2>${escHtml(sec.heading)}</h2>
        <div class="kx-claim">
          ${sourceBadge(sec.sourceClass)}
          <p>${escHtml(sec.body)}</p>
        </div>
        ${provenancePanel(sec.sources, { heading: 'Exact source' })}
      </section>`).join('\n      ');

  return `<!DOCTYPE html>
<html lang="en">
${headBlock({ title: pageTitle, description: metaDesc, canonicalUrl, ogType: 'article',
  image: ogImageFor([season.ogImage]),
  extraJsonLd: [`<script type="application/ld+json">${JSON.stringify(ld)}</script>`,
                `<script type="application/ld+json">${JSON.stringify(crumbs)}</script>`].join('\n  ') })}
<body class="kx-season" data-kx-season="${escHtml(season.slug)}">
${navBlock()}
<main class="season-page">
${seasonHero(season, feature)}
${seasonNav(season, feature.slug)}

  <section class="kx-season-intro">
    <p class="kx-lede">${escHtml(feature.intro || '')}</p>
  </section>

      ${sections}

${joinBlock({
    cta: `season_${season.slug}_${feature.slug}`,
    heading: 'The stories, with their sources',
    copy: 'Join Khatakshetra Family free. One story at a time, the text it comes from named every time, and a question worth asking your children.'
  })}

${sourceShelf(season)}
</main>
${footerBlock()}
</body>
</html>`;
}


/**
 * The season challenge. The match-round pairs are DERIVED from the eight
 * manifestations rather than duplicated, so the game can never disagree with
 * the article. Game data is embedded as JSON (no extra fetch) and played by
 * /season-game.js, which keeps all state local — no answers or score ever
 * reach a URL or a server.
 */
function buildSeasonGame(season, feature) {
  const canonicalUrl = `https://khatakshetra.com/${season.slug}/${feature.slug}`;
  const pageTitle = feature.seoTitle || feature.title;
  const metaDesc = truncate(feature.seoDescription || feature.hook, 155);

  const formsFeature = season.features.find((f) => f.kind === 'forms');
  const pairs = ((formsFeature && formsFeature.forms) || []).map((f) => ({
    key: f.slug, form: f.form, asura: f.asura, obstacle: f.gloss || f.obstacle
  }));

  const gameData = JSON.stringify({
    slug: feature.slug,
    title: feature.title,
    intro: feature.intro,
    rounds: feature.rounds,
    tiers: feature.tiers,
    card: feature.card,
    shareText: feature.shareText,
    pairs
  }).replace(/</g, '\\u003c');   // safe to sit inside a <script> block

  const ld = {
    '@context': 'https://schema.org', '@type': 'Quiz',
    name: pageTitle, description: metaDesc, url: canonicalUrl,
    about: { '@type': 'Thing', name: season.title },
    publisher: { '@type': 'Organization', name: 'Khatakshetra', url: 'https://khatakshetra.com' }
  };
  const crumbs = {
    '@context': 'https://schema.org', '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://khatakshetra.com/' },
      { '@type': 'ListItem', position: 2, name: season.title, item: `https://khatakshetra.com/${season.slug}` },
      { '@type': 'ListItem', position: 3, name: feature.navTitle || feature.title, item: canonicalUrl }
    ]
  };

  return `<!DOCTYPE html>
<html lang="en">
${headBlock({ title: pageTitle, description: metaDesc, canonicalUrl, ogType: 'website',
  image: ogImageFor([season.ogImage]),
  extraJsonLd: [`<script type="application/ld+json">${JSON.stringify(ld)}</script>`,
                `<script type="application/ld+json">${JSON.stringify(crumbs)}</script>`].join('\n  ') })}
<body class="kx-season" data-kx-season="${escHtml(season.slug)}">
${navBlock()}
<main class="season-page">
${seasonHero(season, feature)}
${seasonNav(season, feature.slug)}

  <div id="kxGame" class="kg">
    <noscript><p class="kx-caution">This challenge needs JavaScript. The stories themselves do not &mdash;
      <a href="/${escHtml(season.slug)}/${escHtml(formsFeature ? formsFeature.slug : '')}">read the eight manifestations</a>.</p></noscript>
  </div>

${joinBlock({
    cta: `season_${season.slug}_${feature.slug}`,
    heading: 'Play the next one with them too',
    copy: 'Join Khatakshetra Family free. One story a week with its sources, a question to ask at the table, and the next season challenge when it lands.'
  })}

${sourceShelf(season)}
</main>
<script type="application/json" id="kxGameData">${gameData}</script>
${footerBlock()}
<script src="/season-game.js"></script>
</body>
</html>`;
}

/** '' when there is no season for this page — so pages without one are byte-identical. */
function onRampFor(kind, slug) {
  const banner = ONRAMP[kind] && ONRAMP[kind][slug];
  return banner ? `\n\n    ${banner}` : '';
}

/** A banner pointing an existing deity/festival page at the season it belongs to. */
function seasonOnRamp(season, label) {
  return `<section class="kx-onramp">
      <p class="kx-eyebrow">Season</p>
      <h2>${escHtml(season.title)}</h2>
      <p>${escHtml(season.thesis)}</p>
      <p><a class="kx-btn kx-btn-primary" href="/${escHtml(season.slug)}" data-kx-cta="onramp_${escHtml(label)}">Enter the season &rarr;</a></p>
    </section>`;
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
${headBlock({ title: pageTitle, description: metaDesc, canonicalUrl, ogType: 'article', extraJsonLd,
  image: ogImageFor([`Images/home/${slug}.jpg`, `Images/home/daily-${slug}.jpg`]) })}
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

    ${packSection}${onRampFor('deity', slug)}

    ${joinBlock({
      cta: `deity_${slug}`,
      heading: `Bring ${name} into your family's week`,
      copy: `Join free and we will send you one story at a time — with a question to ask your children and a page they can colour. Ten minutes, not homework.`
    })}
  </article>
</main>
${footerBlock()}
</body>
</html>`;

  return html;
}

// ── FESTIVAL PAGES ────────────────────────────────────────────────────────────

function buildFestivalPage(festival) {
  const { slug, title, date, story, quiz, coloring, kitCta, pack = null } = festival;
  const canonicalUrl = `https://khatakshetra.com/festival/${slug}`;

  // "August 28, 2026" → "2026-08-28" for the client-side countdown.
  const isoDate = (function () {
    const t = Date.parse(date);
    if (isNaN(t)) return '';
    const d = new Date(t);
    const p = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  })();

  // Deep-link straight to the first colouring sheet rather than dumping the
  // visitor on the studio index and making them hunt for the festival.
  const colouringLink = (pack && pack.colouring && pack.colouring.length)
    ? `/paint?page=${encodeURIComponent(pack.colouring[0].slug)}`
    : '';

  const shareText = (pack && pack.shareText) || `${title} 2026 — story, colouring and a family question, free at Khatakshetra.`;

  // The free pack itself: visible immediately (the doc is right that cold
  // traffic must see the value), with the printable PDF behind the email.
  const packSection = pack ? `
    <section class="kx-pack">
      <h2>What is in the free pack</h2>
      <ol class="kx-ritual">
        ${(pack.ritual || []).map((step) => `<li>${escHtml(step)}</li>`).join('\n        ')}
      </ol>

      <div class="kx-pack-grid">
        ${(pack.colouring || []).map((c) => `<a class="kx-pack-card" href="/paint?page=${encodeURIComponent(c.slug)}" data-kx-cta="festival_${escHtml(slug)}_colour">
          <span class="kx-pack-kind">Colour</span>
          <strong>${escHtml(c.title)}</strong>
          <span class="kx-pack-age">Ages ${escHtml(c.age)}</span>
        </a>`).join('\n        ')}
        ${quiz ? `<a class="kx-pack-card" href="/quiz-game.html?quiz=${escHtml(quiz)}" data-kx-cta="festival_${escHtml(slug)}_quiz">
          <span class="kx-pack-kind">Play</span>
          <strong>${escHtml(pack.quizLabel || (title + ' family quiz'))}</strong>
          <span class="kx-pack-age">All ages</span>
        </a>` : ''}
        ${pack.story ? `<a class="kx-pack-card" href="${escHtml(pack.story.href)}" data-kx-cta="festival_${escHtml(slug)}_story">
          <span class="kx-pack-kind">Read</span>
          <strong>${escHtml(pack.story.title)}</strong>
          <span class="kx-pack-age">Source-labelled</span>
        </a>` : ''}
      </div>

      <div class="kx-ask">
        <p class="kx-ask-label">Ask at the table</p>
        <p class="kx-ask-q">${escHtml(pack.familyQuestion)}</p>
      </div>

      ${pack.printable ? `<div class="kx-printable">
        <h3>Want it on paper?</h3>
        <p>The printable starter has every sheet in this pack, ready for the printer.</p>
        <form class="kx-join-form" data-signup-form data-cta="festival_${escHtml(slug)}_printable" data-reveal="printable-${escHtml(slug)}">
          <div class="kx-join-fields" data-signup-fields>
            <input type="email" name="email" placeholder="your@email.com" aria-label="Your email" required>
            <button class="kx-btn kx-btn-primary" type="submit">Send me the printable</button>
          </div>
          <p class="kx-status" data-status role="status"></p>
        </form>
        <div class="kx-reveal" id="printable-${escHtml(slug)}" hidden>
          <a class="kx-btn kx-btn-primary" href="${escHtml(pack.printable)}" download>Download the ${escHtml(title)} printable (PDF)</a>
          <button class="kx-btn" type="button" data-kx-share="${escHtml(shareText)}">Share with one family on WhatsApp</button>
          <a class="kx-btn" href="${SOCIAL.youtube}" target="_blank" rel="noopener" data-kx-social="festival_pack">Subscribe on YouTube</a>
        </div>
      </div>` : ''}
    </section>
` : '';

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
${headBlock({ title: pageTitle, description: metaDesc, canonicalUrl, ogType: 'article', extraJsonLd,
  image: ogImageFor([pack && pack.colouring && pack.colouring.length ? `Images/coloring/${pack.colouring[0].slug}.png` : '']) })}
<body>
${navBlock()}
<main class="festival-page">
  <article>
    <header class="entity-header">
      <p class="kx-eyebrow">${pack ? 'Free family pack' : 'Festival guide'}</p>
      <h1>${escHtml(title)}</h1>
      <p class="festival-date"><strong>2026:</strong> ${escHtml(date)}<span class="kx-countdown" data-kx-countdown="${escHtml(isoDate)}"></span></p>
    </header>

    <section class="entity-summary">
      <p>${escHtml(story)}</p>
      ${pack ? `<p class="festival-promise">${escHtml(pack.promise)}</p>` : ''}
    </section>
${packSection}
    <section class="festival-activities">
      <h2>${pack ? 'Keep going' : `Family activities for ${escHtml(title)}`}</h2>
      <ul class="cta-links">
        ${pack ? '' : (quiz ? `<li><a href="/quiz-game.html?quiz=${escHtml(quiz)}">Play the ${escHtml(title)} quiz</a></li>` : '')}
        ${pack ? '' : (coloring ? `<li><a href="/paint">Colouring activity: ${escHtml(coloring)}</a></li>` : '')}
        <li><a href="/daily">Today&rsquo;s katha &amp; puzzle</a></li>
        ${kitCta ? `<li><a href="/kits?kit=${escHtml(kitCta)}">See the ${escHtml(title)} keepsake kit</a></li>` : ''}
        <li><a href="/festivals">Browse all festivals</a></li>
      </ul>
    </section>${onRampFor('festival', slug)}

    ${joinBlock({
      cta: `festival_${slug}`,
      heading: pack ? `Get the free ${title} pack` : `Never miss a festival again`,
      copy: pack
        ? `One email and the whole pack opens on this page — story, colouring and the family question. We will send the next festival pack before it arrives.`
        : `Join free and we will send you the story, the colouring pages and the family question before each festival — in time to actually use them.`
    })}
  </article>
</main>
${footerBlock()}
<script>
  // "in N days" beside the date — a static page that still feels current.
  (function () {
    var el = document.querySelector('[data-kx-countdown]');
    if (!el) return;
    var target = new Date(el.getAttribute('data-kx-countdown') + 'T00:00:00');
    if (isNaN(target)) return;
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var days = Math.round((target - today) / 86400000);
    if (days > 1) el.textContent = ' — in ' + days + ' days';
    else if (days === 1) el.textContent = ' — tomorrow';
    else if (days === 0) el.textContent = ' — today';
  })();
</script>
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

    ${joinBlock({
      cta: `temple_${slug}`,
      heading: `Know the story before you stand there`,
      copy: `Join free and we will send the story behind the temple you are planning to visit — so the darshan means something to the children too.`
    })}
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

    ${joinBlock({
      cta: `story_${slug}`,
      heading: `One story like this, every week`,
      copy: `Join free and we will send the next one — with a question worth asking at dinner and a page your children can colour while you talk.`
    })}
  </article>
</main>
${footerBlock()}
</body>
</html>`;
}

// ── SITEMAP ───────────────────────────────────────────────────────────────────

function writeSitemap(entities, packBySlug, festivals, temples, stories, seasons = []) {
  const base = 'https://khatakshetra.com';
  const urls = [];
  const add = (loc, priority) => urls.push(`  <url><loc>${base}${loc}</loc><priority>${priority}</priority></url>`);
  add('/', '1.0');
  ['/stories', '/deities', '/games', '/festivals', '/temples'].forEach(u => add(u, '0.9'));
  // /start is the primary acquisition page; /kit and /paint are the free-value
  // pages campaigns point at. These had been hand-added to sitemap.xml, which
  // meant re-running this generator silently deleted them. Declared here so
  // regeneration is lossless.
  add('/start', '0.95'); add('/kits', '0.9'); add('/paint', '0.8'); add('/cards', '0.6');
  add('/daily', '0.9'); add('/which-character', '0.8'); add('/paths', '0.7');
  add('/kids-games', '0.8'); add('/daily-quiz', '0.8'); add('/leaderboard', '0.6'); add('/temple-tips', '0.8');
  add('/about', '0.6'); add('/contact', '0.5');
  ['/ramayana-journey', '/ramayana-path-game'].forEach(u => add(u, '0.8'));
  ['/booklets', '/drawing-kits', '/coloring-book-ramayana', '/storybook-ramayana', '/rama-navami-reader'].forEach(u => add(u, '0.7'));
  ['/sangraha', '/community'].forEach(u => add(u, '0.6'));
  ['ramayana-starter', 'dasharatha-meets-shani', 'ganesha-beginnings', 'dashavatara'].forEach(p => add(`/story-experience?pack=${p}`, '0.8'));
  entities.filter(e => e.type === 'Deity' || packBySlug[e.slug]).forEach(e => add(`/deity/${e.slug}`, '0.7'));
  festivals.forEach(f => add(`/festival/${f.slug}`, '0.8'));
  temples.forEach(t => add(`/temple/${t.slug}`, '0.8'));
  stories.forEach(s => add(`/story/${s.slug}`, '0.7'));
  seasons.forEach(se => {
    add(`/${se.slug}`, '0.9');
    (se.features || []).forEach(f => add(`/${se.slug}/${f.slug}`, '0.8'));
  });
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
  const seasons = fs.existsSync(path.join(CONTENT, 'seasons.json')) ? readJSON('seasons.json') : [];

  // The current season also appears in every footer.
  if (seasons.length) FOOTER_SEASON = { slug: seasons[0].slug, label: seasons[0].footerLabel || 'Ganapati' };

  // Register season on-ramps BEFORE the deity/festival pages render.
  for (const season of seasons) {
    for (const d of (season.onRamps && season.onRamps.deities) || []) ONRAMP.deity[d] = seasonOnRamp(season, 'deity');
    for (const f of (season.onRamps && season.onRamps.festivals) || []) ONRAMP.festival[f] = seasonOnRamp(season, 'festival');
  }

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

  // Season pages
  let seasonCount = 0;
  for (const season of seasons) {
    const dir = path.join(ROOT, season.slug);
    ensureDir(dir);
    fs.writeFileSync(path.join(dir, 'index.html'), buildSeasonHub(season), 'utf8');
    seasonCount++;
    for (const feature of season.features || []) {
      const html = feature.kind === 'forms' ? buildSeasonForms(season, feature)
                 : feature.kind === 'game' ? buildSeasonGame(season, feature)
                 : buildSeasonArticle(season, feature);
      fs.writeFileSync(path.join(dir, `${feature.slug}.html`), html, 'utf8');
      seasonCount++;
    }
  }

  // Sitemap: covers static pages + all generated entity/story pages.
  writeSitemap(entities, packBySlug, festivals, temples, stories, seasons);

  console.log(`Done.`);
  console.log(`  Deity pages:   ${deityCount}`);
  console.log(`  Festival pages: ${festivalCount}`);
  console.log(`  Temple pages:   ${templeCount}`);
  console.log(`  Story pages:    ${storyCount}`);
  console.log(`  Season pages:   ${seasonCount}`);
  console.log(`  Skipped:        ${skipped.length}`);
  console.log(`  sitemap.xml written.`);
  if (skipped.length) console.log(`  Skipped list:  ${skipped.join('; ')}`);
}

main();
