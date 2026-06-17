// "Which character are you?" — a shareable personality quiz. No signup, no DB.
// Loads its data from content/personality-quizzes.json; result is shareable via
// WhatsApp / copy (the social growth loop). Awards a little XP via site.js.
(function () {
  const params = new URLSearchParams(location.search);
  const quizId = params.get('quiz') || 'which-ramayana-character';
  let quiz = null;
  let index = 0;
  const scores = {};

  function el(id) { return document.getElementById(id); }

  function start(data) {
    quiz = data[quizId] || data['which-ramayana-character'];
    if (!quiz) return;
    document.title = `${quiz.title} - Khatakshetra`;
    Object.keys(quiz.results).forEach(function (k) { scores[k] = 0; });
    index = 0;
    renderQuestion();
  }

  function renderQuestion() {
    const q = quiz.questions[index];
    const total = quiz.questions.length;
    el('quizApp').innerHTML = `
      <article class="card featured">
        <div class="eyebrow">Question ${index + 1} of ${total}</div>
        <div class="progress-track" style="height:8px;background:rgba(255,255,255,.08);border:1px solid rgba(232,185,79,.2);margin:.5rem 0 1rem">
          <div style="height:100%;width:${Math.round((index / total) * 100)}%;background:linear-gradient(90deg,var(--gold,#e8b94f),var(--saffron,#e07b1a))"></div>
        </div>
        <h2>${q.q}</h2>
        <div id="optionList"></div>
      </article>
    `;
    const list = el('optionList');
    q.options.forEach(function (opt, i) {
      const b = document.createElement('button');
      b.className = 'btn';
      b.type = 'button';
      b.style.cssText = 'width:100%;justify-content:flex-start;text-align:left;margin:.4rem 0';
      b.textContent = opt.t;
      b.addEventListener('click', function () { choose(opt); });
      list.appendChild(b);
    });
  }

  function choose(opt) {
    (opt.s || []).forEach(function (k) { scores[k] = (scores[k] || 0) + 1; });
    index += 1;
    if (index < quiz.questions.length) renderQuestion();
    else renderResult();
  }

  function winner() {
    let best = null;
    let bestScore = -1;
    // Preserve declaration order for stable tie-breaks.
    Object.keys(quiz.results).forEach(function (k) {
      if ((scores[k] || 0) > bestScore) { best = k; bestScore = scores[k] || 0; }
    });
    return best;
  }

  function renderResult() {
    const key = winner();
    const r = quiz.results[key];
    if (typeof awardKhatakshetraProgress === 'function') {
      try {
        awardKhatakshetraProgress('personality_quiz_done', {
          xp: 10, track: 'story_mastery',
          properties: { quiz: quizId, result: key }
        });
      } catch (e) {}
    }
    const shareText = `I'm ${r.name} ${r.emoji} — ${r.archetype}. Which Ramayana character are you? Find out at https://khatakshetra.com/which-character`;
    el('quizApp').innerHTML = `
      <article class="card featured" style="text-align:center">
        <div class="eyebrow">You are</div>
        <div style="font-size:3rem;line-height:1">${r.emoji}</div>
        <h2 style="margin:.3rem 0">${r.name}</h2>
        <h3 style="color:var(--gold,#e8b94f);margin:.1rem 0 .6rem">${r.archetype}</h3>
        <p style="max-width:48ch;margin:0 auto 0.8rem">${r.blurb}</p>
        <div class="tag-row" style="justify-content:center">${(r.traits || []).map(function (t) { return `<span class="tag">${t}</span>`; }).join('')}</div>
        <div class="journey-actions" style="justify-content:center;margin-top:1rem;flex-wrap:wrap;gap:.5rem">
          <a class="btn primary" id="waShare" target="_blank" rel="noopener">Share on WhatsApp</a>
          <button class="btn" type="button" id="copyShare">Copy result</button>
          <a class="btn" href="${r.link}">Meet ${r.name}</a>
          <button class="btn" type="button" id="again">Play again</button>
        </div>
        <textarea id="shareText" readonly style="position:absolute;left:-9999px">${shareText}</textarea>
      </article>
    `;
    const wa = el('waShare');
    if (wa) wa.href = `https://wa.me/?text=${encodeURIComponent(shareText)}`;
    const copy = el('copyShare');
    if (copy) copy.addEventListener('click', function () {
      const t = el('shareText'); t.select();
      try { document.execCommand('copy'); } catch (e) {}
      if (navigator.clipboard) navigator.clipboard.writeText(shareText).catch(function () {});
      copy.textContent = 'Copied!';
      setTimeout(function () { copy.textContent = 'Copy result'; }, 1500);
    });
    const again = el('again');
    if (again) again.addEventListener('click', function () {
      Object.keys(scores).forEach(function (k) { scores[k] = 0; });
      index = 0; renderQuestion();
    });
  }

  fetch('content/personality-quizzes.json?v=1')
    .then(function (res) { return res.json(); })
    .then(start)
    .catch(function () {
      const app = el('quizApp');
      if (app) app.innerHTML = '<article class="card"><h3>This quiz is resting.</h3><p>Please check back soon.</p></article>';
    });
})();
