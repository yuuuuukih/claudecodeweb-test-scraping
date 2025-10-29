#!/usr/bin/env python3
"""
ソフトバンク店舗情報スクレイパー
全国のソフトバンク店舗の情報を収集します
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from typing import List, Dict, Optional
import logging
from urllib.parse import urljoin

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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

class SoftBankShopScraper:
    def __init__(self):
        self.base_url = "https://www.softbank.jp"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.delay = 1.0  # リクエスト間の遅延（秒）

    def get_municipal_codes(self, pref_code: str) -> List[str]:
        """
        指定された都道府県の地方公共団体コードを取得
        ソフトバンクの検索ページから動的に取得
        """
        url = f"{self.base_url}/shop/search/"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # エリア選択のドロップダウンやJavaScriptから地方公共団体コードを抽出
            # この部分は実際のページ構造に応じて調整が必要
            codes = []

            # 代替方法: すべての可能な地方公共団体コードを試す
            # 地方公共団体コードは通常 XXYYYY の形式（XX=都道府県、YYYY=市区町村）
            # 実際には、各都道府県ごとに001-999の範囲で試すことができる
            for city_code in range(1, 1000):
                code = f"{pref_code}{city_code:03d}"
                codes.append(code)

            return codes

        except Exception as e:
            logger.error(f"地方公共団体コード取得エラー (pref={pref_code}): {e}")
            # フォールバック: 範囲ベースで生成
            return [f"{pref_code}{i:03d}" for i in range(1, 1000)]

    def get_shop_list(self, pref_code: str, area_code: str) -> List[Dict]:
        """
        指定された都道府県・エリアの店舗一覧を取得
        """
        url = f"{self.base_url}/shop/search/list/"
        params = {
            'pref': pref_code,
            'area': area_code,
            'sort': 'aiueo'
        }

        try:
            time.sleep(self.delay)  # レート制限
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            shops = []

            # 店舗リストを抽出（実際のHTML構造に応じて調整が必要）
            # 一般的なパターンを試す
            shop_items = soup.select('.shop-item, .shop-list-item, .store-item, li.shop, div.shop')

            if not shop_items:
                # 別のセレクタを試す
                shop_items = soup.find_all('a', href=lambda x: x and '/shop/search/detail/' in x)

            for item in shop_items:
                try:
                    # 店舗名とURLを抽出
                    if item.name == 'a':
                        link = item
                        shop_name = item.get_text(strip=True)
                    else:
                        link = item.find('a', href=lambda x: x and '/shop/search/detail/' in x)
                        if not link:
                            continue
                        shop_name = link.get_text(strip=True)

                    shop_url = urljoin(self.base_url, link['href'])

                    if shop_name and shop_url:
                        shops.append({
                            'name': shop_name,
                            'url': shop_url,
                            'pref_code': pref_code,
                            'area_code': area_code
                        })

                except Exception as e:
                    logger.debug(f"店舗アイテム解析エラー: {e}")
                    continue

            if shops:
                logger.info(f"pref={pref_code}, area={area_code}: {len(shops)}件の店舗を発見")

            return shops

        except requests.RequestException as e:
            logger.error(f"店舗一覧取得エラー (pref={pref_code}, area={area_code}): {e}")
            return []

    def get_shop_details(self, shop_url: str) -> Optional[Dict]:
        """
        店舗詳細ページから情報を取得
        """
        try:
            time.sleep(self.delay)  # レート制限
            response = self.session.get(shop_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            details = {}

            # 店舗情報テーブルから情報を抽出
            # 一般的なパターン: <th>ラベル</th><td>値</td>

            # パターン1: テーブル形式
            rows = soup.select('table tr, .shop-info tr, .store-info tr')
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
                    elif '電話' in key or 'TEL' in key:
                        details['phone'] = value

            # パターン2: dl/dt/dd形式
            if not details:
                dls = soup.select('dl.shop-info, dl.store-info, .shop-detail dl')
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
                        elif '電話' in key or 'TEL' in key:
                            details['phone'] = value

            # パターン3: div/span形式
            if not details:
                info_sections = soup.select('.shop-info, .store-info, .shop-detail')
                for section in info_sections:
                    text = section.get_text()
                    # テキストから情報を抽出
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    for i, line in enumerate(lines):
                        if '運営会社' in line or '運営' in line:
                            if i + 1 < len(lines):
                                details['operator'] = lines[i + 1]
                        elif '住所' in line:
                            if i + 1 < len(lines):
                                details['address'] = lines[i + 1]
                        elif '電話' in line or 'TEL' in line:
                            if i + 1 < len(lines):
                                details['phone'] = lines[i + 1]

            return details if details else None

        except Exception as e:
            logger.error(f"店舗詳細取得エラー ({shop_url}): {e}")
            return None

    def scrape_all_shops(self) -> List[Dict]:
        """
        全国のソフトバンク店舗情報を収集
        """
        all_shops = []

        for pref_code, pref_name in PREFECTURES.items():
            logger.info(f"都道府県: {pref_name} ({pref_code}) を処理中...")

            # 地方公共団体コードを取得
            municipal_codes = self.get_municipal_codes(pref_code)

            for area_code in municipal_codes:
                # 店舗一覧を取得
                shops = self.get_shop_list(pref_code, area_code)

                for shop in shops:
                    # 既に取得済みの店舗はスキップ
                    if any(s['url'] == shop['url'] for s in all_shops):
                        continue

                    # 詳細情報を取得
                    details = self.get_shop_details(shop['url'])

                    if details:
                        shop_data = {
                            '店舗名': shop['name'],
                            '運営会社': details.get('operator', ''),
                            '住所': details.get('address', ''),
                            '電話番号': details.get('phone', ''),
                            '都道府県': pref_name,
                            '詳細ページURL': shop['url']
                        }
                        all_shops.append(shop_data)
                        logger.info(f"  取得完了: {shop['name']}")
                    else:
                        logger.warning(f"  詳細取得失敗: {shop['name']}")

                # 定期的に保存
                if len(all_shops) > 0 and len(all_shops) % 100 == 0:
                    self.save_to_csv(all_shops, 'softbank_shops_temp.csv')
                    logger.info(f"進捗: {len(all_shops)}件の店舗を保存しました")

        return all_shops

    def save_to_csv(self, shops: List[Dict], filename: str):
        """
        店舗情報をCSVファイルに保存
        """
        df = pd.DataFrame(shops)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"CSVファイルに保存しました: {filename}")

def main():
    logger.info("ソフトバンク店舗情報スクレイピング開始")

    scraper = SoftBankShopScraper()
    shops = scraper.scrape_all_shops()

    # 最終結果を保存
    scraper.save_to_csv(shops, 'softbank_shops_final.csv')

    logger.info(f"完了: 合計 {len(shops)} 件の店舗情報を取得しました")

    # 統計情報を表示
    df = pd.DataFrame(shops)
    print("\n=== 取得結果サマリー ===")
    print(f"総店舗数: {len(shops)}")
    print(f"\n都道府県別店舗数:")
    print(df['都道府県'].value_counts())

if __name__ == "__main__":
    main()
