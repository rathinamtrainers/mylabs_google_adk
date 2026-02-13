"""
Lab 5 - Exercise 5: Custom Rubrics, Hallucination & Safety
===========================================================

This exercise covers advanced evaluation metrics:
1. Rubric-based response quality evaluation
2. Rubric-based tool use quality evaluation
3. Hallucination detection (hallucinations_v1)
4. Safety evaluation (safety_v1)
5. All 7 static metrics combined

Run: uv run python 05_custom_rubrics.py
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
# Part 1: Rubric Concepts
# =============================================================================

def explain_rubrics():
    """Explain rubric-based evaluation."""
    print("""
    RUBRIC-BASED EVALUATION
    =======================
    Rubrics = custom yes/no criteria you define. An LLM judge evaluates each.

    Two types:
      rubric_based_final_response_quality_v1  — evaluates the RESPONSE
      rubric_based_tool_use_quality_v1        — evaluates TOOL USAGE

    Rubric structure:
      {
        "rubric_id": "accuracy",
        "rubric_content": {
          "text_property": "The response accurately reflects tool output data."
        }
      }

    Tips for writing rubrics:
      GOOD: "The response includes the flight price in dollars."
      BAD:  "The response is good." (too vague)
      GOOD: "The agent calls search_flights before book_flight."
      BAD:  "The agent uses tools properly." (not evaluable)
    """)


# =============================================================================
# Part 2: Response Quality Rubrics
# =============================================================================

async def run_response_rubrics():
    """Evaluate with response quality rubrics."""
    print("    Evaluating with 3 response quality rubrics...")

    config = {
        "criteria": {
            "rubric_based_final_response_quality_v1": {
                "threshold": 0.8,
                "judge_model_options": {
                    "judge_model": "gemini-2.0-flash",
                    "num_samples": 3,
                },
                "rubrics": [
                    {
                        "rubric_id": "accuracy",
                        "rubric_content": {
                            "text_property": "The response accurately reflects the data returned by tools."
                        },
                    },
                    {
                        "rubric_id": "helpfulness",
                        "rubric_content": {
                            "text_property": "The response is helpful and answers the user's question."
                        },
                    },
                    {
                        "rubric_id": "conciseness",
                        "rubric_content": {
                            "text_property": "The response is concise and under 5 sentences."
                        },
                    },
                ],
            }
        }
    }
    Path("tests/test_config.json").write_text(json.dumps(config, indent=2))

    results = await safe_evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/05_rubrics.test.json",
        num_runs=1,
        print_detailed_results=True,
    )
    return results


# =============================================================================
# Part 3: Tool Use Quality Rubrics
# =============================================================================

async def run_tool_use_rubrics():
    """Evaluate with tool use quality rubrics."""
    print("    Evaluating with 2 tool use quality rubrics...")

    config = {
        "criteria": {
            "rubric_based_tool_use_quality_v1": {
                "threshold": 0.8,
                "judge_model_options": {
                    "judge_model": "gemini-2.0-flash",
                    "num_samples": 3,
                },
                "rubrics": [
                    {
                        "rubric_id": "search_first",
                        "rubric_content": {
                            "text_property": "The agent searches for flights before attempting to book."
                        },
                    },
                    {
                        "rubric_id": "correct_params",
                        "rubric_content": {
                            "text_property": "The agent passes the correct parameters from user input to tools."
                        },
                    },
                ],
            }
        }
    }
    Path("tests/test_config.json").write_text(json.dumps(config, indent=2))

    results = await safe_evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/05_rubrics.test.json",
        num_runs=1,
        print_detailed_results=True,
    )
    return results


# =============================================================================
# Part 4: Hallucination Detection
# =============================================================================

async def run_hallucination_eval():
    """Evaluate with hallucination detection."""
    print("""
    HALLUCINATION DETECTION (hallucinations_v1)
    ===========================================
    Checks if agent responses are grounded in tool outputs.
    Each sentence is labeled: SUPPORTED, UNSUPPORTED, CONTRADICTORY, NOT_APPLICABLE.
    Score = (SUPPORTED + NOT_APPLICABLE) / Total sentences.

    evaluate_intermediate_nl_responses: true  → also checks intermediate responses
    """)

    config = {
        "criteria": {
            "hallucinations_v1": {
                "threshold": 0.8,
                "evaluate_intermediate_nl_responses": True,
            }
        }
    }
    Path("tests/test_config.json").write_text(json.dumps(config, indent=2))

    results = await safe_evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/05_rubrics.test.json",
        num_runs=1,
        print_detailed_results=True,
    )
    return results


# =============================================================================
# Part 5: Safety Evaluation
# =============================================================================

def explain_safety():
    """Explain safety_v1 and its requirements."""
    print("""
    SAFETY EVALUATION (safety_v1)
    =============================
    Checks for: hate speech, harassment, dangerous info, privacy violations.
    Delegates to Vertex AI General AI Eval SDK.

    REQUIREMENT: Needs GOOGLE_CLOUD_PROJECT environment variable.
    Config: {"criteria": {"safety_v1": 0.9}}

    Skipping execution unless GOOGLE_CLOUD_PROJECT is set.
    """)

    if os.environ.get("GOOGLE_CLOUD_PROJECT"):
        print(f"    GOOGLE_CLOUD_PROJECT={os.environ['GOOGLE_CLOUD_PROJECT']}")
        print("    (Would run safety evaluation here)")
    else:
        print("    GOOGLE_CLOUD_PROJECT not set — skipping safety_v1 execution.")
        print("    To enable: export GOOGLE_CLOUD_PROJECT=your-project-id")


# =============================================================================
# Part 6: All 7 Static Metrics Combined
# =============================================================================

async def run_all_metrics():
    """Run evaluation with all 7 static metrics."""
    print("""
    ALL 7 STATIC METRICS COMBINED
    ==============================
    This config uses every built-in metric (excluding safety_v1 if no GCP):

      1. tool_trajectory_avg_score (IN_ORDER, 0.9)
      2. response_match_score (0.6)
      3. final_response_match_v2 (0.8)
      4. rubric_based_final_response_quality_v1 (0.8, 3 rubrics)
      5. rubric_based_tool_use_quality_v1 (0.8, 2 rubrics)
      6. hallucinations_v1 (0.8)
      7. safety_v1 (0.9) — if GOOGLE_CLOUD_PROJECT is set
    """)

    config = {
        "criteria": {
            "tool_trajectory_avg_score": {"threshold": 0.9, "match_type": "IN_ORDER"},
            "response_match_score": 0.6,
            "final_response_match_v2": {
                "threshold": 0.8,
                "judge_model_options": {"judge_model": "gemini-2.0-flash", "num_samples": 3},
            },
            "rubric_based_final_response_quality_v1": {
                "threshold": 0.8,
                "judge_model_options": {"judge_model": "gemini-2.0-flash", "num_samples": 3},
                "rubrics": [
                    {"rubric_id": "accuracy", "rubric_content": {"text_property": "The response accurately reflects the data returned by tools."}},
                    {"rubric_id": "helpfulness", "rubric_content": {"text_property": "The response is helpful and answers the user's question."}},
                    {"rubric_id": "conciseness", "rubric_content": {"text_property": "The response is concise and under 5 sentences."}},
                ],
            },
            "rubric_based_tool_use_quality_v1": {
                "threshold": 0.8,
                "judge_model_options": {"judge_model": "gemini-2.0-flash", "num_samples": 3},
                "rubrics": [
                    {"rubric_id": "search_first", "rubric_content": {"text_property": "The agent searches for flights before attempting to book."}},
                    {"rubric_id": "correct_params", "rubric_content": {"text_property": "The agent passes the correct parameters from user input to tools."}},
                ],
            },
            "hallucinations_v1": {"threshold": 0.8, "evaluate_intermediate_nl_responses": True},
        }
    }

    # Include safety_v1 only if GCP project is set
    if os.environ.get("GOOGLE_CLOUD_PROJECT"):
        config["criteria"]["safety_v1"] = 0.9

    Path("tests/test_config.json").write_text(json.dumps(config, indent=2))

    results = await safe_evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/05_rubrics.test.json",
        num_runs=1,
        print_detailed_results=True,
    )
    return results


# =============================================================================
# Main
# =============================================================================

async def main():
    os.chdir(Path(__file__).parent)

    print("\n" + "#" * 70)
    print("# Lab 5 Exercise 5: Custom Rubrics, Hallucination & Safety")
    print("#" * 70)

    # Part 1
    print("\n" + "=" * 60)
    print("PART 1: Rubric Concepts")
    print("=" * 60)
    explain_rubrics()

    # Part 2
    print("\n" + "=" * 60)
    print("PART 2: Response Quality Rubrics")
    print("=" * 60)
    await run_response_rubrics()

    # Part 3
    print("\n" + "=" * 60)
    print("PART 3: Tool Use Quality Rubrics")
    print("=" * 60)
    await run_tool_use_rubrics()

    # Part 4
    print("\n" + "=" * 60)
    print("PART 4: Hallucination Detection")
    print("=" * 60)
    await run_hallucination_eval()

    # Part 5
    print("\n" + "=" * 60)
    print("PART 5: Safety Evaluation")
    print("=" * 60)
    explain_safety()

    # Part 6
    print("\n" + "=" * 60)
    print("PART 6: All Metrics Combined")
    print("=" * 60)
    await run_all_metrics()

    print("\n" + "#" * 70)
    print("# Exercise 5 Complete — Next: 06_pytest_integration.py")
    print("#" * 70)


if __name__ == "__main__":
    asyncio.run(main())
