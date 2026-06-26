/**
 * _welcome-email.js — content + Gmail sender for the Khatakshetra welcome email.
 * Leading underscore = Vercel does NOT expose this as an API route (helper module).
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
          step('3', '/drawing-kits', 'Print a colouring page', 'Beautiful, ready-to-print pages to keep little hands busy.') +
        '</table>' +
      '</td></tr>' +

      '<tr><td align="center" style="padding:26px 36px 6px 36px;">' +
        '<table role="presentation" cellpadding="0" cellspacing="0"><tr>' +
          '<td align="center" bgcolor="#E07B1A" style="border-radius:9px;">' +
            '<a href="' + SITE + '/daily" target="_blank" style="display:inline-block;padding:14px 32px;font-family:Georgia,serif;font-size:17px;font-weight:bold;color:#160d02;text-decoration:none;border-radius:9px;background:#E07B1A;">Play today\'s Katha &amp; Puzzle</a>' +
          '</td>' +
        '</tr></table>' +
      '</td></tr>' +

      '<tr><td style="padding:20px 36px 4px 36px;font-family:Georgia,serif;color:#3A2A12;">' +
        '<p style="margin:0 0 8px 0;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#A06A18;">In your free starter kit</p>' +
        '<p style="margin:0;font-size:15px;line-height:1.7;color:#4a3a1e;">A premium story to read &nbsp;&middot;&nbsp; three colouring pages &nbsp;&middot;&nbsp; a beginner quiz with your score saved &nbsp;&middot;&nbsp; a talapatra wisdom card to keep.</p>' +
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
    '3) Print a colouring page for the kids: ' + SITE + '/drawing-kits',
    '',
    'In your free starter kit: a premium story, three colouring pages, a beginner quiz with score saved, and a talapatra wisdom card.',
    '',
    'Reply and tell us which story you grew up with - we read every message.',
    '',
    'Manage preferences or unsubscribe: ' + manage,
    'Khatakshetra - the stories we inherited, brought to life. ' + SITE
  ].join('\n');
}

// ── Gmail API sender (OAuth2 refresh token; HTTPS only, no dependencies) ──
function b64(str) { return Buffer.from(str, 'utf8').toString('base64'); }
function b64url(str) { return Buffer.from(str, 'utf8').toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); }
function wrap76(s) { return s.replace(/.{1,76}/g, '$&\r\n'); }

async function getAccessToken() {
  const params = new URLSearchParams({
    client_id: process.env.GMAIL_CLIENT_ID || '',
    client_secret: process.env.GMAIL_CLIENT_SECRET || '',
    refresh_token: process.env.GMAIL_REFRESH_TOKEN || '',
    grant_type: 'refresh_token'
  });
  const resp = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString()
  });
  if (!resp.ok) throw new Error('oauth ' + resp.status + ' ' + (await resp.text()));
  const j = await resp.json();
  return j.access_token;
}

/** Send the welcome email via Gmail. Safe no-op if Gmail env vars are unset. */
export async function sendWelcomeEmail(to, opts) {
  opts = opts || {};
  if (!process.env.GMAIL_REFRESH_TOKEN || !process.env.GMAIL_CLIENT_ID || !process.env.GMAIL_CLIENT_SECRET) {
    return { sent: false, reason: 'gmail_not_configured' };
  }
  const from = process.env.WELCOME_FROM || 'Khatakshetra <vyasa@khatakshetra.com>';
  const html = welcomeEmailHtml({ name: opts.name, token: opts.token });
  const manageHttps = prefsUrl(opts.token);
  const unsubMailto = 'mailto:' + (from.match(/<([^>]+)>/) ? from.match(/<([^>]+)>/)[1] : 'vyasa@khatakshetra.com') + '?subject=unsubscribe';
  try {
    const accessToken = await getAccessToken();
    const message = [
      'From: ' + from,
      'To: ' + to,
      'Subject: ' + WELCOME_SUBJECT,
      'MIME-Version: 1.0',
      'List-Unsubscribe: <' + manageHttps + '>, <' + unsubMailto + '>',
      'List-Unsubscribe-Post: List-Unsubscribe=One-Click',
      'Content-Type: text/html; charset="UTF-8"',
      'Content-Transfer-Encoding: base64',
      '',
      wrap76(b64(html))
    ].join('\r\n');
    const raw = b64url(message);
    const resp = await fetch('https://gmail.googleapis.com/gmail/v1/users/me/messages/send', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + accessToken, 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw: raw })
    });
    if (!resp.ok) return { sent: false, reason: 'gmail_send_error', status: resp.status, detail: await resp.text() };
    return { sent: true };
  } catch (e) {
    return { sent: false, reason: 'exception', detail: String(e) };
  }
}
