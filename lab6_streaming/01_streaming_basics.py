"""
Lab 6 - Exercise 1: Streaming Basics
=====================================

This exercise introduces ADK Bidi-streaming fundamentals:
1. What is Bidi-streaming?
2. When to use streaming vs non-streaming
3. The four-phase lifecycle
4. Core components overview
5. Simple text streaming demo

Run: uv run python 01_streaming_basics.py
"""

import asyncio
from google.adk.agents import LlmAgent, LiveRequestQueue
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode


# =============================================================================
# Part 1: What is Bidi-streaming?
# =============================================================================

def explain_bidi_streaming():
    """Explain bidirectional streaming concepts."""
    print("""
    WHAT IS BIDI-STREAMING?
    =======================

    Bidi-streaming = Bidirectional streaming
    Real-time, two-way communication between your app and the agent.

    TRADITIONAL (run_async):
    -------------------------
    User sends message → Agent processes → Complete response returned
    [Wait...] [Wait...] [Wait...] [Here's your answer!]

    BIDI-STREAMING (run_live):
    ---------------------------
    User speaks → Agent responds in real-time → User can interrupt!
    [Hi!] [Hello!] [How-] [Actually...] [Yes?]

    KEY DIFFERENCES:
    ----------------
    ┌─────────────────────────────────────────────────────────────┐
    │  Aspect           │  run_async        │  run_live          │
    ├─────────────────────────────────────────────────────────────┤
    │  Communication    │  Request-Response │  Bidirectional     │
    │  Response timing  │  Wait for full    │  Stream as ready   │
    │  Interruptions    │  Not possible     │  Supported         │
    │  Audio/Video      │  File-based       │  Real-time stream  │
    │  Turn detection   │  Explicit         │  Automatic (VAD)   │
    │  Use case         │  Chatbots, tasks  │  Voice assistants  │
    └─────────────────────────────────────────────────────────────┘

    BASED ON:
    ---------
    - Gemini Live API (Google AI Platform)
    - Vertex AI Live API (Google Cloud)

    ENABLES:
    --------
    - Voice conversations
    - Real-time video analysis
    - Low-latency interactions
    - Natural interruptions
    """)


# =============================================================================
# Part 2: When to Use Streaming
# =============================================================================

def explain_when_to_use():
    """Explain when to use streaming vs non-streaming."""
    print("""
    WHEN TO USE STREAMING
    =====================

    USE run_live() (STREAMING) FOR:
    --------------------------------
    1. Voice Applications
       - Voice assistants
       - Phone bots
       - Real-time transcription

    2. Video Applications
       - Security monitoring
       - Video analysis
       - AR/VR interactions

    3. Interactive Applications
       - User might interrupt
       - Need immediate feedback
       - Continuous data flow

    USE run_async() (NON-STREAMING) FOR:
    -------------------------------------
    1. Task Completion
       - Code generation
       - Document analysis
       - Batch processing

    2. Chatbots
       - Text-based chat
       - Customer service
       - Q&A systems

    3. Backend Processing
       - API integrations
       - Scheduled tasks
       - Data pipelines

    HYBRID APPROACH:
    ----------------
    Many apps use BOTH:
    - run_live() for voice/video interactions
    - run_async() for background tasks

    EXAMPLE:
    --------
    Voice assistant app:
    - run_live(): Real-time voice conversation
    - run_async(): Generate detailed reports in background
    """)


# =============================================================================
# Part 3: Four-Phase Lifecycle
# =============================================================================

def explain_lifecycle():
    """Explain the four-phase lifecycle of Bidi-streaming."""
    print("""
    BIDI-STREAMING LIFECYCLE
    ========================

    PHASE 1: INITIALIZATION
    -----------------------
    1. Create LiveRequestQueue
    2. Create/get Session
    3. Configure RunConfig
    4. Prepare agent

    ```python
    queue = LiveRequestQueue()
    session = await session_service.create_session(...)
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["TEXT"]  # or ["AUDIO"]
    )
    ```

    PHASE 2: CONNECTION
    -------------------
    1. Call runner.run_live()
    2. WebSocket connection established
    3. Start upstream/downstream tasks

    ```python
    async for event in runner.run_live(
        user_id="user1",
        session_id="session1",
        live_request_queue=queue,
        run_config=run_config
    ):
        # Process events...
    ```

    PHASE 3: CONVERSATION
    ---------------------
    1. Send messages via queue (upstream)
    2. Receive events via run_live() (downstream)
    3. Handle text, audio, tool calls
    4. Process interruptions

    ```python
    # Upstream: Send user input
    queue.send_content(types.Content(parts=[types.Part(text="Hello")]))

    # Downstream: Receive events
    async for event in runner.run_live(...):
        if event.content:
            handle_response(event)
    ```

    PHASE 4: TERMINATION
    --------------------
    1. Call queue.close()
    2. run_live() exits
    3. Resources cleaned up

    ```python
    queue.close()  # Graceful termination
    ```

    FLOW DIAGRAM:
    -------------
              ┌─────────────────────────────────────┐
              │         Your Application            │
              └─────────────────────────────────────┘
                      │                   ▲
         send_content │                   │ events
         send_realtime│                   │
                      ▼                   │
              ┌───────────────────────────────────┐
              │      LiveRequestQueue             │
              │    (upstream messages)            │
              └───────────────────────────────────┘
                      │                   │
                      ▼                   │
              ┌───────────────────────────────────┐
              │        run_live()                 │
              │    (event generator)              │
              └───────────────────────────────────┘
                      │                   ▲
                      ▼                   │
              ┌───────────────────────────────────┐
              │      Gemini Live API              │
              └───────────────────────────────────┘
    """)


# =============================================================================
# Part 4: Core Components
# =============================================================================

def explain_components():
    """Explain the core streaming components."""
    print("""
    CORE STREAMING COMPONENTS
    =========================

    1. LiveRequestQueue
    -------------------
    Your channel to send messages TO the agent.

    Methods:
    - send_content(content)     # Send text messages
    - send_realtime(blob)       # Send audio/video chunks
    - send_activity_start()     # Signal user started speaking
    - send_activity_end()       # Signal user stopped speaking
    - close()                   # Terminate connection

    2. run_live() AsyncGenerator
    ----------------------------
    Your channel to receive events FROM the agent.

    Returns Event objects with:
    - content: Text or audio response
    - partial: Is this a chunk or complete?
    - turn_complete: Model finished responding?
    - interrupted: User interrupted?
    - input_transcription: User's speech-to-text
    - output_transcription: Agent's speech-to-text

    3. RunConfig
    ------------
    Configure streaming behavior:

    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,  # Enable bidirectional
        response_modalities=["TEXT"],       # or ["AUDIO"]
        speech_config=SpeechConfig(...),    # Voice settings
        input_audio_transcription=True,     # Transcribe user speech
        output_audio_transcription=True,    # Transcribe agent speech
    )

    4. Event
    --------
    Container for all streaming responses:

    event.content           # Text/audio content
    event.author            # Which agent responded
    event.partial           # Streaming chunk?
    event.turn_complete     # Turn finished?
    event.interrupted       # User interrupted?
    event.error_code        # Error information
    event.usage_metadata    # Token counts
    """)


# =============================================================================
# Part 5: Simple Text Streaming Demo
# =============================================================================

def create_streaming_agent():
    """Create a simple agent for streaming demo."""
    agent = LlmAgent(
        name="StreamingAgent",
        model="gemini-2.0-flash",
        instruction="""You are a helpful assistant that provides concise responses.
        When asked a question, answer in 2-3 sentences.""",
    )
    return agent


async def text_streaming_demo():
    """Demonstrate basic text streaming with run_live()."""
    print("\n  Creating streaming agent...")

    agent = create_streaming_agent()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=agent,
        app_name="streaming_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="streaming_demo",
        user_id="user1",
        session_id="stream_session",
        state={}
    )

    # Create the queue for sending messages
    queue = LiveRequestQueue()

    # Configure for text streaming
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["TEXT"],
    )

    print("  Starting streaming conversation...")
    print("  " + "-"*50)

    # Start the streaming task
    async def process_events():
        """Process events from run_live()."""
        event_count = 0
        try:
            async for event in runner.run_live(
                user_id="user1",
                session_id="stream_session",
                live_request_queue=queue,
                run_config=run_config,
            ):
                event_count += 1

                # Check for text content
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            status = "partial" if event.partial else "complete"
                            print(f"  [{event.author}] ({status}): {part.text[:60]}...")

                # Check for turn completion
                if event.turn_complete:
                    print(f"  [Turn complete after {event_count} events]")
                    break  # Exit after first complete response for demo

        except Exception as e:
            print(f"  Error: {e}")

    # Send a message and process response
    async def send_and_receive():
        """Send message and process streaming response."""
        # Give the stream a moment to initialize
        await asyncio.sleep(0.5)

        # Send user message
        print("\n  User: What is Python programming language?")
        queue.send_content(
            types.Content(
                role="user",
                parts=[types.Part(text="What is Python programming language?")]
            )
        )

        # Wait for response to complete
        await asyncio.sleep(5)

        # Close the queue
        queue.close()

    # Run both tasks
    try:
        await asyncio.gather(
            process_events(),
            send_and_receive()
        )
    except Exception as e:
        print(f"  Demo completed: {e}")

    print("\n  " + "-"*50)
    print("  Streaming demo complete!")


# =============================================================================
# Part 6: Comparison with run_async()
# =============================================================================

async def comparison_demo():
    """Compare run_async() vs run_live() behavior."""
    print("\n  Comparing run_async() and run_live():")
    print("  " + "-"*50)

    agent = create_streaming_agent()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=agent,
        app_name="compare_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="compare_demo",
        user_id="user1",
        session_id="async_session",
        state={}
    )

    # Using run_async (non-streaming)
    print("\n  [run_async] - Non-streaming:")
    user_message = types.Content(
        role="user",
        parts=[types.Part(text="Say hello briefly")]
    )

    event_count = 0
    async for event in runner.run_async(
        user_id="user1",
        session_id="async_session",
        new_message=user_message,
    ):
        event_count += 1
        if event.is_final_response() and event.content:
            print(f"    Final response: {event.content.parts[0].text[:80]}...")

    print(f"    Events received: {event_count}")
    print("    (All events arrive together at the end)")

    print("\n  [run_live] - Streaming:")
    print("    Events would arrive incrementally (partial=True)")
    print("    User could interrupt mid-response")
    print("    Supports audio/video in real-time")


async def main():
    print("\n" + "#"*70)
    print("# Lab 6 Exercise 1: Streaming Basics")
    print("#"*70)

    # =========================================================================
    # Part 1: What is Bidi-streaming
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: What is Bidi-streaming?")
    print("="*60)
    explain_bidi_streaming()

    # =========================================================================
    # Part 2: When to Use
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: When to Use Streaming")
    print("="*60)
    explain_when_to_use()

    # =========================================================================
    # Part 3: Lifecycle
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Four-Phase Lifecycle")
    print("="*60)
    explain_lifecycle()

    # =========================================================================
    # Part 4: Components
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Core Components")
    print("="*60)
    explain_components()

    # =========================================================================
    # Part 5: Text Streaming Demo
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Text Streaming Demo")
    print("="*60)

    await text_streaming_demo()

    # =========================================================================
    # Part 6: Comparison
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Comparing run_async() vs run_live()")
    print("="*60)

    await comparison_demo()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Streaming Basics")
    print("#"*70)
    print("""
    BIDI-STREAMING OVERVIEW:
    ------------------------
    Real-time, bidirectional communication with agents.
    Based on Gemini Live API / Vertex AI Live API.

    CORE COMPONENTS:
    ----------------
    - LiveRequestQueue: Send messages upstream
    - run_live(): Receive events downstream
    - RunConfig: Configure streaming behavior
    - Event: Container for all responses

    LIFECYCLE:
    ----------
    1. Initialize: Create queue, session, config
    2. Connect: Call run_live()
    3. Converse: Send/receive concurrently
    4. Terminate: Call queue.close()

    KEY DIFFERENCES FROM run_async():
    ----------------------------------
    - Real-time event streaming (partial chunks)
    - User can interrupt mid-response
    - Supports audio/video streams
    - Automatic voice activity detection

    WHEN TO USE:
    ------------
    - Voice/video applications
    - Real-time interactions
    - Low-latency requirements
    - Natural conversation flow
    """)


if __name__ == "__main__":
    asyncio.run(main())
