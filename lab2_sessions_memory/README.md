# Lab 2: Sessions & Memory

This lab teaches **Session management** and **Memory services** in Google ADK.

## Prerequisites

- Completed Lab 1 (Context & State)
- Python 3.10+
- Google ADK installed
- `GOOGLE_API_KEY` environment variable set

## Setup

```bash
cd lab2_sessions_memory
export GOOGLE_API_KEY="your-api-key-here"
```

## Exercises

### Exercise 1: Session Basics
**File:** `01_session_basics.py`

Learn the fundamentals of Sessions:
- Creating sessions with SessionService
- Session properties (id, app_name, user_id, state, events)
- How sessions capture conversation events
- Listing and retrieving sessions

```bash
uv run python 01_session_basics.py
```

### Exercise 2: Session Lifecycle
**File:** `02_session_lifecycle.py`

Understand the complete session lifecycle:
- CREATE: Start a new session
- USE: Agent interactions add events
- RESUME: Continue existing sessions
- DELETE: Clean up sessions

```bash
uv run python 02_session_lifecycle.py
```

### Exercise 3: Multiple Sessions
**File:** `03_multiple_sessions.py`

Managing multiple sessions:
- Multiple sessions per user
- Sessions for different users
- Session isolation
- Listing and cleanup

```bash
uv run python 03_multiple_sessions.py
```

### Exercise 4: Memory Service Basics
**File:** `04_memory_service.py`

Introduction to MemoryService:
- Session vs Memory concepts
- InMemoryMemoryService setup
- Adding sessions to memory
- Searching memory

```bash
uv run python 04_memory_service.py
```

### Exercise 5: Cross-Session Memory
**File:** `05_cross_session_memory.py`

Using memory across sessions:
- Agent with load_memory tool
- Storing information in one session
- Recalling in another session
- Memory workflow

```bash
uv run python 05_cross_session_memory.py
```

## Key Concepts Summary

### Session vs Memory

| Aspect | Session | Memory |
|--------|---------|--------|
| Scope | Single conversation | Multiple conversations |
| Content | Events from current chat | Searchable archive |
| Persistence | During conversation | Long-term |
| Access | Direct via session_id | Via search query |

### Session Object Properties

```python
session.id          # Unique identifier
session.app_name    # Application name
session.user_id     # User identifier
session.state       # Session-scoped state dict
session.events      # List of all events
session.last_update_time  # Last activity timestamp
```

### SessionService Operations

```python
# Create
session = await service.create_session(
    app_name="app", user_id="user",
    session_id="optional_id", state={}
)

# Get
session = await service.get_session(
    app_name="app", user_id="user", session_id="id"
)

# List
response = await service.list_sessions(
    app_name="app", user_id="user"
)

# Delete
await service.delete_session(
    app_name="app", user_id="user", session_id="id"
)
```

### MemoryService Operations

```python
# Add session to memory
await memory_service.add_session_to_memory(session)

# Search memory
results = await memory_service.search_memory(
    app_name="app", user_id="user", query="search terms"
)
```

### Service Implementations

**SessionService:**
- `InMemorySessionService` - Development (no persistence)
- `DatabaseSessionService` - Production (SQL databases)
- `VertexAiSessionService` - Google Cloud

**MemoryService:**
- `InMemoryMemoryService` - Development (basic keyword search)
- `VertexAiMemoryBankService` - Production (semantic search)

## Next Steps

After completing this lab, proceed to **Lab 3: Callbacks & Plugins** to learn about:
- All 6 callback types
- Design patterns for callbacks
- Creating custom plugins
- Guardrails and rate limiting
