"""
Lab 5 - Exercise 6: Pytest Integration & CLI
=============================================

This exercise covers the three ways to run evaluations:
1. Examine the pytest file (test_travel_agent.py)
2. Run pytest
3. Run adk eval CLI on individual files
4. Run adk eval CLI on a directory
5. The adk web evaluation workflow

Run: uv run python 06_pytest_integration.py
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# Part 1: Examine Pytest File
# =============================================================================

def show_pytest_structure():
    """Read and explain the pytest file."""
    print("""
    PYTEST INTEGRATION
    ==================
    ADK evaluations integrate with pytest for CI/CD pipelines.

    Pattern:
      1. Import AgentEvaluator
      2. Write async test functions with @pytest.mark.asyncio
      3. Call AgentEvaluator.evaluate() in each test
      4. Run with: uv run pytest test_travel_agent.py -v
    """)

    test_file = Path("test_travel_agent.py")
    if test_file.exists():
        content = test_file.read_text()
        print("    Contents of test_travel_agent.py:")
        print("    " + "-" * 50)
        for line in content.splitlines():
            print(f"    {line}")
        print("    " + "-" * 50)
    else:
        print("    WARNING: test_travel_agent.py not found!")


# =============================================================================
# Part 2: Run Pytest
# =============================================================================

def run_pytest():
    """Run pytest on the evaluation tests."""
    print("""
    RUNNING PYTEST
    ==============
    Command: uv run pytest test_travel_agent.py -v -x --tb=short
    (running only the first test for a quick demo)
    """)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "test_travel_agent.py::test_basic_functionality", "-v", "-x", "--tb=short"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    print("    STDOUT:")
    for line in result.stdout.splitlines():
        print(f"    {line}")
    if result.returncode != 0:
        print("    STDERR:")
        for line in result.stderr.splitlines():
            print(f"    {line}")
    print(f"\n    Exit code: {result.returncode}")


# =============================================================================
# Part 3: Run adk eval CLI
# =============================================================================

def run_adk_eval_single():
    """Run adk eval on a single test file."""
    print("""
    ADK EVAL CLI — SINGLE FILE
    ==========================
    Command: uv run adk eval travel_agent tests/01_basic.test.json

    The CLI auto-discovers tests/test_config.json for evaluation criteria.
    """)

    # Ensure a reasonable config exists for the CLI
    import json
    config = {"criteria": {"tool_trajectory_avg_score": 1.0, "response_match_score": 0.5}}
    Path("tests/test_config.json").write_text(json.dumps(config, indent=2))

    result = subprocess.run(
        [sys.executable, "-m", "google.adk.cli", "eval", "travel_agent", "tests/01_basic.test.json"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    print("    Output:")
    for line in result.stdout.splitlines():
        print(f"    {line}")
    if result.returncode != 0 and result.stderr:
        for line in result.stderr.splitlines():
            print(f"    {line}")


# =============================================================================
# Part 4: Run adk eval on Directory
# =============================================================================

def run_adk_eval_directory():
    """Run adk eval on all test files."""
    print("""
    ADK EVAL CLI — DIRECTORY
    ========================
    Command: uv run adk eval travel_agent tests/
    This runs ALL .test.json files in the tests/ directory.
    """)

    # Just show the command — running all tests takes a while
    print("    This would run all test files. For a quick demo,")
    print("    we'll run on a single file with explicit config:")
    print()
    print("    uv run adk eval travel_agent tests/01_basic.test.json \\")
    print("      --config_file_path tests/test_config_basic.json")
    print()
    print("    To run all tests:")
    print("    uv run adk eval travel_agent tests/")


# =============================================================================
# Part 5: adk web Workflow
# =============================================================================

def show_adk_web():
    """Explain the adk web evaluation workflow."""
    print("""
    ADK WEB EVALUATION WORKFLOW
    ===========================
    The ADK dev server provides an interactive evaluation UI.

    Start it:
      uv run adk web

    Then in the browser:
      1. Select your agent from the dropdown
      2. Chat with it to create test sessions
      3. Click "Save as Test Case" to capture a session
      4. Configure evaluation metrics via sliders
      5. Run evaluation and view results with trace views

    The web UI is great for:
      - Exploratory testing before writing .test.json files
      - Debugging evaluation failures (trace inspection)
      - Quick iteration on rubric wording
      - Sharing results with non-technical stakeholders
    """)


# =============================================================================
# Main
# =============================================================================

async def main():
    os.chdir(Path(__file__).parent)

    print("\n" + "#" * 70)
    print("# Lab 5 Exercise 6: Pytest Integration & CLI")
    print("#" * 70)

    # Part 1
    print("\n" + "=" * 60)
    print("PART 1: Examine Pytest File")
    print("=" * 60)
    show_pytest_structure()

    # Part 2
    print("\n" + "=" * 60)
    print("PART 2: Run Pytest")
    print("=" * 60)
    run_pytest()

    # Part 3
    print("\n" + "=" * 60)
    print("PART 3: adk eval CLI — Single File")
    print("=" * 60)
    run_adk_eval_single()

    # Part 4
    print("\n" + "=" * 60)
    print("PART 4: adk eval CLI — Directory")
    print("=" * 60)
    run_adk_eval_directory()

    # Part 5
    print("\n" + "=" * 60)
    print("PART 5: adk web Evaluation Workflow")
    print("=" * 60)
    show_adk_web()

    print("\n" + "#" * 70)
    print("# Exercise 6 Complete — Next: 07_user_simulation.py")
    print("#" * 70)


if __name__ == "__main__":
    asyncio.run(main())
