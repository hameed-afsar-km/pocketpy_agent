# PocketPy Vibe Coding Agent

**GSoC 2026 · Python Software Foundation · [PocketPy](https://pocketpy.dev)**

> An AI-powered agent that generates, validates, debugs, and iteratively improves
> **PocketPy-compatible**, text/ASCII-grid Python games from natural language prompts.

---

## About

This project is an open-source contribution to the
[PocketPy](https://github.com/pocketpy/pocketpy) ecosystem under
**Google Summer of Code 2026**, mentored by the Python Software Foundation.

PocketPy is a lightweight, embeddable Python 3.x interpreter written in C++,
designed to run on constrained devices, game engines, and embedded systems.
This agent demonstrates AI-driven code generation targeting the PocketPy runtime —
producing pure-Python, text/grid-based games that run both in CPython and in PocketPy.

---

## Features

| Feature | Description |
|---|---|
| 🤖 **AI Game Generation** | Natural language → complete PocketPy game in seconds |
| 🔁 **Multi-iteration Debug Loop** | Automatically fixes runtime errors up to N times |
| 🔄 **Smart Continue Mode** | `improve_code` pipeline for incremental refinement |
| 🛡️ **Pygame/GUI Guard** | Rejects any non-PocketPy import before execution |
| 💾 **Project Memory** | Full JSON history per project — prompts, code, errors |
| 📋 **Project Browser** | List all projects with status, timestamp, iterations |
| 🔑 **Hot-swap API Key** | Switch Gemini key mid-session without restarting |
| 🧠 **Multi-provider** | Gemini, OpenAI, Ollama — one config change |
| 🐍 **PocketPy Compatible** | All generated code uses only pure Python builtins |
| 🕹️ **NPC Demo** | Live Gemini-powered AI NPC on a text grid (`templates/`) |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/hameed-afsar/pocketpy_agent.git
cd pocketpy_agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
echo "GEMINI_API_KEY=your_key_here" > .env

# 4. Run the agent
python main.py
```

---

## Menu

```
  1. New Project      Generate a game from a prompt
  2. Continue Project Improve an existing project
  3. Run Project      Run any project
  4. List Projects    Browse all projects
  5. Project History  Iteration log for a project
  6. View Code        Preview latest generated code
  7. Update API Key   Hot-swap Gemini API key
  8. Exit
```

---

## Running a Generated Game

After generation, each game is saved to:

```
workspaces/<project_name>/main.py
```

Run it:

```bash
python workspaces/<project_name>/main.py
```

Or load it inside PocketPy:

```c
pkpy_exec(vm, source_code);
```

---

## AI Providers

Set `provider` in `config.json`:

```json
{
  "provider": "gemini",
  "gemini_model": "gemini-2.5-flash",
  "openai_model": "gpt-4o",
  "ollama_model": "llama3",
  "max_iterations": 5,
  "execution_timeout": 5
}
```

| Provider | Env var needed |
|---|---|
| `gemini` | `GEMINI_API_KEY` |
| `openai` | `OPENAI_API_KEY` |
| `ollama` | None (local server) |

---

## Architecture

```
pocketpy_agent/
├── main.py                       ← CLI entry point (7-option menu)
├── config.json                   ← Provider & model settings
├── requirements.txt
│
├── agent/
│   ├── core.py                   ← CoreAgent (new_project / improve_project)
│   ├── planner.py                ← Compiles user prompt into PocketPy game spec
│   └── executor.py               ← Wraps evaluation result from VirtualContainer
│
├── ai/
│   ├── base_provider.py          ← Abstract AI provider interface
│   ├── prompts.py                ← Centralised PocketPy system prompts
│   ├── gemini_provider.py        ← Google Gemini (google-genai SDK)
│   ├── openai_provider.py        ← OpenAI (openai SDK)
│   └── ollama_provider.py        ← Local Ollama (requests)
│
├── container/
│   └── virtual_container.py      ← exec()-based sandbox + Pygame guard
│
├── memory/
│   └── memory_manager.py         ← JSON history, list_projects, summaries
│
├── utils/
│   └── logger.py                 ← Structured logging
│
├── templates/
│   ├── ai_npc_demo.py            ← Gemini-powered AI NPC on a text grid
│   ├── snake/                    ← Reference snake game template
│   └── flappy/                   ← Reference flappy bird template
│
└── workspaces/
    └── <project_name>/
        └── main.py               ← Generated game (run directly)
```

---

## PocketPy Constraints (Enforced)

The agent's system prompts and the VirtualContainer guard together enforce:

- ✅ Only `math`, `random`, `sys`, `time`, `collections`, `bisect`, `operator`
- ✅ ASCII/text rendering via `print()`
- ✅ Input via `input()` with w/a/s/d or menu commands
- ✅ Grid state as `list[list[str]]`
- ❌ No `pygame`, `tkinter`, `wx`, `PyQt`, `kivy`
- ❌ No `subprocess`, `threading`, `multiprocessing`, `socket`

---

## What `templates/ai_npc_demo.py` Is

`ai_npc_demo.py` is a **standalone reference implementation** demonstrating how to
integrate Gemini as a "primitive AI NPC" decision-maker in a PocketPy-compatible
text-grid game. It is **not** a template used by the generator — it is an interactive
demo you can run directly to see the full Gemini + PocketPy loop in action.

The NPC (@) queries Gemini every N turns to decide its next move (UP/DOWN/LEFT/RIGHT).
If no API key is available it falls back to a built-in Manhattan-distance heuristic.

Run it:

```bash
python templates/ai_npc_demo.py
```

---

## GSoC 2026 Context

This repository demonstrates:

1. **AI-driven PocketPy code generation** — validated, iterable, provider-agnostic
2. **PocketPy runtime compatibility** — all outputs work in the embeddable interpreter
3. **Open tooling for the PocketPy ecosystem** — lowers the barrier for developers
   to build and test games targeting constrained/embedded environments

---

## License

MIT License © 2026

---

*Built with ❤️ for the Python Software Foundation and the PocketPy community.*
