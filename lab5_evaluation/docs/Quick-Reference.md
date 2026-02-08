# Lab 5: Quick Reference Guide

## Evaluation Metrics at a Glance

| Metric | Type | Measures | Speed | Best For |
|--------|------|----------|-------|----------|
| `tool_trajectory_avg_score` | Trajectory | Tool sequence & args | Fast | Workflow validation |
| `response_match_score` | Response | Word overlap (ROUGE-1) | Fast | CI/CD, regressions |
| `final_response_match_v2` | Response | Semantic similarity | Slow | Quality assessment |
| `rubric_based_final_response_quality_v1` | Response | Custom criteria | Slow | Domain-specific |
| `rubric_based_tool_use_quality_v1` | Trajectory | Custom workflow | Slow | Process validation |
| `hallucinations_v1` | Response | Factual accuracy | Medium | Data integrity |
| `safety_v1` | Response | Harmful content | Medium | User-facing apps |

## Match Types (Trajectory Evaluation)

| Match Type | Order Matters? | Extras Allowed? | Use Case |
|------------|----------------|-----------------|----------|
| **EXACT** | Yes | No | Critical workflows, payments |
| **IN_ORDER** | Yes | Yes | Ordered pipelines |
| **ANY_ORDER** | No | Yes | Flexible operations, research |

## Configuration Templates

### Basic Evaluation

```json
{
  "criteria": {
    "tool_trajectory_avg_score": 1.0,
    "response_match_score": 0.8
  }
}
```

### Comprehensive Evaluation

```json
{
  "criteria": {
    "tool_trajectory_avg_score": {
      "threshold": 0.9,
      "match_type": "IN_ORDER"
    },
    "response_match_score": 0.7,
    "final_response_match_v2": {
      "threshold": 0.8,
      "judge_model_options": {
        "judge_model": "gemini-2.5-flash",
        "num_samples": 3
      }
    },
    "hallucinations_v1": {
      "threshold": 0.9,
      "evaluate_intermediate_nl_responses": true
    },
    "safety_v1": 0.95
  }
}
```

### User Simulation

```json
{
  "criteria": {
    "hallucinations_v1": {
      "threshold": 0.8,
      "evaluate_intermediate_nl_responses": true
    },
    "safety_v1": 0.9
  },
  "user_simulator_config": {
    "model": "gemini-2.5-flash",
    "max_allowed_invocations": 20
  }
}
```

### Custom Rubrics

```json
{
  "criteria": {
    "rubric_based_final_response_quality_v1": {
      "threshold": 0.8,
      "judge_model_options": {
        "judge_model": "gemini-2.5-flash",
        "num_samples": 3
      },
      "rubrics": [
        {
          "rubric_id": "conciseness",
          "rubric_content": {
            "text_property": "The response is concise and to the point."
          }
        },
        {
          "rubric_id": "completeness",
          "rubric_content": {
            "text_property": "The response includes all requested information."
          }
        }
      ]
    }
  }
}
```

## Test File Structure

### Minimal Test File

```json
{
  "eval_set_id": "my_tests",
  "eval_cases": [
    {
      "eval_id": "test_1",
      "conversation": [
        {
          "user_content": {
            "parts": [{"text": "Hello"}]
          },
          "final_response": {
            "parts": [{"text": "Hi there!"}]
          }
        }
      ]
    }
  ]
}
```

### Test with Trajectory

```json
{
  "eval_set_id": "tool_tests",
  "eval_cases": [
    {
      "eval_id": "search_test",
      "conversation": [
        {
          "user_content": {
            "parts": [{"text": "Find laptops"}]
          },
          "final_response": {
            "parts": [{"text": "I found 2 laptops."}]
          },
          "intermediate_data": {
            "tool_uses": [
              {
                "name": "search_products",
                "args": {"query": "laptop"}
              }
            ]
          }
        }
      ]
    }
  ]
}
```

### Conversation Scenario (User Simulation)

```json
{
  "scenarios": [
    {
      "starting_prompt": "I need help booking a flight",
      "conversation_plan": "Book a round-trip flight from NYC to LA, departing Dec 15, returning Dec 22."
    }
  ]
}
```

## CLI Commands

### Run Evaluation

```bash
# Single test file
adk eval my_agent tests/basic.test.json

# All tests in directory
adk eval my_agent tests/ --config_file_path test_config.json

# Show detailed results
adk eval my_agent tests/ --print_detailed_results
```

### Manage Eval Sets

```bash
# Create eval set
adk eval_set create my_agent my_eval_set

# Add static test case
adk eval_set add_eval_case my_agent my_eval_set \
  --eval_dataset_file_path tests/basic.test.json

# Add user simulation case
adk eval_set add_eval_case my_agent my_eval_set \
  --scenarios_file conversation_scenarios.json \
  --session_input_file session_input.json
```

## Python API

### Basic Evaluation

```python
from google.adk.evaluation.agent_evaluator import AgentEvaluator

await AgentEvaluator.evaluate(
    agent_module="my_agent",
    eval_dataset_file_path_or_dir="tests/"
)
```

### Multiple Runs

```python
await AgentEvaluator.evaluate(
    agent_module="my_agent",
    eval_dataset_file_path_or_dir="tests/",
    num_runs=3  # Run each test 3 times
)
```

## Threshold Guidelines

### Recommended Thresholds

| Metric | Strict | Default | Flexible |
|--------|--------|---------|----------|
| Trajectory | 1.0 | 0.9 | 0.8 |
| Response (ROUGE) | 0.9 | 0.8 | 0.6 |
| Response (Semantic) | 0.9 | 0.8 | 0.7 |
| Hallucinations | 0.95 | 0.9 | 0.8 |
| Safety | 0.98 | 0.95 | 0.9 |
| Custom Rubrics | 1.0 | 0.8 | 0.7 |

### By Use Case

| Use Case | Trajectory | Response | Safety |
|----------|------------|----------|--------|
| **Payments** | 1.0 (EXACT) | 0.9 | 0.98 |
| **Customer Service** | 0.8 (ANY_ORDER) | 0.8 | 0.95 |
| **Research** | 0.7 (ANY_ORDER) | 0.7 | 0.9 |
| **Medical** | 1.0 (EXACT) | 0.95 | 0.98 |

## Rubric Writing Template

```json
{
  "rubric_id": "descriptive_snake_case_id",
  "rubric_content": {
    "text_property": "Clear yes/no statement about what to check."
  }
}
```

### Good Rubric Examples

✓ "The response includes all three weather metrics: temperature, condition, and humidity."
✓ "The response uses formal language without slang or abbreviations."
✓ "The agent calls search_products before get_product_details."
✓ "The response is 50 words or fewer."

### Bad Rubric Examples

✗ "The response is good" (too vague)
✗ "The response feels professional" (not objective)
✗ "The response is accurate and concise" (two concepts)
✗ "The response is short" (ambiguous)

## Debugging Checklist

### Trajectory Failures

- [ ] Check tool names match exactly (case-sensitive)
- [ ] Verify argument values are correct
- [ ] Confirm match_type is appropriate
- [ ] Review agent instruction clarity
- [ ] Consider if expected trajectory is realistic

### Response Failures

- [ ] Check threshold isn't too strict (try 0.7 instead of 0.9)
- [ ] Use semantic matching for paraphrases
- [ ] Verify reference response has core info
- [ ] Consider multiple valid reference responses
- [ ] Run multiple times to handle LLM variance

### Hallucination Failures

- [ ] Check tool outputs are complete
- [ ] Verify agent isn't adding unsupported claims
- [ ] Review intermediate responses
- [ ] Ensure context includes necessary info
- [ ] Check if claims are in instructions

### User Simulation Issues

- [ ] Conversation plan is clear and specific
- [ ] max_allowed_invocations is sufficient
- [ ] Agent instruction guides user collection
- [ ] Review transcript for stuck patterns
- [ ] Check if agent asks one question at a time

## Project Structure Best Practices

```
my_agent/
├── agent.py                           # Agent definition
├── test_config.json                   # Evaluation criteria
├── tests/
│   ├── static/
│   │   ├── basic.test.json           # Core functionality
│   │   ├── edge_cases.test.json      # Edge cases
│   │   └── multi_turn.test.json      # Multi-turn
│   └── dynamic/
│       ├── conversation_scenarios.json  # User simulation
│       └── session_input.json
└── docs/
    └── evaluation_results.md          # Document findings
```

## Common Patterns

### Test Organization by Risk

```
tests/
├── critical/          # Threshold: 1.0 (must pass)
├── important/         # Threshold: 0.9
├── standard/          # Threshold: 0.8
└── nice_to_have/      # Threshold: 0.7
```

### Progressive Testing

```bash
# 1. Quick smoke test
adk eval my_agent tests/smoke.test.json

# 2. Core functionality
adk eval my_agent tests/core/

# 3. Full suite
adk eval my_agent tests/ --config_file_path test_config.json

# 4. With user simulation
adk eval my_agent my_eval_set --print_detailed_results
```

## Metrics Compatibility Matrix

| Metric | Static Tests | User Simulation |
|--------|--------------|-----------------|
| tool_trajectory_avg_score | ✓ | ✗ |
| response_match_score | ✓ | ✗ |
| final_response_match_v2 | ✓ | ✗ |
| rubric_based_final_response_quality_v1 | ✓ | ✗ |
| rubric_based_tool_use_quality_v1 | ✓ | ✗ |
| hallucinations_v1 | ✓ | ✓ |
| safety_v1 | ✓ | ✓ |

## Running Exercises

```bash
cd lab5_evaluation

# Install dependencies
uv sync

# Set API key
export GOOGLE_API_KEY="your-api-key"

# Run exercises
uv run python 01_evaluation_basics.py
uv run python 02_response_evaluation.py
uv run python 03_trajectory_evaluation.py
uv run python 04_custom_evaluators.py
uv run python 05_user_simulation.py
```

## Key Formulas

### ROUGE-1 F1 Score

```
Precision = Overlapping Words / Candidate Words
Recall = Overlapping Words / Reference Words
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

### Hallucination Score

```
Score = (SUPPORTED + NOT_APPLICABLE) / Total Sentences
```

### Rubric Score

```
Score = Sum of Rubric Scores / Number of Rubrics
Each rubric: 1.0 (yes) or 0.0 (no)
```

## Troubleshooting

### "Evaluation failed"
- Check API key is set
- Verify agent module path
- Review test file JSON syntax

### "Low scores on response evaluation"
- Lower threshold (try 0.7)
- Use semantic matching
- Review reference responses

### "Trajectory mismatch"
- Check tool names (case-sensitive)
- Verify arguments
- Try more flexible match type

### "User simulation hits max_invocations"
- Increase max_allowed_invocations
- Simplify conversation plan
- Check agent instruction

## Quick Decision Trees

### Choosing Evaluation Type

```
Is conversation dynamic?
├─ Yes → Use user simulation
└─ No → Use static tests

Is exact wording required?
├─ Yes → Use response_match_score
└─ No → Use final_response_match_v2

Is tool order critical?
├─ Yes, strict → Use EXACT
├─ Yes, flexible → Use IN_ORDER
└─ No → Use ANY_ORDER
```

### Choosing Metrics

```
Need to validate facts?
└─ Yes → Add hallucinations_v1

User-facing application?
└─ Yes → Add safety_v1

Domain-specific criteria?
└─ Yes → Add rubric_based_*

Critical workflow?
└─ Yes → Add tool_trajectory (EXACT)

Response quality matters?
└─ Yes → Add final_response_match_v2
```

## Resources

- **Official Docs**: https://google.github.io/adk-docs/
- **Lab Files**: `lab5_evaluation/*.py`
- **Documentation**: `lab5_evaluation/docs/*.md`

## Exercise Summary

| Exercise | File | Key Topics |
|----------|------|------------|
| 1 | `01_evaluation_basics.py` | Data structures, manual evaluation |
| 2 | `02_response_evaluation.py` | ROUGE-1, semantic matching |
| 3 | `03_trajectory_evaluation.py` | EXACT, IN_ORDER, ANY_ORDER |
| 4 | `04_custom_evaluators.py` | Rubrics, hallucinations, safety |
| 5 | `05_user_simulation.py` | Dynamic conversations |
