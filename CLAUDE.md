# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains hands-on labs for learning Google ADK (Agent Development Kit) components. Each lab is a standalone Python project with its own virtual environment.

## Reference Resources

- `/home/agenticai/research_gadk/google_adk_codebase` - Google ADK docs, SDK source, samples, and web UI
- https://google.github.io/adk-docs/ - Official online documentation

## Common Commands

### Running Lab Exercises

Each lab uses `uv` for dependency management:

```bash
cd lab<N>_<topic>
uv run python <exercise_file>.py
```

Example:
```bash
cd lab1_context_state
uv run python 01_context_types.py
```

### Environment Setup

```bash
export GOOGLE_API_KEY="your-api-key"
```

### Installing Dependencies

```bash
cd lab<N>_<topic>
uv sync  # Installs from pyproject.toml
```

## Repository Architecture

### Lab Structure

Labs are ordered by learning progression:

| Lab | Topic | Concepts |
|-----|-------|----------|
| lab1_context_state | Foundation | Context types, state prefixes, ToolContext |
| lab2_sessions_memory | Persistence | SessionService, MemoryService, session lifecycle |
| lab3_callbacks_plugins | Interception | Agent/Model/Tool callbacks, BasePlugin |
| lab4_multiagent_mcp | Orchestration | Sub-agents, workflow agents, MCP tools |
| lab5_evaluation | Testing | Eval sets, response/trajectory metrics |
| lab6_streaming | Real-time | Bidi-streaming, LiveRequestQueue, run_live() |
| lab7_artifacts | Binary Data | ArtifactService, namespaces, file tools |
| lab8_a2a | Distributed | A2A protocol, RemoteA2aAgent, agent cards |

### Lab Internal Structure

Each lab follows a consistent pattern:
- `pyproject.toml` - Dependencies (google-adk)
- `README.md` - Concepts and usage
- `01_*.py` through `05_*.py` - Progressive exercises
- `.venv/` - Local virtual environment

### Learning Dependency Chain

```
Context & State → Sessions & Memory → Callbacks & Plugins → Multi-Agent & MCP
```

## Key ADK Patterns Used

### Context Types
- `InvocationContext` - Agent's core implementation
- `ToolContext` - Tool functions (state read/write)
- `CallbackContext` - Callbacks (state read/write)
- `ReadonlyContext` - InstructionProvider

### State Prefixes
- No prefix: Session-scoped
- `user:` - User-scoped across sessions
- `app:` - App-scoped across all users
- `temp:` - Invocation-scoped (discarded)

### Common Agent Patterns
- `LlmAgent` with `sub_agents` for delegation
- `SequentialAgent`, `ParallelAgent`, `LoopAgent` for workflows
- `output_key` for state-based data passing between agents

### A2A (Agent-to-Agent) Protocol
- `to_a2a()` - Expose ADK agent as A2A service
- `RemoteA2aAgent` - Consume remote A2A agents as sub-agents
- `AgentCardBuilder` - Auto-generate agent cards
- Well-known endpoint: `/.well-known/agent-card.json`