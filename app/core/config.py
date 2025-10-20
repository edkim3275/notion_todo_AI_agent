"""
역할 : 
- .env 파일 및 OS 환경변수를 로딩하여 애플리케이션 전역에서 사용할 설정 값을 제공
- 현재 단계에서는 꼭 필요한 최소 키만을 사용
주의 :
- 민감 정보는 절대 코드에 하드코딩하지 말고 .env 또는 배포 환경변수로 주입
"""

from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

@dataclass(frozen=True)
class Settings:
  tz: str = os.getenv("TZ", "Asia/Seoul")
  port: int = int(os.getenv("PORT", "8000"))
  notion_token: str | None = os.getenv("NOTION_TOKEN")
  notion_tasks_db_id: str | None = os.getenv("NOTION_TASKS_DB_ID")

def get_settings() -> Settings:
  """
  Settings 객체를 반환
  - 함수로 감싸두면 추후 DI나 테스트 시에 주입하기가 용이해짐
  """
  return Settings()