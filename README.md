# Pixel Walker（Chrome拡張機能）

https://github.com/user-attachments/assets/b887f71f-f371-447a-83f1-a7f685752090

ドット絵のキャラクターが、いま見ているWebページの見出しや文章を足場にして歩き回る拡張機能です。
文字の行から行へジャンプしたり、段落の端によじ登ったり、ぶら下がって降りたり、座ったり昼寝をしたりします。
飛行機や魚などのキャラクターは、ページの上を自由に飛んだり泳いだりします。

また、プレイヤーのキーボード入力で、キャラクターを直接操作することも可能です。

**無料**で、すべての機能・すべてのキャラクターを使えます。

> **English:** A Chrome extension where a pixel-art character walks around on the headings and text of the page you're viewing — jumping between lines, climbing ledges, sitting and napping — or turn on "Control the character" and move it yourself with the keyboard (←→ to walk, C to jump and double-jump). 196 characters, free, and it never sends the pages you view or your settings anywhere (it only checks for new versions, which you can turn off). Contributions are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).

<img width="1680" height="3712" alt="character-list" src="https://github.com/user-attachments/assets/db395c15-b551-45ff-baba-ffbb23602e23" />

## 特長

- **196種類のキャラクター**を6つのジャンルから選べます
  - 人（会社員・コック・宇宙飛行士・アイドルなど）
  - 動物（イヌ・ネコ・ライオン・パンダなど）
  - 鳥・は虫類（フクロウ・ペンギン・ワニ・カエルなど）
  - 水の生き物（クジラ・イルカ・クラゲ・タコなど）
  - 乗り物（パトカー・新幹線・飛行機・UFOなど）
  - ファンタジー（魔法使い・騎士・ドラゴン・スライムなど）
- キャラクターは**マウスでつまんで好きな場所へ運べます**。離すと、投げた勢いのまま落ちて着地します
  （飛ぶ・泳ぐキャラクターは、離した場所からまた動き出します。ちょんと押すと、その場で小さくはねます）
- 「キャラクターを操作する」をオンにすると、キーボードで動かせます（←→で移動、Cでジャンプ・二段ジャンプなど）
- 大きさは「小・中・大」の3段階
- 日本語・英語・中国語（簡体字/繁体字）・韓国語・スペイン語・ポルトガル語に対応
- ページの操作のじゃまをしません（キャラクターの絵の上以外のクリックは、そのままページに届きます）
- 新しいバージョンが出ると、設定画面に「！」でお知らせします

## インストール

GitHubで配布しています。ダウンロードして、Chromeに読み込みます。

1. [Releases](https://github.com/ItsukiYokoyama/pixel-walker/releases/latest) から `pixel-walker-<バージョン>.zip` をダウンロードし、展開する
2. Chromeで `chrome://extensions` を開き、右上の「デベロッパーモード」をオンにする
3. 「パッケージ化されていない拡張機能を読み込む」を押し、展開してできたフォルダ（`manifest.json` が入っているフォルダ）を選ぶ

### 新しいバージョンへの更新

新しいバージョンが出ると、設定画面の右上に「！」が出ます。リンクから開く
[リリースノートのページ](https://ditsuki.com/pixel-walker/releases)の手順で入れ替えてください。

1. 新しいバージョンの zip をダウンロードし、展開する
2. 展開してできたフォルダの**中身**を、今使っているフォルダ（最初に読み込んだフォルダ）に**上書きでコピー**する
3. `chrome://extensions` で Pixel Walker の「再読み込み」ボタン（丸い矢印）を押す

同じフォルダに上書きすれば、設定（選んだキャラクターなど）はそのまま引き継がれます。

## 使い方

ツールバーの Pixel Walker のアイコンを押すと、設定が開きます。

- **キャラクターを表示**: オン/オフの切り替え
- **サイズ**: 小・中・大
- **キャラクターを操作する**: オンにすると、キャラクターが自分で動くのをやめ、キーボードで動かせます。
  ページを一度クリックしてから操作してください（入力欄で文字を打っているときや、Ctrl・Alt・Cmd と一緒に押したキーには反応しません）

  | キー | 動き |
  |---|---|
  | ← → | 移動（段落の端まで行くと落ちる） |
  | C | ジャンプ（← → を押しながらだと、その向きへ。空中でもう一度押すと二段ジャンプ） |
  | ↓ + C | 今いる段落から下へ降りる |
  | X | アクション（寝る・座る・踊るのどれか。← → で中断） |

  飛ぶ・泳ぐキャラクター（飛行機・魚など）は、↑ ↓ ← → で好きな方向へ動かせます（段落や画像は通り抜けず、縁に沿って進みます）
- **キャラクター**: 上のタブでジャンルを選び、好きなキャラクターを押すとすぐに切り替わります
- **新しいバージョンを確認する**: オフにすると、新しいバージョンの確認（下の「プライバシー」参照）をしません

設定は自動で保存されます。Chromeの同期がオンなら、同じGoogleアカウントの他の端末にも引き継がれます。

## プライバシー

**見ているページの内容も設定も、開発者を含め、どこにも送信しません。**

外部と通信するのは、新しいバージョンの確認だけです。

- 設定画面を開いたとき（1日1回まで）に、`https://ditsuki.com/pixel-walker/latest.json`（最新のバージョン番号だけが
  書かれた公開ファイル）を読み込みます。サイトに届くのは、ふつうにWebページを開いたときと同じ情報（IPアドレス・
  ブラウザの種類など）だけです。設定画面の「新しいバージョンを確認する」をオフにすると、この確認もしません
- キャラクターが歩ける場所を決めるために、ページ上の文字や画像の「位置」をブラウザの中で計算しますが、
  ページの内容を保存したり送ったりはしません
- 設定（表示のオン/オフ・サイズ・選んだキャラクター）は `chrome.storage.sync` に保存されます
- 必要な権限は `storage`（設定の保存）だけです。キャラクターを表示するために全ページで動きます

## 要望・お問い合わせ

「こんなキャラクターがほしい」などの要望は、設定画面の下の「キャラクターの要望・お問い合わせ」か、
[お問い合わせページ](https://ditsuki.com/contact?product=pixel-walker)からお送りください。
リンクを押したときにお問い合わせページが開くだけで、拡張機能から何かが送信されることはありません。

---

## 開発者向け

ビルド不要の素のJavaScriptです。

```
pixel-walker/
├── manifest.json
├── content.js      # 全ページで動く本体。キャラクターの動き・描画
├── background.js   # service worker。content.jsに頼まれて chars/<id>.json を読んで返すだけ
├── characters.js   # 絵データを読み込み、描画用の格子・パレットに変換する
├── chars.js        # キャラクターの一覧（id・名前・ジャンル）。自動生成
├── chars/<id>.json # キャラクター1体ぶんの絵データ。自動生成
├── popup.html / popup.js   # 設定画面（表示のオン/オフ・サイズ・ジャンル別のキャラクター選択）
├── update-check.js # 新しいバージョンの確認（設定画面を開いたときに、1日1回まで ditsuki.com の latest.json を読む）
├── _locales/       # 7言語の文言
├── icons/          # 16/48/128px
├── docs/           # README用の画像
├── character-list.html / .js  # 全キャラクターの待機ポーズの一覧（確認用。開くたびに最新の絵データで描く）
├── tools/          # 絵データの生成スクリプト（Python。拡張機能の動作には不要）
├── .github/        # プルリクエストの自動チェック、Issue・プルリクエストのテンプレート
├── CONTRIBUTING.md # コントリビューションガイド（キャラクターの追加手順）
└── LICENSE         # GPL-3.0
```

ページに読み込むのはキャラクターの一覧（`chars.js`、約7KB）だけで、絵データは表示する1体ぶんだけを
`background.js` 経由で読み込みます（拡張機能の中のファイルを読むだけで、外部とは通信しません）。

### キャラクターの絵データ（tools/）

`python3 tools/build.py` で `chars.js`・`chars/*.json`・`_locales/*/messages.json` のキャラクター名を、`tools/` の
元データからすべて作り直します（Python 3の標準ライブラリだけで動きます）。

- `roster_sprites.py` + `sprites/<id>.json`: ドット絵の元データ（1 文字 = 1 ドットの方眼紙）から作るキャラクター。
  最初からいた68体（冒険家と動物たち）はこの形
- `roster_people.py`: 人・ファンタジーの人型。骨組みのポーズ×見た目（髪・帽子・服・持ち物）から描く（`humanoid.py`）。
  人型は冒険家も含めて、歩きは4枚（踏み出す→脚を交差→反対の脚で踏み出す→交差）
- `roster_vehicles.py` / `roster_creatures.py`: 乗り物・スライムや魚など。部品を描き、傾けてポーズにする（`vehicle.py`）
- `roster_derived.py`: 既存の動物の色替え・模様・角や翼の追加（`derive.py`）
- `i18n_names.py`: キャラクター名・ジャンル名の翻訳
- `preview.py`: 指定したキャラクターの全ポーズを並べた確認用の画像（`preview/<id>.png`）を作る
- `make_zip.py`: 配布用の zip（`dist/pixel-walker-<バージョン>.zip`）を作る（リリースの手順は CONTRIBUTING.md）
- `docs_image.py`: READMEの画像 `docs/characters.png`（ジャンルごとに先頭16体の待機ポーズ）を作り直す。
  `build.py` のあとに `python3 tools/docs_image.py` を実行する

キャラクターの追加手順は [CONTRIBUTING.md](CONTRIBUTING.md) にまとめています。
プルリクエストでは、GitHub Actions（`.github/workflows/check.yml`）が、生成されたファイルの作り直し忘れや
JavaScript・JSON の壊れを自動で確かめます。

全キャラクターの一覧は、拡張機能を読み込んだ状態で `chrome-extension://<拡張機能のID>/character-list.html` を開くと見られます。

### 既知の制約

- 飛ぶ・泳ぐキャラクター（飛行機・魚など）は、待機と2枚の動きの絵だけを持ち、他のポーズは待機の絵で代用する
- 動作確認はヘッドレスのEdge（Chromium）で、全キャラクターの読み込み・描画、ページ上での表示、設定画面の
  タブ表示まで。実際のChromeでの長時間の操作確認は未実施

## コントリビュート / Contributing

キャラクターの追加・動きの改善・翻訳・不具合の修正など、プルリクエストを歓迎します。
手順は [CONTRIBUTING.md](CONTRIBUTING.md) を見てください。キャラクターの要望や不具合の報告は [Issues](https://github.com/ItsukiYokoyama/pixel-walker/issues) へどうぞ。

## ライセンス / License

[GPL-3.0](LICENSE)

---

# Pixel Walker (English)

A Chrome extension where a pixel-art character walks around using the headings and text of the web page you're viewing as platforms.
It jumps from line to line, climbs up the edges of paragraphs, hangs and drops down, sits, and takes naps.
Characters such as airplanes and fish fly or swim freely over the page.

You can also control the character directly with your keyboard.

It's **free**, and every feature and every character is available to everyone.

## Features

- Choose from **196 characters** in 6 genres
  - People (office worker, chef, astronaut, idol, ...)
  - Animals (dog, cat, lion, panda, ...)
  - Birds & reptiles (owl, penguin, crocodile, frog, ...)
  - Sea life (whale, dolphin, jellyfish, octopus, ...)
  - Vehicles (police car, bullet train, airplane, UFO, ...)
  - Fantasy (wizard, knight, dragon, slime, ...)
- **Pick the character up with your mouse and carry it anywhere.** Let go and it flies off with the momentum of your throw, then lands
  (flying and swimming characters start moving again from where you dropped them; a quick tap makes the character hop in place)
- Turn on "Control the character" to move it with the keyboard (←→ to walk, C to jump and double-jump, and more)
- Three sizes: small, medium, large
- Available in Japanese, English, Chinese (Simplified/Traditional), Korean, Spanish, and Portuguese
- Stays out of your way (clicks anywhere except on the character itself go straight through to the page)
- Shows a "!" in the settings window when a new version is released

## Installation

Pixel Walker is distributed on GitHub. Download it and load it into Chrome.

1. Download `pixel-walker-<version>.zip` from [Releases](https://github.com/ItsukiYokoyama/pixel-walker/releases/latest) and extract it
2. Open `chrome://extensions` in Chrome and turn on "Developer mode" in the top right
3. Click "Load unpacked" and choose the extracted folder (the folder that contains `manifest.json`)

### Updating to a new version

When a new version is released, a "!" appears in the top right of the settings window. Follow the steps on the
[release notes page](https://ditsuki.com/en/pixel-walker/releases) it links to.

1. Download the zip of the new version and extract it
2. **Copy the contents** of the extracted folder **over** the folder you are using now (the folder you loaded first)
3. On `chrome://extensions`, press the reload button (circular arrow) for Pixel Walker

If you overwrite the same folder, your settings (such as the character you chose) are kept.

## Usage

Click the Pixel Walker icon in the toolbar to open the settings.

- **Show character**: turn the character on or off
- **Size**: small, medium, large
- **Control the character**: when on, the character stops moving on its own and you move it with the keyboard.
  Click the page once before using the keys (it ignores typing in input fields and keys pressed with Ctrl, Alt, or Cmd)

  | Key | Action |
  |---|---|
  | ← → | Walk (falls off at the edge of a paragraph) |
  | C | Jump (toward ← or → if held; press again in the air to double-jump) |
  | ↓ + C | Drop down from the current paragraph |
  | X | Action (sleep, sit, or dance; ← → cancels it) |

  Flying and swimming characters (airplanes, fish, ...) move freely with ↑ ↓ ← → (they don't pass through paragraphs or images; they slide along their edges)
- **Character**: choose a genre with the tabs at the top, then click a character to switch to it right away
- **Check for new versions**: when off, the extension doesn't check for new versions (see "Privacy" below)

Settings are saved automatically. If Chrome Sync is on, they carry over to your other devices signed in to the same Google account.

## Privacy

**Neither the content of the pages you view nor your settings are sent anywhere, including to the developer.**

The only network access is the check for new versions.

- When you open the settings window (at most once a day), it reads `https://ditsuki.com/pixel-walker/latest.json` (a public file
  containing only the latest version number). The site receives only the same information as any ordinary web page visit
  (such as your IP address and browser type). Turn off "Check for new versions" in the settings window to skip this check
- To decide where the character can walk, it calculates the "positions" of text and images on the page inside your browser,
  but it never saves or sends the page's content
- Settings (on/off, size, chosen character) are stored in `chrome.storage.sync`
- The only permission it needs is `storage` (to save settings). It runs on every page in order to show the character

## Requests and contact

Send requests such as "I'd like this character" from "Request a character / Contact" at the bottom of the settings window,
or from the [contact page](https://ditsuki.com/en/contact?product=pixel-walker).
The link only opens the contact page; the extension itself never sends anything.

---

## For developers

Plain JavaScript with no build step.

```
pixel-walker/
├── manifest.json
├── content.js      # Runs on every page. The character's movement and drawing
├── background.js   # Service worker. Only reads chars/<id>.json for content.js
├── characters.js   # Loads character data and turns it into pixel grids and palettes for drawing
├── chars.js        # List of characters (id, name, genre). Generated
├── chars/<id>.json # Image data for one character. Generated
├── popup.html / popup.js   # Settings window (on/off, size, character selection by genre)
├── update-check.js # New version check (reads latest.json on ditsuki.com at most once a day when the settings window opens)
├── _locales/       # Text in 7 languages
├── icons/          # 16/48/128px
├── docs/           # Images for the README
├── character-list.html / .js  # Idle poses of all characters (for checking; always drawn from the latest data)
├── tools/          # Scripts that generate the character data (Python; not needed to run the extension)
├── .github/        # Pull request checks, issue and pull request templates
├── CONTRIBUTING.md # Contribution guide (how to add characters)
└── LICENSE         # GPL-3.0
```

Only the character list (`chars.js`, about 7 KB) is loaded into each page; the image data is loaded through
`background.js` for the one character being shown (it only reads files inside the extension and never talks to any server).

### Character data (tools/)

`python3 tools/build.py` rebuilds `chars.js`, `chars/*.json`, and the character names in `_locales/*/messages.json`
entirely from the source data in `tools/` (it needs only the Python 3 standard library).

- `roster_sprites.py` + `sprites/<id>.json`: characters built from pixel-art source data (a grid with one character per pixel).
  The original 68 characters (the adventurer and the animals) use this form
- `roster_people.py`: people and humanoid fantasy characters, drawn from skeleton poses × looks (hair, hats, clothes, items) (`humanoid.py`).
  All humanoids, including the adventurer, walk with 4 frames (step → legs cross → step with the other leg → legs cross)
- `roster_vehicles.py` / `roster_creatures.py`: vehicles, slimes, fish, and so on, drawn from parts and tilted into poses (`vehicle.py`)
- `roster_derived.py`: recolors, patterns, and added horns or wings for existing animals (`derive.py`)
- `i18n_names.py`: translations of character and genre names
- `preview.py`: creates an image of every pose of the given character (`preview/<id>.png`) for checking
- `make_zip.py`: creates the zip for distribution (`dist/pixel-walker-<version>.zip`) (see CONTRIBUTING.md for the release steps)
- `docs_image.py`: rebuilds the README image `docs/characters.png` (idle poses of the first 16 characters of each genre).
  Run `python3 tools/docs_image.py` after `build.py`

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add characters.
On pull requests, GitHub Actions (`.github/workflows/check.yml`) checks for generated files that weren't rebuilt and for broken
JavaScript or JSON.

With the extension loaded, open `chrome-extension://<extension id>/character-list.html` to see every character.

### Known limitations

- Flying and swimming characters (airplanes, fish, ...) have only an idle pose and two movement frames; other poses use the idle image
- Testing has been done in headless Edge (Chromium): loading and drawing every character, showing them on pages, and the tabs in the
  settings window. Long-term hands-on testing in real Chrome hasn't been done yet
