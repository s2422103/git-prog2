import flet as ft
import requests
import sqlite3
from datetime import datetime
from typing import Dict

# 地域コードをキーにして地域名を取得できるようにする
area_cache: Dict[str, Dict] = {}

class WeatherDB:
    def __init__(self, db_path="weather.db"):
        # DBファイルのパスを指定
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        # DBがなければ新規作成し、テーブルを初期化する
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weather_forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    area_code TEXT NOT NULL,
                    area_name TEXT NOT NULL,
                    forecast_date DATE NOT NULL,
                    weather_code TEXT NOT NULL,
                    temp_min INTEGER,
                    temp_max INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(area_code, forecast_date)
                )
            """)
def save_forecast(self, area_code: str, area_name: str, forecast_date: str,
                     weather_code: str, temp_min: int, temp_max: int):
        # 予報データをDBに保存。既存のデータがあれば上書きする
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO weather_forecasts
                (area_code, area_name, forecast_date, weather_code, temp_min, temp_max)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (area_code, area_name, forecast_date, weather_code, temp_min, temp_max))

def get_forecast_history(self, area_code: str = None, start_date: str = None, end_date: str = None):
        # 過去の予報データを指定された条件で取得する
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM weather_forecasts WHERE 1=1"
            params = []
            
            if area_code:
                query += " AND area_code = ?"
                params.append(area_code) 
            if start_date:
                query += " AND forecast_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND forecast_date <= ?"
                params.append(end_date) 
            query += " ORDER BY forecast_date DESC"
            return conn.execute(query, params).fetchall()
def get_forecast_by_date(self, area_code: str, selected_date: str):
        # 特定の日付の予報データを取得する
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("""
                SELECT * FROM weather_forecasts
                WHERE area_code = ? AND date(forecast_date) = date(?)
                ORDER BY forecast_date
            """, (area_code, selected_date)).fetchall()
def main(page: ft.Page):
    # アプリケーションのページ設定
    page.title = "地域ごとの天気予報"
    page.theme_mode = "light"

    # WeatherDBインスタンスを作成
    db = WeatherDB()
    current_region_code = None

    # プログレスバーの初期設定
    progress_bar = ft.ProgressBar(visible=False)

    # エラーメッセージを表示する関数
    def show_error(message: str):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            action="閉じる",
            bgcolor=ft.colors.ERROR,
        )
        page.snack_bar.open = True
        page.update()
# 地域一覧を表示するListView
    region_list_view = ft.ListView(
        expand=True,
        spacing=10,
        padding=10,
    )

    # 天気予報表示用のビュー
    forecast_view = ft.Column(
        expand=True,
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
    )

    # 過去の天気予報を表示するビュー
    history_view = ft.Column(
        visible=False,
        expand=True,
    )
# 天気アイコンを取得する関数
def get_weather_icon(weather_code: str) -> str:
    weather_icons = {
        "100": "☀️",  # 晴れ
        "101": "🌤️",  # 晴れ時々曇り
        "102": "🌦️",  # 晴れ時々雨
        "200": "☁️",  # 曇り
        "300": "🌧️",  # 雨
        "317": "🌧️❄️☁️",  # 雨か雪のち曇り
        "400": "❄️",  # 雪
        "402": "❄️☁️",  # 雪時々曇り
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
        "214":"☁️🌧️",
        "204":"☁️❄️⚡️",
        "207":"☁️🌧️❄️",
        "110":"☀️☁️",
        "205":"☁️❄️",
        "217":"☁️❄️",
        "304":"❄️🌧️",
    }
    return weather_icons.get(weather_code, "❓")

def get_weather_text(code: str) -> str:
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
        "317": "雨か雪のち曇り",
        "400": "雪",
        "402": "雪時々曇り",
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
        "214":"曇り後雨",
        "204":"曇り時々雪で雷を伴う",
        "207":"曇り時々雨か雪",
        "110":"晴れのち時々曇り",
        "205":"曇り時々雪",
        "217":"曇り後雪",
        "304":"雪か雨",
    }
    return weather_codes.get(code, f"不明な天気 (コード: {code})")

def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = ft.colors.WHITE

    # JSONデータを読み込む
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        page.add(ft.Text("JSONファイルが見つかりません。", color=ft.colors.RED))
        return
    except json.JSONDecodeError as e:
        page.add(ft.Text(f"JSONデータの読み込みに失敗しました: {e}", color=ft.colors.RED))
        return

    centers = data.get("centers", {})
    offices = data.get("offices", {})
    # 天気情報を表示する領域
    weather_display = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    # 天気情報を取得して表示する関数
    def display_weather(office_code: str):
        weather_display.controls.clear()
        try:
            # 天気情報を取得
            response = requests.get(WEATHER_API_URL.format(office_code=office_code))
            response.raise_for_status()
            weather_data = response.json()

            
            # 天気情報を表示
            for i, day in enumerate(weather_data[0]["timeSeries"][0]["timeDefines"]):
                date = format_date(day)
                # i 番目の天気コードを取得
                weather_code = weather_data[0]["timeSeries"][0]["areas"][0]["weatherCodes"][i]
                weather_display.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(date, size=16, weight="bold"),
                                    ft.Text(get_weather_icon(weather_code)),
                                    ft.Text(get_weather_text(weather_code)),
                                    ft.Text(f"天気コード: {weather_code}"),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            padding=10,
                        )
                    )
                )
        except Exception as e:
            weather_display.controls.append(ft.Text(f"天気情報の取得に失敗しました: {e}", color=ft.colors.RED))

        page.update()

    # 左側のリスト
    center_tiles = []
    for center_key, center_info in centers.items():
        # そのセンターに関連するオフィスを取得
        related_offices = [
            offices[office_key]
            for office_key in center_info.get("children", [])
            if office_key in offices
        ]
        # 選択情報を表示するテキスト
        selected_item = ft.Text("", size=20, color=ft.colors.BLACK)
        selected_index = None  # 選択されたアイテムのインデックス
        forecast_view = ft.Column(spacing=10, expand=True)


        # オフィスリスト
        office_tiles = [
            ft.ListTile(
                title=ft.Text(f"{offices[office_key]['name']} ({offices[office_key]['enName']})"),
                on_click=lambda e, office_code=office_key: display_weather(office_code),
            )
            for office_key in center_info.get("children", [])
            if office_key in offices
        ]
            # 地域リスト
        region_list_view = ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
        )

        # プログレスバーの追加
        progress_bar = ft.ProgressBar(visible=False)

        # ExpansionTile
        center_tiles.append(
            ft.ExpansionTile(
                title=ft.Text(center_info["name"], color=ft.colors.BLACK),
                controls=office_tiles,
                initially_expanded=False,
                text_color=ft.colors.BLACK,
                collapsed_text_color=ft.colors.GREY,
            )
        )

    # 左側のリスト
    region_list = ft.Container(
        content=ft.Column(
            controls=center_tiles,
            scroll=ft.ScrollMode.AUTO,
        ),
        width=250,
        bgcolor=ft.colors.LIGHT_BLUE_50,
        padding=10,
    )

    # レイアウト
    page.add(
        ft.Row(
            controls=[
                region_list,
                ft.Container(
                    content=weather_display, padding=10
                ),
                ft.VerticalDivider(width=1),
                ft.Column(
                    [selected_item, forecast_view],
                    alignment=ft.MainAxisAlignment.START,
                    expand=True,
                ),
            ],
            expand=True,
        ),
        progress_bar,
    )

# 実行
ft.app(target=main)

