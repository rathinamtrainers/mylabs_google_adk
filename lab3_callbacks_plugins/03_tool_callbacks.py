"""
Lab 3 - Exercise 3: Tool Callbacks
===================================

This exercise demonstrates before/after tool callbacks:
1. before_tool_callback - validate/modify tool arguments
2. after_tool_callback - transform tool results
3. Tool execution logging
4. Argument sanitization

Run: uv run python 03_tool_callbacks.py
"""

import asyncio
from typing import Optional, Dict, Any
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, BaseTool, ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Define sample tools
# =============================================================================

def get_weather(city: str) -> dict:
    """Get weather for a city."""
    weather_data = {
        "new york": {"temp": 72, "condition": "Sunny"},
        "london": {"temp": 58, "condition": "Cloudy"},
        "tokyo": {"temp": 68, "condition": "Clear"},
        "paris": {"temp": 65, "condition": "Partly Cloudy"},
    }
    city_lower = city.lower()
    if city_lower in weather_data:
        return {"city": city, **weather_data[city_lower]}
    return {"city": city, "temp": 70, "condition": "Unknown"}


def calculate(operation: str, a: float, b: float) -> dict:
    """Perform a calculation."""
    ops = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else "Error: Division by zero",
    }
    result = ops.get(operation, "Unknown operation")
    return {"operation": operation, "a": a, "b": b, "result": result}


def search_database(query: str, limit: int = 10) -> dict:
    """Search a mock database."""
    # Simulated search results
    results = [
        {"id": 1, "title": f"Result for '{query}' #1"},
        {"id": 2, "title": f"Result for '{query}' #2"},
        {"id": 3, "title": f"Result for '{query}' #3"},
    ]
    return {"query": query, "limit": limit, "results": results[:limit]}


weather_tool = FunctionTool(func=get_weather)
calc_tool = FunctionTool(func=calculate)
search_tool = FunctionTool(func=search_database)


# =============================================================================
# Part 1: Tool Logging Callback
# =============================================================================

def log_tool_call(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext
) -> Optional[Dict]:
    """
    Called BEFORE tool execution.

    Parameters:
        tool: The tool being called
        args: Arguments passed to the tool (can be modified in-place)
        tool_context: Tool execution context

    Returns:
        None - Execute tool normally
        dict - Skip tool and use this as result
    """
    print(f"    [before_tool] Tool: {tool.name}")
    print(f"    [before_tool] Args: {args}")
    return None  # Proceed with tool execution


def log_tool_result(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext,
    tool_response: Dict
) -> Optional[Dict]:
    """
    Called AFTER tool execution.

    Parameters:
        tool: The tool that was called
        args: Arguments that were passed
        tool_context: Tool execution context
        tool_response: Result from tool execution

    Returns:
        None - Use original result
        dict - Replace with modified result
    """
    print(f"    [after_tool] Tool: {tool.name}")
    print(f"    [after_tool] Result: {tool_response}")
    return None  # Use original result


# =============================================================================
# Part 2: Argument Validation
# =============================================================================

ALLOWED_CITIES = ["new york", "london", "tokyo", "paris", "berlin"]

def validate_city(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext
) -> Optional[Dict]:
    """Validate city argument for weather tool."""
    if tool.name != "get_weather":
        return None

    city = args.get("city", "").lower()
    if city not in ALLOWED_CITIES:
        print(f"    [VALIDATION] City '{city}' not in allowed list")
        return {
            "error": f"City '{args.get('city')}' is not supported.",
            "allowed_cities": ALLOWED_CITIES
        }

    print(f"    [VALIDATION] City '{city}' is valid")
    return None


# =============================================================================
# Part 3: Argument Modification
# =============================================================================

def sanitize_args(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext
) -> Optional[Dict]:
    """Sanitize and normalize tool arguments."""
    if tool.name == "get_weather":
        # Normalize city name
        if "city" in args:
            original = args["city"]
            args["city"] = args["city"].strip().title()
            print(f"    [SANITIZE] City: '{original}' -> '{args['city']}'")

    elif tool.name == "search_database":
        # Enforce maximum limit
        if args.get("limit", 0) > 5:
            original = args["limit"]
            args["limit"] = 5
            print(f"    [SANITIZE] Limit capped: {original} -> 5")

        # Sanitize query
        if "query" in args:
            args["query"] = args["query"].strip()

    return None  # Proceed with modified args


# =============================================================================
# Part 4: Result Transformation
# =============================================================================

def enhance_weather_result(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext,
    tool_response: Dict
) -> Optional[Dict]:
    """Add additional info to weather results."""
    if tool.name != "get_weather":
        return None

    # Add temperature in Celsius
    if "temp" in tool_response:
        fahrenheit = tool_response["temp"]
        celsius = round((fahrenheit - 32) * 5 / 9, 1)
        tool_response["temp_celsius"] = celsius
        tool_response["temp_fahrenheit"] = fahrenheit
        del tool_response["temp"]
        print(f"    [ENHANCE] Added Celsius: {celsius}°C")

    # Add timestamp
    from datetime import datetime
    tool_response["timestamp"] = datetime.now().isoformat()

    return tool_response


# =============================================================================
# Part 5: Tool Access Control
# =============================================================================

def check_tool_access(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext
) -> Optional[Dict]:
    """Control access to tools based on state."""
    # Check if user has premium access
    is_premium = tool_context.state.get("is_premium", False)

    if tool.name == "search_database" and not is_premium:
        print(f"    [ACCESS] Search blocked - user is not premium")
        return {
            "error": "Search is a premium feature.",
            "upgrade_url": "https://example.com/upgrade"
        }

    print(f"    [ACCESS] Tool '{tool.name}' access granted")
    return None


# =============================================================================
# Part 6: Tracking Tool Usage
# =============================================================================

tool_usage_count = {}

def track_tool_usage(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext,
    tool_response: Dict
) -> Optional[Dict]:
    """Track how often each tool is used."""
    global tool_usage_count

    if tool.name not in tool_usage_count:
        tool_usage_count[tool.name] = 0
    tool_usage_count[tool.name] += 1

    # Store in state for the agent to see
    tool_context.state[f"tool_calls:{tool.name}"] = tool_usage_count[tool.name]

    print(f"    [TRACK] {tool.name} called {tool_usage_count[tool.name]} times")
    return None


async def main():
    print("\n" + "#"*70)
    print("# Lab 3 Exercise 3: Tool Callbacks")
    print("#"*70)

    session_service = InMemorySessionService()

    # =========================================================================
    # Part 1: Tool Logging
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Tool Logging")
    print("="*60)

    agent1 = LlmAgent(
        name="LoggingAgent",
        model="gemini-2.0-flash",
        instruction="You help with weather and calculations. Use tools when needed.",
        tools=[weather_tool, calc_tool],
        before_tool_callback=log_tool_call,
        after_tool_callback=log_tool_result,
    )

    runner1 = Runner(
        agent=agent1,
        app_name="tool_callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="tool_callback_demo",
        user_id="user1",
        session_id="logging_session",
        state={}
    )

    print("\n  Message: 'What's the weather in Tokyo?'")
    user_message = types.Content(parts=[types.Part(text="What's the weather in Tokyo?")])
    async for event in runner1.run_async(
        user_id="user1",
        session_id="logging_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Response: {event.content.parts[0].text[:100]}...")

    # =========================================================================
    # Part 2: Argument Validation
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Argument Validation")
    print("="*60)

    agent2 = LlmAgent(
        name="ValidatingAgent",
        model="gemini-2.0-flash",
        instruction="You provide weather info. Use the weather tool.",
        tools=[weather_tool],
        before_tool_callback=validate_city,
    )

    runner2 = Runner(
        agent=agent2,
        app_name="tool_callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="tool_callback_demo",
        user_id="user1",
        session_id="validation_session",
        state={}
    )

    # Test with invalid city
    print("\n  Test: 'Weather in Sydney?' (not in allowed list)")
    user_message = types.Content(parts=[types.Part(text="What's the weather in Sydney?")])
    async for event in runner2.run_async(
        user_id="user1",
        session_id="validation_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:120]}...")

    # =========================================================================
    # Part 3: Argument Sanitization
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Argument Sanitization")
    print("="*60)

    agent3 = LlmAgent(
        name="SanitizingAgent",
        model="gemini-2.0-flash",
        instruction="You search a database. Use the search tool.",
        tools=[search_tool],
        before_tool_callback=sanitize_args,
    )

    runner3 = Runner(
        agent=agent3,
        app_name="tool_callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="tool_callback_demo",
        user_id="user1",
        session_id="sanitize_session",
        state={}
    )

    print("\n  Message: 'Search for Python tutorials, show me 20 results'")
    user_message = types.Content(
        parts=[types.Part(text="Search for Python tutorials, show me 20 results")]
    )
    async for event in runner3.run_async(
        user_id="user1",
        session_id="sanitize_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:150]}...")

    # =========================================================================
    # Part 4: Result Enhancement
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Result Enhancement")
    print("="*60)

    agent4 = LlmAgent(
        name="EnhancingAgent",
        model="gemini-2.0-flash",
        instruction="You provide weather. Include both Fahrenheit and Celsius.",
        tools=[weather_tool],
        after_tool_callback=enhance_weather_result,
    )

    runner4 = Runner(
        agent=agent4,
        app_name="tool_callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="tool_callback_demo",
        user_id="user1",
        session_id="enhance_session",
        state={}
    )

    print("\n  Message: 'Weather in London?'")
    user_message = types.Content(parts=[types.Part(text="Weather in London?")])
    async for event in runner4.run_async(
        user_id="user1",
        session_id="enhance_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:150]}...")

    # =========================================================================
    # Part 5: Access Control
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Tool Access Control")
    print("="*60)

    agent5 = LlmAgent(
        name="AccessAgent",
        model="gemini-2.0-flash",
        instruction="You help with weather and search. Use tools when needed.",
        tools=[weather_tool, search_tool],
        before_tool_callback=check_tool_access,
    )

    runner5 = Runner(
        agent=agent5,
        app_name="tool_callback_demo",
        session_service=session_service,
    )

    # Test as non-premium user
    await session_service.create_session(
        app_name="tool_callback_demo",
        user_id="user1",
        session_id="access_session",
        state={"is_premium": False}
    )

    print("\n  Test: Non-premium user tries to search")
    user_message = types.Content(parts=[types.Part(text="Search for machine learning")])
    async for event in runner5.run_async(
        user_id="user1",
        session_id="access_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"  Response: {event.content.parts[0].text[:120]}...")

    # =========================================================================
    # Part 6: Usage Tracking
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Tool Usage Tracking")
    print("="*60)

    global tool_usage_count
    tool_usage_count = {}  # Reset

    agent6 = LlmAgent(
        name="TrackingAgent",
        model="gemini-2.0-flash",
        instruction="You provide weather info. Use the weather tool.",
        tools=[weather_tool],
        after_tool_callback=track_tool_usage,
    )

    runner6 = Runner(
        agent=agent6,
        app_name="tool_callback_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="tool_callback_demo",
        user_id="user1",
        session_id="tracking_session",
        state={}
    )

    cities = ["New York", "Paris", "Tokyo"]
    print("\n  Making 3 weather queries...")
    for city in cities:
        user_message = types.Content(parts=[types.Part(text=f"Weather in {city}?")])
        async for event in runner6.run_async(
            user_id="user1",
            session_id="tracking_session",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                pass  # Just process

    session = await session_service.get_session(
        app_name="tool_callback_demo",
        user_id="user1",
        session_id="tracking_session"
    )
    print(f"\n  Tool usage stored in state: tool_calls:get_weather = {session.state.get('tool_calls:get_weather')}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Tool Callbacks")
    print("#"*70)
    print("""
    CALLBACK SIGNATURES:
    --------------------
    def before_tool_callback(
        tool: BaseTool,
        args: Dict[str, Any],
        tool_context: ToolContext
    ) -> Optional[Dict]:
        # Return None to proceed, or dict to skip tool

    def after_tool_callback(
        tool: BaseTool,
        args: Dict[str, Any],
        tool_context: ToolContext,
        tool_response: Dict
    ) -> Optional[Dict]:
        # Return None for original, or dict to replace

    TOOL CONTEXT PROPERTIES:
    ------------------------
    tool_context.state               # Session state (mutable)
    tool_context.agent_name          # Current agent name
    tool_context.function_call_id    # ID of the function call
    tool_context.actions             # Event actions

    USE CASES:
    ----------
    before_tool_callback:
    - Validate arguments
    - Sanitize input (strip, normalize)
    - Access control checks
    - Rate limiting
    - Logging tool calls

    after_tool_callback:
    - Transform/enhance results
    - Add metadata (timestamps, etc.)
    - Track usage statistics
    - Cache results
    - Log tool results

    ARGUMENT MODIFICATION:
    ----------------------
    # Modify args in-place (no return needed)
    args["limit"] = min(args["limit"], 10)
    return None  # Proceeds with modified args

    RESULT REPLACEMENT:
    -------------------
    # Return new dict to replace result
    tool_response["extra_field"] = "added"
    return tool_response  # Must return to replace

    KEY INSIGHT:
    ------------
    Tool callbacks give you control over every tool
    execution. Use them for:
    - Input validation and sanitization
    - Output transformation and enhancement
    - Access control and rate limiting
    - Logging and analytics
    """)


if __name__ == "__main__":
    asyncio.run(main())
