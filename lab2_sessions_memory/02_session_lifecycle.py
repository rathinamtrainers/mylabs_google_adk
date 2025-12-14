"""
Lab 2 - Exercise 2: Session Lifecycle
======================================

This exercise demonstrates the complete session lifecycle:
1. Create -> Use -> Update -> Delete
2. How events are appended to sessions
3. State updates through events
4. Resuming conversations

Run: uv run python 02_session_lifecycle.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Tool that modifies state
# =============================================================================
def set_preference(preference_name: str, preference_value: str, tool_context: ToolContext) -> dict:
    """Set a user preference in state."""
    tool_context.state[f"pref:{preference_name}"] = preference_value
    return {"status": "saved", "preference": preference_name, "value": preference_value}


def get_preferences(tool_context: ToolContext) -> dict:
    """Get all user preferences from state."""
    prefs = {}
    # Iterate through state keys that start with "pref:"
    for key in ["pref:theme", "pref:language", "pref:timezone"]:
        val = tool_context.state.get(key)
        if val:
            prefs[key.replace("pref:", "")] = val
    return {"preferences": prefs}


set_pref_tool = FunctionTool(func=set_preference)
get_pref_tool = FunctionTool(func=get_preferences)


# =============================================================================
# Create agent
# =============================================================================
preferences_agent = LlmAgent(
    name="PreferencesAgent",
    model="gemini-2.0-flash",
    instruction="""You are a preferences assistant.
    Help users set and retrieve their preferences.
    Use set_preference to save preferences (e.g., theme, language, timezone).
    Use get_preferences to show all saved preferences.
    Keep responses brief.""",
    tools=[set_pref_tool, get_pref_tool],
)


async def main():
    print("\n" + "#"*70)
    print("# Lab 2 Exercise 2: Session Lifecycle")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Stage 1: CREATE - Start a new session
    # =========================================================================
    print("\n" + "="*60)
    print("STAGE 1: CREATE - Starting a New Session")
    print("="*60)

    session = await session_service.create_session(
        app_name="preferences_app",
        user_id="user_alice",
        session_id="prefs_session_1",
        state={"user_name": "Alice"}  # Initial state
    )

    print(f"\n  Created session: {session.id}")
    print(f"  Initial state: user_name={session.state.get('user_name')}")
    print(f"  Events: {len(session.events)}")

    # =========================================================================
    # Stage 2: USE - Interact with the session
    # =========================================================================
    print("\n" + "="*60)
    print("STAGE 2: USE - Agent Interactions Add Events")
    print("="*60)

    runner = Runner(
        agent=preferences_agent,
        app_name="preferences_app",
        session_service=session_service,
    )

    # First interaction: Set a preference
    print("\n  --- Interaction 1: Setting theme preference ---")
    user_message = types.Content(
        parts=[types.Part(text="Set my theme to dark mode")]
    )
    async for event in runner.run_async(
        user_id="user_alice",
        session_id="prefs_session_1",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Agent: {event.content.parts[0].text}")

    # Check session state after interaction
    session = await session_service.get_session(
        app_name="preferences_app",
        user_id="user_alice",
        session_id="prefs_session_1"
    )
    print(f"\n  State after interaction 1:")
    print(f"    pref:theme = {session.state.get('pref:theme')}")
    print(f"    Events: {len(session.events)}")

    # Second interaction: Set another preference
    print("\n  --- Interaction 2: Setting language preference ---")
    user_message = types.Content(
        parts=[types.Part(text="Set my language to Spanish")]
    )
    async for event in runner.run_async(
        user_id="user_alice",
        session_id="prefs_session_1",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Agent: {event.content.parts[0].text}")

    session = await session_service.get_session(
        app_name="preferences_app",
        user_id="user_alice",
        session_id="prefs_session_1"
    )
    print(f"\n  State after interaction 2:")
    print(f"    pref:theme = {session.state.get('pref:theme')}")
    print(f"    pref:language = {session.state.get('pref:language')}")
    print(f"    Events: {len(session.events)}")

    # =========================================================================
    # Stage 3: RESUME - Continue an existing session
    # =========================================================================
    print("\n" + "="*60)
    print("STAGE 3: RESUME - Continuing Existing Session")
    print("="*60)

    print("\n  Simulating app restart... (session persists in service)")

    # In a real app, you'd retrieve the session by ID
    # The runner uses session_id to find the existing session
    print("\n  --- Interaction 3: Asking about preferences ---")
    user_message = types.Content(
        parts=[types.Part(text="What are my current preferences?")]
    )
    async for event in runner.run_async(
        user_id="user_alice",
        session_id="prefs_session_1",  # Same session ID = resume
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Agent: {event.content.parts[0].text}")

    session = await session_service.get_session(
        app_name="preferences_app",
        user_id="user_alice",
        session_id="prefs_session_1"
    )
    print(f"\n  Session has full history: {len(session.events)} events")
    print("  Agent remembers previous context from same session!")

    # =========================================================================
    # Stage 4: EXAMINE - Look at event history
    # =========================================================================
    print("\n" + "="*60)
    print("STAGE 4: EXAMINE - Event History")
    print("="*60)

    print(f"\n  Session {session.id} event summary:")
    for i, event in enumerate(session.events):
        author = event.author if hasattr(event, 'author') else "unknown"
        event_type = "text"
        if hasattr(event, 'actions') and event.actions:
            if event.actions.state_delta:
                event_type = "text + state_update"

        preview = ""
        if event.content and event.content.parts:
            part = event.content.parts[0]
            if hasattr(part, 'text') and part.text:
                preview = part.text[:40] + "..."
            elif hasattr(part, 'function_call') and part.function_call:
                preview = f"[function_call: {part.function_call.name}]"

        print(f"    {i+1}. [{author}] {event_type}")
        if preview:
            print(f"        {preview}")

    # =========================================================================
    # Stage 5: DELETE - Clean up session
    # =========================================================================
    print("\n" + "="*60)
    print("STAGE 5: DELETE - Cleaning Up")
    print("="*60)

    # Before deletion
    sessions = await session_service.list_sessions(
        app_name="preferences_app",
        user_id="user_alice"
    )
    print(f"\n  Sessions before delete: {[s.id for s in sessions.sessions]}")

    # Delete the session
    await session_service.delete_session(
        app_name="preferences_app",
        user_id="user_alice",
        session_id="prefs_session_1"
    )
    print("  Deleted: prefs_session_1")

    # After deletion
    sessions = await session_service.list_sessions(
        app_name="preferences_app",
        user_id="user_alice"
    )
    print(f"  Sessions after delete: {[s.id for s in sessions.sessions]}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Session Lifecycle")
    print("#"*70)
    print("""
    SESSION LIFECYCLE STAGES:
    -------------------------

    1. CREATE
       session = await service.create_session(
           app_name="app", user_id="user", session_id="optional_id",
           state={"initial": "data"}
       )

    2. USE (via Runner)
       - Runner automatically uses the session
       - Each interaction appends events
       - State changes are tracked in events

    3. RESUME
       - Use same session_id in runner.run_async()
       - Session history is preserved
       - Agent has access to full context

    4. EXAMINE
       - session.events contains all interactions
       - Each event has: author, content, actions
       - actions.state_delta shows state changes

    5. DELETE
       await service.delete_session(app_name, user_id, session_id)
       - Removes session and all its data

    HOW EVENTS WORK:
    ----------------
    - User message -> Event (author="user")
    - Agent response -> Event (author="agent_name")
    - Tool call -> Part of agent event
    - State changes -> Captured in event.actions.state_delta

    KEY INSIGHT:
    ------------
    The session lifecycle enables:
    - Persistent conversations
    - State that survives across interactions
    - Full conversation history for context
    - Clean cleanup when done
    """)


if __name__ == "__main__":
    asyncio.run(main())
