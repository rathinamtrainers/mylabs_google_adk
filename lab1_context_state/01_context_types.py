"""
Lab 1 - Exercise 1: Understanding Context Types
================================================

This exercise demonstrates the four context types in Google ADK:
1. InvocationContext - Full access in agent's core implementation
2. ReadonlyContext - Read-only access (e.g., in InstructionProvider)
3. CallbackContext - Used in agent/model callbacks
4. ToolContext - Used in tool functions and tool callbacks

Run: uv run python 01_context_types.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# Helper to safely display state (State object doesn't support dict() directly)
def show_state(state) -> str:
    """Convert state to a readable dict representation."""
    try:
        # Try to access known keys
        keys_to_check = [
            "user_name", "user:preferred_units", "agent_call_count",
            "model_call_count", "last_city_checked", "temp:tool_executed"
        ]
        result = {}
        for key in keys_to_check:
            try:
                val = state.get(key)
                if val is not None:
                    result[key] = val
            except:
                pass
        return str(result) if result else "(state access limited in this context)"
    except:
        return "(state not accessible)"


# =============================================================================
# 1. ToolContext - Available in tool functions
# =============================================================================
def get_weather(city: str, tool_context: ToolContext) -> dict:
    """
    A tool function that receives ToolContext.

    ToolContext provides:
    - state: Read/write access to session state
    - invocation_id: Current invocation identifier
    - agent_name: Name of the agent executing this tool
    - function_call_id: ID of the specific function call
    - load_artifact/save_artifact: Artifact management
    - list_artifacts: List available artifacts
    - search_memory: Search memory service (if configured)
    - request_credential/get_auth_response: Authentication handling
    """
    print("\n" + "="*60)
    print("TOOL CONTEXT (in tool function)")
    print("="*60)
    print(f"  invocation_id: {tool_context.invocation_id}")
    print(f"  agent_name: {tool_context.agent_name}")
    print(f"  function_call_id: {tool_context.function_call_id}")

    # Read from state
    user_name = tool_context.state.get("user_name", "Unknown")
    print(f"  state['user_name']: {user_name}")

    # Write to state - this is tracked automatically
    tool_context.state["last_city_checked"] = city
    tool_context.state["temp:tool_executed"] = True  # temp: prefix = invocation-only
    print(f"  Written: state['last_city_checked'] = {city}")
    print(f"  Written: state['temp:tool_executed'] = True")

    return {"city": city, "temperature": "22°C", "condition": "Sunny"}


weather_tool = FunctionTool(func=get_weather)


# =============================================================================
# 2. CallbackContext - Available in agent and model callbacks
# =============================================================================
def before_agent_callback(callback_context: CallbackContext) -> None:
    """
    Called before the agent runs.

    CallbackContext provides:
    - state: Read/write access to session state
    - invocation_id: Current invocation identifier
    - agent_name: Name of the agent
    - user_content: The initial user message
    - load_artifact/save_artifact: Artifact management
    """
    print("\n" + "="*60)
    print("CALLBACK CONTEXT (in before_agent_callback)")
    print("="*60)
    print(f"  invocation_id: {callback_context.invocation_id}")
    print(f"  agent_name: {callback_context.agent_name}")

    # Track how many times the agent has been called
    call_count = callback_context.state.get("agent_call_count", 0)
    callback_context.state["agent_call_count"] = call_count + 1
    print(f"  Read: agent_call_count was {call_count}")
    print(f"  Written: agent_call_count = {call_count + 1}")

    # Access user content
    if callback_context.user_content and callback_context.user_content.parts:
        user_text = callback_context.user_content.parts[0].text
        print(f"  user_content: '{user_text}'")

    return None  # Return None to continue normal execution


def after_agent_callback(callback_context: CallbackContext) -> None:
    """Called after the agent completes."""
    print("\n" + "="*60)
    print("CALLBACK CONTEXT (in after_agent_callback)")
    print("="*60)
    print(f"  Agent '{callback_context.agent_name}' completed")

    # Read some state values
    call_count = callback_context.state.get("agent_call_count", 0)
    model_calls = callback_context.state.get("model_call_count", 0)
    last_city = callback_context.state.get("last_city_checked", "N/A")
    print(f"  Final agent_call_count: {call_count}")
    print(f"  Final model_call_count: {model_calls}")
    print(f"  Final last_city_checked: {last_city}")
    return None


def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> LlmResponse | None:
    """
    Called before each LLM model call.

    Can inspect/modify the request or return a response to skip the model call.
    """
    print("\n" + "="*60)
    print("CALLBACK CONTEXT (in before_model_callback)")
    print("="*60)
    print(f"  invocation_id: {callback_context.invocation_id}")
    print(f"  Model being called with {len(llm_request.contents)} content(s)")

    # Track model calls
    model_calls = callback_context.state.get("model_call_count", 0)
    callback_context.state["model_call_count"] = model_calls + 1
    print(f"  Written: model_call_count = {model_calls + 1}")

    return None  # Return None to proceed with model call


def after_model_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> LlmResponse | None:
    """Called after each LLM model call."""
    print("\n" + "="*60)
    print("CALLBACK CONTEXT (in after_model_callback)")
    print("="*60)
    print(f"  Model response received")
    return None  # Return None to use the original response


# =============================================================================
# 3. ReadonlyContext - Available in InstructionProvider functions
# =============================================================================
def dynamic_instruction_provider(context: ReadonlyContext) -> str:
    """
    An InstructionProvider function that receives ReadonlyContext.

    ReadonlyContext provides:
    - invocation_id: Current invocation identifier
    - agent_name: Name of the agent
    - state: READ-ONLY view of session state (cannot modify!)
    """
    print("\n" + "="*60)
    print("READONLY CONTEXT (in InstructionProvider)")
    print("="*60)
    print(f"  invocation_id: {context.invocation_id}")
    print(f"  agent_name: {context.agent_name}")

    # Read from state to customize instructions
    user_name = context.state.get("user_name", "User")
    units = context.state.get("user:preferred_units", "celsius")
    print(f"  Read: user_name = {user_name}")
    print(f"  Read: user:preferred_units = {units}")

    # Note: Cannot write to state here - it's read-only!
    # context.state["key"] = "value"  # This would fail!

    return f"""You are a helpful weather assistant.
    The user's name is {user_name}.
    Always be friendly and provide accurate weather information.
    Use the get_weather tool when asked about weather.
    Report temperatures in {units}."""


# =============================================================================
# Create the Agent with all callbacks
# =============================================================================
weather_agent = LlmAgent(
    name="WeatherAgent",
    model="gemini-2.0-flash",
    instruction=dynamic_instruction_provider,  # Uses ReadonlyContext
    tools=[weather_tool],
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)


# =============================================================================
# Run the demonstration
# =============================================================================
async def main():
    print("\n" + "#"*70)
    print("# Lab 1 Exercise 1: Understanding Context Types")
    print("#"*70)

    # Setup
    session_service = InMemorySessionService()
    runner = Runner(
        agent=weather_agent,
        app_name="context_demo",
        session_service=session_service,
    )

    # Create session with initial state
    session = await session_service.create_session(
        app_name="context_demo",
        user_id="demo_user",
        session_id="session_001",
        state={
            "user_name": "Alice",
            "user:preferred_units": "celsius",  # user-scoped state
        }
    )

    print("\n" + "-"*60)
    print("Initial Session State:")
    print("-"*60)
    print(f"  user_name: {session.state.get('user_name')}")
    print(f"  user:preferred_units: {session.state.get('user:preferred_units')}")

    # Run the agent
    print("\n" + "-"*60)
    print("Running agent with: 'What is the weather in Paris?'")
    print("-"*60)

    user_message = types.Content(
        parts=[types.Part(text="What is the weather in Paris?")]
    )

    final_response = ""
    async for event in runner.run_async(
        user_id="demo_user",
        session_id="session_001",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            final_response = event.content.parts[0].text

    print("\n" + "-"*60)
    print("Agent Response:")
    print("-"*60)
    print(f"  {final_response[:300]}...")

    # Check final state
    updated_session = await session_service.get_session(
        app_name="context_demo",
        user_id="demo_user",
        session_id="session_001"
    )

    print("\n" + "-"*60)
    print("Final Session State:")
    print("-"*60)
    print(f"  user_name: {updated_session.state.get('user_name')}")
    print(f"  agent_call_count: {updated_session.state.get('agent_call_count')}")
    print(f"  model_call_count: {updated_session.state.get('model_call_count')}")
    print(f"  last_city_checked: {updated_session.state.get('last_city_checked')}")

    print("\n" + "#"*70)
    print("# Summary: Context Types")
    print("#"*70)
    print("""
    1. InvocationContext: Full access in agent's _run_async_impl
       - Most comprehensive, used internally by framework

    2. ReadonlyContext: Read-only state access
       - Used in InstructionProvider functions
       - Cannot modify state

    3. CallbackContext: Read/write in callbacks
       - Used in before/after agent/model callbacks
       - Can modify state, access artifacts

    4. ToolContext: Full tool capabilities
       - Used in tool functions
       - State, artifacts, memory, authentication
       - Has function_call_id for linking operations
    """)


if __name__ == "__main__":
    asyncio.run(main())
