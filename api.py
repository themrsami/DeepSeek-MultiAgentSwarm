from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn, json, time, uuid
from typing import List, Optional

from auth import load_auth
from deepseek_cli import DeepSeekAgent, run_swarm

app = FastAPI(
    title="DeepSeek Swarm API",
    description="REST API wrapper for the DeepSeek MultiAgent Swarm CLI — OpenAI Compatible",
    version="2.0.0"
)

boss_agent = None

@app.on_event("startup")
def startup_event():
    global boss_agent
    auth_data = load_auth()
    if not auth_data:
        print("[Warning] No authentication found. Please run '/login' via the CLI first.")
    else:
        boss_agent = DeepSeekAgent(name="Boss")
        try:
            boss_agent.init_session(silent=True)
            print("[System] API Boss Agent initialized successfully.")
        except Exception as e:
            print(f"[Error] Failed to initialize Boss session: {e}")

# ─── Custom Swarm Endpoint (Original) ───

class ChatRequest(BaseModel):
    prompt: str
    swarm_mode: bool = False
    num_workers: int = 4
    thinking_enabled: bool = False
    search_enabled: bool = False
    model_class: str = "deepseek_chat"
    context_summary: str = ""

@app.get("/")
def read_root():
    auth_status = "Logged In" if load_auth() else "Not Logged In"
    return {"status": "running", "auth_status": auth_status}

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    global boss_agent
    
    if not load_auth():
        raise HTTPException(status_code=401, detail="Not authenticated. Run CLI and type /login")
        
    if boss_agent is None:
        boss_agent = DeepSeekAgent(name="Boss")
        boss_agent.init_session(silent=True)

    boss_agent.thinking_enabled = req.thinking_enabled
    boss_agent.search_enabled = req.search_enabled
    boss_agent.model_class = req.model_class
    
    if req.swarm_mode:
        if not (2 <= req.num_workers <= 6):
            raise HTTPException(status_code=400, detail="num_workers must be between 2 and 6")
        try:
            result = run_swarm(
                prompt=req.prompt,
                context_summary=req.context_summary,
                boss_agent=boss_agent,
                num_workers=req.num_workers,
                cli_mode=False
            )
            return {"status": "success", "data": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Swarm failed: {str(e)}")
    else:
        try:
            final_prompt = req.prompt
            if req.context_summary:
                final_prompt = f"Previous Context:\n{req.context_summary}\n\nCurrent Task: {req.prompt}"
            ans = boss_agent.send_message(final_prompt, return_text=True)
            return {
                "status": "success",
                "data": {
                    "boss_response": ans,
                    "worker_responses": []
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

@app.delete("/chats")
def delete_all_chats():
    global boss_agent
    if not load_auth():
        raise HTTPException(status_code=401, detail="Not authenticated. Run CLI and type /login")
    if boss_agent is None:
        boss_agent = DeepSeekAgent(name="Boss")
        boss_agent.init_session(silent=True)
    success = boss_agent.delete_all_chats()
    if success:
        return {"status": "success", "message": "All chats have been permanently deleted."}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete chats. Token might be expired.")

# ─── OpenAI-Compatible Endpoint (/v1/chat/completions) ───
from fastapi import Request

@app.get("/v1/models")
def list_models():
    """Returns available models in OpenAI format."""
    return {
        "object": "list",
        "data": [
            {"id": "deepseek-chat", "object": "model", "owned_by": "deepseek"},
            {"id": "deepseek-reasoner", "object": "model", "owned_by": "deepseek"},
        ]
    }

@app.post("/v1/chat/completions")
async def openai_chat_completions(req: Request):
    global boss_agent
    
    if not load_auth():
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    if boss_agent is None:
        boss_agent = DeepSeekAgent(name="Boss")
        boss_agent.init_session(silent=True)

    try:
        data = await req.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    model_name = data.get("model", "deepseek-chat")
    messages = data.get("messages", [])
    stream = data.get("stream", False)

    # Map model name
    if "reasoner" in model_name or "r1" in model_name.lower():
        boss_agent.model_class = "deepseek_reasoner"
        boss_agent.thinking_enabled = True
    else:
        boss_agent.model_class = "deepseek_chat"
        boss_agent.thinking_enabled = False
    
    boss_agent.search_enabled = False

    # Convert messages array to single prompt (OpenAI -> DeepSeek)
    prompt_parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            prompt_parts.insert(0, f"System Instructions: {content}")
        elif role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
    
    final_prompt = "\n".join(prompt_parts)
    
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())

    if stream:
        # ── SSE Streaming Response ──
        def stream_generator():
            # Send initial chunk with role
            init_data = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "delta": {"role": "assistant", "content": ""},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(init_data)}\n\n"

            for chunk in boss_agent.send_message_stream(final_prompt):
                chunk_data = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": chunk},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            
            # Send the final [DONE] signal
            done_data = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(done_data)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        # ── Non-Streaming Response ──
        full_text = boss_agent.send_message(final_prompt, return_text=True)
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": model_name,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": full_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(final_prompt.split()),
                "completion_tokens": len(full_text.split()),
                "total_tokens": len(final_prompt.split()) + len(full_text.split())
            }
        }

@app.post("/v1/completions")
async def openai_completions(req: Request):
    """Legacy completions endpoint used by Continue autocomplete."""
    global boss_agent
    if boss_agent is None:
        boss_agent = DeepSeekAgent(name="Boss")
        boss_agent.init_session(silent=True)
        
    try:
        data = await req.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    prompt = data.get("prompt", "")
    stream = data.get("stream", False)
    model_name = data.get("model", "deepseek-chat")
    boss_agent.model_class = "deepseek_chat"
    boss_agent.thinking_enabled = False

    completion_id = f"cmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())

    if stream:
        def stream_generator():
            for chunk in boss_agent.send_message_stream(prompt):
                chunk_data = {
                    "id": completion_id,
                    "object": "text_completion",
                    "created": created,
                    "model": model_name,
                    "choices": [{"text": chunk, "index": 0, "finish_reason": None}]
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            done_data = {
                "id": completion_id,
                "object": "text_completion",
                "created": created,
                "model": model_name,
                "choices": [{"text": "", "index": 0, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(done_data)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        full_text = boss_agent.send_message(prompt, return_text=True)
        return {
            "id": completion_id,
            "object": "text_completion",
            "created": created,
            "model": model_name,
            "choices": [{"text": full_text, "index": 0, "finish_reason": "stop"}]
        }

if __name__ == "__main__":
    print("Starting API Server on http://localhost:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
