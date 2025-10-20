"""
역할 :
- v1 버전 라우터들을 모아서 앱에 연결하기 위한 엔트리
- 버전 관리를 위해 v1을 별도 모듈로 둠
- 현재는 notion 엔드포인트만 등록
"""

from fastapi import APIRouter
from .endpoints import notion

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(notion.router)