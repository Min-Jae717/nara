import sqlite3
import requests
import json
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote_plus
from dotenv import load_dotenv
import os

# API 설정
load_dotenv()
API_KEY = os.getenv("G2B_API_KEY")

# 🔄 마지막 수집 시점 불러오기 함수
def load_last_collected_time(file_name, default_value):
    try:
        with open(file_name, 'r') as f:
            return json.load(f)['last_collected_time']
    except (FileNotFoundError, KeyError):
        return default_value

# SQLite DB 연결 및 테이블 생성
conn = sqlite3.connect("bids_raw.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS bids (
    bidNtceNo TEXT PRIMARY KEY,
    raw_json TEXT
)
""")

# 수집 시점 설정
last_file = "last_collected_time.json"
default_start = (datetime.now() - timedelta(minutes=5)).strftime("%Y%m%d%H%M")
last_collected_time = load_last_collected_time(last_file, default_start)
current_time = datetime.now().strftime("%Y%m%d%H%M")

# 기본URL 설정
BASE_URL = "http://apis.data.go.kr/1230000/ao/PubDataOpnStdService/getDataSetOpnStdBidPblancInfo"

info = []
page = 1

while True:
    # fallback: 기본값이 없을 경우 최근 5분
    if last_collected_time is None:
        last_collected_time = (datetime.now() - timedelta(minutes=5)).strftime("%Y%m%d%H%M")

    params = {
        'serviceKey': API_KEY,
        'pageNo': page,
        'numOfRows': 100,
        'inqryDiv': 1,
        'type': 'json',
        'bidNtceBgnDt': int(last_collected_time),
        'bidNtceEndDt': int(current_time),
    }

    query_string = urlencode(params, quote_via=quote_plus)
    url = f"{BASE_URL}?{query_string}"

    try:
        response = requests.get(url)
        data = response.json()
        items = data.get("response", {}).get("body", {}).get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"API 호출 오류: {e}")
        break
    except KeyError:
        print("응답 형식 오류: 'items' 키가 없음")
        break

    if not items:
        break
    else:
        info.extend(items)
        page += 1

# 모든 페이지의 데이터 저장
for item in info:
    try:
        cur.execute("""
            INSERT OR REPLACE INTO bids (bidNtceNo, raw_json)
            VALUES (?, ?)
        """, (
            item.get("bidNtceNo"),
            json.dumps(item, ensure_ascii=False)
        ))
    except Exception as e:
        print(f"저장 오류: {e}")

conn.commit()
print(f"{len(info)}건 저장 완료.")

# 마지막 수집 시점 갱신: 마지막 공고의 bidNtceBgnDt 기준
if info:
    last_time = info[-1].get("bidNtceBgnDt", None)
    if last_time:
        with open(last_file, 'w') as f:
            json.dump({"last_collected_time": last_time}, f)

conn.close()
