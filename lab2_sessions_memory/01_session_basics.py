"""
Lab 2 - Exercise 1: Session Basics
===================================

This exercise demonstrates the fundamentals of Sessions in Google ADK:
1. Creating a Session with SessionService
2. Session properties (id, app_name, user_id, state, events)
3. Session as a conversation container
4. Examining session after agent interactions

Run: uv run python 01_session_basics.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Create a simple agent
# =============================================================================
assistant = LlmAgent(
    name="Assistant",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant. Keep responses brief (1-2 sentences).",
)


async def main():
    print("\n" + "#"*70)
    print("# Lab 2 Exercise 1: Session Basics")
    print("#"*70)

    # =========================================================================
    # Part 1: Creating a SessionService
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Creating a SessionService")
    print("="*60)

    # InMemorySessionService stores sessions in memory (lost on restart)
    # Other options: DatabaseSessionService, VertexAiSessionService
    session_service = InMemorySessionService()
    print("  Created InMemorySessionService")
    print("  Note: Data is lost when the application restarts")

    # =========================================================================
    # Part 2: Creating a Session
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Creating a Session")
    print("="*60)

    # Create a new session
    session = await session_service.create_session(
        app_name="my_app",           # Application identifier
        user_id="user_123",          # User identifier
        session_id="conversation_1", # Optional: specific session ID
        state={                      # Optional: initial state
            "user_name": "Alice",
            "preference": "concise"
        }
    )

    print("\n  Session created with properties:")
    print(f"    id:          {session.id}")
    print(f"    app_name:    {session.app_name}")
    print(f"    user_id:     {session.user_id}")
    print(f"    state:       user_name={session.state.get('user_name')}, preference={session.state.get('preference')}")
    print(f"    events:      {len(session.events)} (initially empty)")
    print(f"    last_update: {session.last_update_time}")

    # =========================================================================
    # Part 3: Session as Conversation Container
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Running Agent - Session Captures Events")
    print("="*60)

    runner = Runner(
        agent=assistant,
        app_name="my_app",
        session_service=session_service,
    )

    # First message
    print("\n  --- Turn 1 ---")
    user_message = types.Content(parts=[types.Part(text="What is Python?")])
    async for event in runner.run_async(
        user_id="user_123",
        session_id="conversation_1",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  User: What is Python?")
            print(f"  Agent: {event.content.parts[0].text[:100]}...")

    # Get updated session
    session = await session_service.get_session(
        app_name="my_app",
        user_id="user_123",
        session_id="conversation_1"
    )
    print(f"\n  Events after Turn 1: {len(session.events)}")

    # Second message (continues same session)
    print("\n  --- Turn 2 ---")
    user_message = types.Content(parts=[types.Part(text="What can I build with it?")])
    async for event in runner.run_async(
        user_id="user_123",
        session_id="conversation_1",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  User: What can I build with it?")
            print(f"  Agent: {event.content.parts[0].text[:100]}...")

    # Get updated session again
    session = await session_service.get_session(
        app_name="my_app",
        user_id="user_123",
        session_id="conversation_1"
    )
    print(f"\n  Events after Turn 2: {len(session.events)}")
    print(f"  Last update time: {session.last_update_time}")

    # =========================================================================
    # Part 4: Examining Session Events
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Examining Session Events")
    print("="*60)

    print(f"\n  Total events in session: {len(session.events)}")
    print("\n  Event breakdown:")

    for i, event in enumerate(session.events):
        author = event.author if hasattr(event, 'author') else "unknown"
        has_content = "yes" if event.content else "no"
        content_preview = ""
        if event.content and event.content.parts:
            text = event.content.parts[0].text if hasattr(event.content.parts[0], 'text') else str(event.content.parts[0])
            content_preview = text[:50] + "..." if len(text) > 50 else text

        print(f"    Event {i+1}: author={author}, has_content={has_content}")
        if content_preview:
            print(f"             preview: {content_preview}")

    # =========================================================================
    # Part 5: Retrieving and Listing Sessions
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Retrieving and Listing Sessions")
    print("="*60)

    # Create another session for the same user
    session2 = await session_service.create_session(
        app_name="my_app",
        user_id="user_123",
        session_id="conversation_2",
        state={"topic": "JavaScript"}
    )
    print(f"\n  Created second session: {session2.id}")

    # List all sessions for a user
    sessions = await session_service.list_sessions(
        app_name="my_app",
        user_id="user_123"
    )
    print(f"\n  Sessions for user_123:")
    for s in sessions.sessions:
        print(f"    - {s.id}")

    # Retrieve a specific session
    retrieved = await session_service.get_session(
        app_name="my_app",
        user_id="user_123",
        session_id="conversation_1"
    )
    print(f"\n  Retrieved session: {retrieved.id}")
    print(f"    Events: {len(retrieved.events)}")
    print(f"    State: user_name={retrieved.state.get('user_name')}")

    # =========================================================================
    # Part 6: Deleting a Session
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Deleting a Session")
    print("="*60)

    await session_service.delete_session(
        app_name="my_app",
        user_id="user_123",
        session_id="conversation_2"
    )
    print(f"\n  Deleted session: conversation_2")

    # Verify deletion
    sessions = await session_service.list_sessions(
        app_name="my_app",
        user_id="user_123"
    )
    print(f"  Remaining sessions: {[s.id for s in sessions.sessions]}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Session Basics")
    print("#"*70)
    print("""
    SESSION OBJECT PROPERTIES:
    --------------------------
    - id:               Unique identifier for this conversation
    - app_name:         Application this session belongs to
    - user_id:          User who owns this session
    - state:            Dictionary for session-scoped data
    - events:           List of all interactions (messages, tool calls, etc.)
    - last_update_time: Timestamp of last activity

    SESSION SERVICE OPERATIONS:
    ---------------------------
    - create_session():  Start a new conversation
    - get_session():     Retrieve an existing session
    - list_sessions():   List all sessions for a user
    - delete_session():  Remove a session and its data
    - append_event():    Add an event (usually done by Runner)

    SESSION SERVICE IMPLEMENTATIONS:
    --------------------------------
    - InMemorySessionService:   For development/testing (no persistence)
    - DatabaseSessionService:   For production (SQLite, PostgreSQL, MySQL)
    - VertexAiSessionService:   For Google Cloud deployments

    KEY INSIGHT:
    ------------
    A Session is a conversation container that:
    1. Holds the history of all interactions (events)
    2. Maintains state data specific to this conversation
    3. Enables multi-turn conversations with context
    """)


if __name__ == "__main__":
    asyncio.run(main())
