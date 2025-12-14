"""
Lab 5 - Exercise 3: Trajectory Evaluation
==========================================

This exercise covers tool trajectory evaluation:
1. What is trajectory evaluation?
2. Match types: EXACT, IN_ORDER, ANY_ORDER
3. Evaluating tool arguments
4. Common trajectory patterns
5. Debugging trajectory failures

Run: uv run python 03_trajectory_evaluation.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Part 1: Understanding Trajectory Evaluation
# =============================================================================

def explain_trajectory_evaluation():
    """Explain trajectory evaluation concepts."""
    print("""
    TRAJECTORY EVALUATION OVERVIEW
    ==============================

    Trajectory = The sequence of tools an agent calls to complete a task

    WHY EVALUATE TRAJECTORY?
    ------------------------
    - Ensures agent follows expected workflow
    - Validates correct tool selection
    - Checks parameter accuracy
    - Identifies inefficient paths

    EXAMPLE TRAJECTORY:
    -------------------
    User: "What's the weather in NYC and convert it to Celsius?"

    Expected trajectory:
    1. get_weather(city="New York") -> 72°F
    2. fahrenheit_to_celsius(temp=72) -> 22°C

    Actual trajectory (evaluated against expected):
    1. get_weather(city="NYC")              # Tool name matches
    2. fahrenheit_to_celsius(temp=72)       # Tool + args match

    WHAT IS EVALUATED:
    ------------------
    ┌────────────────────────────────────────────────────────────┐
    │  Aspect           │  Checked?  │  Notes                   │
    ├────────────────────────────────────────────────────────────┤
    │  Tool name        │  Yes       │  Must match exactly      │
    │  Tool arguments   │  Yes       │  Key-value pairs match   │
    │  Tool order       │  Depends   │  Based on match_type     │
    │  Extra tools      │  Depends   │  Based on match_type     │
    │  Tool response    │  No        │  Only inputs matter      │
    └────────────────────────────────────────────────────────────┘
    """)


# =============================================================================
# Part 2: Match Types Explained
# =============================================================================

def explain_match_types():
    """Explain the three trajectory match types."""
    print("""
    TRAJECTORY MATCH TYPES
    ======================

    1. EXACT (Default, strictest)
    -----------------------------
    - All expected tools must be called
    - In the exact order specified
    - With the exact arguments
    - NO extra tools allowed

    Expected: [tool_a(x=1), tool_b(y=2)]
    Actual:   [tool_a(x=1), tool_b(y=2)]      ✓ PASS
    Actual:   [tool_a(x=1), tool_c(), tool_b(y=2)]  ✗ FAIL (extra tool)
    Actual:   [tool_b(y=2), tool_a(x=1)]      ✗ FAIL (wrong order)


    2. IN_ORDER (Medium strictness)
    -------------------------------
    - All expected tools must be called
    - In the specified order
    - With matching arguments
    - Extra tools between expected ones are OK

    Expected: [tool_a(x=1), tool_b(y=2)]
    Actual:   [tool_a(x=1), tool_b(y=2)]      ✓ PASS
    Actual:   [tool_a(x=1), tool_c(), tool_b(y=2)]  ✓ PASS (extra OK)
    Actual:   [tool_b(y=2), tool_a(x=1)]      ✗ FAIL (wrong order)


    3. ANY_ORDER (Most flexible)
    ----------------------------
    - All expected tools must be called
    - Order doesn't matter
    - With matching arguments
    - Extra tools are OK

    Expected: [tool_a(x=1), tool_b(y=2)]
    Actual:   [tool_a(x=1), tool_b(y=2)]      ✓ PASS
    Actual:   [tool_b(y=2), tool_a(x=1)]      ✓ PASS (order OK)
    Actual:   [tool_a(x=1), tool_c(), tool_b(y=2)]  ✓ PASS (extra OK)
    Actual:   [tool_a(x=1)]                   ✗ FAIL (missing tool_b)


    WHEN TO USE EACH:
    -----------------
    ┌────────────────────────────────────────────────────────────┐
    │  Use Case                        │  Match Type             │
    ├────────────────────────────────────────────────────────────┤
    │  Strict workflows (payments)     │  EXACT                  │
    │  Ordered pipelines               │  IN_ORDER               │
    │  Flexible tool gathering         │  ANY_ORDER              │
    │  Regression testing              │  EXACT                  │
    │  Multiple search queries         │  ANY_ORDER              │
    └────────────────────────────────────────────────────────────┘
    """)


# =============================================================================
# Part 3: Sample Agent with Multiple Tools
# =============================================================================

# Simulated data sources
def search_products(query: str, category: str = "") -> dict:
    """Search for products."""
    products = {
        "laptop": [
            {"id": "P001", "name": "Pro Laptop", "price": 1299},
            {"id": "P002", "name": "Budget Laptop", "price": 499},
        ],
        "phone": [
            {"id": "P003", "name": "Smart Phone X", "price": 999},
        ],
    }

    results = []
    for cat, items in products.items():
        if not category or cat == category.lower():
            for item in items:
                if query.lower() in item["name"].lower():
                    results.append(item)

    return {"products": results if results else "No products found"}


def get_product_details(product_id: str) -> dict:
    """Get detailed product information."""
    details = {
        "P001": {"id": "P001", "name": "Pro Laptop", "price": 1299, "specs": "16GB RAM, 512GB SSD"},
        "P002": {"id": "P002", "name": "Budget Laptop", "price": 499, "specs": "8GB RAM, 256GB SSD"},
        "P003": {"id": "P003", "name": "Smart Phone X", "price": 999, "specs": "6.5 inch, 128GB"},
    }
    return details.get(product_id, {"error": "Product not found"})


def check_inventory(product_id: str) -> dict:
    """Check product inventory."""
    inventory = {
        "P001": {"in_stock": True, "quantity": 15},
        "P002": {"in_stock": True, "quantity": 42},
        "P003": {"in_stock": False, "quantity": 0},
    }
    return inventory.get(product_id, {"error": "Product not found"})


def add_to_cart(product_id: str, quantity: int = 1) -> dict:
    """Add product to shopping cart."""
    return {"success": True, "message": f"Added {quantity} of {product_id} to cart"}


def create_shopping_agent():
    """Create a shopping assistant agent."""
    search_tool = FunctionTool(func=search_products)
    details_tool = FunctionTool(func=get_product_details)
    inventory_tool = FunctionTool(func=check_inventory)
    cart_tool = FunctionTool(func=add_to_cart)

    agent = LlmAgent(
        name="ShoppingAgent",
        model="gemini-2.0-flash",
        instruction="""You are a shopping assistant.
        Help customers find and purchase products.

        Workflow for product inquiries:
        1. Search for products using search_products
        2. Get details with get_product_details
        3. Check availability with check_inventory

        For purchases:
        1. First check inventory
        2. Then add to cart

        Always check inventory before adding to cart.""",
        tools=[search_tool, details_tool, inventory_tool, cart_tool],
    )

    return agent


# =============================================================================
# Part 4: Trajectory Matching Simulation
# =============================================================================

def simulate_trajectory_matching():
    """Simulate trajectory matching with different match types."""
    print("\n  Simulating trajectory matching:")
    print("  " + "-"*50)

    # Define expected trajectory
    expected = [
        {"name": "search_products", "args": {"query": "laptop"}},
        {"name": "get_product_details", "args": {"product_id": "P001"}},
        {"name": "check_inventory", "args": {"product_id": "P001"}},
    ]

    # Different actual trajectories to test
    test_cases = [
        {
            "name": "Exact match",
            "actual": [
                {"name": "search_products", "args": {"query": "laptop"}},
                {"name": "get_product_details", "args": {"product_id": "P001"}},
                {"name": "check_inventory", "args": {"product_id": "P001"}},
            ],
        },
        {
            "name": "Extra tool in between",
            "actual": [
                {"name": "search_products", "args": {"query": "laptop"}},
                {"name": "search_products", "args": {"query": "gaming laptop"}},  # Extra
                {"name": "get_product_details", "args": {"product_id": "P001"}},
                {"name": "check_inventory", "args": {"product_id": "P001"}},
            ],
        },
        {
            "name": "Wrong order",
            "actual": [
                {"name": "search_products", "args": {"query": "laptop"}},
                {"name": "check_inventory", "args": {"product_id": "P001"}},  # Swapped
                {"name": "get_product_details", "args": {"product_id": "P001"}},
            ],
        },
        {
            "name": "Missing tool",
            "actual": [
                {"name": "search_products", "args": {"query": "laptop"}},
                {"name": "check_inventory", "args": {"product_id": "P001"}},
            ],
        },
        {
            "name": "Wrong argument",
            "actual": [
                {"name": "search_products", "args": {"query": "phone"}},  # Wrong query
                {"name": "get_product_details", "args": {"product_id": "P001"}},
                {"name": "check_inventory", "args": {"product_id": "P001"}},
            ],
        },
    ]

    # Evaluate each case with different match types
    for case in test_cases:
        print(f"\n  Case: {case['name']}")
        print(f"    Actual: {[t['name'] for t in case['actual']]}")

        # Simulate match type results
        exact_result = evaluate_trajectory(expected, case['actual'], 'EXACT')
        in_order_result = evaluate_trajectory(expected, case['actual'], 'IN_ORDER')
        any_order_result = evaluate_trajectory(expected, case['actual'], 'ANY_ORDER')

        print(f"    EXACT: {'PASS' if exact_result else 'FAIL'}")
        print(f"    IN_ORDER: {'PASS' if in_order_result else 'FAIL'}")
        print(f"    ANY_ORDER: {'PASS' if any_order_result else 'FAIL'}")


def evaluate_trajectory(expected: list, actual: list, match_type: str) -> bool:
    """Simulate trajectory evaluation logic."""

    def tools_match(exp, act):
        """Check if two tool calls match (name and args)."""
        if exp['name'] != act['name']:
            return False
        # Check args match (simplified - just key matching)
        for key, value in exp['args'].items():
            if key not in act['args'] or act['args'][key] != value:
                return False
        return True

    if match_type == 'EXACT':
        # Must be exact match: same tools, same order, no extras
        if len(expected) != len(actual):
            return False
        for exp, act in zip(expected, actual):
            if not tools_match(exp, act):
                return False
        return True

    elif match_type == 'IN_ORDER':
        # Expected tools must appear in order, extras allowed
        exp_idx = 0
        for act in actual:
            if exp_idx < len(expected) and tools_match(expected[exp_idx], act):
                exp_idx += 1
        return exp_idx == len(expected)

    elif match_type == 'ANY_ORDER':
        # All expected tools must appear, any order, extras allowed
        matched = [False] * len(expected)
        for act in actual:
            for i, exp in enumerate(expected):
                if not matched[i] and tools_match(exp, act):
                    matched[i] = True
                    break
        return all(matched)

    return False


# =============================================================================
# Part 5: Running Agent and Capturing Trajectory
# =============================================================================

async def run_and_capture_trajectory():
    """Run the shopping agent and capture its trajectory."""
    print("\n  Running shopping agent to capture trajectory...")

    agent = create_shopping_agent()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=agent,
        app_name="shopping_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="shopping_demo",
        user_id="user1",
        session_id="shopping_session",
        state={}
    )

    query = "Find me a laptop and check if the Pro Laptop is in stock"
    print(f"\n  Query: '{query}'")

    user_message = types.Content(parts=[types.Part(text=query)])

    tool_calls = []
    final_response = ""

    async for event in runner.run_async(
        user_id="user1",
        session_id="shopping_session",
        new_message=user_message,
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    call_info = {
                        "name": part.function_call.name,
                        "args": dict(part.function_call.args) if part.function_call.args else {}
                    }
                    tool_calls.append(call_info)
                    print(f"    Tool called: {call_info['name']}({call_info['args']})")

        if event.is_final_response() and event.content:
            final_response = event.content.parts[0].text

    print(f"\n  Final response: {final_response[:150]}...")
    print(f"\n  Captured trajectory: {len(tool_calls)} tool calls")

    return tool_calls


# =============================================================================
# Part 6: Configuration Examples
# =============================================================================

def show_configuration_examples():
    """Show trajectory evaluation configuration examples."""
    print("""
    TRAJECTORY EVALUATION CONFIGURATION
    ====================================

    Basic (EXACT match, default):
    -----------------------------
    {
      "criteria": {
        "tool_trajectory_avg_score": 1.0
      }
    }

    Explicit EXACT match:
    ---------------------
    {
      "criteria": {
        "tool_trajectory_avg_score": {
          "threshold": 1.0,
          "match_type": "EXACT"
        }
      }
    }

    IN_ORDER match (allows extras):
    --------------------------------
    {
      "criteria": {
        "tool_trajectory_avg_score": {
          "threshold": 1.0,
          "match_type": "IN_ORDER"
        }
      }
    }

    ANY_ORDER match (flexible):
    ---------------------------
    {
      "criteria": {
        "tool_trajectory_avg_score": {
          "threshold": 1.0,
          "match_type": "ANY_ORDER"
        }
      }
    }

    Combined with response:
    -----------------------
    {
      "criteria": {
        "tool_trajectory_avg_score": {
          "threshold": 0.9,
          "match_type": "IN_ORDER"
        },
        "response_match_score": 0.8
      }
    }

    TEST FILE TRAJECTORY FORMAT:
    ----------------------------
    {
      "intermediate_data": {
        "tool_uses": [
          {
            "name": "search_products",
            "args": {"query": "laptop"}
          },
          {
            "name": "get_product_details",
            "args": {"product_id": "P001"}
          }
        ]
      }
    }
    """)


# =============================================================================
# Part 7: Debugging Tips
# =============================================================================

def show_debugging_tips():
    """Show tips for debugging trajectory evaluation failures."""
    print("""
    DEBUGGING TRAJECTORY FAILURES
    =============================

    1. TOOL NAME MISMATCH:
       -------------------
       Expected: "get_weather"
       Actual:   "getWeather"
       Solution: Check exact tool function names

    2. ARGUMENT MISMATCH:
       ------------------
       Expected: {"city": "New York"}
       Actual:   {"city": "NYC"}
       Solution: Update expected args or normalize in tool

    3. MISSING TOOLS:
       ---------------
       Expected: [search, details, inventory]
       Actual:   [search, inventory]  # Missing details
       Solution: Check agent instruction, may need clarification

    4. EXTRA TOOLS:
       ------------
       Expected: [search]
       Actual:   [search, search, search]  # Retries
       Solution: Use IN_ORDER or ANY_ORDER if retries OK

    5. WRONG ORDER:
       -------------
       Expected: [check_inventory, add_to_cart]
       Actual:   [add_to_cart, check_inventory]
       Solution: Check agent instruction for workflow clarity

    DEBUGGING COMMANDS:
    -------------------
    # Run with detailed output
    adk eval my_agent tests/ --print_detailed_results

    # Use pytest for better debugging
    pytest tests/ -v --tb=long

    TIPS:
    -----
    - Start with ANY_ORDER, then tighten to IN_ORDER or EXACT
    - Log tool calls during development
    - Use descriptive tool function names
    - Keep expected trajectories minimal (core tools only)
    """)


async def main():
    print("\n" + "#"*70)
    print("# Lab 5 Exercise 3: Trajectory Evaluation")
    print("#"*70)

    # =========================================================================
    # Part 1: Overview
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Understanding Trajectory Evaluation")
    print("="*60)
    explain_trajectory_evaluation()

    # =========================================================================
    # Part 2: Match Types
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Match Types Explained")
    print("="*60)
    explain_match_types()

    # =========================================================================
    # Part 3: Sample Agent
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Sample Shopping Agent")
    print("="*60)

    agent = create_shopping_agent()
    print(f"  Agent: {agent.name}")
    print(f"  Tools: {[t.name for t in agent.tools]}")

    # =========================================================================
    # Part 4: Matching Simulation
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Trajectory Matching Simulation")
    print("="*60)

    simulate_trajectory_matching()

    # =========================================================================
    # Part 5: Live Trajectory Capture
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Running Agent & Capturing Trajectory")
    print("="*60)

    trajectory = await run_and_capture_trajectory()

    # =========================================================================
    # Part 6: Configuration
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Configuration Examples")
    print("="*60)
    show_configuration_examples()

    # =========================================================================
    # Part 7: Debugging
    # =========================================================================
    print("\n" + "="*60)
    print("PART 7: Debugging Tips")
    print("="*60)
    show_debugging_tips()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Trajectory Evaluation")
    print("#"*70)
    print("""
    TRAJECTORY EVALUATION:
    ----------------------
    Evaluates the sequence of tools an agent calls

    MATCH TYPES:
    ------------
    - EXACT: Perfect match (default, strictest)
    - IN_ORDER: Same order, extras allowed
    - ANY_ORDER: All present, any order

    CONFIGURATION:
    --------------
    {
      "criteria": {
        "tool_trajectory_avg_score": {
          "threshold": 1.0,
          "match_type": "EXACT"  // or "IN_ORDER" or "ANY_ORDER"
        }
      }
    }

    TEST FILE FORMAT:
    -----------------
    {
      "intermediate_data": {
        "tool_uses": [
          {"name": "tool_name", "args": {"key": "value"}}
        ]
      }
    }

    KEY TAKEAWAYS:
    --------------
    - Trajectory = sequence of tool calls
    - Choose match type based on workflow strictness
    - EXACT for critical workflows
    - ANY_ORDER for flexible tool gathering
    - Check both tool names AND arguments
    """)


if __name__ == "__main__":
    asyncio.run(main())
