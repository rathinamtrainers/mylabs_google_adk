"""
Lab 7 - Exercise 1: Artifacts Basics
=====================================

This exercise introduces ADK Artifacts fundamentals:
1. What are Artifacts?
2. Why use Artifacts vs State?
3. Artifact representation (types.Part)
4. Core concepts overview
5. Simple artifact demo

Run: uv run python 01_artifacts_basics.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types


# =============================================================================
# Part 1: What are Artifacts?
# =============================================================================

def explain_artifacts():
    """Explain what artifacts are in ADK."""
    print("""
    WHAT ARE ARTIFACTS?
    ===================

    Artifacts are a mechanism for managing named, versioned binary data
    in ADK. They handle files, images, audio, and other non-text content.

    DEFINITION:
    -----------
    An Artifact is binary data identified by:
    - A unique filename (within a scope)
    - A version number (auto-incremented)
    - A MIME type (describes the content)

    ARTIFACT vs STATE:
    ------------------
    ┌─────────────────────────────────────────────────────────────┐
    │  Aspect           │  State              │  Artifacts        │
    ├─────────────────────────────────────────────────────────────┤
    │  Data type        │  JSON-serializable  │  Binary data      │
    │  Size             │  Small values       │  Files/large data │
    │  Versioning       │  No                 │  Yes (automatic)  │
    │  Examples         │  user_name, count   │  PDF, images      │
    │  Access           │  state["key"]       │  save/load methods│
    └─────────────────────────────────────────────────────────────┘

    REPRESENTATION:
    ---------------
    Artifacts use google.genai.types.Part with inline_data:

    artifact = types.Part(
        inline_data=types.Blob(
            mime_type="image/png",
            data=image_bytes
        )
    )

    # Or use convenience method:
    artifact = types.Part.from_bytes(
        data=image_bytes,
        mime_type="image/png"
    )

    KEY PROPERTIES:
    ---------------
    - artifact.inline_data.data      # The raw bytes
    - artifact.inline_data.mime_type # Content type (e.g., "image/png")
    """)


# =============================================================================
# Part 2: Why Use Artifacts?
# =============================================================================

def explain_why_artifacts():
    """Explain when and why to use artifacts."""
    print("""
    WHY USE ARTIFACTS?
    ==================

    1. HANDLING NON-TEXTUAL DATA
    ----------------------------
    Store and retrieve:
    - Images (PNG, JPEG, GIF)
    - Documents (PDF, DOCX)
    - Audio files (MP3, WAV)
    - Video files (MP4)
    - Spreadsheets (XLSX, CSV)
    - Any binary format

    2. PERSISTING LARGE DATA
    ------------------------
    Session state is NOT optimized for large data.
    Artifacts provide dedicated storage for big files
    without cluttering session state.

    3. USER FILE MANAGEMENT
    -----------------------
    - Users upload files (saved as artifacts)
    - Agent generates files (saved as artifacts)
    - Users download generated outputs

    4. VERSIONING
    -------------
    Every save creates a new version:
    - Version 0: First save
    - Version 1: Second save
    - Version N: N+1th save

    Load latest or specific version:
    - load_artifact("report.pdf")        # Latest
    - load_artifact("report.pdf", 0)     # Version 0

    5. CROSS-SESSION DATA
    ---------------------
    Use "user:" prefix for user-scoped artifacts:
    - "settings.json"      → Session-specific
    - "user:settings.json" → Accessible in all sessions

    USE CASES:
    ----------
    - Generated reports (PDF analysis, CSV export)
    - User uploads (images for analysis)
    - Intermediate binary results (audio synthesis)
    - Persistent user data (profile pictures)
    - Cached generated content (rendered charts)
    """)


# =============================================================================
# Part 3: Artifact Representation
# =============================================================================

def explain_representation():
    """Explain how artifacts are represented."""
    print("""
    ARTIFACT REPRESENTATION
    =======================

    Artifacts use google.genai.types.Part - the same structure
    used for LLM message parts!

    STRUCTURE:
    ----------
    types.Part
    └── inline_data: types.Blob
        ├── data: bytes        # Raw binary content
        └── mime_type: str     # Content type

    CREATING ARTIFACTS:
    -------------------
    Method 1: Constructor
    ```python
    artifact = types.Part(
        inline_data=types.Blob(
            mime_type="application/pdf",
            data=pdf_bytes
        )
    )
    ```

    Method 2: Convenience method (recommended)
    ```python
    artifact = types.Part.from_bytes(
        data=pdf_bytes,
        mime_type="application/pdf"
    )
    ```

    COMMON MIME TYPES:
    ------------------
    Images:
    - image/png
    - image/jpeg
    - image/gif
    - image/webp

    Documents:
    - application/pdf
    - text/plain
    - text/csv
    - application/json

    Audio:
    - audio/mpeg (MP3)
    - audio/wav
    - audio/ogg

    Video:
    - video/mp4
    - video/webm

    Archives:
    - application/zip
    - application/gzip

    ACCESSING DATA:
    ---------------
    # Get the bytes
    raw_bytes = artifact.inline_data.data

    # Get the MIME type
    content_type = artifact.inline_data.mime_type

    # Check data size
    size = len(artifact.inline_data.data)
    """)


# =============================================================================
# Part 4: Core Concepts Overview
# =============================================================================

def explain_core_concepts():
    """Explain core artifact concepts."""
    print("""
    CORE CONCEPTS
    =============

    1. ARTIFACT SERVICE
    -------------------
    Manages storage and retrieval of artifacts.

    Two implementations:
    - InMemoryArtifactService: For testing (non-persistent)
    - GcsArtifactService: For production (Google Cloud Storage)

    Setup:
    ```python
    from google.adk.artifacts import InMemoryArtifactService

    artifact_service = InMemoryArtifactService()

    runner = Runner(
        agent=agent,
        app_name="my_app",
        session_service=session_service,
        artifact_service=artifact_service  # Required!
    )
    ```

    2. FILENAME
    -----------
    Unique identifier within a scope.
    - Use descriptive names: "monthly_report.pdf"
    - Include extensions: ".png", ".pdf", ".json"
    - MIME type determines behavior, not extension

    3. VERSIONING
    -------------
    Automatic version numbering:
    - save_artifact() returns version number
    - Versions start at 0
    - Each save increments version

    4. NAMESPACING
    --------------
    Two scopes for artifacts:

    Session scope (default):
    - Filename: "report.pdf"
    - Tied to: app_name + user_id + session_id
    - Only accessible in that specific session

    User scope:
    - Filename: "user:profile.png"
    - Tied to: app_name + user_id
    - Accessible across ALL user sessions

    5. CONTEXT METHODS
    ------------------
    Access via CallbackContext or ToolContext:

    - save_artifact(filename, artifact) → version
    - load_artifact(filename, version=None) → Part or None
    - list_artifacts() → list of filenames
    """)


# =============================================================================
# Part 5: Simple Artifact Demo
# =============================================================================

async def artifact_basics_demo():
    """Demonstrate basic artifact operations."""
    print("\n  Demonstrating artifact basics...")
    print("  " + "-"*50)

    # Create artifact service
    artifact_service = InMemoryArtifactService()
    session_service = InMemorySessionService()

    # Create a simple agent
    agent = LlmAgent(
        name="ArtifactAgent",
        model="gemini-2.0-flash",
        instruction="You are a helpful assistant.",
    )

    # Create runner with artifact service
    runner = Runner(
        agent=agent,
        app_name="artifact_demo",
        session_service=session_service,
        artifact_service=artifact_service,  # This enables artifacts!
    )

    # Create session
    session = await session_service.create_session(
        app_name="artifact_demo",
        user_id="user1",
        session_id="session1",
        state={}
    )

    print("\n  1. Creating artifacts from different data types:")
    print("  " + "-"*50)

    # Create text artifact
    text_content = "Hello, this is a text file content!"
    text_artifact = types.Part.from_bytes(
        data=text_content.encode('utf-8'),
        mime_type="text/plain"
    )
    print(f"    Text artifact: {len(text_artifact.inline_data.data)} bytes")
    print(f"    MIME type: {text_artifact.inline_data.mime_type}")

    # Create JSON artifact
    import json
    json_data = {"name": "Test", "count": 42, "active": True}
    json_artifact = types.Part.from_bytes(
        data=json.dumps(json_data).encode('utf-8'),
        mime_type="application/json"
    )
    print(f"\n    JSON artifact: {len(json_artifact.inline_data.data)} bytes")
    print(f"    MIME type: {json_artifact.inline_data.mime_type}")

    # Create binary artifact (simulated image header)
    # PNG header bytes
    png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
    image_artifact = types.Part.from_bytes(
        data=png_header,
        mime_type="image/png"
    )
    print(f"\n    Image artifact: {len(image_artifact.inline_data.data)} bytes")
    print(f"    MIME type: {image_artifact.inline_data.mime_type}")

    print("\n  2. Saving artifacts directly to service:")
    print("  " + "-"*50)

    # Save directly to artifact service
    version = await artifact_service.save_artifact(
        app_name="artifact_demo",
        user_id="user1",
        session_id="session1",
        filename="notes.txt",
        artifact=text_artifact
    )
    print(f"    Saved 'notes.txt' as version {version}")

    # Save another version
    updated_text = "Updated content for the text file!"
    updated_artifact = types.Part.from_bytes(
        data=updated_text.encode('utf-8'),
        mime_type="text/plain"
    )
    version2 = await artifact_service.save_artifact(
        app_name="artifact_demo",
        user_id="user1",
        session_id="session1",
        filename="notes.txt",
        artifact=updated_artifact
    )
    print(f"    Saved 'notes.txt' as version {version2}")

    # Save JSON
    json_version = await artifact_service.save_artifact(
        app_name="artifact_demo",
        user_id="user1",
        session_id="session1",
        filename="config.json",
        artifact=json_artifact
    )
    print(f"    Saved 'config.json' as version {json_version}")

    print("\n  3. Loading artifacts:")
    print("  " + "-"*50)

    # Load latest version
    loaded = await artifact_service.load_artifact(
        app_name="artifact_demo",
        user_id="user1",
        session_id="session1",
        filename="notes.txt"
    )
    if loaded:
        content = loaded.inline_data.data.decode('utf-8')
        print(f"    Latest 'notes.txt': {content}")

    # Load specific version (version 0)
    loaded_v0 = await artifact_service.load_artifact(
        app_name="artifact_demo",
        user_id="user1",
        session_id="session1",
        filename="notes.txt",
        version=0
    )
    if loaded_v0:
        content_v0 = loaded_v0.inline_data.data.decode('utf-8')
        print(f"    Version 0 'notes.txt': {content_v0}")

    print("\n  4. Listing artifacts:")
    print("  " + "-"*50)

    # List all artifacts
    artifacts_list = await artifact_service.list_artifact_keys(
        app_name="artifact_demo",
        user_id="user1",
        session_id="session1"
    )
    print(f"    Available artifacts: {artifacts_list}")

    # List versions
    versions = await artifact_service.list_versions(
        app_name="artifact_demo",
        user_id="user1",
        session_id="session1",
        filename="notes.txt"
    )
    print(f"    Versions of 'notes.txt': {versions}")

    print("\n  5. Deleting artifacts:")
    print("  " + "-"*50)

    # Delete an artifact
    await artifact_service.delete_artifact(
        app_name="artifact_demo",
        user_id="user1",
        session_id="session1",
        filename="config.json"
    )
    print("    Deleted 'config.json'")

    # Verify deletion
    remaining = await artifact_service.list_artifact_keys(
        app_name="artifact_demo",
        user_id="user1",
        session_id="session1"
    )
    print(f"    Remaining artifacts: {remaining}")

    print("\n  Demo complete!")


async def main():
    print("\n" + "#"*70)
    print("# Lab 7 Exercise 1: Artifacts Basics")
    print("#"*70)

    # =========================================================================
    # Part 1: What are Artifacts
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: What are Artifacts?")
    print("="*60)
    explain_artifacts()

    # =========================================================================
    # Part 2: Why Use Artifacts
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Why Use Artifacts?")
    print("="*60)
    explain_why_artifacts()

    # =========================================================================
    # Part 3: Representation
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Artifact Representation")
    print("="*60)
    explain_representation()

    # =========================================================================
    # Part 4: Core Concepts
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Core Concepts")
    print("="*60)
    explain_core_concepts()

    # =========================================================================
    # Part 5: Demo
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Artifact Basics Demo")
    print("="*60)

    await artifact_basics_demo()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Artifacts Basics")
    print("#"*70)
    print("""
    ARTIFACTS OVERVIEW:
    -------------------
    Named, versioned binary data management in ADK.
    Perfect for files, images, audio, and large data.

    REPRESENTATION:
    ---------------
    types.Part with inline_data (Blob):
    - data: Raw bytes
    - mime_type: Content type string

    ARTIFACT SERVICE:
    -----------------
    - InMemoryArtifactService: Testing (non-persistent)
    - GcsArtifactService: Production (Google Cloud Storage)

    KEY OPERATIONS:
    ---------------
    - save_artifact(filename, artifact) → version
    - load_artifact(filename, version) → Part or None
    - list_artifact_keys() → list of filenames
    - list_versions(filename) → list of versions
    - delete_artifact(filename) → removes artifact

    VERSIONING:
    -----------
    - Automatic (starts at 0, increments on save)
    - Load latest or specific version

    NAMESPACING:
    ------------
    - Session scope: "report.pdf"
    - User scope: "user:profile.png"

    WHEN TO USE:
    ------------
    - Binary data (images, PDFs, audio)
    - Large files (vs small state values)
    - Versioned content
    - User uploads/downloads
    """)


if __name__ == "__main__":
    asyncio.run(main())
