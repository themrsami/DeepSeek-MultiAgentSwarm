# DeepSeek MultiAgent Swarm CLI 🧠⚡

A powerful terminal-based CLI for interacting with DeepSeek AI, featuring **Grok-style multi-agent orchestration**, real-time streaming, and smart session management.

## Features

- 🤖 **Direct DeepSeek Chat** — Talk to DeepSeek directly from your terminal with full context memory
- 🧠 **Grok-Style Swarm Mode** — 4 Worker agents brainstorm simultaneously, then a Boss agent synthesizes the ultimate answer
- 🔀 **Model Switching** — Toggle between Instant and Expert models on the fly
- 💭 **DeepThink (R1)** — Enable deep reasoning mode for complex problems
- 🔍 **Web Search** — Let DeepSeek search the web for real-time information
- 🎨 **Color-Coded UI** — Beautiful ANSI-colored terminal interface with live status indicators
- 🧹 **Auto-Cleanup** — All temporary sessions are automatically deleted on exit

## Quick Start

### Prerequisites
```bash
pip install requests wasmtime numpy
```

### Run
```bash
python deepseek_cli.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/think` | Toggle DeepThink (R1) reasoning mode |
| `/search` | Toggle web search capability |
| `/expert` | Switch to Expert model |
| `/instant` | Switch to Instant (fast) model |
| `/swarm` | Toggle Grok-style multi-agent orchestration |
| `/exit` | Quit and auto-cleanup all sessions |

## How Swarm Mode Works

```
┌──────────────┐
│   Your Prompt │
└──────┬───────┘
       │
  ┌────┴────┐
  │ Dispatch │
  └────┬────┘
       │
 ┌─────┼─────┬──────┐
 ▼     ▼     ▼      ▼
W1    W2    W3     W4    ← 4 Workers (parallel)
 │     │     │      │
 └─────┼─────┴──────┘
       │
  ┌────┴────┐
  │  Boss   │  ← Synthesizes all 4 responses
  └────┬────┘
       │
  ┌────┴─────┐
  │ Final    │
  │ Answer   │
  └──────────┘
```

Each worker analyzes from a unique angle:
1. **Factual & Analytical** — Direct, data-driven breakdown
2. **Creative & Unconventional** — Out-of-the-box thinking
3. **Edge Cases & Risks** — Identifies pitfalls and downsides
4. **Practical Summary** — Core essence with real-world examples

## Authentication

This CLI reuses your existing DeepSeek browser session. You need to extract your `userToken` and cookies from your logged-in browser session and update the values in `deepseek_cli.py`.

## License

MIT
