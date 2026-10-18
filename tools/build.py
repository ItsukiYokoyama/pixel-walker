"""chars.js を作り直す。既存のキャラクター(手描きの絵データ)はそのまま残し、ジャンルを付け、新しいキャラクターを生成して足す。

使い方: python3 tools/build.py   (Python 3 の標準ライブラリだけで動く)
"""
import json, re, sys
import os
from pwlib import CHARS, CHAR_DIR, ROOT, encode, load_raw
import humanoid, vehicle, derive as dv
from roster_people import PEOPLE
from roster_vehicles import VEHICLES
from roster_creatures import CREATURES
from roster_derived import DERIVED

# 既存キャラクターのジャンル(載っていないものは animals)
OLD_GENRE = {'adventurer': 'people'}
for i in 'duck chick owl eagle hawk ostrich flamingo penguin croc turtle lizard snake frog'.split():
    OLD_GENRE[i] = 'birds'
for i in 'whale dolphin orca shark ray angler sealion seal walrus seaotter manatee'.split():
    OLD_GENRE[i] = 'sea'
GENRES = ['people', 'animals', 'birds', 'sea', 'vehicles', 'fantasy']


def pack(frames, colors, extra=None):
    used = set()
    fr = {}
    for name, f in frames.items():
        rows = [encode(r) for r in f['g']]
        for r in f['g']:
            used.update(r)
        d = {'rows': rows, 'ax': f['ax']}
        if f.get('ledgeRow') is not None:
            d['ledgeRow'] = f['ledgeRow']
        fr[name] = d
    used.discard('.')
    missing = used - set(colors)
    assert not missing, missing
    pal = {k: colors[k] for k in sorted(used | {'k', 'e', 'q'}, key=lambda c: (c not in 'keq', c)) if k in colors}
    d = {'palette': pal, 'unit': 0.5, 'fine': True}
    if extra:
        d.update(extra)
    d['frames'] = fr
    return d


def tuples(fr):
    return {n: {'g': g, 'ax': ax, 'ledgeRow': L} for n, (g, ax, L) in fr.items()}


LOCALES = ['en', 'es_419', 'ko', 'pt_BR', 'zh_CN', 'zh_TW']


def write_locales(entries):
    """_locales/*/messages.json に、キャラクター名(char_<id>)とジャンル名(genre_<ジャンル>)を書く"""
    from i18n_names import NAMES, GENRES as GNAMES
    for loc in ['ja'] + LOCALES:
        path = os.path.join(ROOT, '_locales', loc, 'messages.json')
        old = json.load(open(path, encoding='utf-8'))
        out = {k: v for k, v in old.items() if not k.startswith(('char_', 'genre_'))}
        for cid, label, genre, _ in entries:
            if loc == 'ja':
                msg = label
            elif cid in NAMES:
                msg = NAMES[cid][LOCALES.index(loc)]
            else:
                msg = old['char_' + cid]['message']  # 既存のキャラクター(翻訳済み)
            out['char_' + cid] = {'message': msg}
        for g in GENRES:
            out['genre_' + g] = {'message': GNAMES[g][0 if loc == 'ja' else LOCALES.index(loc) + 1]}
        open(path, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=2) + '\n')


def check(idx):
    """キャラクターを追加したときによくある間違いを、作り直す前に見つける"""
    from i18n_names import NAMES
    errors = []
    tables = [('roster_people.py', PEOPLE), ('roster_vehicles.py', VEHICLES),
              ('roster_creatures.py', CREATURES), ('roster_derived.py', DERIVED)]
    hand = {row[0] for row in idx} - {cid for _, t in tables for cid in t}  # 手描きのキャラクター
    seen = {cid: 'chars/' + cid + '.json' for cid in hand}
    for fname, table in tables:
        for cid, val in table.items():
            if not re.fullmatch(r'[a-z0-9_]+', cid):
                errors.append(f'{fname}: id "{cid}" は英小文字・数字・_ だけにしてください')
            if cid in seen:
                errors.append(f'{fname}: id "{cid}" は {seen[cid]} と重複しています')
            seen[cid] = fname
            genre = 'vehicles' if table is VEHICLES else val[1]
            if genre not in GENRES:
                errors.append(f'{fname}: {cid} のジャンル "{genre}" は {", ".join(GENRES)} のどれかにしてください')
            if cid not in NAMES:
                errors.append(f'i18n_names.py: {cid} の名前の翻訳 (en, es_419, ko, pt_BR, zh_CN, zh_TW) がありません')
            elif len(NAMES[cid]) != len(LOCALES):
                errors.append(f'i18n_names.py: {cid} の翻訳は {len(LOCALES)} 個 (en, es_419, ko, pt_BR, zh_CN, zh_TW) 書いてください')
    for fname, table in tables[3:]:
        for cid, (_, _, base, _) in table.items():
            if base not in seen:
                errors.append(f'{fname}: {cid} の元のキャラクター "{base}" がありません')
    if errors:
        sys.exit('キャラクターの定義に問題があります:\n  ' + '\n  '.join(errors))


def main():
    idx, raw = load_raw()
    check(idx)
    D = {k: json.loads(v) for k, v in raw.items()}
    head = open(CHARS, encoding='utf-8').read()
    head = head[:head.index('window.PW_INDEX')]
    entries = []  # (id, 名前, ジャンル, JSON 文字列)
    for row in idx:
        cid, label = row[0], row[1]
        if cid in PEOPLE or cid in VEHICLES or cid in CREATURES or cid in DERIVED:
            continue  # 生成したもの(作り直す)
        if cid not in raw:
            continue  # 絵データを消したもの(一覧からも外す)
        entries.append((cid, label, OLD_GENRE.get(cid, 'animals'), raw[cid]))
    new = []
    for cid, (label, genre, look) in PEOPLE.items():
        fr, colors = humanoid.frames(look)
        new.append((cid, label, genre, pack(tuples(fr), colors)))
    for cid, (label, genre, base, spec) in DERIVED.items():
        fr, colors = dv.derive(D[base], spec)
        extra = {'swim': D[base]['swim']} if D[base].get('swim') else None
        new.append((cid, label, genre, pack(fr, colors, extra)))
    for table, genre0 in ((VEHICLES, 'vehicles'), (CREATURES, None)):
        for cid, val in table.items():
            if genre0:
                label, spec = val
                genre = genre0
            else:
                label, genre, spec = val
            fr, colors = vehicle.frames(spec)
            extra = {'swim': {'frames': ['walk1', 'walk2'], 'speed': spec.get('speed', 1)}} if spec.get('fly') else None
            new.append((cid, label, genre, pack(tuples(fr), colors, extra)))
    for cid, label, genre, d in new:
        entries.append((cid, label, genre, json.dumps(d, ensure_ascii=False, separators=(',', ':'))))
    # ジャンル順に並べる(同じジャンルの中は元の順)
    order = {g: i for i, g in enumerate(GENRES)}
    entries.sort(key=lambda e: order[e[2]])
    # 絵データ: chars/<id>.json(使う 1 体だけを読み込む)
    os.makedirs(CHAR_DIR, exist_ok=True)
    keep = set()
    total = 0
    for cid, label, genre, s in entries:
        p = os.path.join(CHAR_DIR, cid + '.json')
        open(p, 'w', encoding='utf-8').write(s)
        keep.add(cid + '.json')
        total += len(s.encode())
    for f in os.listdir(CHAR_DIR):
        if f.endswith('.json') and f not in keep:
            os.remove(os.path.join(CHAR_DIR, f))
    # 一覧: chars.js
    head = re.sub(r'// PW_INDEX: .*\n', '// PW_INDEX: [id, 名前, ジャンル] の一覧。絵データは chars/<id>.json (使う 1 体だけ読み込む)。\n', head)
    lines = [head + 'window.PW_INDEX = ' + json.dumps([[e[0], e[1], e[2]] for e in entries], ensure_ascii=False,
                                                       separators=(',', ':')) + ';',
             'window.PW_GENRES = ' + json.dumps(GENRES) + ';']
    open(CHARS, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    write_locales(entries)
    from collections import Counter
    print(len(entries), 'characters', dict(Counter(e[2] for e in entries)))
    print('chars/*.json', round(total / 1024), 'KB in total')


if __name__ == '__main__':
    main()
