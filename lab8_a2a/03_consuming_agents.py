"""
Lab 8 - Exercise 3: Consuming Agents
====================================

This exercise covers how to consume remote A2A agents:
1. Creating RemoteA2aAgent from URL
2. Agent card resolution
3. Using RemoteA2aAgent as a sub-agent
4. Error handling (timeouts, connection failures)
5. Mixing local and remote agents

Run: uv run python 03_consuming_agents.py

Prerequisites:
- Start the math server first in another terminal:
  cd server && uv run python math_agent.py
"""

import asyncio
import threading
import time
import uvicorn
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.genai import types


# =============================================================================
# Part 1: RemoteA2aAgent Overview
# =============================================================================

def explain_remote_a2a_agent():
    """Explain the RemoteA2aAgent class."""
    print("""
    REMOTEA2AAGENT
    ==============

    RemoteA2aAgent is the client-side component for consuming A2A agents.
    It wraps a remote A2A service and makes it usable like a local sub-agent.


    Basic Usage:
    ------------
    from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

    remote_agent = RemoteA2aAgent(
        name="remote_math",
        description="Remote math agent",
        agent_card="http://localhost:8001/.well-known/agent-card.json"
    )


    Constructor Parameters:
    -----------------------
    name: str
        Unique identifier for the agent (required)

    agent_card: AgentCard | str
        How to find the agent (required)
        - URL string: Fetches card from URL
        - File path: Loads card from local JSON file
        - AgentCard object: Uses directly

    description: str | None
        Optional description (overrides card's description)

    timeout: float = 600
        HTTP request timeout in seconds

    httpx_client: httpx.AsyncClient | None
        Optional shared HTTP client


    How It Works:
    -------------
    1. Resolves agent card (fetch URL or load file)
    2. Extracts A2A endpoint URL from card
    3. When invoked, sends JSON-RPC request to endpoint
    4. Converts A2A response to ADK events
    5. Returns results like a local agent
    """)


# =============================================================================
# Part 2: Helper - Start Math Server
# =============================================================================

def create_math_agent():
    """Create the math agent for demo."""

    def add(a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    return LlmAgent(
        name="MathAgent",
        model="gemini-2.0-flash",
        description="Math specialist for arithmetic operations.",
        instruction="You are a math agent. Use tools for calculations.",
        tools=[add, multiply],
    )


def run_server_background(app, port: int):
    """Run server in background thread."""
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


# =============================================================================
# Part 3: Agent Card Resolution
# =============================================================================

def explain_agent_card_resolution():
    """Explain how agent cards are resolved."""
    print("""
    AGENT CARD RESOLUTION
    =====================

    RemoteA2aAgent supports multiple ways to specify the agent card:


    1. URL STRING (Most Common)
    ---------------------------
    remote = RemoteA2aAgent(
        name="remote_agent",
        agent_card="http://localhost:8001/.well-known/agent-card.json"
    )

    - Fetches card via HTTP GET
    - Standard well-known path convention
    - Best for network agents


    2. FILE PATH
    ------------
    remote = RemoteA2aAgent(
        name="remote_agent",
        agent_card="/path/to/agent-card.json"
    )

    - Loads card from local filesystem
    - Useful for testing with saved cards
    - Good for offline development


    3. AGENTCARD OBJECT
    -------------------
    from a2a.types import AgentCard

    card = AgentCard(
        name="CustomAgent",
        url="http://localhost:8001/",
        ...
    )

    remote = RemoteA2aAgent(
        name="remote_agent",
        agent_card=card
    )

    - Programmatically constructed card
    - Maximum flexibility
    - Useful for dynamic configuration


    WELL-KNOWN ENDPOINT
    -------------------
    The standard location for agent cards is:
    /.well-known/agent-card.json

    This follows web conventions (like /.well-known/security.txt)
    and makes agent discovery predictable.
    """)


# =============================================================================
# Part 4: Using as Sub-Agent
# =============================================================================

async def demo_remote_as_subagent():
    """Demonstrate using RemoteA2aAgent as a sub-agent."""
    print("\n  Setting up demo...")

    # Create and start math server
    math_agent = create_math_agent()
    math_app = to_a2a(agent=math_agent, host="127.0.0.1", port=8001)

    server_thread = threading.Thread(
        target=run_server_background,
        args=(math_app, 8001),
        daemon=True
    )
    server_thread.start()
    time.sleep(2)
    print("  Math server started on port 8001")

    # Create remote agent reference
    remote_math = RemoteA2aAgent(
        name="remote_math",
        description="Remote math specialist via A2A",
        agent_card="http://127.0.0.1:8001/.well-known/agent-card.json",
    )

    # Create orchestrator that uses the remote agent
    orchestrator = LlmAgent(
        name="Orchestrator",
        model="gemini-2.0-flash",
        instruction="""You are a helpful assistant.
        When the user asks for math calculations, delegate to the remote_math agent.
        For other questions, answer directly.""",
        sub_agents=[remote_math],
    )

    # Set up runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=orchestrator,
        app_name="remote_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="remote_demo",
        user_id="user1",
        session_id="session1",
    )

    # Test with a math question
    print("\n  --- Testing Remote Agent ---")
    print("  User: What is 25 multiplied by 4?")

    user_message = types.Content(parts=[types.Part(text="What is 25 multiplied by 4?")])

    response_text = ""
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            response_text = event.content.parts[0].text

    print(f"  Response: {response_text}")

    return True


# =============================================================================
# Part 5: Error Handling
# =============================================================================

def explain_error_handling():
    """Explain error handling for remote agents."""
    print("""
    ERROR HANDLING
    ==============

    When working with remote agents, various errors can occur:


    1. CONNECTION ERRORS
    --------------------
    - Server not running
    - Wrong host/port
    - Network issues

    RemoteA2aAgent raises httpx.ConnectError or similar


    2. TIMEOUT ERRORS
    -----------------
    - Agent takes too long
    - Network latency

    Configure timeout:
    remote = RemoteA2aAgent(
        name="remote",
        agent_card="...",
        timeout=30  # 30 seconds (default is 600)
    )


    3. AGENT CARD ERRORS
    --------------------
    - Invalid URL
    - Malformed card JSON
    - Missing required fields


    4. A2A PROTOCOL ERRORS
    ----------------------
    - Invalid JSON-RPC response
    - Task execution failures


    BEST PRACTICES
    ==============

    1. Set appropriate timeouts:
       remote = RemoteA2aAgent(..., timeout=60)

    2. Use try/except for critical paths:
       try:
           async for event in runner.run_async(...):
               ...
       except Exception as e:
           # Handle error

    3. Implement fallback behavior:
       # If remote fails, use local alternative

    4. Monitor and log remote calls

    5. Consider circuit breaker patterns for production
    """)


# =============================================================================
# Part 6: Mixing Local and Remote Agents
# =============================================================================

async def demo_mixed_agents():
    """Demonstrate mixing local and remote agents."""
    print("\n  Setting up mixed agent demo...")

    # Remote math agent (already running from previous demo)
    remote_math = RemoteA2aAgent(
        name="remote_math",
        description="Remote math specialist via A2A",
        agent_card="http://127.0.0.1:8001/.well-known/agent-card.json",
    )

    # Local greeting agent
    local_greeter = LlmAgent(
        name="local_greeter",
        model="gemini-2.0-flash",
        description="Local agent for greetings and small talk.",
        instruction="You are a friendly greeter. Keep responses brief and warm.",
    )

    # Coordinator that uses both
    coordinator = LlmAgent(
        name="Coordinator",
        model="gemini-2.0-flash",
        instruction="""You coordinate between specialists:
        - For math/calculations: use remote_math
        - For greetings/small talk: use local_greeter
        - For other questions: answer directly

        Route appropriately based on the user's request.""",
        sub_agents=[remote_math, local_greeter],
    )

    # Set up runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=coordinator,
        app_name="mixed_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="mixed_demo",
        user_id="user1",
        session_id="session1",
    )

    # Test messages
    test_messages = [
        ("Greeting", "Hello! How are you today?"),
        ("Math", "What is 15 + 27?"),
        ("General", "What's the capital of France?"),
    ]

    for label, message in test_messages:
        print(f"\n  --- {label} Test ---")
        print(f"  User: {message}")

        user_message = types.Content(parts=[types.Part(text=message)])

        response_text = ""
        responding_agent = ""

        async for event in runner.run_async(
            user_id="user1",
            session_id="session1",
            new_message=user_message,
        ):
            if hasattr(event, 'author'):
                responding_agent = event.author
            if event.is_final_response() and event.content:
                response_text = event.content.parts[0].text

        print(f"  Agent: {responding_agent}")
        print(f"  Response: {response_text[:100]}...")


# =============================================================================
# Main
# =============================================================================

async def main():
    print("\n" + "#" * 70)
    print("# Lab 8 Exercise 3: Consuming Agents")
    print("#" * 70)

    # =========================================================================
    # Part 1: RemoteA2aAgent Overview
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 1: RemoteA2aAgent Overview")
    print("=" * 60)

    explain_remote_a2a_agent()

    # =========================================================================
    # Part 2: Agent Card Resolution
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 2: Agent Card Resolution")
    print("=" * 60)

    explain_agent_card_resolution()

    # =========================================================================
    # Part 3: Using RemoteA2aAgent as Sub-Agent
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 3: Using RemoteA2aAgent as Sub-Agent")
    print("=" * 60)

    print("""
    RemoteA2aAgent integrates seamlessly with ADK's sub-agent system.

    The orchestrator doesn't know (or care) whether a sub-agent is:
    - Local LlmAgent
    - Remote A2A agent
    - Any other agent type

    This enables transparent distributed agent systems.
    """)

    await demo_remote_as_subagent()

    # =========================================================================
    # Part 4: Error Handling
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 4: Error Handling")
    print("=" * 60)

    explain_error_handling()

    # =========================================================================
    # Part 5: Mixing Local and Remote Agents
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 5: Mixing Local and Remote Agents")
    print("=" * 60)

    print("""
    Real-world systems often mix:
    - Local agents (fast, no network)
    - Remote agents (specialized, distributed)

    This demo shows a coordinator using both types.
    """)

    await demo_mixed_agents()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#" * 70)
    print("# Summary: Consuming Agents")
    print("#" * 70)
    print("""
    REMOTEA2AAGENT:
    ---------------
    - Client for consuming A2A agents
    - Works like any other sub-agent
    - Handles network communication transparently

    CREATING REMOTE AGENTS:
    -----------------------
    remote = RemoteA2aAgent(
        name="remote_agent",
        agent_card="http://host:port/.well-known/agent-card.json",
        timeout=60  # optional
    )

    AGENT CARD SOURCES:
    -------------------
    - URL: Fetches from network
    - File path: Loads from disk
    - AgentCard object: Direct use

    USING AS SUB-AGENT:
    -------------------
    orchestrator = LlmAgent(
        name="Orchestrator",
        sub_agents=[remote_agent, local_agent],
        ...
    )

    ERROR HANDLING:
    ---------------
    - Set appropriate timeouts
    - Handle connection errors
    - Consider fallbacks

    MIXED SYSTEMS:
    --------------
    - Combine local and remote agents
    - Transparent to orchestrator
    - Flexible architecture

    NEXT STEPS:
    -----------
    Exercise 4: Deep dive into agent card customization
    """)


if __name__ == "__main__":
    asyncio.run(main())
