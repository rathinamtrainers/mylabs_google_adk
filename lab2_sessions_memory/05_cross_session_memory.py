"""
Lab 2 - Exercise 5: Cross-Session Memory with load_memory Tool
===============================================================

This exercise demonstrates using memory across sessions:
1. Agent with load_memory tool
2. Storing information in one session
3. Recalling information in another session
4. Practical memory workflow

Run: uv run python 05_cross_session_memory.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import load_memory  # Built-in memory search tool
from google.genai import types


# =============================================================================
# Create agents
# =============================================================================

# Agent for capturing information (no memory tool needed)
info_capture_agent = LlmAgent(
    name="InfoCaptureAgent",
    model="gemini-2.0-flash",
    instruction="""You are a helpful assistant that acknowledges information.
    When the user tells you something, confirm you've noted it.
    Keep responses brief.""",
)

# Agent that can recall from memory
memory_recall_agent = LlmAgent(
    name="MemoryRecallAgent",
    model="gemini-2.0-flash",
    instruction="""You are a helpful assistant with access to past conversation memories.

    When the user asks about something that might be in past conversations,
    use the 'load_memory' tool to search for relevant information.

    If you find relevant information, use it to answer the user's question.
    If you don't find anything, let them know you don't have that information.

    Keep responses brief and informative.""",
    tools=[load_memory],  # Give this agent the memory tool
)


async def main():
    print("\n" + "#"*70)
    print("# Lab 2 Exercise 5: Cross-Session Memory")
    print("#"*70)

    # Setup shared services
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

    # =========================================================================
    # Phase 1: Capture Information in First Session
    # =========================================================================
    print("\n" + "="*60)
    print("PHASE 1: Capturing Information (Session 1)")
    print("="*60)
    print("  User tells the agent important information...")

    runner1 = Runner(
        agent=info_capture_agent,
        app_name="memory_app",
        session_service=session_service,
        memory_service=memory_service,
    )

    await session_service.create_session(
        app_name="memory_app",
        user_id="user_demo",
        session_id="info_session",
        state={}
    )

    # Tell the agent some facts
    facts = [
        "My name is Sarah and I work at TechCorp as a software engineer.",
        "My favorite project is called 'DataPipeline' - it processes 1 million records daily.",
        "I'm planning to take vacation in Hawaii next month.",
        "My team has 5 members: Alice, Bob, Charlie, Diana, and me.",
    ]

    print("\n  User shares information:")
    for fact in facts:
        user_message = types.Content(parts=[types.Part(text=fact)])
        async for event in runner1.run_async(
            user_id="user_demo",
            session_id="info_session",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                print(f"\n  User: {fact}")
                print(f"  Agent: {event.content.parts[0].text[:80]}...")

    # Get the completed session
    info_session = await session_service.get_session(
        app_name="memory_app",
        user_id="user_demo",
        session_id="info_session"
    )
    print(f"\n  Session 1 complete: {len(info_session.events)} events")

    # =========================================================================
    # Phase 2: Add Session to Memory
    # =========================================================================
    print("\n" + "="*60)
    print("PHASE 2: Storing Session in Long-Term Memory")
    print("="*60)

    await memory_service.add_session_to_memory(info_session)
    print("\n  Session 1 added to memory!")
    print("  The conversation is now searchable in future sessions.")

    # =========================================================================
    # Phase 3: Start New Session and Recall
    # =========================================================================
    print("\n" + "="*60)
    print("PHASE 3: Recalling Information (Session 2 - NEW)")
    print("="*60)
    print("  Starting a brand new session...")
    print("  Agent uses load_memory tool to search past conversations.")

    runner2 = Runner(
        agent=memory_recall_agent,
        app_name="memory_app",
        session_service=session_service,
        memory_service=memory_service,
    )

    await session_service.create_session(
        app_name="memory_app",
        user_id="user_demo",
        session_id="recall_session",  # Different session!
        state={}
    )

    # Ask questions about past information
    questions = [
        "What is my name and where do I work?",
        "Tell me about my favorite project.",
        "When am I planning to take vacation?",
        "Who are the members of my team?",
    ]

    print("\n  User asks questions (agent searches memory):")
    for question in questions:
        print(f"\n  User: {question}")
        user_message = types.Content(parts=[types.Part(text=question)])
        async for event in runner2.run_async(
            user_id="user_demo",
            session_id="recall_session",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                print(f"  Agent: {event.content.parts[0].text[:150]}...")

    # =========================================================================
    # Phase 4: Demonstrate Memory Scope
    # =========================================================================
    print("\n" + "="*60)
    print("PHASE 4: Memory Scope - Different User")
    print("="*60)
    print("  Each user has their own memory...")

    # Create session for different user
    await session_service.create_session(
        app_name="memory_app",
        user_id="other_user",  # Different user!
        session_id="other_session",
        state={}
    )

    print("\n  New user asks: 'What is Sarah's favorite project?'")
    user_message = types.Content(
        parts=[types.Part(text="What is Sarah's favorite project?")]
    )
    async for event in runner2.run_async(
        user_id="other_user",  # Different user
        session_id="other_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Agent: {event.content.parts[0].text[:150]}...")

    print("\n  Note: Other user can't access user_demo's memories!")

    # =========================================================================
    # Phase 5: The Memory Workflow
    # =========================================================================
    print("\n" + "="*60)
    print("PHASE 5: Memory Workflow Summary")
    print("="*60)
    print("""
    COMPLETE MEMORY WORKFLOW:
    -------------------------

    1. USER CONVERSATION (Session A)
       User: "My favorite color is blue"
       Agent: "Got it, blue is your favorite color!"

    2. SESSION COMPLETION
       session = await service.get_session(...)

    3. ADD TO MEMORY
       await memory_service.add_session_to_memory(session)

    4. LATER (Session B - could be days/weeks later)
       User: "What's my favorite color?"
       Agent: [uses load_memory tool]
       Agent: "Your favorite color is blue!"
    """)

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Cross-Session Memory")
    print("#"*70)
    print("""
    KEY CONCEPTS:
    -------------
    1. Sessions are temporary conversation containers
    2. Memory is permanent searchable storage
    3. load_memory tool lets agents search past conversations
    4. Memory is scoped by user_id (privacy)

    BUILT-IN MEMORY TOOLS:
    ----------------------
    - load_memory: Search memory when agent decides
    - PreloadMemoryTool: Always load memory at start of turn

    WHEN TO ADD TO MEMORY:
    ----------------------
    - After session ends
    - After important information is shared
    - Periodically during long conversations
    - Via after_agent_callback (automated)

    MEMORY WORKFLOW:
    ----------------
    # 1. Setup services
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

    runner = Runner(
        agent=agent_with_load_memory_tool,
        session_service=session_service,
        memory_service=memory_service,
    )

    # 2. After conversation, add to memory
    session = await session_service.get_session(...)
    await memory_service.add_session_to_memory(session)

    # 3. Agent can now search this in future sessions

    USE CASES:
    ----------
    - User preferences (theme, language, style)
    - Project information (deadlines, team members)
    - Personal details (name, role, interests)
    - Past decisions and conversations
    - Any information that should persist

    PRODUCTION TIPS:
    ----------------
    - Use VertexAiMemoryBankService for persistence
    - Add sessions to memory at logical endpoints
    - Consider privacy - memory is per user_id
    - Memory search is semantic (not just keywords)
    """)


if __name__ == "__main__":
    asyncio.run(main())
