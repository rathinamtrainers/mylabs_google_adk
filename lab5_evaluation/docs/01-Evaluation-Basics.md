# Exercise 1: Evaluation Basics

## Overview

This exercise introduces the fundamentals of agent evaluation in Google ADK, covering why evaluation is different from traditional testing and how to structure evaluation data.

**File**: `01_evaluation_basics.py`

## Learning Objectives

1. Understand why agent evaluation differs from traditional testing
2. Learn evaluation data structures (EvalSet, EvalCase, Invocation)
3. Run manual evaluation to understand the process
4. Create test files with proper structure
5. Configure evaluation criteria

## Part 1: Why Evaluate Agents?

### The Challenge

**Traditional Software**:
- Deterministic behavior
- Exact output matching
- Simple pass/fail tests

**LLM Agents**:
- Non-deterministic outputs
- Same input → different outputs
- Subjective quality assessment

### Solution: Qualitative Evaluation

Instead of exact matching, evaluate:

#### 1. Trajectory (The Journey)
- Did the agent use the right tools?
- Were tools called in correct order?
- Were parameters correct?

#### 2. Response (The Destination)
- Is the final answer semantically correct?
- Does it match expected output?
- Is it safe and appropriate?

## Part 2: Evaluation Metrics

### Core Metrics Table

| Metric | What It Measures | Type |
|--------|------------------|------|
| `tool_trajectory_avg_score` | Tool call correctness | Trajectory |
| `response_match_score` | Word overlap (ROUGE-1) | Response |
| `final_response_match_v2` | Semantic similarity | Response |
| `rubric_based_*` | Custom criteria | Both |
| `hallucinations_v1` | Factual grounding | Response |
| `safety_v1` | Safety/harmlessness | Response |

## Part 3: Data Structures

### EvalSet
A collection of test cases.

```python
{
    "eval_set_id": "calculator_eval_set",
    "name": "Calculator Agent Tests",
    "description": "Basic arithmetic operation tests",
    "eval_cases": [...]
}
```

**Fields**:
- `eval_set_id`: Unique identifier for the test suite
- `name`: Human-readable name
- `description`: What this test suite covers
- `eval_cases`: Array of EvalCase objects

### EvalCase
A single test scenario (complete conversation).

```python
{
    "eval_id": "addition_simple",
    "conversation": [...],
    "session_input": {
        "app_name": "calculator",
        "user_id": "test_user",
        "state": {}
    }
}
```

**Fields**:
- `eval_id`: Unique identifier for this test case
- `conversation`: Array of Invocation objects
- `session_input`: Initial session state

### Invocation
A single user-agent turn.

```python
{
    "invocation_id": "inv-001",
    "user_content": {
        "parts": [{"text": "What is 5 + 3?"}],
        "role": "user"
    },
    "final_response": {
        "parts": [{"text": "The result is 8."}],
        "role": "model"
    },
    "intermediate_data": {
        "tool_uses": [
            {"name": "add", "args": {"a": 5, "b": 3}}
        ],
        "intermediate_responses": []
    }
}
```

**Fields**:
- `user_content`: What the user said
- `final_response`: Expected agent response
- `intermediate_data`: Expected tool calls and intermediate steps

## Part 4: Sample Agent

The exercise creates a simple calculator agent:

```python
def create_calculator_agent():
    agent = LlmAgent(
        name="CalculatorAgent",
        model="gemini-2.0-flash",
        instruction="""You are a calculator assistant.
        Use the provided math tools to perform calculations.
        Always use tools - never calculate in your head.""",
        tools=[add_tool, subtract_tool, multiply_tool, divide_tool]
    )
    return agent
```

**Tools**:
- `add(a, b)`: Addition
- `subtract(a, b)`: Subtraction
- `multiply(a, b)`: Multiplication
- `divide(a, b)`: Division

## Part 5: Manual Evaluation

The exercise demonstrates manual evaluation by:

1. Running the agent with test queries
2. Capturing tool calls from events
3. Capturing final responses
4. Comparing against expected values

### Example Test Case

```python
test_cases = [
    ("What is 5 + 3?", "add", {"a": 5, "b": 3}, "8"),
    ("Calculate 10 minus 4", "subtract", {"a": 10, "b": 4}, "6"),
    ("What is 7 times 6?", "multiply", {"a": 7, "b": 6}, "42"),
]
```

### Evaluation Logic

```python
# Evaluate trajectory (tool use)
tool_match = False
for call in actual_tool_calls:
    if call["name"] == expected_tool:
        tool_match = True
        break

# Evaluate response (contains expected result)
response_match = expected_contains in final_response
```

## Part 6: Test File Structure

### File Naming Convention
- Use `.test.json` extension
- Example: `calculator_tests.test.json`

### Complete Test File Example

```json
{
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
              {"name": "add", "args": {"a": 5, "b": 3}}
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
              {"name": "subtract", "args": {"a": 10, "b": 4}}
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
```

## Part 7: Evaluation Configuration

### test_config.json

Defines thresholds for different metrics.

```json
{
  "criteria": {
    "tool_trajectory_avg_score": 1.0,
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

### Configuration Options

#### Trajectory Match Types

```json
"tool_trajectory_avg_score": {
  "threshold": 1.0,
  "match_type": "EXACT"  // or "IN_ORDER" or "ANY_ORDER"
}
```

#### Default Criteria
If not specified:
- `tool_trajectory_avg_score`: 1.0 (100% match)
- `response_match_score`: 0.8 (80% word overlap)

## Running the Exercise

```bash
# Navigate to lab5
cd lab5_evaluation

# Run the exercise
uv run python 01_evaluation_basics.py
```

## Expected Output

The exercise will:
1. Explain evaluation concepts
2. Create a calculator agent
3. Show data structure formats
4. Run manual evaluation with 3 test cases
5. Display results (tool match and response match)
6. Show configuration examples

## Key Takeaways

1. **Agent evaluation ≠ traditional testing**
   - Non-deterministic outputs require qualitative metrics

2. **Two evaluation targets**:
   - **Trajectory**: Tool usage correctness
   - **Response**: Answer correctness

3. **Three data structures**:
   - **EvalSet**: Collection of test cases
   - **EvalCase**: Single conversation to test
   - **Invocation**: Single user-agent turn

4. **Test file format**:
   - Use `.test.json` extension
   - Follow EvalSet schema
   - Optional `test_config.json` for criteria

5. **Running evaluations**:
   - Python API: `AgentEvaluator.evaluate()`
   - CLI: `adk eval <agent> <test_file>`

## Next Steps

- **Exercise 2**: Deep dive into response evaluation (ROUGE-1, semantic matching)
- **Exercise 3**: Master trajectory evaluation (match types)
- **Exercise 4**: Create custom rubrics
- **Exercise 5**: Use user simulation for dynamic testing

## Common Patterns

### Test Organization
```
my_agent/
├── agent.py              # Agent definition
├── test_config.json      # Evaluation criteria
└── tests/
    ├── basic.test.json   # Basic functionality
    ├── edge.test.json    # Edge cases
    └── multi.test.json   # Multi-turn conversations
```

### Minimal Test File
```json
{
  "eval_set_id": "minimal_test",
  "eval_cases": [
    {
      "eval_id": "test_1",
      "conversation": [
        {
          "user_content": {"parts": [{"text": "Hello"}]},
          "final_response": {"parts": [{"text": "Hi!"}]}
        }
      ]
    }
  ]
}
```

## Troubleshooting

### Issue: Test file not loading
- Check `.test.json` extension
- Verify JSON syntax
- Ensure all required fields are present

### Issue: Evaluation fails
- Check API key is set: `export GOOGLE_API_KEY="..."`
- Verify agent module path
- Review error messages for missing fields

### Issue: Low scores
- Review agent instruction clarity
- Check if expected outputs are too strict
- Consider using semantic matching instead of exact word matching
