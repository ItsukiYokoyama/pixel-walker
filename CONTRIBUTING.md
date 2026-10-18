# コントリビューションガイド / Contributing

Pixel Walker へのコントリビューションを歓迎します。キャラクターの追加、動きの改善、翻訳、不具合の修正など、どれも大歓迎です。

*English follows the Japanese section → [English](#english)*

---

## 日本語

### 必要なもの

- Chrome（動作確認用）
- Python 3.10 以上（キャラクターの絵データを作るときだけ。標準ライブラリだけで動き、追加のインストールは不要）

拡張機能そのものはビルド不要の素の JavaScript です。リポジトリのフォルダを `chrome://extensions` →「デベロッパーモード」→「パッケージ化されていない拡張機能を読み込む」で読み込めば、そのまま動きます。ファイルを変えたら、`chrome://extensions` で Pixel Walker の再読み込みボタンを押してください。

### 開発の流れ

1. リポジトリを fork し、作業用のブランチを作る
2. 変更する（キャラクターの追加は下の「キャラクターを追加する」を参照）
3. キャラクターの絵データに関わる変更をしたら、`python3 tools/build.py` を実行する
4. Chrome に読み込んで動きを確かめる
5. 生成されたファイル（`chars/`・`chars.js`・`_locales/`）も含めてコミットし、プルリクエストを送る

プルリクエストでは、GitHub Actions が「絵データの作り直し忘れ」「JavaScript と JSON の壊れ」を自動で確かめます。

### キャラクターを追加する

キャラクターは Python の設定から自動で描きます。種類に合わせて、次のどれか 1 つのファイルに 1 行（1 項目）足します。

| 作りたいもの | 書くファイル | 例 |
|---|---|---|
| 人・人型のファンタジー（魔法使いなど） | `tools/roster_people.py` | `boy`, `wizard`, `angel` |
| 部品で描く生き物（魚・スライムなど） | `tools/roster_creatures.py` | `goldfish`, `slime` |
| 乗り物 | `tools/roster_vehicles.py` | `car`, `airplane` |
| 既存のキャラクターの色違い・角や翼の追加 | `tools/roster_derived.py` | `blackcat`, `unicorn` |

**id**（`'boy'` の部分）は英小文字・数字・`_` だけで、ほかのキャラクターと重ならないものにします。**ジャンル**は `people` / `animals` / `birds` / `sea` / `vehicles` / `fantasy` のどれかです（乗り物は書かなくてよい）。

#### 人型（`roster_people.py`）

`id: (日本語名, ジャンル, 見た目)` の形です。見た目は、骨組みに着せる服や髪型の設定で、書かなかった項目は標準の値になります。

```python
'wizard': ('魔法使い', 'fantasy', dict(hat='wizard', hat_col='#4a3a9a', hat_col2='#e0c040', robe={'col': '#4a3a9a'},
                                     sleeve='long', shirt='#4a3a9a', beard='#e8e8e8', hair='#e8e8e8', item='staff',
                                     item_col='#60d0ff')),
```

主な項目（すべての項目と標準の値は `tools/humanoid.py` の `Look.DEF`）:

| 項目 | 内容 | 使える値 |
|---|---|---|
| `skin` / `hair` / `shirt` / `pants` / `shoes` | 肌・髪・服・ズボン・靴の色 | `'#rrggbb'` |
| `hair_style` | 髪型 | `short`（標準）, `side`, `bob`, `long`, `twin`, `pony`, `braid`, `bun`, `spiky`, `afro`, `mohawk` |
| `hat` / `hat_col` / `hat_col2` | 帽子・かぶりものと、その色 | `cap`, `beret`, `bandana`, `headband`, `bow`, `flower`, `leaf`, `crown`, `halo`, `horns`, `antenna`, `antennae`, `cat_hood`, `hood`, `chef`, `nurse`, `police`, `fire`, `hardhat`, `helmet`, `astro`, `knight`, `ninja`, `pirate`, `sailor`, `santa`, `straw`, `cowboy`, `tophat`, `grad`, `witch`, `wizard` |
| `sleeve` | 袖 | `short`（標準）, `long`, `none` |
| `skirt` / `robe` / `cape` / `coat` | スカート・ローブ・マント・上着 | 色（`robe` は `{'col': '#rrggbb'}`） |
| `eyes` | 目 | `normal`（標準）, `big`, `closed`, `glow`, `alien`, `sockets`, `visor` |
| `item` / `item_col` | 手に持つもの | `sword`, `staff`, `wand`, `broom`, `trident`, `scythe`, `flag`, `lantern`, `mic`, `pan`, `brush`, `bat`, `ball`, `stick` |
| `wings` / `tail` | 翼・しっぽ | `{'col': '#rrggbb', 'kind': ...}`（翼は `feather`, `bat`, `fairy`、しっぽは `devil`, `cat`, `fluffy`） |
| `glasses` / `beard` / `tie` / `scarf` | めがね・ひげ・ネクタイ・マフラー | 色 |

歩き・ジャンプ・よじ登りなど 14 枚のポーズは自動で作られます。

#### 部品で描く生き物・乗り物（`roster_creatures.py` / `roster_vehicles.py`）

横から見た絵を、多角形・楕円・角の丸い四角などの部品で描きます。座標は「右が前、下が +、地面が y = 0、中心が x = 0」です。

```python
'slime': ('スライム', 'fantasy', dict(len=20, h=16, parts=[
    ('step', 0, ('poly', [(-9, 0), (-9, -5), (-5, -11), (0, -16), (2, -12), (6, -10), (9, -5), (9, 0)], '#4a90e8')),
    ('step', 1, ('poly', [(-10, 0), (-10, -4), (-6, -9), (0, -13), (2, -10), (7, -8), (10, -4), (10, 0)], '#4a90e8')),
    ('ellipse', -4, -8, 1.6, 1.2, '#c8e4ff', False),
    ('eye', 0, -8, True), ('eye', 4, -8, True), ('dot', 3, -4, '#2a3a6a')])),
```

- `len` / `h`: 全体の長さと高さ。`parts`: 奥から順に描く部品
- 部品: `poly`（多角形）, `ellipse`, `rrect`（角の丸い四角）, `capsule`, `dot`, `eye`, `window`（窓）, `light`（ライト）, `blink`, `flame`, `rotor`, `prop` など（`tools/vehicle.py` の `draw`）
- `('step', 0, 部品)` / `('step', 1, 部品)`: 歩きの 1 枚目・2 枚目だけに描く部品（足や尾びれの動き）
- `fly=True` と `speed`: 地面を歩かず、画面を飛ぶ・泳ぐ
- 乗り物は `wheels=[(x, 半径), ...]` で車輪を付けられる。`roster_vehicles.py` の `car()` などの関数も使える

似たキャラクターをコピーして、少しずつ変えるのが近道です。

#### 色違い・角や翼の追加（`roster_derived.py`）

手描きの動物をもとに、色を置き換えたり部品を足したりします。

```python
'unicorn': ('ユニコーン', 'fantasy', 'horse', dict(maps={'main': '#f6f4f8', 'b': '#c8a0f0', 'c': '#fbf8ff'},
                                                 outline='#5a4a6a', parts=[horn('#f8d860')])),
```

`id: (日本語名, ジャンル, もとのキャラクター, 設定)` の形です。`maps` は色のグループの置き換え、`outline` は輪郭の色、`spots` は模様、`parts` は `horn` / `horns2` / `wings` などの部品です（`tools/derive.py`）。

#### 名前を翻訳する（`tools/i18n_names.py`）

日本語以外の 6 言語の名前を、`NAMES` に `(英語, スペイン語, 韓国語, ポルトガル語, 簡体字, 繁体字)` の順で足します。

```python
'wizard': ('Wizard', 'Mago', '마법사', 'Mago', '魔法师', '魔法師'),
```

#### 作って確かめる

```sh
python3 tools/build.py          # chars/・chars.js・_locales/ を作り直す（定義の間違いがあれば、ここで教えてくれる）
python3 tools/preview.py <id>   # preview/<id>.png に全ポーズを並べた画像を作る（プルリクエストに貼ってください）
```

Chrome に読み込み直し、ポップアップで選んで、歩く・ジャンプ・よじ登る・座る・寝るを確かめてください。全キャラクターの一覧は `chrome-extension://<拡張機能のID>/character-list.html` で見られます。

ジャンルの先頭 16 体に入るキャラクターを変えたときは、README の画像も `python3 tools/docs_image.py` で作り直してください。

#### 受け付けられないキャラクター

アニメ・ゲーム・映画など**既存の作品のキャラクター**や、実在の人物・ブランドのロゴは、著作権・商標の都合で受け付けられません。オリジナルのキャラクターでお願いします。

### コードについて

- 既存のコードの書き方（名前の付け方・コメントの量・日本語のコメント）に合わせてください
- 手描きの 68 体（冒険家と最初の動物たち）の絵データは `chars/<id>.json` にしかありません。直すときはこのファイルを直接編集してください（`build.py` はそのまま残します）
- 外部と通信するコード（今は `update-check.js` の新しいバージョンの確認だけ）や、新しい権限（`manifest.json` の `permissions`）が必要な変更は、先に Issue で相談してください

### リリースの手順（メンテナー向け）

GitHub でリリースを作ると、[ditsuki.com のリリースノートのページ](https://ditsuki.com/pixel-walker/releases)と、
拡張機能の「新しいバージョンがあります」のお知らせ（`https://ditsuki.com/pixel-walker/latest.json`）に自動で反映されます
（サイトは GitHub の Releases を 10 分ほどキャッシュして読む。拡張機能は設定画面を開いたときに 1 日 1 回まで確認する）。

1. `manifest.json` の `version` を上げる（`1.2.3` の形）
2. コミットして push し、GitHub Actions のチェックが通るのを確かめる
3. `python3 tools/make_zip.py` で `dist/pixel-walker-<バージョン>.zip` を作る
4. [`docs/release-template.md`](docs/release-template.md) をもとにリリースノートを書く（前の版からの変更点と、短い更新のしかただけ。インストール方法は README に任せる）
5. `gh release create v<バージョン> dist/pixel-walker-<バージョン>.zip --title "Pixel Walker v<バージョン>" --notes-file <リリースノート>`

### ライセンス

送っていただいた変更は、このリポジトリと同じ [GPL-3.0](LICENSE) で公開されます。

---

## English

Contributions are welcome: new characters, better animations, translations, bug fixes.

### Requirements

- Chrome, to test the extension
- Python 3.10+, only for building character data (standard library only, nothing to install)

The extension itself is plain JavaScript with no build step. Load the repository folder from `chrome://extensions` → "Developer mode" → "Load unpacked". After changing files, press the reload button for Pixel Walker on `chrome://extensions`.

### Workflow

1. Fork the repository and create a branch
2. Make your changes (see "Adding a character" below)
3. If you changed character data, run `python3 tools/build.py`
4. Load it in Chrome and check how it moves
5. Commit, including the generated files (`chars/`, `chars.js`, `_locales/`), and open a pull request

GitHub Actions checks every pull request for out-of-date generated files and broken JavaScript or JSON.

### Adding a character

Characters are drawn automatically from Python definitions. Add one entry to one of these files:

| What | File | Examples |
|---|---|---|
| People and humanoid fantasy characters | `tools/roster_people.py` | `boy`, `wizard`, `angel` |
| Creatures drawn from shapes (fish, slimes, ...) | `tools/roster_creatures.py` | `goldfish`, `slime` |
| Vehicles | `tools/roster_vehicles.py` | `car`, `airplane` |
| Recolors of existing characters, or adding horns/wings | `tools/roster_derived.py` | `blackcat`, `unicorn` |

- The **id** must use only lowercase letters, digits and `_`, and be unique. The **genre** is one of `people`, `animals`, `birds`, `sea`, `vehicles`, `fantasy` (not needed for vehicles).
- **Humanoids**: `id: (Japanese name, genre, look)`. The look sets clothes, hair, hats, items and so on; all options and defaults are in `Look.DEF` in `tools/humanoid.py` (see the table in the Japanese section for the supported values). All 14 poses are generated automatically.
- **Creatures and vehicles**: drawn from shapes (`poly`, `ellipse`, `rrect`, `eye`, `window`, ...) in side view; x = forward, y = down, ground at y = 0. `('step', 0|1, shape)` draws a shape only in walk frame 1 or 2. `fly=True` makes it fly or swim instead of walking. See `draw` in `tools/vehicle.py`. Copying a similar character and changing it is the easiest way.
- **Derived characters**: `id: (Japanese name, genre, base character, settings)` with color `maps`, `outline`, `spots`, and `parts` such as `horn`, `horns2`, `wings` (`tools/derive.py`).
- **Names**: add the name in 6 more languages to `NAMES` in `tools/i18n_names.py`, in the order (English, Spanish, Korean, Portuguese, Simplified Chinese, Traditional Chinese). The Japanese name goes in the roster file.

Then build and check:

```sh
python3 tools/build.py          # rebuilds chars/, chars.js, _locales/ (and reports mistakes in definitions)
python3 tools/preview.py <id>   # writes preview/<id>.png with every pose; please attach it to your pull request
```

Reload the extension in Chrome, pick the character in the popup, and check walking, jumping, climbing, sitting and sleeping. `chrome-extension://<extension id>/character-list.html` shows every character. If you change the first 16 characters of a genre, also rebuild the README image with `python3 tools/docs_image.py`.

**Characters from existing works** (anime, games, movies, ...), real people, and brand logos can't be accepted for copyright and trademark reasons. Please make original characters.

### Code

- Follow the style of the surrounding code (naming, comment density, Japanese comments)
- The 68 hand-drawn characters exist only as `chars/<id>.json`; edit those files directly (`build.py` keeps them as they are)
- Please open an issue first for changes that need network access (currently only the version check in `update-check.js`) or new permissions in `manifest.json`

### Releasing (maintainers)

Creating a GitHub release automatically updates the [release notes page on ditsuki.com](https://ditsuki.com/en/pixel-walker/releases)
and the extension's "new version available" notice (`https://ditsuki.com/pixel-walker/latest.json`).

1. Bump `version` in `manifest.json`
2. Commit, push, and make sure the GitHub Actions check passes
3. Run `python3 tools/make_zip.py` to create `dist/pixel-walker-<version>.zip`
4. Write the release notes from [`docs/release-template.md`](docs/release-template.md) (only the changes since the previous version and the short update steps; installation is covered by the README)
5. `gh release create v<version> dist/pixel-walker-<version>.zip --title "Pixel Walker v<version>" --notes-file <notes>`

### License

Your contributions are published under [GPL-3.0](LICENSE), the same license as this repository.
