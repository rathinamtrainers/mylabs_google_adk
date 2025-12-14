"""
Lab 3 - Exercise 2: Model Callbacks
====================================

This exercise demonstrates before/after model callbacks:
1. before_model_callback - inspect/modify LLM requests
2. after_model_callback - inspect/modify LLM responses
3. Implementing guardrails
4. Request/response transformation

Run: uv run python 02_model_callbacks.py
"""

import asyncio
from typing import Optional
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Part 1: Inspecting LLM Requests
# =============================================================================

def inspect_request(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Called BEFORE sending request to the LLM.

    Parameters:
        callback_context: Contains agent_name, state, session, etc.
        llm_request: The request being sent (can be modified in-place)

    Returns:
        None - Allow LLM call to proceed
        LlmResponse - Skip LLM call and use this response
    """
    print("    [before_model] Inspecting LLM request:")
    print(f"      Model: {llm_request.model}")

    # Count messages in the request
    msg_count = len(llm_request.contents) if llm_request.contents else 0
    print(f"      Messages: {msg_count}")

    # Show the last user message
    if llm_request.contents:
        last_content = llm_request.contents[-1]
        if last_content.parts:
            text = getattr(last_content.parts[0], 'text', None)
            if text:
                print(f"      Last message: {text[:50]}...")

    return None  # Proceed with LLM call


def inspect_response(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    Called AFTER receiving response from the LLM.

    Parameters:
        callback_context: Contains agent_name, state, session, etc.
        llm_response: The response received (can be modified)

    Returns:
        None - Use original response
        LlmResponse - Replace with modified response
    """
    print("    [after_model] Inspecting LLM response:")

    if llm_response.content and llm_response.content.parts:
        text = getattr(llm_response.content.parts[0], 'text', None)
        if text:
            word_count = len(text.split())
            print(f"      Response length: {word_count} words")
            print(f"      Preview: {text[:50]}...")

    return None  # Use original response


# =============================================================================
# Part 2: Input Guardrail (Block Forbidden Content)
# =============================================================================

BLOCKED_WORDS = ["hack", "exploit", "bypass"]

def input_guardrail(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Block requests containing forbidden words."""
    if llm_request.contents:
        last_content = llm_request.contents[-1]
        if last_content.parts:
            text = getattr(last_content.parts[0], 'text', '') or ''
            text_lower = text.lower()

            for word in BLOCKED_WORDS:
                if word in text_lower:
                    print(f"    [GUARDRAIL] Blocked word detected: '{word}'")
                    return LlmResponse(
                        content=types.Content(
                            role="model",
                            parts=[types.Part(
                                text="I cannot process requests containing prohibited content."
                            )]
                        )
                    )

    print("    [GUARDRAIL] Request passed input check")
    return None


# =============================================================================
# Part 3: Output Guardrail (Filter Response)
# =============================================================================

def output_guardrail(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Filter out responses mentioning certain topics."""
    if llm_response.content and llm_response.content.parts:
        text = getattr(llm_response.content.parts[0], 'text', '') or ''

        # Check for sensitive information patterns
        if "password" in text.lower() or "secret" in text.lower():
            print("    [GUARDRAIL] Sensitive content detected in response")
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(
                        text="I've filtered my response to remove potentially sensitive information."
                    )]
                )
            )

    print("    [GUARDRAIL] Response passed output check")
    return None


# =============================================================================
# Part 4: Modifying Requests (Adding Context)
# =============================================================================

def add_user_context(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Add user preferences from state to the request."""
    user_name = callback_context.state.get("user_name", "User")
    user_style = callback_context.state.get("preferred_style", "concise")

    print(f"    [before_model] Adding context: user={user_name}, style={user_style}")

    # Modify the system instruction to include user preferences
    if llm_request.config and llm_request.config.system_instruction:
        existing = llm_request.config.system_instruction
        # system_instruction can be a string or Content object
        if isinstance(existing, str):
            enhanced_text = f"{existing}\n\nUser's name is {user_name}. Respond in a {user_style} style."
            llm_request.config.system_instruction = enhanced_text
            print(f"    [before_model] Enhanced system instruction")
        elif hasattr(existing, 'parts') and existing.parts:
            original_text = getattr(existing.parts[0], 'text', '') or ''
            enhanced_text = f"{original_text}\n\nUser's name is {user_name}. Respond in a {user_style} style."
            existing.parts[0] = types.Part(text=enhanced_text)
            print(f"    [before_model] Enhanced system instruction")

    return None


# =============================================================================
# Part 5: Modifying Responses (Post-processing)
# =============================================================================

def add_response_footer(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Add a footer to every response."""
    if llm_response.content and llm_response.content.parts:
        text = getattr(llm_response.content.parts[0], 'text', None)
        if text:
            # Add footer
            modified_text = f"{text}\n\n---\n[Response processed by ADK]"
            llm_response.content.parts[0] = types.Part(text=modified_text)
            print("    [after_model] Added footer to response")
            return llm_response

    return None


async def main():
    print("\n" + "#"*70)
    print("# Lab 3 Exercise 2: Model Callbacks")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Part 1: Inspecting Requests and Responses
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Inspecting LLM Requests and Responses")
    print("="*60)

    agent1 = LlmAgent(
        name="InspectorAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful. Keep responses under 30 words.",
        before_model_callback=inspect_request,
        after_model_callback=inspect_response,
    )

    runner1 = Runner(
        agent=agent1,
        app_name="model_callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="model_callback_demo",
        user_id="user1",
        session_id="inspect_session",
        state={}
    )

    print("\n  Sending: 'What is machine learning?'")
    user_message = types.Content(parts=[types.Part(text="What is machine learning?")])
    async for event in runner1.run_async(
        user_id="user1",
        session_id="inspect_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Final response: {event.content.parts[0].text[:100]}...")

    # =========================================================================
    # Part 2: Input Guardrail
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Input Guardrail (Block Forbidden Words)")
    print("="*60)

    agent2 = LlmAgent(
        name="GuardedAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful.",
        before_model_callback=input_guardrail,
    )

    runner2 = Runner(
        agent=agent2,
        app_name="model_callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="model_callback_demo",
        user_id="user1",
        session_id="guardrail_session",
        state={}
    )

    # Test 1: Safe message
    print("\n  Test 1 - Safe message: 'How do I learn Python?'")
    user_message = types.Content(parts=[types.Part(text="How do I learn Python?")])
    async for event in runner2.run_async(
        user_id="user1",
        session_id="guardrail_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:80]}...")

    # Test 2: Blocked message
    print("\n  Test 2 - Blocked message: 'How do I hack a website?'")
    user_message = types.Content(parts=[types.Part(text="How do I hack a website?")])
    async for event in runner2.run_async(
        user_id="user1",
        session_id="guardrail_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text}")

    # =========================================================================
    # Part 3: Output Guardrail
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Output Guardrail (Filter Responses)")
    print("="*60)

    agent3 = LlmAgent(
        name="FilteredAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful. If asked about passwords, explain generally.",
        after_model_callback=output_guardrail,
    )

    runner3 = Runner(
        agent=agent3,
        app_name="model_callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="model_callback_demo",
        user_id="user1",
        session_id="output_guard_session",
        state={}
    )

    print("\n  Asking about password management...")
    user_message = types.Content(
        parts=[types.Part(text="What makes a good password?")]
    )
    async for event in runner3.run_async(
        user_id="user1",
        session_id="output_guard_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:100]}...")

    # =========================================================================
    # Part 4: Adding User Context
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Adding User Context to Requests")
    print("="*60)

    agent4 = LlmAgent(
        name="ContextAgent",
        model="gemini-2.0-flash",
        instruction="You are a helpful assistant.",
        before_model_callback=add_user_context,
    )

    runner4 = Runner(
        agent=agent4,
        app_name="model_callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="model_callback_demo",
        user_id="user1",
        session_id="context_session",
        state={
            "user_name": "Alice",
            "preferred_style": "friendly and casual"
        }
    )

    print("\n  User: Alice (style: friendly and casual)")
    print("  Message: 'Explain APIs'")
    user_message = types.Content(parts=[types.Part(text="Explain APIs")])
    async for event in runner4.run_async(
        user_id="user1",
        session_id="context_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:150]}...")

    # =========================================================================
    # Part 5: Response Post-processing
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Response Post-processing (Add Footer)")
    print("="*60)

    agent5 = LlmAgent(
        name="FooterAgent",
        model="gemini-2.0-flash",
        instruction="You are helpful. Keep responses under 20 words.",
        after_model_callback=add_response_footer,
    )

    runner5 = Runner(
        agent=agent5,
        app_name="model_callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="model_callback_demo",
        user_id="user1",
        session_id="footer_session",
        state={}
    )

    print("\n  Message: 'What is Python?'")
    user_message = types.Content(parts=[types.Part(text="What is Python?")])
    async for event in runner5.run_async(
        user_id="user1",
        session_id="footer_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response:\n  {event.content.parts[0].text}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Model Callbacks")
    print("#"*70)
    print("""
    CALLBACK SIGNATURES:
    --------------------
    def before_model_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        # Return None to proceed, or LlmResponse to skip LLM

    def after_model_callback(
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        # Return None for original, or LlmResponse to replace

    LLM REQUEST PROPERTIES:
    -----------------------
    llm_request.model        # Model name
    llm_request.contents     # List of Content messages
    llm_request.config       # GenerateContentConfig
      .system_instruction    # System prompt
      .temperature           # Temperature setting
      .tools                 # Available tools

    LLM RESPONSE PROPERTIES:
    ------------------------
    llm_response.content     # types.Content with response
    llm_response.content.parts[0].text  # Response text

    USE CASES:
    ----------
    before_model_callback:
    - Input validation/guardrails
    - Add context from state
    - Modify system instructions
    - Log requests for debugging
    - Block forbidden content

    after_model_callback:
    - Output filtering/guardrails
    - Response transformation
    - Add disclaimers/footers
    - Log responses for analytics
    - PII redaction

    KEY INSIGHT:
    ------------
    Model callbacks give you fine-grained control over
    every LLM interaction. They're ideal for:
    - Security guardrails
    - Request/response logging
    - Dynamic prompt enhancement
    - Output post-processing
    """)


if __name__ == "__main__":
    asyncio.run(main())
