/**
 * lib/mailer.js — the Gmail sender and the email-theme shell, shared by the
 * welcome email and the drip sequence.
 *
 * Extracted from lib/welcome-email.js so the drip emails send through exactly
 * the same path (one OAuth flow, one place to fix a deliverability problem)
 * and look like the same family of emails.
 *
 * Lives OUTSIDE /api deliberately: Vercel excludes `api/_*` files from the
 * function bundle, and importing a missing module crashes the route at load.
 *
 * Env (same as before):
 *   GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET / GMAIL_REFRESH_TOKEN / WELCOME_FROM
 * Until GMAIL_REFRESH_TOKEN is set, sending is a safe no-op.
 */

export const SITE = 'https://khatakshetra.com';

export function esc(s) {
  return String(s == null ? '' : s).replace(/[<>&"]/g, function (c) {
    return { '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;' }[c];
  });
}

export function prefsUrl(token) {
  return SITE + '/preferences?t=' + encodeURIComponent(token || '{{unsubscribe_token}}');
}

export function mailerConfigured() {
  return !!(process.env.GMAIL_REFRESH_TOKEN && process.env.GMAIL_CLIENT_ID && process.env.GMAIL_CLIENT_SECRET);
}

function fromAddress() {
  return process.env.WELCOME_FROM || 'Khatakshetra <vyasa@khatakshetra.com>';
}

/**
 * The shared visual shell: dark surround, parchment card, gold masthead —
 * matching the website and the printed kits.
 *
 * @param {object} o - { title, preheader, token, bodyHtml, footerNote }
 */
export function emailShell(o) {
  o = o || {};
  const manage = o.token ? prefsUrl(o.token) : '{{unsubscribe_url}}';
  return '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1.0">' +
    '<meta http-equiv="X-UA-Compatible" content="IE=edge">' +
    '<title>' + esc(o.title || 'Khatakshetra') + '</title></head>' +
    '<body style="margin:0;padding:0;background:#160d02;-webkit-text-size-adjust:100%;">' +
    '<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#160d02;font-size:1px;line-height:1px;">' +
      esc(o.preheader || '') + '</div>' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#160d02;">' +
    '<tr><td align="center" style="padding:28px 16px;">' +
      '<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background:#FBF3E2;border:1px solid #E2C98A;border-radius:14px;overflow:hidden;">' +
        '<tr><td align="center" style="background:#2A1206;padding:22px 24px;">' +
          '<span style="font-family:Georgia,serif;font-size:22px;font-weight:bold;letter-spacing:2px;color:#E8B94F;">KHATAKSHETRA</span>' +
          '<div style="font-family:Georgia,serif;font-size:12px;color:#C9A86B;letter-spacing:1px;margin-top:4px;">Itihasa &amp; Purana, brought to life</div>' +
        '</td></tr>' +
        o.bodyHtml +
        '<tr><td style="padding:22px 36px 30px 36px;font-family:Georgia,serif;border-top:1px solid #ECDDB8;">' +
          '<p style="margin:0;font-size:13px;line-height:1.6;color:#7a6a4a;">' +
            (o.footerNote ? esc(o.footerNote) + '<br><br>' : '') +
            'You are getting this because you joined Khatakshetra Family. ' +
            '<a href="' + manage + '" target="_blank" style="color:#6B1A1A;">Choose what you receive or unsubscribe</a> &mdash; one click, no hard feelings.' +
          '</p>' +
        '</td></tr>' +
      '</table>' +
    '</td></tr></table></body></html>';
}

/** A numbered step row, matching the welcome email. */
export function stepRow(n, href, title, line) {
  return '<tr><td style="padding:11px 0;border-bottom:1px solid #ECDDB8;">' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>' +
      '<td width="46" valign="top">' +
        '<div style="width:30px;height:30px;border-radius:50%;background:#E07B1A;color:#FBF3E2;font-family:Georgia,serif;font-weight:bold;font-size:15px;text-align:center;line-height:30px;">' + n + '</div>' +
      '</td>' +
      '<td valign="top" style="font-family:Georgia,serif;">' +
        '<a href="' + SITE + href + '" target="_blank" style="color:#6B1A1A;text-decoration:none;font-size:17px;font-weight:bold;">' + title + ' &rarr;</a>' +
        '<div style="font-size:14px;color:#5a4a2a;line-height:1.5;margin-top:2px;">' + line + '</div>' +
      '</td>' +
    '</tr></table>' +
  '</td></tr>';
}

/** A big gold call-to-action button (table-based, so Outlook renders it). */
export function buttonRow(href, label) {
  return '<tr><td align="center" style="padding:8px 36px 26px 36px;">' +
    '<table role="presentation" cellpadding="0" cellspacing="0"><tr>' +
      '<td align="center" style="background:#E07B1A;border-radius:9px;">' +
        '<a href="' + (href.indexOf('http') === 0 ? href : SITE + href) + '" target="_blank" ' +
        'style="display:inline-block;padding:13px 26px;font-family:Georgia,serif;font-size:16px;font-weight:bold;color:#FBF3E2;text-decoration:none;">' +
        label + '</a>' +
      '</td>' +
    '</tr></table>' +
  '</td></tr>';
}

// ── Gmail API (OAuth2 refresh token; HTTPS only, no dependencies) ──
function b64(str) { return Buffer.from(str, 'utf8').toString('base64'); }
function b64url(str) {
  return Buffer.from(str, 'utf8').toString('base64')
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
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

/**
 * Send one email. Returns { sent, messageId } or { sent:false, reason, detail }
 * — never throws, so one bad address can't abort a drip run.
 *
 * @param {object} o - { to, subject, html, token }
 */
export async function sendMail(o) {
  o = o || {};
  if (!mailerConfigured()) return { sent: false, reason: 'gmail_not_configured' };

  const from = fromAddress();
  const manageHttps = prefsUrl(o.token);
  const fromEmail = (from.match(/<([^>]+)>/) || [])[1] || 'vyasa@khatakshetra.com';
  const unsubMailto = 'mailto:' + fromEmail + '?subject=unsubscribe';

  try {
    const accessToken = await getAccessToken();
    const message = [
      'From: ' + from,
      'To: ' + o.to,
      'Subject: ' + o.subject,
      'MIME-Version: 1.0',
      'List-Unsubscribe: <' + manageHttps + '>, <' + unsubMailto + '>',
      'List-Unsubscribe-Post: List-Unsubscribe=One-Click',
      'Content-Type: text/html; charset="UTF-8"',
      'Content-Transfer-Encoding: base64',
      '',
      wrap76(b64(o.html))
    ].join('\r\n');

    const resp = await fetch('https://gmail.googleapis.com/gmail/v1/users/me/messages/send', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + accessToken, 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw: b64url(message) })
    });
    if (!resp.ok) {
      return { sent: false, reason: 'gmail_send_error', status: resp.status, detail: (await resp.text()).slice(0, 400) };
    }
    const body = await resp.json().catch(function () { return {}; });
    return { sent: true, messageId: body.id || '' };
  } catch (e) {
    return { sent: false, reason: 'exception', detail: String(e).slice(0, 400) };
  }
}
