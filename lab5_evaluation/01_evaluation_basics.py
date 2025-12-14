"""
Lab 5 - Exercise 1: Evaluation Basics
======================================

This exercise introduces agent evaluation fundamentals:
1. Why evaluate agents?
2. What to evaluate (trajectory vs response)
3. Evaluation data structures (EvalSet, EvalCase)
4. Running simple evaluations
5. Understanding evaluation results

Run: uv run python 01_evaluation_basics.py
"""

import asyncio
import json
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# =============================================================================
# Part 1: Why Evaluate Agents?
# =============================================================================

def explain_evaluation():
    """Explain why we need agent evaluation."""
    print("""
    WHY EVALUATE AGENTS?
    ====================

    Traditional software: Deterministic "pass/fail" tests work well
    LLM agents: Probabilistic - same input can give different outputs!

    CHALLENGES:
    -----------
    1. Non-determinism: LLM outputs vary between runs
    2. Quality is subjective: "Good" response is hard to define
    3. Multi-step processes: Need to evaluate the journey, not just destination

    SOLUTION: QUALITATIVE EVALUATION
    ---------------------------------
    Instead of exact matching, we evaluate:

    1. TRAJECTORY (the journey):
       - Did the agent use the right tools?
       - Did it call them in the correct order?
       - Were the parameters correct?

    2. RESPONSE (the destination):
       - Is the final answer semantically correct?
       - Does it match the expected output?
       - Is it safe and appropriate?

    EVALUATION METRICS:
    -------------------
    ┌─────────────────────────────────────────────────────────────┐
    │  Metric                          │  What it measures        │
    ├─────────────────────────────────────────────────────────────┤
    │  tool_trajectory_avg_score       │  Tool call correctness   │
    │  response_match_score            │  Word overlap (ROUGE-1)  │
    │  final_response_match_v2         │  Semantic similarity     │
    │  rubric_based_*                  │  Custom criteria         │
    │  hallucinations_v1               │  Factual grounding       │
    │  safety_v1                       │  Safety/harmlessness     │
    └─────────────────────────────────────────────────────────────┘
    """)


# =============================================================================
# Part 2: Sample Agent for Evaluation
# =============================================================================

# Simple calculator agent that we'll evaluate
def add(a: int, b: int) -> dict:
    """Add two numbers together."""
    return {"result": a + b}

def subtract(a: int, b: int) -> dict:
    """Subtract b from a."""
    return {"result": a - b}

def multiply(a: int, b: int) -> dict:
    """Multiply two numbers."""
    return {"result": a * b}

def divide(a: int, b: int) -> dict:
    """Divide a by b."""
    if b == 0:
        return {"error": "Cannot divide by zero"}
    return {"result": a / b}


def create_calculator_agent():
    """Create a simple calculator agent for evaluation demos."""
    add_tool = FunctionTool(func=add)
    subtract_tool = FunctionTool(func=subtract)
    multiply_tool = FunctionTool(func=multiply)
    divide_tool = FunctionTool(func=divide)

    agent = LlmAgent(
        name="CalculatorAgent",
        model="gemini-2.0-flash",
        instruction="""You are a calculator assistant.
        Use the provided math tools to perform calculations.
        Always use tools - never calculate in your head.
        After getting the result, report it clearly.""",
        tools=[add_tool, subtract_tool, multiply_tool, divide_tool],
    )

    return agent


# =============================================================================
# Part 3: Understanding Eval Data Structures
# =============================================================================

def explain_eval_structures():
    """Explain evaluation data structures."""
    print("""
    EVALUATION DATA STRUCTURES
    ==========================

    1. EvalSet - A collection of test cases
    ┌─────────────────────────────────────────┐
    │  EvalSet                                │
    │  ├── eval_set_id: unique identifier     │
    │  ├── name: descriptive name             │
    │  ├── description: what it tests         │
    │  └── eval_cases: [EvalCase, ...]        │
    └─────────────────────────────────────────┘

    2. EvalCase - A single test scenario (conversation)
    ┌─────────────────────────────────────────┐
    │  EvalCase                               │
    │  ├── eval_id: unique identifier         │
    │  ├── conversation: [Invocation, ...]    │
    │  └── session_input: initial state       │
    └─────────────────────────────────────────┘

    3. Invocation - A single user-agent interaction (turn)
    ┌─────────────────────────────────────────┐
    │  Invocation                             │
    │  ├── user_content: what user said       │
    │  ├── final_response: expected answer    │
    │  └── intermediate_data:                 │
    │      ├── tool_uses: expected tools      │
    │      └── intermediate_responses: [...]  │
    └─────────────────────────────────────────┘

    EXAMPLE TEST FILE (*.test.json):
    ---------------------------------
    {
      "eval_set_id": "calculator_tests",
      "eval_cases": [
        {
          "eval_id": "addition_test",
          "conversation": [
            {
              "user_content": {"parts": [{"text": "What is 5 + 3?"}]},
              "final_response": {"parts": [{"text": "The result is 8."}]},
              "intermediate_data": {
                "tool_uses": [
                  {"name": "add", "args": {"a": 5, "b": 3}}
                ]
              }
            }
          ]
        }
      ]
    }
    """)


# =============================================================================
# Part 4: Manual Evaluation (Without AgentEvaluator)
# =============================================================================

async def manual_evaluation_demo():
    """
    Demonstrate manual evaluation by running agent and comparing results.
    This shows what happens "under the hood" during evaluation.
    """
    print("\n  Creating calculator agent...")
    agent = create_calculator_agent()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=agent,
        app_name="eval_demo",
        session_service=session_service,
    )

    await session_service.create_session(
        app_name="eval_demo",
        user_id="user1",
        session_id="eval_session",
        state={}
    )

    # Test cases: (query, expected_tool, expected_args, expected_result_contains)
    test_cases = [
        ("What is 5 + 3?", "add", {"a": 5, "b": 3}, "8"),
        ("Calculate 10 minus 4", "subtract", {"a": 10, "b": 4}, "6"),
        ("What is 7 times 6?", "multiply", {"a": 7, "b": 6}, "42"),
    ]

    results = []

    for query, expected_tool, expected_args, expected_contains in test_cases:
        print(f"\n  Testing: '{query}'")

        user_message = types.Content(parts=[types.Part(text=query)])

        actual_tool_calls = []
        final_response = ""

        async for event in runner.run_async(
            user_id="user1",
            session_id="eval_session",
            new_message=user_message,
        ):
            # Capture tool calls from events
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        actual_tool_calls.append({
                            "name": part.function_call.name,
                            "args": dict(part.function_call.args) if part.function_call.args else {}
                        })

            # Capture final response
            if event.is_final_response() and event.content:
                final_response = event.content.parts[0].text

        # Evaluate trajectory (tool use)
        tool_match = False
        if actual_tool_calls:
            for call in actual_tool_calls:
                if call["name"] == expected_tool:
                    tool_match = True
                    break

        # Evaluate response (contains expected result)
        response_match = expected_contains in final_response

        result = {
            "query": query,
            "tool_match": tool_match,
            "response_match": response_match,
            "actual_tools": actual_tool_calls,
            "final_response": final_response[:80],
        }
        results.append(result)

        print(f"    Tool match: {'PASS' if tool_match else 'FAIL'}")
        print(f"    Response match: {'PASS' if response_match else 'FAIL'}")

    return results


# =============================================================================
# Part 5: Evaluation Criteria Configuration
# =============================================================================

def explain_eval_config():
    """Explain evaluation configuration options."""
    print("""
    EVALUATION CONFIGURATION (test_config.json)
    ============================================

    Configure thresholds for different metrics:

    {
      "criteria": {
        // Tool trajectory: 1.0 = exact match required
        "tool_trajectory_avg_score": 1.0,

        // Response match: 0.8 = 80% word overlap required
        "response_match_score": 0.8,

        // LLM-judged semantic match
        "final_response_match_v2": {
          "threshold": 0.8,
          "judge_model_options": {
            "judge_model": "gemini-2.5-flash",
            "num_samples": 5
          }
        }
      }
    }

    MATCH TYPES FOR TRAJECTORY:
    ---------------------------
    "tool_trajectory_avg_score": {
      "threshold": 1.0,
      "match_type": "EXACT"     // Perfect match
      // OR "IN_ORDER"          // Same order, extras allowed
      // OR "ANY_ORDER"         // Same tools, any order
    }

    DEFAULT CRITERIA (if not specified):
    ------------------------------------
    - tool_trajectory_avg_score: 1.0 (100% match)
    - response_match_score: 0.8 (80% word overlap)
    """)


# =============================================================================
# Part 6: Creating Test Files
# =============================================================================

def create_sample_test_file():
    """Create a sample test file structure."""

    # This is what a proper test file looks like
    eval_set = {
        "eval_set_id": "calculator_eval_set",
        "name": "Calculator Agent Tests",
        "description": "Basic arithmetic operation tests",
        "eval_cases": [
            {
                "eval_id": "addition_simple",
                "conversation": [
                    {
                        "invocation_id": "inv-001",
                        "user_content": {
                            "parts": [{"text": "What is 5 + 3?"}],
                            "role": "user"
                        },
                        "final_response": {
                            "parts": [{"text": "The result of 5 + 3 is 8."}],
                            "role": "model"
                        },
                        "intermediate_data": {
                            "tool_uses": [
                                {
                                    "name": "add",
                                    "args": {"a": 5, "b": 3}
                                }
                            ],
                            "intermediate_responses": []
                        }
                    }
                ],
                "session_input": {
                    "app_name": "calculator",
                    "user_id": "test_user",
                    "state": {}
                }
            },
            {
                "eval_id": "subtraction_simple",
                "conversation": [
                    {
                        "invocation_id": "inv-002",
                        "user_content": {
                            "parts": [{"text": "Calculate 10 minus 4"}],
                            "role": "user"
                        },
                        "final_response": {
                            "parts": [{"text": "10 minus 4 equals 6."}],
                            "role": "model"
                        },
                        "intermediate_data": {
                            "tool_uses": [
                                {
                                    "name": "subtract",
                                    "args": {"a": 10, "b": 4}
                                }
                            ],
                            "intermediate_responses": []
                        }
                    }
                ],
                "session_input": {
                    "app_name": "calculator",
                    "user_id": "test_user",
                    "state": {}
                }
            }
        ]
    }

    print("\n  Sample EvalSet structure:")
    print(f"    - eval_set_id: {eval_set['eval_set_id']}")
    print(f"    - Number of eval cases: {len(eval_set['eval_cases'])}")
    for case in eval_set['eval_cases']:
        print(f"    - Case '{case['eval_id']}':")
        for inv in case['conversation']:
            query = inv['user_content']['parts'][0]['text']
            tools = [t['name'] for t in inv['intermediate_data']['tool_uses']]
            print(f"        Query: {query}")
            print(f"        Expected tools: {tools}")

    return eval_set


async def main():
    print("\n" + "#"*70)
    print("# Lab 5 Exercise 1: Evaluation Basics")
    print("#"*70)

    # =========================================================================
    # Part 1: Why Evaluate?
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: Why Evaluate Agents?")
    print("="*60)
    explain_evaluation()

    # =========================================================================
    # Part 2: Sample Agent
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: Sample Calculator Agent")
    print("="*60)
    print("  Created a calculator agent with: add, subtract, multiply, divide")

    agent = create_calculator_agent()
    print(f"  Agent name: {agent.name}")
    print(f"  Tools: {[t.name for t in agent.tools]}")

    # =========================================================================
    # Part 3: Eval Data Structures
    # =========================================================================
    print("\n" + "="*60)
    print("PART 3: Evaluation Data Structures")
    print("="*60)
    explain_eval_structures()

    # =========================================================================
    # Part 4: Manual Evaluation
    # =========================================================================
    print("\n" + "="*60)
    print("PART 4: Manual Evaluation Demo")
    print("="*60)
    print("  Running agent and evaluating results manually...")

    results = await manual_evaluation_demo()

    print("\n  Summary:")
    passed = sum(1 for r in results if r['tool_match'] and r['response_match'])
    print(f"    Passed: {passed}/{len(results)}")

    # =========================================================================
    # Part 5: Eval Config
    # =========================================================================
    print("\n" + "="*60)
    print("PART 5: Evaluation Configuration")
    print("="*60)
    explain_eval_config()

    # =========================================================================
    # Part 6: Test File Structure
    # =========================================================================
    print("\n" + "="*60)
    print("PART 6: Creating Test Files")
    print("="*60)

    eval_set = create_sample_test_file()

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "#"*70)
    print("# Summary: Evaluation Basics")
    print("#"*70)
    print("""
    KEY CONCEPTS:
    -------------
    1. Agent evaluation differs from traditional testing
       - Non-deterministic outputs require qualitative metrics

    2. Two things to evaluate:
       - TRAJECTORY: Did agent use right tools correctly?
       - RESPONSE: Is the final answer correct?

    3. Evaluation data structures:
       - EvalSet: Collection of test cases
       - EvalCase: Single conversation to test
       - Invocation: Single user-agent turn

    4. Test files:
       - Use .test.json extension
       - Follow EvalSet schema
       - Optional test_config.json for criteria

    RUNNING EVALUATIONS:
    --------------------
    # Using pytest (recommended for CI/CD)
    from google.adk.evaluation.agent_evaluator import AgentEvaluator

    await AgentEvaluator.evaluate(
        agent_module="my_agent",
        eval_dataset_file_path_or_dir="tests/my_test.test.json",
    )

    # Using CLI
    adk eval my_agent tests/my_test.test.json

    NEXT STEPS:
    -----------
    - Exercise 2: Response evaluation in depth
    - Exercise 3: Trajectory evaluation patterns
    - Exercise 4: Custom rubric-based evaluation
    - Exercise 5: User simulation for dynamic testing
    """)


if __name__ == "__main__":
    asyncio.run(main())
