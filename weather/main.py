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

    # 日付が選択されたときに過去の天気予報を表示する関数
    def on_date_selected(e):
        if e.date:
            selected_date = e.date.strftime("%Y-%m-%d")
            if current_region_code:
                show_forecast_for_date(current_region_code, selected_date)
        page.update()

    # 過去の天気予報を表示する関数
    def show_forecast_for_date(region_code: str, selected_date: str):
        # DBから過去の天気予報を取得して表示する
        history_data = db.get_forecast_by_date(region_code, selected_date)
        if history_data:
            history_view.visible = True
            history_view.controls = [
                ft.Column(
                    controls=[
                        ft.Text(f"{area_cache[region_code]['name']}の{selected_date}の予報",
                               size=20,
                               weight="bold"),
                        ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("日付")),
                                ft.DataColumn(ft.Text("天気")),
                            ],
                            rows=[
                                ft.DataRow(
                                    cells=[
                                        ft.DataCell(ft.Text(format_date(row[3]))),
                                        ft.DataCell(ft.Text(f"{get_weather_icon(row[4])} {get_weather_text(row[4])}")),
                                    ]
                                ) for row in history_data
                            ],
                        )
                    ],
                    scroll=ft.ScrollMode.AUTO,
                )
            ]
        else:
            history_view.visible = True
            history_view.controls = [
                ft.Text(f"選択された日付（{selected_date}）の予報データは見つかりませんでした。",
                       color=ft.colors.ERROR)
            ]
        page.update()
    # APIからデータを取得する関数
    def fetch_data(url: str) -> Dict:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            show_error(f"データ取得エラー: {str(e)}")
            return {}

    # 地域リストを読み込む関数
    def load_region_list():
        try:
            progress_bar.visible = True
            page.update()

            # 気象庁のAPIから地域データを取得
            data = fetch_data("http://www.jma.go.jp/bosai/common/const/area.json")
            if "offices" in data:
                area_cache.update(data["offices"])
                update_region_menu()
            else:
                show_error("地域データの形式が予期したものと異なります。")
        except Exception as e:
            show_error(f"地域データの読み込みに失敗しました: {str(e)}")
        finally:
            progress_bar.visible = False
            page.update()

    # 地域選択メニューを更新する関数
    def update_region_menu():
        region_list_view.controls.clear()
        for code, area in area_cache.items():
            region_list_view.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.LOCATION_ON),
                    title=ft.Text(area["name"]),
                    subtitle=ft.Text(f"地域コード: {code}"),
                    on_click=lambda e, code=code: load_forecast(code),
                )
            )
        page.update()

    # 選択した地域の天気予報を取得する関数
    def load_forecast(region_code: str):
        try:
            global current_region_code
            current_region_code = region_code
            progress_bar.visible = True
            page.update()

            # 気象庁のAPIから天気予報データを取得
            url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"
            data = fetch_data(url)

            if data:
                display_forecast(data)

                # 天気予報データをDBに保存
                weekly_data = data[1]
                weather_forecasts = weekly_data["timeSeries"][0]
                temp_forecasts = weekly_data["timeSeries"][1]
                area_name = area_cache[region_code]["name"]

                # 各日の予報データをDBに保存
                for i in range(len(weather_forecasts["timeDefines"])):
                    date = weather_forecasts["timeDefines"][i]
                    weather_code = weather_forecasts["areas"][0]["weatherCodes"][i]

                    try:
                        min_temp = temp_forecasts["areas"][0]["tempsMin"][i]
                        max_temp = temp_forecasts["areas"][0]["tempsMax"][i]
                    except (IndexError, KeyError):
                        min_temp = max_temp = None

                    db.save_forecast(
                        region_code,
                        area_name,
                        date,
                        weather_code,
                        min_temp if min_temp != '--' else None,
                        max_temp if max_temp != '--' else None
                    )
            else:
                show_error("天気予報データが見つかりません。")
        except Exception as e:
            show_error(f"天気予報の取得に失敗しました: {str(e)}")
        finally:
            progress_bar.visible = False
            page.update()

    # 天気予報データを表示する関数
    def display_forecast(data: Dict):
        forecast_view.controls.clear()
        try:
            weekly_data = data[1]
            weather_forecasts = weekly_data["timeSeries"][0]
            temp_forecasts = weekly_data["timeSeries"][1]

            grid = ft.GridView(
                expand=True,
                runs_count=4,
                max_extent=200,
                child_aspect_ratio=0.8,
                spacing=10,
                run_spacing=10,
                padding=20,
            )

            # 予報データをカード形式で表示
            for i in range(len(weather_forecasts["timeDefines"])):
                date = weather_forecasts["timeDefines"][i]
                weather_code = weather_forecasts["areas"][0]["weatherCodes"][i]

                try:
                    min_temp = temp_forecasts["areas"][0]["tempsMin"][i]
                    max_temp = temp_forecasts["areas"][0]["tempsMax"][i]
                except (IndexError, KeyError):
                    min_temp = max_temp = "--"

                card = ft.Card(
                    content=ft.Container(content=ft.Column(
                            controls=[
                                ft.Text(format_date(date), size=16, weight="bold"),
                                ft.Text(get_weather_icon(weather_code), size=25),
                                ft.Text(get_weather_text(weather_code), size=16),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        padding=20,
                    )
                )
                grid.controls.append(card)

            forecast_view.controls.append(grid)

        except (KeyError, IndexError) as e:
            show_error("週間予報データの取得に失敗しました。")

        page.update()

    page.add(
        ft.Row(
            [
                ft.Container(
                    width=300,
                    content=region_list_view,
                    bgcolor=ft.colors.SURFACE_VARIANT,
                ),
                ft.Container(
                    expand=True,
                    content=ft.Column([
                        forecast_view,
                        history_view,
                    ]),
                ),
            ],
            expand=True,
        ),
        progress_bar
    )

    # 地域リストを読み込む
    load_region_list()

# 日付をフォーマットする関数
def format_date(date_str: str) -> str:
    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    weekday = weekdays[date.weekday()]
    return f"{date.month}/{date.day}\n({weekday})"

# 天気コードから天気のテキストを取得する関数
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

def get_weather_icon(code: str) -> str:
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
    return weather_icons.get(code, "❓")

if __name__ == "__main__":
    ft.app(target=main)