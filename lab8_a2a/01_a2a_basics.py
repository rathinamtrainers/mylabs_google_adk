"""
Lab 8 - Exercise 1: A2A Basics
==============================

This exercise introduces the A2A (Agent-to-Agent) protocol:
1. What is A2A and why use it
2. Key concepts (Agent Cards, JSON-RPC, well-known endpoints)
3. Single-process demo with threading
4. Request/response lifecycle

Run: uv run python 01_a2a_basics.py
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
# Part 1: What is A2A and Why Use It
# =============================================================================

def explain_a2a():
    """Explain the A2A protocol and its use cases."""
    print("""
    WHAT IS A2A?
    ============

    A2A (Agent-to-Agent) is an open protocol that enables AI agents to
    communicate with each other across network boundaries.

    Think of it as "HTTP for AI agents" - a standardized way for agents
    to discover, connect, and collaborate regardless of:
    - What framework built them (ADK, LangChain, custom, etc.)
    - What organization owns them
    - What language they're written in
    - Where they're deployed


    WHY USE A2A?
    ============

    1. INTEROPERABILITY
       - Connect agents from different teams/companies
       - Mix ADK agents with other frameworks
       - Build ecosystems of specialized agents

    2. DISTRIBUTED ARCHITECTURE
       - Run agents on different servers/clouds
       - Scale agents independently
       - Isolate failures

    3. SPECIALIZATION
       - Build expert agents for specific domains
       - Compose complex systems from simple parts
       - Reuse agents across projects

    4. SECURITY BOUNDARIES
       - Agents communicate over defined APIs
       - Each agent controls its own access
       - Audit and monitor agent interactions


    ADK vs A2A SUB-AGENTS
    =====================

    Local sub_agents (Lab 4):
    - Same process, same memory
    - Direct function calls
    - Fast, no network overhead
    - Tightly coupled

    A2A RemoteA2aAgent:
    - Different processes/servers
    - Network communication (JSON-RPC)
    - Can be anywhere on the network
    - Loosely coupled
    """)


# =============================================================================
# Part 2: Key A2A Concepts
# =============================================================================

def explain_key_concepts():
    """Explain the key concepts in A2A."""
    print("""
    KEY A2A CONCEPTS
    ================

    1. AGENT CARD
       -----------
       A JSON document describing an agent's capabilities.
       Like a "business card" for AI agents.

       Contains:
       - name: Agent identifier
       - description: What the agent does
       - url: Where to reach the agent
       - skills: List of capabilities
       - version: API version
       - capabilities: Supported features

       Location: /.well-known/agent-card.json


    2. JSON-RPC
       ---------
       The communication protocol used by A2A.
       Standard request/response over HTTP.

       Request:
       {
         "jsonrpc": "2.0",
         "method": "tasks/send",
         "params": { ... },
         "id": "123"
       }


    3. WELL-KNOWN ENDPOINT
       --------------------
       Standard location for agent discovery:
       http://agent-url/.well-known/agent-card.json

       Clients fetch this to learn about the agent.


    4. TASKS
       ------
       A2A models interactions as "tasks":
       - Client sends a task (message)
       - Server processes and responds
       - Supports streaming updates


    ADK A2A COMPONENTS
    ==================

    EXPOSING (Server-side):
    - to_a2a(): Convert ADK agent to A2A service
    - AgentCardBuilder: Auto-generate agent cards

    CONSUMING (Client-side):
    - RemoteA2aAgent: Connect to remote A2A agents
    - Use like any other sub-agent
    """)


# =============================================================================
# Part 3: Single-Process Demo
# =============================================================================

def create_greeter_agent():
    """Create a simple agent that greets users."""
    return LlmAgent(
        name="GreeterAgent",
        model="gemini-2.0-flash",
        description="A friendly agent that greets users and answers basic questions.",
        instruction="""You are a friendly greeter agent.
        When someone says hello, respond warmly.
        Keep responses brief and cheerful.
        If asked what you can do, explain you're a demo A2A agent.""",
    )


def run_a2a_server(app, host: str, port: int):
    """Run the A2A server in a background thread."""
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


async def demo_a2a_communication():
    """Demonstrate A2A communication in a single process."""
    print("\n  Setting up A2A demo...")

    # Create the agent to expose
    greeter = create_greeter_agent()

    # Convert to A2A service
    a2a_app = to_a2a(agent=greeter, host="127.0.0.1", port=8001)

    # Start server in background thread
    server_thread = threading.Thread(
        target=run_a2a_server,
        args=(a2a_app, "127.0.0.1", 8001),
        daemon=True
    )
    server_thread.start()

    # Wait for server to start
    print("  Waiting for server to start...")
    time.sleep(2)

    print("  Server running at http://127.0.0.1:8001")
    print("  Agent card at: http://127.0.0.1:8001/.well-known/agent-card.json")

    # Create a client agent that uses the remote greeter
    remote_greeter = RemoteA2aAgent(
        name="remote_greeter",
        description="Remote greeter agent via A2A",
        agent_card="http://127.0.0.1:8001/.well-known/agent-card.json",
    )

    # Create orchestrator that uses the remote agent
    orchestrator = LlmAgent(
        name="Orchestrator",
        model="gemini-2.0-flash",
        instruction="""You coordinate with the remote_greeter agent.
        When the user wants to say hello, transfer to the remote_greeter.
        Otherwise, respond directly.""",
        sub_agents=[remote_greeter],
    )

    # Run the orchestrator
    session_service = InMemorySessionService()
    runner = Runner(
        agent=orchestrator,
        app_name="a2a_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="a2a_demo",
        user_id="user1",
        session_id="session1",
    )

    # Send a message
    print("\n  --- Sending message through A2A ---")
    print("  User: Hello there!")

    user_message = types.Content(parts=[types.Part(text="Hello there!")])

    response_text = ""
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            response_text = event.content.parts[0].text

    print(f"  Response: {response_text}")

    print("\n  A2A communication successful!")


# =============================================================================
# Part 4: Request/Response Lifecycle
# =============================================================================

def explain_lifecycle():
    """Explain the A2A request/response lifecycle."""
    print("""
    A2A REQUEST/RESPONSE LIFECYCLE
    ==============================

    1. DISCOVERY
       Client fetches: GET /.well-known/agent-card.json
       Learns about agent capabilities

    2. TASK CREATION
       Client sends JSON-RPC request:
       POST /
       {
         "jsonrpc": "2.0",
         "method": "tasks/send",
         "params": {
           "message": { "parts": [...] }
         }
       }

    3. SERVER PROCESSING
       A2A Server:
       ├── Receives JSON-RPC request
       ├── Converts A2A message → ADK Content
       ├── Creates/gets session
       ├── Runs ADK agent
       └── Converts ADK events → A2A responses

    4. RESPONSE
       Server sends back:
       {
         "jsonrpc": "2.0",
         "result": {
           "status": "completed",
           "artifacts": [...]
         }
       }


    DATA CONVERSION FLOW
    ====================

    Incoming:
    A2A Part → google.genai.types.Part
    A2A Message → types.Content

    Outgoing:
    ADK Event → A2A TaskUpdate
    types.Part → A2A Part


    STREAMING (Optional)
    ====================

    A2A supports streaming for long-running tasks:
    - Server sends incremental updates
    - Client receives partial results
    - Useful for real-time feedback
    """)


# =============================================================================
# Main
# =============================================================================

async def main():
    print("\n" + "#" * 70)
    print("# Lab 8 Exercise 1: A2A Basics")
    print("#" * 70)

    # =========================================================================
    # Part 1: What is A2A
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 1: What is A2A and Why Use It")
    print("=" * 60)

    explain_a2a()

    # =========================================================================
    # Part 2: Key Concepts
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 2: Key A2A Concepts")
    print("=" * 60)

    explain_key_concepts()

    # =========================================================================
    # Part 3: Live Demo
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 3: Single-Process A2A Demo")
    print("=" * 60)

    print("""
    This demo runs both server and client in one process:
    - Server: Exposes GreeterAgent via A2A on port 8001
    - Client: Uses RemoteA2aAgent to connect to server
    - Communication happens over HTTP (localhost)
    """)

    await demo_a2a_communication()

    # =========================================================================
    # Part 4: Lifecycle
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 4: Request/Response Lifecycle")
    print("=" * 60)

    explain_lifecycle()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#" * 70)
    print("# Summary: A2A Basics")
    print("#" * 70)
    print("""
    A2A PROTOCOL:
    -------------
    - Open standard for agent-to-agent communication
    - JSON-RPC over HTTP
    - Agent discovery via well-known endpoint
    - Framework-agnostic

    ADK A2A SUPPORT:
    ----------------
    - to_a2a(): Expose agents as A2A services
    - RemoteA2aAgent: Consume remote A2A agents
    - AgentCardBuilder: Auto-generate agent cards
    - Full bidirectional support

    KEY COMPONENTS:
    ---------------
    1. Agent Card: Describes agent capabilities
    2. Well-known endpoint: /.well-known/agent-card.json
    3. JSON-RPC: Communication protocol
    4. Tasks: Unit of work in A2A

    USE CASES:
    ----------
    - Distributed agent systems
    - Cross-organization collaboration
    - Microservice-style agent architecture
    - Specialized expert agents

    NEXT STEPS:
    -----------
    - Exercise 2: Deep dive into exposing agents
    - Exercise 3: Consuming remote agents
    - Exercise 4: Agent card customization
    - Exercise 5: Multi-process distributed system
    """)


if __name__ == "__main__":
    asyncio.run(main())
