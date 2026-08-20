/**
 * /api/diag — safe, read-only deployment diagnostics.
 * Reports WHICH configuration is present and whether Supabase tables are
 * reachable, WITHOUT ever revealing secret values (booleans only).
 * Use it to answer "why isn't email/preferences working?" in one request.
 */
export default async function handler(req, res) {
  const out = {
    ok: true,
    runtime: { node: process.version },
    env: {
      SUPABASE_URL: !!process.env.SUPABASE_URL,
      SUPABASE_SERVICE_ROLE_KEY: !!(process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY),
      SUPABASE_ANON_KEY: !!process.env.SUPABASE_ANON_KEY,
      GMAIL_CLIENT_ID: !!process.env.GMAIL_CLIENT_ID,
      GMAIL_CLIENT_SECRET: !!process.env.GMAIL_CLIENT_SECRET,
      GMAIL_REFRESH_TOKEN: !!process.env.GMAIL_REFRESH_TOKEN,
      WELCOME_FROM: !!process.env.WELCOME_FROM,
      CRON_SECRET: !!process.env.CRON_SECRET
    },
    tables: {},
    welcomeEmailModule: null,
    welcomeEmailReady: false,
    dripModule: null,
    dripReady: false
  };

  // Can the welcome-email helper actually be imported in this bundle?
  try {
    const mod = await import('../lib/welcome-email.js');
    out.welcomeEmailModule = typeof mod.sendWelcomeEmail === 'function' ? 'ok' : 'loaded-but-missing-export';
  } catch (e) {
    out.welcomeEmailModule = 'import-failed: ' + String((e && e.message) || e);
  }
  out.welcomeEmailReady = out.welcomeEmailModule === 'ok' &&
    out.env.GMAIL_CLIENT_ID && out.env.GMAIL_CLIENT_SECRET && out.env.GMAIL_REFRESH_TOKEN;

  // Can the drip modules be imported in this bundle? (Same class of failure
  // that once broke every signup: a module Vercel didn't bundle.)
  try {
    const dm = await import('../lib/drip-emails.js');
    const mm = await import('../lib/mailer.js');
    out.dripModule = (typeof dm.day2Email === 'function' && typeof mm.sendMail === 'function')
      ? 'ok' : 'loaded-but-missing-export';
  } catch (e) {
    out.dripModule = 'import-failed: ' + String((e && e.message) || e);
  }

  // Are the tables we depend on reachable? (HEAD-style probe, no rows returned.)
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY;
  if (url && key) {
    const headers = { apikey: key, Authorization: 'Bearer ' + key };
    for (const t of ['email_captures', 'email_subscribers', 'email_sends', 'email_subscriber_progress']) {
      try {
        const r = await fetch(`${url.replace(/\/$/, '')}/rest/v1/${t}?select=*&limit=0`, { headers });
        out.tables[t] = r.ok ? 'ok' : `error ${r.status}: ${(await r.text()).slice(0, 160)}`;
      } catch (e) {
        out.tables[t] = 'fetch-failed: ' + String((e && e.message) || e);
      }
    }
  }

  // The drip can only run when the module loads, Gmail is configured, the
  // send log exists (supabase/email-drip.sql) and CRON_SECRET is set. Reported
  // as one boolean so "is the drip live?" is answerable at a glance.
  out.dripReady = out.dripModule === 'ok' && out.welcomeEmailReady &&
    out.env.CRON_SECRET && out.tables.email_sends === 'ok';
  if (!out.dripReady) {
    out.dripBlockedBy = [
      out.dripModule !== 'ok' ? 'drip module: ' + out.dripModule : null,
      !out.welcomeEmailReady ? 'gmail not configured' : null,
      !out.env.CRON_SECRET ? 'CRON_SECRET not set in Vercel' : null,
      out.tables.email_sends !== 'ok' ? 'email_sends table missing — run supabase/email-drip.sql' : null
    ].filter(Boolean);
  }

  res.setHeader('Cache-Control', 'no-store');
  return res.status(200).json(out);
}
