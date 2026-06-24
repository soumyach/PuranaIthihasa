/**
 * _welcome-email.js — content + sender for the Khatakshetra welcome email.
 * The leading underscore means Vercel does NOT expose this as an API route;
 * it is a helper module imported by api/email-capture.js.
 *
 * Sending uses Resend (https://resend.com) — set two env vars in Vercel:
 *   RESEND_API_KEY   your Resend API key (re_...)
 *   WELCOME_FROM     verified sender, e.g. "Khatakshetra <hello@khatakshetra.com>"
 * Until RESEND_API_KEY is set, sending is a safe no-op (signups still capture).
 */

const SITE = 'https://khatakshetra.com';
export const WELCOME_SUBJECT = 'Your first unlock is inside 🪔';
const PREHEADER = 'Three quick ways to begin — a katha, a quiz, and a colouring page for the kids.';

function esc(s) { return String(s || '').replace(/[<>&"]/g, function (c) { return { '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;' }[c]; }); }

/** Build the HTML. `name` is optional; pass '{{first_name}}' to produce a merge-tag template. */
export function welcomeEmailHtml(opts) {
  opts = opts || {};
  const name = opts.name ? esc(opts.name) : 'there';
  const unsub = opts.unsubscribeUrl || '{{unsubscribe_url}}';
  const row = function (emoji, href, title, line) {
    return (
      '<tr><td style="padding:10px 0;border-bottom:1px solid #ECDDB8;">' +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>' +
          '<td width="44" valign="top" style="font-size:26px;line-height:1;">' + emoji + '</td>' +
          '<td valign="top" style="font-family:Georgia,serif;">' +
            '<a href="' + SITE + href + '" target="_blank" style="color:#6B1A1A;text-decoration:none;font-size:17px;font-weight:bold;">' + title + ' &rarr;</a>' +
            '<div style="font-size:14px;color:#5a4a2a;line-height:1.5;margin-top:2px;">' + line + '</div>' +
          '</td>' +
        '</tr></table>' +
      '</td></tr>'
    );
  };
  return '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><meta http-equiv="X-UA-Compatible" content="IE=edge"><title>Welcome to Khatakshetra</title></head>' +
  '<body style="margin:0;padding:0;background:#160d02;-webkit-text-size-adjust:100%;">' +
  '<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#160d02;font-size:1px;line-height:1px;">' + PREHEADER + '</div>' +
  '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#160d02;"><tr><td align="center" style="padding:28px 16px;">' +
    '<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background:#FBF3E2;border:1px solid #E2C98A;border-radius:14px;overflow:hidden;">' +

      // header
      '<tr><td align="center" style="background:#2A1206;padding:22px 24px;">' +
        '<span style="font-family:Georgia,serif;font-size:22px;font-weight:bold;letter-spacing:2px;color:#E8B94F;">KHATAKSHETRA</span>' +
        '<div style="font-family:Georgia,serif;font-size:12px;color:#C9A86B;letter-spacing:1px;margin-top:4px;">Itihasa &amp; Purana, brought to life</div>' +
      '</td></tr>' +

      // hero
      '<tr><td style="padding:32px 36px 6px 36px;font-family:Georgia,serif;color:#3A2A12;">' +
        '<h1 style="margin:0 0 12px 0;font-size:26px;line-height:1.25;color:#6B1A1A;">Welcome, ' + name + ' — the stories are waiting.</h1>' +
        '<p style="margin:0;font-size:16px;line-height:1.65;color:#4a3a1e;">The Ramayana, the Puranas, the deities and the temples around them — the tales we grew up on. Here they\'re not a thick book to revere from a distance, but small joyful ways in, a little every day, for the whole family. Here\'s the easiest way to start:</p>' +
      '</td></tr>' +

      // start with these three
      '<tr><td style="padding:16px 36px 4px 36px;font-family:Georgia,serif;">' +
        '<p style="margin:0 0 6px 0;font-size:13px;letter-spacing:1.5px;text-transform:uppercase;color:#A06A18;">Start with these three</p>' +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">' +
          row('🪔', '/daily', "Today's Katha &amp; Puzzle", 'A 60-second story and a guess-the-deity puzzle. Come back daily and build a streak.') +
          row('🎭', '/which-character', 'Which Ramayana character are you?', 'A one-minute quiz that\'s genuinely fun to share with family.') +
          row('🎨', '/drawing-kits', 'Print a colouring page', 'Beautiful, ready-to-print pages to keep little hands busy.') +
        '</table>' +
      '</td></tr>' +

      // CTA
      '<tr><td align="center" style="padding:26px 36px 6px 36px;">' +
        '<table role="presentation" cellpadding="0" cellspacing="0"><tr>' +
          '<td align="center" bgcolor="#E07B1A" style="border-radius:9px;">' +
            '<a href="' + SITE + '/daily" target="_blank" style="display:inline-block;padding:14px 30px;font-family:Georgia,serif;font-size:17px;font-weight:bold;color:#160d02;text-decoration:none;border-radius:9px;background:#E07B1A;">▶&nbsp; Play today\'s Katha &amp; Puzzle</a>' +
          '</td>' +
        '</tr></table>' +
      '</td></tr>' +

      // starter kit
      '<tr><td style="padding:18px 36px 4px 36px;font-family:Georgia,serif;color:#3A2A12;">' +
        '<p style="margin:0 0 8px 0;font-size:13px;letter-spacing:1.5px;text-transform:uppercase;color:#A06A18;">In your free starter kit</p>' +
        '<p style="margin:0;font-size:15px;line-height:1.7;color:#4a3a1e;">🪔 A premium Ramayana story to read &nbsp;·&nbsp; 🎨 Three colouring pages &nbsp;·&nbsp; 🧠 A beginner quiz with your score saved &nbsp;·&nbsp; 🍃 A talapatra wisdom card to keep.</p>' +
      '</td></tr>' +

      // reply prompt (engagement + deliverability)
      '<tr><td style="padding:18px 36px;font-family:Georgia,serif;">' +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="background:#F3E6C6;border-left:3px solid #E07B1A;border-radius:6px;padding:14px 16px;">' +
          '<p style="margin:0;font-size:15px;line-height:1.6;color:#5a3a0a;">One small thing: <strong>hit reply and tell us which story you grew up with.</strong> We\'re a tiny team, we read every message, and early members like you are shaping what we build next.</p>' +
        '</td></tr></table>' +
      '</td></tr>' +

      // expectation + links
      '<tr><td align="center" style="padding:6px 36px 20px 36px;font-family:Georgia,serif;font-size:14px;">' +
        '<p style="margin:0 0 12px 0;font-size:14px;color:#7a5a2a;line-height:1.6;">Each week we send one short, beautiful thing — a katha, a festival story, or a new game. Never spam.</p>' +
        '<a href="' + SITE + '/stories" target="_blank" style="color:#A0521A;text-decoration:none;">Stories</a> &nbsp;·&nbsp; ' +
        '<a href="' + SITE + '/games" target="_blank" style="color:#A0521A;text-decoration:none;">Games</a> &nbsp;·&nbsp; ' +
        '<a href="' + SITE + '/temples" target="_blank" style="color:#A0521A;text-decoration:none;">Temples</a> &nbsp;·&nbsp; ' +
        '<a href="' + SITE + '/kits" target="_blank" style="color:#A0521A;text-decoration:none;">Festival kits</a>' +
      '</td></tr>' +

      // footer
      '<tr><td style="background:#F1E3C2;padding:18px 36px;font-family:Georgia,serif;font-size:12px;line-height:1.6;color:#8a7448;text-align:center;border-top:1px solid #E2C98A;">' +
        'You\'re receiving this because you signed up at khatakshetra.com.<br>' +
        '<a href="' + unsub + '" style="color:#8a7448;text-decoration:underline;">Unsubscribe</a> &nbsp;·&nbsp; Khatakshetra' +
      '</td></tr>' +

    '</table>' +
    '<div style="font-family:Georgia,serif;font-size:11px;color:#6b5a36;margin-top:14px;">© Khatakshetra — the stories we inherited, brought to life.</div>' +
  '</td></tr></table></body></html>';
}

export function welcomeEmailText(opts) {
  opts = opts || {};
  const name = opts.name || 'there';
  return [
    'Welcome, ' + name + ' — the stories are waiting.',
    '',
    'The Ramayana, the Puranas, the deities and temples around them — a little every day, for the whole family. Start with these three:',
    '',
    '1) Today\'s Katha & Puzzle (60 seconds, build a streak): ' + SITE + '/daily',
    '2) Which Ramayana character are you? (fun to share): ' + SITE + '/which-character',
    '3) Print a colouring page for the kids: ' + SITE + '/drawing-kits',
    '',
    'In your free starter kit: a Ramayana story, three colouring pages, a beginner quiz with score saved, and a talapatra wisdom card.',
    '',
    'Reply and tell us which story YOU grew up with — we read every message.',
    '',
    'Khatakshetra — the stories we inherited, brought to life.',
    SITE
  ].join('\n');
}

/** Send the welcome email via Resend. Safe no-op if RESEND_API_KEY is not set. */
export async function sendWelcomeEmail(to, opts) {
  opts = opts || {};
  const key = process.env.RESEND_API_KEY;
  if (!key) return { sent: false, reason: 'no_resend_key' };
  const from = process.env.WELCOME_FROM || 'Khatakshetra <hello@khatakshetra.com>';
  try {
    const resp = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: from,
        to: [to],
        subject: WELCOME_SUBJECT,
        html: welcomeEmailHtml({ name: opts.name }),
        text: welcomeEmailText({ name: opts.name })
      })
    });
    if (!resp.ok) return { sent: false, reason: 'resend_error', status: resp.status, detail: await resp.text() };
    return { sent: true };
  } catch (e) {
    return { sent: false, reason: 'exception', detail: String(e) };
  }
}
