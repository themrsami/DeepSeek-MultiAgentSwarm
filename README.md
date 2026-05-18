# DeepSeek MultiAgent Swarm (CLI & API) 🧠🤖

A powerful, dual-mode system for interacting with DeepSeek AI. It features a **Stealth Auto-Login Authentication**, **Grok-style multi-agent orchestration**, a beautiful Terminal UI, and a fully functional **FastAPI REST server** for integrating DeepSeek into your own apps!

## ✨ Features

- **Dual Mode Architecture** 🔄 – Run as a beautiful interactive Terminal CLI, or start the headless REST API server to consume it in your web/mobile apps.
- **Stealth Playwright Login** 🕵️‍♂️ – Zero manual token extraction! Type `/login` to open a secure, Cloudflare-bypassing browser, log in normally, and the script auto-saves your encrypted tokens persistently.
- **Grok-Style Swarm Mode** 🐝 – Multiple Worker agents brainstorm simultaneously, then a Boss agent synthesizes the ultimate, comprehensive answer.
- **DeepThink (R1) & Web Search** 🔍 – Toggle deep reasoning mode or live internet search capabilities on the fly.
- **Smart Data Controls** 🗑️ – Added a `/clearall` command (and API endpoint) to permanently wipe all chat history from your DeepSeek account to protect privacy.
- **Color-Coded UI** 🎨 – High-quality ANSI-colored terminal interface using the `rich` library.

---

## 🚀 Quick Start (Installation)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. First-Time Setup (Login)
You must log in at least once to generate the persistent `.ds_auth.json` credentials file.
```bash
python deepseek_cli.py
```
*Inside the CLI, type `/login` and follow the browser prompts.*

---

## 💻 Mode 1: Interactive CLI

Run the CLI for personal terminal usage:
```bash
python deepseek_cli.py
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `/think` | Toggle DeepThink (R1) reasoning mode |
| `/search` | Toggle web search capability |
| `/expert` | Switch to Expert model |
| `/instant` | Switch to Instant (fast) model |
| `/swarm` | Toggle multi-agent swarm mode |
| `/agents N` | Set number of swarm workers (2-6) |
| `/login` | Launch stealth browser to login |
| `/logout` | Delete local credentials |
| `/clearall` | **Permanently delete ALL chats from DeepSeek account** |
| `/exit` | Quit the CLI |

---

## 🌐 Mode 2: REST API Server

Integrate the Swarm system into your own applications!

### Starting the Server
```bash
uvicorn api:app --reload
```
The server will start at `http://localhost:8000`.

### 🌍 Exposing the API Globally (ngrok)
To use this API in a live web app (React, Vercel, etc.) or access it from anywhere in the world, you can expose your local server using **ngrok**:

1. Install ngrok from [ngrok.com](https://ngrok.com/).
2. Add your auth token (only needed once):
   ```bash
   ngrok config add-authtoken YOUR_NGROK_TOKEN
   ```
3. Run ngrok to expose port 8000. You can claim a **free static domain** in the ngrok dashboard so your API URL never changes:
   ```bash
   ngrok http --domain=your-custom-name.ngrok-free.app 8000
   ```
Now your API is permanently live at `https://your-custom-name.ngrok-free.app/chat` and can be fetched from anywhere!


### API Endpoints

#### 1. Health Check
- **Endpoint:** `GET /`
- **Response:**
  ```json
  {
    "status": "running",
    "auth_status": "Logged In"
  }
  ```

#### 2. Chat / Swarm Mode
- **Endpoint:** `POST /chat`
- **Headers:** `Content-Type: application/json`
- **Payload:**
  ```json
  {
    "prompt": "Your question here",
    "swarm_mode": true,
    "num_workers": 4,
    "thinking_enabled": true,
    "search_enabled": false,
    "model_class": "deepseek_chat",
    "context_summary": "Pass previous chat history here for memory."
  }
  ```
- **Response Example:**
  ```json
  {
    "status": "success",
    "data": {
      "boss_response": "The final synthesized answer...",
      "worker_responses": [
         {"worker": "Worker-1", "response": "Analysis from angle 1..."},
         {"worker": "Worker-2", "response": "Analysis from angle 2..."}
      ]
    }
  }
  ```

#### 3. Delete All Chats (Data Control)
- **Endpoint:** `DELETE /chats`
- **Description:** Permanently wipes all chat history from your DeepSeek account.
- **Response:**
  ```json
  {
    "status": "success",
    "message": "All chats have been permanently deleted."
  }
  ```

---

## 🔌 Mode 3: OpenAI-Compatible Endpoint (Cursor / Claude Code)

This API also exposes a **fully OpenAI-compatible** `/v1/chat/completions` endpoint with **SSE Streaming** support. This means you can use it as a drop-in replacement for OpenAI in any tool that supports custom API providers.

#### List Models
- **Endpoint:** `GET /v1/models`
- **Response:** Returns `deepseek-chat` and `deepseek-reasoner`.

#### Chat Completions (Streaming & Non-Streaming)
- **Endpoint:** `POST /v1/chat/completions`
- **Payload (OpenAI format):**
  ```json
  {
    "model": "deepseek-chat",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Write a Python function to sort a list."}
    ],
    "stream": true
  }
  ```
- **Models:** Use `deepseek-chat` (Instant) or `deepseek-reasoner` (Expert/R1).

### 🖥️ Setup in Cursor IDE
1. Open **Cursor Settings** → **Models** → **Add Model**.
2. Set:
   - **Model Name:** `deepseek-chat`
   - **API Base URL:** `http://localhost:8000/v1`  
     *(or your ngrok URL: `https://your-name.ngrok-free.app/v1`)*
   - **API Key:** `sk-anything` *(any non-empty string works, our server doesn't check keys)*
3. Click **Save**. Now select `deepseek-chat` as your model in Cursor and start coding!

### 🤖 Setup in Claude Code (CLI)
Add this to your Claude Code config (or set environment variables):
```bash
export OPENAI_API_BASE="http://localhost:8000/v1"
export OPENAI_API_KEY="sk-anything"
export OPENAI_MODEL="deepseek-chat"
```
Or if using ngrok:
```bash
export OPENAI_API_BASE="https://your-name.ngrok-free.app/v1"
export OPENAI_API_KEY="sk-anything"
export OPENAI_MODEL="deepseek-chat"
```

### 🧪 Quick Test (curl)
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

---

## 🧠 How Swarm Mode Works

```
╭───────────────────────────────────────────────────╮
│                  Your Prompt                      │
╰───────────────────────────────────────────────────╯
                         │
        ╭────────────────┴────────────────╮
        │          Dispatching            │
        ╰────────────────┬────────────────╯
                         │
  ╭───────┬──────────────┼──────────────┬───────╮
  │       │              │              │       │
 W1      W2             W3             W4      W5  (Parallel Processing)
  │       │              │              │       │
  ╰───────┴──────────────┼──────────────┴───────╯
                         │
        ╭────────────────┴────────────────╮
        │       Boss Synthesizes          │
        ╰────────────────┬────────────────╯
                         │
╭───────────────────────────────────────────────────╮
│                  Final Answer                     │
╰───────────────────────────────────────────────────╯
```

## License

MIT

