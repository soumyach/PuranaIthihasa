/**
 * Khatakshetra tracking — the single source of truth for all analytics.
 * Loaded on EVERY page. Handles:
 *   • Google Analytics 4  — the tag itself lives hardcoded in each <head>;
 *                           this file only sends events to it.
 *   • PostHog             — product analytics / funnels / retention
 *   • Microsoft Clarity   — heatmaps + session recordings
 *   • Meta Pixel          — ad optimisation, lookalikes, retargeting
 *   • First-touch attribution (UTM + referrer) so every subscriber can be
 *     traced back to the channel that produced them.
 *
 *  ┌────────────────────────────────────────────────────────────────────┐
 *  │  IDs — set one and that tool switches on.                          │
 *  │  A placeholder value = that tool stays completely dormant.         │
 *  └────────────────────────────────────────────────────────────────────┘
 *
 * Public API (safe to call anywhere; no-ops if a tool is off):
 *   trackKhatakshetra('event_name', { any: 'props' })
 *   trackKhatakshetraSignup({ cta: 'starter_story_kit', segment: 'abroad' })
 *   khatakshetraAttribution()  -> { utm_source, utm_medium, ..., referrer, landing_page }
 */
(function () {
  var ANALYTICS = {
    ga4Id: 'G-X9NTBSLFTJ',
    posthogKey: 'phc_CqRMmaREFGZM3gQdhp3xF3nc3h4MCyfhASP9jjzbT4GZ',
    posthogHost: 'https://us.i.posthog.com',
    clarityId: 'xy5d1aa1xi',
    metaPixelId: 'PIXEL_ID_PLACEHOLDER'   // ← replace with your Meta Pixel ID (digits only, e.g. '1234567890123456')
  };

  if (window.__khAnalyticsLoaded) return;
  window.__khAnalyticsLoaded = true;

  function isReal(v, placeholder) { return !!v && v !== placeholder && v.indexOf('PLACEHOLDER') === -1; }
  var hasGA = /^G-/.test(ANALYTICS.ga4Id) && ANALYTICS.ga4Id !== 'G-XXXXXXXXXX';
  var hasPH = /^phc_/.test(ANALYTICS.posthogKey) && ANALYTICS.posthogKey !== 'phc_XXXXXXXXXXXXXXXX';
  var hasClarity = isReal(ANALYTICS.clarityId, 'CLARITY_ID_PLACEHOLDER');
  var hasPixel = isReal(ANALYTICS.metaPixelId, 'PIXEL_ID_PLACEHOLDER') && /^\d+$/.test(ANALYTICS.metaPixelId);

  // ── Google Analytics 4 ──
  // The gtag snippet is hardcoded in every <head>, so window.gtag already
  // exists. This only loads it as a fallback (a page missing the snippet), so
  // a page can never end up with two Google tags.
  if (hasGA && typeof window.gtag !== 'function') {
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + ANALYTICS.ga4Id;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', ANALYTICS.ga4Id);
  }

  // ── PostHog ──
  // Guarded: site.js also initialises PostHog on some pages. First one wins.
  if (hasPH && !window.__khPosthogInit && !window.posthog) {
    window.__khPosthogInit = true;
    !function (t, e) { var o, n, p, r; e.__SV || (window.posthog = e, e._i = [], e.init = function (i, s, a) { function g(t, e) { var o = e.split("."); 2 == o.length && (t = t[o[0]], e = o[1]), t[e] = function () { t.push([e].concat(Array.prototype.slice.call(arguments, 0))) } } (p = t.createElement("script")).type = "text/javascript", p.async = !0, p.src = s.api_host + "/static/array.js", (r = t.getElementsByTagName("script")[0]).parentNode.insertBefore(p, r); var u = e; for (void 0 !== a ? u = e[a] = [] : a = "posthog", u.people = u.people || [], u.toString = function (t) { var e = "posthog"; return "posthog" !== a && (e += "." + a), t || (e += " (stub)"), e }, u.people.toString = function () { return u.toString(1) + ".people (stub)" }, o = "capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures getActiveMatchingSurveys getSurveys getNextSurveyStep".split(" "), n = 0; n < o.length; n++) g(u, o[n]); e._i.push([i, s, a]) }, e.__SV = 1) }(document, window.posthog || []);
    window.posthog.init(ANALYTICS.posthogKey, { api_host: ANALYTICS.posthogHost, capture_pageview: true });
  }

  // ── Microsoft Clarity (heatmaps + session recordings) ──
  if (hasClarity && !window.clarity) {
    (function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments) };
      t = l.createElement(r); t.async = 1; t.src = 'https://www.clarity.ms/tag/' + i;
      y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
    })(window, document, 'clarity', 'script', ANALYTICS.clarityId);
  }

  // ── Meta Pixel (dormant until metaPixelId is set) ──
  if (hasPixel && !window.fbq) {
    !function (f, b, e, v, n, t, s) {
      if (f.fbq) return; n = f.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments) };
      if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = '2.0'; n.queue = [];
      t = b.createElement(e); t.async = !0; t.src = v; s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
    }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
    window.fbq('init', ANALYTICS.metaPixelId);
    window.fbq('track', 'PageView');
  }

  // ── First-touch attribution ─────────────────────────────────────────
  // Captured once, on the visitor's FIRST landing, kept in localStorage.
  // First-touch (not last) is what answers "which channel produced this
  // subscriber?" even when they return directly, days later, to sign up.
  var ATTR_KEY = 'khatakshetra_attribution';
  function captureAttribution() {
    try {
      var existing = JSON.parse(localStorage.getItem(ATTR_KEY) || 'null');
      if (existing && existing.landing_page) return existing;   // first touch already recorded
      var q = new URLSearchParams(window.location.search);
      var attr = {
        utm_source: q.get('utm_source') || '',
        utm_medium: q.get('utm_medium') || '',
        utm_campaign: q.get('utm_campaign') || '',
        utm_content: q.get('utm_content') || '',
        utm_term: q.get('utm_term') || '',
        ref: q.get('ref') || '',            // referral code — for the Day-17 referral loop
        fbclid: q.get('fbclid') || '',
        gclid: q.get('gclid') || '',
        referrer: document.referrer || '',
        landing_page: window.location.pathname || '/',
        first_seen: new Date().toISOString()
      };
      localStorage.setItem(ATTR_KEY, JSON.stringify(attr));
      return attr;
    } catch (e) { return {}; }
  }
  var attribution = captureAttribution();
  window.khatakshetraAttribution = function () {
    try { return JSON.parse(localStorage.getItem(ATTR_KEY) || '{}'); } catch (e) { return {}; }
  };

  // Surface the channel inside the analytics tools too, not just our database.
  try {
    if (attribution && attribution.utm_source) {
      if (hasPH && window.posthog && window.posthog.register) {
        window.posthog.register({ first_utm_source: attribution.utm_source, first_utm_campaign: attribution.utm_campaign });
      }
      if (hasClarity && window.clarity) window.clarity('set', 'utm_source', attribution.utm_source);
    }
  } catch (e) {}

  // ── Unified event tracking (fans out to every tool that is switched on) ──
  window.trackKhatakshetra = function (event, props) {
    props = props || {};
    try { if (hasGA && window.gtag) window.gtag('event', event, props); } catch (e) {}
    try { if (hasPH && window.posthog && window.posthog.capture) window.posthog.capture(event, props); } catch (e) {}
    try { if (hasPixel && window.fbq) window.fbq('trackCustom', event, props); } catch (e) {}
    try { if (hasClarity && window.clarity) window.clarity('event', event); } catch (e) {}
  };

  // ── Which channel did this visitor come from? ─────────────────────────
  // Explicit resolution so YouTube / Instagram traffic is countable even when
  // a link gets shared without UTMs (referrer fallback).
  function resolveChannel(attr) {
    var src = (attr.utm_source || '').toLowerCase();
    if (src) return src;
    var r = (attr.referrer || '').toLowerCase();
    if (!r) return 'direct';
    if (r.indexOf('youtube.') !== -1 || r.indexOf('youtu.be') !== -1) return 'youtube';
    if (r.indexOf('instagram.') !== -1) return 'instagram';
    if (r.indexOf('facebook.') !== -1) return 'facebook';
    if (r.indexOf('whatsapp') !== -1 || r.indexOf('wa.me') !== -1) return 'whatsapp';
    if (r.indexOf('t.co') !== -1 || r.indexOf('twitter.') !== -1 || r.indexOf('x.com') !== -1) return 'twitter';
    if (r.indexOf('pinterest.') !== -1) return 'pinterest';
    if (r.indexOf('t.me') !== -1 || r.indexOf('telegram') !== -1) return 'telegram';
    if (r.indexOf('google.') !== -1 || r.indexOf('bing.') !== -1) return 'search';
    if (r.indexOf('khatakshetra.com') !== -1) return 'internal';
    return 'referral';
  }
  window.khatakshetraChannel = function () { return resolveChannel(window.khatakshetraAttribution()); };

  // ── Product events (names per the growth spec) ────────────────────────
  // ON DOUBLE-COUNTING: the spec's `member_created` is the same action as
  // GA4's conventional `sign_up`. We deliberately fire ONE conversion event
  // (`sign_up`, which GA4 and Meta optimise against) instead of both, so the
  // conversion numbers stay trustworthy. Everything below is descriptive.
  function ev(name, props) { if (window.trackKhatakshetra) window.trackKhatakshetra(name, props || {}); }

  window.kxTrack = {
    landingView: function (path) {
      var a = window.khatakshetraAttribution();
      ev('landing_view', {
        channel: resolveChannel(a), landing_path: path || location.pathname,
        utm_source: a.utm_source || '', utm_medium: a.utm_medium || '',
        utm_campaign: a.utm_campaign || '', utm_content: a.utm_content || ''
      });
    },
    ctaClick: function (placement, page) {
      ev('membership_cta_click', {
        placement: placement || '', page: page || location.pathname,
        campaign: window.khatakshetraAttribution().utm_campaign || ''
      });
    },
    activityStarted: function (type, subject) { ev('activity_started', { activity_type: type, subject: subject || '' }); },
    activityCompleted: function (type, subject, progress) {
      ev('activity_completed', { activity_type: type, subject: subject || '', progress: progress || '' });
    },
    talapatraUnlocked: function (cardId, from) { ev('talapatra_unlocked', { card_id: cardId, source_activity: from || '' }); },
    journeyProgress: function (journeyId, node, pct) { ev('journey_progress', { journey_id: journeyId, node: node, completion_pct: pct }); },
    kitWaitlist: function (festival, from) { ev('kit_waitlist_join', { festival: festival, source_content: from || '' }); }
  };

  // Fire landing_view once per page load, and detect returning members.
  try {
    window.kxTrack.landingView();
    var joined = localStorage.getItem('khatakshetra_joined_at');
    if (joined) {
      var days = Math.floor((Date.now() - parseInt(joined, 10)) / 86400000);
      var seenKey = 'kx_return_' + new Date().toISOString().slice(0, 10);
      if (!sessionStorage.getItem(seenKey)) {
        sessionStorage.setItem(seenKey, '1');
        ev('return_visit', { days_since_join: days, channel: resolveChannel(window.khatakshetraAttribution()) });
      }
    }
  } catch (e) {}


  // ── Sharing (WhatsApp first — it is how Indian families actually share) ──
  window.kxShare = function (opts) {
    opts = opts || {};
    var url = opts.url || (location.origin + location.pathname);
    var text = opts.text || document.title;
    var full = text + ' ' + url;
    ev('share_clicked', { channel: opts.channel || 'whatsapp', page: location.pathname });
    if (opts.channel === 'native' && navigator.share) {
      navigator.share({ title: document.title, text: text, url: url }).catch(function () {});
      return;
    }
    window.open('https://wa.me/?text=' + encodeURIComponent(full), '_blank', 'noopener');
  };

  // Any element with data-kx-share becomes a WhatsApp share button.
  document.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('[data-kx-share]');
    if (!el) return;
    e.preventDefault();
    window.kxShare({ text: el.getAttribute('data-kx-share') || document.title,
                     url: el.getAttribute('data-kx-share-url') || undefined });
  });

  // Any element with data-kx-cta reports itself as a membership CTA click.
  document.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('[data-kx-cta]');
    if (el && window.kxTrack) window.kxTrack.ctaClick(el.getAttribute('data-kx-cta'));
  });

  /**
   * The canonical subscriber conversion — call the moment a signup succeeds.
   * Sends each tool its *native* event so GA4 key-events, Meta ad optimisation
   * and PostHog funnels all line up on the same conversion.
   */
  window.trackKhatakshetraSignup = function (opts) {
    opts = opts || {};
    var attr = window.khatakshetraAttribution();
    var payload = {
      cta: opts.cta || 'unknown',
      segment: opts.segment || '',
      utm_source: attr.utm_source || '',
      utm_medium: attr.utm_medium || '',
      utm_campaign: attr.utm_campaign || '',
      referrer: attr.referrer || ''
    };
    // Stamp the join so we can measure return visits and day-N retention.
    try { if (!localStorage.getItem('khatakshetra_joined_at')) localStorage.setItem('khatakshetra_joined_at', String(Date.now())); } catch (e) {}
    payload.channel = resolveChannel(attr);
    try { if (hasGA && window.gtag) window.gtag('event', 'sign_up', payload); } catch (e) {}
    try { if (hasPH && window.posthog && window.posthog.capture) window.posthog.capture('signup', payload); } catch (e) {}
    try { if (hasPixel && window.fbq) window.fbq('track', 'Lead', { content_name: payload.cta }); } catch (e) {}
    try { if (hasClarity && window.clarity) { window.clarity('event', 'signup'); window.clarity('set', 'signup_cta', payload.cta); } } catch (e) {}
  };
})();
