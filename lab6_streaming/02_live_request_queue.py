"""
Lab 6 - Exercise 2: LiveRequestQueue
=====================================

This exercise covers sending messages upstream:
1. LiveRequestQueue and LiveRequest structure
2. send_content() for text messages
3. send_realtime() for audio/video
4. Activity signals for manual turn control
5. Control signals and graceful termination

Run: uv run python 02_live_request_queue.py
"""

import asyncio
from google.adk.agents import LlmAgent, LiveRequestQueue
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode


# =============================================================================
# Part 1: Understanding LiveRequestQueue
# =============================================================================

def explain_live_request_queue():
    """Explain the LiveRequestQueue structure."""
    print("""
    LiveRequestQueue OVERVIEW
    =========================

    LiveRequestQueue is your interface for sending messages TO the agent.
    It handles all upstream communication in Bidi-streaming.

    THE LiveRequest MODEL:
    ----------------------
    class LiveRequest:
        content: Optional[Content] = None      # Text messages
        blob: Optional[Blob] = None            # Audio/video data
        activity_start: Optional[ActivityStart] = None  # User started speaking
        activity_end: Optional[ActivityEnd] = None      # User stopped speaking
        close: bool = False                    # Terminate connection

    IMPORTANT: content and blob are MUTUALLY EXCLUSIVE
    - Only one can be set per LiveRequest
    - ADK's convenience methods handle this automatically

    CONVENIENCE METHODS:
    --------------------
    queue.send_content(content)     # Sets content field
    queue.send_realtime(blob)       # Sets blob field
    queue.send_activity_start()     # Sets activity_start
    queue.send_activity_end()       # Sets activity_end
    queue.close()                   # Sets close=True

    MESSAGE FLOW:
    -------------
    Application → LiveRequestQueue → LiveRequest → Gemini Live API

    ┌─────────────────────────────────────────────────────────────┐
    │  Application Code                                           │
    │  - User types text                                          │
    │  - Microphone captures audio                                │
    │  - Camera captures video                                    │
    └─────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  LiveRequestQueue Methods                                   │
    │  - send_content(text)                                       │
    │  - send_realtime(audio/video)                               │
    │  - send_activity_start/end()                                │
    │  - close()                                                  │
    └─────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  LiveRequest Container                                      │
    │  [content | blob | activity_* | close]                      │
    └─────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌─────────────────────────────────────────────────────────────┐
    │  Gemini Live API (WebSocket)                                │
    └─────────────────────────────────────────────────────────────┘
    """)


# =============================================================================
# Part 2: send_content() - Text Messages
# =============================================================================

def explain_send_content():
    """Explain sending text content."""
    print("""
    send_content() - SENDING TEXT
    =============================

    Use send_content() to send text messages to the agent.
    This is "turn-by-turn" mode - each message is a complete turn.

    BASIC USAGE:
    ------------
    from google.genai import types

    content = types.Content(
        role="user",
        parts=[types.Part(text="Hello, how are you?")]
    )
    queue.send_content(content)

    CONTENT STRUCTURE:
    ------------------
    Content:
      role: "user" (always for user messages)
      parts: List[Part]
        - Part(text="...")  # Text content

    WHEN TO USE:
    ------------
    - Text chat messages
    - Commands/queries
    - Structured data as text
    - Turn-by-turn conversations

    WHAT HAPPENS:
    -------------
    1. Content is wrapped in LiveRequest
    2. Sent to Gemini Live API
    3. Model processes as complete turn
    4. Model generates response immediately

    EXAMPLE PATTERNS:
    -----------------
    # Simple text
    queue.send_content(
        types.Content(parts=[types.Part(text="What's the weather?")])
    )

    # Multi-part text (less common)
    queue.send_content(
        types.Content(parts=[
            types.Part(text="Context: "),
            types.Part(text="Question: ")
        ])
    )

    NOTE: For audio/video, use send_realtime() instead!
    """)


# =============================================================================
# Part 3: send_realtime() - Audio/Video Streams
# =============================================================================

def explain_send_realtime():
    """Explain sending audio/video data."""
    print("""
    send_realtime() - AUDIO/VIDEO STREAMS
    ======================================

    Use send_realtime() for binary data streams (audio, images, video).
    This is "realtime" mode - continuous streaming without explicit turns.

    BASIC USAGE:
    ------------
    from google.genai import types

    # Audio chunk
    audio_blob = types.Blob(
        mime_type="audio/pcm;rate=16000",
        data=audio_bytes  # Raw PCM bytes
    )
    queue.send_realtime(audio_blob)

    # Image frame
    image_blob = types.Blob(
        mime_type="image/jpeg",
        data=jpeg_bytes
    )
    queue.send_realtime(image_blob)

    BLOB STRUCTURE:
    ---------------
    Blob:
      mime_type: str  # Format identifier
      data: bytes     # Binary data

    SUPPORTED MIME TYPES:
    ---------------------
    Audio:
      - "audio/pcm;rate=16000"     # Raw PCM, 16kHz (recommended)
      - "audio/pcm"                # Raw PCM

    Images:
      - "image/jpeg"               # JPEG images
      - "image/png"                # PNG images

    Video:
      - Video frames sent as images

    WHEN TO USE:
    ------------
    - Microphone audio streams
    - Camera video frames
    - Screen capture
    - File playback

    STREAMING PATTERN:
    ------------------
    # Continuous audio streaming
    while recording:
        audio_chunk = microphone.read(chunk_size)
        blob = types.Blob(
            mime_type="audio/pcm;rate=16000",
            data=audio_chunk
        )
        queue.send_realtime(blob)
        await asyncio.sleep(0.01)  # ~100 chunks/second

    BASE64 ENCODING:
    ----------------
    Pydantic automatically handles base64 encoding during serialization.
    You provide raw bytes - ADK handles the rest!
    """)


# =============================================================================
# Part 4: Activity Signals
# =============================================================================

def explain_activity_signals():
    """Explain activity signals for manual turn control."""
    print("""
    ACTIVITY SIGNALS - MANUAL TURN CONTROL
    ======================================

    Activity signals let YOU control when the user is speaking,
    instead of relying on automatic Voice Activity Detection (VAD).

    WHEN VAD IS DISABLED:
    ---------------------
    - You MUST use activity signals
    - Model doesn't know when user speaks without them
    - Required for push-to-talk interfaces

    THE SIGNALS:
    ------------
    send_activity_start()
      "User started speaking - accumulate audio"

    send_activity_end()
      "User stopped speaking - process and respond"

    USAGE PATTERN:
    --------------
    # Push-to-talk example
    queue.send_activity_start()  # User pressed button

    while button_held:
        audio_chunk = microphone.read()
        queue.send_realtime(types.Blob(
            mime_type="audio/pcm;rate=16000",
            data=audio_chunk
        ))

    queue.send_activity_end()  # User released button

    WHEN TO USE:
    ------------
    1. Push-to-talk interfaces
       - User holds button to speak
       - Release to get response

    2. Noisy environments
       - Automatic VAD is unreliable
       - Manual control is more accurate

    3. Client-side VAD
       - Your app detects speech locally
       - Reduces network overhead

    4. Custom interaction patterns
       - Gesture-triggered audio
       - Timed audio segments

    DEFAULT BEHAVIOR (WITHOUT SIGNALS):
    ------------------------------------
    When you DON'T send activity signals:
    - Live API uses automatic VAD
    - Detects speech boundaries in audio
    - Handles turn detection for you

    Most apps use automatic VAD - it's simpler!

    CONFIGURING VAD:
    ----------------
    from google.adk.agents.run_config import RunConfig

    # Automatic VAD (default)
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        # VAD enabled by default
    )

    # Manual activity signals
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        realtime_input_config={
            "automatic_activity_detection": {
                "disabled": True
            }
        }
    )
    """)


# =============================================================================
# Part 5: Control Signals - close()
# =============================================================================

def explain_close():
    """Explain graceful termination with close()."""
    print("""
    close() - GRACEFUL TERMINATION
    ==============================

    The close() method terminates the streaming connection gracefully.

    WHAT IT DOES:
    -------------
    1. Sends LiveRequest(close=True) to the API
    2. Signals run_live() to exit
    3. Closes WebSocket connection
    4. Cleans up resources

    BASIC USAGE:
    ------------
    try:
        async for event in runner.run_live(..., live_request_queue=queue):
            # Process events...
            pass
    finally:
        queue.close()  # ALWAYS close in finally!

    WHY ALWAYS USE finally:
    -----------------------
    - Ensures cleanup even if exceptions occur
    - Prevents "zombie" sessions on the server
    - Releases quota/resources immediately

    WHAT HAPPENS IF YOU DON'T CLOSE:
    ---------------------------------
    - Local resources cleaned up eventually
    - BUT server doesn't get termination signal
    - Session stays open until timeout
    - Counts against your concurrent session quota!

    PROPER PATTERNS:
    ----------------
    # Pattern 1: try/finally
    queue = LiveRequestQueue()
    try:
        async for event in runner.run_live(...):
            if should_exit:
                break
    finally:
        queue.close()

    # Pattern 2: Context manager (future ADK versions)
    async with LiveRequestQueue() as queue:
        async for event in runner.run_live(...):
            ...

    # Pattern 3: Error handling
    try:
        async for event in runner.run_live(...):
            process(event)
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        queue.close()

    BIDI vs SSE MODES:
    ------------------
    BIDI mode: YOU must call close() manually
    SSE mode: ADK calls close() automatically on turn_complete
    """)


# =============================================================================
# Part 6: Concurrency and Best Practices
# =============================================================================

def explain_best_practices():
    """Explain concurrency patterns and best practices."""
    print("""
    BEST PRACTICES
    ==============

    1. CREATE QUEUE IN ASYNC CONTEXT:
    ----------------------------------
    # RECOMMENDED
    async def main():
        queue = LiveRequestQueue()  # Correct event loop
        ...

    # NOT RECOMMENDED
    queue = LiveRequestQueue()  # May create new event loop
    asyncio.run(main())

    2. CONCURRENT UPSTREAM/DOWNSTREAM:
    -----------------------------------
    async def upstream():
        '''Send user input to agent.'''
        while True:
            audio = await microphone.read()
            queue.send_realtime(blob=types.Blob(...))

    async def downstream():
        '''Receive events from agent.'''
        async for event in runner.run_live(...):
            await handle_event(event)

    # Run both concurrently
    await asyncio.gather(upstream(), downstream())

    3. MESSAGE ORDERING:
    --------------------
    - FIFO ordering guaranteed
    - Messages processed in send order
    - No coalescing/batching

    4. QUEUE IS UNBOUNDED:
    ----------------------
    - No blocking on send
    - Can grow indefinitely
    - Monitor in production: queue._queue.qsize()

    5. THREAD SAFETY:
    -----------------
    - Safe within same event loop thread
    - For different threads, use loop.call_soon_threadsafe()

    6. RESOURCE CLEANUP:
    --------------------
    - Always use try/finally
    - Call close() to release resources
    - Handle all exceptions

    PRODUCTION PATTERN:
    -------------------
    async def handle_streaming_session():
        queue = LiveRequestQueue()

        async def upstream_task():
            try:
                while True:
                    data = await get_user_input()
                    if data.is_text:
                        queue.send_content(data.content)
                    else:
                        queue.send_realtime(data.blob)
            except asyncio.CancelledError:
                pass

        async def downstream_task():
            async for event in runner.run_live(
                user_id=user_id,
                session_id=session_id,
                live_request_queue=queue,
                run_config=run_config
            ):
                await send_to_client(event)

        try:
            await asyncio.gather(
                upstream_task(),
                downstream_task()
            )
        except Exception as e:
            logger.error(f"Session error: {e}")
        finally:
            queue.close()
    """)


# =============================================================================
# Part 7: Demo - Sending Different Message Types
# =============================================================================

async def message_types_demo():
    """Demonstrate different message types with LiveRequestQueue."""
    print("\n  Demonstrating LiveRequestQueue message types...")

    agent = LlmAgent(
        name="MessageDemo",
        model="gemini-2.0-flash",
        instruction="You are a helpful assistant. Respond briefly.",
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="queue_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="queue_demo",
        user_id="user1",
        session_id="queue_session",
        state={}
    )

    queue = LiveRequestQueue()

    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["TEXT"],
    )

    print("\n  Message Types Available:")
    print("  " + "-"*50)

    # Demonstrate message type creation (without actually streaming)
    print("\n  1. Text Content (send_content):")
    text_content = types.Content(
        role="user",
        parts=[types.Part(text="Hello, world!")]
    )
    print(f"     Content: {text_content}")

    print("\n  2. Audio Blob (send_realtime):")
    # Simulated audio data
    fake_audio = b'\x00\x01' * 100  # Fake PCM bytes
    audio_blob = types.Blob(
        mime_type="audio/pcm;rate=16000",
        data=fake_audio
    )
    print(f"     Blob: mime_type={audio_blob.mime_type}, size={len(audio_blob.data)} bytes")

    print("\n  3. Image Blob (send_realtime):")
    # Simulated image data
    fake_image = b'\xff\xd8\xff' + b'\x00' * 100  # Fake JPEG header
    image_blob = types.Blob(
        mime_type="image/jpeg",
        data=fake_image
    )
    print(f"     Blob: mime_type={image_blob.mime_type}, size={len(image_blob.data)} bytes")

    print("\n  4. Activity Signals:")
    print("     send_activity_start() - Signal user started speaking")
    print("     send_activity_end() - Signal user stopped speaking")

    print("\n  5. Control Signal:")
    print("     close() - Terminate connection gracefully")

    # Quick demo: send text and get response
    print("\n  " + "-"*50)
    print("\n  Quick text exchange demo:")

    async def quick_exchange():
        event_received = False
        try:
            async for event in runner.run_live(
                user_id="user1",
                session_id="queue_session",
                live_request_queue=queue,
                run_config=run_config,
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            print(f"     Agent: {part.text[:80]}...")
                            event_received = True

                if event.turn_complete:
                    break
        except Exception as e:
            print(f"     Exchange completed: {type(e).__name__}")

    async def send_message():
        await asyncio.sleep(0.5)
        print("     User: What is 2+2?")
        queue.send_content(
            types.Content(
                role="user",
                parts=[types.Part(text="What is 2+2? Answer in one word.")]
            )
        )
        await asyncio.sleep(3)
        queue.close()

    try:
        await asyncio.gather(quick_exchange(), send_message())
    except Exception as e:
        pass

    print("\n  Demo complete!")


async def main():
    print("\n" + "#"*70)
    print("# Lab 6 Exercise 2: LiveRequestQueue")
    print("#"*70)

    # =========================================================================
    # Part 1: Overview
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Understanding LiveRequestQueue")
    print("="*60)
    explain_live_request_queue()

    # =========================================================================
    # Part 2: send_content()
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: send_content() - Text Messages")
    print("="*60)
    explain_send_content()

    # =========================================================================
    # Part 3: send_realtime()
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: send_realtime() - Audio/Video")
    print("="*60)
    explain_send_realtime()

    # =========================================================================
    # Part 4: Activity Signals
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Activity Signals")
    print("="*60)
    explain_activity_signals()

    # =========================================================================
    # Part 5: close()
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: close() - Graceful Termination")
    print("="*60)
    explain_close()

    # =========================================================================
    # Part 6: Best Practices
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Best Practices")
    print("="*60)
    explain_best_practices()

    # =========================================================================
    # Part 7: Demo
    # =========================================================================
    print("\n" + "="*60)
    print("PART 7: Message Types Demo")
    print("="*60)

    await message_types_demo()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: LiveRequestQueue")
    print("#"*70)
    print("""
    LiveRequestQueue METHODS:
    -------------------------

    send_content(content)
      - Send text messages
      - Turn-by-turn mode
      - Triggers immediate response

    send_realtime(blob)
      - Send audio/video chunks
      - Continuous streaming
      - Use with types.Blob(mime_type, data)

    send_activity_start()
      - Signal user started speaking
      - Only when VAD is disabled
      - For push-to-talk interfaces

    send_activity_end()
      - Signal user stopped speaking
      - Triggers model response
      - Only when VAD is disabled

    close()
      - Terminate connection gracefully
      - Always call in finally block
      - Releases server resources

    KEY TAKEAWAYS:
    --------------
    - content and blob are mutually exclusive
    - Use convenience methods (send_*)
    - Create queue in async context
    - Always close in finally block
    - Queue is FIFO and unbounded
    - Concurrent upstream/downstream is typical
    """)


if __name__ == "__main__":
    asyncio.run(main())
