"""ベクターの部品(楕円・太い線・多角形)を、変換(回転・平行移動)つきでドット格子に塗る小さな描画エンジン。

部品は「色の段(ramp)」で塗る。ramp は 4 段の記号 (明るい, 基本, 影, 濃い影)。
塗り終えたら finish() で、上からの光の陰影・部品の境目の線・外側の輪郭を付ける。
"""
import math
from pwlib import tint, mix, lum, hls, fromhls

N4 = [(0, -1), (1, 0), (0, 1), (-1, 0)]
N8 = N4 + [(1, 1), (1, -1), (-1, 1), (-1, -1)]

# ramp に割り当てる記号(数字・'.'・k/e/q 以外)
SYMS = [c for c in 'abcdfghijlmnoprstuvwxyzABCDEFGHIJLMNOPQRSTUVWXYZ!#$%&*+<=>?@^_~;:,|/[]{}()`-'
        + ''.join(chr(c) for c in range(0x3b1, 0x3ca)) + ''.join(chr(c) for c in range(0x430, 0x450))
        if c not in 'keqKEQ']


class Palette:
    """色 → 記号。ramp(基本色) から 4 段の記号を作る"""

    def __init__(self, outline='#2b2233'):
        self.colors = {'k': outline, 'e': '#1d1620', 'q': '#ffffff'}
        self.free = list(SYMS)
        self.bycol = {}

    def sym(self, col):
        if col not in self.bycol:
            s = self.free.pop(0)
            self.bycol[col] = s
            self.colors[s] = col
        return self.bycol[col]

    def ramp(self, base, light=1.25, shadow=0.78, dark=0.6):
        """基本色から (明, 基本, 影, 濃) の 4 記号。影は少し色相をずらして暖色/寒色に寄せる"""
        H, L, S = hls(base)
        sh = fromhls(H + (0.012 if 0.08 < H < 0.6 else -0.008), L * shadow, S * 0.95)
        dk = mix(fromhls(H + (0.02 if 0.08 < H < 0.6 else -0.012), L * dark, S * 0.85), self.colors['k'], 0.25)
        return (self.sym(tint(base, light)), self.sym(base), self.sym(sh), self.sym(dk))

    def flat(self, col):
        s = self.sym(col)
        return (s, s, s, s)


class T:
    """2D アフィン変換(回転 deg + 平行移動)。apply は ローカル → 画面"""

    def __init__(self, x=0.0, y=0.0, deg=0.0, sx=1.0):
        self.x, self.y, self.a, self.sx = x, y, math.radians(deg), sx

    def apply(self, px, py):
        px *= self.sx
        c, s = math.cos(self.a), math.sin(self.a)
        return (self.x + px * c - py * s, self.y + px * s + py * c)

    def inv(self, wx, wy):
        dx, dy = wx - self.x, wy - self.y
        c, s = math.cos(self.a), math.sin(self.a)
        return ((dx * c + dy * s) / self.sx, -dx * s + dy * c)

    def then(self, x=0.0, y=0.0, deg=0.0):
        """この変換の中に、さらにローカルな変換を入れ子にする"""
        ox, oy = self.apply(x, y)
        return T(ox, oy, math.degrees(self.a) + deg * (1 if self.sx > 0 else -1), self.sx)


# ---- 形(ローカル座標で、点が中にあるか) ----
def ellipse(cx, cy, rx, ry):
    return lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


def rect(x0, y0, x1, y1):
    return lambda x, y: x0 <= x <= x1 and y0 <= y <= y1


def rrect(x0, y0, x1, y1, r):
    def f(x, y):
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            return False
        cx = min(max(x, x0 + r), x1 - r)
        cy = min(max(y, y0 + r), y1 - r)
        return (x - cx) ** 2 + (y - cy) ** 2 <= r * r
    return f


def capsule(x0, y0, x1, y1, r0, r1=None):
    r1 = r0 if r1 is None else r1

    def f(x, y):
        dx, dy = x1 - x0, y1 - y0
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((x - x0) * dx + (y - y0) * dy) / L))
        px, py = x0 + dx * t, y0 + dy * t
        r = r0 + (r1 - r0) * t
        return (x - px) ** 2 + (y - py) ** 2 <= r * r
    return f


def poly(pts):
    def f(x, y):
        inside = False
        n = len(pts)
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
                inside = not inside
        return inside
    return f


def union(*fs):
    return lambda x, y: any(f(x, y) for f in fs)


def minus(a, b):
    return lambda x, y: a(x, y) and not b(x, y)


def inter(a, b):
    return lambda x, y: a(x, y) and b(x, y)


class Canvas:
    def __init__(self, w, h, pal):
        self.w, self.h, self.pal = w, h, pal
        self.g = [['.'] * w for _ in range(h)]
        self.part = [[-1] * w for _ in range(h)]  # どの部品の画素か(境目の線用)
        self.parts = []  # 部品ごとの (ramp, 線を引くか, 陰影)

    def shape(self, f, t, ramp, line=True, shade=True, bbox=None):
        """形 f をローカル座標で、変換 t をかけて塗る。後から塗った部品が手前"""
        pid = len(self.parts)
        self.parts.append((ramp, line, shade))
        x0, y0, x1, y1 = bbox or (0, 0, self.w, self.h)
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                lx, ly = t.inv(x + 0.5, y + 0.5)
                if f(lx, ly):
                    self.g[y][x] = ramp[1]
                    self.part[y][x] = pid
        return pid

    def dot(self, t, lx, ly, sym, pid=None):
        x, y = t.apply(lx, ly)
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = sym
            if pid is not None:
                self.part[y][x] = pid

    def at(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else '.'

    def pid(self, x, y):
        return self.part[y][x] if 0 <= x < self.w and 0 <= y < self.h else -1

    def finish(self, outline=True):
        """陰影(上からの光)・部品の境目の線・外側の輪郭"""
        W, H = self.w, self.h
        g = self.g
        out = [r[:] for r in g]
        # 1) 部品ごとの陰影: 左上の縁は明るく、右下の縁は影、下側の深い所は濃い影
        for y in range(H):
            for x in range(W):
                p = self.part[y][x]
                if p < 0:
                    continue
                ramp, line, shade = self.parts[p]
                if not shade or g[y][x] != ramp[1]:
                    continue
                # 手前に重なった部品(後から塗った部品)との境目は、体の縁ではないので陰影を付けない
                same = lambda dx, dy: self.pid(x + dx, y + dy) >= p
                if not same(1, 1) or not same(0, 2):
                    out[y][x] = ramp[2] if same(0, -1) or same(-1, 0) else ramp[1]
                    if not same(0, 1) and not same(1, 0) and same(-1, -1):
                        out[y][x] = ramp[3]
                elif not same(-1, -1) or not same(0, -1):
                    out[y][x] = ramp[0]
        # 2) 部品の境目: 奥の部品の、手前の部品に接する画素に、奥の部品の濃い色で線を引く(色が近いときだけ)
        for y in range(H):
            for x in range(W):
                p = self.part[y][x]
                if p < 0 or g[y][x] != self.parts[p][0][1] and g[y][x] not in self.parts[p][0]:
                    continue
                ramp, line, shade = self.parts[p]
                if not line:
                    continue
                for dx, dy in N4:
                    q = self.pid(x + dx, y + dy)
                    if q > p and self.parts[q][1]:
                        a = self.pal.colors[ramp[1]]
                        b = self.pal.colors[self.parts[q][0][1]]
                        if abs(lum(a) - lum(b)) < 46:
                            out[y][x] = ramp[3]
                            break
        self.g = out
        # 3) 外側の輪郭
        if outline:
            add = [(x, y) for y in range(H) for x in range(W)
                   if self.g[y][x] == '.' and any(self.at(x + dx, y + dy) not in '.k' for dx, dy in N4)]
            for x, y in add:
                self.g[y][x] = 'k'
        return self.g
