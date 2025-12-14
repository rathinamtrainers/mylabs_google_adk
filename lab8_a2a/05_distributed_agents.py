"""
Lab 8 - Exercise 5: Distributed Agents
======================================

This exercise demonstrates a realistic multi-process distributed agent system:
1. Architecture overview (coordinator + remote specialists)
2. Starting server agents
3. Building orchestrator that consumes remote agents
4. End-to-end workflow demonstration
5. Shutdown and cleanup

Run: uv run python 05_distributed_agents.py

For the full multi-process experience:
1. Terminal 1: cd server && uv run python math_agent.py
2. Terminal 2: cd server && uv run python weather_agent.py
3. Terminal 3: uv run python 05_distributed_agents.py --external-servers

This exercise runs servers in-process by default for convenience.
"""

import argparse
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
# Part 1: Architecture Overview
# =============================================================================

def explain_architecture():
    """Explain the distributed architecture."""
    print("""
    DISTRIBUTED AGENT ARCHITECTURE
    ==============================

    This exercise demonstrates a realistic distributed system:


    ARCHITECTURE:
    -------------

    ┌─────────────────────────────────────────────────────────────┐
    │                     User/Client                              │
    └─────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │              Orchestrator Agent (Port 8000)                  │
    │  - Routes requests to appropriate specialists                │
    │  - Coordinates multi-step workflows                          │
    │  - Aggregates responses                                      │
    └───────────┬─────────────────────────────────┬───────────────┘
                │                                 │
                │ A2A                             │ A2A
                ▼                                 ▼
    ┌───────────────────────┐       ┌───────────────────────┐
    │  Math Agent (8001)    │       │  Weather Agent (8002) │
    │  - add, subtract      │       │  - get_weather        │
    │  - multiply, divide   │       │  - get_forecast       │
    └───────────────────────┘       └───────────────────────┘


    BENEFITS:
    ---------
    1. SCALABILITY
       - Each agent scales independently
       - Add more instances as needed
       - Load balance across agents

    2. ISOLATION
       - Failure in one agent doesn't crash others
       - Each agent has its own resources
       - Independent deployment

    3. SPECIALIZATION
       - Domain experts in separate services
       - Different teams own different agents
       - Mix of technologies/frameworks

    4. SECURITY
       - Network boundaries between agents
       - Access control per agent
       - Audit logging


    REAL-WORLD EXAMPLES:
    --------------------
    - Company A's customer service bot calls Company B's shipping agent
    - Finance agent calls trading agent and risk agent in parallel
    - Main assistant delegates to specialized domain experts
    """)


# =============================================================================
# Part 2: Create Server Agents (for in-process demo)
# =============================================================================

def create_math_agent():
    """Create math agent for demo."""

    def add(a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    def subtract(a: float, b: float) -> float:
        """Subtract b from a."""
        return a - b

    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    def divide(a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    return LlmAgent(
        name="MathAgent",
        model="gemini-2.0-flash",
        description="Math specialist for arithmetic operations.",
        instruction="Use tools for calculations. Show your work.",
        tools=[add, subtract, multiply, divide],
    )


def create_weather_agent():
    """Create weather agent for demo."""

    MOCK_WEATHER = {
        "new york": {"temp": 72, "condition": "Partly Cloudy"},
        "los angeles": {"temp": 85, "condition": "Sunny"},
        "chicago": {"temp": 68, "condition": "Windy"},
        "london": {"temp": 58, "condition": "Rainy"},
        "tokyo": {"temp": 75, "condition": "Clear"},
    }

    def get_weather(city: str) -> dict:
        """Get current weather for a city."""
        city_lower = city.lower()
        if city_lower in MOCK_WEATHER:
            data = MOCK_WEATHER[city_lower]
            return {"city": city, "temp_f": data["temp"], "condition": data["condition"]}
        return {"city": city, "temp_f": 70, "condition": "Unknown"}

    def get_forecast(city: str, days: int = 3) -> dict:
        """Get weather forecast."""
        current = get_weather(city)
        forecasts = [
            {"day": i + 1, "temp_f": current["temp_f"] + (i * 2 - 3)}
            for i in range(min(days, 5))
        ]
        return {"city": city, "forecasts": forecasts}

    return LlmAgent(
        name="WeatherAgent",
        model="gemini-2.0-flash",
        description="Weather specialist for forecasts and conditions.",
        instruction="Use tools to get weather info. Present it clearly.",
        tools=[get_weather, get_forecast],
    )


def run_server_background(app, port: int, name: str):
    """Run server in background thread."""
    print(f"  Starting {name} on port {port}...")
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def start_servers_in_process():
    """Start both servers in background threads."""
    print("\n  Starting server agents in background threads...")

    # Math agent server
    math_agent = create_math_agent()
    math_app = to_a2a(agent=math_agent, host="127.0.0.1", port=8001)
    math_thread = threading.Thread(
        target=run_server_background,
        args=(math_app, 8001, "MathAgent"),
        daemon=True
    )
    math_thread.start()

    # Weather agent server
    weather_agent = create_weather_agent()
    weather_app = to_a2a(agent=weather_agent, host="127.0.0.1", port=8002)
    weather_thread = threading.Thread(
        target=run_server_background,
        args=(weather_app, 8002, "WeatherAgent"),
        daemon=True
    )
    weather_thread.start()

    # Wait for servers to start
    time.sleep(3)

    print("  Both servers started!")
    print("    MathAgent: http://127.0.0.1:8001")
    print("    WeatherAgent: http://127.0.0.1:8002")

    return math_thread, weather_thread


# =============================================================================
# Part 3: Create Orchestrator
# =============================================================================

def create_orchestrator():
    """Create orchestrator that uses remote agents."""
    print("\n  Creating orchestrator with remote agents...")

    # Remote agent references
    remote_math = RemoteA2aAgent(
        name="math_specialist",
        description="Remote math agent for calculations (add, subtract, multiply, divide)",
        agent_card="http://127.0.0.1:8001/.well-known/agent-card.json",
        timeout=30,
    )

    remote_weather = RemoteA2aAgent(
        name="weather_specialist",
        description="Remote weather agent for forecasts and conditions",
        agent_card="http://127.0.0.1:8002/.well-known/agent-card.json",
        timeout=30,
    )

    # Orchestrator
    orchestrator = LlmAgent(
        name="Orchestrator",
        model="gemini-2.0-flash",
        description="Main coordinator that routes requests to specialists.",
        instruction="""You are an intelligent assistant that coordinates with specialists.

        Available specialists:
        - math_specialist: For any calculations (add, subtract, multiply, divide)
        - weather_specialist: For weather information and forecasts

        Routing rules:
        1. Math questions → delegate to math_specialist
        2. Weather questions → delegate to weather_specialist
        3. Combined questions → delegate to both as needed
        4. Other questions → answer directly

        When delegating, transfer control to the appropriate specialist.
        For complex requests, you may need to combine results from multiple specialists.""",
        sub_agents=[remote_math, remote_weather],
    )

    print("  Orchestrator created with 2 remote specialists")
    return orchestrator


# =============================================================================
# Part 4: Run Demo Workflow
# =============================================================================

async def run_demo_workflow(orchestrator):
    """Run demonstration workflow."""
    print("\n  Setting up runner...")

    session_service = InMemorySessionService()
    runner = Runner(
        agent=orchestrator,
        app_name="distributed_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="distributed_demo",
        user_id="user1",
        session_id="demo_session",
    )

    # Test scenarios
    scenarios = [
        {
            "name": "Math Calculation",
            "message": "What is 42 multiplied by 17?",
            "expected_agent": "math",
        },
        {
            "name": "Weather Query",
            "message": "What's the weather like in Tokyo?",
            "expected_agent": "weather",
        },
        {
            "name": "Combined Query",
            "message": "If it's 72°F in New York and 85°F in LA, what's the temperature difference?",
            "expected_agent": "both",
        },
        {
            "name": "Direct Question",
            "message": "What's the capital of France?",
            "expected_agent": "orchestrator",
        },
    ]

    print("\n" + "=" * 60)
    print("RUNNING DEMO WORKFLOW")
    print("=" * 60)

    for scenario in scenarios:
        print(f"\n  --- {scenario['name']} ---")
        print(f"  Expected routing: {scenario['expected_agent']}")
        print(f"  User: {scenario['message']}")

        user_message = types.Content(parts=[types.Part(text=scenario['message'])])

        response_text = ""
        agents_involved = []

        async for event in runner.run_async(
            user_id="user1",
            session_id="demo_session",
            new_message=user_message,
        ):
            if hasattr(event, 'author') and event.author:
                if event.author not in agents_involved:
                    agents_involved.append(event.author)

            if event.is_final_response() and event.content:
                response_text = event.content.parts[0].text

        print(f"  Agents: {' → '.join(agents_involved)}")
        print(f"  Response: {response_text[:150]}...")

    return True


# =============================================================================
# Part 5: Explain Multi-Process Mode
# =============================================================================

def explain_multi_process_mode():
    """Explain how to run in true multi-process mode."""
    print("""
    TRUE MULTI-PROCESS MODE
    =======================

    For a realistic distributed setup, run each component separately:


    TERMINAL 1 - Math Agent:
    ------------------------
    cd /home/agenticai/research_gadk/mylabs/lab8_a2a/server
    uv run python math_agent.py

    Output:
    Starting Math Agent A2A Server
    A2A: http://localhost:8001/
    Agent Card: http://localhost:8001/.well-known/agent-card.json


    TERMINAL 2 - Weather Agent:
    ---------------------------
    cd /home/agenticai/research_gadk/mylabs/lab8_a2a/server
    uv run python weather_agent.py

    Output:
    Starting Weather Agent A2A Server
    A2A: http://localhost:8002/
    Agent Card: http://localhost:8002/.well-known/agent-card.json


    TERMINAL 3 - Orchestrator:
    --------------------------
    cd /home/agenticai/research_gadk/mylabs/lab8_a2a
    uv run python 05_distributed_agents.py --external-servers


    BENEFITS OF MULTI-PROCESS:
    --------------------------
    1. True isolation between agents
    2. Independent resource allocation
    3. Can run on different machines
    4. Realistic production simulation
    5. Independent restarts/updates


    PRODUCTION DEPLOYMENT:
    ----------------------
    In production, you might:
    - Run agents in Docker containers
    - Deploy to Kubernetes
    - Use cloud services (Cloud Run, App Engine)
    - Set up load balancers
    - Configure service discovery
    """)


# =============================================================================
# Main
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Distributed Agents Demo")
    parser.add_argument(
        "--external-servers",
        action="store_true",
        help="Use external servers instead of starting in-process"
    )
    args = parser.parse_args()

    print("\n" + "#" * 70)
    print("# Lab 8 Exercise 5: Distributed Agents")
    print("#" * 70)

    # =========================================================================
    # Part 1: Architecture Overview
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 1: Architecture Overview")
    print("=" * 60)

    explain_architecture()

    # =========================================================================
    # Part 2: Start Servers
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 2: Starting Server Agents")
    print("=" * 60)

    if args.external_servers:
        print("""
    Running in EXTERNAL SERVER mode.

    Make sure you have started:
    - MathAgent on port 8001
    - WeatherAgent on port 8002

    See the instructions in this exercise's docstring.
        """)
    else:
        print("""
    Running in IN-PROCESS mode (for convenience).

    Both servers will run in background threads.
    For true multi-process, use: --external-servers
        """)
        start_servers_in_process()

    # =========================================================================
    # Part 3: Create Orchestrator
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 3: Creating Orchestrator")
    print("=" * 60)

    orchestrator = create_orchestrator()

    # =========================================================================
    # Part 4: Demo Workflow
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 4: End-to-End Demo")
    print("=" * 60)

    await run_demo_workflow(orchestrator)

    # =========================================================================
    # Part 5: Multi-Process Instructions
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 5: True Multi-Process Mode")
    print("=" * 60)

    explain_multi_process_mode()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#" * 70)
    print("# Summary: Distributed Agents")
    print("#" * 70)
    print("""
    DISTRIBUTED ARCHITECTURE:
    -------------------------
    - Orchestrator coordinates requests
    - Specialists handle domain tasks
    - A2A protocol enables communication
    - Each agent runs independently

    COMPONENTS:
    -----------
    1. MathAgent (port 8001)
       - Arithmetic operations
       - Tools: add, subtract, multiply, divide

    2. WeatherAgent (port 8002)
       - Weather information
       - Tools: get_weather, get_forecast

    3. Orchestrator (client)
       - Routes to specialists
       - Combines results
       - Handles general questions

    RUNNING MODES:
    --------------
    In-Process (default):
    - All in one Python process
    - Background threads
    - Easy for development

    Multi-Process:
    - Separate terminals
    - True isolation
    - Production-like

    KEY LEARNINGS:
    --------------
    1. A2A enables distributed agent systems
    2. RemoteA2aAgent integrates transparently
    3. Orchestrator doesn't know about network
    4. Agents can be anywhere on network
    5. Mix local and remote seamlessly

    PRODUCTION CONSIDERATIONS:
    --------------------------
    - Use HTTPS in production
    - Implement authentication
    - Add monitoring/logging
    - Configure timeouts
    - Plan for failures

    CONGRATULATIONS!
    ----------------
    You've completed all Lab 8 exercises on A2A protocol!

    You now know how to:
    ✓ Expose ADK agents via A2A
    ✓ Consume remote A2A agents
    ✓ Create and customize agent cards
    ✓ Build distributed multi-agent systems
    """)


if __name__ == "__main__":
    asyncio.run(main())
