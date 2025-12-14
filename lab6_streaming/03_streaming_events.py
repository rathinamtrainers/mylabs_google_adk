"""
Lab 6 - Exercise 3: Streaming Events
=====================================

This exercise covers event handling with run_live():
1. The Event class structure
2. Text events with partial/turn_complete/interrupted
3. Audio events (inline_data)
4. Metadata and transcription events
5. Error handling patterns

Run: uv run python 03_streaming_events.py
"""

import asyncio
from google.adk.agents import LlmAgent, LiveRequestQueue
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode


# =============================================================================
# Part 1: Understanding the Event Class
# =============================================================================

def explain_event_class():
    """Explain the Event class structure."""
    print("""
    THE EVENT CLASS
    ===============

    Event is ADK's unified container for all streaming responses.
    Every message from run_live() is an Event object.

    KEY FIELDS:
    -----------

    Content and Identity:
    - event.content         # Text, audio, or function calls
    - event.author          # Agent name or "user"
    - event.id              # Unique event ID
    - event.invocation_id   # Shared across session

    Streaming Flags:
    - event.partial         # True = incremental chunk
    - event.turn_complete   # True = model finished
    - event.interrupted     # True = user interrupted

    Transcription (when enabled):
    - event.input_transcription   # User's speech-to-text
    - event.output_transcription  # Agent's speech-to-text

    Tool Execution:
    - event.get_function_calls()      # Model requesting tools
    - event.get_function_responses()  # Tool results

    Diagnostics:
    - event.usage_metadata    # Token counts
    - event.error_code        # Error identifier
    - event.error_message     # Error description
    - event.finish_reason     # Why model stopped

    CONTENT STRUCTURE:
    ------------------
    event.content = Content(
        role="model",
        parts=[
            Part(text="Hello..."),           # Text
            Part(inline_data=Blob(...)),     # Audio
            Part(function_call=...),         # Tool call
        ]
    )

    EVENT AUTHORSHIP:
    -----------------
    - Model responses: author = agent name (e.g., "MyAgent")
    - User transcriptions: author = "user"

    This helps in multi-agent scenarios to track who said what.
    """)


# =============================================================================
# Part 2: Text Event Handling
# =============================================================================

def explain_text_events():
    """Explain text event handling with flags."""
    print("""
    TEXT EVENTS
    ===========

    Text events contain the model's text responses.
    Key flags help manage streaming display.

    DETECTING TEXT EVENTS:
    ----------------------
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.text:
                handle_text(part.text)

    THE partial FLAG:
    -----------------
    - partial=True:  Incremental chunk (streaming display)
    - partial=False: Complete merged text (final)

    Example stream:
    Event 1: partial=True,  text="Hello"
    Event 2: partial=True,  text=" world"
    Event 3: partial=False, text="Hello world"  # Merged
    Event 4: turn_complete=True                  # Done

    HANDLING partial:
    -----------------
    if event.partial:
        # Streaming display - show immediately
        update_streaming_display(part.text)
    else:
        # Complete - can save/process
        display_final_message(part.text)

    THE turn_complete FLAG:
    -----------------------
    - True when model has finished its complete response
    - Time to enable user input again
    - Comes in a SEPARATE event after content

    if event.turn_complete:
        enable_user_input()
        hide_typing_indicator()

    THE interrupted FLAG:
    ---------------------
    - True when user interrupted mid-response
    - Stop rendering current output immediately

    if event.interrupted:
        stop_streaming_display()
        stop_audio_playback()

    FLAG COMBINATIONS:
    ------------------
    ┌──────────────────────────────────────────────────────────┐
    │  Scenario              │ turn_complete │ interrupted    │
    ├──────────────────────────────────────────────────────────┤
    │  Normal completion     │ True          │ False          │
    │  User interrupted      │ False         │ True           │
    │  Interrupted at end    │ True          │ True           │
    │  Mid-response          │ False         │ False          │
    └──────────────────────────────────────────────────────────┘

    TYPICAL PATTERN:
    ----------------
    async for event in runner.run_live(...):
        # Handle interruption first
        if event.interrupted:
            stop_all_output()
            continue

        # Handle text content
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    if event.partial:
                        stream_text(part.text)
                    else:
                        finalize_text(part.text)

        # Handle turn completion
        if event.turn_complete:
            ready_for_input()
    """)


# =============================================================================
# Part 3: Audio Events
# =============================================================================

def explain_audio_events():
    """Explain audio event handling."""
    print("""
    AUDIO EVENTS
    ============

    When response_modalities=["AUDIO"], model generates audio output.

    DETECTING AUDIO EVENTS:
    -----------------------
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.inline_data:
                audio_data = part.inline_data.data
                mime_type = part.inline_data.mime_type
                play_audio(audio_data)

    inline_data STRUCTURE:
    ----------------------
    part.inline_data = Blob(
        data=bytes,              # Raw audio bytes
        mime_type="audio/pcm"    # Format identifier
    )

    OUTPUT AUDIO FORMAT:
    --------------------
    - 16-bit PCM
    - 24kHz sample rate (native audio models)
    - Mono channel

    AUDIO vs TEXT MODE:
    -------------------
    You must choose ONE per session:

    # Text mode
    run_config = RunConfig(
        response_modalities=["TEXT"]
    )

    # Audio mode
    run_config = RunConfig(
        response_modalities=["AUDIO"]
    )

    CANNOT use both simultaneously!

    AUDIO EVENT PATTERN:
    --------------------
    async for event in runner.run_live(...):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.inline_data:
                    # Raw audio bytes for playback
                    audio_chunk = part.inline_data.data

                    # Queue for audio player
                    audio_queue.put(audio_chunk)

        if event.interrupted:
            # Stop audio immediately
            audio_player.stop()

        if event.turn_complete:
            # Flush audio buffer
            audio_player.flush()

    AUDIO EVENTS ARE EPHEMERAL:
    ---------------------------
    - inline_data is NOT saved to session
    - Only yielded for real-time playback
    - Use file_data for persistence (requires config)

    PERSISTING AUDIO:
    -----------------
    run_config = RunConfig(
        save_live_model_audio_to_session=True
    )

    This saves audio to artifacts with file_data references.
    """)


# =============================================================================
# Part 4: Metadata and Transcription Events
# =============================================================================

def explain_metadata_events():
    """Explain metadata and transcription events."""
    print("""
    METADATA EVENTS
    ===============

    usage_metadata contains token usage information.

    DETECTING METADATA:
    -------------------
    if event.usage_metadata:
        print(f"Prompt tokens: {event.usage_metadata.prompt_token_count}")
        print(f"Response tokens: {event.usage_metadata.candidates_token_count}")
        print(f"Total: {event.usage_metadata.total_token_count}")

    AVAILABLE FIELDS:
    -----------------
    - prompt_token_count       # Input tokens
    - candidates_token_count   # Output tokens
    - total_token_count        # Sum
    - cached_content_token_count  # From cache

    USE CASES:
    ----------
    - Cost monitoring
    - Quota tracking
    - Usage analytics

    TRANSCRIPTION EVENTS
    ====================

    When transcription is enabled, you get speech-to-text.

    ENABLING TRANSCRIPTION:
    -----------------------
    run_config = RunConfig(
        input_audio_transcription=True,   # User speech
        output_audio_transcription=True,  # Agent speech
    )

    DETECTING TRANSCRIPTION:
    ------------------------
    # User's spoken words
    if event.input_transcription:
        user_text = event.input_transcription
        display_caption(f"User: {user_text}")

    # Agent's spoken words
    if event.output_transcription:
        agent_text = event.output_transcription
        display_caption(f"Agent: {agent_text}")

    TRANSCRIPTION AUTHORSHIP:
    -------------------------
    Input transcription events have:
    - event.author = "user"
    - event.content.role = "user"

    USE CASES:
    ----------
    - Accessibility (captions)
    - Conversation logging
    - Search/indexing
    - Debugging

    PARTIAL TRANSCRIPTIONS:
    -----------------------
    - Partial transcriptions are NOT saved to session
    - Only final transcriptions are persisted
    - Partial events have event.partial = True
    """)


# =============================================================================
# Part 5: Error Handling
# =============================================================================

def explain_error_handling():
    """Explain error handling patterns."""
    print("""
    ERROR HANDLING
    ==============

    Errors surface through error_code and error_message fields.

    DETECTING ERRORS:
    -----------------
    if event.error_code:
        logger.error(f"Error: {event.error_code} - {event.error_message}")

        # Decide: break or continue?
        if event.error_code in ["SAFETY", "PROHIBITED_CONTENT"]:
            break  # Terminal error
        else:
            continue  # May recover

    COMMON ERROR CODES:
    -------------------
    Content Policy:
    - SAFETY               # Content violates safety
    - PROHIBITED_CONTENT   # Prohibited material
    - BLOCKLIST            # Matches blocklist

    Limits:
    - MAX_TOKENS           # Output limit reached
    - RESOURCE_EXHAUSTED   # Rate limit / quota

    Transient:
    - UNAVAILABLE          # Service temporarily down
    - DEADLINE_EXCEEDED    # Timeout
    - CANCELLED            # Client cancelled

    System:
    - UNKNOWN              # Unspecified error

    WHEN TO break vs continue:
    --------------------------
    break (Terminal):
    - SAFETY, PROHIBITED_CONTENT, BLOCKLIST
    - MAX_TOKENS
    - Model has stopped generating

    continue (May Recover):
    - UNAVAILABLE, DEADLINE_EXCEEDED
    - RESOURCE_EXHAUSTED (with backoff)
    - UNKNOWN

    ERROR HANDLING PATTERN:
    -----------------------
    retry_count = 0

    try:
        async for event in runner.run_live(...):
            # Check errors first
            if event.error_code:
                if event.error_code in ["SAFETY", "MAX_TOKENS"]:
                    await notify_user(f"Error: {event.error_message}")
                    break

                if event.error_code == "RESOURCE_EXHAUSTED":
                    retry_count += 1
                    if retry_count > 3:
                        break
                    await asyncio.sleep(2 ** retry_count)
                    continue

                continue  # Other errors

            # Reset on success
            retry_count = 0

            # Process normal events
            process_event(event)

    finally:
        queue.close()

    BEST PRACTICES:
    ---------------
    1. Always check error_code FIRST
    2. Log errors with context (session_id, user_id)
    3. Notify users with friendly messages
    4. Implement retry for transient errors
    5. Always close queue in finally
    6. Monitor error rates for systemic issues
    """)


# =============================================================================
# Part 6: Event Serialization
# =============================================================================

def explain_serialization():
    """Explain event serialization for network transport."""
    print("""
    EVENT SERIALIZATION
    ===================

    Events are Pydantic models with built-in serialization.

    SERIALIZING TO JSON:
    --------------------
    # Basic serialization
    json_str = event.model_dump_json()

    # Recommended: exclude None values
    json_str = event.model_dump_json(
        exclude_none=True,
        by_alias=True  # Use camelCase field names
    )

    # Exclude large binary data
    json_str = event.model_dump_json(
        exclude={'content': {'parts': {'__all__': {'inline_data'}}}},
        by_alias=True
    )

    # Include only specific fields
    json_str = event.model_dump_json(
        include={'content', 'author', 'turn_complete'},
        by_alias=True
    )

    WEBSOCKET PATTERN:
    ------------------
    async for event in runner.run_live(...):
        event_json = event.model_dump_json(
            exclude_none=True,
            by_alias=True
        )
        await websocket.send_text(event_json)

    AUDIO OPTIMIZATION:
    -------------------
    Base64 encoding increases size by ~133%.
    For production, send audio separately:

    if has_audio_data(event):
        # Binary frame for audio
        await websocket.send_bytes(audio_data)

        # JSON for metadata only
        metadata = event.model_dump_json(
            exclude={'content': {'parts': {'__all__': {'inline_data'}}}},
            by_alias=True
        )
        await websocket.send_text(metadata)
    else:
        await websocket.send_text(event.model_dump_json(...))

    CLIENT DESERIALIZATION (JavaScript):
    ------------------------------------
    websocket.onmessage = (msg) => {
        const event = JSON.parse(msg.data);

        if (event.turnComplete) {
            enableInput();
        }

        if (event.interrupted) {
            stopPlayback();
        }

        if (event.content?.parts) {
            for (const part of event.content.parts) {
                if (part.text) {
                    displayText(part.text);
                }
            }
        }
    };
    """)


# =============================================================================
# Part 7: Demo - Processing Different Event Types
# =============================================================================

async def event_handling_demo():
    """Demonstrate handling different event types."""
    print("\n  Demonstrating event handling...")

    agent = LlmAgent(
        name="EventDemo",
        model="gemini-2.0-flash",
        instruction="You are helpful. Keep responses under 2 sentences.",
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="event_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="event_demo",
        user_id="user1",
        session_id="event_session",
        state={}
    )

    queue = LiveRequestQueue()
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["TEXT"],
    )

    print("\n  Event Processing:")
    print("  " + "-"*50)

    stats = {
        "total_events": 0,
        "text_events": 0,
        "partial_events": 0,
        "complete_events": 0,
        "turn_complete": False,
        "text_content": []
    }

    async def process_events():
        try:
            async for event in runner.run_live(
                user_id="user1",
                session_id="event_session",
                live_request_queue=queue,
                run_config=run_config,
            ):
                stats["total_events"] += 1

                # Check for errors
                if event.error_code:
                    print(f"  ERROR: {event.error_code}")
                    continue

                # Check for text content
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            stats["text_events"] += 1

                            if event.partial:
                                stats["partial_events"] += 1
                                print(f"  [partial] {part.text[:50]}...")
                            else:
                                stats["complete_events"] += 1
                                stats["text_content"].append(part.text)
                                print(f"  [complete] {part.text[:50]}...")

                # Check for metadata
                if event.usage_metadata:
                    tokens = event.usage_metadata.total_token_count
                    if tokens:
                        print(f"  [metadata] tokens: {tokens}")

                # Check for turn completion
                if event.turn_complete:
                    stats["turn_complete"] = True
                    print("  [turn_complete]")
                    break

        except Exception as e:
            print(f"  Event loop ended: {type(e).__name__}")

    async def send_query():
        await asyncio.sleep(0.5)
        print("  User: What is the capital of France?")
        queue.send_content(
            types.Content(
                role="user",
                parts=[types.Part(text="What is the capital of France?")]
            )
        )
        await asyncio.sleep(4)
        queue.close()

    try:
        await asyncio.gather(process_events(), send_query())
    except Exception:
        pass

    print("\n  " + "-"*50)
    print(f"\n  Event Statistics:")
    print(f"    Total events: {stats['total_events']}")
    print(f"    Text events: {stats['text_events']}")
    print(f"    Partial events: {stats['partial_events']}")
    print(f"    Complete events: {stats['complete_events']}")
    print(f"    Turn completed: {stats['turn_complete']}")

    if stats['text_content']:
        print(f"    Final text: {stats['text_content'][-1][:80]}...")


async def main():
    print("\n" + "#"*70)
    print("# Lab 6 Exercise 3: Streaming Events")
    print("#"*70)

    # =========================================================================
    # Part 1: Event Class
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Understanding the Event Class")
    print("="*60)
    explain_event_class()

    # =========================================================================
    # Part 2: Text Events
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Text Event Handling")
    print("="*60)
    explain_text_events()

    # =========================================================================
    # Part 3: Audio Events
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Audio Events")
    print("="*60)
    explain_audio_events()

    # =========================================================================
    # Part 4: Metadata & Transcription
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Metadata and Transcription Events")
    print("="*60)
    explain_metadata_events()

    # =========================================================================
    # Part 5: Error Handling
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Error Handling")
    print("="*60)
    explain_error_handling()

    # =========================================================================
    # Part 6: Serialization
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Event Serialization")
    print("="*60)
    explain_serialization()

    # =========================================================================
    # Part 7: Demo
    # =========================================================================
    print("\n" + "="*60)
    print("PART 7: Event Handling Demo")
    print("="*60)

    await event_handling_demo()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Streaming Events")
    print("#"*70)
    print("""
    EVENT TYPES:
    ------------
    - Text: event.content.parts[].text
    - Audio: event.content.parts[].inline_data
    - Transcription: event.input/output_transcription
    - Metadata: event.usage_metadata
    - Errors: event.error_code / error_message

    KEY FLAGS:
    ----------
    - partial: True=streaming chunk, False=complete
    - turn_complete: Model finished responding
    - interrupted: User interrupted mid-response

    HANDLING PATTERN:
    -----------------
    async for event in runner.run_live(...):
        # 1. Check errors
        if event.error_code:
            handle_error(event)

        # 2. Check interruption
        if event.interrupted:
            stop_output()

        # 3. Process content
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    display_text(part.text, event.partial)
                if part.inline_data:
                    play_audio(part.inline_data.data)

        # 4. Check turn completion
        if event.turn_complete:
            ready_for_input()

    SERIALIZATION:
    --------------
    event.model_dump_json(exclude_none=True, by_alias=True)
    """)


if __name__ == "__main__":
    asyncio.run(main())
