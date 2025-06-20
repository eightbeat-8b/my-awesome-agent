# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import requests

import google.auth
from google.adk.agents import Agent

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


# カリフォルニアの緯度経度（サンフランシスコ）
CALIFORNIA_LAT = 37.4220
CALIFORNIA_LONG = -122.0841

# Weather APIの設定
WEATHER_API_URL = "https://weather.googleapis.com/v1/currentConditions:lookup"
GEOCODING_API_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def get_coordinates(city: str) -> tuple[float, float] | tuple[None, None]:
    """
    特定の地域、都市または州の緯度と経度を取得します。

    Args:
        city(str): 緯度と経度を知りたい都市の名前
    Returns:
        tuple: 緯度と経度のタプルまたは(None, None)
    """
    print(f"[DEBUG] get_coordinates called with city: {city}")
    api_key = os.getenv("WEATHER_API_KEY")
    print(f"[DEBUG] API key retrieved: {'Set' if api_key else 'Not set'}")

    if not api_key:
        print("[DEBUG] No API key found, returning None, None")
        return None, None

    try:
        params = {
            'address': city,
            'key': api_key,
            'language': 'ja'
        }
        print(f"[DEBUG] Request URL: {GEOCODING_API_URL}")
        print(f"[DEBUG] Request params: {params}")

        response = requests.get(GEOCODING_API_URL, params=params)
        print(f"[DEBUG] Response status code: {response.status_code}")

        response.raise_for_status()
        data = response.json()
        print(f"[DEBUG] Response data: {data}")

        if data["status"] == "OK" and data["results"]:
            location = data['results'][0]['geometry']['location']
            lat, lng = location['lat'], location['lng']
            print(f"[DEBUG] Successfully found coordinates: lat={lat}, lng={lng}")
            return lat, lng
        else:
            print(f"[DEBUG] Geocoding failed: status={data.get('status')}, results count={len(data.get('results', []))}")
            return None, None
    except requests.RequestException as e:
        print(f"[DEBUG] Request exception: {str(e)}")
        return None, None




def get_weather(city: str) -> dict:
    """
    特定の都市、州、地域の現在の天気をお知らせします。大きな地域名でも対応可能です。

    Args:
        city(str): 天気を知りたい都市、州、地域の名前
    Returns:
        dict: 天気情報またはエラー情報を返す
    """
    weather_api_key = os.getenv("WEATHER_API_KEY")

    lat, lng = get_coordinates(city)

    try:
        params = {
            'key': weather_api_key,
            'location.latitude': lat,
            'location.longitude': lng
        }
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        weather_data = response.json()

        temperature = weather_data["temperature"]["degrees"]
        condition = weather_data["weatherCondition"]["description"]["text"]

        return{
            "status": "success",
            "report": f"{city}の現在の天気は{condition}で、気温は{temperature}度です。"
        }
    except requests.RequestException as e:
        return {
            "status": "error",
            "report": f"{city}の天気情報の取得に失敗しました: {str(e)}"
        }


root_agent = Agent(
    name="root_agent",
    model="gemini-2.0-flash",
    instruction="あなたは親切なアシスタントです。ユーザーが聞いた地域の天気やについて、できるだけ柔軟に対応してください。「カリフォルニア」「日本」「アメリカ」のような大きな地域名でも、その地域の代表的な場所の情報を提供してください。",
    tools=[get_weather],
)
