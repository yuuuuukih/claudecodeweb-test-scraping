# ソフトバンク店舗情報スクレイパー

このプロジェクトは、ソフトバンクの店舗検索サイトから全国の店舗情報を収集するスクレイピングツールです。

## 機能

- 全国47都道府県の全地方公共団体コードを自動的に走査
- 各店舗の以下の情報を収集：
  - 店舗名
  - 運営会社
  - 住所
  - 電話番号
  - 都道府県
  - 詳細ページURL
- 収集した情報をCSVファイルに保存
- 進捗状況のログ出力
- 定期的な中間保存（50件ごと）

## ファイル構成

```
├── selenium_scraper.py       # メインスクレイパー（Selenium使用）
├── softbank_shop_scraper.py  # 代替スクレイパー（requests使用）
├── test_page_structure.py    # ページ構造確認用テストスクリプト
├── prefecture_codes.py       # 都道府県コード定義
├── requirements.txt          # 必要なPythonパッケージ
├── docker-compose.yml        # Docker環境設定
└── README.md                 # このファイル
```

## セットアップ方法

### 方法1: ローカル環境での実行（推奨）

#### 前提条件

- Python 3.8以上
- Google Chrome または Chromium ブラウザ

#### インストール手順

1. リポジトリをクローン

```bash
git clone <repository-url>
cd claudecodeweb-test-scraping
```

2. 仮想環境を作成（推奨）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows
```

3. 必要なパッケージをインストール

```bash
pip install -r requirements.txt
```

4. ChromeDriverのインストール確認

webdriver-managerが自動的にChromeDriverをダウンロードしますが、事前にChromeブラウザがインストールされている必要があります。

- **Windows/Mac**: [Google Chrome](https://www.google.com/chrome/)をダウンロードしてインストール
- **Linux**:
  ```bash
  # Ubuntu/Debian
  sudo apt-get update
  sudo apt-get install chromium-browser

  # または
  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  sudo dpkg -i google-chrome-stable_current_amd64.deb
  sudo apt-get install -f
  ```

### 方法2: Docker環境での実行

Docker Composeを使用してSelenium環境を構築できます。

1. docker-compose.ymlを使用してコンテナを起動

```bash
docker-compose up -d
```

2. コンテナ内でスクリプトを実行

```bash
docker-compose exec scraper python selenium_scraper.py
```

## 使用方法

### 基本的な使用方法

```bash
# 全国のすべての店舗を収集（ヘッドレスモード）
python selenium_scraper.py

# テストモード（最初の都道府県のみ）
python selenium_scraper.py --test

# ブラウザを表示して実行
python selenium_scraper.py --no-headless
```

### オプション

- `--test`: テストモード。最初の都道府県（北海道）のみを処理します
- `--no-headless`: ブラウザウィンドウを表示して実行します（デバッグ用）

### 実行例

```bash
# テストモードで動作確認
python selenium_scraper.py --test

# 本番実行（全都道府県）
python selenium_scraper.py
```

## 出力ファイル

スクリプトは以下のファイルを生成します：

- `softbank_shops_final.csv`: 最終的な全店舗情報
- `softbank_shops_progress.csv`: 進捗中の中間データ（50件ごとに更新）
- `scraper.log`: 実行ログ

### CSVファイルの形式

| 列名 | 説明 |
|------|------|
| 店舗名 | 店舗の名称 |
| 運営会社 | 店舗を運営する会社名 |
| 住所 | 店舗の住所 |
| 電話番号 | 店舗の電話番号 |
| 都道府県 | 店舗が所在する都道府県 |
| 詳細ページURL | 店舗詳細ページのURL |

## パフォーマンスと注意事項

### 実行時間

- テストモード（1都道府県）: 約10-30分
- 全都道府県モード: 数時間～1日程度（店舗数と通信速度により変動）

### レート制限

サーバーへの負荷を軽減するため、以下の対策を実装しています：

- リクエスト間に2秒の遅延
- 重複URLのスキップ
- 定期的な中間保存

### エラーハンドリング

- ネットワークエラーやタイムアウトは自動的にログに記録
- 一部のページでエラーが発生しても処理は継続
- 進捗状況は定期的に保存されるため、中断しても再開可能

## トラブルシューティング

### ChromeDriverのエラー

```
WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

**解決方法**:
- Chromeブラウザがインストールされているか確認
- webdriver-managerの再インストール: `pip install --upgrade webdriver-manager`

### 403 Forbiddenエラー

```
403 Client Error: Forbidden
```

**原因**: サイト側がボット検出を行っている可能性があります。

**解決方法**:
- `--no-headless`オプションを使用してブラウザを表示
- `delay`の値を増やす（selenium_scraper.pyの`self.delay`を編集）
- VPNや異なるIPアドレスを使用

### メモリ不足

長時間実行時にメモリ不足になる場合：

1. 定期的にスクリプトを再起動
2. 既に収集済みの都道府県をスキップするよう修正
3. より強力なマシンで実行

## 開発者向け情報

### ページ構造の確認

新しいサイト構造を確認する場合：

```bash
python test_page_structure.py
```

これにより、以下のHTMLサンプルファイルが生成されます：
- `search_page_sample.html`
- `list_page_sample.html`
- `detail_page_sample.html`

### カスタマイズ

#### 遅延時間の変更

`selenium_scraper.py`の`__init__`メソッド内：

```python
self.delay = 2.0  # 秒単位で変更
```

#### 保存頻度の変更

`scrape_all_shops`メソッド内：

```python
if len(all_shops) > 0 and len(all_shops) % 50 == 0:  # 50を変更
```

#### ログレベルの変更

ファイルの先頭付近：

```python
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR から選択
    ...
)
```

## 法的・倫理的注意事項

このツールを使用する前に、以下を確認してください：

1. **利用規約の確認**: ソフトバンクのWebサイトの利用規約を確認し、自動アクセスが許可されているか確認してください

2. **robots.txtの遵守**: サイトのrobots.txtに従ってください

3. **サーバー負荷**: 適切なレート制限を設定し、サーバーに過度な負荷をかけないようにしてください

4. **データの使用**: 収集したデータの使用目的が法的に問題ないか確認してください

5. **個人情報**: 収集したデータに個人情報が含まれる場合、適切に管理してください

## ライセンス

このプロジェクトは教育目的で作成されています。実際の使用にあたっては、関連法規と利用規約を遵守してください。

## トラブルや質問

問題が発生した場合は、以下を確認してください：

1. `scraper.log`ファイルでエラーメッセージを確認
2. Chromeブラウザのバージョンが最新か確認
3. インターネット接続が安定しているか確認
4. 十分なディスク容量があるか確認

## 更新履歴

- 2025-10: 初版リリース
  - Selenium ベースのスクレイパー実装
  - 全都道府県対応
  - CSV出力機能
  - 進捗保存機能
