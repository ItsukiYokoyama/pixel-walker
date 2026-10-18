"""乗り物(横から見た絵)の生成。車体を部品で描き、ポーズは車体の傾き・車輪の回転で表す。

ローカル座標: x = 前(右)、y = 下。地面が y = 0、車体の中心が x = 0。
飛ぶ・泳ぐ乗り物(fly=True)は、地面を走らず画面を自由に移動する(content.js の「泳ぐ」動き)。
"""
import math
from engine import Canvas, Palette, T, ellipse, rect, rrect, capsule, poly, union, minus, inter
from humanoid import trim

HANG_W, HANG_H = 44, 52


def wheel(cv, pal, t, x, r, spin, tire='#2a2a30', hub='#c8ccd4', y=None):
    y = -r if y is None else y
    cv.shape(ellipse(x, y, r, r), t, pal.ramp(tire))
    cv.shape(ellipse(x, y, r * 0.52, r * 0.52), t, pal.ramp(hub), line=False)
    # 回転が分かるように、ハブに 1 点の印
    a = math.radians(spin)
    cv.dot(t, x + math.cos(a) * r * 0.42, y + math.sin(a) * r * 0.42, pal.sym('#5a5e68'))
    cv.dot(t, x - math.cos(a) * r * 0.42, y - math.sin(a) * r * 0.42, pal.sym('#5a5e68'))


def draw(spec, cv, t, step=0, spin=0, bob=0.0, off=False):
    pal = cv.pal
    R = pal.ramp
    tb = t.then(0, -bob)  # 車体(はずむ)
    for part in spec['parts']:
        kind = part[0]
        if kind == 'step':  # 歩きのフレームで切り替わる部品
            if step % 2 != part[1]:
                continue
            part = part[2]
            kind = part[0]
        if kind == 'eye':  # 目(寝ているときは閉じる)
            _, x, y = part[:3]
            big = len(part) > 3 and part[3]
            if off:
                cv.dot(tb, x - 0.5, y + 1, 'e')
                cv.dot(tb, x + 0.5, y + 1, 'e')
            else:
                cv.dot(tb, x, y, 'q' if big else 'e')
                cv.dot(tb, x, y + 1, 'e')
                if big:
                    cv.dot(tb, x + 1, y, 'e')
                    cv.dot(tb, x + 1, y + 1, 'e')
            continue
        if kind == 'poly':
            _, pts, col = part[:3]
            cv.shape(poly(pts), tb, R(col), line=part[3] if len(part) > 3 else True)
        elif kind == 'rrect':
            _, x0, y0, x1, y1, r, col = part[:7]
            cv.shape(rrect(x0, y0, x1, y1, r), tb, R(col), line=part[7] if len(part) > 7 else True)
        elif kind == 'ellipse':
            _, cx, cy, rx, ry, col = part[:6]
            cv.shape(ellipse(cx, cy, rx, ry), tb, R(col), line=part[6] if len(part) > 6 else True)
        elif kind == 'capsule':
            _, x0, y0, x1, y1, r, col = part
            cv.shape(capsule(x0, y0, x1, y1, r), tb, R(col))
        elif kind == 'window':  # 窓(平らな色 + 光の反射)
            _, pts, col = part
            cv.shape(poly(pts), tb, pal.ramp(col, light=1.35, shadow=0.85), line=False)
            x0 = min(p[0] for p in pts)
            y0 = min(p[1] for p in pts)
            cv.dot(tb, x0 + 1.5, y0 + 1.2, pal.sym('#ffffff'))
        elif kind == 'dot':
            _, x, y, col = part
            cv.dot(tb, x, y, pal.sym(col))
        elif kind == 'light':  # 前照灯(寝ているときは消える)
            _, x, y, col = part
            cv.dot(tb, x, y, pal.sym('#8a8070' if off else col))
        elif kind == 'blink':  # 交互に光る(パトランプ)
            _, x, y, c1, c2 = part
            cv.dot(tb, x, y, pal.sym(c1 if step % 2 == 0 else c2))
        elif kind == 'flame':  # 噴射(歩きフレームで長さが変わる)
            _, x, y, ln = part
            l2 = ln * (1.0 if step % 2 == 0 else 0.7)
            cv.shape(poly([(x, y - 2.2), (x - l2, y), (x, y + 2.2)]), tb, R('#f8a030'), line=False)
            cv.shape(poly([(x, y - 1.0), (x - l2 * 0.55, y), (x, y + 1.0)]), tb, R('#fff0a0'), line=False)
        elif kind == 'rotor':  # ヘリのローター(フレームで長さを変えて回して見せる)
            _, x, y, ln = part
            l2 = ln if step % 2 == 0 else ln * 0.35
            cv.shape(rect(x - l2, y - 0.5, x + l2, 0.5 + y), tb, R('#3a3e48'), line=False)
        elif kind == 'prop':
            _, x, y, ln = part
            l2 = ln if step % 2 == 0 else ln * 0.3
            cv.shape(rect(x - 0.5, y - l2, x + 0.5, y + l2), tb, R('#3a3e48'), line=False)
    for wx, r in spec.get('wheels', []):
        wheel(cv, pal, t, wx, r, spin + wx * 20, spec.get('tire', '#2a2a30'), spec.get('hub', '#c8ccd4'))
    for x0, x1, h in spec.get('tracks', []):
        cv.shape(rrect(x0, -h, x1, 0, h / 2), t, R('#3a3a40'))
        n = int((x1 - x0) / 3)
        for i in range(n + 1):
            wx = x0 + h / 2 + i * (x1 - x0 - h) / max(1, n)
            cv.shape(ellipse(wx, -h / 2, 1.2, 1.2), t, R('#8a8e98'), line=False)
        for i in range(int(x1 - x0)):
            if (i + step) % 3 == 0:
                cv.dot(t, x0 + i + 0.5, -h + 0.3, pal.sym('#1d1d22'))


def frames(spec):
    pal = Palette(spec.get('outline', '#22202a'))
    L = spec['len']  # 前後の長さ
    H = spec['h']  # 高さ
    out = {}
    W = max(36, int(L + 6))
    Hh = int(H + 6)
    fly = spec.get('fly')

    def make(w, h, t, **kw):
        cv = Canvas(w, h, pal)
        draw(spec, cv, t, **kw)
        return cv.finish()

    cx = W / 2
    ground = Hh - 1.0
    if fly:
        cy = Hh / 2 + H / 2
        for name, kw in (('idle', {}), ('walk1', dict(step=0)), ('walk2', dict(step=1, bob=0.6))):
            out[name] = (make(W, Hh, T(cx, cy), **kw), cx, None)
        return out, pal.colors
    out['idle'] = (make(W, Hh, T(cx, ground)), cx, None)
    out['walk1'] = (make(W, Hh, T(cx, ground), step=0, spin=0), cx, None)
    out['walk2'] = (make(W, Hh, T(cx, ground), step=1, spin=60, bob=0.7), cx, None)
    # ジャンプ: 後ろの車輪を軸に前を上げる / 落下: 前を下げる
    rear = -L / 2 + 3
    for name, deg in (('jump', -14), ('fall', 10)):
        rad = math.radians(abs(deg))
        extra = int(math.ceil(L * math.sin(rad))) + 2
        h2 = Hh + extra
        if deg < 0:
            t = T(cx + rear, h2 - 1.0, deg).then(-rear, 0)
        else:
            t = T(cx - rear, h2 - 1.0, deg).then(rear, 0)
        out[name] = (trim(make(W, h2, t, step=0))[0], cx, None)
    out['sit'] = (make(W, Hh, T(cx, ground)), cx, None)
    out['sleep'] = (make(W, Hh, T(cx, ground + 0.6), off=True), cx, None)
    # よじ登り: 前の車輪を足場の角 (36, L) に当てて、車体を立てる
    front = L / 2 - 2
    for name, deg, fx, Lr in (('hang1', -84, 35.5, 8), ('hang2', -80, 35.5, 8), ('pull1', -58, 37.5, 0),
                              ('pull2', -34, 40.0, 0), ('pull3', -12, 42.0, 0)):
        rad = math.radians(-deg)
        # 車体が角から左下へ伸びる長さ
        down = (L / 2 + front) * math.sin(rad) + H * math.cos(rad) * 0.2
        ledge = max(Lr, int(round(HANG_H - 2 - down))) if Lr == 0 else Lr
        if name.startswith('hang'):
            ledge = 6
        t = T(fx, ledge, deg).then(-front, 0)
        g = make(HANG_W, HANG_H, t, step=0)
        g, cut = trim(g)
        # 中心: 車体の真ん中の、画面上の x
        ax = t.apply(0, -H / 2)[0]
        out[name] = (g, round(ax), ledge - cut)
    return out, pal.colors
