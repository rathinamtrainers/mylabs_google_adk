# Lab 4: Multi-Agent & MCP

This lab teaches **Multi-Agent Orchestration** and **MCP (Model Context Protocol)** in Google ADK.

## Prerequisites

- Completed Labs 1-3
- Python 3.10+
- Google ADK installed
- `GOOGLE_API_KEY` environment variable set

## Setup

```bash
cd lab4_multiagent_mcp
export GOOGLE_API_KEY="your-api-key-here"
```

## Exercises

### Exercise 1: Multi-Agent Basics
**File:** `01_multi_agent_basics.py`

Learn the fundamentals of multi-agent systems:
- Creating agents with sub-agents
- Agent hierarchy (parent-child)
- Agent transfer (delegation)
- Agent descriptions for routing

```bash
uv run python 01_multi_agent_basics.py
```

### Exercise 2: Workflow Agents
**File:** `02_workflow_agents.py`

Built-in orchestration agents:
- SequentialAgent - step-by-step execution
- ParallelAgent - concurrent execution
- LoopAgent - iterative refinement
- output_key for data passing

```bash
uv run python 02_workflow_agents.py
```

### Exercise 3: Agent Communication
**File:** `03_agent_communication.py`

How agents share information:
- State-based communication
- AgentTool - using agents as tools
- Data passing between agents
- Explicit vs implicit invocation

```bash
uv run python 03_agent_communication.py
```

### Exercise 4: Multi-Agent Patterns
**File:** `04_agent_patterns.py`

Common orchestration patterns:
- Coordinator/Dispatcher pattern
- Generator-Critic pattern
- Pipeline pattern
- Hierarchical decomposition

```bash
uv run python 04_agent_patterns.py
```

### Exercise 5: MCP Tools
**File:** `05_mcp_tools.py`

Model Context Protocol integration:
- Understanding MCP architecture
- McpToolset for external tools
- Using MCP servers
- Building ADK tools for MCP

```bash
uv run python 05_mcp_tools.py
```

## Key Concepts Summary

### Agent Hierarchy

```python
# Sub-agents are defined in parent agent
parent_agent = LlmAgent(
    name="Coordinator",
    sub_agents=[child1, child2, child3]
)

# Framework sets: child1.parent_agent == parent_agent
```

### Agent Transfer

```python
# LLM generates transfer when appropriate
coordinator = LlmAgent(
    name="Coordinator",
    instruction="Route billing to BillingAgent, tech to SupportAgent",
    sub_agents=[billing_agent, support_agent]
)
# LLM calls: transfer_to_agent(agent_name='BillingAgent')
```

### Workflow Agents

| Agent Type | Behavior | Use Case |
|------------|----------|----------|
| SequentialAgent | One after another | Pipelines, multi-step tasks |
| ParallelAgent | All at once | Gather data from multiple sources |
| LoopAgent | Repeat until done | Iterative refinement |

### State-Based Communication

```python
# Agent A writes to state
agent_a = LlmAgent(name="AgentA", output_key="result_a")

# Agent B reads from state
agent_b = LlmAgent(
    name="AgentB",
    instruction="Process the result: {result_a}"
)
```

### AgentTool

```python
from google.adk.tools import agent_tool

# Wrap agent as a tool
helper_tool = agent_tool.AgentTool(agent=helper_agent)

# Use in another agent
main_agent = LlmAgent(
    name="MainAgent",
    tools=[helper_tool]
)
```

## MCP Integration

### Using MCP Servers

```python
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams

tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=['-y', '@modelcontextprotocol/server-filesystem', '/path'],
        ),
    ),
)
```

## Next Steps

After completing this lab, you have covered all major ADK Components:
- Lab 1: Context & State
- Lab 2: Sessions & Memory
- Lab 3: Callbacks & Plugins
- Lab 4: Multi-Agent & MCP

You're now ready to build complex agent systems!
