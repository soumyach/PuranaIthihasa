/**
 * lib/drip-emails.js — the emails that arrive after the welcome.
 *
 * The welcome email delivers what was promised. These three exist to bring a
 * family BACK, which nothing on the site currently does:
 *
 *   day2    (+2 days)  one question to ask at dinner tonight
 *   day5    (+5 days)  the streak and the next festival pack
 *   weekly  (weekly)   three things only: a story, something to do, what's next
 *
 * Each is short on purpose. A parent reading on a phone between two tasks needs
 * one clear thing to do, not a newsletter.
 */

import { SITE, esc, emailShell, stepRow, buttonRow } from './mailer.js';

/** A pull-quote style "ask this" block — the heart of the day-2 email. */
function askBlock(question) {
  return '<tr><td style="padding:6px 36px 20px 36px;">' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" ' +
      'style="background:#F4E8CC;border-left:4px solid #E07B1A;border-radius:8px;"><tr>' +
      '<td style="padding:16px 18px;font-family:Georgia,serif;">' +
        '<div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#A06A18;">Ask at the table</div>' +
        '<div style="font-size:18px;line-height:1.5;color:#3A2A12;font-style:italic;margin-top:6px;">' + esc(question) + '</div>' +
      '</td>' +
    '</tr></table>' +
  '</td></tr>';
}

function para(html, size) {
  return '<tr><td style="padding:0 36px 14px 36px;font-family:Georgia,serif;">' +
    '<p style="margin:0;font-size:' + (size || 16) + 'px;line-height:1.65;color:#4a3a1e;">' + html + '</p>' +
  '</td></tr>';
}

function heading(text) {
  return '<tr><td style="padding:30px 36px 10px 36px;font-family:Georgia,serif;">' +
    '<h1 style="margin:0;font-size:25px;line-height:1.3;color:#6B1A1A;">' + esc(text) + '</h1>' +
  '</td></tr>';
}

// ── DAY +2 ───────────────────────────────────────────────────────────────────
// The job: prove this is about the family talking, not about a website.
export function day2Email(o) {
  o = o || {};
  const name = o.name ? esc(o.name) : 'there';
  const subject = 'A question worth asking at dinner tonight';
  const body =
    heading('One question, tonight.') +
    para('The stories are the easy part, ' + name + '. What makes them stick is the two minutes afterwards, when someone at the table has to answer for themselves.') +
    para('Here is one that works on almost every family, and the youngest usually answers best:') +
    askBlock('Have you ever kept a promise that was hard to keep? What did it cost you?') +
    para('That is Rama’s exile in a single question &mdash; a promise made by someone else, honoured anyway, at the price of a kingdom. Read the katha first if you like, then ask. It takes ten minutes.') +
    buttonRow('/daily', 'Read today’s katha') +
    para('<span style="font-size:14px;color:#7a6a4a;">Or start the seven-day journey and get one of these, with the story and a card to keep, every evening: <a href="' + SITE + '/start" style="color:#6B1A1A;">the 7-day family journey</a>.</span>', 14);

  return {
    subject: subject,
    html: emailShell({
      title: subject, token: o.token, bodyHtml: body,
      preheader: 'One story, one question, ten minutes — and the youngest usually answers best.'
    })
  };
}

// ── DAY +5 ───────────────────────────────────────────────────────────────────
// The job: convert a one-off visit into a habit, using the streak and the
// festival that is actually coming next.
export function day5Email(o) {
  o = o || {};
  const fest = o.festival || null;   // { title, date, days, slug }
  const subject = fest
    ? (fest.title + ' is in ' + fest.days + ' days — here is the free pack')
    : 'Your next family story is waiting';

  let body = heading(fest ? fest.title + ' is close.' : 'Where you had got to.');

  if (fest) {
    body += para('It falls on <strong>' + esc(fest.date) + '</strong> &mdash; ' + fest.days + ' days away. The free family pack is ready now, so you are not printing colouring sheets at eleven at night before the festival.');
    body += para('<strong>What is in it:</strong> three colouring sheets from simple shapes to intricate ones, the story traced to its source, a family question, and a wisdom card to cut out and keep.');
    body += buttonRow('/festival/' + fest.slug, 'Open the free ' + esc(fest.title) + ' pack');
  } else {
    body += para('Every katha you finish leaves a talapatra card behind &mdash; a single line of wisdom you can keep and collect. They add up faster than you would expect.');
    body += buttonRow('/daily', 'Continue your streak');
  }

  body +=
    '<tr><td style="padding:8px 36px 4px 36px;font-family:Georgia,serif;">' +
      '<p style="margin:0 0 8px 0;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#A06A18;">Three ways families use this</p>' +
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">' +
        stepRow('1', '/daily', 'Ten minutes after dinner', 'One katha, one puzzle, one card. A streak the children will defend fiercely.') +
        stepRow('2', '/paint', 'Colour while you talk', 'Hand them a sheet and tell the story over it. Works on a phone or on paper.') +
        stepRow('3', '/kits', 'Print the festival kits', 'Free, and made to be photocopied for a class or a temple group.') +
      '</table>' +
    '</td></tr>';

  return {
    subject: subject,
    html: emailShell({
      title: subject, token: o.token, bodyHtml: body,
      preheader: fest ? ('The free ' + fest.title + ' pack — story, colouring and a question.')
                      : 'Your streak, your cards, and the next story.'
    })
  };
}

// ── WEEKLY DIGEST ────────────────────────────────────────────────────────────
// Deliberately three items. A long digest is a digest nobody opens twice.
export function weeklyEmail(o) {
  o = o || {};
  const fest = o.festival || null;
  const katha = o.katha || null;     // { title, teaser, theme }
  const subject = 'This week at Khatakshetra';

  let body = heading('This week, in three things.');
  body += para('No news, no round-up. One story worth reading, one thing to do with the children, and what is coming.');

  if (katha) {
    body += '<tr><td style="padding:6px 36px 4px 36px;font-family:Georgia,serif;">' +
      '<p style="margin:0 0 6px 0;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#A06A18;">Read</p>' +
      '<a href="' + SITE + '/daily" target="_blank" style="color:#6B1A1A;text-decoration:none;font-size:19px;font-weight:bold;">' + esc(katha.title) + ' &rarr;</a>' +
      '<div style="font-size:15px;color:#5a4a2a;line-height:1.6;margin-top:4px;">' + esc(katha.teaser) + '</div>' +
      '</td></tr>';
  }

  body += '<tr><td style="padding:16px 36px 4px 36px;font-family:Georgia,serif;">' +
    '<p style="margin:0 0 6px 0;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#A06A18;">Do</p>' +
    '<a href="' + SITE + '/paint" target="_blank" style="color:#6B1A1A;text-decoration:none;font-size:19px;font-weight:bold;">Colour a sheet together &rarr;</a>' +
    '<div style="font-size:15px;color:#5a4a2a;line-height:1.6;margin-top:4px;">Tap to fill, pinch to zoom, save the artwork. Nine sheets across the three festivals.</div>' +
    '</td></tr>';

  body += '<tr><td style="padding:16px 36px 4px 36px;font-family:Georgia,serif;">' +
    '<p style="margin:0 0 6px 0;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#A06A18;">Coming</p>' +
    (fest
      ? '<a href="' + SITE + '/festival/' + esc(fest.slug) + '" target="_blank" style="color:#6B1A1A;text-decoration:none;font-size:19px;font-weight:bold;">' + esc(fest.title) + ' &rarr;</a>' +
        '<div style="font-size:15px;color:#5a4a2a;line-height:1.6;margin-top:4px;">' + esc(fest.date) + ' &mdash; in ' + fest.days + ' days. The free family pack is already up.</div>'
      : '<div style="font-size:15px;color:#5a4a2a;line-height:1.6;">New kathas every day, and the next festival pack goes up well before the festival.</div>') +
    '</td></tr>';

  body += buttonRow('/daily', 'Open this week’s katha');

  return {
    subject: subject,
    html: emailShell({
      title: subject, token: o.token, bodyHtml: body,
      preheader: katha ? esc(katha.title) : 'One story, one thing to do, and what is coming.',
      footerNote: 'You are on the weekly digest. You can switch to festival-only emails at any time.'
    })
  };
}

export const TEMPLATES = { day2: day2Email, day5: day5Email, weekly: weeklyEmail };
