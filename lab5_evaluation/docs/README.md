# Lab 5 Documentation

Welcome to the Lab 5: Evaluation & Testing documentation. This directory contains comprehensive guides for all exercises in this lab.

## Documentation Structure

### Overview & Quick Start

- **[Overview.md](Overview.md)** - Lab introduction, core concepts, and getting started
- **[Quick-Reference.md](Quick-Reference.md)** - Quick reference guide with templates and commands

### Exercise-Specific Guides

1. **[01-Evaluation-Basics.md](01-Evaluation-Basics.md)**
   - Why agent evaluation differs from traditional testing
   - Evaluation data structures (EvalSet, EvalCase, Invocation)
   - Creating test files
   - Running evaluations

2. **[02-Response-Evaluation.md](02-Response-Evaluation.md)**
   - ROUGE-1 word overlap scoring
   - Semantic matching with LLM-as-judge
   - Comparing lexical vs semantic approaches
   - Setting thresholds

3. **[03-Trajectory-Evaluation.md](03-Trajectory-Evaluation.md)**
   - Tool trajectory evaluation
   - Match types: EXACT, IN_ORDER, ANY_ORDER
   - Evaluating tool arguments
   - Debugging trajectory failures

4. **[04-Custom-Evaluators.md](04-Custom-Evaluators.md)**
   - Rubric-based evaluation
   - Hallucination detection
   - Safety evaluation
   - Writing effective rubrics

5. **[05-User-Simulation.md](05-User-Simulation.md)**
   - Dynamic user simulation
   - Conversation scenarios
   - Simulator configuration
   - Best practices

## Quick Navigation

### I want to...

#### Learn the Basics
→ Start with [Overview.md](Overview.md), then read [01-Evaluation-Basics.md](01-Evaluation-Basics.md)

#### Find a Configuration Template
→ Check [Quick-Reference.md](Quick-Reference.md) for all templates

#### Understand Response Evaluation
→ Read [02-Response-Evaluation.md](02-Response-Evaluation.md)

#### Validate Tool Usage
→ Read [03-Trajectory-Evaluation.md](03-Trajectory-Evaluation.md)

#### Create Custom Criteria
→ Read [04-Custom-Evaluators.md](04-Custom-Evaluators.md)

#### Test Conversational Flows
→ Read [05-User-Simulation.md](05-User-Simulation.md)

#### Debug Evaluation Issues
→ Check "Debugging" sections in each guide

#### See All CLI Commands
→ Check [Quick-Reference.md](Quick-Reference.md) CLI section

## Document Features

Each exercise guide includes:

- **Learning Objectives** - What you'll learn
- **Detailed Explanations** - Concepts with examples
- **Code Examples** - Configuration and code snippets
- **Running Instructions** - How to execute the exercise
- **Key Takeaways** - Summary of important points
- **Troubleshooting** - Common issues and solutions

## Recommended Reading Order

### For Beginners
1. [Overview.md](Overview.md) - Understand the landscape
2. [01-Evaluation-Basics.md](01-Evaluation-Basics.md) - Learn fundamentals
3. [02-Response-Evaluation.md](02-Response-Evaluation.md) - Response quality
4. [03-Trajectory-Evaluation.md](03-Trajectory-Evaluation.md) - Tool validation
5. [Quick-Reference.md](Quick-Reference.md) - Keep handy for reference

### For Experienced Users
1. [Quick-Reference.md](Quick-Reference.md) - Templates and commands
2. [04-Custom-Evaluators.md](04-Custom-Evaluators.md) - Advanced techniques
3. [05-User-Simulation.md](05-User-Simulation.md) - Dynamic testing

### For Specific Use Cases

**Testing a Customer Service Agent**:
- [02-Response-Evaluation.md](02-Response-Evaluation.md) - Response quality
- [04-Custom-Evaluators.md](04-Custom-Evaluators.md) - Custom rubrics for tone
- [05-User-Simulation.md](05-User-Simulation.md) - Conversational testing

**Testing a Payment Workflow**:
- [03-Trajectory-Evaluation.md](03-Trajectory-Evaluation.md) - EXACT match type
- [04-Custom-Evaluators.md](04-Custom-Evaluators.md) - Safety evaluation

**Testing a Research Agent**:
- [03-Trajectory-Evaluation.md](03-Trajectory-Evaluation.md) - ANY_ORDER match
- [04-Custom-Evaluators.md](04-Custom-Evaluators.md) - Hallucination detection

## Key Concepts Summary

### Evaluation Types
- **Trajectory**: Did agent use right tools correctly?
- **Response**: Did agent give the right answer?

### Core Metrics
- `tool_trajectory_avg_score` - Tool sequence validation
- `response_match_score` - Word overlap (ROUGE-1)
- `final_response_match_v2` - Semantic similarity (LLM-as-judge)
- `hallucinations_v1` - Factual accuracy
- `safety_v1` - Content safety

### Match Types
- **EXACT**: Perfect match (strictest)
- **IN_ORDER**: Sequential with extras allowed
- **ANY_ORDER**: All present, any order (most flexible)

## Configuration Examples

### Basic Setup
```json
{
  "criteria": {
    "tool_trajectory_avg_score": 1.0,
    "response_match_score": 0.8
  }
}
```

### Production-Ready
```json
{
  "criteria": {
    "tool_trajectory_avg_score": {"threshold": 0.9, "match_type": "IN_ORDER"},
    "final_response_match_v2": {"threshold": 0.8},
    "hallucinations_v1": {"threshold": 0.9},
    "safety_v1": 0.95
  }
}
```

See [Quick-Reference.md](Quick-Reference.md) for more templates.

## Running Exercises

```bash
# Navigate to lab5
cd lab5_evaluation

# Install dependencies
uv sync

# Set API key
export GOOGLE_API_KEY="your-api-key"

# Run any exercise
uv run python 01_evaluation_basics.py
uv run python 02_response_evaluation.py
uv run python 03_trajectory_evaluation.py
uv run python 04_custom_evaluators.py
uv run python 05_user_simulation.py
```

## Common Questions

### Q: Which metric should I use for response evaluation?
**A**: Use `response_match_score` for CI/CD (fast, deterministic). Use `final_response_match_v2` for quality assessment (understands meaning).

See: [02-Response-Evaluation.md](02-Response-Evaluation.md)

### Q: What match type should I use for trajectory?
**A**: Use `EXACT` for critical workflows (payments), `IN_ORDER` for pipelines, `ANY_ORDER` for flexible operations.

See: [03-Trajectory-Evaluation.md](03-Trajectory-Evaluation.md)

### Q: How do I create custom evaluation criteria?
**A**: Use rubrics - define yes/no questions that LLM-as-judge evaluates.

See: [04-Custom-Evaluators.md](04-Custom-Evaluators.md)

### Q: Can I test conversational agents with unpredictable flows?
**A**: Yes, use user simulation with conversation scenarios.

See: [05-User-Simulation.md](05-User-Simulation.md)

### Q: What's the difference between static tests and user simulation?
**A**: Static tests have fixed inputs/outputs. User simulation adapts dynamically to agent responses.

See: [05-User-Simulation.md](05-User-Simulation.md)

## Troubleshooting

### Evaluation Fails to Run
1. Check API key: `echo $GOOGLE_API_KEY`
2. Verify test file syntax (valid JSON)
3. Check agent module path

### Low Scores
1. Review thresholds (try 0.7 instead of 0.9)
2. Use semantic matching for paraphrases
3. Check reference responses are realistic

### Trajectory Mismatches
1. Verify tool names are exact (case-sensitive)
2. Check argument values
3. Consider more flexible match type

See troubleshooting sections in each guide for detailed help.

## Additional Resources

- **Official ADK Docs**: https://google.github.io/adk-docs/
- **Lab README**: `../README.md`
- **Exercise Files**: `../*.py`
- **Related Labs**:
  - Lab 1: Context & State
  - Lab 2: Sessions & Memory
  - Lab 3: Callbacks & Plugins

## Contributing

Found an issue or have suggestions? The documentation mirrors the exercise code structure. Updates should maintain consistency with:
- Exercise learning objectives
- Code examples
- Best practices

## Version

This documentation corresponds to:
- **Lab**: lab5_evaluation
- **ADK Version**: >=1.19.0
- **Python**: >=3.12

---

**Happy Evaluating!** 🎯

Start with [Overview.md](Overview.md) or jump to any specific guide above.
