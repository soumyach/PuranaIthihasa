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
check('all eight forms render', doc.querySelectorAll('details.kx-form').length === 8,
      String(doc.querySelectorAll('details.kx-form').length));
check('  → as native <details>, so keyboard + no-JS both work',
      doc.querySelectorAll('details.kx-form > summary').length === 8);
check('  → each is deep-linkable by id', doc.querySelectorAll('details.kx-form[id]').length === 8);
check('  → each names its khaṇḍa', doc.querySelectorAll('.kx-form-khanda').length === 8);
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
check('  → and features declare their own kind (forms/article)',
      season.features.every(f => ['forms','article'].includes(f.kind)));

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

let fails=0; for (const [p,n,d] of results){ if(!p) fails++; console.log(`${p?'PASS':'FAIL'}  ${n}${!p&&d?'  → '+d:''}`);}
console.log(`\n${results.length-fails}/${results.length} passed`); process.exit(fails?1:0);
