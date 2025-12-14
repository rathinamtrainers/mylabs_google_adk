# Lab 1: Context & State

This lab teaches the foundational concepts of **Context** and **State** in Google ADK.

## Prerequisites

- Python 3.10+
- Google ADK installed (`pip install google-adk`)
- A Gemini API key set as `GOOGLE_API_KEY` environment variable

## Setup

```bash
cd lab1_context_state
pip install -r requirements.txt
export GOOGLE_API_KEY="your-api-key-here"
```

## Exercises

### Exercise 1: Understanding Context Types
**File:** `01_context_types.py`

Learn about the four context types in ADK:
- **InvocationContext**: Full access in agent's core implementation
- **ReadonlyContext**: Read-only access in InstructionProvider
- **CallbackContext**: Read/write in agent/model callbacks
- **ToolContext**: Full capabilities in tool functions

```bash
python 01_context_types.py
```

### Exercise 2: State Management with Prefixes
**File:** `02_state_prefixes.py`

Learn how state scoping works with prefixes:
- No prefix: Session-scoped
- `user:` prefix: User-scoped across sessions
- `app:` prefix: App-scoped across all users
- `temp:` prefix: Invocation-scoped (discarded after)

```bash
python 02_state_prefixes.py
```

### Exercise 3: State in Tools
**File:** `03_state_in_tools.py`

Learn how to use state within tool functions:
- Reading state in tools
- Writing state in tools
- Passing data between tools via state
- Shopping cart example

```bash
python 03_state_in_tools.py
```

### Exercise 4: State in Agent Instructions
**File:** `04_state_in_instructions.py`

Learn how to use state in agent instructions:
- `{key}` templating for value injection
- `{key?}` for optional values
- `output_key` to save responses to state
- `InstructionProvider` for dynamic instructions

```bash
python 04_state_in_instructions.py
```

### Exercise 5: Callbacks with State
**File:** `05_callbacks_with_state.py`

Learn how to use CallbackContext for state management:
- Metrics tracking (counts, timing)
- Guardrails (content filtering)
- Rate limiting
- Controlling flow by returning values

```bash
python 05_callbacks_with_state.py
```

## Key Concepts Summary

### Context Types

| Context Type | Where Used | Can Write State? |
|-------------|------------|------------------|
| InvocationContext | Agent's `_run_async_impl` | Yes |
| ReadonlyContext | InstructionProvider | No |
| CallbackContext | Agent/Model callbacks | Yes |
| ToolContext | Tool functions | Yes |

### State Prefixes

| Prefix | Scope | Persistence |
|--------|-------|-------------|
| (none) | Current session | Per session |
| `user:` | Per user | Across sessions |
| `app:` | Application | All users |
| `temp:` | Invocation | Never persists |

### State Access Patterns

```python
# In a tool or callback:
value = context.state.get("key", default)  # Read
context.state["key"] = value                # Write

# In instructions:
instruction = "Hello {user_name}"           # Template
instruction = "Hello {user_name?}"          # Optional

# Save agent output:
agent = LlmAgent(..., output_key="response")
```

## Next Steps

After completing this lab, proceed to **Lab 2: Sessions & Memory** to learn about:
- Session lifecycle management
- SessionService implementations
- Long-term memory with MemoryService
