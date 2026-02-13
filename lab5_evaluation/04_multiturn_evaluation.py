"""
Lab 5 - Exercise 4: Multi-Turn Evaluation
==========================================

This exercise covers evaluating multi-turn conversations:
1. Multi-turn eval case structure
2. session_input with initial state
3. Using num_runs for non-determinism
4. Comparing single vs multiple runs

Run: uv run python 04_multiturn_evaluation.py
"""

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from google.adk.evaluation.agent_evaluator import AgentEvaluator


# =============================================================================
# Helper
# =============================================================================

async def safe_evaluate(**kwargs):
    """Run AgentEvaluator.evaluate(), catching threshold assertion failures."""
    try:
        results = await safe_evaluate(**kwargs)
        print("\n    >>> All metrics PASSED thresholds.\n")
        return results
    except AssertionError as e:
        print(f"\n    >>> Some metrics FAILED:")
        for line in str(e).strip().splitlines():
            print(f"        {line}")
        print()
        return None
    except Exception as e:
        print(f"\n    >>> Evaluation error: {type(e).__name__}: {e}\n")
        return None


# =============================================================================
# Part 1: Multi-Turn Concepts
# =============================================================================

def explain_multiturn():
    """Explain multi-turn evaluation."""
    print("""
    MULTI-TURN EVALUATION
    =====================
    So far we've tested single-turn interactions (one user message, one response).
    Real agents handle multi-turn conversations where context builds up.

    An EvalCase's `conversation` array holds multiple Invocation objects:

      "conversation": [
        { "invocation_id": "turn-1", "user_content": ..., "final_response": ... },
        { "invocation_id": "turn-2", "user_content": ..., "final_response": ... },
        { "invocation_id": "turn-3", "user_content": ..., "final_response": ... }
      ]

    The evaluator replays each turn sequentially within the same session,
    so the agent retains context from earlier turns.

    session_input allows setting initial state:
      "session_input": {
        "app_name": "travel_agent",
        "user_id": "test_user",
        "state": {"user:loyalty_tier": "gold"}
      }

    Our test cases:
      Case A: 3-turn booking flow (search → details → book)
      Case B: 2-turn search-then-cancel (with initial state)
    """)


# =============================================================================
# Part 2: Show Test File Structure
# =============================================================================

def show_test_structure():
    """Show the multi-turn test file."""
    test_file = Path("tests/04_multiturn.test.json")
    data = json.loads(test_file.read_text())

    for case in data["eval_cases"]:
        turns = len(case["conversation"])
        state = case.get("session_input", {}).get("state", {})
        print(f"    Case: {case['eval_id']} — {turns} turns")
        if state:
            print(f"      Initial state: {state}")
        for inv in case["conversation"]:
            query = inv["user_content"]["parts"][0]["text"][:60]
            tools = [t["name"] for t in inv.get("intermediate_data", {}).get("tool_uses", [])]
            print(f"      {inv['invocation_id']}: \"{query}...\"")
            print(f"        Expected tools: {tools}")


# =============================================================================
# Part 3: Run with num_runs=1
# =============================================================================

async def run_single():
    """Baseline evaluation with 1 run."""
    print("\n    Running with num_runs=1 (baseline)...")

    # Write config with relaxed thresholds for multi-turn
    config = {"criteria": {"tool_trajectory_avg_score": 1.0, "response_match_score": 0.4}}
    Path("tests/test_config.json").write_text(json.dumps(config, indent=2))

    results = await safe_evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/04_multiturn.test.json",
        num_runs=1,
        print_detailed_results=True,
    )
    return results


# =============================================================================
# Part 4: Run with num_runs=3
# =============================================================================

async def run_multiple():
    """Multiple runs to handle non-determinism."""
    print("""
    HANDLING NON-DETERMINISM WITH num_runs
    ======================================
    LLM responses vary between runs. Running multiple times shows variance.
    The evaluator reports per-run scores so you can see consistency.
    """)

    results = await safe_evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/04_multiturn.test.json",
        num_runs=3,
        print_detailed_results=True,
    )
    return results


# =============================================================================
# Part 5: Tips
# =============================================================================

def show_tips():
    """Tips for multi-turn evaluation."""
    print("""
    MULTI-TURN EVALUATION TIPS
    ==========================
    1. Use looser thresholds — multi-turn responses are less predictable.
       Our config uses response_match_score: 0.7 (instead of 0.8).

    2. Use IN_ORDER match for trajectories — the agent may add extra
       clarification steps between expected tool calls.

    3. Use num_runs >= 2 to detect flaky test cases.

    4. session_input.state lets you test state-dependent behavior
       (e.g., loyalty tier, user preferences).

    5. Each turn is scored independently, then averaged for the case.
    """)


# =============================================================================
# Main
# =============================================================================

async def main():
    os.chdir(Path(__file__).parent)

    print("\n" + "#" * 70)
    print("# Lab 5 Exercise 4: Multi-Turn Evaluation")
    print("#" * 70)

    # Part 1
    print("\n" + "=" * 60)
    print("PART 1: Multi-Turn Concepts")
    print("=" * 60)
    explain_multiturn()

    # Part 2
    print("\n" + "=" * 60)
    print("PART 2: Test File Structure")
    print("=" * 60)
    show_test_structure()

    # Part 3
    print("\n" + "=" * 60)
    print("PART 3: Baseline (num_runs=1)")
    print("=" * 60)
    await run_single()

    # Part 4
    print("\n" + "=" * 60)
    print("PART 4: Multiple Runs (num_runs=3)")
    print("=" * 60)
    await run_multiple()

    # Part 5
    print("\n" + "=" * 60)
    print("PART 5: Tips")
    print("=" * 60)
    show_tips()

    print("\n" + "#" * 70)
    print("# Exercise 4 Complete — Next: 05_custom_rubrics.py")
    print("#" * 70)


if __name__ == "__main__":
    asyncio.run(main())
