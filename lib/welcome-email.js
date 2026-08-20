/**
 * lib/welcome-email.js — content + Gmail sender for the Khatakshetra welcome email.
 * Lives OUTSIDE /api deliberately: Vercel excludes `api/_*` files from the function
 * bundle, so importing it from an API route crashed the route at load
 * (FUNCTION_INVOCATION_FAILED) and broke every signup.
 *
 * Sends through your own Google / Gmail account via the Gmail API (no SMTP, no deps).
 * Set these env vars in Vercel (see PR description for how to get them):
 *   GMAIL_CLIENT_ID       OAuth 2.0 client ID
 *   GMAIL_CLIENT_SECRET   OAuth 2.0 client secret
 *   GMAIL_REFRESH_TOKEN   refresh token for the sending account (scope gmail.send)
 *   WELCOME_FROM          sender, e.g. "Khatakshetra <hello@khatakshetra.com>"
 *                         (must be the authenticated account or a verified send-as alias)
 * Until GMAIL_REFRESH_TOKEN is set, sending is a safe no-op (signups still capture).
 */

import { sendMail } from './mailer.js';

const SITE = 'https://khatakshetra.com';
export const WELCOME_SUBJECT = 'Welcome to Khatakshetra - your first unlock is inside';
const PREHEADER = 'Three quick ways to begin - a katha, a short quiz, and a printable colouring page.';

function esc(s) { return String(s || '').replace(/[<>&"]/g, function (c) { return { '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;' }[c]; }); }

function prefsUrl(token) { return SITE + '/preferences?t=' + encodeURIComponent(token || '{{unsubscribe_token}}'); }

/** Build the HTML. Pass { name, token }. For an ESP template, pass token omitted → {{...}} tags. */
export function welcomeEmailHtml(opts) {
  opts = opts || {};
  const name = opts.name ? esc(opts.name) : 'there';
  const manage = opts.token ? prefsUrl(opts.token) : (opts.unsubscribeUrl || '{{unsubscribe_url}}');
  // One downloadable festival kit, as an email-safe table row.
  const kitRow = function (kitName, when, href) {
    return '<tr><td style="padding:7px 0;border-bottom:1px solid #ECDDB8;font-family:Georgia,serif;">' +
      '<a href="' + SITE + href + '" target="_blank" style="color:#6B1A1A;text-decoration:none;font-size:15px;font-weight:bold;">' +
      kitName + ' kit &darr;</a>' +
      '<span style="font-size:13px;color:#7a5a2a;"> &nbsp;&middot;&nbsp; ' + when + '</span></td></tr>';
  };
  const step = function (n, href, title, line) {
    return (
      '<tr><td style="padding:11px 0;border-bottom:1px solid #ECDDB8;">' +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>' +
          '<td width="46" valign="top">' +
            '<div style="width:30px;height:30px;border-radius:50%;background:#E07B1A;color:#FBF3E2;font-family:Georgia,serif;font-weight:bold;font-size:15px;text-align:center;line-height:30px;">' + n + '</div>' +
          '</td>' +
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

      '<tr><td align="center" style="background:#2A1206;padding:22px 24px;">' +
        '<span style="font-family:Georgia,serif;font-size:22px;font-weight:bold;letter-spacing:2px;color:#E8B94F;">KHATAKSHETRA</span>' +
        '<div style="font-family:Georgia,serif;font-size:12px;color:#C9A86B;letter-spacing:1px;margin-top:4px;">Itihasa &amp; Purana, brought to life</div>' +
      '</td></tr>' +

      '<tr><td style="padding:32px 36px 6px 36px;font-family:Georgia,serif;color:#3A2A12;">' +
        '<h1 style="margin:0 0 12px 0;font-size:26px;line-height:1.28;color:#6B1A1A;">Welcome, ' + name + '. The stories are waiting.</h1>' +
        '<p style="margin:0;font-size:16px;line-height:1.65;color:#4a3a1e;">The Ramayana and the Mahabharata, the Puranas, and the deities and temples woven through them &mdash; the stories we inherited. Here they are not a vast book to revere from afar, but small, living ways in: a little to read, play, and pass on each day, for the whole family. The easiest way to begin:</p>' +
      '</td></tr>' +

      '<tr><td style="padding:18px 36px 4px 36px;font-family:Georgia,serif;">' +
        '<p style="margin:0 0 8px 0;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#A06A18;">Start with these three</p>' +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">' +
          step('1', '/daily', "Today's Katha &amp; Puzzle", 'A 60-second story and a guess-the-deity puzzle. Come back daily and build a streak.') +
          step('2', '/which-character', 'Which character are you?', 'A one-minute quiz that is genuinely fun to share with family.') +
          step('3', '/paint', 'Colour online, free', 'Tap to fill, undo anything, save your artwork. Any phone or tablet.') +
        '</table>' +
      '</td></tr>' +

      '<tr><td align="center" style="padding:26px 36px 6px 36px;">' +
        '<table role="presentation" cellpadding="0" cellspacing="0"><tr>' +
          '<td align="center" bgcolor="#E07B1A" style="border-radius:9px;">' +
            '<a href="' + SITE + '/daily" target="_blank" style="display:inline-block;padding:14px 32px;font-family:Georgia,serif;font-size:17px;font-weight:bold;color:#160d02;text-decoration:none;border-radius:9px;background:#E07B1A;">Play today\'s Katha &amp; Puzzle</a>' +
          '</td>' +
        '</tr></table>' +
      '</td></tr>' +

      // The actual deliverable: the three printable festival kits.
      '<tr><td style="padding:20px 36px 4px 36px;font-family:Georgia,serif;color:#3A2A12;">' +
        '<p style="margin:0 0 8px 0;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#A06A18;">Your free festival kits</p>' +
        '<p style="margin:0 0 10px 0;font-size:15px;line-height:1.65;color:#4a3a1e;">Each one has three colouring sheets, the story behind the festival, and a wisdom card to cut out. Free to print and share.</p>' +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">' +
          kitRow('Raksha Bandhan', '28 August', '/downloads/raksha-bandhan-diy-starter.pdf') +
          kitRow('Janmashtami', '4 September', '/downloads/janmashtami-diy-starter.pdf') +
          kitRow('Ganesh Chaturthi', '14 September', '/downloads/ganesha-diy-starter.pdf') +
        '</table>' +
      '</td></tr>' +

      '<tr><td style="padding:18px 36px;font-family:Georgia,serif;">' +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="background:#F3E6C6;border-left:3px solid #E07B1A;border-radius:6px;padding:14px 16px;">' +
          '<p style="margin:0;font-size:15px;line-height:1.6;color:#5a3a0a;">One small thing: <strong>reply and tell us which story you grew up with</strong> &mdash; from the Ramayana, the Mahabharata, or a Purana. We are a small team, we read every message, and early members like you shape what we build next.</p>' +
        '</td></tr></table>' +
      '</td></tr>' +

      '<tr><td align="center" style="padding:6px 36px 20px 36px;font-family:Georgia,serif;font-size:14px;">' +
        '<p style="margin:0 0 12px 0;font-size:14px;color:#7a5a2a;line-height:1.6;">Each week we send one short, beautiful thing &mdash; a katha, a festival story, or a new game. Never spam.</p>' +
        '<a href="' + SITE + '/stories" target="_blank" style="color:#A0521A;text-decoration:none;">Stories</a> &nbsp;&middot;&nbsp; ' +
        '<a href="' + SITE + '/games" target="_blank" style="color:#A0521A;text-decoration:none;">Games</a> &nbsp;&middot;&nbsp; ' +
        '<a href="' + SITE + '/temples" target="_blank" style="color:#A0521A;text-decoration:none;">Temples</a> &nbsp;&middot;&nbsp; ' +
        '<a href="' + SITE + '/kits" target="_blank" style="color:#A0521A;text-decoration:none;">Festival kits</a>' +
      '</td></tr>' +

      '<tr><td style="background:#F1E3C2;padding:18px 36px;font-family:Georgia,serif;font-size:12px;line-height:1.7;color:#8a7448;text-align:center;border-top:1px solid #E2C98A;">' +
        'You are receiving this because you signed up at khatakshetra.com.<br>' +
        '<a href="' + manage + '" style="color:#8a7448;text-decoration:underline;">Manage your email preferences or unsubscribe</a><br>' +
        'Khatakshetra' +
      '</td></tr>' +

    '</table>' +
    '<div style="font-family:Georgia,serif;font-size:11px;color:#6b5a36;margin-top:14px;">&copy; Khatakshetra &mdash; the stories we inherited, brought to life.</div>' +
  '</td></tr></table></body></html>';
}

export function welcomeEmailText(opts) {
  opts = opts || {};
  const name = opts.name || 'there';
  const manage = opts.token ? prefsUrl(opts.token) : '{{unsubscribe_url}}';
  return [
    'Welcome, ' + name + '. The stories are waiting.',
    '',
    'The Ramayana and the Mahabharata, the Puranas, and the deities and temples woven through them - the stories we inherited, in small living ways for the whole family. Start with these three:',
    '',
    '1) Today\'s Katha & Puzzle (60 seconds, build a streak): ' + SITE + '/daily',
    '2) Which character are you? (a fun quiz to share): ' + SITE + '/which-character',
    '3) Colour online, free (tap to fill, save your art): ' + SITE + '/paint',
    '',
    'Your free festival kits (colouring sheets + the story + a wisdom card):',
    '  Raksha Bandhan (28 Aug): ' + SITE + '/downloads/raksha-bandhan-diy-starter.pdf',
    '  Janmashtami (4 Sep):     ' + SITE + '/downloads/janmashtami-diy-starter.pdf',
    '  Ganesh Chaturthi (14 Sep): ' + SITE + '/downloads/ganesha-diy-starter.pdf',
    '',
    'Reply and tell us which story you grew up with - we read every message.',
    '',
    'Manage preferences or unsubscribe: ' + manage,
    'Khatakshetra - the stories we inherited, brought to life. ' + SITE
  ].join('\n');
}

// ── Sending ──────────────────────────────────────────────────────────────────
// The OAuth + Gmail plumbing now lives in lib/mailer.js so the drip emails send
// through exactly the same path. This function keeps its original signature.

/** Send the welcome email via Gmail. Safe no-op if Gmail env vars are unset. */
export async function sendWelcomeEmail(to, opts) {
  opts = opts || {};
  const html = welcomeEmailHtml({ name: opts.name, token: opts.token });
  const result = await sendMail({ to: to, subject: WELCOME_SUBJECT, html: html, token: opts.token });
  // Preserve the previous return shape callers already handle.
  if (result.sent) return { sent: true };
  return { sent: false, reason: result.reason, status: result.status, detail: result.detail };
}
