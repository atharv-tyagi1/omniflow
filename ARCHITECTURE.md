# OMNIFLOW – OFFICIAL TECHNOLOGY DIRECTION

## 1. Official Stack
- **Frontend:** Next.js, TypeScript, Tailwind CSS, React, TanStack Query
- **Backend:** Python, Rust
- **Database:** PostgreSQL, pgvector
- **AI Providers:** Gemini, OpenRouter

## 2. Architecture Rule
- **Python:** Orchestration layer
- **Rust:** Performance layer

Do not move orchestration logic or AI workflow logic into Rust. Do not rewrite stable Python systems solely for language consistency.

## 3. Python Responsibilities
Python is the primary application layer and owns:
- FastAPI APIs
- Authentication & Authorization
- Workspace isolation
- Capability enforcement
- Agent orchestration
- Smart Intent Router
- RAG orchestration
- LLM integrations (Gemini, OpenRouter)
- Workflow orchestration
- Public API layer
- Telegram integration
- Voice orchestration
- Dashboard APIs
- Business Analyst
- Conversation Intel
- Analytics orchestration

## 4. Rust Responsibilities
Rust is introduced ONLY where measurable performance benefits exist.
Approved targets for Rust:
- Workflow execution engine
- High-throughput async workers
- Realtime event processing
- Analytics aggregation
- Telemetry pipeline
- Voice processing
- Audio transformation
- Future realtime messaging infrastructure / event bus / streaming services

Rust services must expose HTTP or gRPC APIs. Python remains the caller.

## 5. Communication Rule
Python must communicate with Rust through clear service boundaries via:
- HTTP
- gRPC
- Queue/Event interfaces

Not Allowed:
- Tight coupling
- Shared mutable state
- Rewriting Python modules directly into Rust without profiling evidence

## 6. Database Rule
PostgreSQL remains the source of truth. pgvector remains the vector store.
Do not introduce MongoDB, Firebase, or SQLite for production.

## 7. Migration Rule
All future migrations must remain additive and backward compatible. Destructive schema changes require explicit approval.

## 8. Phase Execution Rule
For all future phases:
1. Build functionality first.
2. Validate functionality.
3. Measure performance.
4. Introduce Rust only when a proven bottleneck exists.

Never perform speculative rewrites.

## 9. Current Status
- Keep existing Python implementation.
- Do not rewrite completed phases.
- Proceed with future phases using the Python + Rust architecture direction.
