import streamlit as st
import pandas as pd
import psycopg2
import json
import os
from dotenv import load_dotenv

# 환경변수에서 DB URL 불러오기
from dotenv import load_dotenv
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# DB 연결 및 데이터 로딩
def load_data():
    conn = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )
    cur = conn.cursor()
    cur.execute("SELECT raw FROM bids_live ORDER BY raw->>'bidNtceBgn' DESC LIMIT 100")
    rows = cur.fetchall()
    conn.close()

    # raw JSONB → pandas DataFrame 변환
    raw_data = [json.loads(row[0]) for row in rows]
    df = pd.json_normalize(raw_data)
    return df

# Streamlit 앱 설정
st.set_page_config(page_title="입찰 공고 실시간 조회", layout="wide")
st.title("📢 나라장터 실시간 입찰 공고")

try:
    df = load_data()
    st.success(f"총 {len(df)}건의 공고를 불러왔습니다.")

    # 주요 컬럼만 표시
    df_display = df[[
        "bidNtceNo", "bidNtceNm", "bsnsDivNm", "ntceInsttNm",
        "bidNtceDate", "bidClseDate", "bidNtceUrl"
    ]].rename(columns={
        "bidNtceNo": "입찰공고번호",
        "bidNtceNm": "입찰공고명",
        "bsnsDivNm": "업무구분명",
        "ntceInsttNm": "공고기관명"
        "bidNtceDate": "입찰공고일자",
        "bidClseDate": "입찰마감일자",
        "bidNtceUrl": "입찰공고URL"
    })

    # 검색 필터
    keyword = st.text_input("🔍 공고명/기관명 검색")
    if keyword:
        df_display = df_display[
            df_display["입찰공고명"].str.contains(keyword, case=False, na=False) |
            df_display["공고기관명"].str.contains(keyword, case=False, na=False)
        ]

    st.dataframe(df_display, use_container_width=True)

except Exception as e:
    st.error(f"❌ 데이터 로딩 실패: {e}")
