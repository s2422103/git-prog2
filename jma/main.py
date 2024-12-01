import flet as ft
import json
import os
import requests
from datetime import datetime, timedelta
from typing import Dict

# JSON ファイルのパス
json_path = os.path.join(os.path.dirname(__file__), 'data.json')

# JSON ファイルを読み込む
try:
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
except FileNotFoundError:
    raise FileNotFoundError(f"JSON ファイル '{json_path}' が見つかりません。")

# サンプル天気予報データ
weather_sample = [
    {"date": (datetime.now() + timedelta(days=i)).isoformat(), "code": "100"} for i in range(7)
]

# 地域キャッシュ
area_cache: Dict[str, Dict] = {}

def format_date(date_str: str) -> str:
# 日付を日本語表記に変換
    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    return date.strftime("%Y年%m月%d日")


def get_weather_text(code: str) -> str:
# 天気コードに対応する天気を返す
    weather_codes = {
        "100": "晴れ",
        "101": "晴れ時々曇り",
        "102": "晴れ時々雨",
        "200": "曇り",
        "201": "曇り時々晴れ",
        "202": "曇り時々雨",
        "218": "曇り時々雪",
        "270": "雪時々曇り",
        "300": "雨",
        "400": "雪",
        "500": "雷雨",
        "413": "雪のち雨",
        "206": "雨時々曇り",
        "111": "雨時々晴れ",
        "112": "雨時々雪",
        "211": "雪時々晴れ",
        "206": "雨時々曇り",
        "212": "雪時々曇り",
        "313": "雪のち雨",
        "314": "雨のち雪",
        "203": "曇り時々雪",
        "302": "雪",
        "114": "雪時々晴れ",
    }
    return weather_codes.get(code, f"不明な天気 (コード: {code})")

def get_weather_icon(code: str) -> str:
# 天気コードに対応する絵文字を返す
    weather_icons = {
        "100": "☀️",  # 晴れ
        "101": "🌤️",  # 晴れ時々曇り
        "102": "🌦️",  # 晴れ時々雨
        "200": "☁️",  # 曇り
        "300": "🌧️",  # 雨
        "400": "❄️",  # 雪
        "500": "⛈️",  # 雷雨
        "413": "❄️→🌧️",  # 雪のち雨
        "314": "🌧️→❄️",  # 雨のち雪
        "201": "🌤️",
        "202": "☁️🌧️",
        "218": "☁️❄️",
        "270": "❄️☁️",
        "206": "🌧️☁️",
        "111": "🌧️☀️",
        "112": "🌧️❄️",
        "211": "❄️☀️",
        "212": "❄️☁️",
        "313": "❄️🌧️",
        "203": "☁️❄️",
        "302": "❄️",
        "114": "❄️☀️",



    }
    # 聞いたことも無い天気の場合は❓を返す
    return weather_icons.get(code, "❓")

def main(page: ft.Page):
    page.title = "地域選択と天気予報表示"
    page.theme_mode = "light"
    # ページの背景色を設定
    page.bgcolor = ft.colors.LIGHT_BLUE_800


    # 選択情報を表示するテキスト
    selected_item = ft.Text("三日間の天気", size=20, color=ft.colors.WHITE)
    selected_index = None  # 選択されたアイテムのインデックス
    forecast_view = ft.Column(spacing=10, expand=True)

    # 地域リスト
    region_list_view = ft.ListView(
        expand=True,
        spacing=10,
        padding=10,
    )

    # プログレスバーの追加
    progress_bar = ft.ProgressBar(visible=False)
