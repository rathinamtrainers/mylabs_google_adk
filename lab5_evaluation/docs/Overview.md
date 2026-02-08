# Lab 5: Evaluation & Testing - Overview

## Introduction

Lab 5 focuses on agent evaluation and testing in Google ADK. Unlike traditional software testing with deterministic pass/fail outcomes, agent evaluation requires qualitative metrics to handle the non-deterministic nature of LLM-based systems.

## Why Agent Evaluation is Different

### Traditional Software Testing
- **Deterministic**: Same input always produces same output
- **Binary outcomes**: Tests pass or fail
- **Exact matching**: Compare actual vs expected

### Agent Evaluation Challenges
1. **Non-determinism**: LLM outputs vary between runs with the same input
2. **Subjective quality**: "Good" responses are hard to define objectively
3. **Multi-step processes**: Must evaluate both the journey (trajectory) and the destination (response)

## Core Evaluation Concepts

### 1. Trajectory Evaluation
**What it measures**: Did the agent use the right tools correctly?

- Tool selection correctness
- Tool call ordering
- Parameter accuracy
- Workflow adherence

### 2. Response Evaluation
**What it measures**: Did the agent give the right answer?

- Semantic correctness
- Completeness
- Accuracy
- Tone and style

## Lab Structure

| Exercise | File | Focus Area | Key Concepts |
|----------|------|------------|--------------|
| 1 | `01_evaluation_basics.py` | Fundamentals | EvalSet, EvalCase, evaluation data structures |
| 2 | `02_response_evaluation.py` | Response Quality | ROUGE-1, semantic matching, LLM-as-judge |
| 3 | `03_trajectory_evaluation.py` | Tool Usage | EXACT, IN_ORDER, ANY_ORDER matching |
| 4 | `04_custom_evaluators.py` | Advanced Metrics | Rubrics, hallucination detection, safety |
| 5 | `05_user_simulation.py` | Dynamic Testing | User simulation for conversational flows |

## Built-in Evaluation Metrics

### Trajectory Metrics
- **`tool_trajectory_avg_score`**: Evaluates tool call sequence and arguments

### Response Metrics
- **`response_match_score`**: ROUGE-1 word overlap (fast, deterministic)
- **`final_response_match_v2`**: LLM-judged semantic similarity (slow, accurate)

### Custom Rubric Metrics
- **`rubric_based_final_response_quality_v1`**: Custom response criteria
- **`rubric_based_tool_use_quality_v1`**: Custom tool usage criteria

### Safety & Accuracy Metrics
- **`hallucinations_v1`**: Detects unsupported or contradictory claims
- **`safety_v1`**: Checks for harmful content

## Evaluation Data Structures

### EvalSet
A collection of test cases for an agent.

```json
{
  "eval_set_id": "my_test_suite",
  "name": "Agent Test Suite",
  "description": "Comprehensive tests for MyAgent",
  "eval_cases": [...]
}
```

### EvalCase
A single test scenario representing a complete conversation.

```json
{
  "eval_id": "test_001",
  "conversation": [...],
  "session_input": {
    "app_name": "my_app",
    "user_id": "test_user",
    "state": {}
  }
}
```

### Invocation
A single user-agent interaction (turn).

```json
{
  "user_content": {
    "parts": [{"text": "What is 5 + 3?"}]
  },
  "final_response": {
    "parts": [{"text": "The result is 8."}]
  },
  "intermediate_data": {
    "tool_uses": [
      {"name": "add", "args": {"a": 5, "b": 3}}
    ]
  }
}
```

## Running Evaluations

### Using CLI
```bash
# Run evaluation on a single test file
adk eval my_agent tests/basic.test.json

# Run evaluation on all tests in a directory
adk eval my_agent tests/ --config_file_path test_config.json

# Show detailed results
adk eval my_agent tests/ --print_detailed_results
```

### Using Python API
```python
from google.adk.evaluation.agent_evaluator import AgentEvaluator

await AgentEvaluator.evaluate(
    agent_module="my_agent",
    eval_dataset_file_path_or_dir="tests/",
    num_runs=3  # Run each test multiple times
)
```

## Configuration

### test_config.json
Defines evaluation criteria and thresholds.

```json
{
  "criteria": {
    "tool_trajectory_avg_score": {
      "threshold": 1.0,
      "match_type": "EXACT"
    },
    "response_match_score": 0.8,
    "final_response_match_v2": {
      "threshold": 0.8,
      "judge_model_options": {
        "judge_model": "gemini-2.5-flash",
        "num_samples": 5
      }
    }
  }
}
```

## Best Practices

1. **Start Simple**: Begin with basic metrics, then add custom rubrics
2. **Use Appropriate Match Types**: Choose based on workflow strictness
3. **Set Realistic Thresholds**: 1.0 is often too strict; 0.8 is a good default
4. **Combine Metrics**: Use both trajectory and response evaluation
5. **Test Edge Cases**: Include error scenarios and boundary conditions
6. **Review Results**: Use `--print_detailed_results` to debug failures

## Prerequisites

```bash
cd lab5_evaluation
uv sync  # Install dependencies from pyproject.toml

# Set API key
export GOOGLE_API_KEY="your-api-key"
```

## Dependencies

- `google-adk>=1.19.0`: ADK framework
- `pandas>=2.3.3`: Data manipulation
- `tabulate>=0.9.0`: Table formatting

## Next Steps

1. **Exercise 1**: Learn evaluation fundamentals and data structures
2. **Exercise 2**: Master response evaluation techniques
3. **Exercise 3**: Understand trajectory evaluation patterns
4. **Exercise 4**: Create custom rubrics and safety checks
5. **Exercise 5**: Use user simulation for dynamic testing

## Related Resources

- [Official ADK Evaluation Docs](https://google.github.io/adk-docs/)
- Lab 1: Context & State (agent fundamentals)
- Lab 2: Sessions & Memory (persistence)
- Lab 3: Callbacks & Plugins (interception)
