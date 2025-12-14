"""
Lab 6 - Exercise 4: Audio & Video Streaming
============================================

This exercise covers audio and video streaming concepts:
1. Audio input/output specifications
2. Voice Activity Detection (VAD)
3. Audio transcription
4. Video/image streaming
5. RunConfig for audio/video

Run: uv run python 04_audio_video_streaming.py
"""

import asyncio
from google.adk.agents import LlmAgent, LiveRequestQueue
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode


# =============================================================================
# Part 1: Audio Input Specifications
# =============================================================================

def explain_audio_input():
    """Explain audio input requirements."""
    print("""
    AUDIO INPUT SPECIFICATIONS
    ==========================

    To send audio to the agent, you must follow these specifications.

    REQUIRED FORMAT:
    ----------------
    - Encoding: 16-bit signed PCM
    - Sample rate: 16,000 Hz (16kHz)
    - Channels: Mono (1 channel)
    - Byte order: Little-endian

    MIME TYPE:
    ----------
    "audio/pcm;rate=16000"

    SENDING AUDIO:
    --------------
    from google.genai import types

    # Read audio from microphone/file
    audio_bytes = get_audio_chunk()  # Raw PCM bytes

    # Create blob
    audio_blob = types.Blob(
        mime_type="audio/pcm;rate=16000",
        data=audio_bytes
    )

    # Send to agent
    queue.send_realtime(audio_blob)

    CHUNK SIZE:
    -----------
    Recommended: 20-100ms of audio per chunk
    At 16kHz, 16-bit mono:
    - 20ms = 640 bytes (16000 * 0.02 * 2)
    - 50ms = 1600 bytes
    - 100ms = 3200 bytes

    STREAMING PATTERN:
    ------------------
    CHUNK_SIZE = 1600  # ~50ms of audio

    async def stream_audio():
        while recording:
            # Read from microphone
            audio_chunk = await microphone.read(CHUNK_SIZE)

            # Send to agent
            queue.send_realtime(types.Blob(
                mime_type="audio/pcm;rate=16000",
                data=audio_chunk
            ))

            # Don't flood - yield control
            await asyncio.sleep(0.01)

    CONVERTING AUDIO FORMATS:
    -------------------------
    If your audio is in a different format, convert it:

    # Using pydub (install: pip install pydub)
    from pydub import AudioSegment

    audio = AudioSegment.from_file("input.wav")
    audio = audio.set_frame_rate(16000)
    audio = audio.set_channels(1)
    audio = audio.set_sample_width(2)  # 16-bit
    pcm_bytes = audio.raw_data

    # Using soundfile (install: pip install soundfile)
    import soundfile as sf
    data, samplerate = sf.read("input.wav")
    # Resample to 16kHz if needed
    """)


# =============================================================================
# Part 2: Audio Output Specifications
# =============================================================================

def explain_audio_output():
    """Explain audio output format."""
    print("""
    AUDIO OUTPUT SPECIFICATIONS
    ===========================

    When response_modalities=["AUDIO"], the model generates audio.

    OUTPUT FORMAT:
    --------------
    - Encoding: 16-bit signed PCM
    - Sample rate: 24,000 Hz (24kHz) for native audio models
    - Channels: Mono (1 channel)

    RECEIVING AUDIO:
    ----------------
    async for event in runner.run_live(...):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.inline_data:
                    audio_data = part.inline_data.data
                    mime_type = part.inline_data.mime_type
                    # Play audio at 24kHz

    AUDIO PLAYBACK:
    ---------------
    # Using pyaudio (install: pip install pyaudio)
    import pyaudio

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=24000,  # Native audio output rate
        output=True
    )

    async for event in runner.run_live(...):
        if has_audio(event):
            stream.write(audio_data)

    # Using sounddevice (install: pip install sounddevice)
    import sounddevice as sd
    import numpy as np

    # Convert bytes to numpy array
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    sd.play(audio_array, samplerate=24000)

    BUFFERING:
    ----------
    For smooth playback, buffer audio chunks:

    audio_buffer = asyncio.Queue()

    async def receive_audio():
        async for event in runner.run_live(...):
            if has_audio(event):
                await audio_buffer.put(event.content.parts[0].inline_data.data)

    async def play_audio():
        while True:
            chunk = await audio_buffer.get()
            play_chunk(chunk)

    await asyncio.gather(receive_audio(), play_audio())

    CONFIGURATION:
    --------------
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],  # Enable audio output
    )
    """)


# =============================================================================
# Part 3: Voice Activity Detection (VAD)
# =============================================================================

def explain_vad():
    """Explain Voice Activity Detection."""
    print("""
    VOICE ACTIVITY DETECTION (VAD)
    ==============================

    VAD determines when the user starts/stops speaking.
    This controls when the model should respond.

    AUTOMATIC VAD (DEFAULT):
    ------------------------
    The Live API automatically detects speech in audio.

    How it works:
    1. You stream audio continuously
    2. Live API detects speech start/end
    3. After speech ends, model responds

    Benefits:
    - Simple to implement
    - Natural conversation flow
    - No extra code needed

    Limitations:
    - May trigger on background noise
    - Latency in noisy environments
    - Less control over turn timing

    MANUAL VAD (ACTIVITY SIGNALS):
    ------------------------------
    You control when user is speaking using activity signals.

    Configuration:
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        realtime_input_config={
            "automatic_activity_detection": {
                "disabled": True
            }
        }
    )

    Usage:
    # Signal start of speech
    queue.send_activity_start()

    # Stream audio while user speaks
    while user_speaking:
        queue.send_realtime(audio_blob)

    # Signal end of speech
    queue.send_activity_end()

    Benefits:
    - Full control over turn boundaries
    - Works in noisy environments
    - Supports push-to-talk UI

    Limitations:
    - More code to write
    - Need speech detection logic
    - May feel less natural

    WHEN TO USE EACH:
    -----------------
    ┌────────────────────────────────────────────────────────────┐
    │  Scenario                    │  Recommendation            │
    ├────────────────────────────────────────────────────────────┤
    │  Quiet environment           │  Automatic VAD             │
    │  Noisy environment           │  Manual VAD                │
    │  Push-to-talk UI             │  Manual VAD                │
    │  Always-on microphone        │  Automatic VAD             │
    │  Client-side VAD (Silero)    │  Manual VAD                │
    │  Mobile app (hands-free)     │  Automatic VAD             │
    └────────────────────────────────────────────────────────────┘

    CLIENT-SIDE VAD:
    ----------------
    You can use libraries like Silero VAD to detect speech locally,
    then use activity signals to tell the server.

    Benefits:
    - Reduces network traffic (only send speech)
    - Works offline
    - Consistent behavior

    # Using Silero VAD
    vad_model = load_silero_vad()

    while True:
        audio_chunk = microphone.read()
        speech_prob = vad_model(audio_chunk)

        if speech_prob > 0.5 and not speaking:
            queue.send_activity_start()
            speaking = True

        if speaking:
            queue.send_realtime(audio_blob)

        if speech_prob < 0.3 and speaking:
            queue.send_activity_end()
            speaking = False
    """)


# =============================================================================
# Part 4: Audio Transcription
# =============================================================================

def explain_transcription():
    """Explain audio transcription features."""
    print("""
    AUDIO TRANSCRIPTION
    ===================

    Transcription provides text versions of speech.

    ENABLING TRANSCRIPTION:
    -----------------------
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        input_audio_transcription=True,   # Transcribe user speech
        output_audio_transcription=True,  # Transcribe agent speech
    )

    RECEIVING TRANSCRIPTIONS:
    -------------------------
    async for event in runner.run_live(...):
        # User's speech transcribed
        if event.input_transcription:
            user_text = event.input_transcription
            display_caption(f"You: {user_text}")

        # Agent's speech transcribed
        if event.output_transcription:
            agent_text = event.output_transcription
            display_caption(f"Agent: {agent_text}")

    TRANSCRIPTION TIMING:
    ---------------------
    Input transcription:
    - Arrives shortly after user stops speaking
    - event.author = "user"

    Output transcription:
    - Arrives as agent speaks
    - May be partial (event.partial = True)
    - Final transcription at turn end

    USE CASES:
    ----------
    1. Accessibility
       - Display captions for hearing impaired
       - Screen reader support

    2. Logging
       - Save conversation as text
       - Search/index conversations

    3. Debugging
       - Verify speech recognition accuracy
       - Debug voice interactions

    4. UI Display
       - Show what user said
       - Show what agent is saying
       - Build chat-like interface for voice

    TRANSCRIPTION + TEXT COMPARISON:
    --------------------------------
    Voice mode with transcription gives you:
    - Audio output (natural voice)
    - Text transcription (for display/logging)

    Text mode gives you:
    - Text output only
    - No audio

    For voice assistants, use AUDIO + transcription for best UX.

    TRANSCRIPTION ACCURACY:
    -----------------------
    - Generally high accuracy
    - May struggle with:
      - Heavy accents
      - Technical jargon
      - Background noise
      - Multiple speakers

    PARTIAL TRANSCRIPTIONS:
    -----------------------
    - Partial transcriptions are NOT saved to session
    - Only final transcriptions are persisted
    - Use partials for real-time display

    if event.partial and event.output_transcription:
        # Streaming display
        update_caption(event.output_transcription)
    elif not event.partial and event.output_transcription:
        # Final - can save
        save_to_log(event.output_transcription)
    """)


# =============================================================================
# Part 5: Video/Image Streaming
# =============================================================================

def explain_video_streaming():
    """Explain video and image streaming."""
    print("""
    VIDEO/IMAGE STREAMING
    =====================

    You can send images and video frames to the agent.

    SENDING IMAGES:
    ---------------
    from google.genai import types

    # Read image as bytes
    with open("image.jpg", "rb") as f:
        image_bytes = f.read()

    # Create blob
    image_blob = types.Blob(
        mime_type="image/jpeg",  # or "image/png"
        data=image_bytes
    )

    # Send to agent
    queue.send_realtime(image_blob)

    SUPPORTED IMAGE FORMATS:
    ------------------------
    - "image/jpeg" (recommended for photos)
    - "image/png" (for screenshots, diagrams)

    VIDEO AS IMAGE FRAMES:
    ----------------------
    Video is sent as a sequence of image frames.

    import cv2

    cap = cv2.VideoCapture(0)  # Webcam

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Encode frame as JPEG
        _, jpeg_bytes = cv2.imencode('.jpg', frame)

        # Send to agent
        queue.send_realtime(types.Blob(
            mime_type="image/jpeg",
            data=jpeg_bytes.tobytes()
        ))

        await asyncio.sleep(0.1)  # ~10 FPS

    FRAME RATE CONSIDERATIONS:
    --------------------------
    - Higher FPS = more bandwidth
    - 1-5 FPS often sufficient for analysis
    - 10 FPS for smoother tracking
    - Consider motion-triggered capture

    USE CASES:
    ----------
    1. Video Monitoring
       - Security camera analysis
       - People counting
       - Object detection

    2. Screen Sharing
       - Help desk support
       - Pair programming
       - Presentations

    3. Document Analysis
       - OCR on documents
       - Form filling
       - Receipt scanning

    4. Real-time Annotation
       - Describe what's in view
       - Navigation assistance
       - AR overlays

    COMBINING AUDIO + VIDEO:
    ------------------------
    You can stream both simultaneously:

    async def stream_audio():
        while True:
            audio = await microphone.read()
            queue.send_realtime(audio_blob)

    async def stream_video():
        while True:
            frame = await camera.read()
            queue.send_realtime(image_blob)
            await asyncio.sleep(0.5)  # 2 FPS

    await asyncio.gather(stream_audio(), stream_video())

    The model sees/hears everything and can respond intelligently!

    STREAMING TOOLS FOR VIDEO:
    --------------------------
    For advanced video analysis, use streaming tools
    with input_stream parameter. See Exercise 5.
    """)


# =============================================================================
# Part 6: RunConfig for Audio/Video
# =============================================================================

def explain_runconfig():
    """Explain RunConfig options for audio/video."""
    print("""
    RunConfig FOR AUDIO/VIDEO
    =========================

    RunConfig controls streaming behavior.

    BASIC AUDIO CONFIG:
    -------------------
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,  # Required
        response_modalities=["AUDIO"],       # Audio output
    )

    WITH TRANSCRIPTION:
    -------------------
    # Transcription is ENABLED by default with AudioTranscriptionConfig()
    # To disable transcription:
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        input_audio_transcription=None,   # Disable user speech-to-text
        output_audio_transcription=None,  # Disable agent speech-to-text
    )

    WITH VOICE SELECTION:
    ---------------------
    from google.adk.agents.run_config import SpeechConfig, VoiceConfig

    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        speech_config=SpeechConfig(
            voice_config=VoiceConfig(
                prebuilt_voice_config={
                    "voice_name": "Aoede"  # Choose voice
                }
            )
        )
    )

    Available voices (may vary):
    - Aoede, Charon, Fenrir, Kore, Puck (English)
    - More for other languages

    WITH MANUAL VAD:
    ----------------
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        realtime_input_config={
            "automatic_activity_detection": {
                "disabled": True
            }
        }
    )

    SAVING AUDIO TO SESSION:
    ------------------------
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        save_live_model_audio_to_session=True,  # Persist audio
    )

    This saves audio to artifacts with file_data references.

    TEXT MODE (NO AUDIO):
    ---------------------
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["TEXT"],  # Text only
    )

    SESSION RESUMPTION:
    -------------------
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        session_resumption=True,  # Handle disconnects
    )

    COMPLETE EXAMPLE:
    -----------------
    from google.genai import types

    run_config = RunConfig(
        # Core streaming
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],

        # Transcription (enabled by default, use None to disable)
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),

        # Voice
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Aoede"
                )
            )
        ),

        # Persistence
        save_live_blob=True,

        # Resilience
        session_resumption=types.SessionResumptionConfig(
            transparent=True
        ),
    )
    """)


# =============================================================================
# Part 7: Demo - Audio Configuration
# =============================================================================

async def audio_config_demo():
    """Demonstrate audio configuration options."""
    print("\n  Demonstrating audio configuration...")

    print("\n  Audio/Video Configuration Options:")
    print("  " + "-"*50)

    # Text mode config
    text_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["TEXT"],
    )
    print("\n  1. Text Mode:")
    print(f"     streaming_mode: BIDI")
    print(f"     response_modalities: ['TEXT']")
    print(f"     Use case: Text chat, no audio")

    # Audio mode config - transcription is enabled by default
    # To configure: types.AudioTranscriptionConfig()
    audio_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        # input_audio_transcription and output_audio_transcription
        # default to types.AudioTranscriptionConfig() which enables transcription
    )
    print("\n  2. Audio Mode with Transcription:")
    print(f"     streaming_mode: BIDI")
    print(f"     response_modalities: ['AUDIO']")
    print(f"     input_audio_transcription: AudioTranscriptionConfig() (default)")
    print(f"     output_audio_transcription: AudioTranscriptionConfig() (default)")
    print(f"     Use case: Voice assistant with captions")

    # Manual VAD config
    manual_vad_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        realtime_input_config={
            "automatic_activity_detection": {
                "disabled": True
            }
        }
    )
    print("\n  3. Manual VAD Mode:")
    print(f"     streaming_mode: BIDI")
    print(f"     response_modalities: ['AUDIO']")
    print(f"     automatic_activity_detection: disabled")
    print(f"     Use case: Push-to-talk, noisy environments")

    print("\n  Audio Input Requirements:")
    print("  " + "-"*50)
    print("    Format: 16-bit PCM")
    print("    Sample rate: 16,000 Hz")
    print("    Channels: Mono")
    print("    Byte order: Little-endian")
    print("    MIME type: audio/pcm;rate=16000")

    print("\n  Audio Output Format:")
    print("  " + "-"*50)
    print("    Format: 16-bit PCM")
    print("    Sample rate: 24,000 Hz")
    print("    Channels: Mono")

    print("\n  Image/Video Requirements:")
    print("  " + "-"*50)
    print("    Formats: JPEG, PNG")
    print("    MIME types: image/jpeg, image/png")
    print("    Video: Send as image frames")
    print("    Recommended FPS: 1-10 for analysis")

    # Demo blob creation
    print("\n  Sample Blob Creation:")
    print("  " + "-"*50)

    # Fake audio
    fake_audio = b'\x00\x00' * 1600  # 50ms at 16kHz
    audio_blob = types.Blob(
        mime_type="audio/pcm;rate=16000",
        data=fake_audio
    )
    print(f"    Audio blob: {len(audio_blob.data)} bytes, {audio_blob.mime_type}")

    # Fake image
    fake_image = b'\xff\xd8\xff' + b'\x00' * 1000  # Fake JPEG
    image_blob = types.Blob(
        mime_type="image/jpeg",
        data=fake_image
    )
    print(f"    Image blob: {len(image_blob.data)} bytes, {image_blob.mime_type}")


async def main():
    print("\n" + "#"*70)
    print("# Lab 6 Exercise 4: Audio & Video Streaming")
    print("#"*70)

    # =========================================================================
    # Part 1: Audio Input
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Audio Input Specifications")
    print("="*60)
    explain_audio_input()

    # =========================================================================
    # Part 2: Audio Output
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Audio Output Specifications")
    print("="*60)
    explain_audio_output()

    # =========================================================================
    # Part 3: VAD
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Voice Activity Detection (VAD)")
    print("="*60)
    explain_vad()

    # =========================================================================
    # Part 4: Transcription
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Audio Transcription")
    print("="*60)
    explain_transcription()

    # =========================================================================
    # Part 5: Video
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Video/Image Streaming")
    print("="*60)
    explain_video_streaming()

    # =========================================================================
    # Part 6: RunConfig
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: RunConfig for Audio/Video")
    print("="*60)
    explain_runconfig()

    # =========================================================================
    # Part 7: Demo
    # =========================================================================
    print("\n" + "="*60)
    print("PART 7: Audio Configuration Demo")
    print("="*60)

    await audio_config_demo()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Audio & Video Streaming")
    print("#"*70)
    print("""
    AUDIO INPUT:
    ------------
    - Format: 16-bit PCM, 16kHz, mono
    - MIME: "audio/pcm;rate=16000"
    - Chunk: 20-100ms recommended

    AUDIO OUTPUT:
    -------------
    - Format: 16-bit PCM, 24kHz, mono
    - Arrives as inline_data in events

    VAD OPTIONS:
    ------------
    - Automatic: Default, handles turn detection
    - Manual: Use activity signals, for push-to-talk

    TRANSCRIPTION:
    --------------
    - input_audio_transcription: User speech-to-text
    - output_audio_transcription: Agent speech-to-text
    - Great for captions and logging

    VIDEO/IMAGE:
    ------------
    - MIME: "image/jpeg" or "image/png"
    - Video = sequence of image frames
    - 1-10 FPS for analysis

    RunConfig KEY OPTIONS:
    ----------------------
    - streaming_mode=StreamingMode.BIDI
    - response_modalities=["AUDIO"] or ["TEXT"]
    - input/output_audio_transcription=True
    - speech_config for voice selection
    - save_live_model_audio_to_session=True
    """)


if __name__ == "__main__":
    asyncio.run(main())
