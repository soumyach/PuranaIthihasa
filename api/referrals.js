/**
 * /api/referrals?code=ABCD1234 — how many families joined through this link.
 *
 * Deliberately returns a COUNT and nothing else. No emails, no names, no dates.
 * Guessing someone's code therefore reveals nothing worth having, which is why
 * this needs no auth and can be called straight from the browser.
 *
 * The code is a member's own short referral code (see khatakshetraReferralCode
 * in site.js) — NOT the subscriber token used for unsubscribe links. A share
 * link must never let a stranger change someone's email preferences.
 *
 * Referrals are counted from email_captures.metadata->>'ref', which
 * analytics.js already captures from ?ref= as first-touch attribution.
 */

const REWARD_AT = 2;

export default async function handler(req, res) {
  const code = String((req.query && req.query.code) || '').trim().toUpperCase();
  res.setHeader('Cache-Control', 'no-store');

  // Codes are 8 alphanumeric characters. Reject anything else rather than
  // passing user input into a PostgREST filter.
  if (!/^[A-Z0-9]{4,16}$/.test(code)) {
    return res.status(400).json({ error: 'invalid code' });
  }

  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY;
  if (!url || !key) {
    // Fail soft: the page shows zero rather than an error box.
    return res.status(200).json({ code: code, referrals: 0, reward_at: REWARD_AT, reward_unlocked: false, degraded: true });
  }

  try {
    const endpoint = `${url.replace(/\/$/, '')}/rest/v1/email_captures` +
      `?metadata->>ref=eq.${encodeURIComponent(code)}&select=email_id`;
    const r = await fetch(endpoint, {
      headers: {
        apikey: key,
        Authorization: 'Bearer ' + key,
        // Ask PostgREST for the exact count in the Content-Range header, so we
        // never pull a list of subscriber emails into this function.
        Prefer: 'count=exact',
        Range: '0-0'
      }
    });
    if (!r.ok) {
      return res.status(200).json({ code: code, referrals: 0, reward_at: REWARD_AT, reward_unlocked: false, degraded: true });
    }
    // Content-Range looks like "0-0/7" — the total is after the slash.
    const range = r.headers.get('content-range') || '';
    const total = parseInt(String(range).split('/')[1], 10);
    const referrals = isNaN(total) ? 0 : total;

    return res.status(200).json({
      code: code,
      referrals: referrals,
      reward_at: REWARD_AT,
      reward_unlocked: referrals >= REWARD_AT
    });
  } catch (e) {
    return res.status(200).json({ code: code, referrals: 0, reward_at: REWARD_AT, reward_unlocked: false, degraded: true });
  }
}
