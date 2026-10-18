"""既存のキャラクターから、色替え・模様・角や翼を足した派生キャラクターを作る。"""
import math
from pwlib import decode, palette, hls, fromhls, hexrgb, mix
from engine import Canvas, Palette, T, ellipse, rect, poly, union, capsule, N4

GROUPS = {'main': 'fyYz', 'b': 'gmMx', 'c': 'vwWu', 'd': 'hjJo'}


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(hexrgb(a), hexrgb(b)))


def recolor(base_pal, maps, outline=None):
    """maps: {グループ名: 新しい基本色}。グループの基本色(2 文字目: y/m/w/j)からの差で、影や明るい色も同じように変える"""
    full = dict(base_pal)
    group_of = {}
    for g, syms in GROUPS.items():
        for s in syms:
            if s in full:
                group_of[s] = g
    # 記号の決まっていない色(陰影の自動生成で増えた色)は、いちばん近い色のグループに入れる
    named = [s for s in group_of]
    for s, c in full.items():
        if s in group_of or s in 'keq' or not c:
            continue
        near = min(named, key=lambda n: dist(full[n], c)) if named else None
        if near and dist(full[near], c) < 60 ** 2:
            group_of[s] = group_of[near]
    out = dict(full)
    for s, g in group_of.items():
        if g not in maps:
            continue
        ob = full[GROUPS[g][1]]
        nb = maps[g]
        Ho, Lo, So = hls(ob)
        Hn, Ln, Sn = hls(nb)
        H, L, S = hls(full[s])
        dL = Ln - Lo
        L2 = 0.5 * (L * (Ln / Lo if Lo else 1)) + 0.5 * (L + dL)
        S2 = S * (Sn / So) if So > 0.02 else Sn
        out[s] = fromhls(Hn + (H - Ho), L2, min(1, S2))
    if outline:
        out['k'] = outline
    return out


def spots(g, syms, mark, seed=0, every=11):
    """syms の画素に、ぽつぽつと mark の斑点を置く(格子の位置で決まるので、フレーム間でほぼそろう)"""
    H, W = len(g), len(g[0])
    out = [r[:] for r in g]
    for y in range(H):
        for x in range(W):
            if (x * 7 + y * 13 + seed) % every == 0 and g[y][x] in syms:
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    if 0 <= y + dy < H and 0 <= x + dx < W and g[y + dy][x + dx] in syms:
                        out[y + dy][x + dx] = mark
    return out


def eye_of(g):
    """目(e)の位置。いちばん右上の e"""
    best = None
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            if c == 'e' and (best is None or (x - y) > (best[0] - best[1])):
                best = (x, y)
    return best


def back_of(g, ax):
    """背中(体の中心より少し後ろの、いちばん上の画素)"""
    xs = [int(ax) - 3, int(ax) - 2, int(ax) - 4]
    for x in xs:
        for y, r in enumerate(g):
            if 0 <= x < len(r) and r[x] not in '.k':
                return (x, y)
    return (int(ax), len(g) // 2)


def overlay(frame, colors, behind=(), front=(), name=''):
    """frame の格子に、後ろの部品(翼など)と前の部品(角など)を足す。部品は (形, 変換, 色)"""
    g = frame['g']
    H, W = len(g), len(g[0])
    pal = Palette(colors.get('k', '#2b2233'))
    used = set(colors) | {c for r in g for c in r}
    pal.free = [s for s in pal.free if s not in used]
    pal.colors = dict(colors)
    # 上に伸びる部品のために、上と横に余白をとる
    pad_t, pad_x = 10, 6
    cv = Canvas(W + pad_x * 2, H + pad_t, pal)
    for f, t, col in behind:
        cv.shape(f, T(t.x + pad_x, t.y + pad_t, math.degrees(t.a)), pal.ramp(col))
    for y in range(H):
        for x in range(W):
            if g[y][x] != '.':
                cv.g[y + pad_t][x + pad_x] = g[y][x]
                cv.part[y + pad_t][x + pad_x] = -1
    for f, t, col in front:
        cv.shape(f, T(t.x + pad_x, t.y + pad_t, math.degrees(t.a)), pal.ramp(col))
    out = cv.finish()
    # 余白を切り詰める(足元・足場の位置はずらさない)
    top = 0
    while top < pad_t and all(c == '.' for c in out[top]):
        top += 1
    left = 0
    while left < pad_x and all(r[left] == '.' for r in out):
        left += 1
    right = 0
    while right < pad_x and all(r[-1 - right] == '.' for r in out):
        right += 1
    # 足場の角(列 36)の位置を保つため、ぶら下がりのフレームは左の余白をちょうど pad_x だけ切る
    ledge = frame.get('ledgeRow') is not None
    cutL = pad_x if ledge else left
    out = [r[cutL:len(r) - right] for r in out[top:]]
    nf = dict(frame)
    nf['g'] = out
    nf['ax'] = frame['ax'] + pad_x - cutL
    if ledge:
        nf['ledgeRow'] = frame['ledgeRow'] + pad_t - top
    return nf, pal.colors


def horn(col):
    def make(g, fr):
        e = eye_of(g)
        if not e:
            return [], []
        x, y = e
        return [], [(poly([(-1.4, 0), (1.4, 0), (1.6, -7.5)]), T(x + 0.5, y - 2.0, 18), col)]
    return make


def wings(col, kind='feather', size=1.0):
    def make(g, fr):
        if fr.get('ledgeRow') is not None:  # 壁をよじ登るときは翼をたたむ
            return [], []
        bx, by = back_of(g, fr['ax'])
        s = size
        if kind == 'bat':
            shp = poly([(0, 0), (-3 * s, -8 * s), (-11 * s, -9 * s), (-9 * s, -5 * s), (-11 * s, -2 * s), (-7 * s, -2.5 * s),
                        (-6 * s, 1 * s)])
        else:
            shp = union(ellipse(-4.5 * s, -4.5 * s, 6 * s, 3.4 * s), ellipse(-8.5 * s, -6.5 * s, 3.8 * s, 2.4 * s),
                        ellipse(-6 * s, -1.5 * s, 4.6 * s, 2.4 * s))
        return [(shp, T(bx + 1.5, by + 2.5, 8), col)], []
    return make


def horns2(col):
    def make(g, fr):
        e = eye_of(g)
        if not e:
            return [], []
        x, y = e
        return [], [(poly([(-1.2, 0), (1.2, 0), (-1.5, -5.5)]), T(x - 2.5, y - 2.0, -15), col)]
    return make


def derive(base, spec):
    """base: chars.js のキャラクター(dict)。spec: maps / outline / spots / parts(関数のリスト)"""
    pal = palette(base)
    colors = recolor(pal, spec.get('maps', {}), spec.get('outline'))
    for k, v in spec.get('set', {}).items():
        colors[k] = v
    frames = {}
    makers = spec.get('parts', [])
    pool = '%&*+<=>?@^_~;:!#$|/[]{}()`-' + ''.join(chr(c) for c in range(0x3b1, 0x3ca)) + ''.join(chr(c) for c in range(0x430, 0x450))
    used = set(colors) | {c for f in base['frames'].values() for r in f['rows'] for c in decode(r)}
    mark = next(c for c in pool if c not in used)
    for name, f in base['frames'].items():
        g = [decode(r) for r in f['rows']]
        fr = {'g': g, 'ax': f['ax'], 'ledgeRow': f.get('ledgeRow')}
        if spec.get('spots'):
            sp = spec['spots']
            colors[mark] = sp['col']
            fr['g'] = spots(fr['g'], sp.get('on', 'fyYz'), mark, sp.get('seed', 0), sp.get('every', 11))
        if makers:
            behind, front = [], []
            for mk in makers:
                b, fr_ = mk(fr['g'], fr)
                behind += b
                front += fr_
            fr, colors = overlay(fr, colors, behind, front, name)
        frames[name] = fr
    return frames, colors
