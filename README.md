# 🧠 DeepSeek MultiAgent Swarm (CLI & Local API)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)

A powerful, highly scalable, dual-mode system designed to interact with DeepSeek AI. It serves as an **OpenAI-compatible Local API** for your favorite coding editors (Cursor, VS Code, etc.) and acts as a **Grok-style multi-agent CLI** orchestrator in your terminal. 

Bring the power of DeepSeek's Free Tier into your professional development workflow, web applications, or mobile apps with zero friction!

---

## ✨ Comprehensive Feature List

- **🔌 Drop-in OpenAI Compatibility:** Exposes a fully compatible `/v1/chat/completions` API (with SSE streaming and `/v1/completions` autocomplete support). Drop this directly into VS Code or Cursor as if you were using OpenAI's paid API.
- **📱 Web & Mobile Ready:** Easily integrate DeepSeek intelligence into your own React, Flutter, or native apps using standard REST API calls.
- **🕵️‍♂️ Stealth Auto-Login Authentication:** Zero manual token extraction required! Use our `/login` command to open a secure browser, log in normally, and let the script handle Cloudflare bypass and encrypted session persistence automatically.
- **🐝 Grok-Style Swarm Mode:** (CLI Mode) Spawn multiple worker agents to brainstorm simultaneously from different perspectives while a Boss agent synthesizes the final comprehensive answer.
- **🔍 DeepThink (R1) & Web Search:** Easily toggle DeepSeek's reasoning mode (R1) or live internet search capabilities with simple parameters.
- **🗑️ Smart Data & Privacy Controls:** Need privacy? Permanently wipe all chat history from your DeepSeek account with a single command or API call.
- **🌍 Global Access via Ngrok:** Need to connect a mobile app being tested on a real device? Easily expose your local API to the web.

---

## 🚀 Step-by-Step Installation

### Step 1: Clone the Repository
Start by cloning the project to your local machine and navigating into the directory:
```bash
git clone https://github.com/themrsami/DeepSeek-MultiAgentSwarm.git
cd DeepSeek-MultiAgentSwarm
```

### Step 2: Install Dependencies
Ensure you have Python 3 installed. Then install the required Python packages and the Playwright browser binaries used for stealth authentication:
```bash
pip install -r requirements.txt
playwright install chromium
```

### Step 3: First-Time Authentication (Login)
You must log in at least once so the script can save your session credentials securely (`.ds_auth.json`).
Run the CLI application:
```bash
python deepseek_cli.py
```
*Once the CLI starts, type `/login` and hit Enter. A browser window will open. Log into your DeepSeek account manually. Once logged in, the script will automatically capture the session tokens and save them. You can now close the browser and use the app headlessly!*

---

## 🛠️ Usage Mode 1: AI Coding Assistant (IDE Integration)

You can use this project as a free backend for powerful AI coding tools. By mimicking OpenAI's API, these tools think they are talking to GPT-4, but they are actually talking to your local DeepSeek Swarm!

### Start the API Server
Open a terminal and leave this running in the background:
```bash
uvicorn api:app --reload
```
*The server will start on `http://localhost:8000`.*

### Editor Setup Guides

#### 🟦 Continue.dev (VS Code) - *Highly Recommended*
1. Install the [Continue](https://continue.dev/) extension in VS Code.
2. Open your Continue configuration file (usually click the gear icon in the extension).
3. Add the following to your `models` list:
```yaml
models:
  - name: DeepSeek Swarm
    provider: openai
    model: deepseek-chat
    apiBase: http://localhost:8000/v1
    apiKey: sk-anything
  - name: DeepSeek Reasoner (R1)
    provider: openai
    model: deepseek-reasoner
    apiBase: http://localhost:8000/v1
    apiKey: sk-anything
```

#### ⬛ Cursor IDE
*Note: Cursor's free tier restricts custom API URLs. If you have the required plan:*
1. Open **Cursor Settings** → **Models** → **Add Model**.
2. Add both models: `deepseek-chat` and `deepseek-reasoner`.
3. **API Base URL:** `http://localhost:8000/v1`
4. **API Key:** `sk-anything` (any string works)
5. Ensure **"Override OpenAI Base URL"** is toggled ON.

#### 🤖 Claude Code (CLI)
You can point Anthropic's official Claude Code CLI to your DeepSeek API (use either `deepseek-chat` or `deepseek-reasoner`):
```bash
export OPENAI_API_BASE="http://localhost:8000/v1"
export OPENAI_API_KEY="sk-anything"
export OPENAI_MODEL="deepseek-reasoner"
claude
```

---

## 📱 Usage Mode 2: Integrating with Web & Mobile Apps

You can easily build your own Web Apps (React, Vue, Next.js) or Mobile Apps (Flutter, React Native, iOS, Android) powered by this API. 

Since the API is 100% OpenAI compatible, you can use standard OpenAI SDKs or standard HTTP requests.

### Option A: Using the OpenAI SDK (Node.js / JavaScript)
If you are building a Node.js backend or a Next.js app, you can use the official `openai` package:

```javascript
import OpenAI from "openai";

const openai = new OpenAI({
  baseURL: "http://localhost:8000/v1", // Point to your local DeepSeek server
  apiKey: "sk-dummy-key", // Key is required by SDK but ignored by our server
});

async function getChatResponse() {
  const completion = await openai.chat.completions.create({
    model: "deepseek-chat", // or "deepseek-reasoner" for R1 DeepThink
    messages: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: "Explain quantum computing in simple terms." }
    ],
    stream: true, // Set to true for typing animations!
  });

  for await (const chunk of completion) {
    process.stdout.write(chunk.choices[0]?.delta?.content || "");
  }
}
getChatResponse();
```

### Option B: Using standard HTTP REST (Flutter / Dart)
If you are building a Flutter app, you can just make a standard POST request:

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<void> fetchDeepSeekResponse() async {
  final url = Uri.parse('http://10.0.2.2:8000/v1/chat/completions'); // 10.0.2.2 is localhost for Android Emulator
  
  final response = await http.post(
    url,
    headers: {"Content-Type": "application/json"},
    body: jsonEncode({
      "model": "deepseek-chat",
      "messages": [
        {"role": "user", "content": "Give me a healthy breakfast recipe."}
      ],
      "stream": false
    }),
  );

  if (response.statusCode == 200) {
    var data = jsonDecode(response.body);
    print(data['choices'][0]['message']['content']);
  }
}
```

---

## 🌍 Usage Mode 3: Expose API Globally (ngrok)

If your mobile app is running on a physical phone, or your web app is deployed on Vercel/Netlify, it cannot access `localhost:8000`. You need to expose your API to the internet using **ngrok**.

1. Download and install [ngrok](https://ngrok.com/).
2. Authenticate your ngrok account in the terminal:
   ```bash
   ngrok config add-authtoken YOUR_NGROK_TOKEN
   ```
3. Expose your server:
   ```bash
   ngrok http --domain=your-custom-name.ngrok-free.app 8000
   ```
4. Update your mobile/web app code to use `https://your-custom-name.ngrok-free.app/v1` instead of `http://localhost:8000/v1`!

---

## 💻 Usage Mode 4: Interactive Terminal CLI (Swarm Mode)

If you don't want to build an app and just want to use DeepSeek powerfully from your terminal, run the CLI:

```bash
python deepseek_cli.py
```

### Swarm Mode Architecture
When you enable Swarm Mode (`/swarm`), your prompt isn't just sent to one model. It is dispatched to a team of AI workers who analyze it from different perspectives. Finally, a Boss AI synthesizes their thoughts into the perfect answer.

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

### Built-in CLI Commands
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

## 📜 Full API Endpoints Reference

If you are building custom tools, here is the full API surface provided by `api.py`:

- `GET /v1/models`: Returns standard OpenAI-compatible model list (`deepseek-chat`, `deepseek-reasoner`).
- `POST /v1/chat/completions`: Standard OpenAI chat completions endpoint. Fully supports `stream: true` via Server-Sent Events (SSE).
- `POST /v1/completions`: Legacy text completions endpoint. Used heavily by code editors for inline autocomplete features.
- `POST /chat`: Custom REST endpoint built specifically for Swarm Mode. Accepts arguments like `swarm_mode: true` and `num_workers: 4`.
- `DELETE /chats`: Privacy endpoint. Permanently wipes all chat history from your DeepSeek account to ensure your local queries aren't saved on their servers.

---

## 🌟 Star History
*(Note: If the graph image below appears broken, it means the repository is too new or currently has 0 stars. The graph will automatically render once the project receives its first few stars!)*

[![Star History Chart](https://api.star-history.com/svg?repos=themrsami/DeepSeek-MultiAgentSwarm&type=Date)](https://star-history.com/#themrsami/DeepSeek-MultiAgentSwarm&Date)

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
