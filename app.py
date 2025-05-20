import streamlit as st
import pandas as pd
import psycopg2
import json
import os
from dotenv import load_dotenv

# 환경변수 불러오기
load_dotenv()
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

# DB 연결 및 데이터 로딩
def load_data():
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT raw FROM bids_live ORDER BY raw->>'bidNtceBgnDt' DESC LIMIT 100")
    rows = cur.fetchall()
    conn.close()

    # raw JSONB → pandas DataFrame 변환
    raw_data = [json.loads(row[0]) for row in rows]
    df = pd.json_normalize(raw_data)
    return df

# Streamlit UI
st.set_page_config(page_title="입찰 공고 실시간 조회", layout="wide")
st.title("\U0001F4E2 나라장터 실시간 입찰 공고")

try:
    df = load_data()
    st.success(f"총 {len(df)}건의 공고 불러옴")

    # 주요 컬럼만 표시
    df_display = df[[
        "bidNtceNo", "bidNtceNm", "ntceInsttNm", "bsnsDivNm",
        "bidNtceDate", "bidClseDate", "bidNtceUrl"
    ]].rename(columns={
        "bidNtceNo": "공고번호",
        "bidNtceNm": "공고명",
        "ntceInsttNm": "기관명",
        "bsnsDivNm": "구분",
        "bidNtceDate": "게시일",
        "bidClseDate": "마감일",
        "bidNtceUrl": "공고링크"
    })

    keyword = st.text_input("\U0001F50D 공고명/기관 검색")
    if keyword:
        df_display = df_display[
            df_display["공고명"].str.contains(keyword, case=False, na=False) |
            df_display["기관명"].str.contains(keyword, case=False, na=False)
        ]

    st.dataframe(df_display, use_container_width=True)

except Exception as e:
    st.error(f"❌ 데이터 로딩 실패: {e}")
