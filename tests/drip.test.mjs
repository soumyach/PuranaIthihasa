/**
 * Drip-sequence tests. Runs api/cron/drip.js against an in-memory Supabase and
 * Gmail — no network, no real email, no credentials needed:
 *
 *   node tests/drip.test.mjs
 *
 * The assertions that matter: nobody is emailed twice, nobody gets two emails in
 * one morning, subscribers who joined long ago are not retro-blasted with the
 * early sequence, and a Gmail failure is recorded rather than silently lost.
 */
/**
 * Exercises api/cron/drip.js against an in-memory Supabase + Gmail, including
 * the case that matters most: the cron running twice in one day.
 */
const results = [];
const check = (n, p, d = '') => results.push([p, n, d]);

process.env.SUPABASE_URL = 'https://fake.supabase.co';
process.env.SUPABASE_SERVICE_ROLE_KEY = 'service-key';
process.env.CRON_SECRET = 'topsecret';
process.env.GMAIL_CLIENT_ID = 'cid';
process.env.GMAIL_CLIENT_SECRET = 'csec';
process.env.GMAIL_REFRESH_TOKEN = 'rtok';
process.env.WELCOME_FROM = 'Khatakshetra <vyasa@khatakshetra.com>';

const iso = (daysAgo) => new Date(Date.now() - daysAgo * 86400000).toISOString();

// in-memory email_sends, enforcing the unique index the real table has
let sends = [];
let sent = [];        // what Gmail was actually asked to deliver
let oauthCalls = 0;

const festivals = [
  { slug: 'raksha-bandhan', title: 'Raksha Bandhan', date: 'August 28, 2026', pack: { promise: 'x' } },
  { slug: 'janmashtami', title: 'Krishna Janmashtami', date: 'September 4, 2026', pack: { promise: 'y' } }
];
const daily = [{ date: '2026-06-16', kathaTitle: 'Why we begin at all', teaser: 'One presence is remembered first.', theme: 'Beginnings' }];

const subscribers = [
  { email: 'new@a.com',      token: 't1', weekly_digest: true,  created_at: iso(0) },   // too new for anything
  { email: 'twoday@b.com',   token: 't2', weekly_digest: false, created_at: iso(2) },   // day2 only
  { email: 'fiveday@c.com',  token: 't3', weekly_digest: true,  created_at: iso(6) },   // day2 + day5 + weekly
  { email: 'oldtimer@d.com', token: 't4', weekly_digest: true,  created_at: iso(40) }   // day2 + day5 + weekly
];

global.fetch = async (url, opts = {}) => {
  const u = String(url);
  const method = (opts.method || 'GET').toUpperCase();

  if (u.includes('oauth2.googleapis.com')) { oauthCalls++; return { ok: true, json: async () => ({ access_token: 'at' }) }; }
  if (u.includes('gmail.googleapis.com')) {
    const raw = JSON.parse(opts.body).raw;
    const decoded = Buffer.from(raw.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8');
    const to = (decoded.match(/^To: (.*)$/m) || [])[1];
    const subject = (decoded.match(/^Subject: (.*)$/m) || [])[1];
    sent.push({ to, subject, hasListUnsub: /List-Unsubscribe:/.test(decoded) });
    return { ok: true, json: async () => ({ id: 'msg-' + sent.length }) };
  }
  if (u.includes('festival-pages-2026.json')) return { ok: true, json: async () => festivals };
  if (u.includes('daily.json')) return { ok: true, json: async () => daily };

  if (u.includes('/rest/v1/email_subscribers')) return { ok: true, json: async () => subscribers };

  if (u.includes('/rest/v1/email_sends')) {
    if (method === 'GET') {
      return { ok: true, status: 200, json: async () => sends
        .filter(r => r.status === 'sent' || r.status === 'pending')
        .map(r => ({ email: r.email, dedupe_key: r.dedupe_key, claimed_at: r.claimed_at || new Date().toISOString() })) };
    }
    if (method === 'POST') {
      const row = JSON.parse(opts.body);
      const dupe = sends.find(r => r.email.toLowerCase() === row.email.toLowerCase() && r.dedupe_key === row.dedupe_key);
      if (dupe) return { ok: false, status: 409, text: async () => 'duplicate key value violates unique constraint' };
      const created = { id: 'row-' + (sends.length + 1), claimed_at: new Date().toISOString(), ...row };
      sends.push(created);
      return { ok: true, status: 201, json: async () => [created] };
    }
    if (method === 'PATCH') {
      const id = decodeURIComponent(u.split('id=eq.')[1]);
      const row = sends.find(r => r.id === id);
      if (row) Object.assign(row, JSON.parse(opts.body));
      return { ok: true, json: async () => [row] };
    }
  }
  return { ok: false, status: 404, text: async () => 'unhandled ' + u };
};

const mod = await import('../api/cron/drip.js');
const handler = mod.default;

function mkRes() {
  const r = { code: 0, body: null };
  r.status = (c) => { r.code = c; return r; };
  r.json = (b) => { r.body = b; return r; };
  return r;
}
const run = async (query = {}, headers = {}) => {
  const res = mkRes();
  await handler({ query, headers: { host: 'khatakshetra.com', ...headers } }, res);
  return res;
};

// ── auth ──
let res = await run({});
check('refuses without the secret', res.code === 401, 'got ' + res.code);
res = await run({ secret: 'wrong' });
check('refuses a wrong secret', res.code === 401, 'got ' + res.code);
res = await run({}, { authorization: 'Bearer topsecret' });
check('accepts the Bearer header Vercel Cron sends', res.code === 200, 'got ' + res.code);

// reset after that live run
sends = []; sent = [];

// ── dry run sends nothing ──
res = await run({ secret: 'topsecret', dry: '1' });
check('dry run sends nothing', sent.length === 0 && res.body.dry_run === true);
// new@a.com too new; twoday→day2; fiveday→day2 (earliest step only); oldtimer→weekly only
check('dry run counts one email per person, not the whole backlog', res.body.due === 3, 'due=' + res.body.due);

// ── real run ──
res = await run({ secret: 'topsecret' });
const byTo = sent.reduce((m, s) => { (m[s.to] = m[s.to] || []).push(s.subject); return m; }, {});
check('the brand-new subscriber gets nothing yet', !byTo['new@a.com']);
check('day-2 subscriber gets exactly one email', (byTo['twoday@b.com'] || []).length === 1, JSON.stringify(byTo['twoday@b.com']));
check('  → and it is the dinner-question one', /question worth asking at dinner/i.test((byTo['twoday@b.com'] || [])[0] || ''));
check('day-2 subscriber opted out of weekly gets no digest',
      !(byTo['twoday@b.com'] || []).some(s => /This week/i.test(s)));
check('6-day subscriber gets ONE email, not three at once', (byTo['fiveday@c.com'] || []).length === 1, JSON.stringify(byTo['fiveday@c.com']));
check('40-day-old subscriber is NOT retro-blasted with day2/day5',
      !(byTo['oldtimer@d.com'] || []).some(s => /dinner|is close|waiting/i.test(s)), JSON.stringify(byTo['oldtimer@d.com']));
check('  → they only get the weekly digest', (byTo['oldtimer@d.com'] || []).every(s => /This week/i.test(s)), JSON.stringify(byTo['oldtimer@d.com']));
check('every message carries List-Unsubscribe', sent.every(s => s.hasListUnsub));
check('run summary counts the sends', res.body.sent === sent.length, JSON.stringify(res.body.by_template));
check('every send is logged as sent in email_sends',
      sends.filter(r => r.status === 'sent').length === sent.length, JSON.stringify(sends.map(r => r.status)));
check('each logged row carries a provider message id', sends.every(r => r.status !== 'sent' || r.provider_message_id));

// ── THE IMPORTANT ONE: the cron fires again the same day ──
const sentAfterFirst = sent.length;
res = await run({ secret: 'topsecret' });
check('a second run the same day sends NOTHING', sent.length === sentAfterFirst,
      'extra sends: ' + (sent.length - sentAfterFirst));
check('  → because nothing new is due', res.body.due === 0, 'due=' + res.body.due);

// ── a Gmail failure must be recorded, not silently lost ──
sends = []; sent = [];
const realFetch = global.fetch;
global.fetch = async (url, opts) => {
  if (String(url).includes('gmail.googleapis.com')) return { ok: false, status: 429, text: async () => 'rate limited' };
  return realFetch(url, opts);
};
res = await run({ secret: 'topsecret' });
check('Gmail failures are counted', res.body.failed > 0, 'failed=' + res.body.failed);
check('  → and written to the log as failed with the reason',
      sends.every(r => r.status === 'failed') && sends.some(r => /gmail_send_error/.test(r.error || '')),
      JSON.stringify(sends.slice(0, 1)));
check('  → and the claim rows exist so nothing double-sends on retry', sends.length === 3, 'rows=' + sends.length);

let fails = 0;
for (const [p, n, d] of results) { if (!p) fails++; console.log(`${p ? 'PASS' : 'FAIL'}  ${n}${!p && d ? '  → ' + d : ''}`); }
console.log(`\n${results.length - fails}/${results.length} passed`);
process.exit(fails ? 1 : 0);
