"""
Lab 5 - Exercise 3: Trajectory Evaluation
==========================================

This exercise explores trajectory (tool call) evaluation:
1. Match types: EXACT, IN_ORDER, ANY_ORDER
2. Running with each match type
3. Comparing results side-by-side

Run: uv run python 03_trajectory_evaluation.py
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
        results = await AgentEvaluator.evaluate(**kwargs)
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
# Part 1: Match Types Recap
# =============================================================================

def explain_match_types():
    """Brief explanation of trajectory match types."""
    print("""
    TRAJECTORY MATCH TYPES
    ======================
    Trajectory = the sequence of tool calls an agent makes.

    EXACT (default, strictest):
      All expected tools called, in exact order, no extras allowed.
      Use for: payments, security-critical workflows.

    IN_ORDER (medium):
      All expected tools called in order, extra tools allowed between.
      Use for: ordered pipelines with optional steps.

    ANY_ORDER (most flexible):
      All expected tools present, any order, extras allowed.
      Use for: information gathering, flexible research.

    Our test cases:
      Case A: simple_search      → expects [search_flights]
      Case B: search_then_book   → expects [search_flights, book_flight]
      Case C: search_and_weather → expects [search_flights, get_weather]
              (agent may call these in either order)
    """)


# =============================================================================
# Part 2: Run with Each Match Type
# =============================================================================

MATCH_TYPES = {"EXACT": 0, "IN_ORDER": 1, "ANY_ORDER": 2}


async def run_with_match_type(match_type: str):
    """Run trajectory evaluation with a specific match type."""
    config = {
        "criteria": {
            "tool_trajectory_avg_score": {
                "threshold": 1.0,
                "match_type": MATCH_TYPES[match_type],
            }
        }
    }
    Path("tests/test_config.json").write_text(json.dumps(config, indent=2))

    print(f"\n    Running with match_type: {match_type} (enum value: {MATCH_TYPES[match_type]})")
    print("    " + "-" * 50)

    await safe_evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/03_trajectory.test.json",
        num_runs=1,
        print_detailed_results=True,
    )


# =============================================================================
# Part 3: Comparison
# =============================================================================

def show_comparison():
    """Show a summary comparison of match types."""
    print("""
    MATCH TYPE COMPARISON SUMMARY
    =============================

    ┌──────────────────┬───────┬──────────┬───────────┐
    │ Case             │ EXACT │ IN_ORDER │ ANY_ORDER │
    ├──────────────────┼───────┼──────────┼───────────┤
    │ simple_search    │ Pass* │ Pass*    │ Pass*     │
    │ search_then_book │ ??    │ ??       │ ??        │
    │ search_and_weather│ ??   │ ??       │ Pass*     │
    └──────────────────┴───────┴──────────┴───────────┘
    * Depends on actual agent behavior

    Key takeaways:
    - EXACT fails if agent adds any extra tool calls
    - IN_ORDER tolerates extras but requires correct ordering
    - ANY_ORDER only checks that required tools are present
    - Choose based on how strict your workflow needs to be
    """)


# =============================================================================
# Part 4: CLI Equivalent
# =============================================================================

def show_cli():
    """Show CLI equivalent."""
    print("""
    CLI EQUIVALENT
    ==============
    uv run adk eval travel_agent tests/03_trajectory.test.json \\
      --config_file_path tests/test_config.json
    """)


# =============================================================================
# Main
# =============================================================================

async def main():
    os.chdir(Path(__file__).parent)

    print("\n" + "#" * 70)
    print("# Lab 5 Exercise 3: Trajectory Evaluation")
    print("#" * 70)

    # Part 1
    print("\n" + "=" * 60)
    print("PART 1: Match Types")
    print("=" * 60)
    explain_match_types()

    # Part 2
    print("\n" + "=" * 60)
    print("PART 2: Running with Each Match Type")
    print("=" * 60)

    for match_type in ["EXACT", "IN_ORDER", "ANY_ORDER"]:
        await run_with_match_type(match_type)

    # Part 3
    print("\n" + "=" * 60)
    print("PART 3: Comparison")
    print("=" * 60)
    show_comparison()

    # Part 4
    print("\n" + "=" * 60)
    print("PART 4: CLI Equivalent")
    print("=" * 60)
    show_cli()

    print("\n" + "#" * 70)
    print("# Exercise 3 Complete — Next: 04_multiturn_evaluation.py")
    print("#" * 70)


if __name__ == "__main__":
    asyncio.run(main())
