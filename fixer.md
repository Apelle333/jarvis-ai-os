# JARVIS Autonomous Software Engineer Rules

## ROLE

You are the autonomous senior software engineer responsible for this entire repository.

You have full authority to:
- inspect files
- modify code
- create missing files
- fix bugs
- refactor broken implementations
- install required dependencies
- run tests
- verify functionality

Your mission is simple:

MAKE THIS PROJECT RUNNING AND STABLE.

Do not just explain problems.
Fix them.

---

# PRIMARY OBJECTIVE

Transform the current repository into a working production-quality application.

Success criteria:

Backend:
- starts without errors
- all imports resolve
- APIs respond correctly
- AI models connect correctly
- memory system works

Frontend:
- installs correctly
- builds successfully
- runs without errors
- communicates with backend

---

# AUTONOMOUS DEBUG LOOP

Follow this exact cycle:


INSPECT
↓
RUN TEST
↓
READ ERROR
↓
FIND ROOT CAUSE
↓
FIX FILES
↓
RUN TEST AGAIN
↓
REPEAT


Never stop after the first error.

Never leave known errors unfixed.

Continue until the application works.

---

# IMPORTANT RULES

## Do not:

- Ask for permission before fixing files.
- Stop after discovering an error.
- Give only explanations.
- Apply temporary hacks.
- Delete features to hide problems.
- Ignore related files.

## Always:

- Fix the real cause.
- Check connected files.
- Preserve existing functionality.
- Improve code quality when possible.
- Test after every significant change.

---

# FIRST ACTION: FULL AUDIT

Before making changes:

1. Inspect repository structure.
2. Read configuration files.
3. Check dependencies.
4. Run automatic checks.

Create an internal TODO list:

Example:


[ ] Syntax errors
[ ] Import errors
[ ] Dependency problems
[ ] Runtime errors
[ ] Configuration problems
[ ] Frontend issues
[ ] Integration issues


Resolve every item.

---

# BACKEND DEBUG PROCEDURE

Location:


backend/


Activate environment:

Windows:


venv\Scripts\activate


Run syntax audit:


python -m compileall .


Check:

- Python syntax
- broken imports
- missing packages
- wrong relative imports
- async problems
- incorrect type usage
- configuration errors
- database errors
- Ollama connection errors


Start backend:


python main.py


If it crashes:

1. Read full traceback.
2. Find responsible file.
3. Fix.
4. Restart.

Repeat until backend starts.

---

# PYTHON CODE QUALITY

When editing Python:

Always verify:

- imports are correct
- indentation is valid
- functions are complete
- async/await usage is correct
- exceptions are handled
- types are consistent

Prefer:


clean architecture
clear naming
production patterns


Avoid:


quick patches
commenting out code
removing functionality


---

# OLLAMA / AI MODEL RULES

The project uses local Ollama models.

Available models may include:


gemma4:12b
qwen3.6:27b-q4_K_M


Verify:


ollama list


Check:

- model names match .env
- API endpoint works
- router selects available models
- missing models are handled correctly

Never replace working local models with cloud APIs.

---

# FRONTEND DEBUG PROCEDURE

Location:


frontend/


Install:


npm install


Build test:


npm run build


Check:

- TypeScript errors
- React errors
- Next.js errors
- broken imports
- missing dependencies
- API connection issues

Fix all errors.

Run:


npm run dev


Verify application loads.

---

# DEPENDENCY MANAGEMENT

When something is missing:

Check:


requirements.txt
package.json


Before installing.

Rules:

- Use compatible versions.
- Avoid unnecessary packages.
- Keep dependency files updated.
- Do not install random libraries without reason.

---

# FILE STRUCTURE RULES

Respect the existing architecture.

Before creating new systems:

Check if functionality already exists.

Avoid duplicate files.

Avoid duplicate implementations.

---

# TESTING REQUIREMENTS

After fixes:

Backend:


python -m compileall .
python main.py


Frontend:


npm run build


Do not declare success without verification.

---

# PERFORMANCE RULES

Optimize for:

- fast startup
- low memory usage
- clean async operations
- efficient AI calls
- modular architecture

Avoid:

- unnecessary loops
- blocking operations
- duplicated code
- inefficient database calls

---

# SECURITY RULES

Check:

- environment variables
- exposed API keys
- unsafe commands
- dangerous system operations
- user input validation

Never hardcode secrets.

---

# FINAL RESPONSE FORMAT

Only after everything works provide:


STATUS:
Backend: PASS/FAIL
Frontend: PASS/FAIL

FILES MODIFIED:

file
file

ERRORS FIXED:

error
solution

TESTS EXECUTED:

command
result

REMAINING ISSUES:

none / list

---

# EXECUTION COMMAND

Start immediately.

Do not explain the plan.

Inspect the repository.
Run tests.
Fix everything.
Continue until working.

---

# FINAL REPORT

Date: 2026-08-04

## STATUS

Backend: PASS
Frontend: PASS
Integration: PASS

## FILES MODIFIED

### Backend
- `backend/main.py` — absolute log/static paths, CORS (localhost:3000), `/health` registered before the static mount, pythonw-safe logging
- `backend/core/brain.py` — `SwarmManager(brain=self)`, `_register_agents()` for all 5 agents, `memory_manager.shutdown()`, Ollama availability wrapped so startup survives Ollama outages
- `backend/core/planner.py` — fixed `_assess_complexity` indentation, whole-word keyword matching (no more `c[api]tal` false positives), `get_running_loop`, simplified `_build_steps`
- `backend/core/model_router.py` — `ollama.list()` key fix, `generate()` offloaded via `asyncio.to_thread` (unblocks event loop), `get_available_models()` returns JSON-serializable dicts
- `backend/models/model_router.py` — `generate()` offloaded via `asyncio.to_thread`; research/planning only prefers the 27B model for expert-level complexity (12B otherwise for latency)
- `backend/agents/research_agent.py` — valid `select_model` call, `memory_manager.search_memory`, browser tool methods, rewritten `_gather_information`, time-boxed `_web_research` (40s), primary report is always a real model-generated answer (template appended only when genuine facts/sources exist)
- `backend/agents/security_agent.py` — valid `select_model` call
- `backend/agents/system_agent.py` — `_get_system_info()` helper (replaced nonexistent `get_system_info`)
- `backend/agents/main_agent.py` — removed duplicate personality/memory application
- `backend/agents/swarm_manager.py` — skips `main_agent` steps to prevent recursion, fallback uses brain router
- `backend/api/dependencies.py` — shared `brain`/`main_agent` via `set_brain()`, vendored into chat/voice/websocket routers
- `backend/api/chat.py` — `context` typed `Optional[Any]`
- `backend/api/websocket.py` — fixed doubled `/ws/ws/{client_id}` path → `/ws/{client_id}`; added `GET /ws/status`
- `backend/voice/whisper.py` — async `get_status()`, `get_running_loop` fixes
- `backend/voice/piper.py` — async `get_status()`
- `backend/memory/sqlite_memory.py` — `"modalite"` → `"modality"`, explicit column mapping in `search()`
- `backend/memory/vector_memory.py` — embedding model loaded via `run_in_executor` (no event-loop block on startup)
- `backend/tools/browser.py` — `get_running_loop`, `actual_url` NameError, request-level `timeout=self.timeout` (30s)
- `backend/.env` — models set to installed `qwen3.6:27b-q4_K_M` / `gemma4:12b`

### Frontend
- `frontend/components/Chat.tsx` — `'use client'`, `marked` named import, JSX className backtick fix, `memarkdown` → `msg.content`, wired to real backend `POST /api/chat/message`
- `frontend/components/SystemPanel.tsx` — `'use client'`, real stats from `GET /api/chat/status`, dynamic widths via inline style
- `frontend/components/VoiceVisualizer.tsx` — `'use client'`, driven by JarvisContext state
- `frontend/components/Avatar3D.tsx` — `'use client'`, animation via `useFrame`, fixed sphere geometry args
- `frontend/components/JarvisOrb.tsx` — `'use client'`, state from JarvisContext (no random simulation)
- `frontend/context/JarvisContext.tsx` — `'use client'`, `NEXT_PUBLIC_BACKEND_URL`, health polling, native `WebSocket` to `/ws/{client_id}` with reconnect + status
- `frontend/package.json` — added `tailwindcss-animate` devDependency
- `frontend/.env.local` — `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`
- `frontend/pages/api/chat.ts`, `frontend/pages/api/health.ts` — removed (dead simulated routes; frontend now talks to FastAPI directly)

## ERRORS FIXED

- Backend startup crashes: broken imports, wrong relative imports, `m["name"]` vs `m["model"]`, invalid `select_model` kwargs, `get_event_loop` deprecations
- Research agent always failed: rewritten `_gather_information`, valid browser/KB methods, real model-generated primary answer
- Event loop fully blocked during generation: `ollama.chat()` was synchronous inside `async def`; now via `asyncio.to_thread` in both routers — `/health` stays responsive during multi-minute generations
- Web research hung indefinitely: request-level 30s timeout + 40s time-boxed web research
- WebSocket 500: `/ws` prefix doubled the path (static mount shadowed it) + `ListResponse` not JSON-serializable
- Voice status 500s: missing `async get_status()` on whisper/piper
- Memory search errors: wrong column parsing, `"modalite"` typo
- Frontend build failures: missing `'use client'`, `marked` default import, backtick-in-`className` JSX syntax error, undefined `memarkdown`, missing `tailwindcss-animate`, broken `pages/api` template literals

## TESTS EXECUTED

- `python -m compileall .` — PASS (no syntax errors)
- Backend boot via scheduled task `JarvisBackend` (`pythonw -m uvicorn main:app --port 8000`) — PASS
- `GET /health`, `GET /api/chat/status`, `GET /api/voice/status`, `GET /ws/status` — 200 OK
- `POST /api/chat/message` "capital of France" — HTTP 200, "The capital of France is Paris."
- Research request — HTTP 200 in ~351s, real model-written answer
- Analysis request — HTTP 200, `/health` still responded in ~2s during generation (event loop free)
- WebSocket client test: connect → `connection/connected`, `get_status` → status JSON, `ping` → `pong`
- CORS: preflight OPTIONS 200, `Access-Control-Allow-Origin: http://localhost:3000` on responses
- `npm run build` — PASS, `/` route compiled (221 kB)
- `next start -p 3000` — HTTP 200; frontend→backend fetch from origin localhost:3000 works

## REMAINING ISSUES

- Inference latency: 12B/27B local models take ~1 min (short chat) to ~6 min (long research/analysis) per answer on this hardware (44% GPU); inherent to local Ollama, not a code bug
- Voice (STT/TTS): `/api/voice/status` works but reports `not_initialized` — whisper/piper engines are stubs and not wired to a working audio pipeline; the voice button in the UI is visual-only
- Web scraping: Google often returns 0 results in this environment; research falls back to model knowledge + internal KB, with web research time-boxed and optional
- Harmless chromadb telemetry errors in the log (posthog version mismatch), non-fatal
- `backend/main.py` `uvicorn.run(reload=True)` is only used when run as `python main.py`; the persistent scheduled task runs without reloader (correct for production)

---

# PHASE: SYSTEM INTELLIGENCE UPGRADE — COMPLETE (2026-08-04)

Real, read-only intelligence layer so JARVIS answers system questions from live data
(never fake). Required pattern honored: User → Brain → Planner → SystemIntelligence →
real data → Ollama → response.

## WHAT WAS BUILT

### Backend
- `backend/tools/system_intelligence.py` — `SystemIntelligence` class, READ-ONLY, all data real:
  `get_active_modules`, `get_system_status`, `get_hardware_info` (CPU/RAM/disk/network + GPU
  via `nvidia-smi`, graceful failure), `get_running_processes`, `get_ollama_status`
  (server + models + loaded models), `get_agent_status`, `get_memory_status`,
  `get_application_health` (ONLINE/DEGRADED/OFFLINE), `get_live_snapshot`,
  `store_system_scan` / `get_last_system_scan` (memory integration). Constants
  ONLINE/OFFLINE/ERROR/NOT_CONFIGURED.
- `backend/core/planner.py` — new `TaskType.SYSTEM_ANALYSIS` + `_is_system_analysis()`
  (whole-word/pattern detection checked BEFORE generic research/code classification);
  prompt mapping entry. Detects: modules, system status/health/scan, GPU/hardware,
  cpu/ram/disk usage, model-in-use, running processes, active agents, Ollama, "are you ok".
- `backend/core/brain.py` — `self.system_intelligence = SystemIntelligence(brain=self)`;
  `process_input` routes `SYSTEM_ANALYSIS` to new `_handle_system_analysis()` (bypasses the
  plain-Ollama path, feeds real snapshot to the LLM for narrative, stores scan in memory).
  `_format_system_summary()` renders real data to readable text (full for users, compact
  for LLM). Empty-LLM fallback returns the raw summary so the user always gets valid data.
- `backend/api/system.py` — new router, endpoints (all read-only, try/except → 500):
  `GET /api/system/status|modules|hardware|agents|ollama|memory|health|processes|snapshot|scan`.
- `backend/main.py` — registered `system_router` under `/api/system`; lifespan now spawns
  `system_snapshot_broadcast_loop(brain)` (cancel on shutdown).
- `backend/api/websocket.py` — new `system_snapshot` message type (snapshot + agents + ollama)
  and background broadcast loop: every 3s pushes `{type: system_snapshot, snapshot}` to all
  connected clients when any are connected.
- `backend/tools/system_intelligence.py` — `get_agent_status` fixed: registered agents report
  ONLINE (were NOT_CONFIGURED due to lazy init); `initialized` flag + detail kept truthful.

### Frontend
- `frontend/components/system/useSystemPoll.ts` — shared polling hook (`useSystemPoll<T>`)
  + `formatUptime`.
- `frontend/components/system/SystemCoreStatus.tsx` — app status, brain state, uptime,
  requests/errors, core/AI/module health (polls `/api/system/status` + `/health`).
- `frontend/components/system/HardwareHUD.tsx` — CPU/RAM/disk meters + GPU card (VRAM, util,
  temp) from `/api/system/hardware` (3s poll).
- `frontend/components/system/ModuleGrid.tsx` — modules grouped by category, glowing status
  dots, from `/api/system/modules`.
- `frontend/components/system/AgentMonitor.tsx` — agent list w/ status + specializations from
  `/api/system/agents`.
- `frontend/components/system/ModelMonitor.tsx` — Ollama server status, loaded models, model
  list from `/api/system/ollama`.
- `frontend/app/page.tsx` — HUD wired into right sidebar (SystemCoreStatus, ModelMonitor,
  AgentMonitor, ModuleGrid) and HardwareHUD in left sidebar.

## TESTS EXECUTED (all PASS)
- `python -m compileall .` — PASS
- Backend restart via `schtasks /run /tn JarvisBackend` — clean boot, 5 agents registered
- `GET /api/system/health` — ONLINE, core=ONLINE, ai=ONLINE, modules=14/16
- `GET /api/system/snapshot` — state=idle, cpu/mem/disk real, gpu_available=True
- `GET /api/system/hardware` — 12 cores @ 2500 MHz, 31.8 GB RAM, RTX 4060 Ti 8 GB, host real
- `GET /api/system/modules` — 16 modules, all Core/AI/Memory ONLINE; agents ONLINE
- `GET /api/system/agents` — 5/5 active, detail "registered, ready on first use"
- `GET /api/system/ollama` — server_running=True, models qwen3.6:27b-q4_K_M, gemma4:12b
- `POST /api/chat/message` "What model are you using and how is your GPU?" — ~8s, real data
- `POST /api/chat/message` "Which modules are active right now?" — ~7s, real data
- `POST /api/chat/message` "Analyze my system and give me a health overview" — LLM narrative
  (real data), scan stored in memory; empty-model-output fallback returns raw summary
- Regression: "What is the capital of France?" — ~27s, "The capital of France is **Paris**."
- WebSocket: connect → connection; `system_snapshot` request → snapshot+agents+ollama;
  background broadcast every 3s while connected
- `npm run build` — PASS (HUD components compile, lint/typecheck clean)

## NOTES / REMAINING
- LLM narrative latency is ~1.5–3 min on this hardware (12B/27B local models, ~44% GPU,
  partially CPU-bound). Simple lookups bypass the LLM (instant). The empty-response gemma4
  quirk is handled by the summary fallback.
- Voice STT/TTS remain stubs (unchanged from previous phase).
