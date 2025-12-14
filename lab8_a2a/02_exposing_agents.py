"""
Lab 8 - Exercise 2: Exposing Agents
===================================

This exercise covers how to expose ADK agents as A2A services:
1. Using to_a2a() function
2. Understanding auto-generated agent cards
3. Custom agent card configuration
4. Server startup and verification
5. Testing the well-known endpoint

Run: uv run python 02_exposing_agents.py

Or run as standalone server:
    uvicorn 02_exposing_agents:app --host 0.0.0.0 --port 8001
"""

import asyncio
import json
import threading
import time
import httpx
import uvicorn
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a


# =============================================================================
# Part 1: Basic Agent to Expose
# =============================================================================

def create_translator_agent():
    """Create a translator agent to expose via A2A."""

    def translate_to_spanish(text: str) -> str:
        """Translate text to Spanish.

        Args:
            text: Text to translate

        Returns:
            Spanish translation (mock)
        """
        # Simple mock translations for demo
        translations = {
            "hello": "hola",
            "goodbye": "adiós",
            "thank you": "gracias",
            "please": "por favor",
            "yes": "sí",
            "no": "no",
        }
        lower_text = text.lower()
        if lower_text in translations:
            return translations[lower_text]
        return f"[Spanish translation of: {text}]"

    def translate_to_french(text: str) -> str:
        """Translate text to French.

        Args:
            text: Text to translate

        Returns:
            French translation (mock)
        """
        translations = {
            "hello": "bonjour",
            "goodbye": "au revoir",
            "thank you": "merci",
            "please": "s'il vous plaît",
            "yes": "oui",
            "no": "non",
        }
        lower_text = text.lower()
        if lower_text in translations:
            return translations[lower_text]
        return f"[French translation of: {text}]"

    return LlmAgent(
        name="TranslatorAgent",
        model="gemini-2.0-flash",
        description="A translation specialist that translates text between languages. "
                    "Supports Spanish and French translations.",
        instruction="""You are a translation specialist.
        Use your tools to translate text:
        - translate_to_spanish(text): Translate to Spanish
        - translate_to_french(text): Translate to French

        When asked to translate, use the appropriate tool.
        Provide the translation clearly and offer to translate more.""",
        tools=[translate_to_spanish, translate_to_french],
    )


# =============================================================================
# Part 2: Using to_a2a() Function
# =============================================================================

def explain_to_a2a():
    """Explain the to_a2a() function."""
    print("""
    THE to_a2a() FUNCTION
    =====================

    to_a2a() is the simplest way to expose an ADK agent as an A2A service.

    Basic Usage:
    ------------
    from google.adk.a2a.utils.agent_to_a2a import to_a2a

    app = to_a2a(agent=my_agent)

    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)


    Parameters:
    -----------
    agent: BaseAgent
        The ADK agent to expose

    host: str = "localhost"
        Host for generating URLs in agent card

    port: int = 8000
        Port for generating URLs in agent card

    protocol: str = "http"
        Protocol (http or https)

    agent_card: AgentCard | str | None = None
        Custom agent card (optional)
        - If None: auto-generates from agent
        - If str: path to JSON file
        - If AgentCard: use directly

    session_service: BaseSessionService | None = None
        Custom session service (optional)
        Default: InMemorySessionService

    artifact_service: BaseArtifactService | None = None
        Custom artifact service (optional)


    Returns:
    --------
    Starlette application ready to serve via ASGI server


    What to_a2a() Does:
    -------------------
    1. Creates session/artifact services if not provided
    2. Builds agent card if not provided
    3. Sets up A2A JSON-RPC endpoint
    4. Configures well-known agent card endpoint
    5. Returns ASGI application
    """)


# =============================================================================
# Part 3: Auto-Generated Agent Cards
# =============================================================================

def explain_auto_agent_cards():
    """Explain automatic agent card generation."""
    print("""
    AUTO-GENERATED AGENT CARDS
    ==========================

    When you don't provide an agent_card to to_a2a(), the AgentCardBuilder
    automatically creates one from your agent's metadata.


    What Gets Extracted:
    --------------------
    1. name: From agent.name
    2. description: From agent.description
    3. url: Generated from host/port/protocol
    4. version: Default "1.0.0"
    5. skills: Extracted from agent configuration
       - Main model skill
       - Tool-based skills
       - Sub-agent skills


    Skill Detection:
    ----------------
    AgentCardBuilder analyzes your agent and creates skills for:
    - The main LLM capability
    - Each tool the agent has
    - Each sub-agent's capabilities


    Example Generated Card:
    -----------------------
    {
      "name": "TranslatorAgent",
      "description": "A translation specialist...",
      "url": "http://localhost:8001/",
      "version": "1.0.0",
      "capabilities": {},
      "skills": [
        {
          "id": "translator_agent_skill",
          "name": "TranslatorAgent",
          "description": "A translation specialist...",
          "tags": []
        }
      ],
      "defaultInputModes": ["text/plain"],
      "defaultOutputModes": ["text/plain"]
    }
    """)


# =============================================================================
# Part 4: Create and Start Server
# =============================================================================

# Create the agent
translator_agent = create_translator_agent()

# Create A2A application (for standalone server mode)
app = to_a2a(
    agent=translator_agent,
    host="localhost",
    port=8001,
    protocol="http",
)


def run_server_in_background(app, host: str, port: int):
    """Run server in a background thread."""
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


# =============================================================================
# Part 5: Verify the Server
# =============================================================================

async def verify_server(base_url: str):
    """Verify the A2A server is running correctly."""
    print(f"\n  Verifying server at {base_url}...")

    async with httpx.AsyncClient() as client:
        # Check agent card endpoint
        try:
            response = await client.get(f"{base_url}/.well-known/agent-card.json")
            if response.status_code == 200:
                print("  [OK] Agent card endpoint accessible")
                agent_card = response.json()

                print("\n  Agent Card Contents:")
                print(f"    Name: {agent_card.get('name', 'N/A')}")
                print(f"    Description: {agent_card.get('description', 'N/A')[:60]}...")
                print(f"    URL: {agent_card.get('url', 'N/A')}")
                print(f"    Version: {agent_card.get('version', 'N/A')}")

                skills = agent_card.get('skills', [])
                print(f"    Skills: {len(skills)} skill(s)")
                for skill in skills[:3]:  # Show first 3
                    print(f"      - {skill.get('name', 'Unknown')}")

                print(f"\n  Full agent card:\n{json.dumps(agent_card, indent=2)}")
            else:
                print(f"  [ERROR] Agent card returned status {response.status_code}")
        except Exception as e:
            print(f"  [ERROR] Could not fetch agent card: {e}")


# =============================================================================
# Main
# =============================================================================

async def main():
    print("\n" + "#" * 70)
    print("# Lab 8 Exercise 2: Exposing Agents")
    print("#" * 70)

    # =========================================================================
    # Part 1: Introduction
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 1: Introduction to Agent Exposure")
    print("=" * 60)

    print("""
    In this exercise, we'll expose a TranslatorAgent via A2A.

    The agent has two tools:
    - translate_to_spanish(text)
    - translate_to_french(text)

    We'll see how to_a2a() wraps this agent for network access.
    """)

    # =========================================================================
    # Part 2: to_a2a() Function
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 2: The to_a2a() Function")
    print("=" * 60)

    explain_to_a2a()

    # =========================================================================
    # Part 3: Auto-Generated Agent Cards
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 3: Auto-Generated Agent Cards")
    print("=" * 60)

    explain_auto_agent_cards()

    # =========================================================================
    # Part 4: Start and Verify Server
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 4: Starting and Verifying Server")
    print("=" * 60)

    print("\n  Starting A2A server in background...")

    # Start server in background thread
    server_thread = threading.Thread(
        target=run_server_in_background,
        args=(app, "127.0.0.1", 8001),
        daemon=True
    )
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    print("  Server started!")
    print("  Endpoints:")
    print("    A2A: http://127.0.0.1:8001/")
    print("    Agent Card: http://127.0.0.1:8001/.well-known/agent-card.json")

    # Verify server
    await verify_server("http://127.0.0.1:8001")

    # =========================================================================
    # Part 5: Alternative: Standalone Server
    # =========================================================================
    print("\n" + "=" * 60)
    print("PART 5: Running as Standalone Server")
    print("=" * 60)

    print("""
    STANDALONE SERVER MODE
    ======================

    Instead of running in a script, you can run the server standalone:

    1. This file exports 'app' at module level:
       app = to_a2a(agent=translator_agent)

    2. Run with uvicorn:
       uvicorn 02_exposing_agents:app --host 0.0.0.0 --port 8001

    3. Or with auto-reload for development:
       uvicorn 02_exposing_agents:app --host 0.0.0.0 --port 8001 --reload


    PRODUCTION CONSIDERATIONS
    =========================

    1. Use HTTPS in production:
       app = to_a2a(agent=agent, protocol="https")

    2. Configure proper host:
       app = to_a2a(agent=agent, host="api.example.com")

    3. Use persistent session service:
       from google.adk.sessions import DatabaseSessionService
       app = to_a2a(agent=agent, session_service=db_session_service)

    4. Add authentication (via middleware)

    5. Configure CORS if needed
    """)

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#" * 70)
    print("# Summary: Exposing Agents")
    print("#" * 70)
    print("""
    EXPOSING AGENTS VIA A2A:
    ------------------------
    1. Create your ADK agent normally
    2. Call to_a2a(agent=agent)
    3. Run with uvicorn

    to_a2a() PARAMETERS:
    --------------------
    - agent: The agent to expose (required)
    - host/port/protocol: For URL generation
    - agent_card: Custom card (optional)
    - session_service: Custom sessions (optional)

    AUTO-GENERATED CARDS:
    ---------------------
    - Extracts name, description from agent
    - Creates skills from tools/sub-agents
    - Sets default input/output modes

    ENDPOINTS CREATED:
    ------------------
    - / : A2A JSON-RPC endpoint
    - /.well-known/agent-card.json : Agent discovery

    RUNNING THE SERVER:
    -------------------
    # In script:
    uvicorn.run(app, host="0.0.0.0", port=8001)

    # Standalone:
    uvicorn module:app --port 8001

    NEXT STEPS:
    -----------
    Exercise 3: Learn to consume A2A agents with RemoteA2aAgent
    """)


if __name__ == "__main__":
    asyncio.run(main())
