"""
역할 :
- FastAPI 애플리케이션 인스턴스를 생성하고 라우터를 등록
"""

from fastapi import FastAPI
from app.api.v1.routers import v1_router
from app.core.config import get_settings

def create_app() -> FastAPI:
  settings = get_settings()

  app = FastAPI(
    title="Notion Tasks Chatbot(Mini)",
    version="1.0.0",
    description="개인용 Notion Tasks 챗봇"
  )

  # 라우터 바인딩
  app.include_router(v1_router)

  # 루트 헬스체크
  @app.get("/")
  def root() -> dict:
    return {
      "ok": True,
      "message": "Notion Tasks Chatbot server is running.",
      "tz": settings.tz
    }
  
  return app

# uvicorn을 직접 실행하는 경우를 고려하여 전역 app심볼도 노출
app = create_app()