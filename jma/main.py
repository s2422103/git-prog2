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
