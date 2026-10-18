"""README 用の画像 docs/characters.png を作り直す。ジャンルごとに先頭の 16 体の「待機」ポーズを 1 段に並べる。

使い方: python3 tools/docs_image.py   (tools/build.py で絵データを作り直したあとに実行する)
"""
import json, os
from pwlib import ROOT, decode, hexrgb, load_raw, palette, png

GENRES = ['people', 'animals', 'birds', 'sea', 'vehicles', 'fantasy']
COLS = 16
SCALE = 3
CELL_W, CELL_H = 138, 144  # 1 体ぶんの枠(px)
BOTTOM = 4  # 枠の下の余白(px)
BG = (250, 248, 243)


def main():
    idx, raw = load_raw()
    W, H = COLS * CELL_W, len(GENRES) * CELL_H
    px = [[BG] * W for _ in range(H)]
    for gy, genre in enumerate(GENRES):
        ids = [row[0] for row in idx if row[2] == genre][:COLS]
        for gx, cid in enumerate(ids):
            d = json.loads(raw[cid])
            pal = palette(d)
            g = [decode(r) for r in d['frames']['idle']['rows']]
            # 枠の中で左右の中央、下に BOTTOM px の余白
            ox = gx * CELL_W + (CELL_W - len(g[0]) * SCALE) // 2
            oy = gy * CELL_H + CELL_H - BOTTOM - len(g) * SCALE
            for y, row in enumerate(g):
                for x, c in enumerate(row):
                    col = pal.get(c)
                    if not col:
                        continue
                    rgb = hexrgb(col)
                    for dy in range(SCALE):
                        for dx in range(SCALE):
                            X, Y = ox + x * SCALE + dx, oy + y * SCALE + dy
                            if 0 <= X < W and gy * CELL_H <= Y < (gy + 1) * CELL_H:
                                px[Y][X] = rgb
    path = os.path.join(ROOT, 'docs', 'characters.png')
    png(path, W, H, px)
    print(path, W, 'x', H)


if __name__ == '__main__':
    main()
