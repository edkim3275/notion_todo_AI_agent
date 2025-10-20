"""
app/core/time.py

역할:
- Asia/Seoul 등 지정된 타임존 기준의 '오늘 날짜'를 제공하고,
  한국어 상대 날짜(오늘/내일/모레/어제)를 간단 치환하는 유틸을 제공합니다.
- 개인용 최소 구성: 복잡한 자연어(다음주 금요일 등)는 다루지 않고, 핵심 키워드만 처리합니다.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

def today_date_str(tz_name: str = "Asia/Seoul") -> str:
    """
    지정한 타임존 기준의 오늘 날짜를 YYYY-MM-DD 문자열로 반환합니다.
    """
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d")

def normalize_korean_relative_dates(text: str, tz_name: str = "Asia/Seoul") -> str:
    """
    입력 문장 내의 간단한 한국어 상대 날짜를 절대 날짜(YYYY-MM-DD)로 치환합니다.
    - 지원 키워드: 오늘(0), 내일(+1), 모레(+2), 어제(-1)
    - '내일부터', '오늘은'처럼 조사/조사 결합은 남겨두고 핵심 단어만 치환합니다.
    - 개인용 최소 기능: 복잡한 표현(다음주 금요일, 다음 달 첫째 주 등)은 다루지 않습니다.
    """
    base = today_date_str(tz_name)
    base_dt = datetime.fromisoformat(base)

    repl = {
        "오늘": base_dt,
        "내일": base_dt + timedelta(days=1),
        "모레": base_dt + timedelta(days=2),
        "어제": base_dt - timedelta(days=1),
    }

    out = text
    for key, dt in repl.items():
        # 조사 결합을 고려해 'key'를 독립 토큰/연결 형태까지 포괄 치환
        # 예) "내일", "내일은", "내일부터" 에서 '내일'만 날짜로 바꿈
        out = re.sub(key, dt.strftime("%Y-%m-%d"), out)

    return out
