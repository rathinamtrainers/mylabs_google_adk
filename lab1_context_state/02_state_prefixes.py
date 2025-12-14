"""
Lab 1 - Exercise 2: State Management with Prefixes
===================================================

This exercise demonstrates state scoping with prefixes:
1. No prefix - Session-scoped (current session only)
2. user: prefix - User-scoped (persists across sessions for same user)
3. app: prefix - App-scoped (shared across all users)
4. temp: prefix - Invocation-scoped (discarded after invocation)

Run: uv run python 02_state_prefixes.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Tool that demonstrates all state prefixes
# =============================================================================
def demonstrate_state_prefixes(action: str, tool_context: ToolContext) -> dict:
    """
    A tool that shows how different state prefixes work.

    State Prefixes:
    - No prefix: session.state['key'] - Session-specific
    - user: prefix: session.state['user:key'] - User-specific, across sessions
    - app: prefix: session.state['app:key'] - App-wide, all users
    - temp: prefix: session.state['temp:key'] - Current invocation only
    """
    if action == "write_all":
        # Read current values
        session_counter = tool_context.state.get("session_counter", 0)
        user_login = tool_context.state.get("user:login_count", 0)
        app_requests = tool_context.state.get("app:total_requests", 0)

        # Write to all state scopes
        tool_context.state["session_counter"] = session_counter + 1
        tool_context.state["user:preference"] = "dark_mode"
        tool_context.state["user:login_count"] = user_login + 1
        tool_context.state["app:total_requests"] = app_requests + 1
        tool_context.state["temp:request_id"] = "req_12345"
        tool_context.state["temp:processing"] = True

        return {
            "action": "write_all",
            "written": {
                "session_counter": session_counter + 1,
                "user:preference": "dark_mode",
                "user:login_count": user_login + 1,
                "app:total_requests": app_requests + 1,
                "temp:request_id": "req_12345",
            }
        }

    elif action == "read_all":
        return {
            "action": "read_all",
            "session_counter": tool_context.state.get("session_counter", "not set"),
            "user:preference": tool_context.state.get("user:preference", "not set"),
            "user:login_count": tool_context.state.get("user:login_count", "not set"),
            "app:total_requests": tool_context.state.get("app:total_requests", "not set"),
            "temp:request_id": tool_context.state.get("temp:request_id", "not set"),
        }

    return {"action": action, "status": "unknown action"}


state_tool = FunctionTool(func=demonstrate_state_prefixes)


# =============================================================================
# Simple agent for state demonstration
# =============================================================================
state_agent = LlmAgent(
    name="state_prefix_demo",
    model="gemini-2.0-flash",
    instruction="""You are a state demonstration assistant.
    When asked to demonstrate state, use the demonstrate_state_prefixes tool.
    - Use action='write_all' to write to all state scopes
    - Use action='read_all' to read current state
    Just call the tool and report what happened.""",
    tools=[state_tool],
)


# =============================================================================
# Helper function to run agent and show state
# =============================================================================
async def run_and_show_state(
    runner: Runner,
    session_service: InMemorySessionService,
    user_id: str,
    session_id: str,
    message: str,
    description: str
):
    """Run agent and display state before/after."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")

    # Get state before
    session = await session_service.get_session(
        app_name="state_prefix_demo",
        user_id=user_id,
        session_id=session_id
    )

    print(f"\n  State BEFORE:")
    print(f"    session_counter: {session.state.get('session_counter', 'not set')}")
    print(f"    user:preference: {session.state.get('user:preference', 'not set')}")
    print(f"    user:login_count: {session.state.get('user:login_count', 'not set')}")
    print(f"    app:total_requests: {session.state.get('app:total_requests', 'not set')}")

    # Run agent
    user_message = types.Content(parts=[types.Part(text=message)])
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_message,
    ):
        pass  # Process all events

    # Get state after
    session = await session_service.get_session(
        app_name="state_prefix_demo",
        user_id=user_id,
        session_id=session_id
    )

    print(f"\n  State AFTER:")
    print(f"    session_counter: {session.state.get('session_counter', 'not set')}")
    print(f"    user:preference: {session.state.get('user:preference', 'not set')}")
    print(f"    user:login_count: {session.state.get('user:login_count', 'not set')}")
    print(f"    app:total_requests: {session.state.get('app:total_requests', 'not set')}")
    print(f"    temp:request_id: {session.state.get('temp:request_id', 'not set (expected - temp is discarded)')}")


# =============================================================================
# Main demonstration
# =============================================================================
async def main():
    print("\n" + "#"*70)
    print("# Lab 1 Exercise 2: State Management with Prefixes")
    print("#"*70)

    session_service = InMemorySessionService()
    runner = Runner(
        agent=state_agent,
        app_name="state_prefix_demo",
        session_service=session_service,
    )

    # =========================================================================
    # Part 1: Create first session for User A
    # =========================================================================
    print("\n" + "-"*70)
    print("PART 1: First Session for User A")
    print("-"*70)

    await session_service.create_session(
        app_name="state_prefix_demo",
        user_id="user_A",
        session_id="session_1",
        state={}  # Start with empty state
    )

    await run_and_show_state(
        runner, session_service,
        user_id="user_A",
        session_id="session_1",
        message="Please write to all state scopes using action write_all",
        description="User A - Session 1 - First invocation"
    )

    # Second invocation in same session
    await run_and_show_state(
        runner, session_service,
        user_id="user_A",
        session_id="session_1",
        message="Please write to all state scopes again",
        description="User A - Session 1 - Second invocation (note: temp: was reset)"
    )

    # =========================================================================
    # Part 2: Create second session for User A (same user, new session)
    # =========================================================================
    print("\n" + "-"*70)
    print("PART 2: Second Session for User A (same user, different session)")
    print("-"*70)
    print("Note: With InMemorySessionService, user: and app: state won't")
    print("      persist across sessions. With Database/VertexAI services,")
    print("      user: state would persist for the same user.")

    await session_service.create_session(
        app_name="state_prefix_demo",
        user_id="user_A",
        session_id="session_2",
        state={}  # New session starts fresh with InMemory
    )

    await run_and_show_state(
        runner, session_service,
        user_id="user_A",
        session_id="session_2",
        message="Read all state using action read_all",
        description="User A - Session 2 - Fresh session (state reset with InMemory)"
    )

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: State Prefixes")
    print("#"*70)
    print("""
    PREFIX          SCOPE                   PERSISTENCE (with DB/VertexAI)
    --------------- ----------------------- --------------------------------
    (no prefix)     Current session only    Persists within session
    user:           Per user                Shared across user's sessions
    app:            Application-wide        Shared across ALL sessions
    temp:           Current invocation      NEVER persists (discarded)

    EXAMPLES:
    ---------
    state['cart_items']           -> This session only
    state['user:theme']           -> All sessions for this user
    state['app:announcement']     -> All users see this
    state['temp:calculation']     -> Gone after this invocation

    IMPORTANT NOTES:
    ----------------
    1. InMemorySessionService: All state is lost on restart
       - user: and app: don't truly persist across sessions

    2. DatabaseSessionService / VertexAiSessionService:
       - Session state: Persists per session
       - user: state: Persists per user across sessions
       - app: state: Persists globally

    3. temp: prefix: ALWAYS discarded after invocation completes
       - Use for intermediate calculations
       - Use for data passed between tools in same invocation
    """)


if __name__ == "__main__":
    asyncio.run(main())
