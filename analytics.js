/**
 * Khatakshetra analytics — GA4 + PostHog, loaded on every page (incl. the homepage).
 * Safe no-op until you set the two IDs below; no tracking fires while they are placeholders.
 *
 *  ┌──────────────────────────────────────────────────────────────────────┐
 *  │  TO TURN ON ANALYTICS: replace the two placeholder values below.        │
 *  │    ga4Id      → your Google Analytics 4 Measurement ID (starts "G-")   │
 *  │    posthogKey → your PostHog project API key (starts "phc_")           │
 *  │  (Use the SAME ga4Id/posthogKey in site.js too, for non-home pages.)   │
 *  └──────────────────────────────────────────────────────────────────────┘
 *
 * Usage anywhere:  window.trackKhatakshetra('event_name', { any: 'props' });
 */
(function () {
  var ANALYTICS = {
    ga4Id: 'G-X9NTBSLFTJ',            // ← replace with real GA4 id, e.g. 'G-AB12CD34EF'
    posthogKey: 'phc_CqRMmaREFGZM3gQdhp3xF3nc3h4MCyfhASP9jjzbT4GZ', // ← replace with real PostHog key, e.g. 'phc_abc123...'
    posthogHost: 'https://us.i.posthog.com'
  };

  if (window.__khAnalyticsLoaded) return;
  window.__khAnalyticsLoaded = true;

  // A value is "real" only if it has the right prefix AND contains no placeholder X's.
  var hasGA = /^G-/.test(ANALYTICS.ga4Id) && ANALYTICS.ga4Id.indexOf('X') === -1;
  var hasPH = /^phc_/.test(ANALYTICS.posthogKey) && ANALYTICS.posthogKey.indexOf('X') === -1;

  // ── Google Analytics 4 ──
  if (hasGA) {
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
  if (hasPH) {
    !function (t, e) { var o, n, p, r; e.__SV || (window.posthog = e, e._i = [], e.init = function (i, s, a) { function g(t, e) { var o = e.split("."); 2 == o.length && (t = t[o[0]], e = o[1]), t[e] = function () { t.push([e].concat(Array.prototype.slice.call(arguments, 0))) } } (p = t.createElement("script")).type = "text/javascript", p.async = !0, p.src = s.api_host + "/static/array.js", (r = t.getElementsByTagName("script")[0]).parentNode.insertBefore(p, r); var u = e; for (void 0 !== a ? u = e[a] = [] : a = "posthog", u.people = u.people || [], u.toString = function (t) { var e = "posthog"; return "posthog" !== a && (e += "." + a), t || (e += " (stub)"), e }, u.people.toString = function () { return u.toString(1) + ".people (stub)" }, o = "capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures getActiveMatchingSurveys getSurveys getNextSurveyStep".split(" "), n = 0; n < o.length; n++) g(u, o[n]); e._i.push([i, s, a]) }, e.__SV = 1) }(document, window.posthog || []);
    window.posthog.init(ANALYTICS.posthogKey, { api_host: ANALYTICS.posthogHost, capture_pageview: true });
  }

  // ── Unified tracker (no-ops safely if analytics are off) ──
  window.trackKhatakshetra = function (event, props) {
    props = props || {};
    try { if (hasGA && window.gtag) window.gtag('event', event, props); } catch (e) {}
    try { if (hasPH && window.posthog && window.posthog.capture) window.posthog.capture(event, props); } catch (e) {}
  };

  // Automatic pageview for GA4 is handled by config; PostHog by capture_pageview.
})();
