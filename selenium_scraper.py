#!/usr/bin/env python3
"""
ソフトバンク店舗情報スクレイパー (Selenium版)
Seleniumを使用してブラウザを操作し、全国のソフトバンク店舗情報を収集します
"""

import time
import logging
import json
import re
from typing import List, Dict, Optional, Set
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
import pandas as pd

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 都道府県コードマッピング
PREFECTURES = {
    "01": "北海道", "02": "青森県", "03": "岩手県", "04": "宮城県",
    "05": "秋田県", "06": "山形県", "07": "福島県", "08": "茨城県",
    "09": "栃木県", "10": "群馬県", "11": "埼玉県", "12": "千葉県",
    "13": "東京都", "14": "神奈川県", "15": "新潟県", "16": "富山県",
    "17": "石川県", "18": "福井県", "19": "山梨県", "20": "長野県",
    "21": "岐阜県", "22": "静岡県", "23": "愛知県", "24": "三重県",
    "25": "滋賀県", "26": "京都府", "27": "大阪府", "28": "兵庫県",
    "29": "奈良県", "30": "和歌山県", "31": "鳥取県", "32": "島根県",
    "33": "岡山県", "34": "広島県", "35": "山口県", "36": "徳島県",
    "37": "香川県", "38": "愛媛県", "39": "高知県", "40": "福岡県",
    "41": "佐賀県", "42": "長崎県", "43": "熊本県", "44": "大分県",
    "45": "宮崎県", "46": "鹿児島県", "47": "沖縄県",
}


class SoftBankSeleniumScraper:
    def __init__(self, headless: bool = True):
        """
        初期化

        Args:
            headless: ヘッドレスモードで実行するか
        """
        self.base_url = "https://www.softbank.jp"
        self.driver = None
        self.headless = headless
        self.delay = 2.0  # ページ遷移間の遅延（秒）
        self.visited_urls: Set[str] = set()  # 重複チェック用

    def setup_driver(self):
        """Chromeドライバーをセットアップ"""
        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument('--headless')

            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # 自動化検出を回避
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info("Chromeドライバーのセットアップ完了")

        except Exception as e:
            logger.error(f"ドライバーセットアップエラー: {e}")
            raise

    def get_area_codes_from_search_page(self, pref_code: str) -> List[str]:
        """
        検索ページから指定都道府県の地方公共団体コードを取得

        Args:
            pref_code: 都道府県コード

        Returns:
            地方公共団体コードのリスト
        """
        url = f"{self.base_url}/shop/search/"
        area_codes = []

        try:
            logger.info(f"検索ページから地方公共団体コードを取得中: {url}")
            self.driver.get(url)
            time.sleep(self.delay)

            # ページのHTMLを取得
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # 方法1: セレクトボックスから取得
            selects = soup.find_all('select')
            for select in selects:
                name = select.get('name', '')
                if 'area' in name.lower() or 'city' in name.lower():
                    options = select.find_all('option')
                    for opt in options:
                        value = opt.get('value', '')
                        if value and value.startswith(pref_code):
                            area_codes.append(value)

            # 方法2: JavaScriptから抽出
            if not area_codes:
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        # エリアコードのパターンを検索
                        matches = re.findall(rf'{pref_code}\d{{3,}}', script.string)
                        area_codes.extend(matches)

            # 方法3: ページ内のリンクから抽出
            if not area_codes:
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    if 'area=' in href:
                        match = re.search(r'area=(\d+)', href)
                        if match and match.group(1).startswith(pref_code):
                            area_codes.append(match.group(1))

            # 重複を除去
            area_codes = list(set(area_codes))

            if area_codes:
                logger.info(f"都道府県 {pref_code} のエリアコード {len(area_codes)} 件を取得")
            else:
                logger.warning(f"都道府県 {pref_code} のエリアコードが見つかりませんでした")
                # フォールバック: 可能性のあるコードを生成
                area_codes = [f"{pref_code}{i:03d}" for i in range(1, 1000)]

            return area_codes

        except Exception as e:
            logger.error(f"エリアコード取得エラー (pref={pref_code}): {e}")
            # フォールバック
            return [f"{pref_code}{i:03d}" for i in range(1, 1000)]

    def get_shops_from_list_page(self, pref_code: str, area_code: str) -> List[Dict]:
        """
        一覧ページから店舗情報を取得

        Args:
            pref_code: 都道府県コード
            area_code: 地方公共団体コード

        Returns:
            店舗情報のリスト
        """
        url = f"{self.base_url}/shop/search/list/"
        params = f"?pref={pref_code}&area={area_code}&sort=aiueo"
        full_url = url + params

        shops = []

        try:
            logger.info(f"店舗一覧ページにアクセス: {full_url}")
            self.driver.get(full_url)
            time.sleep(self.delay)

            # ページのHTMLを取得
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # 店舗が見つからない場合は早期リターン
            if '該当する店舗が見つかりません' in html or '店舗が見つかりません' in html:
                logger.debug(f"店舗なし: pref={pref_code}, area={area_code}")
                return []

            # 店舗リンクを探す
            # パターン1: 詳細ページへのリンク
            detail_links = soup.find_all('a', href=lambda x: x and '/shop/search/detail/' in x)

            for link in detail_links:
                try:
                    shop_url = link.get('href', '')
                    if not shop_url.startswith('http'):
                        shop_url = self.base_url + shop_url

                    # 既に訪問済みならスキップ
                    if shop_url in self.visited_urls:
                        continue

                    shop_name = link.get_text(strip=True)

                    # 店舗名が空でない、かつURLが有効な場合のみ追加
                    if shop_name and '/shop/search/detail/' in shop_url:
                        shops.append({
                            'name': shop_name,
                            'url': shop_url,
                            'pref_code': pref_code,
                            'area_code': area_code
                        })
                        self.visited_urls.add(shop_url)

                except Exception as e:
                    logger.debug(f"店舗リンク解析エラー: {e}")
                    continue

            if shops:
                logger.info(f"pref={pref_code}, area={area_code}: {len(shops)}件の店舗を発見")

            return shops

        except TimeoutException:
            logger.warning(f"タイムアウト: {full_url}")
            return []
        except Exception as e:
            logger.error(f"店舗一覧取得エラー (pref={pref_code}, area={area_code}): {e}")
            return []

    def get_shop_details(self, shop_url: str) -> Optional[Dict]:
        """
        店舗詳細ページから情報を取得

        Args:
            shop_url: 店舗詳細ページのURL

        Returns:
            店舗詳細情報（運営会社、住所、電話番号）
        """
        try:
            logger.info(f"店舗詳細を取得: {shop_url}")
            self.driver.get(shop_url)
            time.sleep(self.delay)

            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            details = {
                'operator': '',
                'address': '',
                'phone': ''
            }

            # パターン1: テーブル形式
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')

                    if th and td:
                        key = th.get_text(strip=True)
                        value = td.get_text(strip=True)

                        if '運営会社' in key or '運営' in key:
                            details['operator'] = value
                        elif '住所' in key:
                            details['address'] = value
                        elif '電話' in key or 'TEL' in key or 'tel' in key.lower():
                            details['phone'] = value

            # パターン2: dl/dt/dd形式
            if not any(details.values()):
                dls = soup.find_all('dl')
                for dl in dls:
                    dts = dl.find_all('dt')
                    dds = dl.find_all('dd')

                    for dt, dd in zip(dts, dds):
                        key = dt.get_text(strip=True)
                        value = dd.get_text(strip=True)

                        if '運営会社' in key or '運営' in key:
                            details['operator'] = value
                        elif '住所' in key:
                            details['address'] = value
                        elif '電話' in key or 'TEL' in key or 'tel' in key.lower():
                            details['phone'] = value

            # パターン3: divやspan、pタグから情報を抽出
            if not any(details.values()):
                # 全テキストを取得して解析
                text = soup.get_text()
                lines = [line.strip() for line in text.split('\n') if line.strip()]

                for i, line in enumerate(lines):
                    if '運営会社' in line or '運営' in line:
                        if i + 1 < len(lines):
                            details['operator'] = lines[i + 1]
                    elif '住所' in line and not details['address']:
                        if i + 1 < len(lines):
                            details['address'] = lines[i + 1]
                    elif ('電話' in line or 'TEL' in line) and not details['phone']:
                        # 電話番号のパターンを探す
                        phone_match = re.search(r'0\d{1,4}-\d{1,4}-\d{4}', line)
                        if phone_match:
                            details['phone'] = phone_match.group()
                        elif i + 1 < len(lines):
                            phone_match = re.search(r'0\d{1,4}-\d{1,4}-\d{4}', lines[i + 1])
                            if phone_match:
                                details['phone'] = phone_match.group()

            # 情報が取得できたかチェック
            if any(details.values()):
                logger.info(f"  詳細取得成功: 運営会社={bool(details['operator'])}, 住所={bool(details['address'])}, 電話={bool(details['phone'])}")
                return details
            else:
                logger.warning(f"  詳細情報が見つかりませんでした")
                return None

        except Exception as e:
            logger.error(f"店舗詳細取得エラー ({shop_url}): {e}")
            return None

    def scrape_all_shops(self, test_mode: bool = False) -> List[Dict]:
        """
        全国のソフトバンク店舗情報を収集

        Args:
            test_mode: テストモード（最初の都道府県のみ処理）

        Returns:
            全店舗情報のリスト
        """
        all_shops = []

        try:
            self.setup_driver()

            prefectures_to_process = list(PREFECTURES.items())
            if test_mode:
                logger.info("テストモード: 最初の都道府県のみ処理します")
                prefectures_to_process = prefectures_to_process[:1]

            for pref_code, pref_name in prefectures_to_process:
                logger.info(f"\n{'='*60}")
                logger.info(f"都道府県: {pref_name} ({pref_code}) を処理中...")
                logger.info(f"{'='*60}")

                # 地方公共団体コードを取得
                area_codes = self.get_area_codes_from_search_page(pref_code)
                logger.info(f"{len(area_codes)}件のエリアコードを処理します")

                processed_areas = 0
                found_shops = 0

                for area_code in area_codes:
                    # 店舗一覧を取得
                    shops = self.get_shops_from_list_page(pref_code, area_code)
                    processed_areas += 1

                    if not shops:
                        continue

                    found_shops += len(shops)

                    # 各店舗の詳細情報を取得
                    for shop in shops:
                        details = self.get_shop_details(shop['url'])

                        shop_data = {
                            '店舗名': shop['name'],
                            '運営会社': details.get('operator', '') if details else '',
                            '住所': details.get('address', '') if details else '',
                            '電話番号': details.get('phone', '') if details else '',
                            '都道府県': pref_name,
                            '詳細ページURL': shop['url']
                        }
                        all_shops.append(shop_data)

                    # 進捗表示
                    if processed_areas % 10 == 0:
                        logger.info(f"  進捗: {processed_areas}/{len(area_codes)} エリア処理済み, {found_shops}件の店舗発見")

                    # 定期的に保存
                    if len(all_shops) > 0 and len(all_shops) % 50 == 0:
                        self.save_to_csv(all_shops, 'softbank_shops_progress.csv')

                logger.info(f"{pref_name}: {found_shops}件の店舗を収集完了")

            return all_shops

        except Exception as e:
            logger.error(f"スクレイピング中にエラー: {e}")
            return all_shops

        finally:
            if self.driver:
                self.driver.quit()
                logger.info("ブラウザを閉じました")

    def save_to_csv(self, shops: List[Dict], filename: str):
        """
        店舗情報をCSVファイルに保存

        Args:
            shops: 店舗情報のリスト
            filename: 出力ファイル名
        """
        if not shops:
            logger.warning("保存するデータがありません")
            return

        df = pd.DataFrame(shops)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"CSVファイルに保存: {filename} ({len(shops)}件)")


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description='ソフトバンク店舗情報スクレイパー')
    parser.add_argument('--test', action='store_true', help='テストモード（最初の都道府県のみ）')
    parser.add_argument('--no-headless', action='store_true', help='ブラウザを表示')
    args = parser.parse_args()

    logger.info("="*60)
    logger.info("ソフトバンク店舗情報スクレイピング開始")
    logger.info("="*60)

    scraper = SoftBankSeleniumScraper(headless=not args.no_headless)

    try:
        shops = scraper.scrape_all_shops(test_mode=args.test)

        # 最終結果を保存
        if shops:
            output_file = 'softbank_shops_final.csv'
            scraper.save_to_csv(shops, output_file)

            # 統計情報を表示
            df = pd.DataFrame(shops)
            logger.info("\n" + "="*60)
            logger.info("取得結果サマリー")
            logger.info("="*60)
            logger.info(f"総店舗数: {len(shops)}")
            logger.info(f"\n都道府県別店舗数:")
            for pref, count in df['都道府県'].value_counts().items():
                logger.info(f"  {pref}: {count}件")
        else:
            logger.warning("店舗情報を取得できませんでした")

    except KeyboardInterrupt:
        logger.info("\n中断されました")
    except Exception as e:
        logger.error(f"エラー: {e}")
        raise


if __name__ == "__main__":
    main()
