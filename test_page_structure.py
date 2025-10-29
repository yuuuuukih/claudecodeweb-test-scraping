#!/usr/bin/env python3
"""
ソフトバンクのページ構造を確認するテストスクリプト
"""

import requests
from bs4 import BeautifulSoup
import json

def test_list_page():
    """一覧ページの構造を確認"""
    url = "https://www.softbank.jp/shop/search/list/"
    params = {
        'pref': '13',
        'area': '131016',
        'sort': 'aiueo'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    print("=" * 60)
    print("店舗一覧ページの構造を確認中...")
    print(f"URL: {url}")
    print(f"パラメータ: {params}")
    print("=" * 60)

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        print(f"ステータスコード: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print()

        soup = BeautifulSoup(response.content, 'html.parser')

        # タイトルを確認
        title = soup.find('title')
        print(f"ページタイトル: {title.get_text() if title else 'N/A'}")
        print()

        # 店舗リンクを探す
        print("店舗詳細へのリンクを検索中...")
        detail_links = soup.find_all('a', href=lambda x: x and '/shop/search/detail/' in x)
        print(f"見つかった詳細リンク数: {len(detail_links)}")
        print()

        if detail_links:
            print("最初の5件のリンク:")
            for i, link in enumerate(detail_links[:5], 1):
                print(f"  {i}. 店舗名: {link.get_text(strip=True)}")
                print(f"     URL: {link['href']}")
                print(f"     親要素: {link.parent.name if link.parent else 'N/A'}")
                print()

        # その他の可能な構造を確認
        print("\n可能な店舗コンテナ要素を検索中...")
        possible_containers = [
            'div.shop-item',
            'div.shop-list-item',
            'li.shop',
            'div.store-item',
            'article',
        ]

        for selector in possible_containers:
            elements = soup.select(selector)
            if elements:
                print(f"  {selector}: {len(elements)}件")

        # HTMLの一部を保存
        with open('list_page_sample.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("\nHTMLサンプルを list_page_sample.html に保存しました")

    except Exception as e:
        print(f"エラー: {e}")


def test_detail_page():
    """詳細ページの構造を確認"""
    url = "https://www.softbank.jp/shop/search/detail/T102/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    print("\n" + "=" * 60)
    print("店舗詳細ページの構造を確認中...")
    print(f"URL: {url}")
    print("=" * 60)

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        print(f"ステータスコード: {response.status_code}")
        print()

        soup = BeautifulSoup(response.content, 'html.parser')

        # タイトルを確認
        title = soup.find('title')
        print(f"ページタイトル: {title.get_text() if title else 'N/A'}")
        print()

        # 店舗情報を探す
        print("店舗情報を検索中...")

        # パターン1: テーブル
        tables = soup.find_all('table')
        print(f"テーブル数: {len(tables)}")
        if tables:
            print("\n最初のテーブルの内容:")
            for row in tables[0].find_all('tr')[:10]:
                cells = row.find_all(['th', 'td'])
                if cells:
                    print(f"  {' | '.join(cell.get_text(strip=True) for cell in cells)}")

        # パターン2: dl/dt/dd
        dls = soup.find_all('dl')
        print(f"\n<dl>要素数: {len(dls)}")
        if dls:
            print("\n最初の<dl>の内容:")
            for dt, dd in zip(dls[0].find_all('dt')[:5], dls[0].find_all('dd')[:5]):
                print(f"  {dt.get_text(strip=True)}: {dd.get_text(strip=True)}")

        # 運営会社、住所、電話番号を検索
        print("\n特定情報を検索中...")
        text = soup.get_text()

        keywords = ['運営会社', '住所', '電話', 'TEL']
        for keyword in keywords:
            if keyword in text:
                print(f"  '{keyword}' が見つかりました")

        # HTMLの一部を保存
        with open('detail_page_sample.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("\nHTMLサンプルを detail_page_sample.html に保存しました")

    except Exception as e:
        print(f"エラー: {e}")


def test_search_page():
    """検索トップページの構造を確認（エリアコード取得のため）"""
    url = "https://www.softbank.jp/shop/search/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    print("\n" + "=" * 60)
    print("検索ページの構造を確認中...")
    print(f"URL: {url}")
    print("=" * 60)

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        print(f"ステータスコード: {response.status_code}")
        print()

        soup = BeautifulSoup(response.content, 'html.parser')

        # セレクトボックスを探す
        selects = soup.find_all('select')
        print(f"セレクトボックス数: {len(selects)}")

        for i, select in enumerate(selects, 1):
            name = select.get('name', 'N/A')
            print(f"\nセレクトボックス {i}: name='{name}'")
            options = select.find_all('option')
            print(f"  オプション数: {len(options)}")
            if options and len(options) < 50:
                print("  オプション一覧:")
                for opt in options[:10]:
                    value = opt.get('value', '')
                    text = opt.get_text(strip=True)
                    print(f"    {value}: {text}")
                if len(options) > 10:
                    print(f"    ... 他 {len(options) - 10} 件")

        # JavaScriptを探す（エリアコードがJSに埋め込まれている可能性）
        scripts = soup.find_all('script')
        print(f"\nスクリプトタグ数: {len(scripts)}")

        # HTMLを保存
        with open('search_page_sample.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("\nHTMLサンプルを search_page_sample.html に保存しました")

    except Exception as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    test_search_page()
    test_list_page()
    test_detail_page()
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)
