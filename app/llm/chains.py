"""
app/llm/chains.py

역할:
- LLM + Tools를 결합해 '함수호출 기반' 에이전트를 구성한다.
- 1회 호출 원칙을 프롬프트로 유도하고, 실행 레벨에선 max_iterations를 1로 제한한다.

전제:
- GOOGLE_API_KEY .env/환경변수에 있어야 한다.
- 모델명은 GEMINI_MODEL(기본: gemini-2.5-flash)을 사용한다.
"""

from __future__ import annotations
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.llm.prompts import SYSTEM_PROMPT
from app.llm.tools import get_tools

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def build_agent() -> AgentExecutor:
    """
    OpenAI 함수호출 기반 에이전트를 구성해 반환한다.
    - 도구는 app.llm.tools.get_tools()에서 로드.
    - 프롬프트는 SYSTEM_PROMPT(한국어) 하나만 단순 적용.
    - max_iterations=1로 제한(단일 호출).
    """
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("GOOGLE_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    llm = ChatGoogleGenerativeAI(model=DEFAULT_MODEL, temperature=0)  # 결정적 응답 유도(툴 JSON 안정화)

    tools = get_tools()
    # ChatPromptTemplate로 시스템/휴먼 메시지를 구성
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    agent = create_openai_tools_agent(llm, tools, prompt)  # 도구 호출형 에이전트 생성
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=1,           # 단일 호출
        handle_parsing_errors=True  # 경미한 파싱 오류는 자동 복구
    )
    return executor