/**
 * Season pages (Ganapati pilot).  node tests/season.test.mjs
 *
 * The assertion that matters most: NO adhyaya/verse locator may reach a
 * published page while the source is unverified. Chapter numbering differs
 * between Puranic witnesses, so a wrong locator would destroy the source-first
 * credibility the whole season rests on. Verified sources get links; unverified
 * ones get khanda-level citation, the edition named, and a "book level" flag.
 */
import { JSDOM } from 'jsdom';
import fs from 'fs';
const results=[]; const check=(n,p,d='')=>results.push([p,n,d]);

const season = JSON.parse(fs.readFileSync('content/seasons.json','utf8'))[0];
const hub = fs.readFileSync('ganapati/index.html','utf8');
const eight = fs.readFileSync('ganapati/eight-manifestations.html','utf8');
const vighna = fs.readFileSync('ganapati/vighnaharta-vighnakarta.html','utf8');
const pages = { hub, eight, vighna };

// ── THE CITATION-HONESTY RULE ──
// Khaṇḍa level only for the Mudgala material: no adhyāya numbers, no deep links
// to a witness we have not checked.
// Test the VISIBLE TEXT, not raw HTML — otherwise viewport "initial-scale=1.0"
// reads as a verse locator.
const adhyaya = /Adhy[āa]ya|adhy[āa]ya\s*\d|\b\d+\.\d+\b|Khaṇḍa\s*\d+\s*,\s*\d|verses?\s*\d+[–-]\d+/;
for (const [name, html] of Object.entries(pages)) {
  const d0 = new JSDOM(html);
  const text = d0.window.document.body.textContent.replace(/\s+/g, ' ');
  check(`[${name}] publishes no adhyāya/verse locator`, !adhyaya.test(text),
        (text.match(adhyaya)||[])[0]);
  d0.window.close();
}
check('the Mudgala source is cited at khaṇḍa level', /Khaṇḍas 1–8/.test(eight));
check('  → and names the edition', /Shree Mudgal Puran Trust/.test(eight));
check('  → and is flagged "book level", not "checked"',
      /kx-prov-pending/.test(eight) && !/Mudgala[^<]*<[^>]*>\s*checked/.test(eight));
check('  → and offers NO link for the unchecked source',
      !/wisdomlib[^"]*mudgala|vedapath/i.test(eight));

// verified sources DO get links
check('the Skanda Purāṇa citation links to the checked edition',
      vighna.includes('https://www.wisdomlib.org/hinduism/book/the-skanda-purana/d/doc366013.html'));
check('the Gaṇeśa Purāṇa citation links to the checked edition',
      vighna.includes('https://www.wisdomlib.org/hinduism/book/the-ganesha-purana/d/doc116225.html'));
check('  → both marked checked', (vighna.match(/kx-prov-ok/g)||[]).length >= 2);

// ── the editorial rule the whole season rests on ──
check('our interpretation is visibly labelled as ours', /Drishti · our reading/.test(vighna));
check('  → and the text-based claims are labelled Mūla', /Mūla · what the text says/.test(vighna));
check('the "not the only eight avatars" caution is published', /not \\"?the only eight avatars|not "the only eight avatars/i.test(eight) || /These are not/.test(eight));
check('mount nuances are preserved (Vikata peacock vs mouse)', /peacock/.test(eight) && /mouse/.test(eight));
check('Dhūmraketu is distinguished from Dhūmravarṇa', /Dhūmraketu/.test(eight));

// ── structure / a11y / plumbing ──
const dom = new JSDOM(eight, { url: 'https://khatakshetra.com/ganapati/eight-manifestations' });
const doc = dom.window.document;
check('all eight forms render', doc.querySelectorAll('article.kx-form').length === 8,
      String(doc.querySelectorAll('article.kx-form').length));
// The paintings are the reason the page exists. They used to sit inside eight
// collapsed rows, invisible until clicked — this is the assertion that stops
// them being hidden again.
check('  → each shows its painting without any interaction',
      doc.querySelectorAll('article.kx-form > .kx-form-shot > img').length === 8 &&
      !doc.querySelector('details > .kx-form-shot'));
check('  → the long reading stays folded, as native <details>',
      doc.querySelectorAll('article.kx-form details.kx-form-more > summary').length === 8);
check('  → and story_open tracking still has its hook on the toggle',
      doc.querySelectorAll('details.kx-form-more[data-kx-form]').length === 8);
check('  → each is deep-linkable by id', doc.querySelectorAll('article.kx-form[id]').length === 8);
check('  → each names its khaṇḍa', doc.querySelectorAll('.kx-form-khanda').length === 8);
check('  → the adversary portrait is the reward for opening it',
      doc.querySelectorAll('details.kx-form-more .kx-form-asura img').length === 8);
check('  → each separates Mūla from Drishti', doc.querySelectorAll('.sc-mula').length >= 8 && doc.querySelectorAll('.sc-drishti').length >= 8);
dom.window.close();

for (const [name, html] of Object.entries(pages)) {
  const d = new JSDOM(html);
  const doc2 = d.window.document;
  check(`[${name}] has tracking + the join form`,
        html.includes('/analytics.js') && html.includes('/site.js') && !!doc2.querySelector('[data-signup-form]'));
  check(`[${name}] has one gtag, a canonical and JSON-LD`,
        (html.match(/googletagmanager.com\/gtag/g)||[]).length === 1 &&
        !!doc2.querySelector('link[rel=canonical]') &&
        doc2.querySelectorAll('script[type="application/ld+json"]').length >= 2);
  check(`[${name}] leaks no unresolved template literal`, !html.includes('${'));
  d.window.close();
}

// ── on-ramps: existing pages point at the season, no parallel URL tree ──
const ganesha = fs.readFileSync('deity/ganesha.html','utf8');
const gc = fs.readFileSync('festival/ganesh-chaturthi.html','utf8');
check('/deity/ganesha links into the season', /class="kx-onramp"/.test(ganesha) && /href="\/ganapati"/.test(ganesha));
check('/festival/ganesh-chaturthi links into the season', /class="kx-onramp"/.test(gc) && /href="\/ganapati"/.test(gc));
const other = fs.readFileSync('deity/krishna.html','utf8');
check('  → and an unrelated deity page does NOT', !/kx-onramp/.test(other));

// ── sitemap ──
const sm = fs.readFileSync('sitemap.xml','utf8');
check('sitemap lists the season hub', sm.includes('<loc>https://khatakshetra.com/ganapati</loc>'));
check('  → and both features', sm.includes('/ganapati/eight-manifestations') && sm.includes('/ganapati/vighnaharta-vighnakarta'));

// ── the data model is season-generic (Navaratri reuse) ──
check('the content model is a LIST of seasons, not ganapati-specific',
      Array.isArray(JSON.parse(fs.readFileSync('content/seasons.json','utf8'))));
check('  → and features declare their own kind (forms/article/game)',
      season.features.every(f => ['forms','article','game'].includes(f.kind)));

// ── DISCOVERY: can a real visitor actually reach the season? ──
const home = fs.readFileSync('index.html','utf8');
check('the homepage has a season band linking to /ganapati',
      /class="strip season"/.test(home) && /href="\/ganapati"/.test(home));
check('  → and a nav entry', /nav-links[\s\S]{0,400}href="\/ganapati"/.test(home));
check('the festivals hub points at the season', /href="\/ganapati"/.test(fs.readFileSync('festivals.html','utf8')));
check('the injected footer carries the season', /\['\/ganapati', 'Ganapati'\]/.test(fs.readFileSync('site.js','utf8')));
check('the generated footer carries the season', /href="\/ganapati">Ganapati<\/a>/.test(hub));
check('finishing the daily offers the season', /after_daily_season/.test(fs.readFileSync('daily.js','utf8')));

// ── every generated page must be shareable (no blank grey card) ──
const gen = ['ganapati/index.html','ganapati/eight-manifestations.html','ganapati/vighnaharta-vighnakarta.html',
             'deity/ganesha.html','deity/krishna.html','festival/raksha-bandhan.html','festival/diwali.html',
             'story/ganesha-elephant-head.html','temple/jagannath-puri.html'];
let missing = gen.filter(f => !/og:image" content="https:\/\/khatakshetra.com\/Images\//.test(fs.readFileSync(f,'utf8')));
check('every sampled generated page has an og:image', missing.length === 0, missing.join(', '));
check('  → and a matching twitter:image',
      gen.every(f => /twitter:image" content="https:\/\/khatakshetra.com\/Images\//.test(fs.readFileSync(f,'utf8'))));
check('  → the deity page uses that deity\'s own portrait',
      /og:image" content="[^"]*daily-ganesha\.jpg|og:image" content="[^"]*home\/ganesha\.jpg/.test(fs.readFileSync('deity/ganesha.html','utf8')));
check('  → and a page with no portrait falls back rather than breaking',
      /og:image" content="[^"]*fullbleed-lamps\.jpg/.test(fs.readFileSync('story/ganesha-elephant-head.html','utf8')));

// ── artwork: referenced now, degrades until the files are uploaded ──
check('each of the eight shows a form portrait',
      (eight.split('kx-forms-list')[1].match(/-form\.jpg/g)||[]).length === 8);
check('  → and its adversary', (eight.match(/-asura\.jpg/g)||[]).length === 8);
check('  → every image degrades if the file is missing',
      (eight.match(/onerror="this\.closest\('figure'\)\.remove\(\)"/g)||[]).length === 8 &&
      (eight.match(/onerror="this\.closest\('\.kx-form-shot'\)\.classList\.add\('is-bare'\)"/g)||[]).length === 8,
      String((eight.match(/onerror=/g)||[]).length));
check('the hub rail carries thumbnails that also degrade',
      (hub.match(/kx-rail-art/g)||[]).length === 8 && /onerror="this\.remove\(\)"/.test(hub));
check('art paths follow the slug convention',
      /\/Images\/ganapati\/vakratunda-matsarasura-form\.jpg/.test(eight) &&
      /\/Images\/ganapati\/dhumravarna-ahamkarasura-asura\.jpg/.test(eight));

// ── hub layout: the full-bleed hero band, and the mooshika ──
check('the hub uses the wide layout, the articles do not',
      /<main class="season-page is-hub"/.test(hub) && !/is-hub/.test(eight));
check('  → and the two-column hero has its own name, used by both',
      /kx-season-hero is-split/.test(hub) && /kx-season-hero is-split/.test(eight));
check('the hub hero is a full-bleed band',
      /<header class="kx-hero-band">/.test(hub) && /kx-hero-band-inner/.test(hub));
check('  → two columns, with the artwork',
      /kx-season-hero is-split/.test(hub) && /kx-hero-art/.test(hub) &&
      /<img src="\/Images\/home\/ganesha\.jpg"/.test(hub));
check('  → and the hero image degrades rather than leaving a hole',
      /onerror="this\.closest\('\.kx-hero-art'\)\.classList\.add\('is-bare'\)"/.test(hub));
check('the intro and the three badges are folded into the band',
      /kx-hero-foot/.test(hub) && !/kx-season-intro/.test(hub) &&
      /kx-hero-foot[\s\S]{0,900}kx-season-legend/.test(hub));
check('  → and the badges are not also left duplicated below it',
      (hub.match(/kx-season-legend/g)||[]).length === 1);

// The mooshika is a painted cutout, committed as base64 so it needs no binary
// and no extra request. A flat vector mouse beside a devotional painting
// reads as clipart — that is the bug this replaced.
check('the mooshika is painted artwork, not an inline vector drawing',
      /kx-moo-body/.test(hub) && !/<svg[^>]*>[\s\S]{0,400}kx-moo/.test(hub));
check('  → its image is inlined, so it costs no extra request',
      /\.kx-moo-body\{background-image:url\(data:image\/webp;base64,/.test(hub));
check('  → and it stays small enough to inline (< 30KB of base64)',
      fs.readFileSync('assets/mooshika-b64.txt','utf8').trim().length < 30000,
      String(fs.readFileSync('assets/mooshika-b64.txt','utf8').trim().length));
check('the mooshika appears on the hub only',
      /kx-mooshika/.test(hub) && !/kx-mooshika/.test(eight) && !/kx-mooshika/.test(vighna));
check('  → and is decorative, not announced to screen readers',
      /<div class="kx-mooshika" aria-hidden="true">/.test(hub));
{
  const css = fs.readFileSync('seo.css','utf8');
  check('the scurry runs once and settles, never loops',
        /animation:\s*kx-moo-run[^;]*forwards/.test(css) && !/kx-moo-run[^;]*infinite/.test(css));
  // The bug this guards: two transform animations on one element, the later
  // one with `both`, fills backwards through its delay and cancels the bob.
  check('  → the look-up does not fill backwards over the scurry',
        !/kx-moo-look[^;]*\bboth\b/.test(css) && /kx-moo-look[^;]*forwards/.test(css));
  check('  → the body bobs and a shadow squashes with it',
        /@keyframes kx-moo-scurry/.test(css) && /@keyframes kx-moo-shadow/.test(css));
  check('  → and motion-sensitive visitors get him at rest',
        /prefers-reduced-motion[\s\S]{0,400}kx-mooshika\s*{\s*animation:\s*none/.test(css));
  check('the full-bleed band cannot produce a horizontal scrollbar',
        /body\.kx-season\s*{\s*overflow-x:\s*clip/.test(css));
  check('the hub is allowed to be wider than an article column',
        /\.season-page\.is-hub\s*{\s*max-width:\s*1280px/.test(css));
  check('  → and its grids reflow instead of stranding one card',
        /\.is-hub \.kx-feat-grid[\s\S]{0,200}auto-fit/.test(css) &&
        /\.is-hub \.kx-rail[\s\S]{0,200}auto-fit/.test(css));
  check('  → the hero stacks on a phone',
        /max-width:\s*860px\)[\s\S]{0,400}\.kx-season-hero\.is-split\s*{\s*grid-template-columns:\s*1fr/.test(css));
}

// ── article pages: the same band, and a gallery that uses the width ──
check('article pages get the hero band too',
      /<header class="kx-hero-band is-article">/.test(eight) &&
      /<header class="kx-hero-band is-article">/.test(vighna));
check('  → the forms page leads with its own first painting',
      /kx-hero-band[\s\S]{0,600}vakratunda-matsarasura-form\.jpg/.test(eight));
check('  → but the mooshika stays the season home\'s alone',
      !/kx-mooshika/.test(eight) && !/kx-mooshika/.test(vighna));
check('the band sits outside <main>, so it needs no 100vw',
      /<header class="kx-hero-band[^"]*">[\s\S]*?<main class="season-page/.test(hub) &&
      /<header class="kx-hero-band[^"]*">[\s\S]*?<main class="season-page/.test(eight));
check('the gallery steps outside the reading column',
      /<section class="kx-forms kx-breakout">/.test(eight));
{
  const css = fs.readFileSync('seo.css','utf8');
  check('  → and is capped against the viewport, so it cannot scroll sideways',
        /\.kx-breakout\s*{[\s\S]{0,160}width:\s*min\(1180px,\s*calc\(100vw - 40px\)\)/.test(css));
  check('  → the band is plain full width now, not 100vw',
        /\.kx-hero-band\s*{[\s\S]{0,200}width:\s*100%/.test(css) &&
        !/\.kx-hero-band\s*{[\s\S]{0,200}width:\s*100vw/.test(css));
  check('  → cards in a row share a height',
        /\.kx-forms\.kx-breakout \.kx-forms-list[\s\S]{0,260}align-items:\s*stretch/.test(css));
}

let fails=0; for (const [p,n,d] of results){ if(!p) fails++; console.log(`${p?'PASS':'FAIL'}  ${n}${!p&&d?'  → '+d:''}`);}
console.log(`\n${results.length-fails}/${results.length} passed`); process.exit(fails?1:0);
