// season-game.js — the three-round season challenge (Ganapati pilot).
//
// Data-driven: the page embeds its rounds as JSON, so Navaratri gets a game by
// adding JSON, not by writing another engine. Reuses the site's existing
// systems rather than duplicating them — getKhatakshetraProfile / XP,
// revealTalapatraCard, kxShare and trackKhatakshetraEvent all come from
// site.js and analytics.js.
//
// Deliberately local-state only: no answers, scores or personal data ever go
// into the URL or to a server, so a shared result link exposes nothing.
(function () {
  'use strict';

  const dataEl = document.getElementById('kxGameData');
  if (!dataEl) return;

  let GAME;
  try { GAME = JSON.parse(dataEl.textContent); } catch (e) { return; }

  const root = document.getElementById('kxGame');
  if (!root || !GAME || !GAME.rounds) return;

  const MATCH_POINTS = 5;          // the matching round is worth 5 of the 15
  const state = { round: 0, score: 0, answered: [], matchCorrect: 0, started: false };

  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function track(name, props) {
    if (typeof trackKhatakshetraEvent === 'function') trackKhatakshetraEvent(name, props || {});
  }
  function reduceMotion() {
    return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }
  function shuffle(a) {
    const out = a.slice();
    for (let i = out.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [out[i], out[j]] = [out[j], out[i]];
    }
    return out;
  }

  function maxScore() {
    return GAME.rounds.reduce(function (n, r) {
      return n + (r.kind === 'match' ? MATCH_POINTS : (r.questions || []).length);
    }, 0);
  }

  function progressBar() {
    return '<div class="kg-prog" aria-hidden="true">' +
      GAME.rounds.map(function (r, i) {
        const cls = i < state.round ? 'is-done' : (i === state.round ? 'is-now' : '');
        return '<span class="kg-prog-step ' + cls + '"></span>';
      }).join('') + '</div>';
  }

  function roundHeader(r) {
    return '<p class="kg-eyebrow">Round ' + (state.round + 1) + ' of ' + GAME.rounds.length + '</p>' +
      '<h2 class="kg-round-title">' + esc(r.title) + '</h2>' +
      (r.blurb ? '<p class="kg-blurb">' + esc(r.blurb) + '</p>' : '') +
      progressBar();
  }

  // ── multiple choice ────────────────────────────────────────────────────────
  function renderMcq(r) {
    let qi = 0;

    function paint() {
      const q = r.questions[qi];
      root.innerHTML =
        roundHeader(r) +
        '<div class="kg-card">' +
          '<p class="kg-qn">Question ' + (qi + 1) + ' of ' + r.questions.length + '</p>' +
          '<p class="kg-q">' + esc(q.q) + '</p>' +
          '<div class="kg-choices" role="group" aria-label="Choices">' +
            shuffle(q.choices).map(function (c) {
              return '<button class="kg-choice" type="button" data-choice="' + esc(c) + '">' + esc(c) + '</button>';
            }).join('') +
          '</div>' +
          '<div class="kg-after" id="kgAfter" hidden></div>' +
        '</div>';

      Array.prototype.forEach.call(root.querySelectorAll('.kg-choice'), function (btn) {
        btn.addEventListener('click', function () { choose(btn, q); });
      });
      const first = root.querySelector('.kg-choice');
      if (first) first.focus();
    }

    function choose(btn, q) {
      if (root.querySelector('.kg-choices.is-locked')) return;
      root.querySelector('.kg-choices').classList.add('is-locked');
      const picked = btn.getAttribute('data-choice');
      const correct = picked === q.answer;
      if (correct) state.score += 1;
      state.answered.push(correct);

      Array.prototype.forEach.call(root.querySelectorAll('.kg-choice'), function (b) {
        const v = b.getAttribute('data-choice');
        if (v === q.answer) b.classList.add('is-right');
        else if (b === btn) b.classList.add('is-wrong');
        b.disabled = true;
      });

      track('game_question_answer', { game: GAME.slug, round: r.id, question: qi + 1, correct: correct });

      // Every answer says where it comes from — the same rule as the articles.
      const after = document.getElementById('kgAfter');
      after.hidden = false;
      after.innerHTML =
        '<p class="kg-verdict ' + (correct ? 'is-right' : 'is-wrong') + '">' +
          (correct ? 'Correct.' : 'Not quite — ' + esc(q.answer) + '.') + '</p>' +
        (q.why ? '<p class="kg-why">' + esc(q.why) + '</p>' : '') +
        (q.source ? '<p class="kg-src">Source: ' + esc(q.source) + '</p>' : '') +
        '<button class="kx-btn kx-btn-primary kg-next" type="button">' +
          (qi + 1 < r.questions.length ? 'Next question' : 'Next round') + ' &rarr;</button>';
      const next = after.querySelector('.kg-next');
      next.addEventListener('click', function () {
        qi += 1;
        if (qi < r.questions.length) paint(); else advanceRound();
      });
      next.focus();
    }

    paint();
  }

  // ── match the eight ────────────────────────────────────────────────────────
  // Tap a manifestation, then tap the adversary. Tap-to-pair rather than drag:
  // it works on touch, with a keyboard, and with a screen reader.
  function renderMatch(r) {
    const pairs = GAME.pairs || [];
    let selected = null;
    let done = 0;

    root.innerHTML =
      roundHeader(r) +
      '<div class="kg-card">' +
        '<div class="kg-match">' +
          '<div class="kg-col"><p class="kg-col-h">Manifestation</p>' +
            shuffle(pairs).map(function (p) {
              return '<button class="kg-tile" type="button" data-side="form" data-key="' + esc(p.key) + '">' + esc(p.form) + '</button>';
            }).join('') +
          '</div>' +
          '<div class="kg-col"><p class="kg-col-h">Confronts</p>' +
            shuffle(pairs).map(function (p) {
              return '<button class="kg-tile" type="button" data-side="asura" data-key="' + esc(p.key) + '">' +
                esc(p.asura) + '<span class="kg-tile-sub">' + esc(p.obstacle) + '</span></button>';
            }).join('') +
          '</div>' +
        '</div>' +
        '<p class="kg-match-msg" id="kgMatchMsg" role="status" aria-live="polite">' +
          (r.note ? esc(r.note) : '') + '</p>' +
        '<div class="kg-after" id="kgAfter" hidden></div>' +
      '</div>';

    const msg = document.getElementById('kgMatchMsg');

    function clearSel() {
      Array.prototype.forEach.call(root.querySelectorAll('.kg-tile.is-sel'), function (t) {
        t.classList.remove('is-sel');
      });
      selected = null;
    }

    Array.prototype.forEach.call(root.querySelectorAll('.kg-tile'), function (tile) {
      tile.addEventListener('click', function () {
        if (tile.disabled) return;

        if (!selected) {
          clearSel();
          selected = tile;
          tile.classList.add('is-sel');
          return;
        }
        if (selected === tile) { clearSel(); return; }
        if (selected.getAttribute('data-side') === tile.getAttribute('data-side')) {
          // same column — treat as changing your mind
          clearSel();
          selected = tile;
          tile.classList.add('is-sel');
          return;
        }

        const a = selected, b = tile;
        const hit = a.getAttribute('data-key') === b.getAttribute('data-key');
        track('game_question_answer', { game: GAME.slug, round: r.id, question: done + 1, correct: hit });

        if (hit) {
          [a, b].forEach(function (t) {
            t.classList.remove('is-sel');
            t.classList.add('is-matched');
            t.disabled = true;
          });
          done += 1;
          state.matchCorrect = done;
          msg.textContent = done + ' of ' + pairs.length + ' paired.';
          selected = null;
          if (done === pairs.length) finishMatch();
        } else {
          [a, b].forEach(function (t) { t.classList.add('is-miss'); });
          msg.textContent = 'Not that one.';
          const pairRefs = [a, b];
          setTimeout(function () {
            pairRefs.forEach(function (t) { t.classList.remove('is-miss', 'is-sel'); });
          }, reduceMotion() ? 0 : 420);
          selected = null;
        }
      });
    });

    function finishMatch() {
      // The matching round is worth MATCH_POINTS, scaled by how many you paired.
      const earned = Math.round((done / pairs.length) * MATCH_POINTS);
      state.score += earned;
      const after = document.getElementById('kgAfter');
      after.hidden = false;
      after.innerHTML =
        '<p class="kg-verdict is-right">All eight paired &mdash; ' + earned + ' of ' + MATCH_POINTS + ' points.</p>' +
        '<p class="kg-why">Each adversary is named for the state of mind the manifestation meets: envy, intoxicated pride, delusion, greed, anger, craving, possessiveness, ego.</p>' +
        '<p class="kg-src">Source: Mudgala Purāṇa, Khaṇḍas 1–8.</p>' +
        '<button class="kx-btn kx-btn-primary kg-next" type="button">Next round &rarr;</button>';
      const next = after.querySelector('.kg-next');
      next.addEventListener('click', advanceRound);
      next.focus();
    }
  }

  // ── result ─────────────────────────────────────────────────────────────────
  function tierFor(score) {
    let best = GAME.tiers[0];
    GAME.tiers.forEach(function (t) { if (score >= t.min) best = t; });
    return best;
  }

  function renderResult() {
    const total = maxScore();
    const tier = tierFor(state.score);
    const pips = state.answered.map(function (ok) { return ok ? '●' : '○'; }).join('');
    const shareText = String(GAME.shareText || 'I scored {score}/{total}')
      .replace('{score}', state.score).replace('{total}', total);

    root.innerHTML =
      '<div class="kg-card kg-result">' +
        '<p class="kg-eyebrow">Your score</p>' +
        '<p class="kg-score">' + state.score + '<span>/' + total + '</span></p>' +
        '<h2 class="kg-tier">' + esc(tier.label) + '</h2>' +
        '<p class="kg-tier-note">' + esc(tier.note) + '</p>' +
        '<div class="kg-actions">' +
          '<button class="kx-btn kx-btn-primary" type="button" id="kgShare">Share your score</button>' +
          '<a class="kx-btn" href="/ganapati/eight-manifestations" data-kx-cta="game_to_eight">Read the eight</a>' +
          '<button class="kx-btn" type="button" id="kgAgain">Play again</button>' +
        '</div>' +
      '</div>';

    track('game_complete', { game: GAME.slug, score: state.score, total: total, tier: tier.label, pips: pips });

    if (typeof awardKhatakshetraProgress === 'function') {
      try {
        awardKhatakshetraProgress('game_complete', {
          xp: 20 + state.score * 2, track: 'story_mastery',
          properties: { game: GAME.slug, score: state.score }
        });
      } catch (e) {}
    }

    // A card for a genuinely good score, using the site's existing reward.
    if (GAME.card && state.score >= 11 && typeof revealTalapatraCard === 'function') {
      setTimeout(function () { try { revealTalapatraCard(GAME.card); } catch (e) {} }, 500);
    }

    document.getElementById('kgShare').addEventListener('click', function () {
      // No answers and no score in the URL — the link is just the game.
      const url = 'https://khatakshetra.com/ganapati/eight-obstacles';
      track('share_click', { surface: 'season_game', score: state.score });
      if (typeof window.kxShare === 'function') window.kxShare({ text: shareText, url: url });
      else window.open('https://wa.me/?text=' + encodeURIComponent(shareText + ' ' + url), '_blank', 'noopener');
    });
    document.getElementById('kgAgain').addEventListener('click', function () {
      state.round = 0; state.score = 0; state.answered = []; state.matchCorrect = 0;
      renderRound();
    });
  }

  // ── flow ───────────────────────────────────────────────────────────────────
  function advanceRound() {
    state.round += 1;
    if (state.round < GAME.rounds.length) renderRound();
    else renderResult();
    try { root.scrollIntoView({ behavior: reduceMotion() ? 'auto' : 'smooth', block: 'start' }); } catch (e) {}
  }

  function renderRound() {
    const r = GAME.rounds[state.round];
    if (!r) return renderResult();
    if (r.kind === 'match') renderMatch(r); else renderMcq(r);
  }

  function start() {
    if (state.started) return;
    state.started = true;
    track('game_start', { game: GAME.slug });
    renderRound();
  }

  // Intro screen first, so the page is readable before it becomes a game.
  root.innerHTML =
    '<div class="kg-card kg-intro">' +
      '<p class="kg-eyebrow">' + GAME.rounds.length + ' rounds &middot; about four minutes</p>' +
      '<h2 class="kg-round-title">' + esc(GAME.title) + '</h2>' +
      '<p class="kg-blurb">' + esc(GAME.intro || '') + '</p>' +
      '<ol class="kg-rounds">' +
        GAME.rounds.map(function (r) {
          return '<li><strong>' + esc(r.title) + '</strong> &mdash; ' + esc(r.blurb || '') + '</li>';
        }).join('') +
      '</ol>' +
      '<button class="kx-btn kx-btn-primary" type="button" id="kgStart">Start the challenge &rarr;</button>' +
    '</div>';
  document.getElementById('kgStart').addEventListener('click', start);
})();
