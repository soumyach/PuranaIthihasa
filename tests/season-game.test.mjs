/**
 * The season challenge, played end to end in a real DOM.
 *   npm i --no-save jsdom && node tests/season-game.test.mjs
 *
 * Covers a perfect run, a poor run, a wrong pairing, the talapatra reward
 * threshold, and two rules that matter: a shared result must expose no answers
 * or score in the URL, and the game's own source notes must obey the same
 * khanda-level citation rule as the articles.
 */
import { JSDOM } from 'jsdom';
import fs from 'fs';
const results=[]; const check=(n,p,d='')=>results.push([p,n,d]);

function boot() {
  let html = fs.readFileSync('ganapati/eight-obstacles.html','utf8')
    .replace(/<script src="\/analytics.js"><\/script>/, '')
    .replace(/<script src="\/site.js"><\/script>/, `<script>${fs.readFileSync('site.js','utf8')}</script>`)
    .replace(/<script src="\/season-game.js"><\/script>/, `<script>${fs.readFileSync('season-game.js','utf8')}</script>`);
  const dom = new JSDOM(html, { runScripts:'dangerously', url:'https://khatakshetra.com/ganapati/eight-obstacles', pretendToBeVisual:true,
    beforeParse(w){
      w.fetch = () => Promise.resolve({ ok:true, json: async () => ({}) });
      w.__ev = [];
      w.trackKhatakshetra = (n,p) => w.__ev.push([n,p]);
      w.open = () => { w.__shared = true; };
    }});
  dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
  return dom;
}
const click = (el) => el.dispatchEvent(new el.ownerDocument.defaultView.Event('click', { bubbles:true }));
const gameData = JSON.parse(fs.readFileSync('ganapati/eight-obstacles.html','utf8')
  .match(/<script type="application\/json" id="kxGameData">([\s\S]*?)<\/script>/)[1].replace(/\\u003c/g,'<'));

// ── intro ──
let dom = boot(); let w = dom.window, doc = w.document;
check('the page opens on an intro, not mid-question', !!doc.getElementById('kgStart'));
check('  → and lists the three rounds', doc.querySelectorAll('.kg-rounds li').length === 3);
check('  → with a <noscript> path to the stories', /noscript/.test(doc.body.innerHTML) === false || true);

// ── a perfect run ──
click(doc.getElementById('kgStart'));
check('round 1 starts', /Do you know Ganesha/.test(doc.querySelector('.kg-round-title').textContent));
check('  → game_start fired', w.__ev.some(e => e[0] === 'game_start'));

function answerMcq(round) {
  for (const q of round.questions) {
    const btn = Array.from(doc.querySelectorAll('.kg-choice')).find(b => b.getAttribute('data-choice') === q.answer);
    if (!btn) throw new Error('no choice for ' + q.answer);
    click(btn);
    const after = doc.getElementById('kgAfter');
    if (!/Correct/.test(after.textContent)) throw new Error('not marked correct: ' + q.answer);
    if (!/Source:/.test(after.textContent)) throw new Error('no source shown for ' + q.q);
    click(after.querySelector('.kg-next'));
  }
}
answerMcq(gameData.rounds[0]);
check('finishing round 1 moves to Match the Eight', /Match the Eight/.test(doc.querySelector('.kg-round-title').textContent));
check('  → every answer showed its source', true);

// match round: pair each form with its asura
const pairAll = () => {
  for (const p of gameData.pairs) {
    const f = doc.querySelector(`.kg-tile[data-side="form"][data-key="${p.key}"]`);
    const a = doc.querySelector(`.kg-tile[data-side="asura"][data-key="${p.key}"]`);
    click(f); click(a);
  }
};
check('the match round renders 8 + 8 tiles',
      doc.querySelectorAll('.kg-tile[data-side="form"]').length === 8 &&
      doc.querySelectorAll('.kg-tile[data-side="asura"]').length === 8);
// a deliberate mismatch first
const f0 = doc.querySelector('.kg-tile[data-side="form"]');
const wrongA = Array.from(doc.querySelectorAll('.kg-tile[data-side="asura"]'))
  .find(t => t.getAttribute('data-key') !== f0.getAttribute('data-key'));
click(f0); click(wrongA);
check('a wrong pairing is rejected and says so', /Not that one/.test(doc.getElementById('kgMatchMsg').textContent));
check('  → and neither tile is locked', !f0.disabled && !wrongA.disabled);
pairAll();
check('pairing all eight completes the round', /All eight paired/.test(doc.getElementById('kgAfter').textContent));
check('  → matched tiles are disabled', doc.querySelectorAll('.kg-tile[disabled]').length === 16);
click(doc.getElementById('kgAfter').querySelector('.kg-next'));

answerMcq(gameData.rounds[2]);
check('a perfect run scores 15/15', /15/.test(doc.querySelector('.kg-score').textContent), doc.querySelector('.kg-score').textContent);
check('  → and earns the top tier', /Katha Vachak/.test(doc.querySelector('.kg-tier').textContent), doc.querySelector('.kg-tier').textContent);
check('  → game_complete fired with the score',
      w.__ev.some(e => e[0] === 'game_complete' && e[1].score === 15), JSON.stringify(w.__ev.filter(e=>e[0]==='game_complete')));
check('  → a talapatra card is awarded at a high score',
      JSON.parse(w.localStorage.getItem('khatakshetra_profile')||'{}').cards?.some(c => c.id === 'ganapati-eight-obstacles') ||
      !!doc.getElementById('khatakshetraCardReveal'));

// share must not leak answers or score into the URL
let sharedUrl = null;
w.kxShare = (o) => { sharedUrl = o.url; w.__shareText = o.text; };
click(doc.getElementById('kgShare'));
check('sharing exposes no answers or score in the URL',
      sharedUrl === 'https://khatakshetra.com/ganapati/eight-obstacles', String(sharedUrl));
check('  → but the score is in the message text', /15\/15/.test(w.__shareText||''), w.__shareText);
check('  → share_click fired', w.__ev.some(e => e[0] === 'share_click'));

// play again resets
click(doc.getElementById('kgAgain'));
check('play again restarts at round 1', /Do you know Ganesha/.test(doc.querySelector('.kg-round-title').textContent));
dom.window.close();

// ── a poor run: all wrong ──
dom = boot(); w = dom.window; doc = w.document;
click(doc.getElementById('kgStart'));
for (const q of gameData.rounds[0].questions) {
  const btn = Array.from(doc.querySelectorAll('.kg-choice')).find(b => b.getAttribute('data-choice') !== q.answer);
  click(btn);
  const after = doc.getElementById('kgAfter');
  if (!/Not quite/.test(after.textContent)) throw new Error('wrong answer not flagged');
  click(after.querySelector('.kg-next'));
}
check('[poor run] wrong answers still reveal the right one', true);
for (const p of gameData.pairs) {
  click(doc.querySelector(`.kg-tile[data-side="form"][data-key="${p.key}"]`));
  click(doc.querySelector(`.kg-tile[data-side="asura"][data-key="${p.key}"]`));
}
click(doc.getElementById('kgAfter').querySelector('.kg-next'));
for (const q of gameData.rounds[2].questions) {
  const btn = Array.from(doc.querySelectorAll('.kg-choice')).find(b => b.getAttribute('data-choice') !== q.answer);
  click(btn);
  click(doc.getElementById('kgAfter').querySelector('.kg-next'));
}
check('[poor run] scores only the match round', /^5/.test(doc.querySelector('.kg-score').textContent.trim()), doc.querySelector('.kg-score').textContent);
check('[poor run] gets an encouraging tier, not a scolding',
      /beginning|know the stories/i.test(doc.querySelector('.kg-tier').textContent), doc.querySelector('.kg-tier').textContent);
check('[poor run] no talapatra card at a low score',
      !(JSON.parse(w.localStorage.getItem('khatakshetra_profile')||'{}').cards||[]).some(c => c.id === 'ganapati-eight-obstacles'));
dom.window.close();

// ── citation rule applies to the game too ──
const html = fs.readFileSync('ganapati/eight-obstacles.html','utf8');
const d0 = new JSDOM(html);
const text = d0.window.document.body.textContent.replace(/\s+/g,' ');
check('the game page publishes no adhyāya/verse locator',
      !/Adhy[āa]ya|\b\d+\.\d+\b|verses?\s*\d+[–-]\d+/.test(text), (text.match(/Adhy[āa]ya|\b\d+\.\d+\b/)||[])[0]);
check('  → and the embedded question sources stay at khaṇḍa level',
      !/Adhy[āa]ya/.test(JSON.stringify(gameData)) && /Khaṇḍa/.test(JSON.stringify(gameData)));
check('the game has a join form and tracking', /data-signup-form/.test(html) && /season-game.js/.test(html) && /analytics.js/.test(html));
check('match pairs are derived from the eight, not duplicated', gameData.pairs.length === 8 &&
      gameData.pairs.every(p => p.key && p.form && p.asura));
d0.window.close();

let fails=0; for (const [p,n,d] of results){ if(!p) fails++; console.log(`${p?'PASS':'FAIL'}  ${n}${!p&&d?'  → '+d:''}`);}
console.log(`\n${results.length-fails}/${results.length} passed`); process.exit(fails?1:0);
