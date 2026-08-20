/**
 * Raksha Bandhan quiz tests. Content sanity (answers are among their own
 * choices, no duplicate options, no Krishna-quiz leftovers) plus a full
 * playthrough in a real DOM:
 *
 *   npm i --no-save jsdom && node tests/rakhi-quiz.test.mjs
 */
import { JSDOM } from 'jsdom';
import fs from 'fs';

const results = []; const check = (n,p,d='') => results.push([p,n,d]);
const quizzes = JSON.parse(fs.readFileSync('content/quizzes.json','utf8'));
const rakhi = quizzes.find(q => q.slug === 'raksha-bandhan-beginner');

// ── content sanity: no Krishna-quiz leftovers, well-formed questions ──
check('rakhi quiz exists', !!rakhi);
check('has 6 questions', rakhi.questions.length === 6, String(rakhi.questions.length));
check('every question has 4 choices', rakhi.questions.every(q => q.choices.length === 4));
check('every answer is one of its own choices', rakhi.questions.every(q => q.choices.includes(q.answer)));
check('every question has an explanation', rakhi.questions.every(q => (q.explanation||'').length > 20));
check('no duplicate choices within a question', rakhi.questions.every(q => new Set(q.choices).size === 4));
const text = JSON.stringify(rakhi).toLowerCase();
check('is about the festival, not Krishna trivia',
      text.includes('raksha') && text.includes('shravana') && text.includes('yama'));
check('slug/id agree', rakhi.id === 'quiz.' + rakhi.slug);
check('quiz slugs are unique across the library',
      new Set(quizzes.map(q=>q.slug)).size === quizzes.length);

// ── the festival + kit now point at it, not at the Krishna quiz ──
const fests = JSON.parse(fs.readFileSync('content/festival-pages-2026.json','utf8'));
const rb = fests.find(f => f.slug === 'raksha-bandhan');
check('festival data points at the rakhi quiz', rb.quiz === 'raksha-bandhan-beginner', rb.quiz);
check('label no longer says Krishna', !/krishna/i.test(rb.pack.quizLabel), rb.pack.quizLabel);
const page = fs.readFileSync('festival/raksha-bandhan.html','utf8');
check('generated festival page links the rakhi quiz', page.includes('quiz=raksha-bandhan-beginner'));
check('generated festival page has no krishna-beginner link', !page.includes('quiz=krishna-beginner'));

// ── play it in a browser ──
let html = fs.readFileSync('quiz-game.html','utf8')
  .replace(/<script src="\/?analytics.js"><\/script>/, '')
  .replace(/<script src="\/?site.js"><\/script>/, `<script>${fs.readFileSync('site.js','utf8')}</script>`);
const dom = new JSDOM(html, {
  runScripts:'dangerously', url:'https://khatakshetra.com/quiz-game.html?quiz=raksha-bandhan-beginner',
  beforeParse(w){
    w.fetch = (u) => String(u).includes('quizzes.json')
      ? Promise.resolve({ json: async () => quizzes })
      : Promise.resolve({ ok:true, json: async () => ({}) });
  }
});
const { window } = dom; const doc = window.document;
await new Promise(r => setTimeout(r, 120));
check('quiz page loads the rakhi quiz', /Raksha Bandhan/i.test(doc.getElementById('quizTitle').textContent),
      doc.getElementById('quizTitle').textContent);

window.eval('setLevel("beginner")');
await new Promise(r => setTimeout(r, 40));
// answer every question correctly
for (let i = 0; i < rakhi.questions.length; i++) {
  const want = rakhi.questions[i].answer;
  const btns = Array.from(doc.querySelectorAll('#questionBox button'));
  const target = btns.find(b => b.textContent.trim() === want);
  if (!target) { check('found the correct choice for Q' + (i+1), false, btns.map(b=>b.textContent.trim()).join(' | ')); break; }
  target.dispatchEvent(new window.Event('click', { bubbles:true }));
  // the quiz deliberately holds each explanation on screen for 1.2s before advancing
  await new Promise(r => setTimeout(r, 1400));
}
await new Promise(r => setTimeout(r, 120));
const resultCopy = (doc.getElementById('resultCopy')||{}).textContent || '';
check('a full-marks run completes', /6\/6/.test(resultCopy) || /scored 6/.test(resultCopy), resultCopy.slice(0,120));
check('  → earns a rakhi-specific card, not the generic fallback',
      /Raksha Sutra|Draupadi|Yamuna/i.test(doc.body.textContent) && !/Story Seeker|Katha Vachak/.test(resultCopy),
      resultCopy.slice(0,160));
check('  → the next-step card appears', !!doc.querySelector('#resultBox .kx-after'));
dom.window.close();

let fails=0;
for (const [p,n,d] of results){ if(!p) fails++; console.log(`${p?'PASS':'FAIL'}  ${n}${!p&&d?'  → '+d:''}`); }
console.log(`\n${results.length-fails}/${results.length} passed`);
process.exit(fails?1:0);
