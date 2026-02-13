"""
Lab 5 - Exercise 2: Response Evaluation
========================================

This exercise explores response evaluation metrics in depth:
1. ROUGE-1 scoring (manual demo + framework)
2. LLM-as-judge semantic matching
3. Combining both metrics
4. Threshold tuning

Run: uv run python 02_response_evaluation.py
"""

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from google.adk.evaluation.agent_evaluator import AgentEvaluator


# =============================================================================
# Helper: safe_evaluate wraps AgentEvaluator.evaluate() to catch assertion
# errors from failing metrics. This lets us demonstrate both passing and
# failing thresholds without crashing the exercise.
# =============================================================================

async def safe_evaluate(**kwargs):
    """Run AgentEvaluator.evaluate(), catching threshold assertion failures."""
    try:
        results = await AgentEvaluator.evaluate(**kwargs)
        print("\n    >>> All metrics PASSED thresholds.\n")
        return results
    except AssertionError as e:
        print(f"\n    >>> Some metrics FAILED (expected for educational demo):")
        for line in str(e).strip().splitlines():
            print(f"        {line}")
        print()
        return None
    except Exception as e:
        print(f"\n    >>> Evaluation error: {type(e).__name__}: {e}\n")
        return None


# =============================================================================
# Part 1: ROUGE-1 Quick Demo
# =============================================================================

def rouge1_demo():
    """Brief manual ROUGE-1 demo to build intuition."""
    print("""
    ROUGE-1 = Word overlap between expected and actual response
    Fast and deterministic, but doesn't understand meaning.
    """)

    def rouge1_f1(ref: str, cand: str) -> float:
        ref_words = set(ref.lower().split())
        cand_words = set(cand.lower().split())
        overlap = ref_words & cand_words
        if not overlap:
            return 0.0
        p = len(overlap) / len(cand_words)
        r = len(overlap) / len(ref_words)
        return round(2 * p * r / (p + r), 3)

    pairs = [
        ("The result is 42", "The result is 42", "Exact match"),
        ("The result is 42", "42 is the result", "Same words, different order"),
        ("The temperature is 72 degrees", "It's 72°F outside", "Same meaning, different words"),
        ("Flight FL001 costs $299", "The price of FL001 is $299", "Paraphrase"),
        ("Booking confirmed", "Your reservation has been confirmed", "Synonym-heavy"),
    ]

    for ref, cand, desc in pairs:
        score = rouge1_f1(ref, cand)
        status = "PASS" if score >= 0.8 else "FAIL" if score < 0.5 else "BORDERLINE"
        print(f"    {desc:35s}  F1={score:.3f}  [{status}]")

    print("""
    Key insight: ROUGE-1 misses semantic equivalence.
    ADK's response_match_score uses this under the hood.
    For meaning-aware matching, use final_response_match_v2 (LLM-as-judge).
    """)


# =============================================================================
# Part 2: Run with ROUGE-1 Only (threshold=0.8 — expect failures)
# =============================================================================

async def run_rouge_eval():
    """Evaluate with response_match_score only at a strict threshold."""
    print("""
    Running with response_match_score: 0.8 (strict)
    LLM responses naturally rephrase, so ROUGE-1 at 0.8 often fails.
    This demonstrates why high ROUGE-1 thresholds are problematic.
    """)

    config = {"criteria": {"response_match_score": 0.8}}
    Path("tests/test_config.json").write_text(json.dumps(config, indent=2))

    await safe_evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/02_response.test.json",
        num_runs=1,
        print_detailed_results=True,
    )


# =============================================================================
# Part 3: Run with LLM-as-Judge
# =============================================================================

async def run_semantic_eval():
    """Evaluate with final_response_match_v2 (LLM-as-judge)."""
    print("""
    LLM-AS-JUDGE (final_response_match_v2)
    =======================================
    An LLM judges whether actual and expected responses convey the same info.
    Uses majority voting across multiple samples for robustness.
    This should pass where ROUGE-1 failed, since it understands meaning.
    """)

    config = {
        "criteria": {
            "final_response_match_v2": {
                "threshold": 0.8,
                "judge_model_options": {
                    "judge_model": "gemini-2.0-flash",
                    "num_samples": 3,
                },
            }
        }
    }
    Path("tests/test_config.json").write_text(json.dumps(config, indent=2))

    await safe_evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/02_response.test.json",
        num_runs=1,
        print_detailed_results=True,
    )


# =============================================================================
# Part 4: Run with Both Combined
# =============================================================================

async def run_combined_eval():
    """Evaluate with both response metrics."""
    print("""
    COMBINING METRICS
    =================
    Use ROUGE-1 as a fast baseline + LLM-as-judge for semantic accuracy.
    Lower the ROUGE-1 threshold when combining (0.4 instead of 0.8).
    """)

    config = {
        "criteria": {
            "response_match_score": 0.4,
            "final_response_match_v2": {
                "threshold": 0.8,
                "judge_model_options": {
                    "judge_model": "gemini-2.0-flash",
                    "num_samples": 3,
                },
            },
        }
    }
    Path("tests/test_config.json").write_text(json.dumps(config, indent=2))

    await safe_evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/02_response.test.json",
        num_runs=1,
        print_detailed_results=True,
    )


# =============================================================================
# Part 5: Threshold Sweep
# =============================================================================

async def threshold_sweep():
    """Run ROUGE-1 at multiple thresholds to show the effect."""
    print("""
    THRESHOLD SWEEP
    ===============
    Running the same tests at different ROUGE-1 thresholds.
    Watch how more cases fail as the threshold increases:
    """)

    for threshold in [0.3, 0.5, 0.8]:
        print(f"\n    --- response_match_score threshold: {threshold} ---")
        config = {"criteria": {"response_match_score": threshold}}
        Path("tests/test_config.json").write_text(json.dumps(config, indent=2))

        await safe_evaluate(
            agent_module="travel_agent",
            eval_dataset_file_path_or_dir="tests/02_response.test.json",
            num_runs=1,
            print_detailed_results=True,
        )


# =============================================================================
# Main
# =============================================================================

async def main():
    os.chdir(Path(__file__).parent)

    print("\n" + "#" * 70)
    print("# Lab 5 Exercise 2: Response Evaluation")
    print("#" * 70)

    # Part 1
    print("\n" + "=" * 60)
    print("PART 1: ROUGE-1 Quick Demo")
    print("=" * 60)
    rouge1_demo()

    # Part 2
    print("\n" + "=" * 60)
    print("PART 2: Evaluate with ROUGE-1 Only (strict threshold)")
    print("=" * 60)
    await run_rouge_eval()

    # Part 3
    print("\n" + "=" * 60)
    print("PART 3: Evaluate with LLM-as-Judge")
    print("=" * 60)
    await run_semantic_eval()

    # Part 4
    print("\n" + "=" * 60)
    print("PART 4: Evaluate with Both Combined")
    print("=" * 60)
    await run_combined_eval()

    # Part 5
    print("\n" + "=" * 60)
    print("PART 5: Threshold Sweep")
    print("=" * 60)
    await threshold_sweep()

    # Summary
    print("\n" + "#" * 70)
    print("# Summary")
    print("#" * 70)
    print("""
    response_match_score      — ROUGE-1 word overlap (fast, deterministic)
    final_response_match_v2   — LLM-as-judge semantic match (slower, smarter)

    Recommendations:
      CI/CD fast checks → response_match_score at 0.5
      Quality assessment → final_response_match_v2 at 0.8
      Best of both      → combine with lower ROUGE threshold (0.4)

    Next: 03_trajectory_evaluation.py
    """)


if __name__ == "__main__":
    asyncio.run(main())
