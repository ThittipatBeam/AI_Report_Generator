import time
import os
import json
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator

from backend.config import settings
from backend.graph import run_agentic_rag_pipeline, agent_pipeline_graph

app = FastAPI(
    title="Agentic AI Report Generator Backend",
    description="FastAPI service exposing OpenAI-compatible API for LangGraph Agent Pipeline",
    version="1.0.0"
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Agentic AI Report Generator API",
        "display_model": settings.DISPLAY_MODEL_NAME,
        "target_model": settings.OPENAI_MODEL,
        "llm_provider": settings.LLM_PROVIDER,
        "base_url": settings.OPENAI_BASE_URL
    }

@app.get("/v1/models")
def list_models():
    """
    OpenAI-compatible models list endpoint for Open WebUI discovery.
    """
    display_id = settings.DISPLAY_MODEL_NAME
    return {
        "object": "list",
        "data": [
            {
                "id": display_id,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "bbl-agent-team",
                "permission": [],
                "root": display_id,
                "parent": None
            }
        ]
    }

async def generate_stream_agent_response(user_query: str, request_model: str) -> AsyncGenerator[str, None]:
    """
    Executes LangGraph 2-Agent pipeline and streams the output to Open WebUI.
    """
    chat_id = f"chatcmpl-{int(time.time())}"
    
    try:
        # Run the full LangGraph 2-Agent Workflow
        final_report = run_agentic_rag_pipeline(user_query)
        
        # Stream the synthesized report in token chunks for smooth Web UI rendering
        chunk_size = 15
        for i in range(0, len(final_report), chunk_size):
            token_chunk = final_report[i:i+chunk_size]
            payload = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request_model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": token_chunk},
                        "finish_reason": None
                    }
                ]
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0.01)

        # Final stop payload
        stop_payload = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": request_model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ]
        }
        yield f"data: {json.dumps(stop_payload)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        print(f"Error executing LangGraph pipeline: {e}")
        error_payload = {
            "error": {"message": str(e), "type": "server_error"}
        }
        yield f"data: {json.dumps(error_payload)}\n\n"
        yield "data: [DONE]\n\n"

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint that invokes the LangGraph 2-Agent Pipeline!
    """
    user_query = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_query = msg.content
            break
            
    if not user_query:
        user_query = "Hello"

    request_model = request.model or settings.DISPLAY_MODEL_NAME

    # Stream response to Open WebUI
    if request.stream:
        return StreamingResponse(
            generate_stream_agent_response(user_query, request_model),
            media_type="text/event-stream"
        )

    # Non-streaming response
    try:
        final_report = run_agentic_rag_pipeline(user_query)
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request_model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": final_report
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 200,
                "total_tokens": 250
            }
        }
    except Exception as e:
        print(f"Error executing LangGraph agent pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Agent Pipeline Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
