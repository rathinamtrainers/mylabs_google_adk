"""
Lab 7 - Exercise 3: Artifact Operations via Context
====================================================

This exercise covers artifact operations through context:
1. Accessing artifacts via CallbackContext
2. Accessing artifacts via ToolContext
3. Save, load, list operations
4. Error handling patterns
5. Working demo with callbacks and tools

Run: uv run python 03_artifact_operations.py
"""

import asyncio
import json
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.genai import types


# =============================================================================
# Part 1: CallbackContext Artifact Access
# =============================================================================

def explain_callback_context():
    """Explain artifact access via CallbackContext."""
    print("""
    ARTIFACTS VIA CALLBACK CONTEXT
    ==============================

    CallbackContext is passed to agent callbacks and provides
    artifact operations within the agent's execution context.

    AVAILABLE IN:
    -------------
    - before_agent_callback(callback_context)
    - after_agent_callback(callback_context)
    - before_model_callback(callback_context, llm_request)
    - after_model_callback(callback_context, llm_response)

    ARTIFACT METHODS:
    -----------------
    1. save_artifact(filename, artifact) -> int
       Saves artifact and returns version number.

    2. load_artifact(filename, version=None) -> Part | None
       Loads artifact (latest if version not specified).

    3. list_artifacts() -> list[str]
       Lists all artifact filenames in current scope.

    EXAMPLE: Before Agent Callback
    ------------------------------
    async def before_agent(callback_context: CallbackContext):
        '''Load user preferences before agent runs.'''

        # Load existing preferences
        prefs = await callback_context.load_artifact("user:preferences.json")

        if prefs:
            # Parse and store in state
            data = json.loads(prefs.inline_data.data.decode())
            callback_context.state["preferences"] = data
            print(f"Loaded preferences: {data}")
        else:
            # Use defaults
            callback_context.state["preferences"] = {"theme": "light"}

    EXAMPLE: After Agent Callback
    -----------------------------
    async def after_agent(callback_context: CallbackContext):
        '''Save conversation summary after agent completes.'''

        # Create summary artifact
        summary = callback_context.state.get("summary", "No summary")
        summary_artifact = types.Part.from_bytes(
            data=summary.encode(),
            mime_type="text/plain"
        )

        # Save it
        version = await callback_context.save_artifact(
            filename="conversation_summary.txt",
            artifact=summary_artifact
        )
        print(f"Saved summary as version {version}")

    CONTEXT SCOPE:
    --------------
    When using callback_context methods:
    - app_name: From Runner configuration
    - user_id: From current invocation
    - session_id: From current session

    These are automatically determined - you just provide filename!
    """)


# =============================================================================
# Part 2: ToolContext Artifact Access
# =============================================================================

def explain_tool_context():
    """Explain artifact access via ToolContext."""
    print("""
    ARTIFACTS VIA TOOL CONTEXT
    ==========================

    ToolContext is passed to tool functions and provides
    artifact operations within tool execution.

    TOOL CONTEXT INHERITANCE:
    -------------------------
    ToolContext inherits from CallbackContext, so all
    callback_context methods are available in tool_context!

    SAME METHODS AVAILABLE:
    -----------------------
    - save_artifact(filename, artifact) -> int
    - load_artifact(filename, version=None) -> Part | None
    - list_artifacts() -> list[str]

    EXAMPLE: File Upload Tool
    -------------------------
    async def upload_file(
        filename: str,
        content: str,
        tool_context: ToolContext
    ) -> str:
        '''Upload a file as an artifact.'''

        # Create artifact from content
        artifact = types.Part.from_bytes(
            data=content.encode('utf-8'),
            mime_type="text/plain"
        )

        # Save it
        version = await tool_context.save_artifact(
            filename=filename,
            artifact=artifact
        )

        return f"Uploaded {filename} as version {version}"

    EXAMPLE: File Download Tool
    ---------------------------
    async def download_file(
        filename: str,
        tool_context: ToolContext
    ) -> str:
        '''Download a file artifact.'''

        # Load the artifact
        artifact = await tool_context.load_artifact(filename)

        if artifact is None:
            return f"File '{filename}' not found"

        # Return content
        content = artifact.inline_data.data.decode('utf-8')
        return f"File content:\\n{content}"

    EXAMPLE: List Files Tool
    ------------------------
    async def list_files(tool_context: ToolContext) -> str:
        '''List all available files.'''

        files = await tool_context.list_artifacts()

        if not files:
            return "No files available"

        return "Available files:\\n" + "\\n".join(f"- {f}" for f in files)

    TOOL REGISTRATION:
    ------------------
    agent = LlmAgent(
        name="FileAgent",
        model="gemini-2.0-flash",
        tools=[upload_file, download_file, list_files],
        instruction="Help users manage their files."
    )

    BEST PRACTICES:
    ---------------
    1. Always check load_artifact return for None
    2. Use appropriate MIME types
    3. Handle encoding/decoding properly
    4. Provide clear error messages to user
    """)


# =============================================================================
# Part 3: Save, Load, List Operations
# =============================================================================

def explain_operations():
    """Explain the core artifact operations in detail."""
    print("""
    ARTIFACT OPERATIONS IN DETAIL
    =============================

    1. SAVE ARTIFACT
    ----------------
    version = await context.save_artifact(
        filename="report.pdf",
        artifact=pdf_part
    )

    Parameters:
    - filename: String identifier for the artifact
    - artifact: types.Part with inline_data

    Returns:
    - int: Version number (0 for first save, increments)

    Creates artifact or adds new version if exists.
    The returned version is tracked in event.actions.artifact_delta

    2. LOAD ARTIFACT
    ----------------
    # Load latest version
    artifact = await context.load_artifact("report.pdf")

    # Load specific version
    artifact = await context.load_artifact("report.pdf", version=0)

    Parameters:
    - filename: String identifier
    - version: Optional int (None = latest)

    Returns:
    - types.Part: If artifact exists
    - None: If artifact/version not found

    IMPORTANT: Always check for None before using!

    3. LIST ARTIFACTS
    -----------------
    filenames = await context.list_artifacts()

    Parameters: None

    Returns:
    - list[str]: Filenames in current scope

    Returns empty list if no artifacts exist.

    ARTIFACT DELTA:
    ---------------
    After save_artifact, the event includes:

    event.actions.artifact_delta = {
        "report.pdf": 0,    # filename: version
        "image.png": 2
    }

    This tells the application which artifacts were created/updated.

    COMPLETE WORKFLOW:
    ------------------
    async def process_document(doc: str, ctx: ToolContext) -> str:
        # 1. List existing artifacts
        existing = await ctx.list_artifacts()
        print(f"Existing files: {existing}")

        # 2. Save new artifact
        artifact = types.Part.from_bytes(
            data=doc.encode(),
            mime_type="text/plain"
        )
        version = await ctx.save_artifact("document.txt", artifact)
        print(f"Saved as version {version}")

        # 3. Load it back (verify)
        loaded = await ctx.load_artifact("document.txt")
        if loaded:
            content = loaded.inline_data.data.decode()
            return f"Saved and verified: {len(content)} chars"

        return "Error: Could not verify save"
    """)


# =============================================================================
# Part 4: Error Handling Patterns
# =============================================================================

def explain_error_handling():
    """Explain error handling for artifact operations."""
    print("""
    ERROR HANDLING PATTERNS
    =======================

    1. NO ARTIFACT SERVICE CONFIGURED
    ----------------------------------
    If Runner has no artifact_service, operations raise ValueError.

    async def my_tool(tool_context: ToolContext) -> str:
        try:
            files = await tool_context.list_artifacts()
            return f"Found {len(files)} files"
        except ValueError as e:
            # artifact_service is None
            return "Error: Artifact service not configured"

    2. ARTIFACT NOT FOUND
    ---------------------
    load_artifact returns None if not found - NOT an exception!

    async def get_file(filename: str, ctx: ToolContext) -> str:
        artifact = await ctx.load_artifact(filename)

        if artifact is None:
            return f"File '{filename}' not found"

        return artifact.inline_data.data.decode()

    3. VERSION NOT FOUND
    --------------------
    Specific version may not exist.

    async def get_version(
        filename: str,
        version: int,
        ctx: ToolContext
    ) -> str:
        artifact = await ctx.load_artifact(filename, version=version)

        if artifact is None:
            return f"Version {version} of '{filename}' not found"

        return artifact.inline_data.data.decode()

    4. DECODING ERRORS
    ------------------
    Binary data may not be valid UTF-8.

    async def read_text_file(filename: str, ctx: ToolContext) -> str:
        artifact = await ctx.load_artifact(filename)

        if artifact is None:
            return "File not found"

        try:
            return artifact.inline_data.data.decode('utf-8')
        except UnicodeDecodeError:
            return "Error: File is not valid UTF-8 text"

    5. GCS ERRORS (Production)
    --------------------------
    GcsArtifactService may raise cloud storage exceptions.

    from google.api_core.exceptions import Forbidden, NotFound

    async def save_to_gcs(data: bytes, ctx: ToolContext) -> str:
        try:
            artifact = types.Part.from_bytes(data, "application/octet-stream")
            version = await ctx.save_artifact("data.bin", artifact)
            return f"Saved as version {version}"

        except Forbidden:
            return "Error: Permission denied to GCS bucket"
        except NotFound:
            return "Error: GCS bucket not found"
        except Exception as e:
            return f"Error saving artifact: {e}"

    DEFENSIVE PATTERN:
    ------------------
    async def safe_artifact_operation(ctx: ToolContext) -> str:
        # Check if artifacts are available
        try:
            await ctx.list_artifacts()
        except ValueError:
            return "Artifacts not available"

        # Proceed with operations
        artifact = await ctx.load_artifact("config.json")
        if artifact is None:
            return "Config not found"

        try:
            data = json.loads(artifact.inline_data.data.decode())
            return f"Config loaded: {data}"
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            return f"Invalid config format: {e}"
    """)


# =============================================================================
# Part 5: Working Demo
# =============================================================================

# Tool: Save a note
async def save_note(
    title: str,
    content: str,
    tool_context: ToolContext
) -> str:
    """Save a note as an artifact.

    Args:
        title: Title of the note (used as filename)
        content: The note content

    Returns:
        Confirmation message with version
    """
    # Create artifact
    artifact = types.Part.from_bytes(
        data=content.encode('utf-8'),
        mime_type="text/plain"
    )

    # Sanitize filename
    filename = f"{title.lower().replace(' ', '_')}.txt"

    # Save artifact
    version = await tool_context.save_artifact(
        filename=filename,
        artifact=artifact
    )

    return f"Saved note '{title}' as {filename} (version {version})"


# Tool: Read a note
async def read_note(
    filename: str,
    tool_context: ToolContext
) -> str:
    """Read a note artifact.

    Args:
        filename: The filename to read

    Returns:
        Note content or error message
    """
    # Load artifact
    artifact = await tool_context.load_artifact(filename)

    if artifact is None:
        return f"Note '{filename}' not found"

    try:
        content = artifact.inline_data.data.decode('utf-8')
        return f"Content of '{filename}':\n{content}"
    except UnicodeDecodeError:
        return f"Error: '{filename}' is not a valid text file"


# Tool: List all notes
async def list_notes(tool_context: ToolContext) -> str:
    """List all saved notes.

    Returns:
        List of available notes
    """
    files = await tool_context.list_artifacts()

    if not files:
        return "No notes saved yet"

    txt_files = [f for f in files if f.endswith('.txt')]

    if not txt_files:
        return "No text notes found"

    return "Available notes:\n" + "\n".join(f"- {f}" for f in txt_files)


# Tool: Save JSON data
async def save_data(
    name: str,
    data: dict,
    tool_context: ToolContext
) -> str:
    """Save JSON data as an artifact.

    Args:
        name: Name for the data (used as filename)
        data: Dictionary to save

    Returns:
        Confirmation message
    """
    # Create JSON artifact
    json_bytes = json.dumps(data, indent=2).encode('utf-8')
    artifact = types.Part.from_bytes(
        data=json_bytes,
        mime_type="application/json"
    )

    filename = f"{name}.json"
    version = await tool_context.save_artifact(filename, artifact)

    return f"Saved data '{name}' as {filename} (version {version})"


# Tool: Load JSON data
async def load_data(
    name: str,
    tool_context: ToolContext
) -> str:
    """Load JSON data artifact.

    Args:
        name: Name of the data to load

    Returns:
        JSON content or error
    """
    filename = f"{name}.json"
    artifact = await tool_context.load_artifact(filename)

    if artifact is None:
        return f"Data '{name}' not found"

    try:
        json_str = artifact.inline_data.data.decode('utf-8')
        data = json.loads(json_str)
        return f"Data '{name}':\n{json.dumps(data, indent=2)}"
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return f"Error loading '{name}': {e}"


async def context_operations_demo():
    """Demonstrate artifact operations via context."""
    print("\n  Demonstrating artifact operations via context...")
    print("  " + "-"*50)

    # Create services
    artifact_service = InMemoryArtifactService()
    session_service = InMemorySessionService()

    # Create agent with tools
    agent = LlmAgent(
        name="NotesAgent",
        model="gemini-2.0-flash",
        tools=[save_note, read_note, list_notes, save_data, load_data],
        instruction="""You are a note-taking assistant.
        Help users save and retrieve their notes and data.
        Use the available tools to manage artifacts.""",
    )

    # Create runner with artifact service
    runner = Runner(
        agent=agent,
        app_name="notes_app",
        session_service=session_service,
        artifact_service=artifact_service,
    )

    # Create session
    session = await session_service.create_session(
        app_name="notes_app",
        user_id="user1",
        session_id="session1",
        state={}
    )

    print("\n  Testing tools directly...")
    print("  " + "-"*50)

    # Create a mock tool context for direct testing
    # We'll use the artifact service directly for demo

    # 1. Save some notes
    print("\n  1. Saving notes directly via service:")

    note1 = types.Part.from_bytes(
        data=b"This is my first note about Python.",
        mime_type="text/plain"
    )
    v1 = await artifact_service.save_artifact(
        app_name="notes_app",
        user_id="user1",
        session_id="session1",
        filename="python_notes.txt",
        artifact=note1
    )
    print(f"    Saved 'python_notes.txt' as version {v1}")

    note2 = types.Part.from_bytes(
        data=b"Meeting notes: Discussed project timeline.",
        mime_type="text/plain"
    )
    v2 = await artifact_service.save_artifact(
        app_name="notes_app",
        user_id="user1",
        session_id="session1",
        filename="meeting.txt",
        artifact=note2
    )
    print(f"    Saved 'meeting.txt' as version {v2}")

    # 2. Save JSON data
    print("\n  2. Saving JSON data:")

    config_data = {"theme": "dark", "language": "en", "notifications": True}
    config = types.Part.from_bytes(
        data=json.dumps(config_data).encode(),
        mime_type="application/json"
    )
    v3 = await artifact_service.save_artifact(
        app_name="notes_app",
        user_id="user1",
        session_id="session1",
        filename="settings.json",
        artifact=config
    )
    print(f"    Saved 'settings.json' as version {v3}")

    # 3. List artifacts
    print("\n  3. Listing all artifacts:")

    files = await artifact_service.list_artifact_keys(
        app_name="notes_app",
        user_id="user1",
        session_id="session1"
    )
    for f in files:
        print(f"    - {f}")

    # 4. Load and display
    print("\n  4. Loading artifacts:")

    for filename in files:
        artifact = await artifact_service.load_artifact(
            app_name="notes_app",
            user_id="user1",
            session_id="session1",
            filename=filename
        )
        if artifact:
            mime = artifact.inline_data.mime_type
            size = len(artifact.inline_data.data)
            print(f"    {filename}: {mime}, {size} bytes")

    # 5. Update a note (new version)
    print("\n  5. Updating a note (creates new version):")

    updated_note = types.Part.from_bytes(
        data=b"This is my first note about Python.\nUpdated with more info!",
        mime_type="text/plain"
    )
    v_new = await artifact_service.save_artifact(
        app_name="notes_app",
        user_id="user1",
        session_id="session1",
        filename="python_notes.txt",
        artifact=updated_note
    )
    print(f"    Updated 'python_notes.txt' to version {v_new}")

    # Show versions
    versions = await artifact_service.list_versions(
        app_name="notes_app",
        user_id="user1",
        session_id="session1",
        filename="python_notes.txt"
    )
    print(f"    Available versions: {versions}")

    # 6. Test agent interaction
    print("\n  6. Testing agent with message:")

    user_message = types.Content(
        role="user",
        parts=[types.Part(text="What notes do I have saved?")]
    )

    print("    User: What notes do I have saved?")
    print("    Agent: ", end="")

    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    print(part.text[:200] + "..." if len(part.text) > 200 else part.text)

    print("\n  Demo complete!")


async def main():
    print("\n" + "#"*70)
    print("# Lab 7 Exercise 3: Artifact Operations via Context")
    print("#"*70)

    # =========================================================================
    # Part 1: CallbackContext
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Artifacts via CallbackContext")
    print("="*60)
    explain_callback_context()

    # =========================================================================
    # Part 2: ToolContext
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Artifacts via ToolContext")
    print("="*60)
    explain_tool_context()

    # =========================================================================
    # Part 3: Operations Detail
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Save, Load, List Operations")
    print("="*60)
    explain_operations()

    # =========================================================================
    # Part 4: Error Handling
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Error Handling Patterns")
    print("="*60)
    explain_error_handling()

    # =========================================================================
    # Part 5: Demo
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Working Demo")
    print("="*60)

    await context_operations_demo()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Artifact Operations via Context")
    print("#"*70)
    print("""
    CONTEXT METHODS:
    ----------------
    Both CallbackContext and ToolContext provide:
    - save_artifact(filename, artifact) → int
    - load_artifact(filename, version=None) → Part | None
    - list_artifacts() → list[str]

    CALLBACK CONTEXT USAGE:
    -----------------------
    Available in:
    - before_agent_callback
    - after_agent_callback
    - before_model_callback
    - after_model_callback

    TOOL CONTEXT USAGE:
    -------------------
    async def my_tool(tool_context: ToolContext) -> str:
        # Save
        version = await tool_context.save_artifact(name, part)

        # Load
        artifact = await tool_context.load_artifact(name)

        # List
        files = await tool_context.list_artifacts()

    ERROR HANDLING:
    ---------------
    - ValueError: No artifact service configured
    - None return: Artifact/version not found
    - UnicodeDecodeError: Binary data not valid text
    - GCS exceptions: Permission, bucket issues

    BEST PRACTICES:
    ---------------
    1. Always check load_artifact() for None
    2. Use try/except for decoding
    3. Provide clear error messages
    4. Use appropriate MIME types
    5. Sanitize filenames
    """)


if __name__ == "__main__":
    asyncio.run(main())
