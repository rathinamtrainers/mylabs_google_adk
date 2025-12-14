"""
Lab 7 - Exercise 4: Artifact Namespaces
========================================

This exercise covers artifact namespacing:
1. Session-scoped artifacts (default)
2. User-scoped artifacts ("user:" prefix)
3. Choosing the right namespace
4. Cross-session artifact access
5. Namespace demo

Run: uv run python 04_artifact_namespaces.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types


# =============================================================================
# Part 1: Session-Scoped Artifacts
# =============================================================================

def explain_session_scope():
    """Explain session-scoped artifacts."""
    print("""
    SESSION-SCOPED ARTIFACTS
    ========================

    The DEFAULT scope for artifacts.
    Artifacts are tied to a specific session.

    IDENTIFIER COMPONENTS:
    ----------------------
    Session-scoped artifacts are identified by:
    - app_name (from Runner)
    - user_id (from invocation)
    - session_id (from current session)
    - filename (plain string, no prefix)

    FILENAME FORMAT:
    ----------------
    Just use a plain filename:
    - "report.pdf"
    - "notes.txt"
    - "image.png"
    - "config.json"

    BEHAVIOR:
    ---------
    - Only accessible within the SAME session
    - Different sessions = different artifacts
    - Same filename in different sessions = separate files

    EXAMPLE:
    --------
    # Session 1
    await ctx.save_artifact("notes.txt", notes_part)
    # Saved to: app/user1/session1/notes.txt

    # Session 2 (same user, different session)
    artifact = await ctx.load_artifact("notes.txt")
    # Returns None! Different session = different storage

    STORAGE PATH (Conceptual):
    --------------------------
    {app_name}/{user_id}/{session_id}/{filename}

    Example paths:
    - my_app/user123/session_abc/report.pdf
    - my_app/user123/session_xyz/report.pdf  (different file!)
    - my_app/user456/session_abc/report.pdf  (different file!)

    USE CASES:
    ----------
    - Conversation-specific data
    - Temporary files during a session
    - Session-specific outputs
    - Draft documents
    - Intermediate results

    LIFECYCLE:
    ----------
    - Created when saved in session
    - Persists with session (if using persistent storage)
    - Deleted when artifact/session is cleaned up
    - NOT shared across sessions
    """)


# =============================================================================
# Part 2: User-Scoped Artifacts
# =============================================================================

def explain_user_scope():
    """Explain user-scoped artifacts."""
    print("""
    USER-SCOPED ARTIFACTS
    =====================

    Artifacts accessible across ALL sessions for a user.
    Use "user:" prefix in filename.

    IDENTIFIER COMPONENTS:
    ----------------------
    User-scoped artifacts are identified by:
    - app_name (from Runner)
    - user_id (from invocation)
    - filename (with "user:" prefix)

    NOTE: session_id is NOT part of the identifier!

    FILENAME FORMAT:
    ----------------
    Add "user:" prefix:
    - "user:profile.png"
    - "user:preferences.json"
    - "user:settings.txt"
    - "user:avatar.jpg"

    BEHAVIOR:
    ---------
    - Accessible from ANY session for the user
    - Persists across sessions
    - Same filename = same file in all sessions
    - Perfect for user-level data

    EXAMPLE:
    --------
    # Session 1
    await ctx.save_artifact("user:profile.png", profile_part)
    # Saved to: app/user1/user:profile.png (session-independent)

    # Session 2 (same user, different session)
    profile = await ctx.load_artifact("user:profile.png")
    # Returns the profile! Same user = same storage

    # Session 3 (different user)
    profile = await ctx.load_artifact("user:profile.png")
    # Returns None or different profile! Different user!

    STORAGE PATH (Conceptual):
    --------------------------
    {app_name}/{user_id}/{filename}

    The "user:" prefix signals to skip session_id.

    Example paths:
    - my_app/user123/user:profile.png
    - my_app/user456/user:profile.png  (different user!)

    USE CASES:
    ----------
    - User profile pictures
    - User preferences/settings
    - Persistent user configurations
    - Cross-session documents
    - User-specific templates

    LIFECYCLE:
    ----------
    - Created when saved
    - Persists independently of sessions
    - Available in ALL user sessions
    - Must be explicitly deleted
    """)


# =============================================================================
# Part 3: Choosing the Right Namespace
# =============================================================================

def explain_choosing_namespace():
    """Explain how to choose between namespaces."""
    print("""
    CHOOSING THE RIGHT NAMESPACE
    ============================

    Decision guide for artifact scoping.

    USE SESSION SCOPE WHEN:
    -----------------------
    ✓ Data is conversation-specific
    ✓ Files are temporary/intermediate
    ✓ Different sessions need different versions
    ✓ Data should be isolated between sessions
    ✓ Cleanup should happen with session

    Examples:
    - Conversation transcripts → "transcript.txt"
    - Session-specific reports → "analysis_report.pdf"
    - Temporary processing files → "temp_data.json"
    - Draft documents → "draft.docx"

    USE USER SCOPE WHEN:
    --------------------
    ✓ Data should persist across sessions
    ✓ User settings or preferences
    ✓ Profile information
    ✓ Shared across all conversations
    ✓ User-owned content

    Examples:
    - Profile picture → "user:avatar.png"
    - App preferences → "user:settings.json"
    - User templates → "user:email_template.txt"
    - Saved documents → "user:my_document.pdf"

    DECISION FLOWCHART:
    -------------------
    Is this data needed across multiple sessions?
        │
        ├── YES → Use "user:" prefix
        │
        └── NO → Is it conversation-specific?
                │
                ├── YES → Use plain filename (session scope)
                │
                └── NO → Consider if it should be user-scoped

    NAMING CONVENTIONS:
    -------------------
    Session-scoped (no prefix):
    - session_notes.txt
    - conversation_summary.pdf
    - temp_image_001.png

    User-scoped (user: prefix):
    - user:profile.json
    - user:settings.yaml
    - user:avatar.png
    - user:saved_templates/email.txt

    MIXING SCOPES:
    --------------
    You can use BOTH in the same session:

    # User's profile (persistent)
    profile = await ctx.load_artifact("user:profile.json")

    # Session-specific analysis (temporary)
    await ctx.save_artifact("analysis.pdf", analysis_part)

    # Reference user settings in session work
    settings = await ctx.load_artifact("user:settings.json")
    await ctx.save_artifact("report.pdf", report_part)

    VERSIONING IN BOTH SCOPES:
    --------------------------
    Both scopes support versioning!

    # User scope with versions
    v1 = await ctx.save_artifact("user:profile.png", old_pic)
    v2 = await ctx.save_artifact("user:profile.png", new_pic)

    # Load specific version of user artifact
    old = await ctx.load_artifact("user:profile.png", version=0)
    """)


# =============================================================================
# Part 4: Cross-Session Access
# =============================================================================

def explain_cross_session():
    """Explain cross-session artifact access patterns."""
    print("""
    CROSS-SESSION ARTIFACT ACCESS
    =============================

    Patterns for accessing artifacts across sessions.

    SCENARIO 1: User Returns in New Session
    ---------------------------------------
    Session 1:
        # Save user preferences
        await ctx.save_artifact("user:prefs.json", prefs_part)

    Session 2 (later):
        # Load user preferences - works!
        prefs = await ctx.load_artifact("user:prefs.json")

    SCENARIO 2: Migrating Session Data to User
    ------------------------------------------
    Sometimes you want to "promote" session data to user scope:

    async def save_as_permanent(ctx: ToolContext, filename: str) -> str:
        '''Migrate session artifact to user scope.'''

        # Load from session scope
        artifact = await ctx.load_artifact(filename)
        if not artifact:
            return f"'{filename}' not found in session"

        # Save to user scope
        user_filename = f"user:{filename}"
        version = await ctx.save_artifact(user_filename, artifact)

        return f"Saved as '{user_filename}' (version {version})"

    SCENARIO 3: Copy User Data to Session
    -------------------------------------
    Copy user template to session for modification:

    async def use_template(ctx: ToolContext, template: str) -> str:
        '''Copy user template to session for editing.'''

        # Load from user scope
        user_template = f"user:{template}"
        artifact = await ctx.load_artifact(user_template)
        if not artifact:
            return f"Template '{template}' not found"

        # Save to session scope (for editing)
        session_filename = f"editing_{template}"
        version = await ctx.save_artifact(session_filename, artifact)

        return f"Copied to '{session_filename}' for editing"

    SCENARIO 4: Checking Both Scopes
    --------------------------------
    Look for artifact in session first, fall back to user:

    async def find_file(ctx: ToolContext, name: str) -> Part | None:
        '''Find artifact in session or user scope.'''

        # Try session scope first
        artifact = await ctx.load_artifact(name)
        if artifact:
            return artifact

        # Fall back to user scope
        user_name = f"user:{name}"
        artifact = await ctx.load_artifact(user_name)
        return artifact

    SCENARIO 5: List All User's Artifacts
    -------------------------------------
    Note: list_artifacts() returns BOTH session and user scoped!

    files = await ctx.list_artifacts()
    # Returns: ["report.pdf", "user:settings.json", "temp.txt", ...]

    session_files = [f for f in files if not f.startswith("user:")]
    user_files = [f for f in files if f.startswith("user:")]

    BEST PRACTICES:
    ---------------
    1. Use clear naming to distinguish purposes
    2. Document which scope artifacts use
    3. Consider cleanup strategies for both
    4. Handle missing artifacts gracefully
    5. Be consistent within your application
    """)


# =============================================================================
# Part 5: Namespace Demo
# =============================================================================

async def namespace_demo():
    """Demonstrate artifact namespace behavior."""
    print("\n  Demonstrating artifact namespaces...")
    print("  " + "-"*50)

    # Create services
    artifact_service = InMemoryArtifactService()
    session_service = InMemorySessionService()

    # Test parameters
    app_name = "namespace_demo"
    user_id = "user123"
    session_1 = "session_A"
    session_2 = "session_B"

    print("\n  1. Creating artifacts in Session A:")
    print("  " + "-"*50)

    # Session-scoped artifact
    session_artifact = types.Part.from_bytes(
        data=b"Session A specific data",
        mime_type="text/plain"
    )
    v1 = await artifact_service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_1,
        filename="session_data.txt",
        artifact=session_artifact
    )
    print(f"    Saved 'session_data.txt' (session-scoped) v{v1}")

    # User-scoped artifact
    user_artifact = types.Part.from_bytes(
        data=b'{"theme": "dark", "language": "en"}',
        mime_type="application/json"
    )
    v2 = await artifact_service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_1,
        filename="user:settings.json",
        artifact=user_artifact
    )
    print(f"    Saved 'user:settings.json' (user-scoped) v{v2}")

    # Another user-scoped artifact
    profile_artifact = types.Part.from_bytes(
        data=b"\x89PNG... (fake profile image)",
        mime_type="image/png"
    )
    v3 = await artifact_service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_1,
        filename="user:profile.png",
        artifact=profile_artifact
    )
    print(f"    Saved 'user:profile.png' (user-scoped) v{v3}")

    print("\n  2. Listing artifacts from Session A:")
    print("  " + "-"*50)

    session_a_files = await artifact_service.list_artifact_keys(
        app_name=app_name,
        user_id=user_id,
        session_id=session_1
    )
    for f in session_a_files:
        scope = "USER" if f.startswith("user:") else "SESSION"
        print(f"    [{scope}] {f}")

    print("\n  3. Accessing from Session B (different session):")
    print("  " + "-"*50)

    # Try to load session-scoped artifact from different session
    session_data = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_2,
        filename="session_data.txt"
    )
    print(f"    'session_data.txt' from Session B: {session_data}")
    # Should be None - session-scoped!

    # Load user-scoped artifact from different session
    settings = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_2,
        filename="user:settings.json"
    )
    if settings:
        content = settings.inline_data.data.decode()
        print(f"    'user:settings.json' from Session B: {content}")
    # Should work - user-scoped!

    # Load another user-scoped artifact
    profile = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_2,
        filename="user:profile.png"
    )
    if profile:
        size = len(profile.inline_data.data)
        print(f"    'user:profile.png' from Session B: {size} bytes")

    print("\n  4. Creating session-specific artifact in Session B:")
    print("  " + "-"*50)

    # Save session B specific artifact
    session_b_artifact = types.Part.from_bytes(
        data=b"Session B specific data",
        mime_type="text/plain"
    )
    v4 = await artifact_service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_2,
        filename="session_data.txt",
        artifact=session_b_artifact
    )
    print(f"    Saved 'session_data.txt' in Session B v{v4}")

    # Now both sessions have different session_data.txt
    print("\n  5. Comparing session_data.txt across sessions:")
    print("  " + "-"*50)

    data_a = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_1,
        filename="session_data.txt"
    )
    data_b = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_2,
        filename="session_data.txt"
    )

    if data_a:
        print(f"    Session A: {data_a.inline_data.data.decode()}")
    if data_b:
        print(f"    Session B: {data_b.inline_data.data.decode()}")

    print("\n  6. Different user (user456) access:")
    print("  " + "-"*50)

    different_user = "user456"

    # Try to access user123's user-scoped artifact as user456
    other_settings = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=different_user,
        session_id=session_1,
        filename="user:settings.json"
    )
    print(f"    user456 accessing user123's 'user:settings.json': {other_settings}")
    # Should be None - different user!

    # Save user456's own settings
    user456_settings = types.Part.from_bytes(
        data=b'{"theme": "light", "language": "fr"}',
        mime_type="application/json"
    )
    v5 = await artifact_service.save_artifact(
        app_name=app_name,
        user_id=different_user,
        session_id=session_1,
        filename="user:settings.json",
        artifact=user456_settings
    )
    print(f"    Saved user456's 'user:settings.json' v{v5}")

    # Verify isolation
    user123_settings = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_1,
        filename="user:settings.json"
    )
    user456_loaded = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=different_user,
        session_id=session_1,
        filename="user:settings.json"
    )

    print("\n  7. Verifying user isolation:")
    print("  " + "-"*50)

    if user123_settings:
        print(f"    user123 settings: {user123_settings.inline_data.data.decode()}")
    if user456_loaded:
        print(f"    user456 settings: {user456_loaded.inline_data.data.decode()}")

    print("\n  8. Updating user-scoped artifact (versioning):")
    print("  " + "-"*50)

    # Update user settings
    updated_settings = types.Part.from_bytes(
        data=b'{"theme": "dark", "language": "en", "notifications": true}',
        mime_type="application/json"
    )
    v6 = await artifact_service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_1,
        filename="user:settings.json",
        artifact=updated_settings
    )
    print(f"    Updated 'user:settings.json' to v{v6}")

    # List versions
    versions = await artifact_service.list_versions(
        app_name=app_name,
        user_id=user_id,
        session_id=session_1,
        filename="user:settings.json"
    )
    print(f"    Available versions: {versions}")

    # Load specific version
    old_version = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_1,
        filename="user:settings.json",
        version=0
    )
    new_version = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_1,
        filename="user:settings.json"  # latest
    )

    if old_version:
        print(f"    Version 0: {old_version.inline_data.data.decode()}")
    if new_version:
        print(f"    Latest: {new_version.inline_data.data.decode()}")

    print("\n  Demo complete!")


async def main():
    print("\n" + "#"*70)
    print("# Lab 7 Exercise 4: Artifact Namespaces")
    print("#"*70)

    # =========================================================================
    # Part 1: Session Scope
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Session-Scoped Artifacts")
    print("="*60)
    explain_session_scope()

    # =========================================================================
    # Part 2: User Scope
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: User-Scoped Artifacts")
    print("="*60)
    explain_user_scope()

    # =========================================================================
    # Part 3: Choosing Namespace
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Choosing the Right Namespace")
    print("="*60)
    explain_choosing_namespace()

    # =========================================================================
    # Part 4: Cross-Session Access
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Cross-Session Artifact Access")
    print("="*60)
    explain_cross_session()

    # =========================================================================
    # Part 5: Demo
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Namespace Demo")
    print("="*60)

    await namespace_demo()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Artifact Namespaces")
    print("#"*70)
    print("""
    TWO ARTIFACT SCOPES:
    --------------------

    1. SESSION SCOPE (default):
       - Filename: "report.pdf" (no prefix)
       - Tied to: app_name + user_id + session_id
       - Access: Only in same session
       - Use for: Conversation-specific data

    2. USER SCOPE:
       - Filename: "user:settings.json" (user: prefix)
       - Tied to: app_name + user_id
       - Access: All sessions for that user
       - Use for: Persistent user data

    CHOOSING THE RIGHT SCOPE:
    -------------------------
    Session scope when:
    - Data is conversation-specific
    - Files are temporary
    - Should be isolated between sessions

    User scope when:
    - Data persists across sessions
    - User settings/preferences
    - Profile information

    KEY BEHAVIORS:
    --------------
    - Different sessions with session scope = separate files
    - Same user with user scope = same file across sessions
    - Different users with user scope = separate files
    - Both scopes support versioning

    ISOLATION:
    ----------
    - Users are always isolated from each other
    - Sessions are isolated (for session scope)
    - User scope shares across user's sessions only
    """)


if __name__ == "__main__":
    asyncio.run(main())
