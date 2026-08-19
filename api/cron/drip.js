/**
 * api/cron/drip.js — the scheduled job that actually sends the drip.
 *
 * Runs once a day (see vercel.json → crons). For every subscriber it works out
 * what they are due and sends it:
 *
 *   day2    joined 2-14 days ago, never sent day2
 *   day5    joined 5-21 days ago, never sent day5
 *   weekly  weekly_digest on, joined >= 3 days ago, none sent this ISO week
 *
 * At most ONE email per person per run, and a 20-hour per-person cooldown, so
 * neither an extra cron tick nor a manual trigger can walk someone through two
 * emails in a morning. The day2/day5 windows stop the whole back catalogue being
 * blasted with "day 2" the first time this runs.
 *
 * DOUBLE-SEND SAFETY — the important part. Rather than "send, then log", we
 * CLAIM first: insert a row into email_sends with status 'pending'. The unique
 * index on (lower(email), dedupe_key) means a second attempt for the same
 * email+template fails at the database, so we skip it and never send twice.
 * Only after the claim succeeds do we call Gmail, then mark the row sent/failed.
 * A cron that fires twice, or two overlapping runs, cannot spam anyone.
 *
 * Auth: Vercel Cron sends `Authorization: Bearer $CRON_SECRET`. Manual runs can
 * pass ?secret=... instead. Without CRON_SECRET set the endpoint refuses to run,
 * so it can never be triggered anonymously.
 *
 * Env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, CRON_SECRET,
 *      GMAIL_* (as for the welcome email).
 *
 * Manual dry run (counts only, sends nothing):
 *   curl "https://khatakshetra.com/api/cron/drip?secret=...&dry=1"
 */

import { sendMail, mailerConfigured } from '../../lib/mailer.js';
import { day2Email, day5Email, weeklyEmail } from '../../lib/drip-emails.js';

// Gmail's daily cap is around 500. Staying well under it keeps the sending
// reputation intact, and the backlog just goes out on the next day's run.
const MAX_SENDS_PER_RUN = 120;

function isoWeekKey(d) {
  // ISO-8601 week number, so "this week" means the same thing every year.
  const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  const day = t.getUTCDay() || 7;
  t.setUTCDate(t.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
  const week = Math.ceil((((t - yearStart) / 86400000) + 1) / 7);
  return t.getUTCFullYear() + '-W' + String(week).padStart(2, '0');
}

function daysSince(iso) {
  const then = Date.parse(iso);
  if (isNaN(then)) return 0;
  return Math.floor((Date.now() - then) / 86400000);
}

/** The next festival with a free pack, so day5 and the digest stay current. */
async function nextFestival(origin) {
  try {
    const r = await fetch(origin + '/content/festival-pages-2026.json');
    if (!r.ok) return null;
    const list = await r.json();
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const upcoming = list
      .filter(function (f) { return f.pack && !isNaN(Date.parse(f.date)); })
      .map(function (f) {
        const d = new Date(Date.parse(f.date)); d.setHours(0, 0, 0, 0);
        return { slug: f.slug, title: f.title, date: f.date, days: Math.round((d - today) / 86400000) };
      })
      .filter(function (f) { return f.days >= 0; })
      .sort(function (a, b) { return a.days - b.days; });
    return upcoming[0] || null;
  } catch (e) { return null; }
}

/** Today's katha, for the digest's "Read" slot. */
async function todaysKatha(origin) {
  try {
    const r = await fetch(origin + '/content/daily.json');
    if (!r.ok) return null;
    const list = await r.json();
    if (!Array.isArray(list) || !list.length) return null;
    const i = Math.abs(Math.floor((Date.now() - Date.UTC(2026, 0, 1)) / 86400000)) % list.length;
    const e = list[i];
    return { title: e.kathaTitle || '', teaser: e.teaser || '', theme: e.theme || '' };
  } catch (e) { return null; }
}

export default async function handler(req, res) {
  const supabaseUrl = process.env.SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  const secret = process.env.CRON_SECRET;

  // Refuse rather than run unauthenticated — this endpoint sends real email.
  if (!secret) return res.status(503).json({ error: 'CRON_SECRET not configured' });
  const auth = req.headers.authorization || '';
  const given = auth.startsWith('Bearer ') ? auth.slice(7) : (req.query && req.query.secret) || '';
  if (given !== secret) return res.status(401).json({ error: 'unauthorized' });

  if (!supabaseUrl || !serviceKey) return res.status(503).json({ error: 'supabase not configured' });

  const dryRun = !!(req.query && (req.query.dry === '1' || req.query.dry === 'true'));
  const origin = 'https://' + (req.headers['x-forwarded-host'] || req.headers.host || 'khatakshetra.com');
  const H = {
    apikey: serviceKey,
    Authorization: 'Bearer ' + serviceKey,
    'Content-Type': 'application/json'
  };
  const REST = supabaseUrl.replace(/\/$/, '') + '/rest/v1';

  const summary = { checked: 0, due: 0, sent: 0, skipped_already_sent: 0, failed: 0, dry_run: dryRun, by_template: {}, errors: [] };

  try {
    // Only people who still want email. Cap the page — a daily run does not
    // need to walk an unbounded list in one invocation.
    const subsResp = await fetch(
      REST + '/email_subscribers?subscribed=eq.true&select=email,token,weekly_digest,created_at&order=created_at.asc&limit=2000',
      { headers: H }
    );
    if (!subsResp.ok) {
      return res.status(502).json({ error: 'subscriber fetch failed', status: subsResp.status, detail: (await subsResp.text()).slice(0, 300) });
    }
    const subs = await subsResp.json();
    summary.checked = subs.length;

    const week = isoWeekKey(new Date());
    const festival = await nextFestival(origin);
    const katha = await todaysKatha(origin);

    // What has already gone out? Read it once, so queueing is accurate and the
    // dry-run numbers mean something.
    const already = new Set();
    const lastTouch = {};   // email -> most recent claim time, for the cooldown
    const logResp = await fetch(
      REST + '/email_sends?status=in.(sent,pending)&select=email,dedupe_key,claimed_at&limit=20000',
      { headers: H }
    );
    if (logResp.ok) {
      for (const row of await logResp.json()) {
        const key = String(row.email).toLowerCase();
        already.add(key + '|' + row.dedupe_key);
        const t = Date.parse(row.claimed_at || '');
        if (!isNaN(t) && (!lastTouch[key] || t > lastTouch[key])) lastTouch[key] = t;
      }
    } else if (logResp.status === 404) {
      return res.status(503).json({ error: 'email_sends table missing — run supabase/email-drip.sql first' });
    }

    // Three rules that keep this from behaving like a spam cannon:
    //
    // 1. WINDOWS. day2/day5 only go to people who genuinely just joined. Without
    //    this, switching the drip on would blast the whole back catalogue: a
    //    subscriber from 40 days ago would get "welcome, here's day 2" today.
    // 2. ONE EMAIL PER PERSON PER RUN. Someone who joined 6 days ago is due both
    //    day2 and day5; sending both the same morning reads as broken. They get
    //    the earlier step now and the next one tomorrow.
    // 3. COOLDOWN. One email per person per day, however often this endpoint is
    //    hit. Without it, triggering the cron manually a few times would walk a
    //    subscriber through day2 then day5 within minutes.
    const COOLDOWN_HOURS = 20;
    const WINDOW = { day2: [2, 14], day5: [5, 21] };
    const queue = [];
    for (const s of subs) {
      const age = daysSince(s.created_at);
      const key = String(s.email).toLowerCase();
      if (lastTouch[key] && (Date.now() - lastTouch[key]) < COOLDOWN_HOURS * 3600000) {
        summary.skipped_cooldown = (summary.skipped_cooldown || 0) + 1;
        continue;
      }
      const candidates = [];
      if (age >= WINDOW.day2[0] && age <= WINDOW.day2[1]) candidates.push({ template: 'day2', dedupe: 'day2' });
      if (age >= WINDOW.day5[0] && age <= WINDOW.day5[1]) candidates.push({ template: 'day5', dedupe: 'day5' });
      if (s.weekly_digest && age >= 3) candidates.push({ template: 'weekly', dedupe: 'weekly-' + week });

      const next = candidates.find(function (c) { return !already.has(key + '|' + c.dedupe); });
      if (next) queue.push({ sub: s, template: next.template, dedupe: next.dedupe });
    }
    summary.due = queue.length;

    if (dryRun) {
      for (const item of queue) {
        summary.by_template[item.template] = (summary.by_template[item.template] || 0) + 1;
      }
      return res.status(200).json(summary);
    }
    if (!mailerConfigured()) return res.status(503).json({ error: 'gmail not configured', summary });

    for (const item of queue) {
      if (summary.sent >= MAX_SENDS_PER_RUN) { summary.capped = true; break; }
      const email = item.sub.email;

      // ── 1. CLAIM. The unique index is what makes this safe: if the row
      //       already exists (sent earlier, or being sent by a parallel run),
      //       the insert is rejected and we move on without sending.
      const claim = await fetch(REST + '/email_sends', {
        method: 'POST',
        headers: Object.assign({}, H, { Prefer: 'return=representation' }),
        body: JSON.stringify({
          email: email, template: item.template, dedupe_key: item.dedupe,
          status: 'pending',
          metadata: { festival: festival ? festival.slug : null, week: week }
        })
      });
      if (claim.status === 409) { summary.skipped_already_sent++; continue; }
      if (!claim.ok) {
        summary.failed++;
        summary.errors.push({ email: email, step: 'claim', status: claim.status, detail: (await claim.text()).slice(0, 200) });
        continue;
      }
      const claimed = (await claim.json())[0] || null;

      // ── 2. SEND.
      const opts = { token: item.sub.token, festival: festival, katha: katha };
      const built = item.template === 'day2' ? day2Email(opts)
                  : item.template === 'day5' ? day5Email(opts)
                  : weeklyEmail(opts);
      const result = await sendMail({ to: email, subject: built.subject, html: built.html, token: item.sub.token });

      // ── 3. RECORD the outcome on the row we already claimed.
      if (claimed && claimed.id) {
        await fetch(REST + '/email_sends?id=eq.' + encodeURIComponent(claimed.id), {
          method: 'PATCH',
          headers: H,
          body: JSON.stringify(result.sent
            ? { status: 'sent', sent_at: new Date().toISOString(), provider_message_id: result.messageId || '' }
            : { status: 'failed', error: (result.reason || 'unknown') + (result.detail ? ': ' + result.detail : '') })
        }).catch(function () {});
      }

      if (result.sent) {
        summary.sent++;
        summary.by_template[item.template] = (summary.by_template[item.template] || 0) + 1;
      } else {
        summary.failed++;
        summary.errors.push({ email: email, step: 'send', reason: result.reason });
      }
    }

    return res.status(200).json(summary);
  } catch (err) {
    return res.status(500).json({ error: 'drip run failed', detail: String(err).slice(0, 400), summary });
  }
}
