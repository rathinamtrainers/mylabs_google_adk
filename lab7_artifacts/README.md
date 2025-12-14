# Lab 7: Artifacts

Learn how to manage binary data, files, and versioned content with ADK Artifacts.

## Prerequisites
- Completed Labs 1-6
- Google API Key configured
- Understanding of sessions and tools

## Exercises

### Exercise 1: Artifacts Basics
Learn the fundamentals of ADK artifacts.
- What are artifacts and why use them
- Artifact vs State comparison
- types.Part representation
- Core concepts overview

```bash
uv run python 01_artifacts_basics.py
```

### Exercise 2: Artifact Services
Understand artifact service implementations.
- BaseArtifactService interface
- InMemoryArtifactService (testing)
- GcsArtifactService (production)
- Configuring Runner with artifact service

```bash
uv run python 02_artifact_service.py
```

### Exercise 3: Artifact Operations via Context
Master artifact operations through context objects.
- CallbackContext artifact access
- ToolContext artifact access
- Save, load, list operations
- Error handling patterns

```bash
uv run python 03_artifact_operations.py
```

### Exercise 4: Artifact Namespaces
Learn about artifact scoping and namespaces.
- Session-scoped artifacts (default)
- User-scoped artifacts ("user:" prefix)
- Cross-session artifact access
- Choosing the right namespace

```bash
uv run python 04_artifact_namespaces.py
```

### Exercise 5: Artifact Tools
Build tools that work with artifacts.
- File management tools
- Document processing tools
- Image handling tools
- Best practices for artifact tools

```bash
uv run python 05_artifact_tools.py
```

## Key Concepts

### Artifact Representation
```python
from google.genai import types

# Create artifact from bytes
artifact = types.Part.from_bytes(
    data=file_bytes,
    mime_type="application/pdf"
)

# Access data
raw_bytes = artifact.inline_data.data
content_type = artifact.inline_data.mime_type
```

### Artifact Services
```python
from google.adk.artifacts import InMemoryArtifactService

# For testing
artifact_service = InMemoryArtifactService()

# Configure Runner
runner = Runner(
    agent=agent,
    app_name="my_app",
    session_service=session_service,
    artifact_service=artifact_service  # Required!
)
```

### Context Operations
```python
# In a tool
async def my_tool(tool_context: ToolContext) -> str:
    # Save artifact
    version = await tool_context.save_artifact("file.txt", artifact)

    # Load artifact
    data = await tool_context.load_artifact("file.txt")

    # List artifacts
    files = await tool_context.list_artifacts()
```

### Namespacing
```python
# Session-scoped (default)
await ctx.save_artifact("report.pdf", artifact)

# User-scoped (persists across sessions)
await ctx.save_artifact("user:settings.json", artifact)
```

## Common MIME Types
- `text/plain` - Plain text
- `text/csv` - CSV data
- `application/json` - JSON data
- `application/pdf` - PDF documents
- `image/png` - PNG images
- `image/jpeg` - JPEG images
- `audio/mpeg` - MP3 audio
- `video/mp4` - MP4 video
