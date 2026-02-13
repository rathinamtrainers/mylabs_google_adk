# Lab 5 Evaluation — Redesign Document

## Problem Statement

The current lab5_evaluation exercises teach evaluation **concepts** through printed explanations and hand-coded simulations, but never invoke the actual ADK evaluation framework. A student completing all 5 exercises would understand what ROUGE-1 scoring is or how trajectory match types differ, yet would not know how to set up and run a real evaluation on their own agent.

### Specific gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| No `AgentEvaluator.evaluate()` call | Critical | The framework's primary Python API is never used |
| No `.test.json` files | Critical | No runnable test artifacts exist in the lab |
| No agent module structure | Critical | `adk eval` requires a module with `root_agent`; lab has none |
| No `adk eval` CLI usage | Critical | The primary CLI execution path is never demonstrated |
| No pytest integration | High | CI/CD pattern (`@pytest.mark.asyncio` + `AgentEvaluator`) not shown |
| No `adk eval_set` commands | High | Eval set management (create, add_eval_case) not shown |
| No multi-turn eval cases | High | Only single-turn (1 invocation) shown |
| No `num_runs` | Medium | Non-determinism handling not demonstrated |
| `per_turn_user_simulator_quality_v1` missing | Medium | 8th metric not covered |
| `custom_instructions` for simulator missing | Medium | Advanced simulator config not shown |
| No `adk web` evaluation workflow | Low | Interactive UI-based eval not mentioned |
| `session_input` with initial state | Low | Not demonstrated in a test file |

## Design Goals

1. **Hands-on first** — Every exercise produces runnable artifacts (`.test.json` files, agent modules, pytest files, CLI commands) that the student can execute.
2. **Progressive complexity** — Start with the simplest possible evaluation, layer on metrics and features one at a time.
3. **One shared agent** — Use a single, well-understood agent throughout all exercises so the focus stays on evaluation, not agent construction.
4. **Cover 100% of ADK eval surface** — All 8 metrics, all 3 execution methods (CLI, pytest, Web UI), eval set management, user simulation, and multi-turn evaluation.
5. **Keep conceptual context** — Retain brief explanations of _what_ and _why_ for each concept, but shift the bulk of time from reading printed walls-of-text to running real evaluations.
6. **Follow repository conventions** — Match the section-separator style, `async def main()`, `uv run python` execution, and `pyproject.toml` dependency management used across other labs.

## Architecture

### Shared Agent Module

All exercises evaluate the same agent: a **travel assistant** with enough tool variety to demonstrate every evaluation scenario. It lives in a proper module structure so `adk eval` works.

```
lab5_evaluation/
├── travel_agent/                    # Shared agent module (adk eval target)
│   ├── __init__.py                  # Exports root_agent
│   └── agent.py                     # Agent definition + tools
```

#### Agent tools

| Tool | Purpose | Evaluation scenario it enables |
|------|---------|-------------------------------|
| `search_flights(origin, dest, date)` | Search flights | Trajectory: correct tool + args |
| `get_flight_details(flight_id)` | Get pricing/details | Trajectory: ordered pipeline |
| `book_flight(flight_id, passenger, email)` | Book a flight | Trajectory: strict workflow |
| `cancel_booking(confirmation)` | Cancel booking | Multi-turn eval |
| `get_weather(city)` | Weather at destination | Trajectory: optional extra tool |

The agent instruction defines a clear workflow: search → details → book. This gives deterministic-enough trajectories for evaluation while allowing flexibility for IN_ORDER/ANY_ORDER demos.

### Exercise & File Layout

```
lab5_evaluation/
├── travel_agent/                         # Shared agent module
│   ├── __init__.py
│   └── agent.py
│
├── tests/                                # Evaluation artifacts
│   ├── 01_basic.test.json               # Ex 1: single-turn, trajectory + response
│   ├── 02_response.test.json            # Ex 2: response-focused, multiple references
│   ├── 03_trajectory.test.json          # Ex 3: trajectory with match type configs
│   ├── 04_multiturn.test.json           # Ex 4: multi-turn conversation eval cases
│   ├── 05_rubrics.test.json             # Ex 5: rubric-based eval cases
│   ├── test_config_basic.json           # Ex 1 config
│   ├── test_config_response.json        # Ex 2 config
│   ├── test_config_trajectory.json      # Ex 3 config (EXACT, IN_ORDER, ANY_ORDER)
│   ├── test_config_multiturn.json       # Ex 4 config
│   ├── test_config_rubrics.json         # Ex 5 config (rubrics + hallucinations)
│   ├── test_config_all_metrics.json     # Ex 6 config (all 7 static metrics)
│   └── test_config_user_sim.json        # Ex 7 config (simulation metrics)
│
├── scenarios/                            # User simulation artifacts
│   ├── conversation_scenarios.json       # Ex 7 scenarios
│   └── session_input.json                # Ex 7 session input
│
├── 01_first_evaluation.py               # Run first eval with AgentEvaluator
├── 02_response_evaluation.py            # Response metrics deep-dive
├── 03_trajectory_evaluation.py          # Trajectory metrics deep-dive
├── 04_multiturn_evaluation.py           # Multi-turn conversations
├── 05_custom_rubrics.py                 # Rubrics + hallucination + safety
├── 06_pytest_integration.py             # Pytest patterns for CI/CD
├── 07_user_simulation.py                # User simulation + eval_set CLI
│
├── test_travel_agent.py                 # Runnable pytest file (Ex 6)
│
├── pyproject.toml
├── README.md
└── DESIGN.md                            # This file
```

## Exercises

---

### Exercise 1: Your First Evaluation

**File**: `01_first_evaluation.py`
**Learning objectives**: Understand EvalSet/EvalCase/Invocation data structures; create a `.test.json` file; run `AgentEvaluator.evaluate()` programmatically; interpret results.

#### What the student does

1. **Read**: Brief explanation of why evaluation differs from traditional testing (keep this from current exercise 01, but condense to ~20 lines of print).
2. **Examine**: The `travel_agent/` module — show how `root_agent` is exported.
3. **Generate**: The exercise programmatically builds an `EvalSet` dict with 2 single-turn eval cases (one flight search, one booking) and writes `tests/01_basic.test.json`.
4. **Evaluate**: Call `AgentEvaluator.evaluate()` with default criteria (trajectory=1.0, response=0.8).
5. **Interpret**: Print and explain the `EvalSetResult` — which cases passed/failed and why.

#### Code structure

```python
"""
Lab 5 - Exercise 1: Your First Evaluation
==========================================
...
Run: uv run python 01_first_evaluation.py
"""
import asyncio
import json
from pathlib import Path
from google.adk.evaluation.agent_evaluator import AgentEvaluator

# Part 1: Brief conceptual intro (print, ~20 lines)
# Part 2: Show the travel agent structure
# Part 3: Build and write .test.json programmatically
# Part 4: Run AgentEvaluator.evaluate()
# Part 5: Interpret results
# Part 6: Show equivalent CLI command (printed, not executed)

async def main():
    # ... parts 1-6

    # Part 4 (core):
    results = await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/01_basic.test.json",
        num_runs=1,
        print_detailed_results=True,
    )

    # Part 6:
    print("  Equivalent CLI command:")
    print("    uv run adk eval travel_agent tests/01_basic.test.json --print_detailed_results")
```

#### Test artifacts created

**`tests/01_basic.test.json`** — 2 eval cases, single-turn each, with expected tool_uses and final_response.

**`tests/test_config_basic.json`**:
```json
{
  "criteria": {
    "tool_trajectory_avg_score": 1.0,
    "response_match_score": 0.8
  }
}
```

#### Key concepts introduced
- EvalSet → EvalCase → Invocation hierarchy
- `AgentEvaluator.evaluate()` signature
- `.test.json` file format
- Default criteria (trajectory=1.0, response=0.8)
- Agent module convention (`root_agent` export)

---

### Exercise 2: Response Evaluation

**File**: `02_response_evaluation.py`
**Learning objectives**: Understand ROUGE-1 vs LLM-as-judge; configure `response_match_score` and `final_response_match_v2`; see how different thresholds affect pass/fail.

#### What the student does

1. **Quick recap**: ROUGE-1 = word overlap (fast, deterministic); LLM-as-judge = semantic (slower, smarter). Keep the ROUGE-1 manual calculation from the current exercise as a brief demo (~10 example pairs), then immediately contrast with the real framework.
2. **Create test file**: `tests/02_response.test.json` — 4 eval cases with varying response similarity:
   - Exact match case
   - Paraphrase case (same meaning, different words)
   - Partial match case (missing info)
   - Wrong answer case
3. **Run with ROUGE-1 only**: `response_match_score: 0.8` — show which pass/fail.
4. **Run with LLM-as-judge**: `final_response_match_v2` with `judge_model_options` — show the paraphrase case now passes.
5. **Run with both combined**: Show how combining metrics works.
6. **Threshold sweep**: Run the same test file at thresholds 0.5, 0.7, 0.9 to show the effect.

#### Code structure

```python
async def main():
    # Part 1: ROUGE-1 quick demo (manual, ~10 pairs — condensed from current 02)
    # Part 2: Build tests/02_response.test.json
    # Part 3: Evaluate with response_match_score only
    results_rouge = await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/02_response.test.json",
        num_runs=1,
    )
    # Part 4: Evaluate with final_response_match_v2
    # (swap config file)
    # Part 5: Evaluate with both metrics
    # Part 6: Threshold sweep loop
```

#### Test artifacts

**`tests/02_response.test.json`** — 4 eval cases focused on response variety.

**`tests/test_config_response.json`** — three variants written by the exercise:
```json
// Variant A: ROUGE-1 only
{ "criteria": { "response_match_score": 0.8 } }

// Variant B: LLM-as-judge only
{ "criteria": {
    "final_response_match_v2": {
      "threshold": 0.8,
      "judge_model_options": {
        "judge_model": "gemini-2.0-flash",
        "num_samples": 3
      }
    }
  }
}

// Variant C: Both
{ "criteria": {
    "response_match_score": 0.6,
    "final_response_match_v2": { "threshold": 0.8, ... }
  }
}
```

#### Key concepts introduced
- `response_match_score` configuration
- `final_response_match_v2` with `judge_model_options`
- `num_samples` and majority voting
- Threshold tuning
- Combining metrics

---

### Exercise 3: Trajectory Evaluation

**File**: `03_trajectory_evaluation.py`
**Learning objectives**: Understand EXACT/IN_ORDER/ANY_ORDER match types; configure `tool_trajectory_avg_score`; see how match type choice affects results.

#### What the student does

1. **Quick recap**: Trajectory = sequence of tool calls. Three match types with visual table (condensed from current exercise 03).
2. **Create test file**: `tests/03_trajectory.test.json` — 3 eval cases with different trajectory patterns:
   - **Case A**: Simple search → expect `[search_flights]`
   - **Case B**: Full pipeline → expect `[search_flights, get_flight_details, book_flight]`
   - **Case C**: Flexible info gathering → expect `[search_flights, get_weather]` (either order OK)
3. **Run with EXACT**: Show Case C likely fails (agent may call in different order).
4. **Run with IN_ORDER**: Show Case C still may fail (order matters).
5. **Run with ANY_ORDER**: Show Case C now passes.
6. **Compare all three**: Side-by-side result table.
7. **CLI equivalent**: Print the `adk eval` command with `--config_file_path`.

#### Code structure

```python
async def main():
    # Part 1: Match types visual recap (brief)
    # Part 2: Build tests/03_trajectory.test.json
    # Part 3-5: Run with each match type config
    for match_type in ["EXACT", "IN_ORDER", "ANY_ORDER"]:
        write_config(match_type)
        results = await AgentEvaluator.evaluate(
            agent_module="travel_agent",
            eval_dataset_file_path_or_dir="tests/03_trajectory.test.json",
            num_runs=1,
        )
        display_results(match_type, results)
    # Part 6: Comparison table
    # Part 7: CLI command
```

#### Test artifacts

**`tests/03_trajectory.test.json`** — 3 eval cases focused on trajectory patterns.

**`tests/test_config_trajectory.json`** — dynamically rewritten by the exercise with different `match_type` values.

#### Key concepts introduced
- `match_type`: EXACT, IN_ORDER, ANY_ORDER
- `tool_trajectory_avg_score` with nested config
- How agent instruction wording affects trajectory
- Choosing the right match type for different workflows

---

### Exercise 4: Multi-Turn Evaluation

**File**: `04_multiturn_evaluation.py`
**Learning objectives**: Evaluate multi-turn conversations; use `session_input` with initial state; use `num_runs` for non-determinism; understand how conversations flow through multiple invocations.

#### What the student does

1. **Explain multi-turn**: An EvalCase's `conversation` array can have multiple `Invocation` objects, representing a multi-turn dialogue. This tests stateful agent behavior.
2. **Create test file**: `tests/04_multiturn.test.json` — 2 eval cases:
   - **Case A**: 3-turn booking flow (search → choose → book)
   - **Case B**: 2-turn search-then-cancel flow
3. **Show `session_input`**: Demonstrate `session_input` field with `app_name`, `user_id`, and initial `state` (e.g., `{"user:loyalty_tier": "gold"}`).
4. **Run with `num_runs=1`**: Show baseline results.
5. **Run with `num_runs=3`**: Show how multiple runs handle non-determinism — results may vary across runs.
6. **Compare**: Print per-run breakdown to show variance.

#### Test artifacts

**`tests/04_multiturn.test.json`**:
```json
{
  "eval_set_id": "multiturn_tests",
  "eval_cases": [
    {
      "eval_id": "booking_flow",
      "conversation": [
        {
          "invocation_id": "turn-1",
          "user_content": {"parts": [{"text": "Find flights from NYC to LA on Dec 15"}]},
          "final_response": {"parts": [{"text": "...flights found..."}]},
          "intermediate_data": {
            "tool_uses": [{"name": "search_flights", "args": {"origin": "NYC", "destination": "LA", "date": "2025-12-15"}}]
          }
        },
        {
          "invocation_id": "turn-2",
          "user_content": {"parts": [{"text": "Book FL001 for John Smith, john@example.com"}]},
          "final_response": {"parts": [{"text": "...booking confirmed..."}]},
          "intermediate_data": {
            "tool_uses": [{"name": "book_flight", "args": {"flight_id": "FL001", "passenger": "John Smith", "email": "john@example.com"}}]
          }
        }
      ],
      "session_input": {
        "app_name": "travel_agent",
        "user_id": "test_user",
        "state": {}
      }
    }
  ]
}
```

**`tests/test_config_multiturn.json`** — trajectory IN_ORDER + response 0.7 (looser for multi-turn).

#### Key concepts introduced
- Multi-turn `conversation` array with multiple `Invocation` objects
- `session_input` with initial state
- `num_runs` parameter for non-determinism
- Per-run result inspection
- Looser thresholds for multi-turn (agent responses are less predictable)

---

### Exercise 5: Custom Rubrics, Hallucination & Safety

**File**: `05_custom_rubrics.py`
**Learning objectives**: Write rubric-based criteria; configure `hallucinations_v1`; understand `safety_v1` requirements; combine all 7 static metrics in one config.

#### What the student does

1. **Rubric introduction**: Brief explanation of rubric_based_final_response_quality_v1 and rubric_based_tool_use_quality_v1. Show the rubric structure.
2. **Create test file**: `tests/05_rubrics.test.json` — 3 eval cases designed to test rubric scenarios:
   - **Case A**: Good response (helpful, accurate, uses tools correctly)
   - **Case B**: Hallucination-prone (agent might add info not in tool output)
   - **Case C**: Edge case (ambiguous query, tests tool selection quality)
3. **Run with response rubrics**: Define 3 rubrics (accuracy, helpfulness, conciseness) and evaluate.
4. **Run with tool use rubrics**: Define 2 rubrics (correct tool order, parameter accuracy) and evaluate.
5. **Run with hallucinations_v1**: Show `evaluate_intermediate_nl_responses` option.
6. **Explain safety_v1**: Note the `GOOGLE_CLOUD_PROJECT` requirement. Show config but skip execution if env var not set.
7. **All-metrics config**: Build and display `tests/test_config_all_metrics.json` combining all 7 static metrics. Run it.

#### Code structure

```python
async def main():
    # Part 1: Rubric structure explanation
    # Part 2: Build tests/05_rubrics.test.json

    # Part 3: Response quality rubrics
    write_config_with_rubrics("response", rubrics=[...])
    results = await AgentEvaluator.evaluate(...)

    # Part 4: Tool use quality rubrics
    write_config_with_rubrics("tool_use", rubrics=[...])
    results = await AgentEvaluator.evaluate(...)

    # Part 5: Hallucination detection
    write_config_hallucinations()
    results = await AgentEvaluator.evaluate(...)

    # Part 6: Safety (conditional on GOOGLE_CLOUD_PROJECT)
    if os.environ.get("GOOGLE_CLOUD_PROJECT"):
        # run safety eval
    else:
        print("  Skipping safety_v1 (requires GOOGLE_CLOUD_PROJECT)")

    # Part 7: All metrics combined
    write_all_metrics_config()
    results = await AgentEvaluator.evaluate(...)
```

#### Test artifacts

**`tests/05_rubrics.test.json`** — 3 eval cases.

**`tests/test_config_rubrics.json`** — rubric configs.

**`tests/test_config_all_metrics.json`** — all 7 static metrics:
```json
{
  "criteria": {
    "tool_trajectory_avg_score": {"threshold": 0.9, "match_type": "IN_ORDER"},
    "response_match_score": 0.6,
    "final_response_match_v2": {
      "threshold": 0.8,
      "judge_model_options": {"judge_model": "gemini-2.0-flash", "num_samples": 3}
    },
    "rubric_based_final_response_quality_v1": {
      "threshold": 0.8,
      "judge_model_options": {"judge_model": "gemini-2.0-flash", "num_samples": 3},
      "rubrics": [
        {"rubric_id": "accuracy", "rubric_content": {"text_property": "The response accurately reflects the data returned by tools."}},
        {"rubric_id": "helpfulness", "rubric_content": {"text_property": "The response is helpful and answers the user's question."}},
        {"rubric_id": "conciseness", "rubric_content": {"text_property": "The response is concise and under 5 sentences."}}
      ]
    },
    "rubric_based_tool_use_quality_v1": {
      "threshold": 0.8,
      "judge_model_options": {"judge_model": "gemini-2.0-flash", "num_samples": 3},
      "rubrics": [
        {"rubric_id": "search_first", "rubric_content": {"text_property": "The agent searches for flights before attempting to book."}},
        {"rubric_id": "correct_params", "rubric_content": {"text_property": "The agent passes the correct parameters from user input to tools."}}
      ]
    },
    "hallucinations_v1": {"threshold": 0.8, "evaluate_intermediate_nl_responses": true},
    "safety_v1": 0.9
  }
}
```

#### Key concepts introduced
- Rubric structure (`rubric_id`, `rubric_content.text_property`)
- `judge_model_options` (`judge_model`, `num_samples`)
- `hallucinations_v1` with `evaluate_intermediate_nl_responses`
- `safety_v1` and its GCP requirement
- All 7 static metrics combined

---

### Exercise 6: Pytest Integration & CLI

**File**: `06_pytest_integration.py` (educational script that explains patterns)
**File**: `test_travel_agent.py` (actual runnable pytest file)
**Learning objectives**: Write pytest-based evaluation tests; use `adk eval` CLI; understand CI/CD integration patterns.

#### What the student does

1. **Examine `test_travel_agent.py`**: The exercise reads and explains the pytest file structure.
2. **Run pytest**: `uv run pytest test_travel_agent.py -v`
3. **Run `adk eval` CLI**: Execute via the exercise for each test file:
   - `uv run adk eval travel_agent tests/01_basic.test.json --print_detailed_results`
   - `uv run adk eval travel_agent tests/ --config_file_path tests/test_config_all_metrics.json`
4. **Run `adk eval` on directory**: Show running all tests at once.
5. **Show `adk web` evaluation**: Explain that `uv run adk web` provides an interactive UI for evaluation — create sessions, save as test cases, configure metrics via sliders, view traces. Print instructions for the student to try it.

#### Pytest file: `test_travel_agent.py`

```python
"""
Pytest-based evaluation tests for the travel agent.

Run: uv run pytest test_travel_agent.py -v
"""
import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator


@pytest.mark.asyncio
async def test_basic_functionality():
    """Test basic search and booking functionality."""
    await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/01_basic.test.json",
        num_runs=1,
        print_detailed_results=True,
    )


@pytest.mark.asyncio
async def test_response_quality():
    """Test response quality with semantic matching."""
    await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/02_response.test.json",
        num_runs=2,
        print_detailed_results=True,
    )


@pytest.mark.asyncio
async def test_trajectory_exact():
    """Test trajectory with exact matching."""
    await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/03_trajectory.test.json",
        num_runs=1,
        print_detailed_results=True,
    )


@pytest.mark.asyncio
async def test_multiturn_conversations():
    """Test multi-turn conversation evaluation."""
    await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/04_multiturn.test.json",
        num_runs=2,
        print_detailed_results=True,
    )


@pytest.mark.asyncio
async def test_all_metrics():
    """Comprehensive evaluation with all metrics."""
    await AgentEvaluator.evaluate(
        agent_module="travel_agent",
        eval_dataset_file_path_or_dir="tests/05_rubrics.test.json",
        num_runs=1,
        print_detailed_results=True,
    )
```

#### Code structure of `06_pytest_integration.py`

```python
async def main():
    # Part 1: Read and explain test_travel_agent.py structure
    # Part 2: Run pytest programmatically (subprocess)
    # Part 3: Run adk eval CLI (subprocess) on individual test files
    # Part 4: Run adk eval CLI on entire tests/ directory
    # Part 5: Explain adk web evaluation workflow
```

#### Key concepts introduced
- `@pytest.mark.asyncio` decorator
- `pytest-asyncio` dependency
- `AgentEvaluator.evaluate()` in test functions
- `adk eval` CLI syntax and flags
- `adk eval` on a directory (runs all `.test.json` files)
- `adk web` interactive evaluation UI
- CI/CD integration pattern

---

### Exercise 7: User Simulation & Eval Set Management

**File**: `07_user_simulation.py`
**Learning objectives**: Create conversation scenarios; manage eval sets with `adk eval_set` commands; run user simulation evaluation; understand `per_turn_user_simulator_quality_v1`; configure `custom_instructions` for the simulator.

#### What the student does

1. **Explain user simulation**: Brief recap — an LLM plays the user following a conversation plan. When to use vs static tests.
2. **Create scenario files**: Write `scenarios/conversation_scenarios.json` and `scenarios/session_input.json`.
3. **Create eval set via CLI**: Run `adk eval_set create travel_agent travel_sim_eval_set`.
4. **Add eval cases via CLI**: Run `adk eval_set add_eval_case` with the scenario files.
5. **Configure simulation**: Write `tests/test_config_user_sim.json` with:
   - `hallucinations_v1`
   - `safety_v1`
   - `per_turn_user_simulator_quality_v1`
   - `user_simulator_config` with model, max_allowed_invocations, custom_instructions
6. **Run evaluation**: `adk eval travel_agent travel_sim_eval_set --config_file_path tests/test_config_user_sim.json --print_detailed_results`
7. **Metrics compatibility recap**: Show which metrics work with static tests vs user simulation.

#### Scenario artifacts

**`scenarios/conversation_scenarios.json`**:
```json
{
  "scenarios": [
    {
      "starting_prompt": "I need to book a flight.",
      "conversation_plan": "Search for flights from New York to Los Angeles on December 15th. Ask about the cheapest option. Book it for Jane Doe, jane@example.com."
    },
    {
      "starting_prompt": "Can you help me with travel?",
      "conversation_plan": "Ask about flights to Chicago. Change your mind and ask about flights to Miami instead. Pick the afternoon flight."
    },
    {
      "starting_prompt": "I need to cancel my booking.",
      "conversation_plan": "Provide confirmation number CONF-FL001-001 and ask to cancel. Confirm the cancellation."
    }
  ]
}
```

**`scenarios/session_input.json`**:
```json
{
  "app_name": "travel_agent",
  "user_id": "sim_user"
}
```

#### User simulation config

**`tests/test_config_user_sim.json`**:
```json
{
  "criteria": {
    "hallucinations_v1": {
      "threshold": 0.8,
      "evaluate_intermediate_nl_responses": true
    },
    "safety_v1": 0.9,
    "per_turn_user_simulator_quality_v1": {
      "threshold": 0.8
    }
  },
  "user_simulator_config": {
    "model": "gemini-2.0-flash",
    "max_allowed_invocations": 15,
    "custom_instructions": "You are testing a travel booking agent. Follow the conversation plan: {conversation_plan}. When the task is complete, say '{stop_signal}'. Conversation so far: {conversation_history}"
  }
}
```

#### Code structure

```python
async def main():
    # Part 1: User simulation concept (brief)
    # Part 2: Write scenario files
    # Part 3: Run `adk eval_set create` (subprocess)
    # Part 4: Run `adk eval_set add_eval_case` (subprocess)
    # Part 5: Write user_sim config (with custom_instructions + per_turn metric)
    # Part 6: Run `adk eval` on the eval set (subprocess)
    # Part 7: Metrics compatibility matrix (print)
```

#### Key concepts introduced
- `ConversationScenario` (starting_prompt + conversation_plan)
- `adk eval_set create` / `adk eval_set add_eval_case` CLI
- `user_simulator_config` (model, max_allowed_invocations, custom_instructions)
- `per_turn_user_simulator_quality_v1` metric
- `custom_instructions` with `{stop_signal}`, `{conversation_plan}`, `{conversation_history}` placeholders
- Metrics compatibility: static vs user simulation

---

## Shared Agent Module: `travel_agent/`

### `travel_agent/__init__.py`

```python
from .agent import root_agent

__all__ = ["root_agent"]
```

### `travel_agent/agent.py`

```python
"""Travel assistant agent for evaluation exercises."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool


# --- Tool functions ---

def search_flights(origin: str, destination: str, date: str) -> dict:
    """Search for available flights."""
    flights = [
        {"flight_id": "FL001", "price": 299, "departure": "08:00", "arrival": "11:00", "airline": "SkyAir"},
        {"flight_id": "FL002", "price": 399, "departure": "14:00", "arrival": "17:00", "airline": "CloudJet"},
        {"flight_id": "FL003", "price": 249, "departure": "20:00", "arrival": "23:00", "airline": "SkyAir"},
    ]
    return {"origin": origin, "destination": destination, "date": date, "flights": flights}


def get_flight_details(flight_id: str) -> dict:
    """Get detailed flight information."""
    details = {
        "FL001": {"flight_id": "FL001", "price": 299, "class": "economy", "baggage": "1 carry-on", "meal": "snack"},
        "FL002": {"flight_id": "FL002", "price": 399, "class": "economy+", "baggage": "1 checked", "meal": "full"},
        "FL003": {"flight_id": "FL003", "price": 249, "class": "economy", "baggage": "1 carry-on", "meal": "none"},
    }
    return details.get(flight_id, {"error": f"Flight {flight_id} not found"})


def book_flight(flight_id: str, passenger_name: str, email: str) -> dict:
    """Book a flight for a passenger."""
    return {
        "success": True,
        "confirmation_number": f"CONF-{flight_id}-001",
        "flight_id": flight_id,
        "passenger": passenger_name,
        "email": email,
    }


def cancel_booking(confirmation_number: str) -> dict:
    """Cancel a flight booking."""
    return {"success": True, "message": f"Booking {confirmation_number} cancelled. Refund will be processed in 5-7 days."}


def get_weather(city: str) -> dict:
    """Get weather information for a city."""
    weather = {
        "new york": {"temp_f": 35, "condition": "cloudy", "humidity": 65},
        "los angeles": {"temp_f": 72, "condition": "sunny", "humidity": 30},
        "chicago": {"temp_f": 28, "condition": "snowy", "humidity": 70},
        "miami": {"temp_f": 80, "condition": "sunny", "humidity": 75},
    }
    return weather.get(city.lower(), {"error": f"Weather data not available for {city}"})


# --- Agent definition ---

root_agent = LlmAgent(
    name="TravelAgent",
    model="gemini-2.0-flash",
    instruction="""You are a travel assistant. Help users search for flights, book tickets, and get travel information.

    Workflow for booking:
    1. Search for flights using search_flights
    2. If user wants details, use get_flight_details
    3. To book, use book_flight with passenger name and email

    For cancellations, use cancel_booking with the confirmation number.
    You can also check weather at destinations using get_weather.

    Be helpful, concise, and always confirm details before booking.""",
    tools=[
        FunctionTool(func=search_flights),
        FunctionTool(func=get_flight_details),
        FunctionTool(func=book_flight),
        FunctionTool(func=cancel_booking),
        FunctionTool(func=get_weather),
    ],
)
```

## Dependencies

### `pyproject.toml`

```toml
[project]
name = "lab5-evaluation"
version = "0.1.0"
description = "Lab 5: Agent Evaluation & Testing"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "google-adk>=1.19.0",
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
]
```

Note: `pandas`, `tabulate`, and `rouge-score` are removed — no longer needed since we use the framework's built-in metrics rather than hand-coding them.

## Feature Coverage Matrix

| ADK Feature | Exercise | How demonstrated |
|-------------|----------|-----------------|
| `AgentEvaluator.evaluate()` | 1, 2, 3, 4, 5 | Called directly in Python |
| `.test.json` files | 1, 2, 3, 4, 5 | Created programmatically and stored in `tests/` |
| `test_config.json` | 1, 2, 3, 4, 5, 7 | Written with varying criteria |
| `adk eval` CLI | 6 | Executed via subprocess |
| `adk eval_set create` | 7 | Executed via subprocess |
| `adk eval_set add_eval_case` | 7 | Executed via subprocess |
| `adk web` evaluation | 6 | Explained with instructions |
| pytest integration | 6 | `test_travel_agent.py` |
| `root_agent` module convention | 1 | `travel_agent/__init__.py` |
| `tool_trajectory_avg_score` | 1, 3 | Default and explicit configs |
| `response_match_score` | 1, 2 | ROUGE-1 threshold config |
| `final_response_match_v2` | 2 | LLM-as-judge config |
| `rubric_based_final_response_quality_v1` | 5 | Custom response rubrics |
| `rubric_based_tool_use_quality_v1` | 5 | Custom tool use rubrics |
| `hallucinations_v1` | 5, 7 | With and without intermediate responses |
| `safety_v1` | 5, 7 | Conditional on GCP env var |
| `per_turn_user_simulator_quality_v1` | 7 | User simulation config |
| EXACT match type | 3 | Explicit config |
| IN_ORDER match type | 3, 4 | Explicit config |
| ANY_ORDER match type | 3 | Explicit config |
| Multi-turn eval cases | 4 | Multiple Invocations in conversation |
| `session_input` with state | 4 | Initial state in eval case |
| `num_runs` | 4 | Compared 1 vs 3 runs |
| `judge_model_options` | 2, 5 | judge_model + num_samples |
| `user_simulator_config` | 7 | model, max_allowed_invocations |
| `custom_instructions` | 7 | With placeholder variables |
| ConversationScenario | 7 | starting_prompt + conversation_plan |
| Threshold tuning | 2 | Sweep across values |
| All 7 static metrics combined | 5 | Single config file |
| Agent module structure | 1 | `travel_agent/` with `root_agent` |

## What Gets Removed

The current exercises (01–05) are **replaced**, not retained alongside the new ones. The new exercises cover every concept the old ones taught, plus the missing practical features. Specifically:

| Current content | Disposition |
|----------------|-------------|
| Conceptual explanations (ROUGE-1 theory, match type diagrams) | **Condensed** into brief intros in new exercises |
| Hand-coded `evaluate_trajectory()` | **Removed** — replaced by real `tool_trajectory_avg_score` |
| Hand-coded `calculate_rouge1_score()` | **Kept briefly** in Ex 2 as a 10-line demo, then contrasted with framework |
| Config JSON printed as text | **Replaced** by actual config files written to disk and used |
| Calculator/Weather/Shopping/Banking/Flight agents | **Replaced** by single shared `travel_agent/` module |
| `docs/` directory | **Updated** to reflect new exercise structure |

## Execution Order

The recommended execution order matches the exercise numbering:

```
Exercise 1 → Creates tests/01_basic.test.json, runs first evaluation
Exercise 2 → Creates tests/02_response.test.json, explores response metrics
Exercise 3 → Creates tests/03_trajectory.test.json, explores trajectory metrics
Exercise 4 → Creates tests/04_multiturn.test.json, multi-turn + num_runs
Exercise 5 → Creates tests/05_rubrics.test.json + all-metrics config
Exercise 6 → Runs pytest + CLI on all existing test files
Exercise 7 → Creates eval set with scenarios, runs user simulation
```

Exercises 1–5 each produce artifacts that Exercise 6 consumes. Exercise 7 is independent.

## Open Questions

1. **Should exercises auto-generate `.test.json` files or should they be pre-written?**
   Recommendation: Exercises 1-5 generate them programmatically (teaches the schema) but also commit pre-written versions as fallbacks so Exercise 6 always has files to work with.

2. **Should `safety_v1` be demonstrated if it requires GCP credentials?**
   Recommendation: Include it in the config and attempt to run, but gracefully skip with an explanatory message if `GOOGLE_CLOUD_PROJECT` is not set.

3. **Should the `docs/` folder be updated simultaneously?**
   Recommendation: Yes, but as a follow-up pass after the exercises are validated.
