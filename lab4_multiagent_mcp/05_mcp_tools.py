"""
Lab 4 - Exercise 5: MCP Tools
==============================

This exercise demonstrates Model Context Protocol integration:
1. Understanding MCP architecture
2. MCP concepts (servers, tools, resources)
3. How ADK integrates with MCP
4. Practical MCP usage patterns

Note: This exercise is primarily educational. Running actual MCP servers
requires additional setup (Node.js, MCP server packages).

Run: uv run python 05_mcp_tools.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Part 1: Understanding MCP
# =============================================================================

def explain_mcp():
    """Explain MCP concepts."""
    print("""
    WHAT IS MCP (Model Context Protocol)?
    ======================================

    MCP is an OPEN STANDARD that defines how LLMs communicate with:
    - External applications
    - Data sources
    - Tools and services

    Think of MCP as a "universal adapter" between AI and external systems.

    MCP ARCHITECTURE:
    -----------------

    ┌─────────────┐     MCP Protocol      ┌─────────────┐
    │  MCP Client │◄────────────────────►│  MCP Server │
    │  (ADK/LLM)  │                       │  (Tools)    │
    └─────────────┘                       └─────────────┘

    MCP Client: Your ADK agent
    MCP Server: External service exposing tools

    MCP COMPONENTS:
    ---------------
    1. TOOLS    - Functions the LLM can call
    2. RESOURCES - Data the LLM can access
    3. PROMPTS   - Templates for common interactions

    EXAMPLE MCP SERVERS:
    --------------------
    - @modelcontextprotocol/server-filesystem  (File operations)
    - @modelcontextprotocol/server-github      (GitHub API)
    - @modelcontextprotocol/server-postgres    (Database queries)
    - @modelcontextprotocol/server-google-maps (Maps & directions)
    """)


# =============================================================================
# Part 2: ADK + MCP Integration
# =============================================================================

def explain_adk_mcp_integration():
    """Explain how ADK integrates with MCP."""
    print("""
    ADK + MCP INTEGRATION:
    ======================

    ADK provides McpToolset to connect to MCP servers:

    ```python
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from mcp import StdioServerParameters

    # Create MCP toolset
    mcp_tools = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command='npx',
                args=['-y', '@modelcontextprotocol/server-filesystem', '/path'],
            ),
        ),
        # Optional: filter specific tools
        # tool_filter=['read_file', 'write_file']
    )

    # Use in agent
    agent = LlmAgent(
        name="FileAgent",
        model="gemini-2.0-flash",
        instruction="Help manage files.",
        tools=[mcp_tools]  # MCP tools act like regular tools!
    )
    ```

    HOW IT WORKS:
    -------------
    1. McpToolset connects to MCP server via stdio
    2. Server exposes available tools
    3. ADK wraps MCP tools as ADK tools
    4. Agent uses them like any other tool

    CONNECTION TYPES:
    -----------------
    - StdioConnectionParams: Local process (most common)
    - SSEConnectionParams: Server-Sent Events (remote)
    """)


# =============================================================================
# Part 3: MCP Server Examples
# =============================================================================

def show_mcp_examples():
    """Show examples of MCP server configurations."""
    print("""
    EXAMPLE 1: Filesystem Server
    ============================
    Access local files (read, write, list directories)

    ```python
    import os
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from mcp import StdioServerParameters

    filesystem_tools = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command='npx',
                args=[
                    '-y',
                    '@modelcontextprotocol/server-filesystem',
                    '/home/user/documents',  # Allowed path
                ],
            ),
        ),
    )

    agent = LlmAgent(
        name="FileManager",
        model="gemini-2.0-flash",
        instruction="Help manage files in the documents folder.",
        tools=[filesystem_tools]
    )
    ```

    Available tools:
    - list_directory: List files in a directory
    - read_file: Read file contents
    - write_file: Write to a file
    - create_directory: Create new directories


    EXAMPLE 2: GitHub Server
    ========================
    Interact with GitHub repositories

    ```python
    github_tools = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command='npx',
                args=['-y', '@modelcontextprotocol/server-github'],
                env={
                    'GITHUB_PERSONAL_ACCESS_TOKEN': os.environ['GITHUB_TOKEN']
                }
            ),
        ),
    )

    agent = LlmAgent(
        name="GitHubAssistant",
        model="gemini-2.0-flash",
        instruction="Help with GitHub operations.",
        tools=[github_tools]
    )
    ```

    Available tools:
    - create_repository
    - search_repositories
    - get_file_contents
    - create_or_update_file
    - create_issue
    - list_issues


    EXAMPLE 3: Google Maps Server
    =============================
    Get directions and place information

    ```python
    maps_tools = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command='npx',
                args=['-y', '@modelcontextprotocol/server-google-maps'],
                env={
                    'GOOGLE_MAPS_API_KEY': os.environ['MAPS_KEY']
                }
            ),
        ),
    )

    agent = LlmAgent(
        name="MapsAssistant",
        model="gemini-2.0-flash",
        instruction="Help with directions and finding places.",
        tools=[maps_tools]
    )
    ```


    EXAMPLE 4: PostgreSQL Server
    ============================
    Query databases directly

    ```python
    db_tools = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command='npx',
                args=['-y', '@modelcontextprotocol/server-postgres'],
                env={
                    'POSTGRES_CONNECTION_STRING': 'postgresql://user:pass@localhost/db'
                }
            ),
        ),
    )

    agent = LlmAgent(
        name="DatabaseAssistant",
        model="gemini-2.0-flash",
        instruction="Help query the database.",
        tools=[db_tools]
    )
    ```
    """)


# =============================================================================
# Part 4: Building ADK Tools for MCP
# =============================================================================

def show_adk_to_mcp():
    """Show how to expose ADK tools via MCP."""
    print("""
    EXPOSING ADK TOOLS VIA MCP:
    ===========================

    You can also create an MCP server that exposes ADK tools!
    This lets non-ADK MCP clients use your ADK tools.

    ```python
    # my_mcp_server.py
    import asyncio
    from mcp import types as mcp_types
    from mcp.server.lowlevel import Server
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio

    from google.adk.tools.function_tool import FunctionTool
    from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

    # Your ADK tool
    def calculate(expression: str) -> dict:
        '''Evaluate a math expression.'''
        result = eval(expression)  # Simple example
        return {"result": result}

    adk_tool = FunctionTool(calculate)

    # MCP Server
    app = Server("my-adk-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[mcp_types.Tool]:
        # Convert ADK tool to MCP format
        mcp_tool = adk_to_mcp_tool_type(adk_tool)
        return [mcp_tool]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == adk_tool.name:
            result = await adk_tool.run_async(args=arguments, tool_context=None)
            return [mcp_types.TextContent(type="text", text=str(result))]
        return [mcp_types.TextContent(type="text", text="Tool not found")]

    async def main():
        async with mcp.server.stdio.stdio_server() as (read, write):
            await app.run(read, write, InitializationOptions(...))

    asyncio.run(main())
    ```

    KEY CONVERSION:
    ---------------
    from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

    # Converts ADK tool schema to MCP tool schema
    mcp_schema = adk_to_mcp_tool_type(adk_tool)
    """)


# =============================================================================
# Part 5: MCP Toolbox for Databases
# =============================================================================

def show_mcp_toolbox():
    """Show MCP Toolbox for production database access."""
    print("""
    MCP TOOLBOX (Production-Ready):
    ===============================

    Google's MCP Toolbox provides secure, production-ready tools
    for accessing various data sources.

    Repository: https://github.com/googleapis/genai-toolbox

    SUPPORTED DATA SOURCES:
    -----------------------

    Google Cloud:
    - BigQuery
    - AlloyDB
    - Spanner
    - Cloud SQL
    - Firestore
    - Bigtable
    - Dataplex
    - Cloud Monitoring

    Relational Databases:
    - PostgreSQL
    - MySQL
    - SQL Server
    - SQLite
    - ClickHouse

    NoSQL:
    - MongoDB
    - Redis
    - Cassandra
    - Couchbase

    Graph Databases:
    - Neo4j
    - Dgraph

    Other:
    - Looker
    - HTTP APIs

    USAGE:
    ------
    1. Install: pip install genai-toolbox
    2. Configure data source connections
    3. Run toolbox server
    4. Connect ADK agent to toolbox via MCP
    """)


# =============================================================================
# Simulated MCP-like Tool Demo
# =============================================================================

# Since actual MCP requires Node.js setup, we'll simulate the concept
# using regular ADK tools that behave like MCP tools would

def simulated_file_read(filepath: str) -> dict:
    """Simulated file read (like MCP filesystem server would provide)."""
    # In real MCP, this would read actual files
    simulated_files = {
        "/docs/readme.txt": "Welcome to our project! This is the documentation.",
        "/docs/config.json": '{"debug": true, "version": "1.0"}',
        "/src/main.py": "print('Hello from main.py')",
    }
    content = simulated_files.get(filepath, f"File not found: {filepath}")
    return {"filepath": filepath, "content": content}


def simulated_file_list(directory: str) -> dict:
    """Simulated directory listing."""
    simulated_dirs = {
        "/docs": ["readme.txt", "config.json"],
        "/src": ["main.py", "utils.py", "tests/"],
        "/": ["docs/", "src/", "README.md"],
    }
    files = simulated_dirs.get(directory, [])
    return {"directory": directory, "files": files}


def simulated_search(query: str, directory: str = "/") -> dict:
    """Simulated file search."""
    # Simulate searching for files
    results = []
    if "readme" in query.lower():
        results.append("/docs/readme.txt")
    if "config" in query.lower():
        results.append("/docs/config.json")
    if "main" in query.lower():
        results.append("/src/main.py")
    return {"query": query, "directory": directory, "matches": results}


async def main():
    print("\n" + "#"*70)
    print("# Lab 4 Exercise 5: MCP Tools")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Part 1: Understanding MCP
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Understanding MCP")
    print("="*60)
    explain_mcp()

    # =========================================================================
    # Part 2: ADK + MCP Integration
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: ADK + MCP Integration")
    print("="*60)
    explain_adk_mcp_integration()

    # =========================================================================
    # Part 3: MCP Server Examples
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: MCP Server Examples")
    print("="*60)
    show_mcp_examples()

    # =========================================================================
    # Part 4: Building ADK Tools for MCP
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Exposing ADK Tools via MCP")
    print("="*60)
    show_adk_to_mcp()

    # =========================================================================
    # Part 5: MCP Toolbox
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: MCP Toolbox for Databases")
    print("="*60)
    show_mcp_toolbox()

    # =========================================================================
    # Part 6: Simulated MCP Demo
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Simulated MCP-like Demo")
    print("="*60)
    print("  (Simulating what MCP tools would do)")

    # Create tools that simulate MCP behavior
    file_read_tool = FunctionTool(func=simulated_file_read)
    file_list_tool = FunctionTool(func=simulated_file_list)
    search_tool = FunctionTool(func=simulated_search)

    # Agent with "MCP-like" tools
    file_agent = LlmAgent(
        name="FileAssistant",
        model="gemini-2.0-flash",
        instruction="""You are a file assistant with access to filesystem tools.

        You can:
        - List files in directories using simulated_file_list
        - Read file contents using simulated_file_read
        - Search for files using simulated_search

        Help users navigate and read files.""",
        tools=[file_read_tool, file_list_tool, search_tool],
    )

    runner = Runner(
        agent=file_agent,
        app_name="mcp_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="mcp_demo",
        user_id="user1",
        session_id="mcp_session",
        state={}
    )

    # Test the simulated MCP tools
    test_queries = [
        "List files in /docs",
        "Read the readme file from /docs",
        "Search for files containing 'config'",
    ]

    for query in test_queries:
        print(f"\n  User: {query}")
        user_message = types.Content(parts=[types.Part(text=query)])

        async for event in runner.run_async(
            user_id="user1",
            session_id="mcp_session",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                print(f"  Agent: {event.content.parts[0].text[:150]}...")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: MCP Tools")
    print("#"*70)
    print("""
    WHAT IS MCP:
    ------------
    - Open standard for LLM <-> External tool communication
    - Client-server architecture
    - Exposes Tools, Resources, and Prompts

    ADK + MCP:
    ----------
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams

    mcp_tools = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command='npx',
                args=['-y', '@modelcontextprotocol/server-NAME', ...],
            ),
        ),
    )

    agent = LlmAgent(tools=[mcp_tools])

    POPULAR MCP SERVERS:
    --------------------
    - server-filesystem   (File operations)
    - server-github       (GitHub API)
    - server-postgres     (PostgreSQL)
    - server-google-maps  (Maps & directions)
    - server-brave-search (Web search)

    WHEN TO USE MCP:
    ----------------
    - Access external systems (files, databases, APIs)
    - Leverage existing MCP servers
    - Share tools across different LLM platforms
    - Build reusable tool libraries

    ALTERNATIVES:
    -------------
    - Use FunctionTool for simple custom tools
    - Use AgentTool for agent-as-tool patterns
    - MCP is best for external integrations

    SETUP REQUIREMENTS:
    -------------------
    - Node.js (for npx command)
    - MCP server packages (npm install)
    - Environment variables for API keys
    - Proper path permissions for filesystem
    """)


if __name__ == "__main__":
    asyncio.run(main())
