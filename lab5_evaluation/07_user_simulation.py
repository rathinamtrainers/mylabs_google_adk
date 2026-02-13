"""
Lab 5 - Exercise 7: User Simulation & Eval Set Management
==========================================================

This exercise covers dynamic user simulation and eval set management:
1. User simulation concepts
2. Creating scenario files
3. Eval set management with adk eval_set CLI
4. User simulator configuration (incl. custom_instructions)
5. per_turn_user_simulator_quality_v1 metric
6. Running user simulation evaluation
7. Metrics compatibility matrix

Run: uv run python 07_user_simulation.py
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# Part 1: User Simulation Concepts
# =============================================================================

def explain_user_simulation():
    """Explain why and how user simulation works."""
    print("""
    USER SIMULATION
    ===============
    Problem: Fixed test cases can't handle dynamic conversations.
    The agent may ask questions in different order or phrasing each run.

    Solution: An LLM plays the role of the user, following a plan.

    ConversationScenario:
      {
        "starting_prompt": "First message from the simulated user",
        "conversation_plan": "Description of what the user wants to achieve"
      }

    The simulator LLM reads agent responses and generates appropriate
    user messages until the conversation goal is achieved.

    When to use:
      Static tests  → known input/output pairs, all metrics available
      User simulation → dynamic conversations, only hallucination/safety metrics
    """)


# =============================================================================
# Part 2: Create Scenario Files
# =============================================================================

def create_scenario_files():
    """Create conversation scenario and session input files."""
    scenarios_dir = Path("scenarios")
    scenarios_dir.mkdir(exist_ok=True)

    scenarios = {
        "scenarios": [
            {
                "starting_prompt": "I need to book a flight.",
                "conversation_plan": "Search for flights from New York to Los Angeles on December 15th. Ask about the cheapest option. Book it for Jane Doe, jane@example.com.",
            },
            {
                "starting_prompt": "Can you help me with travel?",
                "conversation_plan": "Ask about flights to Chicago. Change your mind and ask about flights to Miami instead. Pick the afternoon flight.",
            },
            {
                "starting_prompt": "I need to cancel my booking.",
                "conversation_plan": "Provide confirmation number CONF-FL001-001 and ask to cancel. Confirm the cancellation.",
            },
        ]
    }

    scenarios_file = scenarios_dir / "conversation_scenarios.json"
    scenarios_file.write_text(json.dumps(scenarios, indent=2))
    print(f"    Wrote {scenarios_file} with {len(scenarios['scenarios'])} scenarios")

    for i, s in enumerate(scenarios["scenarios"], 1):
        print(f"      Scenario {i}: \"{s['starting_prompt'][:40]}...\"")

    session_input = {"app_name": "travel_agent", "user_id": "sim_user"}
    session_file = scenarios_dir / "session_input.json"
    session_file.write_text(json.dumps(session_input, indent=2))
    print(f"    Wrote {session_file}")


# =============================================================================
# Part 3: Eval Set Management
# =============================================================================

def show_eval_set_commands():
    """Show adk eval_set CLI commands."""
    print("""
    EVAL SET MANAGEMENT (adk eval_set)
    ===================================
    Eval sets can be managed via CLI commands:

    Create an eval set:
      uv run adk eval_set create travel_agent travel_sim_eval_set

    Add a static test case:
      uv run adk eval_set add_eval_case travel_agent travel_sim_eval_set \\
        --eval_dataset_file_path tests/01_basic.test.json

    Add user simulation scenarios:
      uv run adk eval_set add_eval_case travel_agent travel_sim_eval_set \\
        --scenarios_file scenarios/conversation_scenarios.json \\
        --session_input_file scenarios/session_input.json

    Run evaluation on the eval set:
      uv run adk eval travel_agent travel_sim_eval_set \\
        --config_file_path tests/test_config_user_sim.json

    NOTE: adk eval_set commands require the agent module to be importable.
    They store eval sets in a local database managed by ADK.
    """)


# =============================================================================
# Part 4: User Simulator Configuration
# =============================================================================

def create_user_sim_config():
    """Create and explain user simulator configuration."""
    print("""
    USER SIMULATOR CONFIGURATION
    ============================
    The user_simulator_config section controls how the simulated user behaves.
    """)

    config = {
        "criteria": {
            "hallucinations_v1": {
                "threshold": 0.8,
                "evaluate_intermediate_nl_responses": True,
            },
            "safety_v1": 0.9,
            "per_turn_user_simulator_quality_v1": {
                "threshold": 0.8,
            },
        },
        "user_simulator_config": {
            "model": "gemini-2.0-flash",
            "max_allowed_invocations": 15,
            "custom_instructions": (
                "You are testing a travel booking agent. "
                "Follow the conversation plan: {conversation_plan}. "
                "When the task is complete, say '{stop_signal}'. "
                "Conversation so far: {conversation_history}"
            ),
        },
    }

    config_file = Path("tests/test_config_user_sim.json")
    config_file.write_text(json.dumps(config, indent=2))
    print(f"    Wrote {config_file}")

    print("""
    Configuration options:
      model                  — LLM for the simulated user (default: gemini-2.5-flash)
      max_allowed_invocations — max turns before stopping (default: 20)
      custom_instructions     — override default simulator prompt

    custom_instructions placeholders:
      {conversation_plan}   — replaced with the scenario's conversation_plan
      {stop_signal}         — replaced with the signal that ends the conversation
      {conversation_history} — replaced with the conversation so far
    """)

    print("""
    per_turn_user_simulator_quality_v1
    ==================================
    This 8th metric validates that the simulated user actually follows
    the conversation plan. An LLM judge checks each turn to see if
    the simulator's responses align with the intended scenario.

    Score = fraction of turns where the simulator followed the plan.
    """)


# =============================================================================
# Part 5: Metrics Compatibility
# =============================================================================

def show_compatibility():
    """Show metrics compatibility matrix."""
    print("""
    METRICS COMPATIBILITY MATRIX
    ============================

    ┌─────────────────────────────────────────┬────────┬────────────┐
    │ Metric                                  │ Static │ User Sim   │
    ├─────────────────────────────────────────┼────────┼────────────┤
    │ tool_trajectory_avg_score               │   Y    │     N      │
    │ response_match_score                    │   Y    │     N      │
    │ final_response_match_v2                 │   Y    │     N      │
    │ rubric_based_final_response_quality_v1  │   Y    │     N      │
    │ rubric_based_tool_use_quality_v1        │   Y    │     N      │
    │ hallucinations_v1                       │   Y    │     Y      │
    │ safety_v1                               │   Y    │     Y      │
    │ per_turn_user_simulator_quality_v1      │   N    │     Y      │
    └─────────────────────────────────────────┴────────┴────────────┘

    Static tests: Use all 7 metrics (not per_turn_user_simulator).
    User simulation: Use hallucinations, safety, and per_turn_user_simulator.
    Combine both for comprehensive coverage.
    """)


# =============================================================================
# Main
# =============================================================================

async def main():
    os.chdir(Path(__file__).parent)

    print("\n" + "#" * 70)
    print("# Lab 5 Exercise 7: User Simulation & Eval Set Management")
    print("#" * 70)

    # Part 1
    print("\n" + "=" * 60)
    print("PART 1: User Simulation Concepts")
    print("=" * 60)
    explain_user_simulation()

    # Part 2
    print("\n" + "=" * 60)
    print("PART 2: Create Scenario Files")
    print("=" * 60)
    create_scenario_files()

    # Part 3
    print("\n" + "=" * 60)
    print("PART 3: Eval Set Management")
    print("=" * 60)
    show_eval_set_commands()

    # Part 4
    print("\n" + "=" * 60)
    print("PART 4: User Simulator Configuration")
    print("=" * 60)
    create_user_sim_config()

    # Part 5
    print("\n" + "=" * 60)
    print("PART 5: Metrics Compatibility Matrix")
    print("=" * 60)
    show_compatibility()

    # Summary
    print("\n" + "#" * 70)
    print("# Summary")
    print("#" * 70)
    print("""
    USER SIMULATION enables testing dynamic, multi-turn conversations
    where the agent's behavior is unpredictable.

    Key components:
      ConversationScenario  — starting_prompt + conversation_plan
      user_simulator_config — model, max_invocations, custom_instructions
      adk eval_set          — CLI for managing eval sets

    Supported metrics:
      hallucinations_v1, safety_v1, per_turn_user_simulator_quality_v1

    Best practice: Combine static tests (all 7 metrics) with user
    simulation (dynamic behavior) for comprehensive agent evaluation.

    LAB 5 COMPLETE!
    """)


if __name__ == "__main__":
    asyncio.run(main())
