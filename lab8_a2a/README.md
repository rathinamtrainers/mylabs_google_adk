# Lab 8: A2A (Agent-to-Agent) Protocol

This lab teaches the **A2A (Agent-to-Agent) protocol** in Google ADK for building distributed agent systems.

## Prerequisites

- Completed Labs 1-4 (especially Lab 4: Multi-Agent)
- Python 3.12+
- Google ADK installed
- `GOOGLE_API_KEY` environment variable set

## Setup

```bash
cd lab8_a2a
uv sync
export GOOGLE_API_KEY="your-api-key-here"
```

## Exercises

| Exercise | Topic | Description |
|----------|-------|-------------|
| 01 | A2A Basics | Protocol concepts, single-process demo |
| 02 | Exposing Agents | `to_a2a()` function, auto-generated cards |
| 03 | Consuming Agents | `RemoteA2aAgent`, mixing local/remote |
| 04 | Agent Cards | Card structure, customization, skills |
| 05 | Distributed Agents | Multi-process realistic scenario |

## Running Exercises

```bash
# Basic exercises (self-contained)
uv run python 01_a2a_basics.py
uv run python 02_exposing_agents.py
uv run python 03_consuming_agents.py
uv run python 04_agent_cards.py

# Distributed demo (in-process mode)
uv run python 05_distributed_agents.py

# Distributed demo (multi-process mode)
# Terminal 1:
uv run python server/math_agent.py
# Terminal 2:
uv run python server/weather_agent.py
# Terminal 3:
uv run python 05_distributed_agents.py --external-servers
```

## Key Concepts

### What is A2A?

A2A (Agent-to-Agent) is an open protocol for AI agents to communicate across network boundaries. It enables:
- Cross-framework agent collaboration
- Distributed agent architectures
- Agent discovery via standardized endpoints

### Core Components

| Component | Purpose |
|-----------|---------|
| `to_a2a()` | Expose an ADK agent as an A2A service |
| `RemoteA2aAgent` | Consume a remote A2A agent |
| `AgentCardBuilder` | Auto-generate agent cards |
| Agent Card | JSON document describing agent capabilities |

### Exposing Agents

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a

app = to_a2a(agent=my_agent, host="localhost", port=8001)
# Run with: uvicorn module:app --port 8001
```

### Consuming Agents

```python
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

remote = RemoteA2aAgent(
    name="remote_agent",
    agent_card="http://localhost:8001/.well-known/agent-card.json"
)

orchestrator = LlmAgent(
    name="Orchestrator",
    sub_agents=[remote],  # Use like any sub-agent
    ...
)
```

### Agent Card Structure

```json
{
  "name": "AgentName",
  "description": "What the agent does",
  "url": "http://host:port/",
  "version": "1.0.0",
  "skills": [
    {
      "id": "skill_id",
      "name": "Skill Name",
      "description": "What this skill does",
      "tags": ["tag1", "tag2"]
    }
  ],
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["text/plain"]
}
```

## Server Agents

The `server/` directory contains standalone agents for distributed demos:

- `server/math_agent.py` - Math operations (port 8001)
- `server/weather_agent.py` - Weather info (port 8002)

## A2A vs Local Sub-Agents

| Aspect | Local Sub-Agents | A2A Remote Agents |
|--------|------------------|-------------------|
| Location | Same process | Any network location |
| Communication | Direct calls | JSON-RPC over HTTP |
| Coupling | Tight | Loose |
| Scaling | Together | Independent |
| Failure | Shared | Isolated |

## Next Steps

After completing this lab, you have covered all major ADK components:
- Lab 1: Context & State
- Lab 2: Sessions & Memory
- Lab 3: Callbacks & Plugins
- Lab 4: Multi-Agent & MCP
- Lab 5: Evaluation
- Lab 6: Streaming
- Lab 7: Artifacts
- Lab 8: A2A Protocol

You're now ready to build production distributed agent systems!
