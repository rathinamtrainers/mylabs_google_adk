"""
Lab 7 - Exercise 2: Artifact Services
======================================

This exercise covers artifact service implementations:
1. BaseArtifactService interface
2. InMemoryArtifactService (testing)
3. GcsArtifactService (production)
4. Configuring Runner with artifact service
5. Service comparison demo

Run: uv run python 02_artifact_service.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types


# =============================================================================
# Part 1: BaseArtifactService Interface
# =============================================================================

def explain_base_interface():
    """Explain the BaseArtifactService interface."""
    print("""
    BASE ARTIFACT SERVICE INTERFACE
    ================================

    All artifact services implement BaseArtifactService.
    This defines the contract for artifact storage.

    ABSTRACT METHODS:
    -----------------
    1. save_artifact(app_name, user_id, session_id, filename, artifact)
       - Stores artifact and returns version number
       - Returns: int (version)

    2. load_artifact(app_name, user_id, session_id, filename, version=None)
       - Retrieves artifact (latest if version is None)
       - Returns: types.Part or None

    3. list_artifact_keys(app_name, user_id, session_id)
       - Lists all artifact filenames in scope
       - Returns: list[str]

    4. list_versions(app_name, user_id, session_id, filename)
       - Lists all versions of an artifact
       - Returns: list[int]

    5. delete_artifact(app_name, user_id, session_id, filename)
       - Removes artifact (all versions)
       - Returns: None

    INTERFACE DEFINITION:
    ---------------------
    from abc import ABC, abstractmethod

    class BaseArtifactService(ABC):

        @abstractmethod
        async def save_artifact(
            self,
            app_name: str,
            user_id: str,
            session_id: str,
            filename: str,
            artifact: types.Part
        ) -> int:
            '''Save artifact and return version.'''
            pass

        @abstractmethod
        async def load_artifact(
            self,
            app_name: str,
            user_id: str,
            session_id: str,
            filename: str,
            version: int | None = None
        ) -> types.Part | None:
            '''Load artifact by filename and optional version.'''
            pass

        # ... other methods

    PARAMETERS EXPLAINED:
    ---------------------
    - app_name: Your application identifier
    - user_id: User identifier
    - session_id: Session identifier
    - filename: Artifact name (unique within scope)
    - version: Optional version number (None = latest)
    """)


# =============================================================================
# Part 2: InMemoryArtifactService
# =============================================================================

def explain_inmemory_service():
    """Explain InMemoryArtifactService."""
    print("""
    INMEMORY ARTIFACT SERVICE
    =========================

    Stores artifacts in Python dictionaries (RAM).
    Perfect for development and testing.

    CHARACTERISTICS:
    ----------------
    - Storage: Python dict in memory
    - Persistence: None (lost on restart)
    - Speed: Very fast (memory access)
    - Setup: No external dependencies

    USAGE:
    ------
    from google.adk.artifacts import InMemoryArtifactService

    # Create instance
    artifact_service = InMemoryArtifactService()

    # Configure runner
    runner = Runner(
        agent=agent,
        app_name="my_app",
        session_service=session_service,
        artifact_service=artifact_service
    )

    INTERNAL STRUCTURE:
    -------------------
    The service uses nested dictionaries:

    self.artifacts = {
        "app_name": {
            "user_id": {
                "session_id": {
                    "filename": [Part_v0, Part_v1, Part_v2, ...]
                }
            }
        }
    }

    Each filename maps to a LIST of versions.
    Index 0 = version 0, Index 1 = version 1, etc.

    WHEN TO USE:
    ------------
    - Local development
    - Unit tests
    - Integration tests
    - Demos and prototypes
    - Short-lived processes

    WHEN NOT TO USE:
    ----------------
    - Production environments
    - Data that must persist
    - Multi-instance deployments
    - Large file storage (memory limits)

    MEMORY CONSIDERATIONS:
    ----------------------
    Be careful with large artifacts!
    - 10MB image × 100 versions = 1GB RAM
    - Consider cleanup strategies
    - Monitor memory usage in tests
    """)


# =============================================================================
# Part 3: GcsArtifactService
# =============================================================================

def explain_gcs_service():
    """Explain GcsArtifactService."""
    print("""
    GCS ARTIFACT SERVICE
    ====================

    Stores artifacts in Google Cloud Storage.
    Perfect for production deployments.

    CHARACTERISTICS:
    ----------------
    - Storage: Google Cloud Storage buckets
    - Persistence: Durable (99.999999999%)
    - Speed: Network latency (but cached)
    - Setup: GCS bucket + credentials

    USAGE:
    ------
    from google.adk.artifacts import GcsArtifactService

    # Create instance with bucket name
    artifact_service = GcsArtifactService(
        bucket_name="my-adk-artifacts-bucket"
    )

    # Configure runner
    runner = Runner(
        agent=agent,
        app_name="my_app",
        session_service=session_service,
        artifact_service=artifact_service
    )

    GCS OBJECT NAMING:
    ------------------
    Objects are stored with hierarchical paths:

    gs://bucket-name/
    └── app_name/
        └── user_id/
            └── session_id/
                └── filename/
                    └── version_N  (actual blob)

    Example:
    gs://my-bucket/my_app/user123/session456/report.pdf/version_0

    PREREQUISITES:
    --------------
    1. Create GCS bucket:
       gsutil mb gs://my-adk-artifacts-bucket

    2. Set up authentication:
       - Application Default Credentials (ADC)
       - Service account with Storage Object Admin role

    3. Install google-cloud-storage:
       pip install google-cloud-storage

    IAM PERMISSIONS NEEDED:
    -----------------------
    - storage.objects.create
    - storage.objects.get
    - storage.objects.list
    - storage.objects.delete

    Role: "Storage Object Admin" (roles/storage.objectAdmin)

    WHEN TO USE:
    ------------
    - Production environments
    - Data that must persist
    - Multi-instance deployments
    - Large file storage
    - Cross-region access needed

    ERROR HANDLING:
    ---------------
    from google.api_core.exceptions import Forbidden, NotFound

    try:
        version = await artifact_service.save_artifact(...)
    except Forbidden as e:
        print("Permission denied - check IAM roles")
    except NotFound as e:
        print("Bucket not found - check bucket name")
    except Exception as e:
        print(f"Storage error: {e}")

    COST CONSIDERATIONS:
    --------------------
    GCS charges for:
    - Storage (per GB per month)
    - Operations (per 10,000 operations)
    - Network egress (data transfer out)

    Tips:
    - Use lifecycle policies for cleanup
    - Consider storage class (Standard vs Nearline)
    - Monitor usage with Cloud Monitoring
    """)


# =============================================================================
# Part 4: Configuring Runner
# =============================================================================

def explain_runner_config():
    """Explain how to configure Runner with artifact service."""
    print("""
    CONFIGURING RUNNER WITH ARTIFACT SERVICE
    =========================================

    The Runner needs an artifact service to enable artifacts.

    BASIC CONFIGURATION:
    --------------------
    from google.adk.runners import Runner
    from google.adk.artifacts import InMemoryArtifactService
    from google.adk.sessions import InMemorySessionService

    # Create services
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()

    # Create agent
    agent = LlmAgent(
        name="my_agent",
        model="gemini-2.0-flash"
    )

    # Configure runner with artifact service
    runner = Runner(
        agent=agent,
        app_name="my_app",
        session_service=session_service,
        artifact_service=artifact_service  # Enable artifacts!
    )

    WITHOUT ARTIFACT SERVICE:
    -------------------------
    If you don't provide artifact_service:
    - save_artifact() raises ValueError
    - load_artifact() raises ValueError
    - list_artifacts() raises ValueError

    runner_no_artifacts = Runner(
        agent=agent,
        app_name="my_app",
        session_service=session_service,
        # artifact_service not provided - artifacts disabled!
    )

    PRODUCTION CONFIGURATION:
    -------------------------
    from google.adk.artifacts import GcsArtifactService
    from google.adk.sessions import DatabaseSessionService

    # Production services
    session_service = DatabaseSessionService(
        database_url="postgresql://..."
    )
    artifact_service = GcsArtifactService(
        bucket_name="prod-artifacts-bucket"
    )

    runner = Runner(
        agent=agent,
        app_name="production_app",
        session_service=session_service,
        artifact_service=artifact_service
    )

    DEVELOPMENT VS PRODUCTION:
    --------------------------
    import os

    if os.getenv("ENV") == "production":
        artifact_service = GcsArtifactService(
            bucket_name=os.getenv("GCS_BUCKET")
        )
    else:
        artifact_service = InMemoryArtifactService()

    CONTEXT ACCESS:
    ---------------
    Once configured, artifacts are accessible via context:

    async def my_tool(tool_context: ToolContext):
        # Save artifact
        version = await tool_context.save_artifact(
            filename="output.pdf",
            artifact=pdf_part
        )

        # Load artifact
        data = await tool_context.load_artifact("output.pdf")

        # List artifacts
        files = await tool_context.list_artifacts()
    """)


# =============================================================================
# Part 5: Service Comparison Demo
# =============================================================================

async def service_comparison_demo():
    """Demonstrate InMemoryArtifactService capabilities."""
    print("\n  Demonstrating InMemoryArtifactService...")
    print("  " + "-"*50)

    # Create service
    artifact_service = InMemoryArtifactService()

    # Test parameters
    app_name = "demo_app"
    user_id = "user123"
    session_id = "session456"

    print("\n  1. Saving multiple versions:")
    print("  " + "-"*50)

    # Save version 0
    v0_data = types.Part.from_bytes(
        data=b"Version 0 content",
        mime_type="text/plain"
    )
    v0 = await artifact_service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        filename="data.txt",
        artifact=v0_data
    )
    print(f"    Saved version: {v0}")

    # Save version 1
    v1_data = types.Part.from_bytes(
        data=b"Version 1 content - updated",
        mime_type="text/plain"
    )
    v1 = await artifact_service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        filename="data.txt",
        artifact=v1_data
    )
    print(f"    Saved version: {v1}")

    # Save version 2
    v2_data = types.Part.from_bytes(
        data=b"Version 2 content - final",
        mime_type="text/plain"
    )
    v2 = await artifact_service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        filename="data.txt",
        artifact=v2_data
    )
    print(f"    Saved version: {v2}")

    print("\n  2. Loading different versions:")
    print("  " + "-"*50)

    # Load latest (should be v2)
    latest = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        filename="data.txt"
    )
    print(f"    Latest: {latest.inline_data.data.decode()}")

    # Load version 0
    version_0 = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        filename="data.txt",
        version=0
    )
    print(f"    Version 0: {version_0.inline_data.data.decode()}")

    # Load version 1
    version_1 = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        filename="data.txt",
        version=1
    )
    print(f"    Version 1: {version_1.inline_data.data.decode()}")

    print("\n  3. Listing versions:")
    print("  " + "-"*50)

    versions = await artifact_service.list_versions(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        filename="data.txt"
    )
    print(f"    Available versions: {versions}")

    print("\n  4. Multiple artifacts:")
    print("  " + "-"*50)

    # Save different artifacts
    await artifact_service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        filename="image.png",
        artifact=types.Part.from_bytes(data=b"\x89PNG...", mime_type="image/png")
    )
    await artifact_service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        filename="config.json",
        artifact=types.Part.from_bytes(data=b'{"key": "value"}', mime_type="application/json")
    )

    # List all artifacts
    all_artifacts = await artifact_service.list_artifact_keys(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )
    print(f"    All artifacts: {all_artifacts}")

    print("\n  5. Session isolation:")
    print("  " + "-"*50)

    # Save to different session
    await artifact_service.save_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id="different_session",
        filename="unique.txt",
        artifact=types.Part.from_bytes(data=b"Different session data", mime_type="text/plain")
    )

    # List artifacts in original session
    session1_artifacts = await artifact_service.list_artifact_keys(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )
    print(f"    Session '{session_id}' artifacts: {session1_artifacts}")

    # List artifacts in different session
    session2_artifacts = await artifact_service.list_artifact_keys(
        app_name=app_name,
        user_id=user_id,
        session_id="different_session"
    )
    print(f"    Session 'different_session' artifacts: {session2_artifacts}")

    print("\n  6. Non-existent artifact handling:")
    print("  " + "-"*50)

    # Try to load non-existent artifact
    missing = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        filename="nonexistent.txt"
    )
    print(f"    Loading non-existent artifact: {missing}")

    # Try to load non-existent version
    missing_version = await artifact_service.load_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        filename="data.txt",
        version=999
    )
    print(f"    Loading non-existent version: {missing_version}")

    print("\n  7. Delete artifact:")
    print("  " + "-"*50)

    await artifact_service.delete_artifact(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        filename="config.json"
    )
    print("    Deleted 'config.json'")

    remaining = await artifact_service.list_artifact_keys(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )
    print(f"    Remaining artifacts: {remaining}")

    print("\n  Demo complete!")


async def main():
    print("\n" + "#"*70)
    print("# Lab 7 Exercise 2: Artifact Services")
    print("#"*70)

    # =========================================================================
    # Part 1: Base Interface
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: BaseArtifactService Interface")
    print("="*60)
    explain_base_interface()

    # =========================================================================
    # Part 2: InMemory Service
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: InMemoryArtifactService")
    print("="*60)
    explain_inmemory_service()

    # =========================================================================
    # Part 3: GCS Service
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: GcsArtifactService")
    print("="*60)
    explain_gcs_service()

    # =========================================================================
    # Part 4: Runner Configuration
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Configuring Runner")
    print("="*60)
    explain_runner_config()

    # =========================================================================
    # Part 5: Demo
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Service Comparison Demo")
    print("="*60)

    await service_comparison_demo()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Artifact Services")
    print("#"*70)
    print("""
    ARTIFACT SERVICE IMPLEMENTATIONS:
    ---------------------------------

    1. InMemoryArtifactService:
       - Storage: Python dict (RAM)
       - Persistence: None
       - Use for: Development, testing

    2. GcsArtifactService:
       - Storage: Google Cloud Storage
       - Persistence: Durable
       - Use for: Production

    RUNNER CONFIGURATION:
    ---------------------
    runner = Runner(
        agent=agent,
        app_name="my_app",
        session_service=session_service,
        artifact_service=artifact_service  # Required for artifacts!
    )

    KEY METHODS:
    ------------
    - save_artifact() → version number
    - load_artifact() → Part or None
    - list_artifact_keys() → filenames
    - list_versions() → version numbers
    - delete_artifact() → removes all versions

    VERSION HANDLING:
    -----------------
    - save_artifact() auto-increments version
    - load_artifact() gets latest by default
    - load_artifact(version=N) gets specific version
    - list_versions() shows all available

    SESSION ISOLATION:
    ------------------
    - Different sessions have separate artifact storage
    - Same filename in different sessions = different artifacts
    - Use "user:" prefix for cross-session access
    """)


if __name__ == "__main__":
    asyncio.run(main())
