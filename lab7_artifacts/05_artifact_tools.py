"""
Lab 7 - Exercise 5: Artifact Tools
===================================

This exercise covers building tools that work with artifacts:
1. File management tools
2. Document processing tools
3. Image handling tools
4. Artifact best practices
5. Complete file manager demo

Run: uv run python 05_artifact_tools.py
"""

import asyncio
import json
import base64
from datetime import datetime
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.tools.tool_context import ToolContext
from google.genai import types


# =============================================================================
# Part 1: File Management Tools
# =============================================================================

def explain_file_management_tools():
    """Explain file management tools with artifacts."""
    print("""
    FILE MANAGEMENT TOOLS
    =====================

    Tools that help users manage files as artifacts.

    COMMON FILE OPERATIONS:
    -----------------------
    1. Upload file (save artifact)
    2. Download file (load artifact)
    3. List files (list artifacts)
    4. Delete file (via service)
    5. Get file info (metadata)

    UPLOAD TOOL EXAMPLE:
    --------------------
    async def upload_file(
        filename: str,
        content: str,
        content_type: str,
        tool_context: ToolContext
    ) -> str:
        '''Upload a file.

        Args:
            filename: Name for the file
            content: Base64 encoded content (for binary) or plain text
            content_type: MIME type (e.g., "text/plain", "image/png")
        '''
        # Decode if base64 binary
        if content_type.startswith("image/") or content_type == "application/pdf":
            data = base64.b64decode(content)
        else:
            data = content.encode('utf-8')

        artifact = types.Part.from_bytes(data=data, mime_type=content_type)
        version = await tool_context.save_artifact(filename, artifact)

        return f"Uploaded '{filename}' (version {version})"

    DOWNLOAD TOOL EXAMPLE:
    ----------------------
    async def download_file(
        filename: str,
        tool_context: ToolContext
    ) -> str:
        '''Download a file.

        Args:
            filename: Name of file to download
        '''
        artifact = await tool_context.load_artifact(filename)

        if artifact is None:
            return f"File '{filename}' not found"

        mime = artifact.inline_data.mime_type
        data = artifact.inline_data.data

        # Return as base64 for binary, text otherwise
        if mime.startswith("text/"):
            return f"Content ({mime}):\\n{data.decode('utf-8')}"
        else:
            b64 = base64.b64encode(data).decode('ascii')
            return f"File ({mime}): [base64]{b64[:100]}..."

    LIST FILES TOOL:
    ----------------
    async def list_files(tool_context: ToolContext) -> str:
        '''List all available files.'''
        files = await tool_context.list_artifacts()

        if not files:
            return "No files found"

        # Categorize by scope
        session_files = [f for f in files if not f.startswith("user:")]
        user_files = [f for f in files if f.startswith("user:")]

        result = []
        if session_files:
            result.append("Session files:")
            result.extend(f"  - {f}" for f in session_files)
        if user_files:
            result.append("User files:")
            result.extend(f"  - {f}" for f in user_files)

        return "\\n".join(result) if result else "No files found"
    """)


# =============================================================================
# Part 2: Document Processing Tools
# =============================================================================

def explain_document_tools():
    """Explain document processing tools with artifacts."""
    print("""
    DOCUMENT PROCESSING TOOLS
    =========================

    Tools for working with text documents and data files.

    TEXT DOCUMENT TOOL:
    -------------------
    async def create_document(
        title: str,
        content: str,
        tool_context: ToolContext
    ) -> str:
        '''Create a text document.'''
        filename = f"{title.lower().replace(' ', '_')}.txt"
        artifact = types.Part.from_bytes(
            data=content.encode('utf-8'),
            mime_type="text/plain"
        )
        version = await tool_context.save_artifact(filename, artifact)
        return f"Created '{filename}' (version {version})"

    JSON DATA TOOL:
    ---------------
    async def save_json_data(
        name: str,
        data: dict,
        tool_context: ToolContext
    ) -> str:
        '''Save JSON data.'''
        filename = f"{name}.json"
        json_bytes = json.dumps(data, indent=2).encode('utf-8')
        artifact = types.Part.from_bytes(
            data=json_bytes,
            mime_type="application/json"
        )
        version = await tool_context.save_artifact(filename, artifact)
        return f"Saved JSON '{filename}' (version {version})"

    async def load_json_data(
        name: str,
        tool_context: ToolContext
    ) -> dict | None:
        '''Load JSON data.'''
        filename = f"{name}.json"
        artifact = await tool_context.load_artifact(filename)

        if artifact is None:
            return None

        json_str = artifact.inline_data.data.decode('utf-8')
        return json.loads(json_str)

    CSV EXPORT TOOL:
    ----------------
    async def export_to_csv(
        name: str,
        headers: list[str],
        rows: list[list],
        tool_context: ToolContext
    ) -> str:
        '''Export data to CSV file.'''
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)

        csv_content = output.getvalue()
        artifact = types.Part.from_bytes(
            data=csv_content.encode('utf-8'),
            mime_type="text/csv"
        )

        filename = f"{name}.csv"
        version = await tool_context.save_artifact(filename, artifact)
        return f"Exported to '{filename}' ({len(rows)} rows)"

    MARKDOWN REPORT TOOL:
    ---------------------
    async def create_report(
        title: str,
        sections: dict[str, str],
        tool_context: ToolContext
    ) -> str:
        '''Create a markdown report.'''
        md_content = f"# {title}\\n\\n"
        md_content += f"Generated: {datetime.now().isoformat()}\\n\\n"

        for section_title, section_content in sections.items():
            md_content += f"## {section_title}\\n\\n"
            md_content += f"{section_content}\\n\\n"

        artifact = types.Part.from_bytes(
            data=md_content.encode('utf-8'),
            mime_type="text/markdown"
        )

        filename = f"{title.lower().replace(' ', '_')}.md"
        version = await tool_context.save_artifact(filename, artifact)
        return f"Created report '{filename}'"
    """)


# =============================================================================
# Part 3: Image Handling Tools
# =============================================================================

def explain_image_tools():
    """Explain image handling tools with artifacts."""
    print("""
    IMAGE HANDLING TOOLS
    ====================

    Tools for managing image artifacts.

    SAVE IMAGE TOOL:
    ----------------
    async def save_image(
        name: str,
        image_data: str,  # Base64 encoded
        image_type: str,  # "png", "jpeg", "gif"
        tool_context: ToolContext
    ) -> str:
        '''Save an image artifact.'''
        # Decode base64
        try:
            data = base64.b64decode(image_data)
        except Exception:
            return "Error: Invalid base64 image data"

        mime_type = f"image/{image_type}"
        artifact = types.Part.from_bytes(data=data, mime_type=mime_type)

        filename = f"{name}.{image_type}"
        version = await tool_context.save_artifact(filename, artifact)

        return f"Saved image '{filename}' ({len(data)} bytes)"

    GET IMAGE INFO TOOL:
    --------------------
    async def get_image_info(
        filename: str,
        tool_context: ToolContext
    ) -> str:
        '''Get information about an image artifact.'''
        artifact = await tool_context.load_artifact(filename)

        if artifact is None:
            return f"Image '{filename}' not found"

        data = artifact.inline_data.data
        mime = artifact.inline_data.mime_type

        # Basic info
        info = {
            "filename": filename,
            "mime_type": mime,
            "size_bytes": len(data),
        }

        # Try to get dimensions (requires PIL)
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(data))
            info["width"] = img.width
            info["height"] = img.height
            info["mode"] = img.mode
        except ImportError:
            info["note"] = "Install PIL for dimension info"
        except Exception as e:
            info["error"] = str(e)

        return json.dumps(info, indent=2)

    PROFILE PICTURE TOOL:
    ---------------------
    async def set_profile_picture(
        image_data: str,  # Base64
        tool_context: ToolContext
    ) -> str:
        '''Set user profile picture (user-scoped).'''
        try:
            data = base64.b64decode(image_data)
        except Exception:
            return "Error: Invalid image data"

        # Detect image type from magic bytes
        if data[:8] == b'\\x89PNG\\r\\n\\x1a\\n':
            mime = "image/png"
        elif data[:2] == b'\\xff\\xd8':
            mime = "image/jpeg"
        else:
            mime = "image/png"  # default

        artifact = types.Part.from_bytes(data=data, mime_type=mime)

        # User-scoped for persistence across sessions
        filename = "user:profile_picture"
        version = await tool_context.save_artifact(filename, artifact)

        return f"Profile picture updated (version {version})"

    async def get_profile_picture(tool_context: ToolContext) -> str:
        '''Get user profile picture.'''
        artifact = await tool_context.load_artifact("user:profile_picture")

        if artifact is None:
            return "No profile picture set"

        data = artifact.inline_data.data
        mime = artifact.inline_data.mime_type

        # Return base64 encoded
        b64 = base64.b64encode(data).decode('ascii')
        return f"Profile picture ({mime}, {len(data)} bytes):\\n[base64]{b64[:50]}..."
    """)


# =============================================================================
# Part 4: Artifact Best Practices
# =============================================================================

def explain_best_practices():
    """Explain best practices for artifact tools."""
    print("""
    ARTIFACT BEST PRACTICES
    =======================

    1. ALWAYS CHECK FOR NONE
    ------------------------
    artifact = await ctx.load_artifact(filename)
    if artifact is None:
        return f"File '{filename}' not found"

    # Now safe to use artifact.inline_data

    2. USE APPROPRIATE MIME TYPES
    -----------------------------
    Common types:
    - text/plain, text/csv, text/markdown
    - application/json, application/pdf
    - image/png, image/jpeg, image/gif
    - audio/mpeg, audio/wav

    3. HANDLE ENCODING PROPERLY
    ---------------------------
    # Text data
    artifact = types.Part.from_bytes(
        data=text.encode('utf-8'),  # Encode to bytes
        mime_type="text/plain"
    )

    # Binary data (already bytes)
    artifact = types.Part.from_bytes(
        data=image_bytes,  # Already bytes
        mime_type="image/png"
    )

    # Loading text
    text = artifact.inline_data.data.decode('utf-8')

    4. SANITIZE FILENAMES
    ---------------------
    def sanitize_filename(name: str) -> str:
        # Remove unsafe characters
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
        return safe.lower()

    filename = sanitize_filename(user_input) + ".txt"

    5. PROVIDE CLEAR TOOL DESCRIPTIONS
    ----------------------------------
    async def upload_file(
        filename: str,
        content: str,
        content_type: str,
        tool_context: ToolContext
    ) -> str:
        '''Upload a file to storage.

        Args:
            filename: The name to save the file as (e.g., "report.pdf")
            content: The file content (base64 for binary, plain text for text)
            content_type: MIME type (e.g., "text/plain", "image/png")

        Returns:
            Confirmation message with version number
        '''

    6. VERSION AWARENESS
    --------------------
    # Document version in responses
    version = await ctx.save_artifact(filename, artifact)
    return f"Saved '{filename}' as version {version}. Use version={version} to access this specific version."

    7. SIZE LIMITS
    --------------
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    if len(data) > MAX_FILE_SIZE:
        return f"Error: File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)"

    8. ERROR HANDLING
    -----------------
    async def safe_load(filename: str, ctx: ToolContext) -> str:
        try:
            artifact = await ctx.load_artifact(filename)
            if artifact is None:
                return f"File not found: {filename}"

            data = artifact.inline_data.data
            mime = artifact.inline_data.mime_type

            if mime.startswith("text/"):
                return data.decode('utf-8')
            else:
                return f"Binary file ({mime}, {len(data)} bytes)"

        except UnicodeDecodeError:
            return "Error: File contains invalid characters"
        except Exception as e:
            return f"Error loading file: {e}"

    9. NAMESPACE CONSISTENCY
    ------------------------
    # Document which artifacts are user-scoped
    USER_SCOPED_FILES = ["user:settings.json", "user:profile.png"]

    # Or use naming convention
    # user:* = user-scoped, everything else = session-scoped
    """)


# =============================================================================
# Part 5: Complete File Manager Demo
# =============================================================================

# File Manager Tools

async def create_text_file(
    filename: str,
    content: str,
    tool_context: ToolContext
) -> str:
    """Create a text file.

    Args:
        filename: Name of the file (will add .txt if needed)
        content: Text content of the file

    Returns:
        Confirmation message
    """
    if not filename.endswith('.txt'):
        filename += '.txt'

    artifact = types.Part.from_bytes(
        data=content.encode('utf-8'),
        mime_type="text/plain"
    )

    version = await tool_context.save_artifact(filename, artifact)
    return f"Created '{filename}' (version {version}, {len(content)} characters)"


async def read_file(
    filename: str,
    tool_context: ToolContext
) -> str:
    """Read a file's content.

    Args:
        filename: Name of the file to read

    Returns:
        File content or error message
    """
    artifact = await tool_context.load_artifact(filename)

    if artifact is None:
        return f"File '{filename}' not found"

    mime = artifact.inline_data.mime_type
    data = artifact.inline_data.data

    if mime.startswith("text/") or mime == "application/json":
        try:
            content = data.decode('utf-8')
            return f"=== {filename} ({mime}) ===\n{content}"
        except UnicodeDecodeError:
            return f"Error: '{filename}' contains invalid text encoding"
    else:
        return f"Binary file '{filename}' ({mime}, {len(data)} bytes)"


async def list_all_files(tool_context: ToolContext) -> str:
    """List all available files.

    Returns:
        List of files with their types
    """
    files = await tool_context.list_artifacts()

    if not files:
        return "No files stored"

    result = ["Available files:"]
    for f in sorted(files):
        scope = "[user]" if f.startswith("user:") else "[session]"
        result.append(f"  {scope} {f}")

    return "\n".join(result)


async def save_json(
    name: str,
    data: dict,
    tool_context: ToolContext
) -> str:
    """Save JSON data.

    Args:
        name: Name for the JSON file (without extension)
        data: Dictionary to save

    Returns:
        Confirmation message
    """
    filename = f"{name}.json"
    json_bytes = json.dumps(data, indent=2).encode('utf-8')

    artifact = types.Part.from_bytes(
        data=json_bytes,
        mime_type="application/json"
    )

    version = await tool_context.save_artifact(filename, artifact)
    return f"Saved JSON '{filename}' (version {version})"


async def load_json(
    name: str,
    tool_context: ToolContext
) -> str:
    """Load JSON data.

    Args:
        name: Name of the JSON file (without extension)

    Returns:
        JSON content or error message
    """
    filename = f"{name}.json"
    artifact = await tool_context.load_artifact(filename)

    if artifact is None:
        return f"JSON file '{filename}' not found"

    try:
        json_str = artifact.inline_data.data.decode('utf-8')
        data = json.loads(json_str)
        return f"=== {filename} ===\n{json.dumps(data, indent=2)}"
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return f"Error parsing '{filename}': {e}"


async def save_user_setting(
    key: str,
    value: str,
    tool_context: ToolContext
) -> str:
    """Save a user setting (persists across sessions).

    Args:
        key: Setting name
        value: Setting value

    Returns:
        Confirmation message
    """
    # Load existing settings
    settings_artifact = await tool_context.load_artifact("user:settings.json")

    if settings_artifact:
        try:
            settings = json.loads(
                settings_artifact.inline_data.data.decode('utf-8')
            )
        except (UnicodeDecodeError, json.JSONDecodeError):
            settings = {}
    else:
        settings = {}

    # Update setting
    settings[key] = value
    settings["_updated"] = datetime.now().isoformat()

    # Save back
    json_bytes = json.dumps(settings, indent=2).encode('utf-8')
    artifact = types.Part.from_bytes(
        data=json_bytes,
        mime_type="application/json"
    )

    version = await tool_context.save_artifact("user:settings.json", artifact)
    return f"Saved setting '{key}' = '{value}' (settings version {version})"


async def get_user_settings(tool_context: ToolContext) -> str:
    """Get all user settings.

    Returns:
        User settings or message if none
    """
    artifact = await tool_context.load_artifact("user:settings.json")

    if artifact is None:
        return "No user settings saved yet"

    try:
        settings = json.loads(
            artifact.inline_data.data.decode('utf-8')
        )
        return f"User settings:\n{json.dumps(settings, indent=2)}"
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "Error: User settings file is corrupted"


async def file_manager_demo():
    """Demonstrate a complete file manager with artifacts."""
    print("\n  Complete File Manager Demo")
    print("  " + "-"*50)

    # Setup
    artifact_service = InMemoryArtifactService()
    session_service = InMemorySessionService()

    agent = LlmAgent(
        name="FileManager",
        model="gemini-2.0-flash",
        tools=[
            create_text_file,
            read_file,
            list_all_files,
            save_json,
            load_json,
            save_user_setting,
            get_user_settings,
        ],
        instruction="""You are a file manager assistant.
        Help users create, read, and manage their files.
        Use the available tools to work with artifacts.""",
    )

    runner = Runner(
        agent=agent,
        app_name="file_manager",
        session_service=session_service,
        artifact_service=artifact_service,
    )

    await session_service.create_session(
        app_name="file_manager",
        user_id="user1",
        session_id="session1",
        state={}
    )

    print("\n  Testing file manager tools directly...")

    # Test creating files
    print("\n  1. Creating text files:")

    note1 = types.Part.from_bytes(
        data=b"My first note about learning ADK artifacts.",
        mime_type="text/plain"
    )
    v1 = await artifact_service.save_artifact(
        app_name="file_manager",
        user_id="user1",
        session_id="session1",
        filename="note1.txt",
        artifact=note1
    )
    print(f"    Created 'note1.txt' (v{v1})")

    note2 = types.Part.from_bytes(
        data=b"Second note with more detailed information.",
        mime_type="text/plain"
    )
    v2 = await artifact_service.save_artifact(
        app_name="file_manager",
        user_id="user1",
        session_id="session1",
        filename="note2.txt",
        artifact=note2
    )
    print(f"    Created 'note2.txt' (v{v2})")

    # Test creating JSON
    print("\n  2. Creating JSON files:")

    config_data = {"app": "file_manager", "version": "1.0", "features": ["save", "load", "list"]}
    config = types.Part.from_bytes(
        data=json.dumps(config_data, indent=2).encode(),
        mime_type="application/json"
    )
    v3 = await artifact_service.save_artifact(
        app_name="file_manager",
        user_id="user1",
        session_id="session1",
        filename="config.json",
        artifact=config
    )
    print(f"    Created 'config.json' (v{v3})")

    # Test user-scoped settings
    print("\n  3. Creating user-scoped settings:")

    settings_data = {"theme": "dark", "language": "en", "notifications": True}
    settings = types.Part.from_bytes(
        data=json.dumps(settings_data, indent=2).encode(),
        mime_type="application/json"
    )
    v4 = await artifact_service.save_artifact(
        app_name="file_manager",
        user_id="user1",
        session_id="session1",
        filename="user:settings.json",
        artifact=settings
    )
    print(f"    Created 'user:settings.json' (v{v4})")

    # Test listing files
    print("\n  4. Listing all files:")

    files = await artifact_service.list_artifact_keys(
        app_name="file_manager",
        user_id="user1",
        session_id="session1"
    )
    for f in sorted(files):
        scope = "[USER]" if f.startswith("user:") else "[SESSION]"
        print(f"    {scope} {f}")

    # Test reading files
    print("\n  5. Reading file contents:")

    for filename in ["note1.txt", "config.json"]:
        artifact = await artifact_service.load_artifact(
            app_name="file_manager",
            user_id="user1",
            session_id="session1",
            filename=filename
        )
        if artifact:
            content = artifact.inline_data.data.decode()
            preview = content[:50] + "..." if len(content) > 50 else content
            print(f"    {filename}: {preview}")

    # Test versioning
    print("\n  6. Testing versioning:")

    updated_note = types.Part.from_bytes(
        data=b"Updated first note with new information added.",
        mime_type="text/plain"
    )
    v5 = await artifact_service.save_artifact(
        app_name="file_manager",
        user_id="user1",
        session_id="session1",
        filename="note1.txt",
        artifact=updated_note
    )
    print(f"    Updated 'note1.txt' to v{v5}")

    versions = await artifact_service.list_versions(
        app_name="file_manager",
        user_id="user1",
        session_id="session1",
        filename="note1.txt"
    )
    print(f"    Versions of 'note1.txt': {versions}")

    # Load different versions
    v0_content = await artifact_service.load_artifact(
        app_name="file_manager",
        user_id="user1",
        session_id="session1",
        filename="note1.txt",
        version=0
    )
    latest_content = await artifact_service.load_artifact(
        app_name="file_manager",
        user_id="user1",
        session_id="session1",
        filename="note1.txt"
    )

    print(f"    v0: {v0_content.inline_data.data.decode()[:40]}...")
    print(f"    latest: {latest_content.inline_data.data.decode()[:40]}...")

    # Test with agent
    print("\n  7. Testing agent interaction:")

    user_message = types.Content(
        role="user",
        parts=[types.Part(text="What files do I have?")]
    )

    print("    User: What files do I have?")
    print("    Agent: ", end="")

    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response = part.text[:300]
                    print(response + ("..." if len(part.text) > 300 else ""))

    print("\n  Demo complete!")


async def main():
    print("\n" + "#"*70)
    print("# Lab 7 Exercise 5: Artifact Tools")
    print("#"*70)

    # =========================================================================
    # Part 1: File Management Tools
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: File Management Tools")
    print("="*60)
    explain_file_management_tools()

    # =========================================================================
    # Part 2: Document Processing Tools
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Document Processing Tools")
    print("="*60)
    explain_document_tools()

    # =========================================================================
    # Part 3: Image Handling Tools
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Image Handling Tools")
    print("="*60)
    explain_image_tools()

    # =========================================================================
    # Part 4: Best Practices
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Artifact Best Practices")
    print("="*60)
    explain_best_practices()

    # =========================================================================
    # Part 5: Demo
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Complete File Manager Demo")
    print("="*60)

    await file_manager_demo()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Artifact Tools")
    print("#"*70)
    print("""
    ARTIFACT TOOL PATTERNS:
    -----------------------

    1. File Management:
       - upload_file(filename, content, type)
       - download_file(filename)
       - list_files()
       - delete_file(filename)

    2. Document Processing:
       - create_document(title, content)
       - save_json(name, data)
       - load_json(name)
       - export_to_csv(name, headers, rows)

    3. Image Handling:
       - save_image(name, base64_data, type)
       - get_image_info(filename)
       - set_profile_picture(base64_data)

    BEST PRACTICES:
    ---------------
    1. Always check load_artifact() for None
    2. Use appropriate MIME types
    3. Handle encoding/decoding carefully
    4. Sanitize user-provided filenames
    5. Provide clear tool descriptions
    6. Document version numbers in responses
    7. Implement size limits
    8. Use proper error handling
    9. Be consistent with namespace usage

    TOOL DESIGN TIPS:
    -----------------
    - Make tools self-documenting with docstrings
    - Return clear success/error messages
    - Handle edge cases gracefully
    - Use user: prefix for persistent data
    - Consider versioning in tool design
    """)


if __name__ == "__main__":
    asyncio.run(main())
