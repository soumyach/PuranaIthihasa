// Kids Games hub — four self-contained mini-games (no database). Data comes
// from content/kids-games.json; completion awards a little XP via site.js.
(function () {
  let DATA = null;
  function app() { return document.getElementById('kidsApp'); }
  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }
  function award(game) {
    if (typeof awardKhatakshetraProgress === 'function') {
      try { awardKhatakshetraProgress('kids_game_complete', { xp: 15, track: 'creative_practice', properties: { game: game } }); } catch (e) {}
    }
  }
  function header(title) {
    return `<button class="btn" type="button" id="kidsBack" style="margin-bottom:1rem">&lsaquo; All games</button><h2>${title}</h2>`;
  }
  function wireBack() {
    const b = document.getElementById('kidsBack');
    if (b) b.addEventListener('click', renderMenu);
  }

  function renderMenu() {
    app().innerHTML = `
      <div class="grid">
        <article class="card"><div class="eyebrow">🧠 Pairs</div><h3>Memory Match</h3><p>Flip the cards and match the deities.</p><button class="btn primary" type="button" data-game="memory">Play</button></article>
        <article class="card"><div class="eyebrow">🐂 Match</div><h3>Match the Vahana</h3><p>Pair each deity with their mount (vahana).</p><button class="btn primary" type="button" data-game="vahana">Play</button></article>
        <article class="card"><div class="eyebrow">🔢 Order</div><h3>Story Order</h3><p>Put the Ramayana events in the right order.</p><button class="btn primary" type="button" data-game="sequence">Play</button></article>
        <article class="card"><div class="eyebrow">🧩 Puzzle</div><h3>Sliding Picture</h3><p>Slide the tiles to complete the picture.</p><button class="btn primary" type="button" data-game="jigsaw">Play</button></article>
      </div>`;
    app().querySelectorAll('[data-game]').forEach(function (b) {
      b.addEventListener('click', function () {
        const g = b.dataset.game;
        if (g === 'memory') startMemory();
        else if (g === 'vahana') startVahana();
        else if (g === 'sequence') startSequence();
        else startJigsaw();
      });
    });
  }

  // ── Memory Match ──
  function startMemory() {
    const pairs = DATA.memory.pairs;
    const deck = shuffle(pairs.concat(pairs));
    let first = null, lock = false, matched = 0;
    app().innerHTML = header(DATA.memory.title) + '<p id="memMsg">Find all the pairs.</p><div class="grid" id="memGrid" style="grid-template-columns:repeat(4,1fr);gap:.5rem"></div>';
    wireBack();
    const grid = document.getElementById('memGrid');
    deck.forEach(function (card) {
      const c = document.createElement('button');
      c.className = 'btn'; c.type = 'button';
      c.style.cssText = 'aspect-ratio:1;font-size:1.7rem;min-height:64px';
      c.textContent = '?';
      c.addEventListener('click', function () { flip(c, card); });
      grid.appendChild(c);
    });
    function flip(c, card) {
      if (lock || c.disabled || c.dataset.up === '1') return;
      c.textContent = card.emoji; c.dataset.up = '1';
      if (!first) { first = { c: c, card: card }; return; }
      if (first.card.label === card.label && first.c !== c) {
        first.c.disabled = c.disabled = true; matched++; first = null;
        if (matched === pairs.length) { document.getElementById('memMsg').textContent = 'You matched them all! 🎉'; award('memory'); }
      } else {
        lock = true; const f = first; first = null;
        setTimeout(function () {
          f.c.textContent = '?'; c.textContent = '?'; f.c.dataset.up = '0'; c.dataset.up = '0'; lock = false;
        }, 800);
      }
    }
  }

  // ── Match the Vahana ──
  function startVahana() {
    const pairs = DATA.vahana.pairs;
    let selected = null, matched = 0;
    app().innerHTML = header(DATA.vahana.title) +
      '<p id="vMsg">Tap a deity, then tap their vahana.</p>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem"><div id="vDeities"></div><div id="vVahanas"></div></div>';
    wireBack();
    const dCol = document.getElementById('vDeities');
    const vCol = document.getElementById('vVahanas');
    pairs.forEach(function (p) {
      const b = document.createElement('button');
      b.className = 'btn'; b.type = 'button'; b.style.cssText = 'width:100%;margin:.3rem 0';
      b.textContent = p.deity; b.dataset.deity = p.deity;
      b.addEventListener('click', function () {
        if (b.disabled) return;
        if (selected) selected.classList.remove('primary');
        selected = b; b.classList.add('primary');
      });
      dCol.appendChild(b);
    });
    shuffle(pairs).forEach(function (p) {
      const b = document.createElement('button');
      b.className = 'btn'; b.type = 'button'; b.style.cssText = 'width:100%;margin:.3rem 0';
      b.textContent = p.emoji + '  ' + p.vahana; b.dataset.deity = p.deity;
      b.addEventListener('click', function () {
        if (b.disabled || !selected) return;
        if (selected.dataset.deity === p.deity) {
          b.disabled = selected.disabled = true;
          b.classList.remove('primary'); b.classList.add('is-correct');
          selected.classList.remove('primary'); selected.classList.add('is-correct');
          selected = null; matched++;
          if (matched === pairs.length) { document.getElementById('vMsg').textContent = 'Perfect match! 🎉'; award('vahana'); }
        } else {
          document.getElementById('vMsg').textContent = 'Not a match — try again.';
        }
      });
      vCol.appendChild(b);
    });
  }

  // ── Story Sequencing ──
  function startSequence() {
    const correct = DATA.sequence.items;
    const shuffled = shuffle(correct);
    let answer = [];
    app().innerHTML = header(DATA.sequence.title) +
      '<p id="sMsg">Tap the events in the order they happen.</p><div id="sChoices"></div><ol id="sAnswer" style="margin-top:1rem"></ol><button class="btn" type="button" id="sReset">Reset</button>';
    wireBack();
    const choices = document.getElementById('sChoices');
    function render() {
      choices.innerHTML = '';
      shuffled.forEach(function (item) {
        if (answer.indexOf(item) !== -1) return;
        const b = document.createElement('button');
        b.className = 'btn'; b.type = 'button';
        b.style.cssText = 'display:block;width:100%;text-align:left;margin:.3rem 0';
        b.textContent = item;
        b.addEventListener('click', function () { answer.push(item); render(); });
        choices.appendChild(b);
      });
      document.getElementById('sAnswer').innerHTML = answer.map(function (a) { return '<li>' + a + '</li>'; }).join('');
      if (answer.length === correct.length) {
        const ok = answer.every(function (a, i) { return a === correct[i]; });
        document.getElementById('sMsg').textContent = ok ? 'Correct order! 🎉' : 'Not quite — tap Reset and try again.';
        if (ok) award('sequence');
      }
    }
    document.getElementById('sReset').addEventListener('click', function () {
      answer = []; document.getElementById('sMsg').textContent = 'Tap the events in the order they happen.'; render();
    });
    render();
  }

  // ── Sliding Picture Puzzle ──
  function startJigsaw() {
    const size = DATA.jigsaw.size || 3;
    const img = DATA.jigsaw.image;
    const n = size * size;
    const blankVal = n - 1;
    let tiles = [];
    for (let i = 0; i < n; i++) tiles.push(i);
    let blank = n - 1;
    function neighbors(b) {
      const r = Math.floor(b / size), c = b % size, res = [];
      if (r > 0) res.push(b - size);
      if (r < size - 1) res.push(b + size);
      if (c > 0) res.push(b - 1);
      if (c < size - 1) res.push(b + 1);
      return res;
    }
    for (let k = 0; k < 200; k++) {
      const nb = neighbors(blank);
      const t = nb[Math.floor(Math.random() * nb.length)];
      const tmp = tiles[blank]; tiles[blank] = tiles[t]; tiles[t] = tmp; blank = t;
    }
    app().innerHTML = header(DATA.jigsaw.title) +
      '<p id="jMsg">Slide tiles into the empty space to complete the picture.</p>' +
      '<div id="jGrid" style="display:grid;grid-template-columns:repeat(' + size + ',1fr);gap:3px;max-width:360px"></div>';
    wireBack();
    const grid = document.getElementById('jGrid');
    function draw() {
      grid.innerHTML = '';
      tiles.forEach(function (val, pos) {
        const cell = document.createElement('button');
        cell.type = 'button';
        cell.style.cssText = 'aspect-ratio:1;border:1px solid rgba(232,185,79,.3);padding:0;cursor:pointer;background-repeat:no-repeat;background-size:' + (size * 100) + '% ' + (size * 100) + '%';
        if (val === blankVal) {
          cell.style.visibility = 'hidden';
        } else {
          const r = Math.floor(val / size), c = val % size;
          cell.style.backgroundImage = 'url("' + img + '")';
          cell.style.backgroundPosition = (c * 100 / (size - 1)) + '% ' + (r * 100 / (size - 1)) + '%';
        }
        cell.addEventListener('click', function () { tryMove(pos); });
        grid.appendChild(cell);
      });
    }
    function tryMove(pos) {
      if (neighbors(blank).indexOf(pos) === -1) return;
      const tmp = tiles[blank]; tiles[blank] = tiles[pos]; tiles[pos] = tmp; blank = pos;
      draw();
      if (tiles.every(function (v, i) { return v === i; })) {
        document.getElementById('jMsg').textContent = 'You solved it! 🎉'; award('jigsaw');
      }
    }
    draw();
  }

  fetch('content/kids-games.json?v=1')
    .then(function (r) { return r.json(); })
    .then(function (d) { DATA = d; renderMenu(); })
    .catch(function () { const a = app(); if (a) a.innerHTML = '<article class="card"><h3>Games are loading soon.</h3></article>'; });
})();
