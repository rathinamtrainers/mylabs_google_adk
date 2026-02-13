"""
Lab 5 - Exercise 1: Your First Evaluation
==========================================

This exercise introduces ADK agent evaluation by running a real evaluation:
1. Why evaluate agents (brief)
2. The travel_agent module structure
3. Building a .test.json file programmatically
4. Running AgentEvaluator.evaluate()
5. Interpreting results

Run: uv run python 01_first_evaluation.py
"""

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from google.adk.evaluation.agent_evaluator import AgentEvaluator


# =============================================================================
# Part 1: Why Evaluate Agents? (Brief)
# =============================================================================

def explain_evaluation():
    """Brief intro to agent evaluation."""
    print("""
    WHY EVALUATE AGENTS?
    ====================
    Traditional software: Deterministic — same input always gives same output.
    LLM agents: Probabilistic — outputs vary between runs.

    Solution: Qualitative evaluation with two dimensions:
      TRAJECTORY — Did the agent call the right tools in the right order?
      RESPONSE   — Is the final answer correct / helpful?

    ADK provides 8 built-in metrics. This exercise uses the two defaults:
      tool_trajectory_avg_score  (trajectory correctness, threshold: 1.0)
      response_match_score       (ROUGE-1 word overlap, threshold: 0.5)
    """)


# =============================================================================
# Part 2: The Travel Agent Module
# =============================================================================

def show_agent_structure():
    """Show how the travel_agent module is structured."""
    print("""
    AGENT MODULE STRUCTURE
    ======================
    For `adk eval` and AgentEvaluator to work, the agent must be a Python
    module that exports `root_agent`:

      travel_agent/
      ├── __init__.py     # from .agent import root_agent
      └── agent.py        # root_agent = LlmAgent(...)

    Our agent has 5 tools:
      search_flights(origin, destination, date)
      get_flight_details(flight_id)
      book_flight(flight_id, passenger_name, email)
      cancel_booking(confirmation_number)
      get_weather(city)
    """)

    # Verify the module is importable
    from travel_agent import root_agent
    print(f"    Agent name:  {root_agent.name}")
    print(f"    Model:       {root_agent.model}")
    print(f"    Tools:       {[t.name for t in root_agent.tools]}")


# =============================================================================
# Part 3: Build a .test.json File
# =============================================================================

def build_test_file():
    """Build and write a test file programmatically."""
    print("""
    EVALUATION DATA STRUCTURES
    ==========================
    EvalSet  → collection of test cases (the .test.json file)
    EvalCase → single test scenario (a conversation)
    Invocation → single user-agent turn within a conversation
    """)

    eval_set = {
        "eval_set_id": "basic_eval_set",
        "name": "Basic Travel Agent Tests",
        "description": "Simple single-turn tests for flight search and booking",
        "eval_cases": [
            {
                "eval_id": "flight_search",
                "conversation": [
                    {
                        "invocation_id": "inv-001",
                        "user_content": {
                            "parts": [{"text": "Find flights from New York to Los Angeles on December 15th"}],
                            "role": "user",
                        },
                        "final_response": {
                            "parts": [{"text": "I found 3 flights from New York to Los Angeles on December 15th:\n1. FL001 - SkyAir, departing 08:00, arriving 11:00, $299\n2. FL002 - CloudJet, departing 14:00, arriving 17:00, $399\n3. FL003 - SkyAir, departing 20:00, arriving 23:00, $249"}],
                            "role": "model",
                        },
                        "intermediate_data": {
                            "tool_uses": [
                                {
                                    "name": "search_flights",
                                    "args": {"origin": "New York", "destination": "Los Angeles", "date": "December 15th"},
                                }
                            ],
                            "intermediate_responses": [],
                        },
                    }
                ],
                "session_input": {"app_name": "travel_agent", "user_id": "test_user", "state": {}},
            },
            {
                "eval_id": "flight_booking",
                "conversation": [
                    {
                        "invocation_id": "inv-002",
                        "user_content": {
                            "parts": [{"text": "Book flight FL001 for John Smith, email john@example.com"}],
                            "role": "user",
                        },
                        "final_response": {
                            "parts": [{"text": "Flight FL001 has been booked for John Smith. Your confirmation number is CONF-FL001-001. A confirmation email has been sent to john@example.com."}],
                            "role": "model",
                        },
                        "intermediate_data": {
                            "tool_uses": [
                                {
                                    "name": "book_flight",
                                    "args": {"flight_id": "FL001", "passenger_name": "John Smith", "email": "john@example.com"},
                                }
                            ],
                            "intermediate_responses": [],
                        },
                    }
                ],
                "session_input": {"app_name": "travel_agent", "user_id": "test_user", "state": {}},
            },
        ],
    }

    # Write to tests/ directory
    test_dir = Path("tests")
    test_dir.mkdir(exist_ok=True)

    test_file = test_dir / "01_basic.test.json"
    test_file.write_text(json.dumps(eval_set, indent=2))
    print(f"    Wrote {test_file} with {len(eval_set['eval_cases'])} test cases")

    # Write config — must be named test_config.json for auto-discovery
    config = {"criteria": {"tool_trajectory_avg_score": 1.0, "response_match_score": 0.5}}
    config_file = test_dir / "test_config.json"
    config_file.write_text(json.dumps(config, indent=2))
    print(f"    Wrote {config_file}")

    return str(test_file)


# =============================================================================
# Part 4: Run AgentEvaluator.evaluate()
# =============================================================================

async def run_evaluation(test_file: str):
    """Run the actual ADK evaluation framework."""
    print("""
    RUNNING AgentEvaluator.evaluate()
    ==================================
    This is the core ADK evaluation API. It:
    1. Loads the agent from the module
    2. Reads the .test.json file
    3. Replays each conversation turn against the agent
    4. Compares actual tool calls and responses to expected
    5. Scores using configured criteria
    """)

    results = await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir=test_file,
        num_runs=1,
        print_detailed_results=True,
    )

    return results


# =============================================================================
# Part 5: Interpret Results
# =============================================================================

def interpret_results(results):
    """Explain what the evaluation results mean."""
    print("""
    INTERPRETING RESULTS
    ====================
    The output above shows per-case scores for each metric.

    - tool_trajectory_avg_score: 1.0 means the agent called exactly the
      expected tools with the expected arguments.
    - response_match_score: The ROUGE-1 F1 overlap between actual and
      expected response. Higher is better, 0.8+ is typically passing.

    If a case fails, check:
    - Did the agent call a different tool? (trajectory mismatch)
    - Did the agent's response use very different wording? (low ROUGE-1)
    """)


# =============================================================================
# Part 6: CLI Equivalent
# =============================================================================

def show_cli_command():
    """Show the equivalent CLI command."""
    print("""
    EQUIVALENT CLI COMMAND
    ======================
    You can run the same evaluation from the command line:

      uv run adk eval travel_agent tests/01_basic.test.json

    Or with explicit config:

      uv run adk eval travel_agent tests/01_basic.test.json \\
        --config_file_path tests/test_config.json

    The CLI auto-discovers test_config.json in the same directory as the test file.
    """)


# =============================================================================
# Main
# =============================================================================

async def main():
    os.chdir(Path(__file__).parent)

    print("\n" + "#" * 70)
    print("# Lab 5 Exercise 1: Your First Evaluation")
    print("#" * 70)

    # Part 1
    print("\n" + "=" * 60)
    print("PART 1: Why Evaluate Agents?")
    print("=" * 60)
    explain_evaluation()

    # Part 2
    print("\n" + "=" * 60)
    print("PART 2: The Travel Agent Module")
    print("=" * 60)
    show_agent_structure()

    # Part 3
    print("\n" + "=" * 60)
    print("PART 3: Building a .test.json File")
    print("=" * 60)
    test_file = build_test_file()

    # Part 4
    print("\n" + "=" * 60)
    print("PART 4: Running AgentEvaluator.evaluate()")
    print("=" * 60)
    results = await run_evaluation(test_file)

    # Part 5
    print("\n" + "=" * 60)
    print("PART 5: Interpreting Results")
    print("=" * 60)
    interpret_results(results)

    # Part 6
    print("\n" + "=" * 60)
    print("PART 6: CLI Equivalent")
    print("=" * 60)
    show_cli_command()

    print("\n" + "#" * 70)
    print("# Exercise 1 Complete — Next: 02_response_evaluation.py")
    print("#" * 70)


if __name__ == "__main__":
    asyncio.run(main())
