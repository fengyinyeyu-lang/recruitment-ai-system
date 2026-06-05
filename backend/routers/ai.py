"""AI 助手路由 - 普通对话、RAG 增强对话、智能体对话、追问推荐、知识库重建"""
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.dependencies import get_current_user
from backend.schemas.models import ChatRequest, ChatResponse, ApiResponse, AgentChatRequest

router = APIRouter(prefix="/api/ai", tags=["AI 助手"])


@router.post("/chat", response_model=ApiResponse)
def chat(req: ChatRequest, username: str = Depends(get_current_user)):
    """普通对话"""
    from src.llm_service.chat_api import chat_with_llm

    try:
        reply = chat_with_llm(req.message, history=req.history)
        return ApiResponse(data=ChatResponse(reply=reply).model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")


@router.post("/rag-chat", response_model=ApiResponse)
def rag_chat(req: ChatRequest, username: str = Depends(get_current_user)):
    """RAG 增强对话"""
    from src.llm_service.rag_engine import rag_chat as do_rag_chat

    try:
        reply, sources = do_rag_chat(req.message, history=req.history)
        # 序列化 sources
        serializable_sources = []
        for s in sources:
            serializable_sources.append({
                "title": s.get("title", ""),
                "content": s.get("content", ""),
                "score": round(float(s.get("score", 0)), 4),
            })
        return ApiResponse(data=ChatResponse(
            reply=reply,
            sources=serializable_sources,
        ).model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG 对话失败: {str(e)}")


@router.get("/followup", response_model=ApiResponse)
def get_followup(username: str = Depends(get_current_user)):
    """获取追问推荐"""
    from src.llm_service.prompts import get_random_prompts

    prompts = get_random_prompts(2)
    return ApiResponse(data={"questions": prompts})


@router.post("/rebuild-rag", response_model=ApiResponse)
def rebuild_rag(username: str = Depends(get_current_user)):
    """重建 RAG 知识库"""
    from src.llm_service.rag_engine import build_knowledge_base, get_rag_engine

    try:
        build_knowledge_base()
        engine = get_rag_engine()
        engine.rebuild_embeddings()
        return ApiResponse(data={"status": "ok"}, message="RAG 知识库重建完成")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识库重建失败: {str(e)}")


@router.post("/agent-chat", response_model=ApiResponse)
def agent_chat(req: AgentChatRequest, username: str = Depends(get_current_user)):
    """智能体对话（调用百炼智能体应用）"""
    from src.llm_service.chat_api import chat_with_agent

    try:
        reply, session_id = chat_with_agent(req.message, session_id=req.session_id)
        return ApiResponse(data=ChatResponse(
            reply=reply,
            sources=[],
            session_id=session_id,
        ).model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能体对话失败: {str(e)}")


@router.post("/agent-chat-stream")
async def agent_chat_stream(req: AgentChatRequest, username: str = Depends(get_current_user)):
    """智能体流式对话（SSE）"""
    from src.llm_service.chat_api import chat_with_agent_stream
    import asyncio

    async def event_generator():
        for chunk in chat_with_agent_stream(req.message, session_id=req.session_id):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            # 让出事件循环，确保数据立即 flush
            await asyncio.sleep(0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
