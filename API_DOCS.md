# DeepSeek Swarm API Documentation

This API wraps the DeepSeek Multi-Agent Swarm system, allowing you to use complex reasoning and multi-agent workflows in any external application (React, Next.js, Mobile Apps, etc.).

## 1. Prerequisites (First-time Setup)
Before starting the API, you must log in at least once using the interactive CLI to generate the `.ds_auth.json` credentials file.
```bash
python deepseek_cli.py
# Type /login and follow the browser prompts.
```

## 2. Starting the Server
Open a terminal in the project directory and run the FastAPI server:
```bash
uvicorn api:app --reload
```
The server will start at `http://localhost:8000`.

## 3. Global Access (ngrok)
To expose this API to the internet permanently:
```bash
ngrok http --domain=YOUR_DOMAIN.ngrok-free.dev 8000
```
Your global API endpoint will be `https://YOUR_DOMAIN.ngrok-free.dev/chat`.

---

## 4. API Endpoints

### Health Check
- **Endpoint:** `GET /`
- **Description:** Checks if the server is running and if the auth token is present.
- **Response:**
  ```json
  {
    "status": "running",
    "auth_status": "Logged In"
  }
  ```

### Chat / Swarm Mode
- **Endpoint:** `POST /chat`
- **Headers:** `Content-Type: application/json`
- **Payload:**
  ```json
  {
    "prompt": "Your question here",
    "swarm_mode": true,          // true for multi-agent, false for single boss
    "num_workers": 4,            // between 2 and 6 (only if swarm_mode is true)
    "thinking_enabled": true,    // enables R1 DeepThink reasoning
    "search_enabled": false,     // enables Web Search
    "model_class": "deepseek_chat", // "deepseek_chat" (Instant) or "deepseek_reasoner" (Expert)
    "context_summary": ""        // Pass previous chat history here for context
  }
  ```

### Example Usage (JavaScript / fetch)
```javascript
const response = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        prompt: "Write a React component for a login form.",
        swarm_mode: false,
        thinking_enabled: false
    })
});

const json = await response.json();
console.log("Boss Answer:", json.data.boss_response);
```

### Example Usage (Python / requests)
```python
import requests

payload = {
    "prompt": "Brainstorm 3 app ideas",
    "swarm_mode": True,
    "num_workers": 3,
    "thinking_enabled": True
}
res = requests.post("http://localhost:8000/chat", json=payload)
data = res.json()

print(data["data"]["boss_response"])
for worker in data["data"]["worker_responses"]:
    print(worker["worker"], ":", worker["response"])
```

## 5. Notes & Limitations
- **Timeout:** Swarm mode with 4+ workers can take 30-60 seconds to process. Ensure your frontend HTTP client does not timeout prematurely.
- **Context:** The API is stateless. It does not remember past messages. You must send previous conversation history via the `context_summary` field.

### Delete All Chats
- **Endpoint:** `DELETE /chats`
- **Description:** Permanently deletes all chat history from your DeepSeek account (Data Controls).
- **Response:**
  ``json
  {
    "status": "success",
    "message": "All chats have been permanently deleted."
  }
  ``

