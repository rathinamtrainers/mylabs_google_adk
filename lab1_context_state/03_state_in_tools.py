"""
Lab 1 - Exercise 3: State in Tools
===================================

This exercise demonstrates how to use state within tool functions:
1. Reading state in tools
2. Writing state in tools
3. Passing data between tools via state
4. Using temp: prefix for invocation-scoped data

Run: uv run python 03_state_in_tools.py
"""

import asyncio
import uuid
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Tool 1: Get User Profile (writes user_id to state)
# =============================================================================
def get_user_profile(tool_context: ToolContext) -> dict:
    """
    Simulates fetching a user profile.
    Saves the user_id to state so other tools can use it.
    """
    print("\n  [Tool: get_user_profile]")

    # Check if we already have a user_id in state
    existing_id = tool_context.state.get("temp:current_user_id")
    if existing_id:
        print(f"    Found existing user_id in state: {existing_id}")
        return {
            "status": "cached",
            "user_id": existing_id,
            "name": tool_context.state.get("user_name", "Unknown")
        }

    # Generate a new user_id
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    user_name = tool_context.state.get("user_name", "Demo User")

    # Save to temp: state for use by other tools in this invocation
    tool_context.state["temp:current_user_id"] = user_id
    tool_context.state["temp:profile_fetched"] = True

    print(f"    Generated new user_id: {user_id}")
    print(f"    Saved to state: temp:current_user_id = {user_id}")

    return {
        "status": "success",
        "user_id": user_id,
        "name": user_name
    }


# =============================================================================
# Tool 2: Get User Orders (reads user_id from state)
# =============================================================================
def get_user_orders(tool_context: ToolContext) -> dict:
    """
    Fetches orders for a user.
    Reads user_id from state (set by get_user_profile).
    """
    print("\n  [Tool: get_user_orders]")

    # Read user_id from state (set by get_user_profile)
    user_id = tool_context.state.get("temp:current_user_id")

    if not user_id:
        print("    ERROR: No user_id in state. Call get_user_profile first!")
        return {"error": "User profile not loaded. Please fetch profile first."}

    print(f"    Read user_id from state: {user_id}")

    # Simulate fetching orders
    orders = [
        {"order_id": "ORD-001", "item": "Laptop", "status": "shipped"},
        {"order_id": "ORD-002", "item": "Mouse", "status": "delivered"},
    ]

    # Save order count to session state (persists across invocations)
    total_orders = tool_context.state.get("total_orders_viewed", 0) + len(orders)
    tool_context.state["total_orders_viewed"] = total_orders

    print(f"    Found {len(orders)} orders")
    print(f"    Updated total_orders_viewed to: {total_orders}")

    return {
        "user_id": user_id,
        "orders": orders,
        "count": len(orders)
    }


# =============================================================================
# Tool 3: Add to Cart (reads/writes cart state)
# =============================================================================
def add_to_cart(item: str, quantity: int, tool_context: ToolContext) -> dict:
    """
    Adds an item to the shopping cart.
    Cart is stored in session state and persists across invocations.
    """
    print("\n  [Tool: add_to_cart]")

    # Read current cart from state (default to empty list)
    cart = tool_context.state.get("cart_items", [])
    # Ensure cart is a list (handle if it's None)
    if cart is None:
        cart = []

    # Add new item
    cart_item = {"item": item, "quantity": quantity}
    cart.append(cart_item)

    # Save updated cart back to state
    tool_context.state["cart_items"] = cart
    tool_context.state["cart_last_updated"] = "just now"

    print(f"    Added {quantity}x {item} to cart")
    print(f"    Cart now has {len(cart)} item(s)")

    return {
        "status": "added",
        "item": item,
        "quantity": quantity,
        "cart_size": len(cart)
    }


# =============================================================================
# Tool 4: View Cart (reads cart state)
# =============================================================================
def view_cart(tool_context: ToolContext) -> dict:
    """
    Views the current shopping cart.
    Demonstrates reading complex state (list of dicts).
    """
    print("\n  [Tool: view_cart]")

    cart = tool_context.state.get("cart_items", [])
    if cart is None:
        cart = []
    last_updated = tool_context.state.get("cart_last_updated", "never")

    print(f"    Cart has {len(cart)} item(s)")

    return {
        "items": cart,
        "total_items": len(cart),
        "last_updated": last_updated
    }


# =============================================================================
# Create tools
# =============================================================================
profile_tool = FunctionTool(func=get_user_profile)
orders_tool = FunctionTool(func=get_user_orders)
add_cart_tool = FunctionTool(func=add_to_cart)
view_cart_tool = FunctionTool(func=view_cart)


# =============================================================================
# Create Agent
# =============================================================================
shopping_agent = LlmAgent(
    name="ShoppingAssistant",
    model="gemini-2.0-flash",
    instruction="""You are a shopping assistant that helps users manage their orders and cart.

    Available tools:
    1. get_user_profile - Get user information (call this first to get user_id)
    2. get_user_orders - Get user's orders (requires profile to be loaded first)
    3. add_to_cart - Add items to shopping cart (requires item name and quantity)
    4. view_cart - View current cart contents

    IMPORTANT: When asked about orders, always call get_user_profile first to
    load the user_id, then call get_user_orders.

    Keep responses brief.""",
    tools=[profile_tool, orders_tool, add_cart_tool, view_cart_tool],
)


# =============================================================================
# Main demonstration
# =============================================================================
async def main():
    print("\n" + "#"*70)
    print("# Lab 1 Exercise 3: State in Tools")
    print("#"*70)

    session_service = InMemorySessionService()
    runner = Runner(
        agent=shopping_agent,
        app_name="shopping_demo",
        session_service=session_service,
    )

    # Create session with initial state
    session = await session_service.create_session(
        app_name="shopping_demo",
        user_id="demo_user",
        session_id="shopping_session",
        state={"user_name": "Alice"}
    )

    print("\n" + "="*60)
    print("Initial State:")
    print("="*60)
    print(f"  user_name: {session.state.get('user_name')}")

    # =========================================================================
    # Test 1: Profile and Orders (tool-to-tool data passing)
    # =========================================================================
    print("\n" + "="*60)
    print("TEST 1: Get user profile and orders")
    print("="*60)
    print("  This demonstrates passing data between tools via state")

    user_message = types.Content(
        parts=[types.Part(text="Show me my orders please")]
    )

    async for event in runner.run_async(
        user_id="demo_user",
        session_id="shopping_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Agent: {event.content.parts[0].text[:300]}...")

    session = await session_service.get_session(
        app_name="shopping_demo",
        user_id="demo_user",
        session_id="shopping_session"
    )
    print(f"\n  State after TEST 1:")
    print(f"    total_orders_viewed: {session.state.get('total_orders_viewed')}")
    print(f"    temp:current_user_id: {session.state.get('temp:current_user_id', 'not set (temp discarded)')}")

    # =========================================================================
    # Test 2: Shopping cart operations
    # =========================================================================
    print("\n" + "="*60)
    print("TEST 2: Add items to cart")
    print("="*60)

    user_message = types.Content(
        parts=[types.Part(text="Add 2 laptops to my cart")]
    )

    async for event in runner.run_async(
        user_id="demo_user",
        session_id="shopping_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Agent: {event.content.parts[0].text[:200]}...")

    session = await session_service.get_session(
        app_name="shopping_demo",
        user_id="demo_user",
        session_id="shopping_session"
    )
    print(f"\n  State after TEST 2:")
    print(f"    cart_items: {session.state.get('cart_items')}")

    # =========================================================================
    # Test 3: View cart (state persists across invocations)
    # =========================================================================
    print("\n" + "="*60)
    print("TEST 3: View cart (state persists)")
    print("="*60)

    user_message = types.Content(
        parts=[types.Part(text="What's in my cart?")]
    )

    async for event in runner.run_async(
        user_id="demo_user",
        session_id="shopping_session",
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            print(f"\n  Agent: {event.content.parts[0].text[:200]}...")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: State in Tools")
    print("#"*70)
    print("""
    KEY PATTERNS:
    -------------
    1. Reading state:
       value = tool_context.state.get("key", default_value)

    2. Writing state:
       tool_context.state["key"] = value

    3. Passing data between tools (same invocation):
       - Tool A: tool_context.state["temp:data"] = result
       - Tool B: data = tool_context.state.get("temp:data")
       - Use temp: prefix so it's cleaned up automatically

    4. Persisting data across invocations:
       - Use regular keys (no prefix) or user:/app: for broader scope
       - Example: tool_context.state["cart_items"] = [...]

    5. Complex state values:
       - Lists and dicts are supported
       - Must be JSON-serializable
       - Avoid custom class instances

    BEST PRACTICES:
    ---------------
    - Use temp: for intermediate data between tools
    - Use descriptive key names
    - Always provide defaults when reading: state.get("key", default)
    - Keep state values simple and serializable
    """)


if __name__ == "__main__":
    asyncio.run(main())
