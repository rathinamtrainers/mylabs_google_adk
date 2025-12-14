"""
Lab 2 - Exercise 4: Memory Service Basics
==========================================

This exercise introduces the MemoryService concept:
1. Difference between Session and Memory
2. InMemoryMemoryService for development
3. Adding sessions to memory
4. Searching memory

Run: uv run python 04_memory_service.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai import types


# =============================================================================
# Create agent
# =============================================================================
assistant = LlmAgent(
    name="Assistant",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant. Acknowledge what the user tells you. Keep responses brief.",
)


async def main():
    print("\n" + "#"*70)
    print("# Lab 2 Exercise 4: Memory Service Basics")
    print("#"*70)

    # =========================================================================
    # Part 1: Understanding Session vs Memory
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Session vs Memory")
    print("="*60)
    print("""
    SESSION (SessionService):
    - Tracks a SINGLE ongoing conversation
    - Contains events (messages, actions) for CURRENT chat
    - State is session-specific
    - Think: "Short-term memory for this chat"

    MEMORY (MemoryService):
    - Stores information across MULTIPLE sessions
    - Searchable knowledge archive
    - Persists after sessions end
    - Think: "Long-term memory across all chats"
    """)

    # =========================================================================
    # Part 2: Setup Services
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Setting Up Session and Memory Services")
    print("="*60)

    # Create both services
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

    print("\n  Created InMemorySessionService (for conversations)")
    print("  Created InMemoryMemoryService (for long-term storage)")
    print("\n  Note: Both services must be shared across runners!")

    # Create runner with both services
    runner = Runner(
        agent=assistant,
        app_name="memory_demo",
        session_service=session_service,
        memory_service=memory_service,  # Provide memory service to runner
    )

    # =========================================================================
    # Part 3: Create Conversations to Store in Memory
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Creating Conversations for Memory")
    print("="*60)

    # Session 1: About a project
    print("\n  --- Session 1: Project Discussion ---")
    await session_service.create_session(
        app_name="memory_demo",
        user_id="alice",
        session_id="project_chat",
        state={}
    )

    messages = [
        "I'm working on Project Alpha. It's a machine learning project.",
        "The deadline for Project Alpha is next Friday.",
        "We're using TensorFlow for Project Alpha."
    ]

    for msg in messages:
        user_message = types.Content(parts=[types.Part(text=msg)])
        async for event in runner.run_async(
            user_id="alice",
            session_id="project_chat",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                print(f"  User: {msg[:50]}...")
                print(f"  Agent: {event.content.parts[0].text[:50]}...")

    # Session 2: About preferences
    print("\n  --- Session 2: Preferences Discussion ---")
    await session_service.create_session(
        app_name="memory_demo",
        user_id="alice",
        session_id="prefs_chat",
        state={}
    )

    messages = [
        "My favorite programming language is Python.",
        "I prefer dark mode for all my editors.",
        "I usually work from 9am to 5pm."
    ]

    for msg in messages:
        user_message = types.Content(parts=[types.Part(text=msg)])
        async for event in runner.run_async(
            user_id="alice",
            session_id="prefs_chat",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                print(f"  User: {msg[:50]}...")
                print(f"  Agent: {event.content.parts[0].text[:50]}...")

    # =========================================================================
    # Part 4: Add Sessions to Memory
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Adding Sessions to Memory")
    print("="*60)

    # Get completed sessions
    project_session = await session_service.get_session(
        app_name="memory_demo", user_id="alice", session_id="project_chat"
    )
    prefs_session = await session_service.get_session(
        app_name="memory_demo", user_id="alice", session_id="prefs_chat"
    )

    print(f"\n  Project session has {len(project_session.events)} events")
    print(f"  Prefs session has {len(prefs_session.events)} events")

    # Add both sessions to memory
    await memory_service.add_session_to_memory(project_session)
    print("\n  Added project_chat session to memory")

    await memory_service.add_session_to_memory(prefs_session)
    print("  Added prefs_chat session to memory")

    print("\n  Memory now contains information from both conversations!")

    # =========================================================================
    # Part 5: Search Memory
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Searching Memory")
    print("="*60)

    # Search for project info
    print("\n  --- Search 1: 'Project Alpha' ---")
    results = await memory_service.search_memory(
        app_name="memory_demo",
        user_id="alice",
        query="Project Alpha"
    )

    if results.memories:
        print(f"  Found {len(results.memories)} memory result(s)")
        for i, memory in enumerate(results.memories):
            print(f"    Result {i+1}:")
            if hasattr(memory, 'events') and memory.events:
                for event in memory.events[:2]:  # Show first 2 events
                    if event.content and event.content.parts:
                        text = event.content.parts[0].text[:60] if hasattr(event.content.parts[0], 'text') else ""
                        print(f"      - {text}...")
    else:
        print("  No results found")

    # Search for preferences
    print("\n  --- Search 2: 'favorite language' ---")
    results = await memory_service.search_memory(
        app_name="memory_demo",
        user_id="alice",
        query="favorite language"
    )

    if results.memories:
        print(f"  Found {len(results.memories)} memory result(s)")
        for i, memory in enumerate(results.memories):
            print(f"    Result {i+1}:")
            if hasattr(memory, 'events') and memory.events:
                for event in memory.events[:2]:
                    if event.content and event.content.parts:
                        text = event.content.parts[0].text[:60] if hasattr(event.content.parts[0], 'text') else ""
                        print(f"      - {text}...")
    else:
        print("  No results found")

    # Search for deadline
    print("\n  --- Search 3: 'deadline' ---")
    results = await memory_service.search_memory(
        app_name="memory_demo",
        user_id="alice",
        query="deadline"
    )

    if results.memories:
        print(f"  Found {len(results.memories)} memory result(s)")
    else:
        print("  No results found")

    # =========================================================================
    # Part 6: Memory Isolation by User
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Memory Isolation by User")
    print("="*60)

    # Search as different user
    print("\n  Searching as 'bob' for 'Project Alpha'...")
    results = await memory_service.search_memory(
        app_name="memory_demo",
        user_id="bob",  # Different user
        query="Project Alpha"
    )

    if results.memories:
        print(f"  Found {len(results.memories)} result(s)")
    else:
        print("  No results - Bob can't see Alice's memories!")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Memory Service Basics")
    print("#"*70)
    print("""
    SESSION vs MEMORY:
    ------------------
    Session:
    - Current conversation only
    - Events from this chat
    - Managed by SessionService
    - Deleted when conversation ends

    Memory:
    - Archive across conversations
    - Searchable knowledge base
    - Managed by MemoryService
    - Persists beyond sessions

    MEMORY SERVICE SETUP:
    ---------------------
    memory_service = InMemoryMemoryService()

    runner = Runner(
        agent=agent,
        session_service=session_service,
        memory_service=memory_service,  # Add memory service
    )

    ADDING TO MEMORY:
    -----------------
    session = await session_service.get_session(...)
    await memory_service.add_session_to_memory(session)

    SEARCHING MEMORY:
    -----------------
    results = await memory_service.search_memory(
        app_name="app",
        user_id="user",
        query="search terms"
    )
    # Returns SearchMemoryResponse with memories list

    MEMORY IMPLEMENTATIONS:
    -----------------------
    - InMemoryMemoryService: For development (no persistence)
    - VertexAiMemoryBankService: For production (Google Cloud)

    KEY INSIGHT:
    ------------
    Memory enables agents to recall information from past
    conversations, making them more useful and personalized.
    """)


if __name__ == "__main__":
    asyncio.run(main())
