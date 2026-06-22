// Kids Games hub — an Adventure ladder (mixed mini-rounds + rewards) plus a
// Practice mode (pick a game/theme/level). Card art comes from
// content/kids-games.json (assets are embedded data URIs). XP via site.js.
(function () {
  let DATA = null;
  function app() { return document.getElementById('kidsApp'); }

  // ── Adventure ladder: each level chains a few rounds, mixing themes ──
  const LADDER = [
    { name: 'First steps',      rounds: [ { type: 'memory', pool: 'deities', pairs: 3 }, { type: 'vahana', pairs: 3 } ] },
    { name: 'Finding the way',  rounds: [ { type: 'memory', pool: 'mixed', pairs: 4 }, { type: 'sequence', cat: 'ramayana', count: 3 } ] },
    { name: 'Growing stronger', rounds: [ { type: 'memory', pool: 'mixed', pairs: 5 }, { type: 'vahana', pairs: 4 }, { type: 'sequence', cat: 'ramayana', count: 4 } ] },
    { name: 'Sacred mounts',    rounds: [ { type: 'memory', pool: 'mixed', pairs: 6 }, { type: 'memory', pool: 'deity_vahana', pairs: 4 }, { type: 'sequence', cat: 'ramayana', count: 6 } ] },
    { name: 'The long journey', rounds: [ { type: 'memory', pool: 'mixed', pairs: 8 }, { type: 'vahana', pairs: 5 }, { type: 'sequence', cat: 'ramayana', count: 8 } ] },
    { name: 'Master of avatars',rounds: [ { type: 'memory', pool: 'dashavatara', pairs: 10 }, { type: 'sequence', cat: 'dashavatara', count: 10 }, { type: 'vahana', pairs: 5 } ] }
  ];

  // ── tiny helpers ──
  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); const t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function img(id) { return (DATA.assets && DATA.assets[id]) || ''; }
  function theme(id) { return DATA.memory.themes.filter(function (t) { return t.id === id; })[0]; }
  function catItems(id) { const c = DATA.sequence.categories.filter(function (x) { return x.id === id; })[0]; return c ? c.items : []; }
  function colsFor(pairs) { return pairs <= 3 ? 3 : (pairs <= 8 ? 4 : 5); }
  function starStr(n) { let s = ''; for (let i = 0; i < 3; i++) s += (i < n ? '★' : '☆'); return s; }
  function award(event, props) {
    if (typeof awardKhatakshetraProgress === 'function') {
      try { awardKhatakshetraProgress(event, { xp: 15, track: 'creative_practice', properties: props || {} }); } catch (e) {}
    }
  }
  function clear() { const a = app(); a.innerHTML = ''; return a; }
  function head(backLabel, backFn, title, subtitle) {
    const wrap = document.createElement('div');
    const b = document.createElement('button'); b.className = 'btn kg-back'; b.type = 'button'; b.textContent = backLabel || '‹ Back';
    b.addEventListener('click', backFn); wrap.appendChild(b);
    const h = document.createElement('h2'); h.className = 'kg-title'; h.textContent = title; wrap.appendChild(h);
    if (subtitle) { const p = document.createElement('p'); p.className = 'kg-sub'; p.textContent = subtitle; wrap.appendChild(p); }
    return wrap;
  }
  function msg(text) { const p = document.createElement('p'); p.className = 'kg-msg'; p.id = 'kgMsg'; p.textContent = text || ''; return p; }
  function setMsg(t) { const m = document.getElementById('kgMsg'); if (m) m.textContent = t; }
  function actionsBar() { const d = document.createElement('div'); d.className = 'kg-actions'; d.id = 'kgActions'; return d; }
  function clearActions() { const h = document.getElementById('kgActions'); if (h) h.innerHTML = ''; }
  function showActions(actions) {
    const host = document.getElementById('kgActions'); if (!host) return;
    host.innerHTML = '';
    actions.forEach(function (a) {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'btn' + (a.primary ? ' primary' : '');
      b.textContent = a.label; b.addEventListener('click', a.onClick); host.appendChild(b);
    });
    try { host.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (e) {}
  }
  function chooser(options) {
    const grid = document.createElement('div'); grid.className = 'kg-choose';
    options.forEach(function (o) {
      const c = document.createElement('button'); c.type = 'button'; c.className = 'kg-opt' + (o.locked ? ' is-locked' : '');
      let inner = '';
      if (o.thumb) inner += '<span class="kg-opt-thumb" style="background-image:url(' + o.thumb + ')"></span>';
      inner += '<span class="kg-opt-body"><span class="kg-opt-name">' + o.name + '</span>';
      if (o.sub) inner += '<span class="kg-opt-sub">' + o.sub + '</span>';
      inner += '</span>';
      c.innerHTML = inner;
      if (o.locked) c.disabled = true; else c.addEventListener('click', o.onClick);
      grid.appendChild(c);
    });
    return grid;
  }

  // ── reward: self-contained canvas confetti ──
  function confettiBurst(count, duration) {
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const cv = document.createElement('canvas'); cv.className = 'kg-confetti';
    cv.width = window.innerWidth; cv.height = window.innerHeight; document.body.appendChild(cv);
    const ctx = cv.getContext('2d');
    const colors = ['#E8B94F', '#E07B1A', '#F5A23C', '#6fcf97', '#cf6f9b', '#F7EBD2'];
    const parts = [];
    for (let i = 0; i < count; i++) parts.push({ x: cv.width / 2 + (Math.random() - 0.5) * cv.width * 0.4, y: cv.height * 0.32 + (Math.random() - 0.5) * 50, vx: (Math.random() - 0.5) * 9, vy: Math.random() * -9 - 2, g: 0.22 + Math.random() * 0.12, s: 5 + Math.random() * 7, c: colors[i % colors.length], r: Math.random() * Math.PI, vr: (Math.random() - 0.5) * 0.32 });
    const start = performance.now();
    function frame(t) {
      const el = t - start; ctx.clearRect(0, 0, cv.width, cv.height);
      parts.forEach(function (p) { p.vy += p.g; p.x += p.vx; p.y += p.vy; p.r += p.vr; ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.fillStyle = p.c; ctx.fillRect(-p.s / 2, -p.s / 2, p.s, p.s * 0.6); ctx.restore(); });
      if (el < duration) requestAnimationFrame(frame); else cv.remove();
    }
    requestAnimationFrame(frame);
  }
  function smallConfetti() { confettiBurst(70, 1200); }
  function bigConfetti() { confettiBurst(170, 2300); }

  // ── progress (localStorage) ──
  const PKEY = 'khatakshetra_kids_ladder';
  function loadProgress() { try { return JSON.parse(localStorage.getItem(PKEY) || '{}'); } catch (e) { return {}; } }
  function saveProgress(p) { try { localStorage.setItem(PKEY, JSON.stringify(p)); } catch (e) {} }

  // ── shared board builders (used by Adventure rounds AND Practice) ──
  function memoryUnits(pool, pairs) {
    let units = [];
    if (pool === 'deity_vahana') {
      const t = theme('deity_vahana');
      shuffle(t.pairs).slice(0, pairs).forEach(function (p, i) { units.push({ key: 'k' + i, id: p.a.id, label: p.a.label }); units.push({ key: 'k' + i, id: p.b.id, label: p.b.label }); });
    } else {
      let cards;
      if (pool === 'deities') cards = theme('deities').cards;
      else if (pool === 'dashavatara') cards = theme('dashavatara').cards;
      else cards = theme('deities').cards.concat(theme('dashavatara').cards); // mixed
      shuffle(cards).slice(0, pairs).forEach(function (card, i) { units.push({ key: 'k' + i, id: card.id, label: card.label }); units.push({ key: 'k' + i, id: card.id, label: card.label }); });
    }
    return shuffle(units);
  }
  function buildMemory(host, units, cols, onWin) {
    const grid = document.createElement('div'); grid.className = 'kg-grid'; grid.style.gridTemplateColumns = 'repeat(' + cols + ', 1fr)';
    host.appendChild(grid);
    const total = units.length / 2;
    let first = null, lock = false, matched = 0, moves = 0, mistakes = 0, done = false;
    units.forEach(function (unit) {
      const c = document.createElement('button'); c.type = 'button'; c.className = 'kg-card';
      c.innerHTML = '<span class="kg-back">ॐ</span><span class="kg-face"><img src="' + img(unit.id) + '" alt="' + unit.label + '" loading="lazy"><span class="kg-cap">' + unit.label + '</span></span>';
      c.addEventListener('click', function () { flip(c, unit); });
      grid.appendChild(c);
    });
    function flip(c, unit) {
      if (lock || done || c.classList.contains('is-up') || c.classList.contains('is-done')) return;
      c.classList.add('is-up');
      if (!first) { first = { c: c, unit: unit }; return; }
      moves++;
      if (first.unit.key === unit.key && first.c !== c) {
        first.c.classList.add('is-done'); c.classList.add('is-done'); first = null; matched++;
        if (matched === total) { done = true; onWin({ moves: moves, mistakes: mistakes }); }
      } else {
        mistakes++; lock = true; const f = first; first = null;
        setTimeout(function () { f.c.classList.remove('is-up'); c.classList.remove('is-up'); lock = false; }, 850);
      }
    }
  }
  function buildVahana(host, pairs, onWin) {
    pairs.forEach(function (p, i) { p._k = 'p' + i; });
    const cols = document.createElement('div'); cols.className = 'kg-cols';
    const dCol = document.createElement('div'); dCol.className = 'kg-col';
    const vCol = document.createElement('div'); vCol.className = 'kg-col';
    cols.appendChild(dCol); cols.appendChild(vCol); host.appendChild(cols);
    function tile(item, key, col) { const b = document.createElement('button'); b.type = 'button'; b.className = 'kg-tile'; b.dataset.key = key; b.innerHTML = '<img src="' + img(item.id) + '" alt="' + item.label + '" loading="lazy"><span class="kg-cap">' + item.label + '</span>'; col.appendChild(b); return b; }
    let selected = null, matched = 0, mistakes = 0, done = false;
    shuffle(pairs).forEach(function (p) {
      const b = tile(p.deity, p._k, dCol);
      b.addEventListener('click', function () { if (done || b.classList.contains('is-done')) return; if (selected) selected.classList.remove('is-sel'); selected = b; b.classList.add('is-sel'); });
    });
    shuffle(pairs).forEach(function (p) {
      const b = tile(p.vahana, p._k, vCol);
      b.addEventListener('click', function () {
        if (done || b.classList.contains('is-done') || !selected) return;
        if (selected.dataset.key === b.dataset.key) {
          b.classList.add('is-done'); selected.classList.add('is-done'); selected.classList.remove('is-sel'); selected = null; matched++;
          if (matched === pairs.length) { done = true; onWin({ mistakes: mistakes }); } else { setMsg('Yes! ' + matched + ' of ' + pairs.length + ' matched.'); }
        } else { mistakes++; setMsg('Not their vahana — try again.'); }
      });
    });
  }
  function buildSequence(host, correct, onWin) {
    const pool = shuffle(correct); let answer = [], mistakes = 0, done = false;
    const ansRow = document.createElement('div'); ansRow.className = 'kg-seq-answer';
    const choices = document.createElement('div'); choices.className = 'kg-seq-choices';
    const reset = document.createElement('button'); reset.className = 'btn kg-reset'; reset.type = 'button'; reset.textContent = 'Reset';
    host.appendChild(ansRow); host.appendChild(choices); host.appendChild(reset);
    function tileFor(item, n) {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'kg-scene';
      b.innerHTML = (n ? '<span class="kg-ord">' + n + '</span>' : '') + '<img src="' + img(item.id) + '" alt="' + item.label + '" loading="lazy"><span class="kg-cap">' + item.label + '</span>';
      return b;
    }
    function render() {
      if (done) return;
      clearActions();
      choices.innerHTML = '';
      pool.forEach(function (item) { if (answer.indexOf(item) !== -1) return; const b = tileFor(item, 0); b.addEventListener('click', function () { answer.push(item); render(); }); choices.appendChild(b); });
      ansRow.innerHTML = '';
      answer.forEach(function (item, i) { const b = tileFor(item, i + 1); b.addEventListener('click', function () { answer.splice(i, 1); render(); }); ansRow.appendChild(b); });
      if (answer.length === correct.length) {
        const ok = answer.every(function (it, i) { return it === correct[i]; });
        if (ok) { done = true; onWin({ mistakes: mistakes }); } else { mistakes++; setMsg('Not quite — tap a placed scene to remove it, or Reset.'); }
      } else { setMsg('Tap the scenes in the order they happen.'); }
    }
    reset.addEventListener('click', function () { if (done) return; answer = []; render(); });
    render();
  }

  // ── Adventure: map → level → chained rounds → celebration ──
  function renderMap() {
    const a = clear();
    a.appendChild(head('‹ All games', renderMenu, 'Adventure', 'Clear a level to unlock the next.'));
    const p = loadProgress(); const cleared = p.cleared || 0; const stars = p.stars || {};
    const map = document.createElement('div'); map.className = 'kg-map'; a.appendChild(map);
    LADDER.forEach(function (lv, i) {
      const locked = i > cleared;
      const tile = document.createElement('button'); tile.type = 'button';
      tile.className = 'kg-leveltile' + (locked ? ' is-locked' : '') + (i === cleared && !locked ? ' is-next' : '');
      const badge = locked ? '🔒' : String(i + 1);
      const sub = locked ? 'Locked' : (stars[i] ? starStr(stars[i]) : 'Play ▸');
      tile.innerHTML = '<span class="kg-lnum">' + badge + '</span><span class="kg-lbody"><span class="kg-lname">' + lv.name + '</span><span class="kg-stars">' + sub + '</span></span>';
      if (locked) tile.disabled = true; else tile.addEventListener('click', function () { startLevel(i); });
      map.appendChild(tile);
    });
  }
  function roundInstruction(round) {
    if (round.type === 'memory') return round.pool === 'deity_vahana' ? 'Flip cards to match each deity with its vahana.' : 'Flip the cards to find all the pairs.';
    if (round.type === 'vahana') return 'Tap a deity, then tap the vahana they ride.';
    return 'Tap the scenes in the order they happen.';
  }
  function roundTitle(round) {
    if (round.type === 'memory') return 'Memory · ' + round.pairs + ' pairs';
    if (round.type === 'vahana') return 'Match the Vahana';
    return 'Story Order · ' + (round.cat === 'dashavatara' ? 'Dashavatara' : 'Ramayana');
  }
  function roundBar(level, r) {
    const d = document.createElement('div'); d.className = 'kg-roundbar';
    let dots = '';
    for (let i = 0; i < level.rounds.length; i++) dots += '<span class="kg-dot' + (i < r ? ' is-done' : (i === r ? ' is-cur' : '')) + '"></span>';
    d.innerHTML = '<span class="kg-roundlabel">Round ' + (r + 1) + ' of ' + level.rounds.length + ' · ' + roundTitle(level.rounds[r]) + '</span><span class="kg-dots">' + dots + '</span>';
    return d;
  }
  function startLevel(idx) {
    const level = LADDER[idx];
    let r = 0, levelMistakes = 0;
    function step() {
      const a = clear();
      a.appendChild(head('‹ Adventure map', renderMap, 'Level ' + (idx + 1) + ' · ' + level.name));
      a.appendChild(roundBar(level, r));
      a.appendChild(msg(roundInstruction(level.rounds[r])));
      const host = document.createElement('div'); a.appendChild(host);
      const round = level.rounds[r];
      const onWin = function (stats) {
        levelMistakes += (stats && stats.mistakes) || 0;
        r++;
        if (r < level.rounds.length) { smallConfetti(); setMsg('Round done! ✓  Next round…'); setTimeout(step, 950); }
        else { completeLevel(idx, levelMistakes); }
      };
      if (round.type === 'memory') buildMemory(host, memoryUnits(round.pool, round.pairs), colsFor(round.pairs), onWin);
      else if (round.type === 'vahana') buildVahana(host, shuffle(DATA.vahana.pairs).slice(0, round.pairs).map(function (p) { return { deity: p.deity, vahana: p.vahana }; }), onWin);
      else buildSequence(host, catItems(round.cat).slice(0, round.count), onWin);
    }
    step();
  }
  function completeLevel(idx, mistakes) {
    const stars = mistakes <= 1 ? 3 : (mistakes <= 4 ? 2 : 1);
    const p = loadProgress(); p.stars = p.stars || {};
    p.stars[idx] = Math.max(p.stars[idx] || 0, stars);
    if ((p.cleared || 0) <= idx) p.cleared = idx + 1;
    saveProgress(p);
    award('kids_ladder_level', { level: idx + 1, stars: stars, mistakes: mistakes });
    bigConfetti();
    const a = clear();
    const card = document.createElement('div'); card.className = 'kg-celebrate';
    card.innerHTML = '<div class="kg-cel-emoji">🎉</div><h2 class="kg-title">Level ' + (idx + 1) + ' complete!</h2>' +
      '<div class="kg-stars-big">' + starStr(stars) + '</div>' +
      '<p class="kg-sub">' + (mistakes === 0 ? 'Flawless — perfect run!' : (mistakes <= 4 ? 'Well played!' : 'You did it!')) + '</p>';
    a.appendChild(card);
    a.appendChild(actionsBar());
    const acts = [{ label: '↻ Replay', onClick: function () { startLevel(idx); } }];
    if (idx + 1 < LADDER.length) acts.push({ label: 'Next level →', primary: true, onClick: function () { startLevel(idx + 1); } });
    else acts.push({ label: '🏆 Adventure complete!', primary: true, onClick: renderMap });
    acts.push({ label: 'Map', onClick: renderMap });
    showActions(acts);
  }

  // ── Practice mode (pick a specific game) ──
  function renderMemoryThemes() {
    const a = clear();
    a.appendChild(head('‹ All games', renderMenu, DATA.memory.title, 'Pick a theme.'));
    a.appendChild(chooser(DATA.memory.themes.map(function (th) {
      const sample = th.mode === 'related' ? (th.pairs[0] && th.pairs[0].a.id) : (th.cards[0] && th.cards[0].id);
      return { name: th.name, sub: th.tagline || '', thumb: img(sample), onClick: function () { renderMemoryLevels(th); } };
    })));
  }
  function renderMemoryLevels(th) {
    const a = clear();
    a.appendChild(head('‹ Themes', renderMemoryThemes, th.name, 'Pick a level.'));
    a.appendChild(chooser(th.levels.map(function (lv) { return { name: lv.name, sub: lv.pairs + ' pairs · ' + (lv.pairs * 2) + ' cards', onClick: function () { playMemory(th, lv); } }; })));
  }
  function playMemory(th, level) {
    const a = clear();
    a.appendChild(head('‹ Levels', function () { renderMemoryLevels(th); }, th.name + ' — ' + level.name));
    a.appendChild(msg('Find all the pairs.'));
    const host = document.createElement('div'); a.appendChild(host); a.appendChild(actionsBar());
    let units;
    if (th.mode === 'related') { units = []; shuffle(th.pairs).slice(0, level.pairs).forEach(function (p, i) { units.push({ key: 'k' + i, id: p.a.id, label: p.a.label }); units.push({ key: 'k' + i, id: p.b.id, label: p.b.label }); }); units = shuffle(units); }
    else units = memoryUnits(th.id, level.pairs);
    buildMemory(host, units, colsFor(level.pairs), function (stats) {
      setMsg('You matched them all in ' + stats.moves + ' moves! 🎉'); smallConfetti(); award('kids_game_complete', { game: 'memory', theme: th.id, level: level.name, moves: stats.moves });
      const li = th.levels.indexOf(level);
      const acts = [{ label: '↻ Play again', onClick: function () { playMemory(th, level); } }];
      if (li > -1 && li < th.levels.length - 1) acts.push({ label: 'Next level →', primary: true, onClick: function () { playMemory(th, th.levels[li + 1]); } });
      else acts.push({ label: 'Try another theme →', primary: true, onClick: renderMemoryThemes });
      showActions(acts);
    });
  }
  function renderVahanaLevels() {
    const a = clear();
    a.appendChild(head('‹ All games', renderMenu, DATA.vahana.title, 'Pick a level.'));
    a.appendChild(chooser(DATA.vahana.levels.map(function (lv) { return { name: lv.name, sub: lv.pairs + ' deities to match', onClick: function () { playVahana(lv); } }; })));
  }
  function playVahana(level) {
    const a = clear();
    a.appendChild(head('‹ Levels', renderVahanaLevels, DATA.vahana.title + ' — ' + level.name));
    a.appendChild(msg('Tap a deity, then the vahana they ride.'));
    const host = document.createElement('div'); a.appendChild(host); a.appendChild(actionsBar());
    const pairs = shuffle(DATA.vahana.pairs).slice(0, level.pairs).map(function (p) { return { deity: p.deity, vahana: p.vahana }; });
    buildVahana(host, pairs, function () {
      setMsg('Perfect match! 🎉'); smallConfetti(); award('kids_game_complete', { game: 'vahana', level: level.name });
      const li = DATA.vahana.levels.indexOf(level);
      const acts = [{ label: '↻ Play again', onClick: function () { playVahana(level); } }];
      if (li > -1 && li < DATA.vahana.levels.length - 1) acts.push({ label: 'Next level →', primary: true, onClick: function () { playVahana(DATA.vahana.levels[li + 1]); } });
      else acts.push({ label: 'More games →', primary: true, onClick: renderMenu });
      showActions(acts);
    });
  }
  function renderSequenceCats() {
    const a = clear();
    a.appendChild(head('‹ All games', renderMenu, DATA.sequence.title, 'Pick an epic.'));
    a.appendChild(chooser(DATA.sequence.categories.map(function (cat) {
      return { name: cat.name + (cat.locked ? '  🔒' : ''), sub: cat.locked ? (cat.note || 'Coming soon') : (cat.items.length + ' scenes'), thumb: cat.items ? img(cat.items[0].id) : '', locked: !!cat.locked, onClick: function () { renderSequenceLevels(cat); } };
    })));
  }
  function renderSequenceLevels(cat) {
    const a = clear();
    a.appendChild(head('‹ Epics', renderSequenceCats, cat.name, 'Pick a level.'));
    a.appendChild(chooser(cat.levels.map(function (lv) { return { name: lv.name, sub: lv.count + ' scenes to order', onClick: function () { playSequence(cat, lv); } }; })));
  }
  function playSequence(cat, level) {
    const a = clear();
    a.appendChild(head('‹ Levels', function () { renderSequenceLevels(cat); }, cat.name + ' — ' + level.name));
    a.appendChild(msg('Tap the scenes in the order they happen.'));
    const host = document.createElement('div'); a.appendChild(host); a.appendChild(actionsBar());
    buildSequence(host, cat.items.slice(0, level.count), function () {
      setMsg('Correct order! 🎉'); smallConfetti(); award('kids_game_complete', { game: 'sequence', category: cat.id, level: level.name });
      const li = cat.levels.indexOf(level);
      const acts = [{ label: '↻ Play again', onClick: function () { playSequence(cat, level); } }];
      if (li > -1 && li < cat.levels.length - 1) acts.push({ label: 'Next level →', primary: true, onClick: function () { playSequence(cat, cat.levels[li + 1]); } });
      else acts.push({ label: 'Try another epic →', primary: true, onClick: renderSequenceCats });
      showActions(acts);
    });
  }
  function renderJigsawChoices() {
    const a = clear();
    a.appendChild(head('‹ All games', renderMenu, DATA.jigsaw.title, 'Pick a picture and a size.'));
    let pick = DATA.jigsaw.choices[0];
    const picGrid = chooser(DATA.jigsaw.choices.map(function (ch) { return { name: ch.label, thumb: img(ch.id), onClick: function () { pick = ch; hi(); } }; }));
    a.appendChild(picGrid);
    function hi() { const opts = picGrid.querySelectorAll('.kg-opt'); DATA.jigsaw.choices.forEach(function (ch, i) { opts[i].classList.toggle('is-sel', ch === pick); }); }
    hi();
    const sizeRow = document.createElement('div'); sizeRow.className = 'kg-sizes';
    DATA.jigsaw.sizes.forEach(function (s) { const b = document.createElement('button'); b.className = 'btn primary'; b.type = 'button'; b.textContent = s.name; b.addEventListener('click', function () { playJigsaw(pick, s.size); }); sizeRow.appendChild(b); });
    a.appendChild(sizeRow);
  }
  function playJigsaw(choice, size) {
    const a = clear();
    a.appendChild(head('‹ Pictures', renderJigsawChoices, DATA.jigsaw.title + ' — ' + choice.label));
    a.appendChild(msg('Slide tiles into the empty space to complete the picture.'));
    const image = img(choice.id); const n = size * size, blankVal = n - 1;
    let tiles = [], blank = n - 1;
    for (let i = 0; i < n; i++) tiles.push(i);
    function neighbors(b) { const r = Math.floor(b / size), c = b % size, res = []; if (r > 0) res.push(b - size); if (r < size - 1) res.push(b + size); if (c > 0) res.push(b - 1); if (c < size - 1) res.push(b + 1); return res; }
    for (let k = 0; k < 300; k++) { const nb = neighbors(blank); const t = nb[Math.floor(Math.random() * nb.length)]; const tmp = tiles[blank]; tiles[blank] = tiles[t]; tiles[t] = tmp; blank = t; }
    const grid = document.createElement('div'); grid.className = 'kg-jig'; grid.style.gridTemplateColumns = 'repeat(' + size + ', 1fr)';
    a.appendChild(grid); a.appendChild(actionsBar());
    function draw() {
      grid.innerHTML = '';
      tiles.forEach(function (val, pos) {
        const cell = document.createElement('button'); cell.type = 'button'; cell.className = 'kg-jigcell';
        if (val === blankVal) cell.style.visibility = 'hidden';
        else { const r = Math.floor(val / size), c = val % size; cell.style.backgroundImage = 'url("' + image + '")'; cell.style.backgroundSize = (size * 100) + '% ' + (size * 100) + '%'; cell.style.backgroundPosition = (c * 100 / (size - 1)) + '% ' + (r * 100 / (size - 1)) + '%'; }
        cell.addEventListener('click', function () { tryMove(pos); });
        grid.appendChild(cell);
      });
    }
    function tryMove(pos) {
      if (neighbors(blank).indexOf(pos) === -1) return;
      const tmp = tiles[blank]; tiles[blank] = tiles[pos]; tiles[pos] = tmp; blank = pos; draw();
      if (tiles.every(function (v, i) { return v === i; })) {
        setMsg('You solved it! 🎉'); smallConfetti(); award('kids_game_complete', { game: 'jigsaw', picture: choice.id, size: size });
        const acts = [{ label: '↻ Shuffle again', onClick: function () { playJigsaw(choice, size); } }];
        if (size < 4) acts.push({ label: 'Try 4 × 4 →', primary: true, onClick: function () { playJigsaw(choice, 4); } });
        else acts.push({ label: 'New picture →', primary: true, onClick: renderJigsawChoices });
        showActions(acts);
      }
    }
    draw();
  }

  // ── Menu: Adventure (primary) + Free play ──
  function renderMenu() {
    const a = clear();
    const p = loadProgress(); const cleared = p.cleared || 0;
    const adv = document.createElement('article'); adv.className = 'card kg-advcard';
    adv.innerHTML = '<div class="eyebrow">⭐ Adventure</div><h3>Play the level ladder</h3>' +
      '<p>Each level mixes a few quick games and gets a little harder. ' + (cleared ? ('You have cleared ' + cleared + ' of ' + LADDER.length + ' levels.') : 'Start at Level 1 and climb.') + '</p>';
    const ab = document.createElement('button'); ab.className = 'btn primary'; ab.type = 'button';
    ab.textContent = cleared ? ('Continue · Level ' + Math.min(cleared + 1, LADDER.length)) : 'Start the adventure';
    ab.addEventListener('click', renderMap); adv.appendChild(ab); a.appendChild(adv);

    const fh = document.createElement('h3'); fh.className = 'kg-freehead'; fh.textContent = 'Or practice one game'; a.appendChild(fh);
    const grid = document.createElement('div'); grid.className = 'kg-menu';
    const games = [
      { tag: '🧠 Pairs', name: 'Memory Match', desc: 'Match pairs — deities, Dashavatara, or deity & vahana.', go: renderMemoryThemes },
      { tag: '🦅 Match', name: 'Match the Vahana', desc: 'Pair each deity with the mount they ride.', go: renderVahanaLevels },
      { tag: '🔢 Order', name: 'Story Order', desc: 'Put an epic\'s scenes in the right order.', go: renderSequenceCats },
      { tag: '🧩 Puzzle', name: 'Sliding Picture', desc: 'Slide the tiles to complete a picture.', go: renderJigsawChoices }
    ];
    games.forEach(function (g) {
      const c = document.createElement('article'); c.className = 'card kg-gamecard';
      c.innerHTML = '<div class="eyebrow">' + g.tag + '</div><h3>' + g.name + '</h3><p>' + g.desc + '</p>';
      const b = document.createElement('button'); b.className = 'btn'; b.type = 'button'; b.textContent = 'Practice';
      b.addEventListener('click', g.go); c.appendChild(b); grid.appendChild(c);
    });
    a.appendChild(grid);
  }

  fetch('content/kids-games.json?v=2')
    .then(function (r) { return r.json(); })
    .then(function (d) { DATA = d; renderMenu(); })
    .catch(function () { const a = app(); if (a) a.innerHTML = '<article class="card"><h3>Games are loading soon.</h3></article>'; });
})();
