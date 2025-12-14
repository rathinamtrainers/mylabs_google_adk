# Lab 6: Streaming (Bidi-streaming / Live)

This lab covers bidirectional streaming in Google ADK:
1. Streaming basics and architecture
2. LiveRequestQueue for sending messages
3. Event handling with run_live()
4. Audio and video streaming concepts
5. Streaming tools for real-time updates

## Prerequisites

```bash
cd /home/agenticai/research_gadk/mylabs/lab6_streaming
uv init
uv add google-adk
```

## Exercises

| Exercise | Topic | Description |
|----------|-------|-------------|
| 01 | Streaming Basics | Bidi-streaming concepts, architecture, lifecycle |
| 02 | LiveRequestQueue | Sending text, audio, activity signals |
| 03 | Streaming Events | Event types, handling text/audio events |
| 04 | Audio & Video | Audio specifications, transcription, VAD |
| 05 | Streaming Tools | Tools that stream intermediate results |

## Running Exercises

```bash
# Set your API key
export GOOGLE_API_KEY="your-api-key"

# Run individual exercises
uv run python 01_streaming_basics.py
uv run python 02_live_request_queue.py
uv run python 03_streaming_events.py
uv run python 04_audio_video_streaming.py
uv run python 05_streaming_tools.py
```

## Key Concepts

### Bidi-streaming
- Real-time, two-way communication
- User can interrupt agent mid-response
- Supports text, audio, and video input/output
- Based on Gemini Live API / Vertex AI Live API

### Core Components
- `LiveRequestQueue` - Send messages upstream to agent
- `run_live()` - Async generator yielding events downstream
- `RunConfig` - Configure streaming behavior
- `Event` - Unified container for all responses

### Event Types
- Text events with `partial`, `turn_complete`, `interrupted` flags
- Audio events with `inline_data` (raw bytes)
- Transcription events for speech-to-text
- Tool call events for function execution
- Metadata events for token usage

### Audio Specifications
- Input: 16-bit PCM at 16kHz (mono)
- Output: 16-bit PCM at 24kHz (native audio models)
- Voice Activity Detection (VAD) for turn detection
