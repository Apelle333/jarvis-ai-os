# JARVIS AI OS

### A Local-First, Multi-Agent AI Desktop System

**Python · FastAPI · Ollama · Next.js · TypeScript · Tauri · Rust**

JARVIS AI OS is an independent AI engineering project inspired by Tony Stark's JARVIS.

It explores how locally hosted large language models can be integrated into a modular desktop application capable of handling natural-language requests, coordinating specialized agents, maintaining persistent memory, processing voice input, and interacting with the operating system.

Rather than relying on a single chatbot interface, JARVIS combines **LLM inference, task planning, agent orchestration, semantic memory, system automation, and real-time visualization** into one architecture.

> **Project Status:** Experimental prototype. Core components and integrations are implemented in the repository, but some features require additional configuration, testing, and security hardening. The project is intended for development, experimentation, and learning rather than production deployment.

---

## Overview

JARVIS is designed around a central Python orchestration layer that connects multiple subsystems:

- **Local AI inference:** Run language models through Ollama without relying on a cloud LLM provider.
- **Multi-agent architecture:** Coordinate specialized agents for different categories of tasks.
- **Task-aware model routing:** Select models according to task requirements and configured preferences.
- **Persistent memory:** Store conversations and retrieve relevant information through embeddings and vector search.
- **Voice interaction:** Process speech using Whisper and generate speech through Piper.
- **Computer interaction:** Connect AI requests to operating-system tools and automation.
- **Live system monitoring:** Display application and hardware status through a reactive interface.
- **Desktop integration:** Package the interface within a Tauri-based Windows desktop shell.

The project emphasizes the engineering challenges involved in connecting AI models to real software systems.

## System Architecture

```text
                 ┌──────────────────────┐
                 │    JARVIS Desktop    │
                 │   Next.js + React    │
                 │   TypeScript + UI    │
                 └──────────┬───────────┘
                            │
                    REST / WebSocket
                            │
                 ┌──────────▼───────────┐
                 │   FastAPI Backend    │
                 │      Python          │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │     JARVIS Brain     │
                 │ Central Orchestrator │
                 └──────────┬───────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
       Task Planner     Model Router    Memory Manager
            │               │               │
            ▼               ▼               ▼
       Swarm Manager       Ollama      SQLite / ChromaDB
            │               │               │
            ▼               ▼               ▼
      Specialized       Local LLMs      Embeddings
         Agents                        Semantic Search
            │
            ▼
       Tools & System
         Automation

         Tauri 2 + Rust Desktop Shell
```

### Request Processing

A typical user request follows this general path:

1. The user submits a request through the desktop interface or API.
2. The backend processes the request through the central JARVIS coordinator.
3. The planner analyzes the task.
4. The model router selects a configured local model.
5. Complex requests can be delegated to specialized agents.
6. Agents interact with the relevant models, memory, or tools.
7. Results are returned through the backend.
8. The frontend displays the response and available state information.

Certain recognized computer-control requests follow a more direct, rule-based execution path.

## Key Components

### 1. AI Model Routing

JARVIS implements a task-aware routing system for local LLM inference.

The model router provides:

- Model selection based on task categories.
- Configurable primary and fallback models.
- Availability checks against Ollama.
- Generation parameter configuration.
- Routing metadata for monitoring and debugging.

Model roles include general-purpose assistance, coding, reasoning, personality-related responses, and fast responses.

The routing system is configurable rather than being tied to one specific model.

**Implementation:** `backend/core/model_router.py`

### 2. Multi-Agent Orchestration

The system separates responsibilities across specialized agents.

| Agent | Responsibility |
|---|---|
| Main Agent | Conversational interaction and request handling |
| Coding Agent | Code-related assistance |
| Research Agent | Information gathering and analysis |
| Security Agent | Security-related analysis |
| System Agent | Operating-system interactions |
| Swarm Manager | Coordination and task distribution |

The Swarm Manager supports agent selection, task coordination, execution state tracking, and result handling.

This architecture provides a foundation for exploring more complex agent workflows.

**Implementation:** `backend/agents/`

### 3. Persistent Memory and Semantic Retrieval

JARVIS combines structured storage with vector-based retrieval.

**Short-term and structured memory**

SQLite supports conversation persistence and related application data.

**Long-term semantic memory**

The vector-memory subsystem uses:

- Sentence Transformers for text embeddings.
- ChromaDB for vector storage.
- Similarity-based retrieval.
- Knowledge storage and duplicate detection.
- Persistent local storage.

The implementation includes fallback behavior when its preferred embedding or vector-storage components are unavailable.

The hash-based embedding fallback is intended only as a functional fallback and is not equivalent to semantic embeddings.

**Implementation:** `backend/memory/`

### 4. Voice Processing

The repository contains a voice-processing pipeline built around locally executed speech models.

**Speech-to-Text**

- Open-source Whisper model integration.
- Audio transcription.
- Language support.
- Audio-processing utilities.

**Text-to-Speech**

- Piper TTS integration.
- Configurable voices.
- Speech synthesis.
- Local audio generation.

The voice API includes a pipeline connecting speech recognition, assistant processing, and speech synthesis.

Availability depends on the correct installation of local models, executables, and audio dependencies.

**Implementation:** `backend/voice/` and `backend/api/voice.py`

### 5. Computer Control and Automation

JARVIS includes modules designed to translate certain natural-language requests into computer actions.

The code covers areas such as:

- Application and window management.
- File and directory operations.
- Keyboard and mouse automation.
- System monitoring.
- Terminal operations.
- Browser-related tools.
- Task automation.

The implementation includes command filters, workspace path restrictions, action logging, and confirmation mechanisms.

These measures are not a substitute for a complete security boundary or independent security audit.

**Implementation:** `backend/tools/` and `backend/agents/system_agent.py`

### 6. Real-Time Interface

The frontend is built with Next.js, React, and TypeScript.

It includes components for:

- A three-dimensional JARVIS-inspired interface.
- Chat and command interaction.
- System telemetry.
- Agent activity visualization.
- Model and memory status.
- Voice interaction feedback.
- Real-time state updates.

The UI uses React Three Fiber, Three.js, Framer Motion, and Tailwind CSS.

Backend and frontend communicate through HTTP APIs and WebSocket connections.

**Implementation:** `frontend/`

### 7. Native Desktop Integration

JARVIS uses Tauri 2 and Rust for its Windows desktop shell.

The desktop layer includes:

- Native window management.
- Backend process startup.
- Application lifecycle integration.
- System tray-related functionality.
- Application notifications.
- Desktop packaging configuration.

The Windows backend launcher starts the Python service locally and monitors its readiness.

**Implementation:** `src-tauri/`

---

## Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python 3.12+, FastAPI, Uvicorn |
| LLM Inference | Ollama, local language models |
| Embeddings | Sentence Transformers |
| Vector Database | ChromaDB |
| Database | SQLite, aiosqlite |
| Configuration | Pydantic, pydantic-settings |
| Speech Recognition | Whisper |
| Speech Synthesis | Piper |
| System Automation | PyAutoGUI, psutil |
| Computer Vision Libraries | OpenCV |
| Frontend | Next.js 13, React 18 |
| Language | TypeScript |
| Styling | Tailwind CSS 3 |
| 3D Visualization | Three.js, React Three Fiber |
| Animations | Framer Motion |
| Desktop Framework | Tauri 2, Rust |
| Communication | REST APIs, WebSockets |
| Testing | pytest, pytest-asyncio |

See the repository dependency manifests for precise package versions.

---

## Project Structure

```text
jarvis-ai-os/
│
├── backend/
│   ├── agents/
│   │   ├── main_agent.py
│   │   ├── coding_agent.py
│   │   ├── research_agent.py
│   │   ├── security_agent.py
│   │   ├── system_agent.py
│   │   └── swarm_manager.py
│   │
│   ├── core/
│   │   ├── brain.py
│   │   ├── planner.py
│   │   ├── model_router.py
│   │   ├── personality.py
│   │   └── settings.py
│   │
│   ├── memory/
│   │   ├── memory_manager.py
│   │   ├── sqlite_memory.py
│   │   └── vector_memory.py
│   │
│   ├── api/
│   │   ├── chat.py
│   │   ├── voice.py
│   │   ├── system.py
│   │   └── websocket.py
│   │
│   ├── tools/
│   ├── voice/
│   ├── tests/
│   ├── requirements.txt
│   └── main.py
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── context/
│   ├── lib/
│   └── package.json
│
├── src-tauri/
│   ├── src/
│   ├── capabilities/
│   └── Cargo.toml
│
├── ARCHITECTURE.md
├── SUMMARY.md
├── README.md
└── LICENSE
```

## Installation

### Requirements

The project primarily targets Windows.

You will need:

- Python 3.12.
- Node.js 18 or later.
- Git.
- Ollama.
- A compatible local language model.
- Sufficient memory and storage for the selected models.

The optional Tauri desktop build also requires Rust and the Windows dependencies required by Tauri.

### Step 1 — Clone the Repository

```powershell
git clone https://github.com/Apelle333/jarvis-ai-os.git
cd jarvis-ai-os
```

### Step 2 — Install Ollama and a Model

Install Ollama from:

https://ollama.com

With Ollama running, download a model supported by your hardware.

For example:

```powershell
ollama pull qwen3:8b
```

Verify the installed models:

```powershell
ollama list
```

The model router can be configured to use different models for different tasks.

### Step 3 — Set Up the Python Backend

From the repository root:

```powershell
py -3.12 -m venv backend\.venv
```

Install the required Python packages:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### Step 4 — Configure the Backend

Create a `.env` file inside `backend/`.

The current Python configuration supports model routing and related environment settings.

Example for development with one installed model:

```env
OLLAMA_HOST=http://localhost:11434

DEFAULT_MODEL=qwen3:8b

GENERAL_PRIMARY=qwen3:8b
GENERAL_FALLBACK=qwen3:8b

REASONING_PRIMARY=qwen3:8b
REASONING_FALLBACK=qwen3:8b

CODING_PRIMARY=qwen3:8b
CODING_FALLBACK=qwen3:8b

PERSONALITY_PRIMARY=qwen3:8b
PERSONALITY_FALLBACK=qwen3:8b

FAST_PRIMARY=qwen3:8b

EMERGENCY_FALLBACK=qwen3:8b
LAST_RESORT_MODEL=qwen3:8b
```

These values are intended for a simple development environment.

For more specialized behavior, configure separate models for coding, reasoning, and general requests.

**Note:** The repository's existing `backend/.env.example` contains some older model defaults. Refer to `backend/core/settings.py` for the current configuration fields.

Never commit actual credentials or private `.env` files.

### Step 5 — Start the Backend

From the repository root:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

The backend should be accessible locally at:

http://127.0.0.1:8000

Check its health endpoint:

http://127.0.0.1:8000/health

The health response reports whether the backend initialized successfully or is operating in a degraded or unavailable state.

### Step 6 — Start the Frontend

Open a second terminal from the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open:

http://localhost:3000

The frontend expects the backend at `http://localhost:8000` by default.

You can configure a different address through `NEXT_PUBLIC_BACKEND_URL`.

### Optional — Native Desktop Application

The `src-tauri/` directory contains the Tauri desktop application configuration and Rust source code.

Building the desktop application requires a compatible Rust toolchain and Tauri setup.

A prebuilt release installer is not currently provided in this repository.

---

## API Overview

The FastAPI backend exposes multiple interfaces.

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Backend health and readiness |
| `/api/chat/message` | POST | Conversational requests |
| `/api/voice/speech-to-text` | POST | Audio transcription |
| `/api/voice/process-voice` | POST | Voice interaction pipeline |
| `/api/voice/text-to-speech` | POST | Speech generation |
| `/api/system/status` | GET | System status |
| `/api/system/hardware` | GET | Hardware information |
| `/ws/{client_id}` | WebSocket | Real-time state communication |

Example chat request:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/chat/message" `
  -ContentType "application/json" `
  -Body '{"message":"What can you do?"}'
```

The backend must be running with the required dependencies for this request to succeed.

---

## Testing

The repository includes Python tests for parts of the orchestration and telemetry architecture.

Examples include testing:

- Planner state events.
- Model-router state updates.
- Agent state transitions.
- WebSocket telemetry broadcasting.
- Error handling during broadcast failures.

To run the telemetry tests:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_telemetry.py
```

**Verification status:** Test modules are present in the repository, but a complete clean-environment installation, full automated test suite, and end-to-end desktop build have not been independently verified for this version.

Passing tests should not be assumed without executing them.

## Security Considerations

JARVIS provides access to functionality that can interact with the operating system.

**The project should be run only in a trusted local development environment. Do not expose its backend to the public internet or an untrusted network.**

Important limitations:

- API token security is disabled by default in the current configuration.
- Computer-control functionality is enabled by default.
- The `python main.py` entry point currently binds the server to `0.0.0.0`.
- Some actions can require confirmation, but this does not establish a fully secure sandbox.
- Terminal and filesystem tools contain restrictions that have not undergone independent security auditing.
- The system is not intended for deployment with elevated operating-system privileges.

For development, prefer starting Uvicorn explicitly with `--host 127.0.0.1`.

Before deploying beyond a trusted local environment, authentication, authorization, input validation, process isolation, and security controls require further work.

## Current Limitations

JARVIS is an experimental engineering project.

Current limitations include:

- Not every subsystem has been verified through end-to-end tests.
- Voice capabilities depend on locally installed models and additional audio components.
- Some API functionality, including chat-history retrieval, remains incomplete.
- Local model performance depends on hardware resources and model selection.
- The semantic-memory fallback does not provide the same retrieval quality as proper embedding models.
- The system has not been security-audited for production deployment.
- Model training and fine-tuning are outside the current implementation.
- Cloud-based OpenAI API integration is not currently demonstrated.

JARVIS is not designed or validated as a clinical application or a system for processing real patient data.

## Engineering Focus

This project has provided an opportunity to explore several practical software-engineering topics.

**AI Integration**

Connecting locally hosted language models to application logic, APIs, and user interfaces.

**Multi-Agent Design**

Separating responsibilities across specialized modules and coordinating execution through a central manager.

**Memory and Retrieval**

Combining structured persistence with embedding-based information retrieval.

**Backend Engineering**

Organizing Python services, asynchronous operations, API endpoints, configuration, and error handling.

**Human-Computer Interaction**

Connecting AI-assisted requests to desktop controls, system telemetry, and a visual interface.

**Full-Stack Development**

Integrating Python services with a TypeScript frontend and a native desktop runtime.

## Future Development

Potential areas for further development include:

- More comprehensive automated testing.
- Better agent observability and execution tracing.
- Improved model-routing evaluation and performance measurements.
- Stronger permissions and execution isolation.
- Improved memory retrieval and relevance evaluation.
- More robust voice-processing workflows.
- Optional integrations with remote AI providers.
- Improved packaging and installation.
- Documentation of performance benchmarks.

These are future directions, not completed features.

---

## Author

**Luca Bastanzetti**

Independent developer interested in AI engineering, full-stack development, local language models, and autonomous software systems.

**GitHub:** https://github.com/Apelle333

## License

Released under the [MIT License](LICENSE).

## Acknowledgments

Built using open-source technologies and inspired by the JARVIS concept from the Marvel universe.

Key technologies include Ollama, FastAPI, Whisper, Piper, ChromaDB, Sentence Transformers, Next.js, Three.js, and Tauri.

---

*JARVIS AI OS — Exploring the intersection of local AI, intelligent automation, and desktop computing.*
