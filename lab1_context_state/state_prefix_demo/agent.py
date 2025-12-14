"""
Agent definition for state_prefix_demo
"""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, ToolContext


# =============================================================================
# Tool that demonstrates all state prefixes
# =============================================================================
def demonstrate_state_prefixes(action: str, tool_context: ToolContext) -> dict:
    """
    A tool that shows how different state prefixes work.

    State Prefixes:
    - No prefix: session.state['key'] - Session-specific
    - user: prefix: session.state['user:key'] - User-specific, across sessions
    - app: prefix: session.state['app:key'] - App-wide, all users
    - temp: prefix: session.state['temp:key'] - Current invocation only
    """
    if action == "write_all":
        # Read current values
        session_counter = tool_context.state.get("session_counter", 0)
        user_login = tool_context.state.get("user:login_count", 0)
        app_requests = tool_context.state.get("app:total_requests", 0)

        # Write to all state scopes
        tool_context.state["session_counter"] = session_counter + 1
        tool_context.state["user:preference"] = "dark_mode"
        tool_context.state["user:login_count"] = user_login + 1
        tool_context.state["app:total_requests"] = app_requests + 1
        tool_context.state["temp:request_id"] = "req_12345"
        tool_context.state["temp:processing"] = True

        return {
            "action": "write_all",
            "written": {
                "session_counter": session_counter + 1,
                "user:preference": "dark_mode",
                "user:login_count": user_login + 1,
                "app:total_requests": app_requests + 1,
                "temp:request_id": "req_12345",
            }
        }

    elif action == "read_all":
        return {
            "action": "read_all",
            "session_counter": tool_context.state.get("session_counter", "not set"),
            "user:preference": tool_context.state.get("user:preference", "not set"),
            "user:login_count": tool_context.state.get("user:login_count", "not set"),
            "app:total_requests": tool_context.state.get("app:total_requests", "not set"),
            "temp:request_id": tool_context.state.get("temp:request_id", "not set"),
        }

    return {"action": action, "status": "unknown action"}


state_tool = FunctionTool(func=demonstrate_state_prefixes)


# =============================================================================
# Agent - name matches the package folder name
# =============================================================================
root_agent = LlmAgent(
    name="state_prefix_demo",
    model="gemini-2.0-flash",
    instruction="""You are a state demonstration assistant.
    When asked to demonstrate state, use the demonstrate_state_prefixes tool.
    - Use action='write_all' to write to all state scopes
    - Use action='read_all' to read current state
    Just call the tool and report what happened.""",
    tools=[state_tool],
)
