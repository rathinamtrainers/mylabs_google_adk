# Lab 3: Callbacks & Plugins

This lab teaches **Callbacks** and **Plugins** in Google ADK.

## Prerequisites

- Completed Lab 1 (Context & State) and Lab 2 (Sessions & Memory)
- Python 3.10+
- Google ADK installed
- `GOOGLE_API_KEY` environment variable set

## Setup

```bash
cd lab3_callbacks_plugins
export GOOGLE_API_KEY="your-api-key-here"
```

## Exercises

### Exercise 1: Agent Callbacks
**File:** `01_agent_callbacks.py`

Learn before/after agent callbacks:
- `before_agent_callback` - intercept before agent runs
- `after_agent_callback` - modify agent output
- Skipping agent execution
- Replacing agent responses

```bash
uv run python 01_agent_callbacks.py
```

### Exercise 2: Model Callbacks
**File:** `02_model_callbacks.py`

Control LLM interactions:
- `before_model_callback` - inspect/modify LLM requests
- `after_model_callback` - inspect/modify LLM responses
- Implementing guardrails
- Request/response transformation

```bash
uv run python 02_model_callbacks.py
```

### Exercise 3: Tool Callbacks
**File:** `03_tool_callbacks.py`

Intercept tool execution:
- `before_tool_callback` - validate/modify tool arguments
- `after_tool_callback` - transform tool results
- Tool execution logging
- Argument sanitization

```bash
uv run python 03_tool_callbacks.py
```

### Exercise 4: Callback Patterns
**File:** `04_callback_patterns.py`

Common callback design patterns:
- Content guardrails (block forbidden content)
- Request logging and metrics
- Rate limiting
- Response sanitization

```bash
uv run python 04_callback_patterns.py
```

### Exercise 5: Plugins
**File:** `05_plugins.py`

Creating reusable plugins:
- BasePlugin class
- Plugin lifecycle callbacks
- Global vs agent-level callbacks
- Building a metrics plugin

```bash
uv run python 05_plugins.py
```

## Key Concepts Summary

### Callback Types

| Callback | Parameters | Return to Skip/Replace |
|----------|------------|------------------------|
| `before_agent_callback` | `CallbackContext` | `types.Content` |
| `after_agent_callback` | `CallbackContext` | `types.Content` |
| `before_model_callback` | `CallbackContext`, `LlmRequest` | `LlmResponse` |
| `after_model_callback` | `CallbackContext`, `LlmResponse` | `LlmResponse` |
| `before_tool_callback` | `BaseTool`, `args`, `ToolContext` | `dict` |
| `after_tool_callback` | `BaseTool`, `args`, `ToolContext`, `tool_response` | `dict` |

### Callback Return Behavior

- Return `None` → Allow normal execution (with any in-place modifications)
- Return a value → Skip/replace the operation with your value

### CallbackContext Properties

```python
callback_context.agent_name      # Current agent name
callback_context.invocation_id   # Unique invocation ID
callback_context.state           # Session state (mutable)
callback_context.session         # Current session
callback_context.app_name        # Application name
callback_context.user_id         # Current user ID
```

### Plugin Structure

```python
from google.adk.plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="my_plugin")

    async def before_agent_callback(self, *, agent, callback_context):
        pass  # Global callback for all agents

    async def before_model_callback(self, *, callback_context, llm_request):
        pass  # Global callback for all LLM calls
```

## Next Steps

After completing this lab, proceed to **Lab 4: MCP & A2A** to learn about:
- Model Context Protocol (MCP)
- Agent-to-Agent (A2A) communication
- External tool integration
- Multi-agent orchestration
