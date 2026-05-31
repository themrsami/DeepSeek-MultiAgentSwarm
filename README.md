# 🧠 DeepSeek MultiAgent Swarm (CLI & Local API)

A powerful, dual-mode system designed to interact with DeepSeek AI. It serves as an **OpenAI-compatible Local API** for your favorite coding editors (Cursor, VS Code, T3 Code) and acts as a **Grok-style multi-agent CLI** orchestrator in your terminal. 

Bring the power of DeepSeek's Free Tier into your professional development workflow with zero friction!

---

## ✨ Key Features

- **🔌 Drop-in OpenAI Compatibility:** Exposes a fully compatible `/v1/chat/completions` API (with SSE streaming and `/v1/completions` autocomplete support) that works instantly with VS Code, Cursor, and T3 Code.
- **🕵️‍♂️ Stealth Auto-Login:** Zero manual token extraction! Use `/login` to open a secure browser, log in normally, and let the script handle Cloudflare bypass and session persistence.
- **🐝 Grok-Style Swarm Mode:** (CLI Mode) Spawn multiple worker agents to brainstorm simultaneously while a Boss agent synthesizes the final comprehensive answer.
- **🔍 DeepThink (R1) & Web Search:** Easily toggle DeepSeek's reasoning mode (R1) or live internet search capabilities.
- **🗑️ Smart Data Controls:** Need privacy? Permanently wipe all chat history from your DeepSeek account with a single command or API call.
- **🌍 Global Access (Ngrok):** Easily expose your local API to the web for mobile apps or external integrations.

---

## 🚀 Quick Start & Installation

### 1. Install Dependencies
Make sure you have Python 3 installed. Then run:
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. First-Time Authentication
You must log in at least once so the script can save your session credentials (`.ds_auth.json`).
```bash
python deepseek_cli.py
```
*Once the CLI starts, type `/login` and follow the browser prompts to log into your DeepSeek account.*

---

## 🛠️ Usage 1: AI Coding Assistant (IDE Integration)

You can use this project as a free backend for powerful AI coding tools like **Continue.dev**, **Cline**, **Cursor**, and **T3 Code**.

### Start the API Server
Leave this running in the background:
```bash
uvicorn api:app --reload
```
*The server will start on `http://localhost:8000`.*

### Setup Guides

#### 🟦 Continue.dev (VS Code) - *Recommended*
1. Install the [Continue](https://continue.dev/) extension in VS Code.
2. Open `~/.continue/config.json` (or click the gear icon in the extension).
3. Add the following to your `models` list:
```json
{
  "title": "DeepSeek Swarm",
  "provider": "openai",
  "model": "deepseek-chat",
  "apiBase": "http://localhost:8000/v1",
  "apiKey": "sk-anything"
}
```

#### ⬛ Cursor IDE
*Note: Cursor's free tier restricts custom API URLs. If you have the required plan:*
1. Open **Cursor Settings** → **Models** → **Add Model**.
2. **Model Name:** `deepseek-chat`
3. **API Base URL:** `http://localhost:8000/v1`
4. **API Key:** `sk-anything` (any string works)
5. Ensure **"Override OpenAI Base URL"** is toggled ON.

#### 🤖 Claude Code (CLI)
```bash
export OPENAI_API_BASE="http://localhost:8000/v1"
export OPENAI_API_KEY="sk-anything"
export OPENAI_MODEL="deepseek-chat"
claude
```

#### 💻 T3 Code (Desktop App)
In settings, select **OpenAI** as the provider, set the Base URL to `http://localhost:8000/v1`, Model to `deepseek-chat`, and enter any dummy API key.

---

## 💻 Usage 2: Interactive Terminal CLI

Prefer the terminal? Run the CLI to utilize the multi-agent Swarm mode!

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

### 🧠 How Swarm Mode Works
```text
╭───────────────────────────────────────────────────╮
│                  Your Prompt                      │
╰───────────────────────────────────────────────────╯
                         │
        ╭────────────────┴────────────────╮
        │          Dispatching            │
        ╰────────────────┬────────────────╯
                         │
  ╭───────┬──────────────┼──────────────┬───────╮
 W1      W2             W3             W4      W5  (Parallel Processing)
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

---

## 🌐 Usage 3: Expose API Globally (ngrok)

Want to use your API in a live web app or access it remotely? Expose your local port using [ngrok](https://ngrok.com/):

```bash
ngrok http --domain=your-custom-name.ngrok-free.app 8000
```
*Now your API is permanently live at `https://your-custom-name.ngrok-free.app/v1`!*

---

## 📜 API Endpoints Reference

If you are building your own tools, the REST server supports the following routes:

- `GET /v1/models`: Returns standard OpenAI-compatible model list (`deepseek-chat`, `deepseek-reasoner`).
- `POST /v1/chat/completions`: Standard chat completions with `stream: true` (SSE) and `stream: false` support.
- `POST /v1/completions`: Legacy text completions endpoint (often used for autocomplete tools).
- `POST /chat`: Custom Swarm endpoint (supports passing `swarm_mode: true` and `num_workers: 4`).
- `DELETE /chats`: Permanently wipes all chat history from your DeepSeek account.

---

## License
MIT
