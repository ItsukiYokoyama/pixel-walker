(() => {
  if (window.top !== window || window.__pixelWalker) return;
  window.__pixelWalker = true;

  // ---------- 設定 ----------
  const DEFAULTS = { enabled: true, scale: 4, character: 'adventurer', detail: 2, control: false };
  let settings = { ...DEFAULTS };

  // ---------- 物理パラメータ (px, 秒) ----------
  const GRAV = 3375;
  const WALK = 105;
  const MAX_VX = 390;
  const MAX_PLATFORMS = 1500;
  const maxH = () => 72 * settings.scale; // ジャンプの最大高さ

  // ---------- ドット絵 ----------
  // ピクセル格子は characters.js (window.PW) が組み立てる。
  // 足場の角の位置 (LEDGE_COL、標準解像度の列) と、体の中心 (ax) がフレームごとに決まっている。
  const LEDGE_COL = PW.LEDGE_COL;
  let sprites = {};

  // 各フレームの { c: canvas, ax: 体の中心(px), ledgeY: 足場の上端の高さ(px), ledgeDX: 中心から足場の角までの横距離(px) }
  function buildBuiltinSprites() {
    // res: 1 = 標準(1 ドット = scale px) / 2 = 細かい(絵を 2 倍の解像度に補間して 1 ドット = scale/2 px)。大きさはどちらも同じ。
    const fine = PW.fine(settings.character);
    const res = fine || settings.detail === 1 ? 1 : 2;
    const dot = (settings.scale / res) * PW.unit(settings.character); // 1 セルの px
    const palette = PW.palette(settings.character);
    const out = {};
    for (const [name, { g, ax, ledgeRow }] of Object.entries(PW.grids(settings.character, res))) {
      out[name] = {
        c: PW.render(g, palette, dot, res > 1 && !fine),
        ax: ax * dot,
        ledgeY: (ledgeRow || 0) * dot,
        ledgeDX: LEDGE_COL * settings.scale - ax * dot,
      };
    }
    return out;
  }

  function buildSprites() {
    try {
      sprites = buildBuiltinSprites();
      // 泳ぐキャラクターと、歩くキャラクターの切り替え
      const swimming = !!PW.swim(settings.character);
      if (swimming !== ch.swimming) {
        ch.swimming = swimming;
        if (canvas.isConnected) spawn();
      }
    } catch (e) {
      console.error('Pixel Walker: 絵の作成に失敗しました', e); // 失敗しても、今の絵のまま動き続ける
    }
  }

  // ---------- キャンバス ----------
  const canvas = document.createElement('canvas');
  canvas.id = '__pixel-walker-canvas';
  canvas.style.cssText =
    'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:2147483647;';
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    ctx.imageSmoothingEnabled = false;
  }

  // ---------- 足場 ----------
  let platforms = [];
  let blocks = []; // 泳ぐキャラクターがよける箱 { l, r, t, b }(ドキュメント座標)
  const BLOCK_SELECTOR = 'h1,h2,h3,h4,h5,h6,p,li,pre,blockquote,table,figure,img,video,iframe,button,input,textarea,select';
  let docHeight = 0;
  // 地面はドキュメント末尾。ただし画面より下なら画面下端を床にする。
  const floorY = () => Math.min(docHeight, window.scrollY + window.innerHeight);

  // 足場は「実際に文字がある行」と、画像・ボタンなどの部品の上端。
  // p や span の箱全体ではなく、テキストの各行(Range の矩形)を足場にするので、余白の上は歩かない。
  const NON_TEXT = 'img,button,input,textarea,select,video,iframe';
  const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEXTAREA', 'SELECT', 'OPTION', 'SVG', 'CANVAS', 'IFRAME']);
  const nodeIds = new WeakMap();
  let nextId = 1;
  const idOf = (n) => {
    if (!nodeIds.has(n)) nodeIds.set(n, nextId++);
    return nodeIds.get(n);
  };

  function refreshPlatforms() {
    if (document.hidden || !document.body) return;
    const de = document.documentElement;
    const docW = de.clientWidth;
    const docH = Math.max(de.scrollHeight, document.body.scrollHeight);
    const sx = window.scrollX;
    const sy = window.scrollY;
    docHeight = docH;
    const vh = window.innerHeight;
    const list = [{ el: 'ground', l: 0, r: docW, t: floorY(), ground: true }];

    // position: fixed の要素(の中)はスクロールで動くので足場にしない
    const fixedCache = new Map();
    const isFixed = (el) => {
      if (!el || el === document.body || el === de) return false;
      if (!fixedCache.has(el)) {
        fixedCache.set(el, getComputedStyle(el).position === 'fixed' || isFixed(el.parentElement));
      }
      return fixedCache.get(el);
    };
    const visible = (el) =>
      !el.checkVisibility || el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true });
    const add = (key, r, into) => {
      if (r.width < 24 || r.height < 6) return;
      if (r.bottom < -vh || r.top > vh * 2) return;
      const l = Math.max(0, r.left + sx);
      const rr = Math.min(docW, r.right + sx);
      const t = r.top + sy;
      if (rr - l < 24 || t < 0 || t > docH - 2) return;
      into.push({ el: key, l, r: rr, t });
    };

    // テキストの各行
    const lines = [];
    const range = document.createRange();
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
      acceptNode(n) {
        if (n.nodeType === 1) {
          if (n === canvas || SKIP_TAGS.has(n.tagName.toUpperCase())) return NodeFilter.FILTER_REJECT;
          const r = n.getBoundingClientRect();
          if ((r.width || r.height) && (r.bottom < -vh || r.top > vh * 2)) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_SKIP; // 子は辿る
        }
        return n.nodeValue.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
      },
    });
    while (lines.length < MAX_PLATFORMS && walker.nextNode()) {
      const node = walker.currentNode;
      const parent = node.parentElement;
      if (!parent || !visible(parent) || isFixed(parent)) continue;
      range.selectNodeContents(node);
      const rects = range.getClientRects();
      for (let i = 0; i < rects.length; i++) add(idOf(node) + ':' + i, rects[i], lines);
    }

    // 同じ行に並ぶ隣り合った断片(strong や a で分かれた文字など)をつなげる
    lines.sort((a, b) => Math.round(a.t / 3) - Math.round(b.t / 3) || a.l - b.l);
    const merged = [];
    for (const p of lines) {
      const last = merged[merged.length - 1];
      if (last && Math.abs(last.t - p.t) < 3 && p.l - last.r < 10 && p.l >= last.l) last.r = Math.max(last.r, p.r);
      else merged.push({ ...p });
    }
    list.push(...merged);

    // 画像・ボタンなどは箱の上端
    for (const el of document.querySelectorAll(NON_TEXT)) {
      if (list.length >= MAX_PLATFORMS) break;
      if (el === canvas || !visible(el) || isFixed(el)) continue;
      add(idOf(el) + ':0', el.getBoundingClientRect(), list);
    }
    // 泳ぐキャラクターがよける「ブロック」(段落・見出し・画像・表など。画面の大半を占める箱は除く)
    const bl = [];
    for (const el of document.querySelectorAll(BLOCK_SELECTOR)) {
      if (bl.length >= 400) break;
      if (el === canvas || !visible(el) || isFixed(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 8 || r.height < 8 || r.bottom < -vh || r.top > vh * 2) continue;
      if (r.width * r.height > 0.6 * docW * vh) continue;
      bl.push({ l: r.left + sx, r: r.right + sx, t: r.top + sy, b: r.bottom + sy });
    }
    blocks = bl;
    platforms = list;

    // 立っている足場を新しい情報に差し替える。無ければ落下。
    if (ch.mode === 'climb') {
      const p = platforms.find((q) => q.el === ch.climb.p.el);
      if (p) ch.climb.p = p;
      else startFall(0);
    }
    if (ch.grab) {
      const p = platforms.find((q) => q.el === ch.grab.p.el);
      if (p) ch.grab.p = p;
      else ch.grab = null;
    }
    if (ch.mode === 'ground' && ch.standing) {
      const p = platforms.find((q) => q.el === ch.standing.el);
      if (p) {
        ch.standing = p;
        ch.y = p.t;
      } else {
        startFall(0);
      }
    }
  }

  // ---------- キャラクター ----------
  const ch = {
    x: 100, y: 0, vx: 0, vy: 0, dir: 1,
    mode: 'air', // 'ground' | 'air' | 'climb' | 'return'
    act: 'idle', // 'idle' | 'walk'
    timer: 0, edge: null, // edge: 端に着いたときの動き 'hang'(ぶら下がって降りる) | 'off'(飛び降りる) | null(折り返す)
    standing: null, animT: 0,
    ignore: null, ignoreT: 0, // すり抜け中の足場
    actName: null, actT: 0, actDur: 3, // その場でのアクション
    swimming: false, tx: 0, ty: 0, retarget: 0, stuck: 0, swimT: 0, pitch: 0, // 泳ぐキャラクター用
    grab: null, airT: 0, // ジャンプで足場の縁につかまる予定
    climb: null, frame: 'idle',
    airJumps: 0, // 操作しているときに、空中であと何回ジャンプできるか(二段ジャンプ)
  };

  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const rand = (a, b) => a + Math.random() * (b - a);
  const lerp = (a, b, k) => a + (b - a) * k;

  // ぶら下がったときの足(feet)の、足場上端からの距離
  const hangOffset = () => {
    const sp = sprites.hang1;
    return sp.c.height - sp.ledgeY;
  };
  const edgeXOf = (p, d) => (d > 0 ? p.l : p.r);

  function spawn() {
    endDrag(null); // つまんでいる途中にキャラクターが切り替わったら、離す
    if (ch.swimming) return startSwim();
    ch.x = rand(60, Math.max(100, window.innerWidth - 60));
    ch.y = window.scrollY + 10;
    ch.vx = ch.vy = 0;
    ch.mode = 'air';
    ch.standing = null;
    ch.grab = null;
    ch.climb = null;
  }

  function startFall(vx) {
    ch.mode = 'air';
    ch.standing = null;
    ch.grab = null;
    ch.climb = null;
    ch.vx = vx;
    ch.vy = 0;
  }

  function land(p) {
    ch.airJumps = 1; // 着地したら、また二段ジャンプできる
    ch.mode = 'ground';
    ch.standing = p;
    ch.y = p.t;
    ch.vx = ch.vy = 0;
    ch.act = 'idle';
    ch.timer = rand(0.2, 0.6);
  }

  // ---- よじ登り / ぶら下がって降りる ----
  // 登り: ぶら下がり → 足を振り上げ → 片足を引っかけ → 反対の足を振り上げ → 乗り上げ。降りるときはその逆。
  const UP_STEPS = [
    ['hang1', 0.2], ['hang2', 0.2], ['pull1', 0.22], ['pull2', 0.25], ['pull3', 0.25], ['mantle', 0.28],
  ];
  const DOWN_STEPS = [...UP_STEPS].reverse();

  function startClimb(p, d, rev) {
    ch.mode = 'climb';
    ch.climb = { p, d, rev, steps: rev ? DOWN_STEPS : UP_STEPS, i: 0, t: 0 };
    ch.dir = d;
    ch.standing = null;
    ch.grab = null;
    ch.vx = ch.vy = 0;
  }

  // 足場の角にフレームの ledge を合わせたときのキャラクターの位置
  function poseOf(name, p, d) {
    const sp = sprites[name];
    const sc = settings.scale;
    return {
      x: edgeXOf(p, d) - d * sp.ledgeDX,
      y: p.t + sp.c.height - sp.ledgeY,
    };
  }

  function standX(p, d) {
    return clamp(edgeXOf(p, d) + d * 8 * settings.scale, p.l + 4, p.r - 4);
  }

  function updateClimb(dt) {
    const c = ch.climb;
    const { p, d } = c;
    const sc = settings.scale;
    c.t += dt;
    while (c.i < c.steps.length && c.t >= c.steps[c.i][1]) {
      c.t -= c.steps[c.i][1];
      c.i++;
    }
    if (c.i >= c.steps.length) {
      if (c.rev) {
        const pose = poseOf('hang1', p, d);
        ch.x = pose.x;
        ch.y = pose.y;
        startFall(0); // 手を離して落ちる
      } else {
        ch.x = standX(p, d);
        land(p);
      }
      return;
    }
    const [name, dur] = c.steps[c.i];
    if (name === 'mantle') {
      let k = c.t / dur;
      if (c.rev) k = 1 - k;
      const from = poseOf('pull3', p, d);
      ch.x = lerp(from.x, standX(p, d), k);
      ch.y = lerp(from.y, p.t, k) - Math.sin(Math.PI * k) * 8 * sc;
      ch.frame = 'jump';
    } else {
      const pose = poseOf(name, p, d);
      ch.x = pose.x;
      ch.y = pose.y;
      ch.frame = name;
    }
  }

  // 端でぶら下がって降りられるなら開始する
  function beginHang(p, atRight) {
    const sc = settings.scale;
    const d = atRight ? -1 : 1;
    const pose = poseOf('hang1', p, d);
    const vw = document.documentElement.clientWidth;
    if (pose.x < 8 || pose.x > vw - 8) return false;
    if (pose.y > platforms[0].t - 4) return false; // 床に近すぎる
    ch.x = standX(p, d);
    startClimb(p, d, true);
    return true;
  }

  // 目標 (tx, 上方向 dy) へ届く放物線を決める。頂点の高さは lo〜lo+100 からランダムに選び、
  // 届かなければ最大の高さ(滞空時間が最長)で試す。これで遠くや斜め上の足場にも跳べる。
  function planJump(tx, dy, lo, H) {
    for (const apex of [rand(lo, Math.min(H, lo + 100)), H]) {
      const v = Math.sqrt(2 * GRAV * apex);
      const disc = v * v - 2 * GRAV * dy;
      if (disc < 0) continue;
      const T = (v + Math.sqrt(disc)) / GRAV;
      const vx = (tx - ch.x) / T;
      if (Math.abs(vx) <= MAX_VX) return { v, T, vx };
    }
    return null;
  }

  function tryJump() {
    const s = ch.standing;
    const sc = settings.scale;
    const H = maxH();
    const vw = document.documentElement.clientWidth;
    const top = window.scrollY;
    const bottom = top + window.innerHeight;
    const up = [];
    const other = [];
    for (const p of platforms) {
      if (p === s || p.ground || p.r - p.l < 24) continue;
      if (p.t < top + 24 || p.t > bottom) continue;
      const dy = ch.y - p.t; // 正なら上方向
      if (dy < -1000) continue; // 高い所からの飛び降りも可
      if (dy > 40 * sc) {
        // 高い足場: 縁にぶら下がってよじ登る
        const dirs = ch.x < p.l ? [1] : ch.x > p.r ? [-1] : [1, -1];
        const d = dirs[Math.floor(Math.random() * dirs.length)];
        const hx = d > 0 ? p.l - sprites.hang1.ledgeDX : p.r + sprites.hang1.ledgeDX;
        if (hx < 8 || hx > vw - 8) continue;
        const dyH = dy - hangOffset();
        const lo = Math.max(dyH, 0) + 10;
        if (lo > H) continue;
        const plan = planJump(hx, dyH, lo, H);
        if (!plan) continue;
        up.push({ vx: plan.vx, vy: -plan.v, grab: { p, d, T: plan.T } });
      } else {
        const lo = Math.max(dy, 0) + 20;
        if (lo > H) continue;
        const tx = clamp(ch.x + rand(-80, 80), p.l + 8, p.r - 8);
        const plan = planJump(tx, dy, lo, H);
        if (!plan) continue;
        (dy > 4 ? up : other).push({ vx: plan.vx, vy: -plan.v, grab: null });
      }
    }
    const pool = up.length && (Math.random() < 0.85 || !other.length) ? up : other;
    if (!pool.length) return false;
    const c = pool[Math.floor(Math.random() * pool.length)];
    ch.mode = 'air';
    ch.standing = null;
    ch.vx = c.vx;
    ch.vy = c.vy;
    ch.grab = c.grab;
    ch.airT = 0;
    if (c.grab) ch.dir = c.grab.d;
    else if (c.vx) ch.dir = c.vx > 0 ? 1 : -1;
    return true;
  }

  function dropThrough() {
    ch.ignore = ch.standing.el;
    ch.ignoreT = 0.25;
    ch.mode = 'air';
    ch.standing = null;
    ch.vx = 0;
    ch.vy = 60;
  }

  function startWalk(edge) {
    ch.act = 'walk';
    ch.dir = Math.random() < 0.5 ? -1 : 1;
    ch.timer = rand(1, 3);
    const r = Math.random();
    ch.edge = edge !== undefined ? edge : r < 0.2 ? 'hang' : r < 0.35 ? 'off' : null;
  }

  // ジャンプできる足場が近くに無いとき、上にある足場の方へ歩いて近づく
  function walkTowardHigher() {
    const s = ch.standing;
    const top = window.scrollY;
    const cands = platforms.filter(
      (p) => p !== s && !p.ground && p.t < ch.y - 4 && p.t > top + 24 && p.r - p.l >= 24
    );
    if (!cands.length) return false;
    const p = cands[Math.floor(Math.random() * cands.length)];
    startWalk(null);
    ch.dir = (p.l + p.r) / 2 > ch.x ? 1 : -1;
    ch.timer = rand(0.5, 1.2);
    return true;
  }

  // その場でのアクション(約 3 秒): 座る・寝る・ダンス
  const ACTIONS = ['sit', 'sleep', 'dance'];
  function startAction() {
    ch.act = 'action';
    ch.actName = ACTIONS[Math.floor(Math.random() * ACTIONS.length)];
    ch.actT = 0;
    ch.actDur = rand(2.6, 3.4);
    ch.timer = ch.actDur;
  }

  function decide() {
    const s = ch.standing;
    const r = Math.random();
    if (r < 0.08) {
      ch.act = 'idle';
      ch.timer = rand(0.4, 1.2);
    } else if (r < 0.22) {
      startAction();
    } else if (r < 0.38) {
      startWalk();
    } else if (r < 0.8) {
      if (!tryJump() && !walkTowardHigher()) startWalk();
    } else if (!s.ground) {
      if (Math.random() < 0.5) {
        // 近い方の端まで歩いて、ぶら下がって降りる
        startWalk('hang');
        ch.dir = ch.x - s.l < s.r - ch.x ? -1 : 1;
        ch.timer = 99;
      } else {
        dropThrough();
      }
    } else {
      startWalk();
    }
  }

  function updateGround(dt) {
    if (settings.control) return controlGround(dt);
    const s = ch.standing;
    ch.y = s.t;
    ch.animT += dt;
    ch.timer -= dt;
    if (ch.act === 'action') ch.actT += dt;
    if (ch.act === 'walk') {
      ch.x += ch.dir * WALK * dt;
      const atL = ch.x < s.l + 4;
      const atR = ch.x > s.r - 4;
      if (atL || atR) {
        if (!s.ground && ch.edge === 'hang' && beginHang(s, atR)) return;
        if (!s.ground && ch.edge === 'off') {
          startFall(ch.dir * 50);
          return;
        }
        ch.dir *= -1;
        ch.x = clamp(ch.x, s.l + 4, s.r - 4);
      }
    }
    if (ch.timer <= 0) decide();
  }

  function updateAir(dt) {
    const prevY = ch.y;
    ch.airT += dt;
    if (ch.ignoreT > 0) {
      ch.ignoreT -= dt;
      if (ch.ignoreT <= 0) ch.ignore = null;
    }
    ch.vy += GRAV * dt;
    if (settings.control && !ch.grab) {
      const d = keyDir();
      ch.vx += (d * AIR_VX - ch.vx) * Math.min(1, dt * 8);
      if (d) ch.dir = d;
    }
    ch.x += ch.vx * dt;
    ch.y += ch.vy * dt;
    const w = document.documentElement.clientWidth;
    ch.x = clamp(ch.x, 8, Math.max(8, w - 8));

    if (ch.grab) {
      if (ch.airT >= ch.grab.T) startClimb(ch.grab.p, ch.grab.d, false);
      return;
    }
    const ground = platforms[0];
    if (ch.vy > 0) {
      let hit = null;
      for (const p of platforms) {
        if (p.el === ch.ignore) continue;
        if (prevY <= p.t + 0.5 && ch.y >= p.t && ch.x >= p.l && ch.x <= p.r) {
          if (!hit || p.t < hit.t) hit = p;
        }
      }
      if (hit) return land(hit);
    }
    if (ground && ch.y > ground.t) land(ground); // ページが縮んだ場合の保険
  }

  // ---------- 泳ぐキャラクター(魚・海の生き物・カエル) ----------
  // 画面全体を自由に泳ぐ。段落・画像などのブロックにはぶつからず、よけて進む。
  function swimBox() {
    const sp = sprites.idle;
    return { w: sp.c.width * 0.7, h: sp.c.height * 0.5 };
  }

  function hitsBlock(x, y, w, h, m = 0) {
    for (const b of blocks) {
      if (x + w / 2 + m > b.l && x - w / 2 - m < b.r && y + h / 2 + m > b.t && y - h / 2 - m < b.b) return true;
    }
    return false;
  }

  // 次に向かう場所(ブロックに重ならない所)を選ぶ
  function pickTarget() {
    const { w, h } = swimBox();
    const vw = document.documentElement.clientWidth;
    const top = window.scrollY;
    const vh = window.innerHeight;
    for (let i = 0; i < 30; i++) {
      const x = rand(w / 2 + 10, Math.max(w / 2 + 11, vw - w / 2 - 10));
      const y = top + rand(h / 2 + 10, Math.max(h / 2 + 11, vh - h / 2 - 10));
      if (Math.hypot(x - ch.x, y - ch.y) < 80 || hitsBlock(x, y, w, h, 12)) continue;
      ch.tx = x;
      ch.ty = y;
      ch.retarget = rand(4, 8);
      return;
    }
    ch.tx = vw / 2;
    ch.ty = top + vh / 2;
    ch.retarget = 2;
  }

  function startSwim() {
    const { w, h } = swimBox();
    ch.mode = 'swim';
    ch.standing = null;
    ch.grab = null;
    ch.climb = null;
    ch.vx = ch.vy = 0;
    ch.swimT = 0;
    ch.stuck = 0;
    ch.pitch = 0;
    const vw = document.documentElement.clientWidth;
    ch.x = rand(w, Math.max(w + 1, vw - w));
    ch.y = window.scrollY + window.innerHeight * rand(0.25, 0.75);
    for (let i = 0; i < 20 && hitsBlock(ch.x, ch.y, w, h); i++) {
      ch.x = rand(w, Math.max(w + 1, vw - w));
      ch.y = window.scrollY + window.innerHeight * rand(0.15, 0.85);
    }
    pickTarget();
  }

  // ブロックにめり込んだら、いちばん浅い向きに押し出す
  function pushOut(x, y, w, h) {
    for (let pass = 0; pass < 3; pass++) {
      let moved = false;
      for (const b of blocks) {
        const hx0 = x - w / 2, hx1 = x + w / 2, hy0 = y - h / 2, hy1 = y + h / 2;
        if (hx1 <= b.l || hx0 >= b.r || hy1 <= b.t || hy0 >= b.b) continue;
        const ox = Math.min(hx1 - b.l, b.r - hx0);
        const oy = Math.min(hy1 - b.t, b.b - hy0);
        if (ox < oy) x += x < (b.l + b.r) / 2 ? -ox : ox;
        else y += y < (b.t + b.b) / 2 ? -oy : oy;
        moved = true;
      }
      if (!moved) break;
    }
    return { x, y };
  }

  function updateSwim(dt) {
    if (settings.control) return controlSwim(dt);
    const info = PW.swim(settings.character) || { frames: ['walk1', 'walk2'], speed: 1 };
    const { w, h } = swimBox();
    const vw = document.documentElement.clientWidth;
    const top = window.scrollY;
    const vh = window.innerHeight;
    const base = 24 * settings.scale * info.speed;
    // スクロールで画面外に出たら、すばやく画面内へ戻る(その間はブロックを無視)
    const outside = ch.y < top + h / 2 || ch.y > top + vh - h / 2;
    if (outside) {
      ch.tx = clamp(ch.x, w / 2, vw - w / 2);
      ch.ty = top + vh / 2;
    }
    ch.swimT += dt;
    ch.retarget -= dt;
    let dx = ch.tx - ch.x;
    let dy = ch.ty - ch.y;
    let dist = Math.hypot(dx, dy);
    if (!outside && (dist < 24 || ch.retarget <= 0 || ch.stuck > 1.2)) {
      pickTarget();
      ch.stuck = 0;
      dx = ch.tx - ch.x;
      dy = ch.ty - ch.y;
      dist = Math.hypot(dx, dy);
    }
    const sp = outside ? base * 3.5 : base;
    let wx = (dx / (dist || 1)) * sp;
    let wy = (dy / (dist || 1)) * sp;
    // 近くのブロックから遠ざかる(手前でよける)
    if (!outside) {
      const range = 46 + Math.max(w, h) / 2;
      for (const b of blocks) {
        const nx = clamp(ch.x, b.l, b.r);
        const ny = clamp(ch.y, b.t, b.b);
        const d = Math.hypot(ch.x - nx, ch.y - ny);
        if (d >= range) continue;
        const ux = d > 0.5 ? (ch.x - nx) / d : ch.x < (b.l + b.r) / 2 ? -1 : 1;
        const uy = d > 0.5 ? (ch.y - ny) / d : ch.y < (b.t + b.b) / 2 ? -1 : 1;
        const k = ((range - d) / range) * sp * 1.6;
        wx += ux * k;
        wy += uy * k;
      }
      const m = Math.hypot(wx, wy);
      if (m > sp) {
        wx = (wx / m) * sp;
        wy = (wy / m) * sp;
      }
    }
    const turn = Math.min(1, dt * 3);
    ch.vx += (wx - ch.vx) * turn;
    ch.vy += (wy - ch.vy) * turn;

    let nx = ch.x + ch.vx * dt;
    let ny = ch.y + ch.vy * dt;
    if (!outside) {
      nx = clamp(nx, w / 2 + 2, vw - w / 2 - 2);
      ny = clamp(ny, top + h / 2 + 2, top + vh - h / 2 - 2);
      const p = pushOut(nx, ny, w, h);
      nx = p.x;
      ny = p.y;
    }
    // 進めなかった(ぶつかった)ぶんを速度から引く。進めない状態が続いたら目標を変える
    const moved = Math.hypot(nx - ch.x, ny - ch.y);
    if (moved < sp * dt * 0.3) ch.stuck += dt;
    else ch.stuck = Math.max(0, ch.stuck - dt);
    ch.vx = (nx - ch.x) / (dt || 1);
    ch.vy = (ny - ch.y) / (dt || 1);
    ch.x = nx;
    ch.y = ny;
    if (Math.abs(ch.vx) > 14) ch.dir = ch.vx > 0 ? 1 : -1;
    const target = Math.atan2(ch.vy, Math.max(30, Math.abs(ch.vx)));
    ch.pitch += (clamp(target, -0.5, 0.5) - ch.pitch) * Math.min(1, dt * 6);
    ch.frame = info.frames[Math.floor(ch.swimT / 0.28) % info.frames.length];
  }

  // ---------- キーボードで操作する(設定の「キャラクターを操作する」) ----------
  // ←→: 歩く / C: ジャンプ(空中でもう一度押すと二段ジャンプ) / ↓+C: 足場から降りる / X: その場のアクション(寝る・座る・踊る)。
  // 泳ぐ・飛ぶキャラクターは ↑↓←→ で動く。入力欄での入力中や、Ctrl/Alt/Cmd 付きのキー(コピーなど)には反応しない
  const keys = { left: false, right: false, up: false, down: false };
  const AIR_VX = 180; // 空中で左右に動く速さ(px/秒)
  const keyDir = () => (keys.right ? 1 : 0) - (keys.left ? 1 : 0);
  const jumpV = () => Math.sqrt(2 * GRAV * 42 * settings.scale); // 1〜2 行上の文字に届く高さ

  function controlGround(dt) {
    const s = ch.standing;
    ch.y = s.t;
    ch.animT += dt;
    const d = keyDir();
    if (ch.act === 'action') {
      ch.actT += dt;
      if (d || ch.actT >= ch.actDur) ch.act = 'idle'; // 動き出したら(または時間が来たら)アクションをやめる
      else return;
    }
    if (!d) {
      ch.act = 'idle';
      return;
    }
    ch.act = 'walk';
    ch.dir = d;
    ch.x += d * WALK * dt;
    const vw = document.documentElement.clientWidth;
    if (!s.ground && (ch.x < s.l || ch.x > s.r)) return startFall(d * WALK); // 端から落ちる
    ch.x = clamp(ch.x, Math.max(8, s.l), Math.min(vw - 8, s.r));
  }

  function controlJump() {
    // 空中: 着地するまでに 1 回だけ、その場からもう一段跳べる(二段ジャンプ)。2 段目は少し低い
    if (ch.mode === 'air' && !ch.grab && ch.airJumps > 0) {
      ch.airJumps--;
      const d = keyDir();
      if (d) {
        ch.vx = d * AIR_VX;
        ch.dir = d;
      }
      ch.vy = -jumpV() * 0.85;
      return;
    }
    if (ch.mode !== 'ground' || !ch.standing) return;
    if (keys.down) {
      if (!ch.standing.ground) dropThrough(); // ↓ + C: 今の足場をすり抜けて降りる
      return;
    }
    const d = keyDir();
    ch.mode = 'air';
    ch.standing = null;
    ch.grab = null;
    ch.act = 'idle';
    ch.vx = d * AIR_VX;
    ch.vy = -jumpV();
    ch.airT = 0;
    if (d) ch.dir = d;
  }

  function controlAction() {
    if (ch.mode !== 'ground' || !ch.standing) return;
    startAction();
  }

  function controlSwim(dt) {
    const info = PW.swim(settings.character) || { frames: ['walk1', 'walk2'], speed: 1 };
    const { w, h } = swimBox();
    const vw = document.documentElement.clientWidth;
    const top = window.scrollY;
    const vh = window.innerHeight;
    const sp = 40 * settings.scale * info.speed;
    const wx = keyDir() * sp;
    const wy = ((keys.down ? 1 : 0) - (keys.up ? 1 : 0)) * sp;
    const turn = Math.min(1, dt * 6);
    ch.vx += (wx - ch.vx) * turn;
    ch.vy += (wy - ch.vy) * turn;
    // 段落・画像などのブロックは通り抜けない(自動で泳ぐときと同じく、めり込んだら押し出す)。
    // 押し出された向きの速さは消すので、ブロックの縁に沿って滑るように動く
    const nx = clamp(ch.x + ch.vx * dt, w / 2 + 2, vw - w / 2 - 2);
    const ny = clamp(ch.y + ch.vy * dt, top + h / 2 + 2, top + vh - h / 2 - 2);
    const p = pushOut(nx, ny, w, h);
    if (p.x !== nx) ch.vx = 0;
    if (p.y !== ny) ch.vy = 0;
    ch.x = p.x;
    ch.y = p.y;
    ch.swimT += dt;
    if (Math.abs(ch.vx) > 14) ch.dir = ch.vx > 0 ? 1 : -1;
    const target = Math.atan2(ch.vy, Math.max(30, Math.abs(ch.vx)));
    ch.pitch += (clamp(target, -0.5, 0.5) - ch.pitch) * Math.min(1, dt * 6);
    ch.frame = info.frames[Math.floor(ch.swimT / 0.28) % info.frames.length];
  }

  // 入力欄・編集できる所で打っている文字は、操作に使わない
  function isTyping(e) {
    const el = e.target;
    if (!(el instanceof Element)) return false;
    return !!el.closest('input, textarea, select, [contenteditable]:not([contenteditable="false"])');
  }

  const ARROWS = { ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'up', ArrowDown: 'down' };
  window.addEventListener(
    'keydown',
    (e) => {
      if (!settings.control || !canvas.isConnected || e.ctrlKey || e.altKey || e.metaKey || e.isComposing || isTyping(e)) return;
      const arrow = ARROWS[e.key];
      // ↑ は泳ぐ・飛ぶキャラクターだけが使う(歩くキャラクターではページのスクロールに残す)
      if (arrow && !(arrow === 'up' && !ch.swimming)) keys[arrow] = true;
      else if (e.code === 'KeyC' && !ch.swimming) {
        if (!e.repeat) controlJump();
      } else if (e.code === 'KeyX' && !ch.swimming) {
        if (!e.repeat) controlAction();
      } else return;
      e.preventDefault(); // ページのスクロールや、サイトのショートカットキーに渡さない
      e.stopImmediatePropagation();
    },
    true
  );
  window.addEventListener(
    'keyup',
    (e) => {
      const arrow = ARROWS[e.key];
      if (arrow) keys[arrow] = false;
    },
    true
  );
  window.addEventListener('blur', () => {
    for (const k of Object.keys(keys)) keys[k] = false;
  });

  function drawSwim() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const sp = sprites[ch.frame] || sprites.idle;
    ctx.save();
    ctx.translate(Math.round(ch.x - window.scrollX), Math.round(ch.y - window.scrollY));
    if (ch.dir < 0) ctx.scale(-1, 1);
    ctx.rotate(ch.pitch); // 進む向きに合わせて頭を上げ下げ
    ctx.drawImage(sp.c, -sp.ax, -sp.c.height / 2);
    ctx.restore();
    shown = { sp, px: ch.x - window.scrollX, py: ch.y - window.scrollY, flip: ch.dir < 0, rot: ch.pitch, oy: sp.c.height / 2 };
  }

  // 画面外に出たら(スクロールされたら)、すばやく画面内へ戻ってから落下する。
  function startReturn() {
    ch.mode = 'return';
    ch.standing = null;
    ch.grab = null;
    ch.climb = null;
    ch.vx = 0;
  }

  function updateReturn(dt) {
    const ty = window.scrollY + window.innerHeight * 0.3;
    const dy = ty - ch.y;
    const step = Math.max(1800 * dt, Math.abs(dy) * Math.min(1, dt * 8));
    ch.vy = dy < 0 ? -1 : 1; // 描画するポーズ判定用
    if (Math.abs(dy) <= step) {
      ch.y = ty;
      ch.vy = 0;
      ch.mode = 'air';
    } else {
      ch.y += Math.sign(dy) * step;
    }
  }

  // 「Z」のドット絵(5x5)
  const Z_GLYPH = ['11111', '00010', '00100', '01000', '11111'];

  function drawZzz(x, y, t) {
    const dot = Math.max(2, Math.round(settings.scale / 2));
    for (let i = 0; i < 3; i++) {
      const k = (t * 0.7 + i / 3) % 1;
      const size = dot * (0.6 + 0.6 * k);
      ctx.globalAlpha = Math.min(1, (1 - k) * 1.5);
      ctx.fillStyle = '#4a5cff';
      const gx = x + k * 10 * settings.scale * 0.5 + i * dot;
      const gy = y - k * 12 * settings.scale * 0.6;
      Z_GLYPH.forEach((row, ry) =>
        [...row].forEach((v, rx) => {
          if (v === '1') ctx.fillRect(Math.round(gx + rx * size), Math.round(gy + ry * size), Math.ceil(size), Math.ceil(size));
        })
      );
    }
    ctx.globalAlpha = 1;
  }

  // 歩きのフレーム。walk3/walk4 があるキャラクター(人型)は、踏み出す → 脚を交差 → 反対の脚で踏み出す → 交差 の 4 枚。
  // 1 枚の時間は、体が半歩(約 4 マス = 2 * scale px)進む時間にして、足が地面をすべって見えないようにする
  const WALK4 = ['walk1', 'walk3', 'walk2', 'walk4'];
  function walkFrame() {
    if (!sprites.walk3 || !sprites.walk4) return Math.floor(ch.animT / 0.15) % 2 ? 'walk1' : 'walk2';
    const step = Math.max(0.07, (2 * settings.scale) / WALK);
    return WALK4[Math.floor(ch.animT / step) % WALK4.length];
  }

  function draw() {
    if (ch.mode === 'swim' || (ch.mode === 'drag' && ch.swimming)) return drawSwim();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const sc = settings.scale;
    let name = 'idle';
    let hop = 0; // 上方向のずれ(px)
    if (ch.mode === 'climb') name = ch.frame;
    else if (ch.mode !== 'ground') name = ch.vy < 0 ? 'jump' : 'fall';
    else if (ch.act === 'walk') name = walkFrame();
    else if (ch.act === 'action') {
      const k = Math.min(1, ch.actT / ch.actDur);
      if (ch.actName === 'sit') {
        name = 'sit';
      } else if (ch.actName === 'sleep') {
        name = 'sleep';
      } else if (ch.actName === 'dance') {
        // 向きや傾きは変えず、0.25 秒ごとにポーズを切り替えながらはねる
        const beat = Math.floor(ch.actT / 0.25);
        const phase = (ch.actT % 0.25) / 0.25;
        name = beat % 2 ? 'idle' : 'jump';
        hop = Math.sin(phase * Math.PI) * 4 * sc;
      }
    }
    const sp = sprites[name];
    const px = Math.round(ch.x - window.scrollX);
    const py = Math.round(ch.y - window.scrollY - hop);
    ctx.save();
    ctx.translate(px, py);
    if (ch.dir < 0) ctx.scale(-1, 1);
    ctx.drawImage(sp.c, -sp.ax, -sp.c.height);
    ctx.restore();
    shown = { sp, px, py, flip: ch.dir < 0, rot: 0, oy: sp.c.height };
    if (ch.mode === 'ground' && ch.act === 'action' && ch.actName === 'sleep') {
      drawZzz(px + ch.dir * sp.c.width * 0.3, py - sp.c.height, ch.actT);
    }
  }

  // ---------- つまんで移動(ドラッグ&ドロップ) ----------
  // キャンバスはクリックを素通りさせる(pointer-events:none)ので、ページ全体の pointer イベントを先に受け取り、
  // キャラクターの絵の上で押されたときだけ横取りする。それ以外の操作はページにそのまま届く。
  let shown = null; // 最後に描いた絵 { sp, px, py: 基準点(画面座標), flip, rot, oy: 基準点の絵の上端からの高さ }
  const drag = { id: null, cx: 0, cy: 0, dx: 0, dy: 0, t0: 0, x0: 0, y0: 0, hist: [] };
  let suppressClickUntil = 0;

  // 画面座標 (x, y) がキャラクターの絵(透明でない画素)の上か。少しの余白はつまめるようにする
  function hitTest(x, y) {
    if (!shown || !canvas.isConnected) return false;
    const { sp, px, py, flip, rot, oy } = shown;
    const w = sp.c.width;
    const h = sp.c.height;
    if (!sp.alpha) sp.alpha = sp.c.getContext('2d').getImageData(0, 0, w, h).data;
    const r = Math.max(2, settings.scale);
    const cos = Math.cos(rot);
    const sin = Math.sin(rot);
    for (const [ox, oy2] of [[0, 0], [r, 0], [-r, 0], [0, r], [0, -r]]) {
      let dx = x + ox - px;
      const dy = y + oy2 - py;
      if (flip) dx = -dx;
      const u = Math.floor(dx * cos + dy * sin + sp.ax);
      const v = Math.floor(-dx * sin + dy * cos + oy);
      if (u >= 0 && v >= 0 && u < w && v < h && sp.alpha[(v * w + u) * 4 + 3] > 0) return true;
    }
    return false;
  }

  // つまめる所では「つかむ」カーソル、つまんでいる間は「つかんでいる」カーソル(ページ側のカーソル指定より優先)
  const cursorStyle = document.createElement('style');
  let cursorNow = null;
  function setCursor(c) {
    if (c === cursorNow) return;
    cursorNow = c;
    if (!c) {
      cursorStyle.remove();
      return;
    }
    cursorStyle.textContent =
      `html, html * { cursor: ${c} !important; }` +
      (c === 'grabbing' ? 'html, html * { user-select: none !important; -webkit-user-select: none !important; }' : '');
    if (!cursorStyle.isConnected) (document.head || document.documentElement).appendChild(cursorStyle);
  }

  function startDrag(e) {
    drag.id = e.pointerId;
    drag.cx = drag.x0 = e.clientX;
    drag.cy = drag.y0 = e.clientY;
    drag.t0 = performance.now();
    drag.dx = ch.x - (e.clientX + window.scrollX);
    drag.dy = ch.y - (e.clientY + window.scrollY);
    drag.hist = [{ t: drag.t0, x: e.clientX, y: e.clientY }];
    ch.mode = 'drag';
    ch.standing = ch.grab = ch.climb = null;
    ch.act = 'idle';
    ch.vx = ch.vy = 0; // 落下の絵(手足をぶら下げた姿)で持ち上がる
    ch.pitch = 0;
    setCursor('grabbing');
  }

  // 指(マウス)の位置にキャラクターを置く。スクロールしても指についてくる
  function followPointer() {
    ch.x = drag.cx + window.scrollX + drag.dx;
    ch.y = drag.cy + window.scrollY + drag.dy;
  }

  // 離したら、投げた勢いで落ちる(泳ぐキャラクターは、そこから泳ぎ始める)。e が null なら勢いなしで離す
  function endDrag(e) {
    if (drag.id === null) return;
    drag.id = null;
    setCursor(null);
    if (ch.mode !== 'drag') return;
    let vx = 0;
    let vy = 0;
    if (e) {
      const now = performance.now();
      const old = drag.hist.find((p) => now - p.t <= 100) || drag.hist[drag.hist.length - 1];
      const dt = Math.max(0.016, (now - old.t) / 1000);
      vx = (e.clientX - old.x) / dt;
      vy = (e.clientY - old.y) / dt;
      // ほとんど動かさずに離したら(ちょんとつついたら)、その場で小さくはねる
      if (Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) < 4 && now - drag.t0 < 300) vy = -900;
    }
    if (Math.abs(vx) > 30) ch.dir = vx > 0 ? 1 : -1;
    if (ch.swimming) {
      ch.mode = 'swim';
      ch.vx = clamp(vx, -600, 600);
      ch.vy = clamp(vy, -600, 600);
      ch.stuck = 0;
      pickTarget();
      return;
    }
    ch.mode = 'air';
    ch.vx = clamp(vx, -MAX_VX, MAX_VX);
    ch.vy = clamp(vy, -1800, 1800);
    ch.airT = 0;
    ch.ignore = null;
  }

  window.addEventListener(
    'pointerdown',
    (e) => {
      if (!e.isPrimary || e.button !== 0 || drag.id !== null || !hitTest(e.clientX, e.clientY)) return;
      e.preventDefault(); // 文字の選択・リンクのドラッグを始めない
      e.stopImmediatePropagation(); // ページ側には押されたことを伝えない
      startDrag(e);
    },
    true
  );
  window.addEventListener(
    'pointermove',
    (e) => {
      if (drag.id === null) {
        if (e.pointerType === 'mouse' && !e.buttons) setCursor(hitTest(e.clientX, e.clientY) ? 'grab' : null);
        return;
      }
      if (e.pointerId !== drag.id) return;
      e.preventDefault();
      e.stopImmediatePropagation();
      drag.cx = e.clientX;
      drag.cy = e.clientY;
      const now = performance.now();
      drag.hist.push({ t: now, x: e.clientX, y: e.clientY });
      while (drag.hist.length > 2 && now - drag.hist[0].t > 150) drag.hist.shift();
    },
    true
  );
  const release = (e) => {
    if (drag.id === null || e.pointerId !== drag.id) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    endDrag(e.type === 'pointerup' ? e : null);
    suppressClickUntil = performance.now() + 400; // 離したあとの click がページ(リンクなど)に届かないように
  };
  window.addEventListener('pointerup', release, true);
  window.addEventListener('pointercancel', release, true);
  window.addEventListener(
    'click',
    (e) => {
      if (performance.now() > suppressClickUntil) return;
      suppressClickUntil = 0;
      e.preventDefault();
      e.stopImmediatePropagation();
    },
    true
  );
  window.addEventListener('blur', () => endDrag(null)); // つまんだまま別のウィンドウへ移ったら離す

  // ---------- メインループ ----------
  let last = 0;
  let raf = 0;
  let timerId = 0;

  function frame(now) {
    raf = requestAnimationFrame(frame);
    const dt = Math.min(0.05, (now - last) / 1000 || 0);
    last = now;
    if (document.hidden) return;
    if (ch.mode === 'drag') {
      followPointer();
      draw();
      return;
    }
    if (ch.mode === 'swim') {
      updateSwim(dt);
      draw();
      return;
    }
    if (platforms[0]) platforms[0].t = floorY();
    const top = window.scrollY;
    if (ch.mode !== 'return' && (ch.y < top || ch.y > top + window.innerHeight + 2)) startReturn();
    if (ch.mode === 'return') updateReturn(dt);
    else if (ch.mode === 'climb') updateClimb(dt);
    else if (ch.mode === 'ground' && ch.standing) updateGround(dt);
    else updateAir(dt);
    draw();
  }

  function start() {
    if (canvas.isConnected) return;
    buildSprites();
    document.documentElement.appendChild(canvas);
    resize();
    refreshPlatforms();
    spawn();
    last = performance.now();
    raf = requestAnimationFrame(frame);
    timerId = setInterval(refreshPlatforms, 800);
  }

  function stop() {
    endDrag(null);
    cancelAnimationFrame(raf);
    clearInterval(timerId);
    canvas.remove();
  }

  // 表示するキャラクターの絵データを読み込んでから、表示を始める/絵を差し替える
  let applySeq = 0;
  function apply() {
    if (!settings.enabled) {
      applySeq++;
      stop();
      return;
    }
    const seq = ++applySeq;
    PW.load(settings.character)
      .catch(() => PW.load((settings.character = DEFAULTS.character))) // 消えたキャラクターなら既定の絵
      .then(() => {
        if (seq !== applySeq || !settings.enabled) return; // 読み込み中に設定が変わった
        if (canvas.isConnected) buildSprites();
        else start();
      })
      .catch((e) => console.error('Pixel Walker: 絵の読み込みに失敗しました', e));
  }

  let scrollPending = false;
  window.addEventListener(
    'scroll',
    () => {
      if (scrollPending) return;
      scrollPending = true;
      setTimeout(() => {
        scrollPending = false;
        refreshPlatforms();
      }, 100);
    },
    { passive: true }
  );

  window.addEventListener('resize', () => {
    resize();
    refreshPlatforms();
  });

  chrome.storage.sync.get(DEFAULTS, (v) => {
    settings = { ...DEFAULTS, ...v };
    apply();
  });

  // ポップアップからの即時反映(保存の通知を待たずに、開いているタブへ直接届く)
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg && msg.type === 'pw-set' && msg.changes) {
      Object.assign(settings, msg.changes);
      apply();
    }
  });

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'sync') return;
    for (const [k, c] of Object.entries(changes)) settings[k] = c.newValue;
    apply();
  });
})();
