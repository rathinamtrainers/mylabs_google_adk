"""
Lab 8 - Server: Math Agent
==========================

A standalone math agent exposed via A2A protocol.
Provides basic arithmetic operations.

Run: uv run python server/math_agent.py

The agent will be available at:
- A2A endpoint: http://localhost:8001/
- Agent card: http://localhost:8001/.well-known/agent-card.json
"""

import uvicorn
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a


# =============================================================================
# Math Tools
# =============================================================================

def add(a: float, b: float) -> float:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b
    """
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract b from a.

    Args:
        a: First number
        b: Number to subtract

    Returns:
        The difference (a - b)
    """
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        The product of a and b
    """
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b.

    Args:
        a: Numerator
        b: Denominator (must not be zero)

    Returns:
        The quotient (a / b)

    Raises:
        ValueError: If b is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


# =============================================================================
# Math Agent
# =============================================================================

math_agent = LlmAgent(
    name="MathAgent",
    model="gemini-2.0-flash",
    description="A math specialist that performs arithmetic calculations. "
                "Can add, subtract, multiply, and divide numbers.",
    instruction="""You are a math specialist agent.
    Use your tools to perform calculations:
    - add(a, b): Add two numbers
    - subtract(a, b): Subtract b from a
    - multiply(a, b): Multiply two numbers
    - divide(a, b): Divide a by b

    Always use tools for calculations - don't calculate in your head.
    Show the operation and result clearly.""",
    tools=[add, subtract, multiply, divide],
)


# =============================================================================
# A2A Server Setup
# =============================================================================

# Convert agent to A2A service
app = to_a2a(agent=math_agent, host="localhost", port=8001)


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Starting Math Agent A2A Server")
    print("=" * 50)
    print("\nEndpoints:")
    print("  A2A:        http://localhost:8001/")
    print("  Agent Card: http://localhost:8001/.well-known/agent-card.json")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)
