from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.ai.deepseek_client import DeepSeekClient
from backend.persistence.database import get_session
from backend.persistence.models import Recommendation, Stock

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


@router.post("/ai/chat")
async def ai_chat(body: ChatRequest, request: Request):
    config = request.app.state.config
    client = DeepSeekClient(
        api_key=config.ai.api_key,
        base_url=config.ai.base_url,
        model=config.ai.model,
        max_tokens=config.ai.max_tokens,
        temperature=config.ai.temperature,
        max_concurrent=config.ai.rate_limit.max_concurrent,
    )

    session = get_session()
    context_parts = []
    try:
        latest = session.query(Recommendation.trade_date).order_by(Recommendation.trade_date.desc()).first()
        trade_date = str(latest[0]) if latest else str(date.today())
        top_recs = (
            session.query(Recommendation)
            .filter(Recommendation.trade_date == trade_date)
            .order_by(Recommendation.composite_score.desc())
            .limit(10).all()
        )
        for rec in top_recs:
            s = session.query(Stock).filter(Stock.symbol == rec.symbol).first()
            name = s.name if s else rec.symbol
            context_parts.append(
                f"{name}({rec.symbol}): 评分{rec.composite_score:.0f}, "
                f"风险{rec.risk_level}, 预测收益{rec.predicted_return:.1f}%"
            )
    finally:
        session.close()

    context = "\n".join(context_parts)

    system_prompt = (
        "你是鲸灵宝AI选股助手，基于DeepSeek大模型。你的回答基于量化因子模型（60%）、"
        "机器学习预测（30%）和事件驱动分析（10%）的三层选股引擎。"
        "回答风格：专业、简洁、数据驱动。用中文回复。"
        f"\n\n当前Top10推荐标的：\n{context}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": body.question},
    ]

    async def generate():
        async for token in client.chat_stream(messages):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
