"""
Lab 1 - Exercise 5: Callbacks with State
=========================================

This exercise demonstrates using CallbackContext to manage state in callbacks:
1. before_agent_callback / after_agent_callback
2. before_model_callback / after_model_callback
3. Tracking metrics (call counts, timing)
4. Implementing guardrails
5. Controlling flow by returning values

Run: uv run python 05_callbacks_with_state.py
"""

import asyncio
import time
from typing import Optional
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Callback 1: Metrics Tracking (before/after agent)
# =============================================================================
def metrics_before_agent(callback_context: CallbackContext) -> None:
    """
    Track when agent starts and count invocations.
    """
    print("\n  [before_agent_callback: metrics_before_agent]")

    # Track invocation count
    count = callback_context.state.get("metrics:invocation_count", 0)
    callback_context.state["metrics:invocation_count"] = count + 1
    print(f"    Invocation #{count + 1}")

    # Store start time for duration calculation
    callback_context.state["temp:start_time"] = time.time()

    # Log the user's input
    if callback_context.user_content and callback_context.user_content.parts:
        user_text = callback_context.user_content.parts[0].text
        callback_context.state["temp:user_input"] = user_text
        print(f"    User input: {user_text[:50]}...")

    return None  # Continue with normal execution


def metrics_after_agent(callback_context: CallbackContext) -> None:
    """
    Calculate duration and log completion.
    """
    print("\n  [after_agent_callback: metrics_after_agent]")

    # Calculate duration
    start_time = callback_context.state.get("temp:start_time", time.time())
    duration = time.time() - start_time
    print(f"    Duration: {duration:.3f} seconds")

    # Store duration in session state (persists)
    total_duration = callback_context.state.get("metrics:total_duration", 0.0)
    callback_context.state["metrics:total_duration"] = total_duration + duration

    # Track average duration
    count = callback_context.state.get("metrics:invocation_count", 1)
    avg_duration = callback_context.state["metrics:total_duration"] / count
    callback_context.state["metrics:avg_duration"] = avg_duration
    print(f"    Average duration: {avg_duration:.3f} seconds")

    return None


# =============================================================================
# Callback 2: Model Call Tracking (before/after model)
# =============================================================================
def track_before_model(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Track model calls and optionally modify requests.
    """
    print("\n  [before_model_callback: track_before_model]")

    # Count model calls
    model_calls = callback_context.state.get("metrics:model_call_count", 0)
    callback_context.state["metrics:model_call_count"] = model_calls + 1
    print(f"    Model call #{model_calls + 1}")

    # Log request info
    content_count = len(llm_request.contents) if llm_request.contents else 0
    print(f"    Request has {content_count} content(s)")

    # Store model call start time
    callback_context.state["temp:model_start_time"] = time.time()

    return None  # Return None to proceed with model call


def track_after_model(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    Track model response and calculate model latency.
    """
    print("\n  [after_model_callback: track_after_model]")

    # Calculate model latency
    start_time = callback_context.state.get("temp:model_start_time", time.time())
    latency = time.time() - start_time
    print(f"    Model latency: {latency:.3f} seconds")

    # Track total model time
    total_model_time = callback_context.state.get("metrics:total_model_time", 0.0)
    callback_context.state["metrics:total_model_time"] = total_model_time + latency

    return None  # Return None to use original response


# =============================================================================
# Callback 3: Guardrail - Block certain topics
# =============================================================================
BLOCKED_WORDS = ["secret", "password", "hack"]


def guardrail_before_agent(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    A guardrail callback that blocks requests containing certain words.

    Returning a Content object SKIPS the agent and returns that as the response.
    Returning None continues normal execution.
    """
    print("\n  [before_agent_callback: guardrail_before_agent]")

    if callback_context.user_content and callback_context.user_content.parts:
        user_text = callback_context.user_content.parts[0].text.lower()

        for word in BLOCKED_WORDS:
            if word in user_text:
                print(f"    BLOCKED: Found '{word}' in user input")

                # Track blocked requests
                blocked_count = callback_context.state.get("metrics:blocked_count", 0)
                callback_context.state["metrics:blocked_count"] = blocked_count + 1

                # Return a Content to skip the agent
                return types.Content(
                    parts=[types.Part(
                        text="I'm sorry, I can't help with that topic. "
                             "Please ask about something else."
                    )]
                )

    print("    Input OK - proceeding")
    return None  # Continue with normal execution


# =============================================================================
# Callback 4: Rate Limiting
# =============================================================================
MAX_REQUESTS_PER_SESSION = 5


def rate_limit_before_agent(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Implement simple rate limiting using state.
    """
    print("\n  [before_agent_callback: rate_limit_before_agent]")

    request_count = callback_context.state.get("rate:request_count", 0)
    print(f"    Request count: {request_count}/{MAX_REQUESTS_PER_SESSION}")

    if request_count >= MAX_REQUESTS_PER_SESSION:
        print("    RATE LIMITED: Too many requests")
        return types.Content(
            parts=[types.Part(
                text=f"Rate limit exceeded. Maximum {MAX_REQUESTS_PER_SESSION} "
                     "requests per session. Please start a new session."
            )]
        )

    # Increment counter
    callback_context.state["rate:request_count"] = request_count + 1
    return None


# =============================================================================
# Create agents with different callback configurations
# =============================================================================

# Agent with metrics tracking only
metrics_agent = LlmAgent(
    name="MetricsAgent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant. Keep responses brief (1-2 sentences).",
    before_agent_callback=metrics_before_agent,
    after_agent_callback=metrics_after_agent,
    before_model_callback=track_before_model,
    after_model_callback=track_after_model,
)

# Agent with guardrails
guardrail_agent = LlmAgent(
    name="GuardrailAgent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant. Keep responses brief.",
    before_agent_callback=guardrail_before_agent,
)

# Agent with rate limiting
rate_limited_agent = LlmAgent(
    name="RateLimitedAgent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant. Keep responses very brief.",
    before_agent_callback=rate_limit_before_agent,
)


# =============================================================================
# Main demonstration
# =============================================================================
async def main():
    print("\n" + "#"*70)
    print("# Lab 1 Exercise 5: Callbacks with State")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Demo 1: Metrics Tracking
    # =========================================================================
    print("\n" + "="*60)
    print("DEMO 1: Metrics Tracking with Callbacks")
    print("="*60)

    runner1 = Runner(
        agent=metrics_agent,
        app_name="callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="callback_demo",
        user_id="user1",
        session_id="metrics_session",
        state={}
    )

    # First request
    print("\n--- Request 1 ---")
    user_message = types.Content(parts=[types.Part(text="What is Python?")])
    async for event in runner1.run_async(
        user_id="user1", session_id="metrics_session", new_message=user_message
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Response: {event.content.parts[0].text[:100]}...")

    # Second request
    print("\n--- Request 2 ---")
    user_message = types.Content(parts=[types.Part(text="What is JavaScript?")])
    async for event in runner1.run_async(
        user_id="user1", session_id="metrics_session", new_message=user_message
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Response: {event.content.parts[0].text[:100]}...")

    # Show metrics
    session = await session_service.get_session(
        app_name="callback_demo", user_id="user1", session_id="metrics_session"
    )
    print("\n--- Metrics Summary ---")
    print(f"  Invocation count: {session.state.get('metrics:invocation_count')}")
    print(f"  Model call count: {session.state.get('metrics:model_call_count')}")
    print(f"  Total duration: {session.state.get('metrics:total_duration', 0):.3f}s")
    print(f"  Avg duration: {session.state.get('metrics:avg_duration', 0):.3f}s")
    print(f"  Total model time: {session.state.get('metrics:total_model_time', 0):.3f}s")

    # =========================================================================
    # Demo 2: Guardrails
    # =========================================================================
    print("\n" + "="*60)
    print("DEMO 2: Guardrail Callback (Content Filtering)")
    print("="*60)

    runner2 = Runner(
        agent=guardrail_agent,
        app_name="callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="callback_demo",
        user_id="user2",
        session_id="guardrail_session",
        state={}
    )

    # Normal request
    print("\n--- Normal Request ---")
    user_message = types.Content(parts=[types.Part(text="Tell me about Python")])
    async for event in runner2.run_async(
        user_id="user2", session_id="guardrail_session", new_message=user_message
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:100]}...")

    # Blocked request
    print("\n--- Blocked Request (contains 'password') ---")
    user_message = types.Content(parts=[types.Part(text="How do I hack a password?")])
    async for event in runner2.run_async(
        user_id="user2", session_id="guardrail_session", new_message=user_message
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text}")

    # Check blocked count
    session = await session_service.get_session(
        app_name="callback_demo", user_id="user2", session_id="guardrail_session"
    )
    print(f"\n  Blocked request count: {session.state.get('metrics:blocked_count', 0)}")

    # =========================================================================
    # Demo 3: Rate Limiting
    # =========================================================================
    print("\n" + "="*60)
    print(f"DEMO 3: Rate Limiting ({MAX_REQUESTS_PER_SESSION} requests max)")
    print("="*60)

    runner3 = Runner(
        agent=rate_limited_agent,
        app_name="callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="callback_demo",
        user_id="user3",
        session_id="rate_limit_session",
        state={}
    )

    # Make several requests
    for i in range(7):  # Try 7 requests (limit is 5)
        print(f"\n--- Request {i+1} ---")
        user_message = types.Content(parts=[types.Part(text=f"Request number {i+1}")])
        async for event in runner3.run_async(
            user_id="user3", session_id="rate_limit_session", new_message=user_message
        ):
            if event.is_final_response() and event.content:
                response_text = event.content.parts[0].text
                if "Rate limit" in response_text:
                    print(f"  BLOCKED: {response_text}")
                else:
                    print(f"  Response: {response_text[:80]}...")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Callbacks with State")
    print("#"*70)
    print("""
    CALLBACK TYPES:
    ---------------
    1. before_agent_callback(ctx) -> Optional[Content]
       - Runs before agent starts
       - Return Content to skip agent (guardrail)
       - Return None to continue

    2. after_agent_callback(ctx) -> None
       - Runs after agent completes
       - Good for cleanup, logging, metrics

    3. before_model_callback(ctx, llm_request) -> Optional[LlmResponse]
       - Runs before each LLM call
       - Return LlmResponse to skip model
       - Return None to continue

    4. after_model_callback(ctx, llm_response) -> Optional[LlmResponse]
       - Runs after each LLM call
       - Return new LlmResponse to override
       - Return None to use original

    STATE IN CALLBACKS:
    -------------------
    - Use callback_context.state to read/write
    - Use temp: prefix for invocation-only data
    - Use metrics: or similar for tracking data
    - Changes are automatically tracked in EventActions

    COMMON PATTERNS:
    ----------------
    1. Metrics: Track counts, timing, usage
    2. Guardrails: Block inappropriate content
    3. Rate limiting: Limit requests per session/user
    4. Logging: Log inputs/outputs for debugging
    5. Caching: Cache responses in state
    6. Request modification: Modify before sending to model
    7. Response modification: Modify model response
    """)


if __name__ == "__main__":
    asyncio.run(main())
