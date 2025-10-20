"""
역할 :
- 개발 환경에서 FastAPI 앱을 빠르게 띄우기 위한 진입점
- uvicorn을 코드에서 직접 실행
"""

import uvicorn
from app.core.config import get_settings

if __name__ == "__main__":
  settings = get_settings()
  uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=settings.port,
    reload=True # 개발 편의성: 코드 변경 시 자동 재기동
  )