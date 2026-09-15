/**
 * Talapatra card artwork + the homepage seal.
 *
 *   npm i --no-save jsdom && node tests/card-art.test.mjs
 *
 * Covers talapatraArt() slug/alias resolution, the portrait appearing in the
 * reveal modal and being saved with the card, and the homepage card unsealing
 * after the daily is solved — including when the homepage was already open in
 * another tab.
 */
import { JSDOM } from 'jsdom';
import fs from 'fs';
const results=[]; const check=(n,p,d='')=>results.push([p,n,d]);
const daily = JSON.parse(fs.readFileSync('content/daily.json','utf8'));
const today = (d=>d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'))(new Date());
const entry = JSON.parse(JSON.stringify(daily[4])); entry.date = today;   // Shani

function boot(file, opts = {}) {
  let html = fs.readFileSync(file,'utf8')
    .replace(/<script src="\/?analytics.js"><\/script>/, '')
    .replace(/<script src="\/?site.js"><\/script>/, `<script>${fs.readFileSync('site.js','utf8')}</script>`)
    .replace(/<script src="\/?daily.js"><\/script>/, `<script>${fs.readFileSync('daily.js','utf8')}</script>`);
  const dom = new JSDOM(html, { runScripts:'dangerously', url:'https://khatakshetra.com/'+file, pretendToBeVisual:true,
    beforeParse(w){
      if (opts.profile) w.localStorage.setItem('khatakshetra_profile', opts.profile);
      w.fetch = (u) => String(u).includes('daily.json') ? Promise.resolve({ json: async () => [entry] })
                                                        : Promise.resolve({ ok:true, json: async () => ({}) });
      w.HTMLCanvasElement.prototype.getContext = () => ({ clearRect(){},save(){},translate(){},rotate(){},fillRect(){},restore(){} });
    }});
  return dom;
}

// ── the art helper itself ──
let dom = boot('daily.html');
dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
await new Promise(r=>setTimeout(r,120));
let w = dom.window;
const art = (c) => w.eval('talapatraArt(' + JSON.stringify(c) + ')');
check('finds art from a card title', art({ title:'Ganesha' }) === 'Images/home/daily-ganesha.jpg', art({title:'Ganesha'}));
check('finds art from an id like daily-krishna-epic', art({ id:'daily-krishna-epic' }) === 'Images/home/daily-krishna.jpg', art({id:'daily-krishna-epic'}));
check('handles "Shani Dev"', art({ title:'Shani Dev' }) === 'Images/home/daily-shani.jpg', art({title:'Shani Dev'}));
check('maps an alias (Vighnaharta → Ganesha)', art({ title:'Vighnaharta' }) === 'Images/home/daily-ganesha.jpg', art({title:'Vighnaharta'}));
check('maps an alias (Anjaneya → Hanuman)', art({ title:'Anjaneya' }) === 'Images/home/daily-hanuman.jpg', art({title:'Anjaneya'}));
check('returns nothing for a card with no portrait', art({ title:'Raksha Sutra' }) === '', art({title:'Raksha Sutra'}));
check('an explicit art field wins', art({ title:'Rama', art:'custom.jpg' }) === 'custom.jpg');

// ── the reveal modal, on solving the daily ──
w.document.getElementById('dqInput').value = 'Shani';
w.document.getElementById('dqForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
await new Promise(r=>setTimeout(r,700));   // the modal appears after 500ms
const modal = w.document.getElementById('khatakshetraCardReveal');
check('the talapatra modal opens after a correct guess', modal && modal.classList.contains('is-open'));
const img = w.document.querySelector('#talapatraPrize .talapatra-art img');
check('  → the modal now shows the deity photo', !!img, 'no img in the prize');
check('  → pointing at the right portrait', img && /daily-shani\.jpg$/.test(img.getAttribute('src')), img && img.getAttribute('src'));
check('  → the name is still there', /Shani/.test(w.document.getElementById('talapatraPrize').textContent));
const stored = JSON.parse(w.localStorage.getItem('khatakshetra_profile'));
check('  → the art is saved with the card for the Sangraha',
      stored.cards.length === 1 && /daily-shani\.jpg/.test(stored.cards[0].art||''), JSON.stringify(stored.cards[0]||{}));
const profile = w.localStorage.getItem('khatakshetra_profile');
dom.window.close();

// ── the homepage, loaded fresh after solving ──
dom = boot('index.html', { profile });
await new Promise(r=>setTimeout(r,200));
let doc = dom.window.document, card = doc.getElementById('todayCard');
check('homepage card is unsealed after solving', !card.classList.contains('is-sealed') && card.classList.contains('is-revealed'), card.className);
check('  → and carries the deity art class', /d-shani/.test(card.className), card.className);
check('  → the name is unmasked', /Shani/.test(doc.getElementById('todayDeity').textContent));
dom.window.close();

// ── THE CASE THAT WAS BROKEN: homepage already open, puzzle solved elsewhere ──
dom = boot('index.html');            // opened BEFORE solving → sealed
await new Promise(r=>setTimeout(r,200));
doc = dom.window.document; card = doc.getElementById('todayCard');
check('a homepage opened before solving starts sealed', card.classList.contains('is-sealed'));
// another tab solves it: the profile lands in storage, then the tab is revisited
dom.window.localStorage.setItem('khatakshetra_profile', profile);
dom.window.dispatchEvent(new dom.window.Event('pageshow'));
await new Promise(r=>setTimeout(r,80));
check('  → revisiting the tab unseals it without a manual reload',
      card.classList.contains('is-revealed') && !card.classList.contains('is-sealed'), card.className);
check('  → and fills in the deity', /Shani/.test(doc.getElementById('todayDeity').textContent), doc.getElementById('todayDeity').textContent);
dom.window.close();

let fails=0; for (const [p,n,d] of results){ if(!p) fails++; console.log(`${p?'PASS':'FAIL'}  ${n}${!p&&d?'  → '+d:''}`);}
console.log(`\n${results.length-fails}/${results.length} passed`); process.exit(fails?1:0);
