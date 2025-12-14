"""
Lab 3 - Exercise 1: Agent Callbacks
====================================

This exercise demonstrates before/after agent callbacks:
1. before_agent_callback - intercept before agent runs
2. after_agent_callback - modify agent output
3. Skipping agent execution by returning Content
4. Replacing agent responses

Run: uv run python 01_agent_callbacks.py
"""

import asyncio
from typing import Optional
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Part 1: Basic before_agent_callback
# =============================================================================

def simple_before_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Called BEFORE the agent starts processing.

    Parameters:
        callback_context: Contains agent_name, state, session, etc.

    Returns:
        None - Allow agent to run normally
        types.Content - Skip agent and use this as the response
    """
    print(f"    [before_agent] Agent '{callback_context.agent_name}' is about to run")
    print(f"    [before_agent] Invocation ID: {callback_context.invocation_id[:8]}...")
    return None  # Allow normal execution


def simple_after_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Called AFTER the agent finishes processing.

    Parameters:
        callback_context: Contains agent_name, state, session, etc.

    Returns:
        None - Use agent's original response
        types.Content - Replace agent's response with this
    """
    print(f"    [after_agent] Agent '{callback_context.agent_name}' finished")
    return None  # Use original response


# =============================================================================
# Part 2: Skipping agent execution
# =============================================================================

def skip_if_flagged(callback_context: CallbackContext) -> Optional[types.Content]:
    """Skip agent execution if 'skip_agent' flag is set in state."""
    skip = callback_context.state.get("skip_agent", False)

    if skip:
        print("    [before_agent] SKIPPING - 'skip_agent' flag is True")
        return types.Content(
            role="model",
            parts=[types.Part(text="Agent execution was skipped by callback.")]
        )

    print("    [before_agent] Proceeding with agent execution")
    return None


# =============================================================================
# Part 3: Modifying agent response
# =============================================================================

def add_disclaimer(callback_context: CallbackContext) -> Optional[types.Content]:
    """Add a disclaimer to the agent's response."""
    # Note: In after_agent_callback, we don't have direct access to the response
    # We can only replace it entirely if needed
    # For response modification, after_model_callback is more appropriate

    # Track that this callback ran
    callback_context.state["disclaimer_checked"] = True
    print("    [after_agent] Disclaimer check completed")
    return None


# =============================================================================
# Part 4: Conditional response replacement
# =============================================================================

call_count = 0

def limit_responses(callback_context: CallbackContext) -> Optional[types.Content]:
    """Replace response after 3 calls."""
    global call_count
    call_count += 1

    if call_count > 3:
        print(f"    [after_agent] Call #{call_count} - Replacing with limit message")
        return types.Content(
            role="model",
            parts=[types.Part(text="Response limit reached. Please start a new session.")]
        )

    print(f"    [after_agent] Call #{call_count} - Using original response")
    return None


async def main():
    print("\n" + "#"*70)
    print("# Lab 3 Exercise 1: Agent Callbacks")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Part 1: Basic Callbacks
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Basic before/after Agent Callbacks")
    print("="*60)
    print("  Callbacks log when agent starts and finishes.")

    agent1 = LlmAgent(
        name="BasicAgent",
        model="gemini-2.0-flash",
        instruction="You are a helpful assistant. Keep responses under 20 words.",
        before_agent_callback=simple_before_callback,
        after_agent_callback=simple_after_callback,
    )

    runner1 = Runner(
        agent=agent1,
        app_name="callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="callback_demo",
        user_id="user1",
        session_id="basic_session",
        state={}
    )

    print("\n  Sending message: 'What is 2+2?'")
    user_message = types.Content(parts=[types.Part(text="What is 2+2?")])
    async for event in runner1.run_async(
        user_id="user1",
        session_id="basic_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Agent response: {event.content.parts[0].text}")

    # =========================================================================
    # Part 2: Skipping Agent Execution
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Skipping Agent Execution")
    print("="*60)
    print("  before_agent_callback can skip the agent entirely.")

    agent2 = LlmAgent(
        name="SkippableAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful.",
        before_agent_callback=skip_if_flagged,
    )

    runner2 = Runner(
        agent=agent2,
        app_name="callback_demo",
        session_service=session_service,
    )

    # Test 1: Normal execution (skip_agent=False)
    await session_service.create_session(
        app_name="callback_demo",
        user_id="user1",
        session_id="skip_test_1",
        state={"skip_agent": False}
    )

    print("\n  Test 1: skip_agent=False")
    user_message = types.Content(parts=[types.Part(text="Hello!")])
    async for event in runner2.run_async(
        user_id="user1",
        session_id="skip_test_1",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:60]}...")

    # Test 2: Skip execution (skip_agent=True)
    await session_service.create_session(
        app_name="callback_demo",
        user_id="user1",
        session_id="skip_test_2",
        state={"skip_agent": True}
    )

    print("\n  Test 2: skip_agent=True")
    async for event in runner2.run_async(
        user_id="user1",
        session_id="skip_test_2",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text}")

    # =========================================================================
    # Part 3: after_agent_callback with State
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: after_agent_callback with State")
    print("="*60)
    print("  after_agent_callback can modify state.")

    agent3 = LlmAgent(
        name="StateAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful. Keep responses brief.",
        after_agent_callback=add_disclaimer,
    )

    runner3 = Runner(
        agent=agent3,
        app_name="callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="callback_demo",
        user_id="user1",
        session_id="state_session",
        state={}
    )

    print("\n  Sending message...")
    user_message = types.Content(parts=[types.Part(text="Tell me a fact.")])
    async for event in runner3.run_async(
        user_id="user1",
        session_id="state_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:80]}...")

    session = await session_service.get_session(
        app_name="callback_demo",
        user_id="user1",
        session_id="state_session"
    )
    print(f"  State after callback: disclaimer_checked={session.state.get('disclaimer_checked')}")

    # =========================================================================
    # Part 4: Response Limiting with after_agent_callback
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Response Limiting")
    print("="*60)
    print("  after_agent_callback replaces response after 3 calls.")

    global call_count
    call_count = 0  # Reset counter

    agent4 = LlmAgent(
        name="LimitedAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful. Keep responses under 15 words.",
        after_agent_callback=limit_responses,
    )

    runner4 = Runner(
        agent=agent4,
        app_name="callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="callback_demo",
        user_id="user1",
        session_id="limit_session",
        state={}
    )

    questions = ["What is Python?", "What is Java?", "What is Rust?", "What is Go?", "What is C++?"]

    print("\n  Sending 5 messages (limit is 3):")
    for i, q in enumerate(questions, 1):
        print(f"\n  Message {i}: {q}")
        user_message = types.Content(parts=[types.Part(text=q)])
        async for event in runner4.run_async(
            user_id="user1",
            session_id="limit_session",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                print(f"  Response: {event.content.parts[0].text[:60]}...")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Agent Callbacks")
    print("#"*70)
    print("""
    CALLBACK SIGNATURES:
    --------------------
    def before_agent_callback(
        callback_context: CallbackContext
    ) -> Optional[types.Content]:
        # Return None to proceed, or Content to skip agent

    def after_agent_callback(
        callback_context: CallbackContext
    ) -> Optional[types.Content]:
        # Return None to use original, or Content to replace

    CALLBACK CONTEXT PROPERTIES:
    ----------------------------
    callback_context.agent_name      # Name of the current agent
    callback_context.invocation_id   # Unique ID for this invocation
    callback_context.state           # Session state (mutable)
    callback_context.session         # Current session object
    callback_context.app_name        # Application name
    callback_context.user_id         # Current user ID

    USE CASES:
    ----------
    before_agent_callback:
    - Check permissions before running
    - Skip agent based on conditions
    - Log/track agent invocations
    - Validate input requirements

    after_agent_callback:
    - Track completion metrics
    - Update state after processing
    - Replace response conditionally
    - Trigger follow-up actions

    KEY INSIGHT:
    ------------
    Agent callbacks wrap the ENTIRE agent execution.
    For finer control over LLM calls, use model callbacks.
    For tool-specific interception, use tool callbacks.
    """)


if __name__ == "__main__":
    asyncio.run(main())
