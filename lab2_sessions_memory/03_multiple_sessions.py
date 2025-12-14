"""
Lab 2 - Exercise 3: Multiple Sessions
======================================

This exercise demonstrates managing multiple sessions:
1. Multiple sessions per user (different conversations)
2. Sessions for different users
3. Session isolation (each session is independent)
4. Listing and managing sessions

Run: uv run python 03_multiple_sessions.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Create agent
# =============================================================================
assistant = LlmAgent(
    name="Assistant",
    model="gemini-2.0-flash",
    instruction="""You are a helpful assistant.
    The user's name is {user_name?}.
    The conversation topic is: {topic?}
    Keep responses brief (1-2 sentences).""",
)


async def run_turn(runner, user_id, session_id, message_text, session_service):
    """Helper to run a single conversation turn and show result."""
    user_message = types.Content(parts=[types.Part(text=message_text)])

    response_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            response_text = event.content.parts[0].text

    # Get session info
    session = await session_service.get_session(
        app_name="multi_session_app",
        user_id=user_id,
        session_id=session_id
    )

    return response_text, len(session.events)


async def main():
    print("\n" + "#"*70)
    print("# Lab 2 Exercise 3: Multiple Sessions")
    print("#"*70)

    session_service = InMemorySessionService()
    runner = Runner(
        agent=assistant,
        app_name="multi_session_app",
        session_service=session_service,
    )

    # =========================================================================
    # Part 1: Multiple Sessions for Same User
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Multiple Sessions for Same User (Alice)")
    print("="*60)
    print("  Each session is a separate conversation thread")

    # Create two sessions for Alice
    session_python = await session_service.create_session(
        app_name="multi_session_app",
        user_id="alice",
        session_id="alice_python_chat",
        state={"user_name": "Alice", "topic": "Python programming"}
    )

    session_cooking = await session_service.create_session(
        app_name="multi_session_app",
        user_id="alice",
        session_id="alice_cooking_chat",
        state={"user_name": "Alice", "topic": "Cooking recipes"}
    )

    print(f"\n  Created session 1: {session_python.id} (topic: Python)")
    print(f"  Created session 2: {session_cooking.id} (topic: Cooking)")

    # Interact with Python session
    print("\n  --- Python Session ---")
    response, events = await run_turn(
        runner, "alice", "alice_python_chat",
        "What is a list comprehension?",
        session_service
    )
    print(f"  User: What is a list comprehension?")
    print(f"  Agent: {response[:100]}...")
    print(f"  Events in this session: {events}")

    # Interact with Cooking session
    print("\n  --- Cooking Session ---")
    response, events = await run_turn(
        runner, "alice", "alice_cooking_chat",
        "How do I make pasta?",
        session_service
    )
    print(f"  User: How do I make pasta?")
    print(f"  Agent: {response[:100]}...")
    print(f"  Events in this session: {events}")

    # Continue Python session (has different context)
    print("\n  --- Back to Python Session ---")
    response, events = await run_turn(
        runner, "alice", "alice_python_chat",
        "Show me an example",
        session_service
    )
    print(f"  User: Show me an example")
    print(f"  Agent: {response[:100]}...")
    print(f"  Events in this session: {events}")
    print("  Note: Agent remembers Python context, not cooking!")

    # =========================================================================
    # Part 2: Sessions for Different Users
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Sessions for Different Users")
    print("="*60)
    print("  Each user has their own isolated sessions")

    # Create session for Bob
    session_bob = await session_service.create_session(
        app_name="multi_session_app",
        user_id="bob",
        session_id="bob_chat",
        state={"user_name": "Bob", "topic": "Music"}
    )

    print(f"\n  Created session for Bob: {session_bob.id}")

    # Bob's interaction
    print("\n  --- Bob's Session ---")
    response, events = await run_turn(
        runner, "bob", "bob_chat",
        "What instruments are in a rock band?",
        session_service
    )
    print(f"  User: What instruments are in a rock band?")
    print(f"  Agent: {response[:100]}...")

    # Alice's sessions are separate
    print("\n  --- Listing Sessions by User ---")
    alice_sessions = await session_service.list_sessions(
        app_name="multi_session_app",
        user_id="alice"
    )
    bob_sessions = await session_service.list_sessions(
        app_name="multi_session_app",
        user_id="bob"
    )

    print(f"  Alice's sessions: {[s.id for s in alice_sessions.sessions]}")
    print(f"  Bob's sessions: {[s.id for s in bob_sessions.sessions]}")

    # =========================================================================
    # Part 3: Session Isolation Demonstration
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Session Isolation")
    print("="*60)
    print("  Sessions don't share state or history")

    # Check state in each session
    python_session = await session_service.get_session(
        app_name="multi_session_app", user_id="alice", session_id="alice_python_chat"
    )
    cooking_session = await session_service.get_session(
        app_name="multi_session_app", user_id="alice", session_id="alice_cooking_chat"
    )
    bob_session = await session_service.get_session(
        app_name="multi_session_app", user_id="bob", session_id="bob_chat"
    )

    print(f"\n  Session Comparison:")
    print(f"  +-----------------------+--------+--------+--------+")
    print(f"  | Property              | Python | Cooking| Bob    |")
    print(f"  +-----------------------+--------+--------+--------+")
    print(f"  | user_id               | alice  | alice  | bob    |")
    print(f"  | topic                 | Python | Cooking| Music  |")
    print(f"  | event_count           | {len(python_session.events):6} | {len(cooking_session.events):6} | {len(bob_session.events):6} |")
    print(f"  +-----------------------+--------+--------+--------+")

    # =========================================================================
    # Part 4: Auto-generated Session IDs
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Auto-generated Session IDs")
    print("="*60)

    # Create session without specifying ID
    auto_session = await session_service.create_session(
        app_name="multi_session_app",
        user_id="charlie",
        # session_id not specified - will be auto-generated
        state={"user_name": "Charlie"}
    )

    print(f"\n  Created session without specifying ID")
    print(f"  Auto-generated ID: {auto_session.id}")

    # =========================================================================
    # Part 5: Cleanup - Delete Specific Sessions
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Selective Session Cleanup")
    print("="*60)

    # Delete only the cooking session
    await session_service.delete_session(
        app_name="multi_session_app",
        user_id="alice",
        session_id="alice_cooking_chat"
    )
    print(f"\n  Deleted Alice's cooking session")

    # Verify
    alice_sessions = await session_service.list_sessions(
        app_name="multi_session_app",
        user_id="alice"
    )
    print(f"  Alice's remaining sessions: {[s.id for s in alice_sessions.sessions]}")

    # Python session still exists with full history
    python_session = await session_service.get_session(
        app_name="multi_session_app", user_id="alice", session_id="alice_python_chat"
    )
    print(f"  Python session events: {len(python_session.events)} (preserved)")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Multiple Sessions")
    print("#"*70)
    print("""
    MULTIPLE SESSIONS PER USER:
    ---------------------------
    - Same user can have many conversation threads
    - Each session has unique session_id
    - Sessions are completely independent
    - Use case: Different topics, projects, or contexts

    SESSIONS ACROSS USERS:
    ----------------------
    - Each user has their own set of sessions
    - user_id + session_id uniquely identifies a session
    - Users cannot access each other's sessions
    - Use case: Multi-user applications

    SESSION ISOLATION:
    ------------------
    - State is NOT shared between sessions
    - Event history is per-session
    - Agent context is session-specific
    - Even same user's different sessions are isolated

    LISTING SESSIONS:
    -----------------
    sessions = await service.list_sessions(
        app_name="app",
        user_id="user"
    )
    # Returns ListSessionsResponse with sessions attribute

    SESSION ID OPTIONS:
    -------------------
    - Explicit: session_id="my_custom_id"
    - Auto-generated: omit session_id parameter
    - Use explicit IDs for predictable retrieval
    - Use auto-generated for temporary conversations

    COMMON PATTERNS:
    ----------------
    1. One session per conversation topic
    2. One session per project/task
    3. Daily sessions (session_id="2024-01-15")
    4. Feature-specific sessions (session_id="support_chat")
    """)


if __name__ == "__main__":
    asyncio.run(main())
