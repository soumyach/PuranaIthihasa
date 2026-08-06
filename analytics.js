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
    try { if (hasGA && window.gtag) window.gtag('event', 'sign_up', payload); } catch (e) {}
    try { if (hasPH && window.posthog && window.posthog.capture) window.posthog.capture('signup', payload); } catch (e) {}
    try { if (hasPixel && window.fbq) window.fbq('track', 'Lead', { content_name: payload.cta }); } catch (e) {}
    try { if (hasClarity && window.clarity) { window.clarity('event', 'signup'); window.clarity('set', 'signup_cta', payload.cta); } } catch (e) {}
  };
})();
