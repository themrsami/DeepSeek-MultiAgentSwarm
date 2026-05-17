from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from typing import List, Optional, Dict, Any

from auth import load_auth
from deepseek_cli import DeepSeekAgent, run_swarm

app = FastAPI(
    title="DeepSeek Swarm API",
    description="REST API wrapper for the DeepSeek MultiAgent Swarm CLI",
    version="1.0.0"
)

# We initialize a global boss agent for single-agent requests
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

class ChatRequest(BaseModel):
    prompt: str
    swarm_mode: bool = False
    num_workers: int = 4
    thinking_enabled: bool = False
    search_enabled: bool = False
    model_class: str = "deepseek_chat"  # or deepseek_reasoner
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

    # Configure Boss agent based on request
    boss_agent.thinking_enabled = req.thinking_enabled
    boss_agent.search_enabled = req.search_enabled
    boss_agent.model_class = req.model_class
    
    if req.swarm_mode:
        if not (2 <= req.num_workers <= 6):
            raise HTTPException(status_code=400, detail="num_workers must be between 2 and 6")
            
        try:
            # Run the swarm in headless mode
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
            ans = boss_agent.send_message(req.prompt, return_text=True)
            return {
                "status": "success",
                "data": {
                    "boss_response": ans,
                    "worker_responses": []
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

if __name__ == "__main__":
    print("Starting API Server on http://localhost:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
