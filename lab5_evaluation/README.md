# Lab 5: Evaluation & Testing

Hands-on exercises for evaluating agents using the ADK evaluation framework. Every exercise runs real evaluations — no simulations.

## Prerequisites

```bash
cd lab5_evaluation
export GOOGLE_API_KEY="your-api-key"
uv sync
```

## Exercises

| # | File | Topic | What you'll do |
|---|------|-------|----------------|
| 1 | `01_first_evaluation.py` | First Evaluation | Build a `.test.json` file, run `AgentEvaluator.evaluate()` |
| 2 | `02_response_evaluation.py` | Response Metrics | Compare ROUGE-1 vs LLM-as-judge, tune thresholds |
| 3 | `03_trajectory_evaluation.py` | Trajectory Metrics | Try EXACT / IN_ORDER / ANY_ORDER match types |
| 4 | `04_multiturn_evaluation.py` | Multi-Turn | Evaluate multi-turn conversations, use `num_runs` |
| 5 | `05_custom_rubrics.py` | Rubrics & Safety | Custom rubrics, hallucination detection, all 7 metrics |
| 6 | `06_pytest_integration.py` | Pytest & CLI | Run `pytest`, `adk eval` CLI, `adk web` workflow |
| 7 | `07_user_simulation.py` | User Simulation | Conversation scenarios, eval set management, 8th metric |

## Running

```bash
# Run exercises in order (each builds on previous artifacts)
uv run python 01_first_evaluation.py
uv run python 02_response_evaluation.py
uv run python 03_trajectory_evaluation.py
uv run python 04_multiturn_evaluation.py
uv run python 05_custom_rubrics.py
uv run python 06_pytest_integration.py
uv run python 07_user_simulation.py

# Run pytest directly
uv run pytest test_travel_agent.py -v

# Run adk eval CLI
uv run adk eval travel_agent tests/01_basic.test.json
uv run adk eval travel_agent tests/  # all test files
```

## Project Structure

```
lab5_evaluation/
├── travel_agent/                    # Shared agent module
│   ├── __init__.py                  # Exports root_agent
│   └── agent.py                     # Agent + 5 tools
├── tests/                           # Evaluation artifacts
│   ├── 01_basic.test.json           # Single-turn tests
│   ├── 02_response.test.json        # Response-focused tests
│   ├── 03_trajectory.test.json      # Trajectory tests
│   ├── 04_multiturn.test.json       # Multi-turn tests
│   ├── 05_rubrics.test.json         # Rubric tests
│   └── test_config_*.json           # Evaluation configs
├── scenarios/                       # User simulation
│   ├── conversation_scenarios.json
│   └── session_input.json
├── 01_first_evaluation.py           # Exercises
├── ...
├── 07_user_simulation.py
├── test_travel_agent.py             # Pytest file
└── DESIGN.md                        # Design document
```

## All 8 Evaluation Metrics

| Metric | Type | Works with |
|--------|------|------------|
| `tool_trajectory_avg_score` | Trajectory | Static tests |
| `response_match_score` | Response (ROUGE-1) | Static tests |
| `final_response_match_v2` | Response (LLM judge) | Static tests |
| `rubric_based_final_response_quality_v1` | Response (custom) | Static tests |
| `rubric_based_tool_use_quality_v1` | Trajectory (custom) | Static tests |
| `hallucinations_v1` | Grounding | Static + User sim |
| `safety_v1` | Safety | Static + User sim |
| `per_turn_user_simulator_quality_v1` | Sim quality | User sim only |

## Three Ways to Run Evaluations

1. **Python API**: `await AgentEvaluator.evaluate(agent_module="travel_agent", ...)`
2. **CLI**: `uv run adk eval travel_agent tests/01_basic.test.json`
3. **Web UI**: `uv run adk web` (interactive browser-based evaluation)
