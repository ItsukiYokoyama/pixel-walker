"""chars.js の読み書きと、ドット絵の格子・パレットを扱う道具(Python 標準ライブラリだけ)。"""
import json, re, zlib, struct, colorsys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = os.path.join(ROOT, 'chars.js')


CHAR_DIR = os.path.join(ROOT, 'chars')


def load_raw(path=CHARS):
    """[[id, 名前, (ジャンル)]] と {id: JSON 文字列}。絵データは chars/<id>.json(古い形式では chars.js の中)"""
    src = open(path, encoding='utf-8').read()
    idx = json.loads(re.search(r'window.PW_INDEX = (.*?);\n', src).group(1))
    raw = {k: json.loads(v) for k, v in re.findall(r'^  "(\w+)": (".*"),?$', src, re.M)}
    for row in idx:
        f = os.path.join(CHAR_DIR, row[0] + '.json')
        if row[0] not in raw and os.path.exists(f):
            raw[row[0]] = open(f, encoding='utf-8').read()
    return idx, raw


def load(path=CHARS):
    idx, raw = load_raw(path)
    return idx, {k: json.loads(v) for k, v in raw.items()}


def decode(enc):
    out = []
    for ch, n in re.findall(r'(\D)(\d*)', enc):
        out += [ch] * (int(n) if n else 1)
    return out


def encode(row):
    out = []
    i = 0
    while i < len(row):
        j = i
        while j < len(row) and row[j] == row[i]:
            j += 1
        assert not row[i].isdigit()
        out.append(row[i] + (str(j - i) if j - i > 1 else ''))
        i = j
    return ''.join(out)


def hexrgb(h):
    n = int(h[1:], 16)
    return ((n >> 16) & 255, (n >> 8) & 255, n & 255)


def rgbhex(c):
    return '#%02x%02x%02x' % tuple(max(0, min(255, round(v))) for v in c)


def tint(h, f):
    return rgbhex([v * f if f < 1 else v + (255 - v) * (f - 1) for v in hexrgb(h)])


def mix(a, b, t):
    return rgbhex([x + (y - x) * t for x, y in zip(hexrgb(a), hexrgb(b))])


def lum(h):
    r, g, b = hexrgb(h)
    return .3 * r + .59 * g + .11 * b


def hls(h):
    return colorsys.rgb_to_hls(*[v / 255 for v in hexrgb(h)])


def fromhls(H, L, S):
    return rgbhex([v * 255 for v in colorsys.hls_to_rgb(H % 1, max(0, min(1, L)), max(0, min(1, S)))])


def palette(d):
    """characters.js の palette() と同じ規則で、全記号の色を求める"""
    p = {'k': '#2b2233', 'e': '#0f0b14', **d['palette']}
    out = dict(p)
    for k, v in p.items():
        K = k.upper()
        if k != 'k' and k != K and K not in p:
            out[K] = tint(v, 0.8)
    for k in 'tla':
        if k not in p and 'y' in out:
            out[k] = out['y']
            out[k.upper()] = out.get('Y')
    return out


def png(path, W, H, px):
    raw = b''.join(b'\0' + bytes(sum((px[y][x] for x in range(W)), ())) for y in range(H))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def sheet(path, items, scale=4, cols=8, cell=(48, 48), bg=(246, 244, 239)):
    """items: [(格子, 色の辞書)] を並べた確認用の PNG"""
    cw, chh = cell
    rows = (len(items) + cols - 1) // cols
    W = cols * (cw + 2) * scale
    H = rows * (chh + 2) * scale
    px = [[bg] * W for _ in range(H)]
    for i, (g, pal) in enumerate(items):
        ox = (i % cols) * (cw + 2) * scale + scale
        oy = (i // cols) * (chh + 2) * scale + scale
        for y in range(chh * scale):
            for x in range(cw * scale):
                px[oy + y][ox + x] = (255, 255, 255)
        for y, row in enumerate(g[:chh]):
            for x, c in enumerate(row[:cw]):
                col = pal.get(c)
                if not col:
                    continue
                rgb = hexrgb(col)
                for dy in range(scale):
                    r = px[oy + y * scale + dy]
                    for dx in range(scale):
                        r[ox + x * scale + dx] = rgb
    png(path, W, H, px)
