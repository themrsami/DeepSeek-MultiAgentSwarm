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

*(Optional: Use `ngrok http 8000` to expose this API to the internet permanently!)*

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
