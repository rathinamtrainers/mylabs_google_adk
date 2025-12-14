"""
Lab 5 - Exercise 5: User Simulation
====================================

This exercise covers dynamic user simulation for testing:
1. Why user simulation?
2. Conversation scenarios
3. Setting up user simulation
4. Configuring the simulator
5. Combining with other metrics

Run: uv run python 05_user_simulation.py
"""

import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Part 1: Why User Simulation?
# =============================================================================

def explain_user_simulation():
    """Explain why user simulation is needed."""
    print("""
    WHY USER SIMULATION?
    ====================

    THE PROBLEM:
    ------------
    Fixed test cases can't handle dynamic conversations.

    Example scenario:
    Agent needs user's email and phone number.

    Case 1 - Agent asks both at once:
    Agent: "Please provide your email and phone number."
    User: ??? (your fixed test didn't expect this)

    Case 2 - Agent asks one at a time:
    Agent: "What's your email?"
    User: "user@example.com"
    Agent: "What's your phone number?"
    User: ??? (different flow than Case 1)

    THE SOLUTION:
    -------------
    User Simulation: An LLM plays the role of the user!

    Instead of fixed prompts, you define:
    - A starting prompt (first message)
    - A conversation plan (what the user wants to achieve)

    The simulator LLM:
    - Reads the agent's responses
    - Generates appropriate user messages
    - Follows the conversation plan
    - Decides when the conversation is complete

    BENEFITS:
    ---------
    1. Handles dynamic agent behavior
    2. Tests real conversation flows
    3. More realistic than static tests
    4. Catches edge cases

    LIMITATIONS:
    ------------
    - Cannot compare against expected trajectory/response
    - Works best with hallucinations_v1 and safety_v1 metrics
    - Adds LLM cost for the simulator
    """)


# =============================================================================
# Part 2: Conversation Scenarios
# =============================================================================

def explain_conversation_scenarios():
    """Explain conversation scenario structure."""
    print("""
    CONVERSATION SCENARIOS
    ======================

    A ConversationScenario defines the user's goal:

    {
      "starting_prompt": "The first message to send",
      "conversation_plan": "Description of what user wants to achieve"
    }

    EXAMPLE SCENARIOS:
    ------------------

    Simple Task:
    {
      "starting_prompt": "Hi, I need help",
      "conversation_plan": "Ask the agent to find a flight from NYC to LA for next Friday."
    }

    Multi-Step Task:
    {
      "starting_prompt": "I want to make a purchase",
      "conversation_plan": "Search for laptops under $1000. Ask about the cheapest option's specs. If it looks good, add it to cart."
    }

    Information Gathering:
    {
      "starting_prompt": "What can you help me with?",
      "conversation_plan": "Ask the agent about its capabilities. Then ask it to demonstrate one feature with a simple example."
    }

    Challenging Scenario:
    {
      "starting_prompt": "I'm frustrated with your service!",
      "conversation_plan": "Express dissatisfaction about a previous order. See how the agent handles complaints and if it offers a resolution."
    }

    SCENARIOS FILE FORMAT:
    ----------------------
    conversation_scenarios.json:
    {
      "scenarios": [
        {
          "starting_prompt": "...",
          "conversation_plan": "..."
        },
        {
          "starting_prompt": "...",
          "conversation_plan": "..."
        }
      ]
    }
    """)


# =============================================================================
# Part 3: Setting Up User Simulation
# =============================================================================

def show_setup_steps():
    """Show how to set up user simulation."""
    print("""
    SETTING UP USER SIMULATION
    ==========================

    STEP 1: Create scenarios file
    -----------------------------
    # my_agent/conversation_scenarios.json
    {
      "scenarios": [
        {
          "starting_prompt": "Hello, I need to book a flight",
          "conversation_plan": "Book a round-trip flight from New York to Los Angeles. Departure on December 15th, return on December 22nd. Prefer economy class."
        },
        {
          "starting_prompt": "What flights are available?",
          "conversation_plan": "Ask about same-day flights to Chicago. Accept the cheapest option if under $300, otherwise decline."
        }
      ]
    }

    STEP 2: Create session input file
    ----------------------------------
    # my_agent/session_input.json
    {
      "app_name": "flight_booking_agent",
      "user_id": "test_user"
    }

    STEP 3: Create eval set with scenarios
    --------------------------------------
    # Using CLI
    adk eval_set create my_agent my_eval_set

    adk eval_set add_eval_case \\
      my_agent \\
      my_eval_set \\
      --scenarios_file my_agent/conversation_scenarios.json \\
      --session_input_file my_agent/session_input.json

    STEP 4: Create eval config
    --------------------------
    # my_agent/eval_config.json
    {
      "criteria": {
        "hallucinations_v1": {
          "threshold": 0.8,
          "evaluate_intermediate_nl_responses": true
        },
        "safety_v1": {
          "threshold": 0.9
        }
      }
    }

    STEP 5: Run evaluation
    ----------------------
    adk eval \\
      my_agent \\
      --config_file_path my_agent/eval_config.json \\
      my_eval_set \\
      --print_detailed_results

    NOTE: Reference-based metrics (tool_trajectory, response_match)
    are NOT supported with user simulation because responses are dynamic.
    """)


# =============================================================================
# Part 4: User Simulator Configuration
# =============================================================================

def show_simulator_config():
    """Show user simulator configuration options."""
    print("""
    USER SIMULATOR CONFIGURATION
    ============================

    The simulator can be customized in eval_config.json:

    {
      "criteria": {
        "hallucinations_v1": {"threshold": 0.8},
        "safety_v1": 0.9
      },
      "user_simulator_config": {
        "model": "gemini-2.5-flash",
        "model_configuration": {
          "thinking_config": {
            "include_thoughts": true,
            "thinking_budget": 10240
          }
        },
        "max_allowed_invocations": 20
      }
    }

    CONFIGURATION OPTIONS:
    ----------------------

    model (string):
    - The LLM model for user simulation
    - Default: "gemini-2.5-flash"
    - Options: Any Gemini model

    model_configuration (GenerateContentConfig):
    - Controls model behavior
    - thinking_config: Enable reasoning
    - temperature: Creativity level
    - Other generation parameters

    max_allowed_invocations (int):
    - Maximum user-agent turns
    - Default: 20
    - Prevents infinite conversations
    - Set higher for complex scenarios

    THINKING CONFIG:
    ----------------
    The simulator can "think" about what to say next:

    "thinking_config": {
      "include_thoughts": true,    // Enable reasoning
      "thinking_budget": 10240     // Token budget for thinking
    }

    This helps the simulator:
    - Better follow the conversation plan
    - Make more realistic decisions
    - Determine when conversation is complete
    """)


# =============================================================================
# Part 5: Sample Agent for Simulation Demo
# =============================================================================

def search_flights(origin: str, destination: str, date: str) -> dict:
    """Search for available flights."""
    flights = [
        {"flight": "FL001", "price": 299, "departure": "08:00", "arrival": "11:00"},
        {"flight": "FL002", "price": 399, "departure": "14:00", "arrival": "17:00"},
        {"flight": "FL003", "price": 249, "departure": "20:00", "arrival": "23:00"},
    ]
    return {
        "origin": origin,
        "destination": destination,
        "date": date,
        "flights": flights
    }


def book_flight(flight_id: str, passenger_name: str, email: str) -> dict:
    """Book a flight."""
    return {
        "success": True,
        "confirmation": f"CONF-{flight_id}-001",
        "passenger": passenger_name,
        "email": email,
        "message": f"Flight {flight_id} booked successfully!"
    }


def cancel_booking(confirmation_number: str) -> dict:
    """Cancel a flight booking."""
    return {
        "success": True,
        "message": f"Booking {confirmation_number} has been cancelled."
    }


def create_flight_agent():
    """Create a flight booking agent."""
    search_tool = FunctionTool(func=search_flights)
    book_tool = FunctionTool(func=book_flight)
    cancel_tool = FunctionTool(func=cancel_booking)

    agent = LlmAgent(
        name="FlightAgent",
        model="gemini-2.0-flash",
        instruction="""You are a flight booking assistant.
        Help customers search for and book flights.

        Workflow:
        1. Ask for origin, destination, and date
        2. Search for available flights
        3. Help customer choose a flight
        4. Collect passenger name and email
        5. Book the flight
        6. Provide confirmation number

        Be helpful and guide the customer through each step.
        Ask for one piece of information at a time.""",
        tools=[search_tool, book_tool, cancel_tool],
    )

    return agent


async def simulate_conversation():
    """Simulate a multi-turn conversation with the flight agent."""
    print("\n  Simulating a user conversation with the flight agent...")
    print("  (This demonstrates how user simulation works)")

    agent = create_flight_agent()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=agent,
        app_name="flight_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="flight_demo",
        user_id="user1",
        session_id="flight_session",
        state={}
    )

    # Simulated user messages (in real simulation, these would be generated)
    conversation = [
        "Hi, I need to book a flight",
        "I want to fly from New York to Los Angeles on December 15th",
        "I'll take the cheapest one, FL003",
        "My name is John Smith and my email is john@example.com",
    ]

    print("\n  Conversation:")
    print("  " + "-"*50)

    for user_msg in conversation:
        print(f"\n  User: {user_msg}")

        user_message = types.Content(parts=[types.Part(text=user_msg)])

        async for event in runner.run_async(
            user_id="user1",
            session_id="flight_session",
            new_message=user_message,
        ):
            if event.is_final_response() and event.content:
                response = event.content.parts[0].text
                # Truncate for display
                lines = response.split('\n')
                short_response = '\n  '.join(lines[:3])
                print(f"  Agent: {short_response}...")

    print("\n  " + "-"*50)
    print("  (In real user simulation, an LLM generates the user messages)")


# =============================================================================
# Part 6: Supported Metrics with User Simulation
# =============================================================================

def show_supported_metrics():
    """Show which metrics work with user simulation."""
    print("""
    METRICS COMPATIBLE WITH USER SIMULATION
    =======================================

    SUPPORTED:
    ----------
    ✓ hallucinations_v1
      - Checks if agent makes unsupported claims
      - Works because it evaluates agent output vs context
      - No expected response needed

    ✓ safety_v1
      - Checks if agent output is safe
      - Evaluates agent responses only
      - No expected response needed

    NOT SUPPORTED:
    --------------
    ✗ tool_trajectory_avg_score
      - Requires expected tool calls
      - Dynamic conversation = unpredictable tools

    ✗ response_match_score
      - Requires expected response
      - Dynamic conversation = unpredictable responses

    ✗ final_response_match_v2
      - Requires reference response
      - Dynamic conversation = no fixed reference

    ✗ rubric_based_final_response_quality_v1
      - Currently not supported with simulation
      - May be added in future versions

    ✗ rubric_based_tool_use_quality_v1
      - Currently not supported with simulation
      - May be added in future versions

    RECOMMENDED CONFIG FOR USER SIMULATION:
    ---------------------------------------
    {
      "criteria": {
        "hallucinations_v1": {
          "threshold": 0.8,
          "evaluate_intermediate_nl_responses": true
        },
        "safety_v1": 0.9
      },
      "user_simulator_config": {
        "model": "gemini-2.5-flash",
        "max_allowed_invocations": 20
      }
    }
    """)


# =============================================================================
# Part 7: Best Practices
# =============================================================================

def show_best_practices():
    """Show best practices for user simulation."""
    print("""
    USER SIMULATION BEST PRACTICES
    ==============================

    1. WRITE CLEAR CONVERSATION PLANS:
       --------------------------------
       BAD:  "Book a flight"
       GOOD: "Book a round-trip flight from NYC to LA. Departure Dec 15, return Dec 22. Prefer economy class under $400."

    2. TEST EDGE CASES:
       -----------------
       - "Try to book a flight but change your mind halfway"
       - "Ask about something the agent can't do"
       - "Express frustration and see how agent responds"

    3. SET APPROPRIATE MAX_INVOCATIONS:
       ---------------------------------
       - Simple tasks: 5-10
       - Medium complexity: 10-15
       - Complex multi-step: 15-25
       - Default: 20

    4. USE VARIED STARTING PROMPTS:
       ----------------------------
       - Formal: "I would like to inquire about..."
       - Casual: "Hey, can you help me..."
       - Direct: "Book a flight to NYC"
       - Vague: "I need some travel help"

    5. COMBINE STATIC AND DYNAMIC TESTS:
       ----------------------------------
       - Static tests: Known good inputs with expected outputs
       - Dynamic tests: User simulation for flexibility

    6. MONITOR CONVERSATION LENGTH:
       -----------------------------
       If conversations frequently hit max_invocations:
       - Conversation plan may be too complex
       - Agent may be getting stuck
       - Simulator may be confused

    7. REVIEW SIMULATION TRANSCRIPTS:
       ------------------------------
       Run with --print_detailed_results to see:
       - Full conversation history
       - Where things went wrong
       - Unexpected agent behavior

    EXAMPLE SCENARIO SET:
    ---------------------
    {
      "scenarios": [
        // Happy path
        {"starting_prompt": "Book a flight", "conversation_plan": "Complete booking with all valid info"},

        // Edge case: Cancellation
        {"starting_prompt": "I made a booking", "conversation_plan": "Ask to cancel, provide confirmation number"},

        // Edge case: Unavailable route
        {"starting_prompt": "Fly me to the moon", "conversation_plan": "Ask for impossible route, accept agent's limitations gracefully"},

        // Stress test: Changing requirements
        {"starting_prompt": "I need a flight", "conversation_plan": "Start with NYC to LA, then change to Chicago, then back to LA"}
      ]
    }
    """)


async def main():
    print("\n" + "#"*70)
    print("# Lab 5 Exercise 5: User Simulation")
    print("#"*70)

    # =========================================================================
    # Part 1: Why User Simulation
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Why User Simulation?")
    print("="*60)
    explain_user_simulation()

    # =========================================================================
    # Part 2: Conversation Scenarios
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Conversation Scenarios")
    print("="*60)
    explain_conversation_scenarios()

    # =========================================================================
    # Part 3: Setup Steps
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Setting Up User Simulation")
    print("="*60)
    show_setup_steps()

    # =========================================================================
    # Part 4: Simulator Config
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: User Simulator Configuration")
    print("="*60)
    show_simulator_config()

    # =========================================================================
    # Part 5: Demo Conversation
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Simulated Conversation Demo")
    print("="*60)

    await simulate_conversation()

    # =========================================================================
    # Part 6: Supported Metrics
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Supported Metrics")
    print("="*60)
    show_supported_metrics()

    # =========================================================================
    # Part 7: Best Practices
    # =========================================================================
    print("\n" + "="*60)
    print("PART 7: Best Practices")
    print("="*60)
    show_best_practices()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: User Simulation")
    print("#"*70)
    print("""
    USER SIMULATION OVERVIEW:
    -------------------------
    An LLM plays the role of the user, generating dynamic responses
    based on a conversation plan.

    CONVERSATION SCENARIO:
    ----------------------
    {
      "starting_prompt": "First user message",
      "conversation_plan": "Description of user's goal"
    }

    SETUP STEPS:
    ------------
    1. Create conversation_scenarios.json with scenarios
    2. Create session_input.json with app/user info
    3. Add scenarios to eval set: adk eval_set add_eval_case
    4. Create eval_config.json with supported metrics
    5. Run: adk eval my_agent my_eval_set

    SUPPORTED METRICS:
    ------------------
    ✓ hallucinations_v1 - Fact checking
    ✓ safety_v1 - Safety checking
    ✗ tool_trajectory_* - Not supported
    ✗ response_match_* - Not supported

    SIMULATOR CONFIG:
    -----------------
    {
      "user_simulator_config": {
        "model": "gemini-2.5-flash",
        "max_allowed_invocations": 20
      }
    }

    KEY TAKEAWAYS:
    --------------
    - User simulation handles dynamic conversations
    - Define goals, not exact messages
    - Only hallucination and safety metrics supported
    - Combine with static tests for full coverage
    - Review transcripts to debug issues
    """)


if __name__ == "__main__":
    asyncio.run(main())
