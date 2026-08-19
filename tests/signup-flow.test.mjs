/**
 * Signup + membership flow tests for the generated pages and the homepage.
 *
 * Run from the repo root:   npm i --no-save jsdom && node tests/signup-flow.test.mjs
 *
 * Covers the things that silently break in production and are invisible in a
 * diff: does a generated page actually capture an email, does the family still
 * get their pack when the API is down, and — critically — do we avoid counting
 * a conversion we cannot back up with a Supabase row?
 */
import { JSDOM } from 'jsdom';
import fs from 'fs';

const results = [];
const check = (name, pass, detail = '') => { results.push([pass, name, detail]); };

// ── 1. A generated festival page, with site.js actually running in it ─────────
async function testGeneratedPage(file, mode) {
  let html = fs.readFileSync(file, 'utf8');
  html = html.replace(/<script src="\/analytics.js"><\/script>/, '')
             .replace(/<script src="\/site.js"><\/script>/, `<script>${fs.readFileSync('site.js','utf8')}</script>`);
  const dom = new JSDOM(html, { runScripts: 'dangerously', url: 'https://khatakshetra.com/festival/janmashtami' });
  const { window } = dom;
  const posts = [], convs = [];
  window.fetch = (url, opts) => {
    posts.push(JSON.parse(opts.body));
    return mode === 'ok' ? Promise.resolve({ ok: true }) : Promise.reject(new Error('down'));
  };
  window.trackKhatakshetraSignup = (o) => convs.push(o.cta);
  window.khatakshetraAttribution = () => ({ utm_source: 'youtube', referrer: '' });
  window.document.dispatchEvent(new window.Event('DOMContentLoaded'));
  await new Promise(r => setTimeout(r, 50));

  const doc = window.document;
  const form = doc.querySelector('form[data-cta="festival_janmashtami_printable"]');
  const reveal = doc.getElementById('printable-janmashtami');
  check(`[${mode}] printable form + reveal exist`, !!form && !!reveal);
  check(`[${mode}] reveal starts hidden`, reveal.hidden === true);

  form.querySelector('input[type=email]').value = 'A@B.com';
  form.dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
  await new Promise(r => setTimeout(r, 60));

  check(`[${mode}] posted normalised email`, posts[0] && posts[0].email_id === 'a@b.com', JSON.stringify(posts[0] && posts[0].email_id));
  check(`[${mode}] attribution travelled`, posts[0] && posts[0].attribution.utm_source === 'youtube');
  check(`[${mode}] pack revealed`, reveal.hidden === false);
  check(`[${mode}] fields hidden after success`, form.querySelector('[data-signup-fields]').hidden === true);
  check(`[${mode}] conversion ${mode === 'ok' ? 'fired' : 'NOT fired'}`,
        mode === 'ok' ? convs.length === 1 : convs.length === 0, JSON.stringify(convs));
  if (mode !== 'ok') {
    const pending = JSON.parse(window.localStorage.getItem('khatakshetra_signups') || '[]');
    check('[down] email stored locally for recovery', pending.some(p => p.email === 'a@b.com' && p.unsent));
  }

  // social links + tracking
  const yt = doc.querySelector('.site-footer-social a[href*="youtube"]');
  const ig = doc.querySelector('.site-footer-social a[href*="instagram"]');
  check(`[${mode}] footer YouTube link`, yt && yt.href === 'https://www.youtube.com/@Khatakshetra', yt && yt.href);
  check(`[${mode}] footer Instagram link`, ig && ig.href === 'https://www.instagram.com/khatakshetra/', ig && ig.href);
  const subscribe = doc.querySelector('#printable-janmashtami a[href*="youtube"]');
  check(`[${mode}] subscribe ask inside the pack reveal`, !!subscribe);

  let socialEvents = [];
  window.trackKhatakshetraEvent = (n) => socialEvents.push(n);
  window.gtag = (t, n) => socialEvents.push('gtag:' + n);
  yt.dispatchEvent(new window.Event('click', { bubbles: true }));
  await new Promise(r => setTimeout(r, 10));
  check(`[${mode}] YouTube click tracked`, socialEvents.some(e => e.includes('youtube_click')), socialEvents.join(','));
  dom.window.close();
}

// ── 2. The join block on a page with NO pack → next-steps panel appears ──────
async function testNextSteps() {
  let html = fs.readFileSync('deity/krishna.html', 'utf8');
  html = html.replace(/<script src="\/analytics.js"><\/script>/, '')
             .replace(/<script src="\/site.js"><\/script>/, `<script>${fs.readFileSync('site.js','utf8')}</script>`);
  const dom = new JSDOM(html, { runScripts: 'dangerously', url: 'https://khatakshetra.com/deity/krishna' });
  const { window } = dom;
  window.fetch = () => Promise.resolve({ ok: true });
  window.trackKhatakshetraSignup = () => {};
  window.khatakshetraAttribution = () => ({});
  window.document.dispatchEvent(new window.Event('DOMContentLoaded'));
  await new Promise(r => setTimeout(r, 40));
  const doc = window.document;
  const form = doc.querySelector('form[data-cta="deity_krishna"]');
  check('deity page has a join form', !!form);
  form.querySelector('input[type=email]').value = 'x@y.com';
  form.dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
  await new Promise(r => setTimeout(r, 60));
  const next = doc.querySelector('.kx-next');
  check('next-steps panel appears when there is no pack', !!next);
  if (next) {
    check('  → offers start', !!next.querySelector('a[href="/start"]'));
    check('  → offers subscribe', !!next.querySelector('a[href*="youtube"]'));
    check('  → offers share', !!next.querySelector('[data-kx-share]'));
  }
  // submitting again must not stack panels
  form.dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
  await new Promise(r => setTimeout(r, 40));
  check('panel is not duplicated on a second submit', doc.querySelectorAll('.kx-next').length === 1);
  dom.window.close();
}

// ── 3. Homepage: footer socials + its own next-steps panel ───────────────────
async function testHomepage() {
  let html = fs.readFileSync('index.html', 'utf8');
  html = html.replace(/<script src="analytics.js"><\/script>/, '');
  const convs = [];
  // fetch must exist BEFORE the inline scripts parse, and jsdom lacks the
  // form.email named-element getter that browsers provide.
  const dom = new JSDOM(html, {
    runScripts: 'dangerously', url: 'https://khatakshetra.com/',
    beforeParse(w) {
      w.fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      w.trackKhatakshetraSignup = (o) => convs.push(o.cta);
    }
  });
  const { window } = dom;
  await new Promise(r => setTimeout(r, 60));
  const doc = window.document;
  check('homepage footer YouTube link', !!doc.querySelector('.foot-social a[href*="youtube"]'));
  check('homepage footer Instagram link', !!doc.querySelector('.foot-social a[href*="instagram"]'));
  const form = doc.querySelector('[data-signup-form]');
  const emailInput = form.querySelector('input[type=email]');
  emailInput.value = 'home@test.com';
  if (!form.email) Object.defineProperty(form, 'email', { value: emailInput }); // jsdom shim
  form.dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
  await new Promise(r => setTimeout(r, 80));
  const ns = doc.querySelector('.next-steps');
  check('homepage shows next steps after signup', !!ns);
  check('homepage fires exactly one conversion', convs.length === 1, JSON.stringify(convs));
  check('homepage next steps offer all three asks',
        ns && !!ns.querySelector('a[href="start.html"]') && !!ns.querySelector('a[href*="youtube"]') && !!ns.querySelector('[data-kx-share]'));
  dom.window.close();
}

await testGeneratedPage('festival/janmashtami.html', 'ok');
await testGeneratedPage('festival/janmashtami.html', 'down');
await testNextSteps();
await testHomepage();

let fails = 0;
for (const [pass, name, detail] of results) {
  if (!pass) fails++;
  console.log(`${pass ? 'PASS' : 'FAIL'}  ${name}${detail && !pass ? '  → ' + detail : ''}`);
}
console.log(`\n${results.length - fails}/${results.length} passed`);
process.exit(fails ? 1 : 0);
