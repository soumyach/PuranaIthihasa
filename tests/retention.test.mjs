/**
 * Retention-loop tests: does completing something on the site lead anywhere?
 *
 * Run from the repo root:  npm i --no-save jsdom && node tests/retention.test.mjs
 *
 * Covers khatakshetraOfferNextStep() (the shared "what next" card), the merged
 * /kits page, and the quiz completion path.
 */
import { JSDOM } from 'jsdom';
import fs from 'fs';

const results = [];
const check = (n, p, d = '') => results.push([p, n, d]);

function boot(file, { inline = [], url = 'https://khatakshetra.com/x', member = false } = {}) {
  let html = fs.readFileSync(file, 'utf8');
  // generated pages use /site.js, hand-written ones use site.js
  html = html.replace(/<script src="\/?analytics.js"><\/script>/, '')
             .replace(/<script src="\/?site.js"><\/script>/, `<script>${fs.readFileSync('site.js','utf8')}</script>`);
  const dom = new JSDOM(html, {
    runScripts: 'dangerously', url,
    beforeParse(w) {
      w.fetch = (u, o) => {
        if (String(u).includes('content/quizzes.json')) return Promise.resolve({ json: () => Promise.resolve(JSON.parse(fs.readFileSync('content/quizzes.json','utf8'))) });
        if (String(u).includes('festival-pages-2026.json')) return Promise.resolve({ json: () => Promise.resolve(JSON.parse(fs.readFileSync('content/festival-pages-2026.json','utf8'))) });
        if (String(u).includes('daily.json')) return Promise.resolve({ json: () => Promise.resolve(JSON.parse(fs.readFileSync('content/daily.json','utf8'))) });
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      };
      w.trackKhatakshetraSignup = () => { w.__conv = (w.__conv || 0) + 1; };
      if (member) {
        w.localStorage.setItem('khatakshetra_profile', JSON.stringify({
          anonymous_id: 'a', email: 'already@member.com', xp: 0, level: 1,
          tracks: {}, unlocks: [], cards: [], events: []
        }));
      }
    }
  });
  return dom;
}

// ── the shared card itself, exercised through a generated page ──
async function testCard(member) {
  const dom = boot('deity/krishna.html', { member });
  const { window } = dom;
  window.document.dispatchEvent(new window.Event('DOMContentLoaded'));
  await new Promise(r => setTimeout(r, 40));
  const doc = window.document;
  const mount = doc.createElement('div'); mount.id = 'mount'; doc.body.appendChild(mount);
  window.eval(`khatakshetraOfferNextStep({
    mount: 'mount', context: 'quiz', cta: 'quiz_complete_krishna-beginner',
    heading: 'Want tomorrow\\u2019s story?', copy: 'Save your streak.', button: 'Save my streak',
    actions: [{ label: 'Daily', href: 'daily.html', kxCta: 'after_quiz_daily' },
              { label: 'Share', share: 'text', shareUrl: 'https://khatakshetra.com/' }]
  });`);
  const card = doc.querySelector('.kx-after[data-context="quiz"]');
  const label = member ? 'member' : 'anonymous';
  check(`[${label}] card renders`, !!card);
  check(`[${label}] email ask ${member ? 'skipped (we already have it)' : 'present'}`,
        member ? !card.querySelector('input[type=email]') : !!card.querySelector('input[type=email]'));
  check(`[${label}] next actions render`, card.querySelectorAll('.kx-after-actions .kx-after-btn').length === 2);
  check(`[${label}] share button uses the share handler`, !!card.querySelector('[data-kx-share]'));

  if (!member) {
    // the injected form must be live even though page-load wiring already ran
    card.querySelector('input[type=email]').value = 'new@fam.com';
    card.querySelector('form').dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
    await new Promise(r => setTimeout(r, 60));
    check('[anonymous] injected form actually submits', window.__conv === 1, 'conversions=' + window.__conv);
    check('[anonymous] status confirms', /in|Saved/.test(card.querySelector('[data-status]').textContent),
          JSON.stringify(card.querySelector('[data-status]').textContent));
  }
  // called twice → one card, not two
  window.eval(`khatakshetraOfferNextStep({ mount: 'mount', context: 'quiz', heading: 'again' });`);
  check(`[${label}] not duplicated when called twice`, doc.querySelectorAll('.kx-after[data-context="quiz"]').length === 1);
  dom.window.close();
}

// ── the merged /kits page ──
async function testKits() {
  const dom = boot('kits.html', { url: 'https://khatakshetra.com/kits?kit=ganesh_kit' });
  const { window } = dom;
  await new Promise(r => setTimeout(r, 120));
  const doc = window.document;
  const kits = doc.querySelectorAll('.kt-kit');
  check('kits page renders all three kits from the shared JSON', kits.length === 3, 'found ' + kits.length);
  check('  → rakhi sheets deep-link into the studio',
        !!doc.querySelector('#kit-raksha-bandhan a[href="paint.html?page=rakhi"]'));
  check('  → family question shown per kit', doc.querySelectorAll('.kt-ask').length === 3);
  check('  → ritual steps shown per kit', doc.querySelectorAll('.kt-ritual').length === 3);
  check('  → countdown rendered', /in \d+ days|tomorrow|today|has passed/.test(doc.querySelector('.kt-when').innerHTML),
        doc.querySelector('.kt-when').innerHTML);
  check('  → ?kit=ganesh_kit highlights the Ganesha kit',
        doc.getElementById('kit-ganesh-chaturthi').classList.contains('is-target'));
  check('  → physical-kit interest section present, framed as not on sale',
        !!doc.getElementById('physical') && /not on sale/i.test(doc.getElementById('physical').textContent));
  check('  → PDFs still gated behind the email form', doc.getElementById('ktDone').classList.contains('is-on') === false);
  dom.window.close();
}

// ── quiz page: finish a quiz and confirm the card lands in the result box ──
async function testQuizPage() {
  const dom = boot('quiz-game.html', { url: 'https://khatakshetra.com/quiz-game.html?quiz=krishna-beginner' });
  const { window } = dom;
  await new Promise(r => setTimeout(r, 120));
  const doc = window.document;
  check('quiz page loaded the Krishna quiz', /Krishna/i.test(doc.getElementById('quizTitle').textContent),
        doc.getElementById('quizTitle').textContent);
  window.eval('setLevel("beginner")');
  await new Promise(r => setTimeout(r, 30));
  window.eval('renderResult()');
  await new Promise(r => setTimeout(r, 60));
  const card = doc.querySelector('#resultBox .kx-after[data-context="quiz"]');
  check('finishing a quiz offers a next step', !!card);
  check('  → asks to save the streak', !!card && /streak/i.test(card.textContent));
  check('  → offers the daily katha', !!card && !!card.querySelector('[href="daily.html"]'));
  check('  → offers the 7-day journey', !!card && !!card.querySelector('[href="start.html"]'));
  dom.window.close();
}

await testCard(false);
await testCard(true);
await testKits();
await testQuizPage();

let fails = 0;
for (const [p, n, d] of results) { if (!p) fails++; console.log(`${p ? 'PASS' : 'FAIL'}  ${n}${!p && d ? '  → ' + d : ''}`); }
console.log(`\n${results.length - fails}/${results.length} passed`);
process.exit(fails ? 1 : 0);
