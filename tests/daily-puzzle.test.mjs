/**
 * Daily puzzle interaction tests:
 *
 *   npm i --no-save jsdom && node tests/daily-puzzle.test.mjs
 *
 * Covers incremental clue reveal (the card must NOT be rebuilt), the styled
 * pips that replaced the emoji squares, repeated guesses costing nothing, the
 * reveal state, and — the important one — a correct guess still resolving when
 * localStorage throws.
 */
import { JSDOM } from 'jsdom';
import fs from 'fs';
const results=[]; const check=(n,p,d='')=>results.push([p,n,d]);

const daily = JSON.parse(fs.readFileSync('content/daily.json','utf8'));
const today = (d=>d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'))(new Date());
const entry = JSON.parse(JSON.stringify(daily[4])); // Shani — the one in the screenshot
entry.date = today;

async function boot(blockStorage) {
  let html = fs.readFileSync('daily.html','utf8')
    .replace(/<script src="\/?analytics.js"><\/script>/, '')
    .replace(/<script src="\/?site.js"><\/script>/, `<script>${fs.readFileSync('site.js','utf8')}</script>`)
    .replace(/<script src="\/?daily.js"><\/script>/, `<script>${fs.readFileSync('daily.js','utf8')}</script>`);
  const dom = new JSDOM(html, { runScripts:'dangerously', url:'https://khatakshetra.com/daily', pretendToBeVisual:true,
    beforeParse(w){
      w.fetch = (u) => String(u).includes('daily.json')
        ? Promise.resolve({ json: async () => [entry] })
        : Promise.resolve({ ok:true, json: async () => ({}) });
      w.HTMLCanvasElement.prototype.getContext = () => ({ clearRect(){}, save(){}, translate(){}, rotate(){}, fillRect(){}, restore(){} });
      if (blockStorage) {
        // Reproduce Safari private browsing / in-app webviews, where merely
        // touching localStorage throws SecurityError.
        Object.defineProperty(w, 'localStorage', {
          configurable: true,
          get() { throw new Error("SecurityError: the document is sandboxed"); }
        });
      }
    }});
  dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
  await new Promise(r=>setTimeout(r,120));
  return dom;
}
const guess = async (w, text) => {
  w.document.getElementById('dqInput').value = text;
  w.document.getElementById('dqForm').dispatchEvent(new w.Event('submit', { bubbles:true, cancelable:true }));
  await new Promise(r=>setTimeout(r,80));
};

let dom = await boot(); let w = dom.window, doc = w.document;

// ── initial state ──
check('one clue shown at the start', doc.querySelectorAll('.dq-clue').length === 1);
check('clues are numbered', /Clue 1/.test(doc.querySelector('.dq-clue-n').textContent));
check('five styled pips, not emoji squares', doc.querySelectorAll('.dq-pip').length === 5);
check('no ⬜/🟩 emoji anywhere in the UI', !/⬜|🟩/.test(doc.getElementById('dailyApp').textContent));
check('guesses-left counter shown', /5 guesses/.test(doc.getElementById('dqLeft').textContent), doc.getElementById('dqLeft').textContent);
check('the lesson stays hidden until the end', doc.getElementById('dqLesson').hidden === true);
check('status announcements are live for screen readers',
      doc.getElementById('dqMsg').getAttribute('aria-live') === 'polite');

// ── a wrong guess ──
const cardBefore = doc.querySelector('.card.featured');
await guess(w, 'Rama');
check('a wrong guess appends a SECOND clue', doc.querySelectorAll('.dq-clue').length === 2);
check('  → the new clue is tagged "new"', !!doc.querySelector('.dq-clue.is-new .dq-clue-tag'));
check('  → the older clue is dimmed, not tagged',
      doc.querySelectorAll('.dq-clue')[0].classList.contains('is-old') &&
      !doc.querySelectorAll('.dq-clue')[0].querySelector('.dq-clue-tag'));
check('  → the katha card above is NOT rebuilt (no blink)', doc.querySelector('.card.featured') === cardBefore);
check('  → one pip marked wrong', doc.querySelectorAll('.dq-pip.is-wrong').length === 1);
check('  → the guess is recorded as a chip so it is not repeated',
      doc.querySelector('.dq-chip') && doc.querySelector('.dq-chip').textContent === 'Rama');
check('  → the message names what failed and what is left',
      /Not Rama/.test(doc.getElementById('dqMsg').textContent) && /4 guesses left/.test(doc.getElementById('dqMsg').textContent),
      doc.getElementById('dqMsg').textContent);
check('  → the input is cleared and refocused',
      doc.getElementById('dqInput').value === '' && doc.activeElement === doc.getElementById('dqInput'));

// ── repeating a guess must not cost an attempt ──
await guess(w, 'rama');
check('a repeated guess costs no attempt', doc.querySelectorAll('.dq-pip.is-wrong').length === 1);
check('  → and says so', /already tried/i.test(doc.getElementById('dqMsg').textContent), doc.getElementById('dqMsg').textContent);
check('  → clue count unchanged', doc.querySelectorAll('.dq-clue').length === 2);

// ── an accepted alias counts as correct ──
await guess(w, 'Saturn');   // entry.accept includes Saturn for Shani
check('an accepted alias solves it', doc.querySelector('.dq-pip.is-right') !== null);
check('  → the reveal appears', doc.getElementById('dqEnd').hidden === false);
check('  → the answer is shown large', /Shani/.test(doc.querySelector('.dq-answer').textContent));
check('  → the deity artwork is shown', !!doc.querySelector('.dq-art img'), 'art missing');
check('  → the form is hidden once finished', doc.getElementById('dqForm').hidden === true);
check('  → the lesson is now revealed', doc.getElementById('dqLesson').hidden === false);
// Rama (1) + the ignored repeat + Saturn (2) = two attempts, which is the point:
// the repeat genuinely did not cost a guess.
check('  → "Solved in 2 guesses" — the repeat did not count',
      /Solved in 2 guesses/.test(doc.getElementById('dqEnd').textContent), doc.querySelector('.dq-verdict').textContent);
check('  → share text still uses the emoji grid (right for WhatsApp)',
      /⬜|🟩/.test(doc.getElementById('dqShareText').value), doc.getElementById('dqShareText').value);
check('  → WhatsApp link built', (doc.getElementById('dqWa').href||'').startsWith('https://wa.me/?text='));
check('  → next-step card offered', !!doc.querySelector('.kx-after[data-context="daily"]'));
dom.window.close();

// ── running out of guesses ──
dom = await boot(); w = dom.window; doc = w.document;
for (const g of ['Rama','Krishna','Durga','Ganesha','Hanuman']) await guess(w, g);
check('five wrong guesses ends the puzzle', doc.getElementById('dqEnd').hidden === false);
check('  → all four clues were revealed along the way', doc.querySelectorAll('.dq-clue').length === 4, String(doc.querySelectorAll('.dq-clue').length));
check('  → the answer is revealed warmly, not as "Revealed"',
      /the clues pointed to Shani/i.test(doc.querySelector('.dq-verdict').textContent), doc.querySelector('.dq-verdict').textContent);
check('  → status reads "The answer was…"', /answer was/i.test(doc.getElementById('dqStatus').textContent), doc.getElementById('dqStatus').textContent);
check('  → out-of-guesses shown on the counter', /Out of guesses/.test(doc.getElementById('dqLeft').textContent));
check('  → five wrong pips', doc.querySelectorAll('.dq-pip.is-wrong').length === 5);
dom.window.close();

// ── storage blocked (Safari private mode, in-app webviews) ──
dom = await boot(true); w = dom.window; doc = w.document;
check('[storage blocked] the puzzle still loads', doc.querySelectorAll('.dq-clue').length === 1);
await guess(w, 'Rama');
check('[storage blocked] a wrong guess still adds a clue', doc.querySelectorAll('.dq-clue').length === 2);
await guess(w, 'Shani');
check('[storage blocked] a CORRECT guess still reveals the answer', doc.getElementById('dqEnd').hidden === false);
check('[storage blocked]   → the answer is shown', /Shani/.test((doc.querySelector('.dq-answer')||{}).textContent||''), 'no answer element');
dom.window.close();

let fails=0; for (const [p,n,d] of results){ if(!p) fails++; console.log(`${p?'PASS':'FAIL'}  ${n}${!p&&d?'  → '+d:''}`);}
console.log(`\n${results.length-fails}/${results.length} passed`); process.exit(fails?1:0);
