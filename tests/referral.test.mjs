/**
 * Referral loop tests: the count API (which must never leak subscriber emails)
 * and the /cards reward gate at 0, 1 and 2 referrals.
 *
 *   npm i --no-save jsdom && node tests/referral.test.mjs
 */
import { JSDOM } from 'jsdom';
import fs from 'fs';
const results=[]; const check=(n,p,d='')=>results.push([p,n,d]);

// ── /api/referrals ──
process.env.SUPABASE_URL='https://fake.supabase.co';
process.env.SUPABASE_SERVICE_ROLE_KEY='k';
const api = (await import('../api/referrals.js')).default;
function mkRes(){const r={headers:{}};r.setHeader=(k,v)=>{r.headers[k]=v};r.status=c=>{r.code=c;return r};r.json=b=>{r.body=b;return r};return r;}
let lastUrl='', lastHeaders={};
const withCount = (n) => { global.fetch = async (u,o={}) => { lastUrl=String(u); lastHeaders=o.headers||{};
  return { ok:true, headers:{ get:(h)=> h.toLowerCase()==='content-range' ? `0-0/${n}` : null } }; }; };

withCount(0);
let res=mkRes(); await api({query:{code:'ABCD1234'}},res);
check('returns a count', res.body.referrals === 0 && res.body.reward_at === 2, JSON.stringify(res.body));
check('  → never returns emails, only a count', !JSON.stringify(res.body).includes('@') && !('emails' in res.body));
check('  → asks PostgREST for a count, not rows', /Prefer/.test(Object.keys(lastHeaders).join()) && lastHeaders.Prefer==='count=exact' && lastHeaders.Range==='0-0');

withCount(1); res=mkRes(); await api({query:{code:'abcd1234'}},res);
check('lowercases are normalised', res.body.code === 'ABCD1234' && res.body.reward_unlocked === false);

withCount(2); res=mkRes(); await api({query:{code:'ABCD1234'}},res);
check('two referrals unlocks the reward', res.body.referrals===2 && res.body.reward_unlocked===true);

withCount(9); res=mkRes(); await api({query:{code:"' or 1=1--"}},res);
check('rejects a code that is not plain alphanumeric', res.code===400, JSON.stringify(res.body));
res=mkRes(); await api({query:{}},res);
check('rejects a missing code', res.code===400);

global.fetch = async () => { throw new Error('supabase down'); };
res=mkRes(); await api({query:{code:'ABCD1234'}},res);
check('fails soft when Supabase is down (shows zero, not an error)', res.code===200 && res.body.degraded===true);

// ── the /cards gate ──
async function cardsPage(referrals) {
  let html = fs.readFileSync('cards.html','utf8')
    .replace(/<script src="analytics.js"><\/script>/, '')
    .replace(/<script src="site.js"><\/script>/, `<script>${fs.readFileSync('site.js','utf8')}</script>`);
  const daily = JSON.parse(fs.readFileSync('content/daily.json','utf8'));
  const dom = new JSDOM(html, { runScripts:'dangerously', url:'https://khatakshetra.com/cards', pretendToBeVisual:true,
    beforeParse(w){
      w.fetch = (u) => String(u).includes('daily.json')
        ? Promise.resolve({ json: async () => daily })
        : Promise.resolve({ ok:true, json: async () => ({ referrals, reward_at:2, reward_unlocked: referrals>=2 }) });
      w.print = () => {};
    }});
  dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
  await new Promise(r=>setTimeout(r,120));
  return dom;
}

let dom = await cardsPage(0);
let doc = dom.window.document;
check('0 referrals → locked', doc.getElementById('cdLocked').classList.contains('is-on') && !doc.getElementById('cdOpen').classList.contains('is-on'));
check('  → shows progress "0 of 2"', /0 of 2/.test(doc.getElementById('cdCount').textContent));
check('  → the invite link carries a referral code', /\?ref=[A-Z0-9]{4,}/.test(doc.getElementById('cdUrl').value), doc.getElementById('cdUrl').value);
check('  → the code is NOT the unsubscribe token', !/token/i.test(doc.getElementById('cdUrl').value));
check('  → no cards are rendered while locked', doc.querySelectorAll('.cd-card').length === 0);
dom.window.close();

dom = await cardsPage(1); doc = dom.window.document;
check('1 referral → still locked, one pip lit',
      doc.getElementById('cdLocked').classList.contains('is-on') && doc.getElementById('cdPip1').classList.contains('is-on') && !doc.getElementById('cdPip2').classList.contains('is-on'));
dom.window.close();

dom = await cardsPage(2); doc = dom.window.document;
check('2 referrals → unlocked', doc.getElementById('cdOpen').classList.contains('is-on') && !doc.getElementById('cdLocked').classList.contains('is-on'));
check('  → all 8 cards render', doc.querySelectorAll('.cd-card').length === 8, String(doc.querySelectorAll('.cd-card').length));
check('  → cards carry the wisdom quote', /Wisdom begins by making space/.test(doc.body.textContent));
check('  → print styles exist for cutting out', /@media print/.test(doc.querySelector('style').textContent));
dom.window.close();

// ── the referral code is stable per member ──
dom = await cardsPage(0);
const w = dom.window;
const a = w.eval('khatakshetraReferralCode()'), b = w.eval('khatakshetraReferralCode()');
check('the referral code is stable across calls', a === b && /^[A-Z0-9]{8}$/.test(a), a + ' vs ' + b);
check('  → and is stored on the profile', JSON.parse(w.localStorage.getItem('khatakshetra_profile')).referral_code === a);
dom.window.close();

let fails=0; for (const [p,n,d] of results){ if(!p) fails++; console.log(`${p?'PASS':'FAIL'}  ${n}${!p&&d?'  → '+d:''}`);}
console.log(`\n${results.length-fails}/${results.length} passed`); process.exit(fails?1:0);
